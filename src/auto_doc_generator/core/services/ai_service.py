"""
AI/ML analysis service.

This service orchestrates AI and ML component analysis,
coordinating between different AI analyzers and managing AI-related insights.
Includes proper LLM integration for intelligent code analysis.
"""

from typing import Dict, List, Any, Optional, Union
import logging
import time
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from ..repositories.file_repository import FileRepository
from ..repositories.cache_repository import CacheRepository
from ...analyzers.ai.framework_detector import FrameworkDetector
from ...analyzers.ai.model_analyzer import ModelAnalyzer
from ...analyzers.ai.pipeline_analyzer import PipelineAnalyzer


class AIService:
    """
    Service that orchestrates AI/ML analysis operations.
    
    This service coordinates between different AI analyzers to provide
    comprehensive AI/ML component analysis.
    """
    
    def __init__(self, file_repository: FileRepository, 
                 cache_repository: CacheRepository, config: Dict[str, Any]):
        """
        Initialize AI service.
        
        Args:
            file_repository: File operations repository
            cache_repository: Caching repository
            config: Configuration dictionary
        """
        self.file_repository = file_repository
        self.cache_repository = cache_repository
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI analyzers
        self.framework_detector = FrameworkDetector(config)
        self.model_analyzer = ModelAnalyzer(config)
        self.pipeline_analyzer = PipelineAnalyzer(config)
        
        # Initialize LLM client
        self.llm_client = None
        self.llm_enabled = False
        self._rate_limiter = {}
        self._setup_llm_client()
        
        self.logger.info(f"AI service initialized (LLM enabled: {self.llm_enabled})")
    
    def _setup_llm_client(self):
        """Setup LLM client based on configuration."""
        try:
            if not OPENAI_AVAILABLE:
                self.logger.warning("OpenAI library not available. LLM features will be disabled.")
                return
            
            llm_config = self.config.get('llm', {})
            
            if not llm_config.get('enabled', False):
                self.logger.info("LLM analysis disabled in configuration")
                return
            
            api_key = llm_config.get('openai_api_key') or self.config.get('OPENAI_API_KEY')
            
            if not api_key:
                self.logger.warning("No OpenAI API key found. LLM features will be disabled.")
                return
            
            # Initialize OpenAI client
            self.llm_client = openai.OpenAI(api_key=api_key)
            self.llm_enabled = True
            
            # Setup rate limiting parameters
            self.max_requests_per_minute = llm_config.get('max_requests_per_minute', 60)
            self.max_tokens_per_request = llm_config.get('max_tokens_per_request', 4000)
            self.default_model = llm_config.get('default_model', 'gpt-3.5-turbo')
            
            self.logger.info(f"LLM client initialized with model: {self.default_model}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup LLM client: {e}")
            self.llm_enabled = False
    
    def analyze_with_context(self, prompt: str, context: str, max_tokens: int = 1000, 
                           model: Optional[str] = None, temperature: float = 0.3) -> Dict[str, Any]:
        """
        Analyze with LLM using context.
        
        Args:
            prompt: The prompt to send to the LLM
            context: Context for the analysis
            max_tokens: Maximum tokens in response
            model: Model to use (defaults to configured model)
            temperature: Temperature for response generation
            
        Returns:
            Dictionary with analysis results
        """
        if not self.llm_enabled:
            return {
                'success': False,
                'error': 'LLM service is not available',
                'context': context,
                'fallback': True
            }
        
        try:
            # Rate limiting check
            if not self._check_rate_limit():
                return {
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'context': context,
                    'retry_after': 60
                }
            
            # Use provided model or default
            model_name = model or self.default_model
            
            # Limit max_tokens to configured maximum
            max_tokens = min(max_tokens, self.max_tokens_per_request)
            
            # Create messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert software architect and AI/ML engineer. "
                              "Analyze the provided code context and give detailed, actionable insights."
                },
                {
                    "role": "user", 
                    "content": f"Context: {context}\n\nPrompt: {prompt}"
                }
            ]
            
            self.logger.debug(f"Sending LLM request with {len(str(messages))} characters")
            
            # Make API call with retry logic
            response = self._make_llm_request(
                messages=messages,
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if response['success']:
                result = {
                    'success': True,
                    'content': response['content'],
                    'context': context,
                    'tokens_used': response.get('tokens_used', 0),
                    'model_used': model_name,
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
                # Cache successful responses
                self._cache_llm_response(prompt, context, result)
                return result
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'Unknown LLM error'),
                    'context': context
                }
            
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'context': context
            }
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.now()
        minute_key = now.strftime('%Y%m%d%H%M')
        
        if minute_key not in self._rate_limiter:
            self._rate_limiter[minute_key] = 0
            # Clean up old entries
            old_keys = [k for k in self._rate_limiter.keys() 
                       if k != minute_key and len(self._rate_limiter) > 5]
            for old_key in old_keys:
                del self._rate_limiter[old_key]
        
        if self._rate_limiter[minute_key] >= self.max_requests_per_minute:
            return False
        
        self._rate_limiter[minute_key] += 1
        return True
    
    def _make_llm_request(self, messages: List[Dict[str, str]], model: str, 
                         max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Make LLM request with retry logic."""
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = self.llm_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=30
                )
                
                return {
                    'success': True,
                    'content': response.choices[0].message.content,
                    'tokens_used': response.usage.total_tokens if response.usage else 0,
                    'finish_reason': response.choices[0].finish_reason
                }
                
            except openai.RateLimitError as e:
                if attempt == max_retries - 1:
                    return {'success': False, 'error': f'Rate limit exceeded: {str(e)}'}
                time.sleep(base_delay * (2 ** attempt))
                
            except openai.APITimeoutError as e:
                if attempt == max_retries - 1:
                    return {'success': False, 'error': f'API timeout: {str(e)}'}
                time.sleep(base_delay * (2 ** attempt))
                
            except openai.BadRequestError as e:
                return {'success': False, 'error': f'Bad request: {str(e)}'}
                
            except Exception as e:
                if attempt == max_retries - 1:
                    return {'success': False, 'error': f'Unexpected error: {str(e)}'}
                time.sleep(base_delay * (2 ** attempt))
        
        return {'success': False, 'error': 'Max retries exceeded'}
    
    def _cache_llm_response(self, prompt: str, context: str, result: Dict[str, Any]):
        """Cache LLM response for future use."""
        try:
            cache_key = f"llm_response_{hash(prompt + context)}"
            # Cache for 1 hour
            self.cache_repository.set(cache_key, result, ttl=3600)
        except Exception as e:
            self.logger.warning(f"Failed to cache LLM response: {e}")
    
    def analyze_code_quality(self, code_content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Analyze code quality using LLM.
        
        Args:
            code_content: The code to analyze
            file_path: Path of the file being analyzed
            
        Returns:
            Quality analysis results
        """
        prompt = """
        Analyze this code for:
        1. Code quality and maintainability
        2. Potential bugs or security issues
        3. Performance improvements
        4. Best practices adherence
        5. Documentation quality
        
        Provide specific, actionable recommendations with code examples where helpful.
        """
        
        context = f"File: {file_path}\n\nCode:\n{code_content[:3000]}..."  # Limit context size
        
        return self.analyze_with_context(prompt, context, max_tokens=1500)
    
    def analyze_architecture_patterns(self, module_structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze architectural patterns using LLM.
        
        Args:
            module_structure: Structure of modules and their relationships
            
        Returns:
            Architecture analysis results
        """
        prompt = """
        Analyze this codebase structure for:
        1. Architectural patterns used (MVC, Clean Architecture, etc.)
        2. Design pattern implementation
        3. Code organization and modularity
        4. Dependency management
        5. Suggestions for architectural improvements
        
        Focus on identifying concrete patterns and providing specific recommendations.
        """
        
        context = f"Module Structure:\n{json.dumps(module_structure, indent=2)[:2000]}..."
        
        return self.analyze_with_context(prompt, context, max_tokens=1200)
    
    def generate_documentation_suggestions(self, function_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate documentation suggestions using LLM.
        
        Args:
            function_data: Information about functions, classes, and modules
            
        Returns:
            Documentation suggestions
        """
        prompt = """
        Analyze these functions/classes and suggest:
        1. Missing or inadequate docstrings
        2. Better parameter documentation
        3. Return type documentation
        4. Usage examples where helpful
        5. Comments for complex logic
        
        Provide specific examples of improved documentation.
        """
        
        context = f"Function/Class Data:\n{json.dumps(function_data, indent=2)[:2500]}..."
        
        return self.analyze_with_context(prompt, context, max_tokens=1000)
    
    def analyze_ai_components(self, target_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive AI/ML component analysis.
        
        Args:
            target_path: Path to analyze
            
        Returns:
            Combined AI analysis results
        """
        self.logger.info(f"Starting AI/ML analysis for: {target_path}")
        
        try:
            target = Path(target_path)
            
            # Run framework detection
            framework_result = self.framework_detector.analyze(target)
            
            # Run model analysis
            model_result = self.model_analyzer.analyze(target)
            
            # Run pipeline analysis
            pipeline_result = self.pipeline_analyzer.analyze(target)
            
            # Combine results
            combined_result = self._combine_ai_results(framework_result, model_result, pipeline_result)
            
            # Cache results
            cache_key = f"ai_analysis_{target_path}"
            self.cache_repository.set(cache_key, combined_result)
            
            self.logger.info("AI/ML analysis completed successfully")
            return combined_result
            
        except Exception as e:
            self.logger.error(f"AI/ML analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': {},
                'timestamp': self._get_timestamp()
            }
    
    def _combine_ai_results(self, framework_result: Dict[str, Any], 
                           model_result: Dict[str, Any], 
                           pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine results from different AI analyzers.
        
        Args:
            framework_result: Results from framework detector
            model_result: Results from model analyzer
            pipeline_result: Results from pipeline analyzer
            
        Returns:
            Combined AI analysis results
        """
        combined = {
            'success': True,
            'timestamp': self._get_timestamp(),
            'analyzers_used': [],
            'results': {
                'frameworks_detected': [],
                'models': [],
                'pipelines': [],
                'training_files': [],
                'inference_files': [],
                'summary': {}
            }
        }
        
        # Include framework detection results
        if framework_result.get('success', True) and framework_result.get('results'):
            framework_data = framework_result['results']
            combined['results']['frameworks_detected'] = framework_data.get('frameworks', [])
            combined['analyzers_used'].append('framework_detector')
        
        # Include model analysis results
        if model_result.get('success', True) and model_result.get('results'):
            model_data = model_result['results']
            combined['results']['models'] = model_data.get('models', [])
            combined['results']['training_files'].extend(model_data.get('training_files', []))
            combined['results']['inference_files'].extend(model_data.get('inference_files', []))
            combined['analyzers_used'].append('model_analyzer')
        
        # Include pipeline analysis results
        if pipeline_result.get('success', True) and pipeline_result.get('results'):
            pipeline_data = pipeline_result['results']
            combined['results']['pipelines'] = pipeline_data.get('pipelines', [])
            
            # Merge workflow files into training/inference files
            workflow_files = pipeline_data.get('workflow_files', [])
            for workflow in workflow_files:
                if 'train' in workflow.get('workflow_steps', []):
                    combined['results']['training_files'].append(workflow['file'])
                if any(step in workflow.get('workflow_steps', []) for step in ['predict', 'inference']):
                    combined['results']['inference_files'].append(workflow['file'])
            
            combined['analyzers_used'].append('pipeline_analyzer')
        
        # Remove duplicates
        combined['results']['training_files'] = list(set(combined['results']['training_files']))
        combined['results']['inference_files'] = list(set(combined['results']['inference_files']))
        combined['results']['frameworks_detected'] = list(set(combined['results']['frameworks_detected']))
        
        # Generate summary
        combined['results']['summary'] = self._generate_ai_summary(combined['results'])
        
        return combined
    
    def _generate_ai_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summary statistics for AI analysis.
        
        Args:
            results: Combined AI analysis results
            
        Returns:
            Summary statistics
        """
        summary = {
            'total_frameworks': len(results.get('frameworks_detected', [])),
            'total_models': len(results.get('models', [])),
            'total_pipelines': len(results.get('pipelines', [])),
            'total_training_files': len(results.get('training_files', [])),
            'total_inference_files': len(results.get('inference_files', [])),
            'has_ai_components': False,
            'complexity_level': 'none',
            'primary_framework': None,
            'model_types': []
        }
        
        # Determine if there are AI components
        summary['has_ai_components'] = (
            summary['total_frameworks'] > 0 or 
            summary['total_models'] > 0 or 
            summary['total_pipelines'] > 0
        )
        
        # Determine complexity level
        total_components = summary['total_models'] + summary['total_pipelines']
        if total_components == 0:
            summary['complexity_level'] = 'none'
        elif total_components <= 2:
            summary['complexity_level'] = 'low'
        elif total_components <= 5:
            summary['complexity_level'] = 'medium'
        else:
            summary['complexity_level'] = 'high'
        
        # Determine primary framework
        frameworks = results.get('frameworks_detected', [])
        if frameworks:
            # Count framework usage across models
            framework_counts = {}
            for model in results.get('models', []):
                framework = model.get('framework')
                if framework:
                    framework_counts[framework] = framework_counts.get(framework, 0) + 1
            
            if framework_counts:
                summary['primary_framework'] = max(framework_counts.items(), key=lambda x: x[1])[0]
            else:
                summary['primary_framework'] = frameworks[0]
        
        # Collect model types
        model_types = set()
        for model in results.get('models', []):
            model_type = model.get('model_type')
            if model_type:
                model_types.add(model_type)
        summary['model_types'] = list(model_types)
        
        return summary
    
    def detect_frameworks(self, target_path: str) -> Dict[str, Any]:
        """
        Quick framework detection for a target.
        
        Args:
            target_path: Path to analyze
            
        Returns:
            Framework detection results
        """
        # Check cache first
        cache_key = f"frameworks_{target_path}"
        cached = self.cache_repository.get(cache_key)
        if cached:
            return cached
        
        try:
            target = Path(target_path)
            result = self.framework_detector.analyze(target)
            
            if result.get('success', True) and result.get('results'):
                frameworks = result['results'].get('frameworks', [])
                summary = {
                    'frameworks': frameworks,
                    'total_frameworks': len(frameworks),
                    'has_ai': len(frameworks) > 0,
                    'timestamp': self._get_timestamp()
                }
                
                # Cache for 30 minutes
                self.cache_repository.set(cache_key, summary, ttl=1800)
                return summary
            
        except Exception as e:
            self.logger.error(f"Framework detection failed: {e}")
        
        return {
            'frameworks': [],
            'total_frameworks': 0,
            'has_ai': False,
            'error': 'Framework detection failed',
            'timestamp': self._get_timestamp()
        }
    
    def analyze_models_only(self, target_path: str) -> Dict[str, Any]:
        """
        Analyze only AI/ML models in the target.
        
        Args:
            target_path: Path to analyze
            
        Returns:
            Model analysis results
        """
        try:
            target = Path(target_path)
            result = self.model_analyzer.analyze(target)
            
            if result.get('success', True) and result.get('results'):
                return {
                    'success': True,
                    'models': result['results'].get('models', []),
                    'summary': result['results'].get('summary', {}),
                    'timestamp': self._get_timestamp()
                }
            
        except Exception as e:
            self.logger.error(f"Model analysis failed: {e}")
        
        return {
            'success': False,
            'models': [],
            'error': 'Model analysis failed',
            'timestamp': self._get_timestamp()
        }
    
    def analyze_pipelines_only(self, target_path: str) -> Dict[str, Any]:
        """
        Analyze only AI/ML pipelines in the target.
        
        Args:
            target_path: Path to analyze
            
        Returns:
            Pipeline analysis results
        """
        try:
            target = Path(target_path)
            result = self.pipeline_analyzer.analyze(target)
            
            if result.get('success', True) and result.get('results'):
                return {
                    'success': True,
                    'pipelines': result['results'].get('pipelines', []),
                    'workflow_files': result['results'].get('workflow_files', []),
                    'summary': result['results'].get('summary', {}),
                    'timestamp': self._get_timestamp()
                }
            
        except Exception as e:
            self.logger.error(f"Pipeline analysis failed: {e}")
        
        return {
            'success': False,
            'pipelines': [],
            'workflow_files': [],
            'error': 'Pipeline analysis failed',
            'timestamp': self._get_timestamp()
        }
    
    def get_ai_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """
        Generate AI/ML improvement recommendations based on analysis.
        
        Args:
            analysis_results: AI analysis results
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        try:
            results = analysis_results.get('results', {})
            summary = results.get('summary', {})
            
            # Framework recommendations
            frameworks = results.get('frameworks_detected', [])
            if not frameworks:
                recommendations.append("Consider adding AI/ML frameworks to enhance your application")
            elif len(frameworks) > 3:
                recommendations.append("Consider consolidating AI/ML frameworks to reduce complexity")
            
            # Model recommendations
            models = results.get('models', [])
            if models:
                model_types = set(model.get('model_type', 'unknown') for model in models)
                if len(model_types) == 1 and 'unknown' in model_types:
                    recommendations.append("Add proper model type documentation for better analysis")
                
                # Check for missing docstrings
                undocumented_models = [m for m in models if not m.get('docstring')]
                if undocumented_models:
                    recommendations.append(f"Add documentation to {len(undocumented_models)} AI/ML models")
            
            # Pipeline recommendations
            pipelines = results.get('pipelines', [])
            if pipelines:
                simple_pipelines = [p for p in pipelines if len(p.get('steps', [])) < 3]
                if simple_pipelines:
                    recommendations.append("Consider adding more comprehensive pipeline steps")
            
            # Training/Inference balance
            training_files = len(results.get('training_files', []))
            inference_files = len(results.get('inference_files', []))
            
            if training_files > 0 and inference_files == 0:
                recommendations.append("Consider adding inference/prediction endpoints")
            elif training_files == 0 and inference_files > 0:
                recommendations.append("Consider adding training scripts for model development")
            
            # Complexity recommendations
            complexity = summary.get('complexity_level', 'none')
            if complexity == 'high':
                recommendations.append("Consider breaking down complex AI pipelines into smaller components")
            elif complexity == 'none':
                recommendations.append("Consider adding AI/ML capabilities to enhance your application")
            
        except Exception as e:
            self.logger.error(f"AI recommendations generation failed: {e}")
            recommendations.append("Unable to generate AI recommendations due to analysis error")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def generate_code_insights(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive code insights using LLM.
        
        Args:
            analysis_data: Complete analysis data from code analyzers
            
        Returns:
            Comprehensive insights and recommendations
        """
        if not self.llm_enabled:
            return {
                'success': False,
                'error': 'LLM service not available',
                'insights': []
            }
        
        try:
            # Extract key metrics for analysis
            modules = analysis_data.get('modules', [])
            total_functions = sum(len(m.get('functions', [])) for m in modules)
            total_classes = sum(len(m.get('classes', [])) for m in modules)
            
            # Create high-level summary
            summary = {
                'total_modules': len(modules),
                'total_functions': total_functions,
                'total_classes': total_classes,
                'complexity_issues': [],
                'architecture_patterns': []
            }
            
            # Find high complexity functions
            for module in modules:
                for func in module.get('functions', []):
                    if func.get('complexity', 0) > 10:
                        summary['complexity_issues'].append({
                            'name': func.get('name'),
                            'module': module.get('module_path'),
                            'complexity': func.get('complexity')
                        })
            
            prompt = """
            Based on this codebase analysis, provide:
            
            1. **Architecture Assessment**: What architectural patterns do you see?
            2. **Quality Issues**: What are the main quality concerns?
            3. **Improvement Priorities**: Top 5 areas for improvement
            4. **Technical Debt**: Areas of technical debt to address
            5. **Scalability Concerns**: Potential scalability bottlenecks
            
            Be specific and actionable in your recommendations.
            """
            
            context = f"Codebase Summary:\n{json.dumps(summary, indent=2)}"
            
            return self.analyze_with_context(prompt, context, max_tokens=2000)
            
        except Exception as e:
            self.logger.error(f"Failed to generate code insights: {e}")
            return {
                'success': False,
                'error': str(e),
                'insights': []
            }
    
    def analyze_performance_bottlenecks(self, complexity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze potential performance bottlenecks using complexity data.
        
        Args:
            complexity_data: Complexity analysis results
            
        Returns:
            Performance bottleneck analysis
        """
        prompt = """
        Analyze these complexity metrics for performance bottlenecks:
        
        1. **Critical Functions**: Functions with highest complexity that may cause performance issues
        2. **Bottleneck Patterns**: Common patterns that lead to performance problems
        3. **Optimization Strategies**: Specific strategies to improve performance
        4. **Monitoring Recommendations**: What metrics to monitor in production
        5. **Refactoring Priorities**: Which functions should be refactored first
        
        Focus on actionable performance improvements.
        """
        
        context = f"Complexity Data:\n{json.dumps(complexity_data, indent=2)[:3000]}..."
        
        return self.analyze_with_context(prompt, context, max_tokens=1500)
    
    def suggest_testing_strategy(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest comprehensive testing strategy using LLM.
        
        Args:
            analysis_data: Code analysis results
            
        Returns:
            Testing strategy recommendations
        """
        prompt = """
        Based on this codebase structure, suggest a comprehensive testing strategy:
        
        1. **Unit Testing**: Which functions/classes need unit tests most
        2. **Integration Testing**: Key integration points to test
        3. **Performance Testing**: Functions that need performance testing
        4. **Edge Cases**: Important edge cases to test
        5. **Test Coverage**: Recommended coverage targets for different components
        
        Provide specific examples and priorities.
        """
        
        # Prepare relevant data for testing analysis
        test_data = {
            'modules': len(analysis_data.get('modules', [])),
            'high_complexity_functions': [],
            'api_functions': [],
            'data_processing_functions': []
        }
        
        # Extract functions that need testing priority
        for module in analysis_data.get('modules', []):
            for func in module.get('functions', []):
                if func.get('complexity', 0) > 10:
                    test_data['high_complexity_functions'].append({
                        'name': func.get('name'),
                        'complexity': func.get('complexity'),
                        'module': module.get('module_path')
                    })
                
                # Look for API or data processing patterns
                func_name = func.get('name', '').lower()
                if any(pattern in func_name for pattern in ['api', 'endpoint', 'route']):
                    test_data['api_functions'].append(func.get('name'))
                elif any(pattern in func_name for pattern in ['process', 'transform', 'parse']):
                    test_data['data_processing_functions'].append(func.get('name'))
        
        context = f"Testing Analysis Data:\n{json.dumps(test_data, indent=2)}"
        
        return self.analyze_with_context(prompt, context, max_tokens=1200)
    
    async def analyze_with_context_async(self, prompt: str, context: str, 
                                       max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Async version of analyze_with_context for concurrent processing.
        
        Args:
            prompt: The prompt to send to the LLM
            context: Context for the analysis
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary with analysis results
        """
        # Run the sync version in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: self.analyze_with_context(prompt, context, max_tokens)
        )
        return result
    
    def batch_analyze(self, analysis_requests: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Perform batch analysis of multiple requests.
        
        Args:
            analysis_requests: List of {prompt, context} dictionaries
            
        Returns:
            List of analysis results
        """
        results = []
        
        for i, request in enumerate(analysis_requests):
            self.logger.info(f"Processing batch request {i+1}/{len(analysis_requests)}")
            
            result = self.analyze_with_context(
                prompt=request.get('prompt', ''),
                context=request.get('context', ''),
                max_tokens=request.get('max_tokens', 1000)
            )
            
            results.append(result)
            
            # Add small delay between requests to respect rate limits
            if i < len(analysis_requests) - 1:
                time.sleep(0.1)
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get status of AI service and its components.
        
        Returns:
            Service status information
        """
        return {
            'service_name': 'AIService',
            'analyzers_available': [
                'FrameworkDetector',
                'ModelAnalyzer', 
                'PipelineAnalyzer'
            ],
            'llm_capabilities': [
                'analyze_with_context',
                'analyze_code_quality',
                'analyze_architecture_patterns',
                'generate_documentation_suggestions',
                'generate_code_insights',
                'analyze_performance_bottlenecks',
                'suggest_testing_strategy'
            ] if self.llm_enabled else [],
            'total_analyzers': 3,
            'llm_enabled': self.llm_enabled,
            'llm_model': self.default_model if self.llm_enabled else None,
            'openai_available': OPENAI_AVAILABLE,
            'config': self.config.get('ai', {}),
            'cache_enabled': self.cache_repository is not None,
            'rate_limit_per_minute': self.max_requests_per_minute if self.llm_enabled else 0,
            'ready': True
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
