"""
AI analysis coordinator.

This module coordinates AI-enhanced analysis and documentation generation,
integrating with LLMs and AI services for intelligent insights.
"""

from typing import Dict, List, Any, Optional
import json
import logging

from ..base.base_generator import BaseGenerator


class AICoordinator(BaseGenerator):
    """
    Coordinator that enhances analysis and documentation with AI insights.
    
    This class orchestrates AI-powered enhancements to code analysis,
    documentation generation, and quality assessment.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ai_config = config.get('ai', {})
        self.llm_config = config.get('llm', {})
        self.openai_enabled = self.llm_config.get('enabled', False)
        
        # Initialize OpenAI client if available
        if self.openai_enabled:
            try:
                import openai
                self.client = openai.OpenAI()
                self.logger.info("✅ OpenAI client initialized")
            except ImportError:
                self.logger.warning("OpenAI package not available")
                self.openai_enabled = False
                self.client = None
        else:
            self.client = None
            self.logger.info("AI coordination disabled in config")
    
    def generate(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI-enhanced analysis and insights.
        
        Args:
            analysis_data: Combined analysis results
            
        Returns:
            Dictionary containing AI-enhanced analysis
        """
        self.log_generation_start("AI Coordination")
        
        result = self.create_result_template()
        
        try:
            enhanced_data = analysis_data.copy()
            
            # Enhance code analysis with AI insights
            if 'code_analysis' in analysis_data:
                enhanced_data['code_analysis'] = self.enhance_code_analysis(
                    analysis_data['code_analysis']
                )
            
            # Enhance quality analysis with AI insights
            if 'quality_analysis' in analysis_data:
                enhanced_data['quality_analysis'] = self.enhance_quality_analysis(
                    analysis_data['quality_analysis']
                )
            
            # Generate AI-powered documentation insights
            ai_insights = self.generate_ai_insights(enhanced_data)
            enhanced_data['ai_insights'] = ai_insights
            
            # Generate architecture recommendations
            arch_recommendations = self.generate_architecture_recommendations(enhanced_data)
            enhanced_data['architecture_recommendations'] = arch_recommendations
            
            result['results'] = {
                'enhanced_analysis': enhanced_data,
                'ai_enabled': self.openai_enabled,
                'insights_generated': len(ai_insights.get('insights', [])),
                'recommendations_generated': len(arch_recommendations.get('recommendations', []))
            }
            
            self.log_generation_complete("AI Coordination", 1)
            
        except Exception as e:
            result['errors'].append(f"AI coordination failed: {str(e)}")
            self.logger.error(f"AI coordination error: {e}")
        
        return result
    
    def enhance_code_analysis(self, code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance code analysis with AI insights.
        
        Args:
            code_analysis: Original code analysis results
            
        Returns:
            Enhanced code analysis with AI insights
        """
        enhanced = code_analysis.copy()
        
        if not self.openai_enabled:
            enhanced['ai_enhancement'] = {'enabled': False, 'reason': 'OpenAI not available'}
            return enhanced
        
        try:
            modules = code_analysis.get('modules', [])
            
            # Analyze top modules for patterns and insights
            top_modules = sorted(
                modules, 
                key=lambda x: x.get('stats', {}).get('functions', 0) + x.get('stats', {}).get('classes', 0),
                reverse=True
            )[:5]  # Top 5 most complex modules
            
            ai_insights = []
            for module in top_modules:
                try:
                    insight = self.analyze_module_with_ai(module)
                    if insight:
                        ai_insights.append(insight)
                except Exception as e:
                    self.logger.warning(f"Failed to analyze module {module.get('name')}: {e}")
            
            enhanced['ai_insights'] = {
                'module_insights': ai_insights,
                'total_analyzed': len(ai_insights),
                'analysis_timestamp': self._get_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Code analysis enhancement failed: {e}")
            enhanced['ai_enhancement'] = {'enabled': True, 'error': str(e)}
        
        return enhanced
    
    def enhance_quality_analysis(self, quality_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance quality analysis with AI insights.
        
        Args:
            quality_analysis: Original quality analysis results
            
        Returns:
            Enhanced quality analysis with AI insights
        """
        enhanced = quality_analysis.copy()
        
        if not self.openai_enabled:
            return enhanced
        
        try:
            # Generate quality improvement recommendations
            recommendations = self.generate_quality_recommendations(quality_analysis)
            enhanced['ai_recommendations'] = recommendations
            
            # Analyze quality patterns
            patterns = self.analyze_quality_patterns(quality_analysis)
            enhanced['quality_patterns'] = patterns
            
        except Exception as e:
            self.logger.error(f"Quality analysis enhancement failed: {e}")
        
        return enhanced
    
    def analyze_module_with_ai(self, module: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a single module using AI.
        
        Args:
            module: Module analysis data
            
        Returns:
            AI analysis insights or None if failed
        """
        if not self.client:
            return None
        
        try:
            # Prepare module summary for AI analysis
            module_summary = {
                'name': module.get('name', 'Unknown'),
                'type': module.get('type', 'module'),
                'functions': len(module.get('functions', [])),
                'classes': len(module.get('classes', [])),
                'lines': module.get('stats', {}).get('lines', 0),
                'description': module.get('description', 'No description')
            }
            
            prompt = f"""
Analyze this Python module and provide insights:

Module: {module_summary['name']}
Type: {module_summary['type']}
Functions: {module_summary['functions']}
Classes: {module_summary['classes']}
Lines of Code: {module_summary['lines']}
Description: {module_summary['description']}

Please provide:
1. Purpose and responsibility assessment
2. Code organization quality
3. Potential improvements
4. Design pattern suggestions

Keep response concise (max 200 words).
"""
            
            response = self.client.chat.completions.create(
                model=self.llm_config.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are a senior software architect analyzing Python code modules."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            analysis_text = response.choices[0].message.content
            
            return {
                'module_name': module_summary['name'],
                'ai_analysis': analysis_text,
                'timestamp': self._get_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"AI module analysis failed: {e}")
            return None
    
    def generate_quality_recommendations(self, quality_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI-powered quality improvement recommendations.
        
        Args:
            quality_analysis: Quality analysis results
            
        Returns:
            Quality improvement recommendations
        """
        if not self.client:
            return {'enabled': False}
        
        try:
            overview = quality_analysis.get('overview', {})
            distribution = quality_analysis.get('quality_distribution', {})
            
            prompt = f"""
Based on this code quality analysis, provide improvement recommendations:

Average Quality Score: {overview.get('average_quality_score', 0):.3f}
Total Modules: {overview.get('total_modules', 0)}
Quality Distribution: {json.dumps(distribution.get('quality_ranges', {}), indent=2)}

Provide 5 specific, actionable recommendations to improve code quality.
Format as a numbered list.
"""
            
            response = self.client.chat.completions.create(
                model=self.llm_config.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are a code quality expert providing improvement recommendations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=400
            )
            
            recommendations_text = response.choices[0].message.content
            
            # Parse recommendations into list
            recommendations = []
            for line in recommendations_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Clean up the recommendation text
                    clean_rec = line.lstrip('0123456789.-• ').strip()
                    if clean_rec:
                        recommendations.append(clean_rec)
            
            return {
                'enabled': True,
                'recommendations': recommendations,
                'raw_response': recommendations_text,
                'timestamp': self._get_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Quality recommendations generation failed: {e}")
            return {'enabled': True, 'error': str(e)}
    
    def analyze_quality_patterns(self, quality_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze quality patterns in the codebase.
        
        Args:
            quality_analysis: Quality analysis results
            
        Returns:
            Quality pattern analysis
        """
        patterns = {
            'high_quality_modules': [],
            'low_quality_modules': [],
            'common_issues': [],
            'quality_trends': {}
        }
        
        try:
            assessments = quality_analysis.get('module_assessments', {})
            
            # Identify high and low quality modules
            sorted_modules = sorted(
                assessments.items(),
                key=lambda x: x[1].get('overall_score', 0),
                reverse=True
            )
            
            # Top 3 highest quality modules
            patterns['high_quality_modules'] = [
                {
                    'module': module_path,
                    'score': assessment.get('overall_score', 0),
                    'grade': assessment.get('grade', 'F')
                }
                for module_path, assessment in sorted_modules[:3]
            ]
            
            # Bottom 3 lowest quality modules
            patterns['low_quality_modules'] = [
                {
                    'module': module_path,
                    'score': assessment.get('overall_score', 0),
                    'grade': assessment.get('grade', 'F')
                }
                for module_path, assessment in sorted_modules[-3:]
            ]
            
            # Analyze common issues
            all_issues = []
            for assessment in assessments.values():
                all_issues.extend(assessment.get('issues', []))
            
            # Count issue types
            issue_counts = {}
            for issue in all_issues:
                issue_type = issue.get('type', 'unknown')
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
            
            patterns['common_issues'] = [
                {'type': issue_type, 'count': count}
                for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
            ][:5]  # Top 5 most common issues
            
        except Exception as e:
            self.logger.error(f"Quality pattern analysis failed: {e}")
            patterns['error'] = str(e)
        
        return patterns
    
    def generate_ai_insights(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate general AI insights about the codebase.
        
        Args:
            analysis_data: Combined analysis results
            
        Returns:
            AI-generated insights
        """
        insights = {
            'insights': [],
            'summary': '',
            'enabled': self.openai_enabled
        }
        
        if not self.client:
            return insights
        
        try:
            # Generate high-level codebase insights
            code_analysis = analysis_data.get('code_analysis', {})
            overview = code_analysis.get('overview', {})
            
            prompt = f"""
Analyze this codebase and provide key insights:

Total Files: {overview.get('total_files', 0)}
Total Functions: {overview.get('total_functions', 0)}
Total Classes: {overview.get('total_classes', 0)}
Project Type: {overview.get('project_type', 'Unknown')}
Languages: {', '.join(overview.get('languages_detected', []))}

Provide 3-5 key insights about the codebase architecture, organization, and potential areas for improvement.
"""
            
            response = self.client.chat.completions.create(
                model=self.llm_config.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are a software architecture analyst providing codebase insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            insights_text = response.choices[0].message.content
            
            # Parse insights
            insight_list = []
            for line in insights_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    clean_insight = line.lstrip('0123456789.-• ').strip()
                    if clean_insight:
                        insight_list.append(clean_insight)
            
            insights['insights'] = insight_list
            insights['summary'] = insights_text[:200] + '...' if len(insights_text) > 200 else insights_text
            
        except Exception as e:
            self.logger.error(f"AI insights generation failed: {e}")
            insights['error'] = str(e)
        
        return insights
    
    def generate_architecture_recommendations(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate architecture improvement recommendations.
        
        Args:
            analysis_data: Combined analysis results
            
        Returns:
            Architecture recommendations
        """
        recommendations = {
            'recommendations': [],
            'enabled': self.openai_enabled
        }
        
        if not self.client:
            return recommendations
        
        try:
            # Analyze architecture for recommendations
            code_analysis = analysis_data.get('code_analysis', {})
            modules = code_analysis.get('modules', [])
            
            # Simple heuristics for architecture analysis
            arch_insights = []
            
            # Check for large modules
            large_modules = [m for m in modules if m.get('stats', {}).get('lines', 0) > 500]
            if large_modules:
                arch_insights.append(f"Consider breaking down {len(large_modules)} large modules (>500 lines)")
            
            # Check for modules with many functions
            complex_modules = [m for m in modules if m.get('stats', {}).get('functions', 0) > 20]
            if complex_modules:
                arch_insights.append(f"Consider refactoring {len(complex_modules)} modules with many functions (>20)")
            
            # Check for missing documentation
            undocumented = [m for m in modules if not m.get('description')]
            if undocumented:
                arch_insights.append(f"Add documentation to {len(undocumented)} modules")
            
            recommendations['recommendations'] = arch_insights
            
        except Exception as e:
            self.logger.error(f"Architecture recommendations failed: {e}")
            recommendations['error'] = str(e)
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
