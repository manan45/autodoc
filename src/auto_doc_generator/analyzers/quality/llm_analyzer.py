"""
LLM-powered code quality analysis.

This module uses large language models to provide intelligent
code quality assessments and recommendations.
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from ..base.base_analyzer import BaseAnalyzer


class LLMAnalyzer(BaseAnalyzer):
    """
    Analyzer that uses LLM for intelligent code quality assessment.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm_config = config.get('llm', {})
        self.openai_enabled = self.llm_config.get('enabled', False)
        
        if self.openai_enabled:
            try:
                import openai
                self.client = openai.OpenAI()
            except ImportError:
                self.logger.warning("OpenAI not available. LLM analysis will be skipped.")
                self.openai_enabled = False
                self.client = None
        else:
            self.client = None
    
    def analyze(self, target: Path) -> Dict[str, Any]:
        """
        Analyze code quality using LLM.
        
        Args:
            target: Directory or file path to analyze
            
        Returns:
            Dictionary containing LLM analysis results
        """
        self.log_analysis_start(str(target))
        
        result = self.create_result_template()
        result['timestamp'] = datetime.now().isoformat()
        
        if not self.openai_enabled:
            result['results'] = {
                'assessments': {},
                'global_insights': {},
                'summary': {
                    'llm_enabled': False,
                    'reason': 'LLM analysis disabled or OpenAI not available'
                }
            }
            return result
        
        if target.is_file():
            files = [target]
        else:
            files = self.find_python_files(target)
        
        # Limit files for LLM analysis due to cost
        max_files = self.llm_config.get('max_files', 5)
        files = files[:max_files]
        
        assessments = {}
        
        for i, file_path in enumerate(files):
            try:
                # Add rate limiting between files to prevent API overload
                if i > 0:  # Don't delay before first file
                    import time
                    delay = self.llm_config.get('delay_between_files', 0.5)
                    time.sleep(delay)
                
                assessment = self.analyze_file_with_llm(file_path)
                if assessment:
                    relative_path = str(file_path.relative_to(target if target.is_dir() else target.parent))
                    assessments[relative_path] = assessment
                    
            except Exception as e:
                result['errors'].append(f"Failed LLM analysis for {file_path}: {str(e)}")
        
        # Generate global insights
        global_insights = self.generate_global_insights(assessments)
        
        result['results'] = {
            'assessments': assessments,
            'global_insights': global_insights,
            'summary': {
                'llm_enabled': True,
                'files_analyzed': len(assessments),
                'total_files_found': len(self.find_python_files(target))
            }
        }
        
        self.log_analysis_complete(str(target), len(assessments))
        return result
    
    def analyze_file_with_llm(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze a single file using LLM.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dictionary with LLM assessment or None if analysis failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Note: Empty files are now filtered out at the BaseAnalyzer level
            
            # Limit content size for LLM
            max_chars = self.llm_config.get('max_chars_per_file', 8000)
            if len(content) > max_chars:
                content = content[:max_chars] + "\n# ... (truncated for analysis)"
            
            prompt = self.build_analysis_prompt(content, str(file_path))
            
            # Add retry logic and better error handling for API calls
            import time
            max_retries = self.llm_config.get('max_retries', 3)
            base_delay = self.llm_config.get('retry_base_delay', 1.0)
            
            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=self.llm_config.get('model', 'gpt-3.5-turbo'),
                        messages=[
                            {
                                "role": "system", 
                                "content": "You are a senior software engineer and code quality expert. Analyze the provided Python code and give detailed feedback on code quality, best practices, and potential improvements."
                            },
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_tokens=1000,
                        timeout=30
                    )
                    break  # Success, exit retry loop
                    
                except Exception as api_error:
                    error_type = type(api_error).__name__
                    
                    # Handle specific OpenAI API errors
                    if 'RateLimitError' in error_type:
                        if attempt == max_retries - 1:
                            self.logger.error(f"Rate limit exceeded after {max_retries} attempts for {file_path}")
                            return None
                        delay = base_delay * (3 ** attempt)  # Longer delay for rate limits
                        self.logger.warning(f"Rate limit hit for {file_path}. Retrying in {delay}s...")
                        time.sleep(delay)
                    elif 'APITimeoutError' in error_type:
                        if attempt == max_retries - 1:
                            self.logger.error(f"API timeout after {max_retries} attempts for {file_path}")
                            return None
                        delay = base_delay * (2 ** attempt)
                        self.logger.warning(f"API timeout for {file_path}. Retrying in {delay}s...")
                        time.sleep(delay)
                    elif 'BadRequestError' in error_type:
                        self.logger.error(f"Bad request for {file_path}: {api_error}")
                        return None  # Don't retry bad requests
                    else:
                        if attempt == max_retries - 1:
                            self.logger.error(f"API call failed after {max_retries} attempts for {file_path}: {api_error}")
                            return None
                        delay = base_delay * (2 ** attempt)
                        self.logger.warning(f"API call attempt {attempt + 1} failed for {file_path}: {api_error}. Retrying in {delay}s...")
                        time.sleep(delay)
            
            analysis_text = response.choices[0].message.content
            
            # Handle case where content is None
            if analysis_text is None:
                self.logger.warning(f"LLM returned None content for {file_path}")
                self.logger.warning(f"Response details - finish_reason: {response.choices[0].finish_reason}")
                self.logger.warning(f"Response details - refusal: {getattr(response.choices[0].message, 'refusal', None)}")
                return None
            
            # Parse the response into structured data
            structured_assessment = self.parse_llm_response(analysis_text)
            
            return {
                'file_path': str(file_path),
                'raw_analysis': analysis_text,
                'structured_assessment': structured_assessment,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in LLM analysis for {file_path}: {e}")
            return None
    
    def build_analysis_prompt(self, content: str, file_path: str) -> str:
        """
        Build the prompt for LLM analysis.
        
        Args:
            content: File content
            file_path: Path to the file
            
        Returns:
            Formatted prompt string
        """
        return f"""
Please analyze the following Python code from file: {file_path}

Code:
```python
{content}
```

Please provide a comprehensive code quality analysis covering:

1. **Code Structure & Organization**: How well is the code organized and structured?
2. **Readability & Maintainability**: Is the code easy to read and maintain?
3. **Best Practices**: Does it follow Python best practices and conventions?
4. **Performance Considerations**: Any performance issues or optimization opportunities?
5. **Security Concerns**: Any potential security vulnerabilities?
6. **Documentation**: Quality of comments and docstrings
7. **Error Handling**: How well are errors and edge cases handled?
8. **Testing**: Is the code testable? Any testing-related observations?

For each aspect, provide:
- A score from 1-10
- Key strengths
- Areas for improvement
- Specific recommendations

Format your response as structured text that can be easily parsed.
"""
    
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured data.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Structured assessment dictionary
        """
        # Handle None response
        if response is None:
            response = ""
        
        # Simple parsing - in production, you'd want more robust parsing
        aspects = {
            'structure': {'score': 5, 'strengths': [], 'improvements': []},
            'readability': {'score': 5, 'strengths': [], 'improvements': []},
            'best_practices': {'score': 5, 'strengths': [], 'improvements': []},
            'performance': {'score': 5, 'strengths': [], 'improvements': []},
            'security': {'score': 5, 'strengths': [], 'improvements': []},
            'documentation': {'score': 5, 'strengths': [], 'improvements': []},
            'error_handling': {'score': 5, 'strengths': [], 'improvements': []},
            'testing': {'score': 5, 'strengths': [], 'improvements': []}
        }
        
        # Extract scores using regex (basic implementation)
        import re
        
        # Look for scores in the response
        score_patterns = [
            r'Structure.*?(\d+)/10',
            r'Readability.*?(\d+)/10',
            r'Best Practices.*?(\d+)/10',
            r'Performance.*?(\d+)/10',
            r'Security.*?(\d+)/10',
            r'Documentation.*?(\d+)/10',
            r'Error Handling.*?(\d+)/10',
            r'Testing.*?(\d+)/10'
        ]
        
        aspect_names = list(aspects.keys())
        
        for i, pattern in enumerate(score_patterns):
            matches = re.search(pattern, response, re.IGNORECASE)
            if matches and i < len(aspect_names):
                try:
                    score = int(matches.group(1))
                    aspects[aspect_names[i]]['score'] = min(10, max(1, score))
                except (ValueError, IndexError):
                    pass
        
        # Extract key points (simplified)
        strengths = []
        strengths_section = re.search(r'strengths?:?\s*\n(.*?)(?=improvements?|recommendations?|\n\n|\Z)', 
                                    response, re.IGNORECASE | re.DOTALL)
        if strengths_section:
            strengths_text = strengths_section.group(1)
            if strengths_text:  # Check if strengths_text is not None
                # Extract bullet points or lines
                strengths = [line.strip('- •*').strip() for line in strengths_text.split('\n') 
                            if line.strip() and not line.strip().startswith('#')]
        
        # Distribute strengths across aspects (simplified)
        for aspect in aspects.values():
            aspect['strengths'] = strengths[:2] if strengths else []  # Take first 2 strengths
        
        improvements = []
        improvements_section = re.search(r'improvements?|recommendations?:?\s*\n(.*?)(?=\n\n|\Z)', 
                                       response, re.IGNORECASE | re.DOTALL)
        if improvements_section:
            improvements_text = improvements_section.group(1)
            if improvements_text:  # Check if improvements_text is not None
                improvements = [line.strip('- •*').strip() for line in improvements_text.split('\n') 
                              if line.strip() and not line.strip().startswith('#')]
        
        # Distribute improvements across aspects (simplified)
        for aspect in aspects.values():
            aspect['improvements'] = improvements[:2] if improvements else []  # Take first 2 improvements
        
        # Calculate overall score
        overall_score = sum(aspect['score'] for aspect in aspects.values()) / len(aspects)
        
        return {
            'aspects': aspects,
            'overall_score': round(overall_score, 1),
            'grade': self.score_to_grade(overall_score / 10),
            'summary': self.extract_summary(response)
        }
    
    def extract_summary(self, response: str) -> str:
        """Extract a summary from the LLM response."""
        if response is None:
            return 'No summary available - LLM response was None'
        
        lines = response.split('\n')
        summary_lines = []
        
        for line in lines[:5]:  # Take first few lines as summary
            if line.strip() and not line.strip().startswith('#'):
                summary_lines.append(line.strip())
        
        return ' '.join(summary_lines)[:200] + '...' if summary_lines else 'No summary available'
    
    def score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'
    
    def generate_global_insights(self, assessments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate global insights from individual file assessments.
        
        Args:
            assessments: Dictionary of file assessments
            
        Returns:
            Global insights dictionary
        """
        if not assessments:
            return {}
        
        # Calculate aggregate scores
        all_scores = []
        aspect_scores = {
            'structure': [],
            'readability': [],
            'best_practices': [],
            'performance': [],
            'security': [],
            'documentation': [],
            'error_handling': [],
            'testing': []
        }
        
        for assessment in assessments.values():
            structured = assessment.get('structured_assessment', {})
            if 'overall_score' in structured:
                all_scores.append(structured['overall_score'])
            
            aspects = structured.get('aspects', {})
            for aspect_name, aspect_data in aspects.items():
                if aspect_name in aspect_scores:
                    aspect_scores[aspect_name].append(aspect_data.get('score', 5))
        
        # Calculate averages
        avg_scores = {}
        for aspect, scores in aspect_scores.items():
            avg_scores[aspect] = sum(scores) / len(scores) if scores else 5
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for aspect, avg_score in avg_scores.items():
            if avg_score >= 8:
                strengths.append(aspect.replace('_', ' ').title())
            elif avg_score <= 5:
                weaknesses.append(aspect.replace('_', ' ').title())
        
        return {
            'overall_average': sum(all_scores) / len(all_scores) if all_scores else 5,
            'aspect_averages': avg_scores,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'files_analyzed': len(assessments),
            'recommendations': self.generate_recommendations(strengths, weaknesses)
        }
    
    def generate_recommendations(self, strengths: List[str], weaknesses: List[str]) -> List[str]:
        """Generate high-level recommendations based on analysis."""
        recommendations = []
        
        if 'Documentation' in weaknesses:
            recommendations.append("Improve code documentation with comprehensive docstrings and comments")
        
        if 'Testing' in weaknesses:
            recommendations.append("Add comprehensive unit tests and test coverage")
        
        if 'Error Handling' in weaknesses:
            recommendations.append("Implement robust error handling and input validation")
        
        if 'Security' in weaknesses:
            recommendations.append("Review and address potential security vulnerabilities")
        
        if 'Performance' in weaknesses:
            recommendations.append("Optimize performance-critical code sections")
        
        if not recommendations:
            recommendations.append("Continue maintaining high code quality standards")
        
        return recommendations
