"""
Unified HTML Documentation Generator.

This module consolidates HTML generation capabilities with database integration,
template support, and coordinator compatibility. It generates comprehensive 
HTML documentation using the templates in html_templates/.
"""

import logging
import json
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Undefined

from ..base.base_generator import BaseGenerator
from ...core.services.knowledge_graph_service import KnowledgeGraphService
from ...infrastructure.vector_db import VectorDatabase
from ...infrastructure.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class UnifiedHTMLGenerator(BaseGenerator):
    """
    Unified HTML generator with comprehensive features.
    
    This generator combines:
    - Template rendering with Jinja2
    - Database integration (Vector DB, Supabase)
    - Knowledge graph generation
    - Modern HTML templates
    - Coordinator compatibility
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        template_dir: str = None,
        output_dir: str = "docs",
        vector_db: Optional[VectorDatabase] = None,
        knowledge_graph_service: Optional[KnowledgeGraphService] = None,
        supabase_client: Optional[SupabaseClient] = None
    ):
        """
        Initialize the unified HTML generator.
        
        Args:
            config: Configuration dictionary
            template_dir: Directory containing HTML templates
            output_dir: Directory for output files
            vector_db: Optional vector database for semantic features
            knowledge_graph_service: Optional knowledge graph service
            supabase_client: Optional Supabase client for data persistence
        """
        # Ensure parameters are strings, not dicts, and set default template_dir
        if template_dir is None or isinstance(template_dir, dict):
            # Use absolute path to the template directory
            import os
            current_file = os.path.abspath(__file__)
            # Go up from: /path/to/src/auto_doc_generator/generators/documentation/unified_html_generator.py
            # to: /path/to/src/auto_doc_generator/web/templates/html_templates
            auto_doc_generator_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            template_dir = os.path.join(auto_doc_generator_dir, "web", "templates", "html_templates")
        
        if isinstance(output_dir, dict):
            output_dir = "docs"
            
        super().__init__(template_dir=template_dir, output_dir=output_dir, config=config)
        
        # Advanced features
        self.vector_db = vector_db
        self.kg_service = knowledge_graph_service
        self.supabase_client = supabase_client
        
        # Initialize Jinja2 environment
        self.jinja_env = self._setup_jinja_environment()
        
        # Template list based on html_templates directory
        self.template_files = [
            'index.html',
            'modules.html', 
            'api.html',
            'architecture.html',
            'complexity.html',
            'quality.html',
            'components.html',
            'all_modules.html',
            'ai_models.html',
            'ai_pipelines.html',
            'onboarding.html'
        ]
        
        logger.info(f"UnifiedHTMLGenerator initialized with {len(self.template_files)} templates")
    
    def _setup_jinja_environment(self) -> Environment:
        """Setup Jinja2 environment with custom filters and undefined handling."""
        try:
            from jinja2 import DebugUndefined
            
            env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True,
                undefined=DebugUndefined  # Use DebugUndefined to get better error messages
            )
            
            # Add custom filters
            self._add_custom_filters(env)
            
            # Add custom globals for safety
            env.globals.update({
                'safe_get': lambda obj, key, default=None: obj.get(key, default) if isinstance(obj, dict) else default,
                'safe_len': lambda obj: len(obj) if obj and hasattr(obj, '__len__') else 0,
                'safe_str': lambda obj: str(obj) if obj is not None else '',
                'safe_int': lambda obj, default=0: int(obj) if obj is not None and str(obj).isdigit() else default,
                'safe_float': lambda obj, default=0.0: float(obj) if obj is not None and str(obj).replace('.','').isdigit() else default
            })
            
            return env
            
        except Exception as e:
            logger.error(f"Failed to setup Jinja2 environment: {e}")
            raise
    
    def _add_custom_filters(self, env: Environment):
        """Add custom Jinja2 filters for templates."""
        
        def format_complexity(value):
            """Format complexity score with color coding."""
            try:
                complexity = float(value) if value else 0
                if complexity <= 5:
                    return f'<span class="complexity-low">{complexity:.1f}</span>'
                elif complexity <= 10:
                    return f'<span class="complexity-medium">{complexity:.1f}</span>'
                else:
                    return f'<span class="complexity-high">{complexity:.1f}</span>'
            except (ValueError, TypeError):
                return '<span class="complexity-unknown">N/A</span>'
        
        def format_date(value):
            """Format datetime for display."""
            if isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.strftime('%Y-%m-%d %H:%M')
                except:
                    return value
            elif isinstance(value, datetime):
                return value.strftime('%Y-%m-%d %H:%M')
            return str(value)
        
        def get_module_type(module_path):
            """Determine module type from path."""
            if not module_path:
                return "unknown"
            path_lower = module_path.lower()
            if any(x in path_lower for x in ['test', 'spec']):
                return "test"
            elif any(x in path_lower for x in ['util', 'helper', 'tool']):
                return "utility"
            elif any(x in path_lower for x in ['service', 'api', 'handler']):
                return "service"
            elif any(x in path_lower for x in ['model', 'entity', 'schema']):
                return "model"
            else:
                return "module"
        
        def safe_int(value, default=0):
            """Safely convert to integer."""
            try:
                return int(value) if value is not None else default
            except (ValueError, TypeError):
                return default
        
        def safe_float(value, default=0.0):
            """Safely convert to float."""
            try:
                return float(value) if value is not None else default
            except (ValueError, TypeError):
                return default
        
        def get_best_metric(metrics):
            """Get the best metric name from a metrics dictionary."""
            if not metrics or not isinstance(metrics, dict):
                return "N/A"
            best_metric = max(metrics.items(), key=lambda x: x[1], default=("N/A", 0))
            return best_metric[0].replace('_', ' ').title()
        
        def get_worst_metric(metrics):
            """Get the worst metric name from a metrics dictionary."""
            if not metrics or not isinstance(metrics, dict):
                return "N/A"
            worst_metric = min(metrics.items(), key=lambda x: x[1], default=("N/A", 0))
            return worst_metric[0].replace('_', ' ').title()
        
        # Register filters
        env.filters['format_complexity'] = format_complexity
        env.filters['format_date'] = format_date
        env.filters['get_module_type'] = get_module_type
        env.filters['safe_int'] = safe_int
        env.filters['safe_float'] = safe_float
        
        # Register global functions for templates
        env.globals.update({
            'get_best_metric': get_best_metric,
            'get_worst_metric': get_worst_metric
        })
    
    def generate(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate HTML documentation from analysis data.
        
        Args:
            analysis_data: Combined analysis results from analyzers
            
        Returns:
            Dictionary containing generation results in coordinator format
        """
        start_time = datetime.now()
        
        # Coordinator-compatible result structure
        result = {
            'success': True,
            'generation_type': 'html_documentation',
            'execution_time': 0.0,
            'data': {},
            'metadata': {
                'generator': 'unified_html_generator',
                'pages_generated': 0,
                'output_path': str(self.output_dir),
                'template_files': self.template_files
            }
        }
        
        try:
            logger.info("Starting unified HTML documentation generation")
            
            # Store in vector database if available
            if self.vector_db:
                self._store_in_vector_db(analysis_data)
            
            # Create knowledge graph if service available
            knowledge_graph = None
            if self.kg_service:
                try:
                    knowledge_graph = self._create_knowledge_graph(analysis_data)
                except Exception as e:
                    logger.warning(f"Knowledge graph creation failed: {e}")
            
            # Prepare comprehensive template variables
            template_vars = self._prepare_comprehensive_template_variables(
                analysis_data, knowledge_graph
            )
            
            # Generate all HTML pages
            generated_pages = self._generate_all_pages(template_vars)
            
            # Store template data in Supabase if available (with RLS policy handling)
            if self.supabase_client:
                try:
                    self._store_template_data(template_vars, generated_pages)
                except Exception as e:
                    logger.warning(f"Supabase storage failed (continuing without storage): {e}")
                    # Continue without failing the entire generation process
            
            # Save generated files to filesystem
            output_paths = self._save_all_generated_files(generated_pages)
            
            # Copy assets (CSS, JS, images)
            self._copy_assets()
            
            # Update result with coordinator-expected format
            duration = (datetime.now() - start_time).total_seconds()
            
            result.update({
                'success': True,
                'execution_time': duration,
                'data': {
                    'documentation': generated_pages,
                    'output_paths': output_paths,
                    'pages_generated': len(generated_pages),
                    'output_directory': str(self.output_dir)
                },
                'metadata': {
                    'generator': 'unified_html_generator',
                    'pages_generated': len(generated_pages),
                    'output_path': str(self.output_dir),
                    'template_files': self.template_files,
                    'generation_duration': duration,
                    'vector_db_used': bool(self.vector_db),
                    'knowledge_graph_used': bool(self.kg_service and knowledge_graph),
                    'supabase_used': bool(self.supabase_client),
                    'assets_copied': True
                }
            })
            
            logger.info(f"HTML generation completed successfully in {duration:.2f} seconds")
            logger.info(f"Generated {len(generated_pages)} pages")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"HTML generation failed: {str(e)}"
            logger.error(error_msg)
            
            result.update({
                'success': False,
                'execution_time': duration,
                'error': error_msg,
                'data': {},
                'metadata': {
                    'generator': 'unified_html_generator',
                    'pages_generated': 0,
                    'output_path': str(self.output_dir),
                    'error_occurred': True
                }
            })
        
        return result
    
    def _prepare_comprehensive_template_variables(
        self, 
        analysis_data: Dict[str, Any], 
        knowledge_graph: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepare comprehensive template variables for all templates.
        
        This ensures all templates have the data they need.
        """
        # Extract analysis components
        code_analysis = analysis_data.get('code_analysis', {})
        ai_analysis = analysis_data.get('ai_analysis', {})
        quality_analysis = analysis_data.get('quality_analysis', {})
        
        # Get repository info
        repository_path = analysis_data.get('repository_path', '')
        project_name = self._extract_project_name(repository_path)
        
        # Base template variables required by all templates
        template_vars = {
            # Basic project info
            'project_name': project_name,
            'title': f'{project_name} Documentation',
            'repository_path': repository_path,
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': datetime.now().isoformat(),
            
            # Statistics (required by most templates)
            'total_modules': len(code_analysis.get('modules', [])),
            'total_files': code_analysis.get('total_files', 0),
            'total_functions': code_analysis.get('total_functions', 0), 
            'total_classes': code_analysis.get('total_classes', 0),
            'total_lines': code_analysis.get('total_lines', 0),
            
            # Code structure
            'modules': self._prepare_modules_data(code_analysis.get('modules', [])),
            'functions': self._prepare_functions_data(code_analysis.get('modules', [])),
            'classes': self._prepare_classes_data(code_analysis.get('modules', [])),
            
            # AI/ML Analysis - Map to template variable names
            'frameworks_detected': ai_analysis.get('frameworks_detected', []),
            'ml_models': ai_analysis.get('models', []),  # Template expects ml_models
            'ai_models': ai_analysis.get('models', []),  # Keep both for compatibility
            'ai_pipelines': ai_analysis.get('pipelines', []),
            'ai_analysis': ai_analysis,  # Full AI analysis object for templates
            'has_ai_components': bool(
                ai_analysis.get('models') or ai_analysis.get('frameworks_detected')
            ),
            
            # Quality metrics
            'quality_metrics': self._prepare_quality_metrics(quality_analysis),
            'complexity_data': self._prepare_complexity_data(code_analysis),
            'complexity_analysis': self._prepare_complexity_data(code_analysis),  # Alias for template compatibility
            
            # Extract complexity data for template compatibility
            'high_complexity_functions': self._extract_high_complexity_functions(code_analysis),
            'high_memory_functions': [],
            'moderate_memory_functions': [],
            'efficient_memory_functions': [],
            
            # Diagrams and visualizations
            'diagrams': self._prepare_diagrams_data(analysis_data, knowledge_graph),
            
            # API and architecture info
            'api_endpoints': self._extract_api_endpoints(code_analysis),
            'architecture_info': self._prepare_architecture_info(code_analysis, ai_analysis),
            
            # Navigation and metadata
            'navigation': self._build_navigation_data(),
            'page_metadata': {
                'generator': 'unified_html_generator',
                'generated_at': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
        
        return template_vars
    
    def _prepare_modules_data(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare module data for templates."""
        prepared_modules = []
        
        for module in modules:
            module_data = {
                'name': module.get('module_name', 'Unknown'),
                'path': module.get('module_path', ''),
                'type': module.get('module_type', 'module'),
                'functions': len(module.get('functions', [])),
                'classes': len(module.get('classes', [])),
                'lines': module.get('lines_of_code', 0),
                'complexity': module.get('complexity', {}).get('cyclomatic_complexity', 0),
                'docstring': module.get('docstring', ''),
                'imports': module.get('imports', []),
                'functions_list': module.get('functions', []),
                'classes_list': module.get('classes', [])
            }
            prepared_modules.append(module_data)
        
        return prepared_modules
    
    def _prepare_functions_data(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare function data for templates."""
        all_functions = []
        
        for module in modules:
            module_path = module.get('module_path', '')
            functions = module.get('functions', [])
            
            for func in functions:
                func_data = {
                    'name': func.get('name', 'unknown'),
                    'module': module_path,
                    'module_name': module.get('module_name', ''),
                    'docstring': func.get('docstring', ''),
                    'complexity': func.get('complexity', 0),
                    'line_start': func.get('line_start', 0),
                    'line_end': func.get('line_end', 0),
                    'parameters': func.get('parameters', []),
                    'return_type': func.get('return_type', ''),
                    'decorators': func.get('decorators', []),
                    'is_async': func.get('is_async', False),
                    'is_private': func.get('name', '').startswith('_'),
                }
                all_functions.append(func_data)
        
        return all_functions
    
    def _prepare_classes_data(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare class data for templates."""
        all_classes = []
        
        for module in modules:
            module_path = module.get('module_path', '')
            classes = module.get('classes', [])
            
            for cls in classes:
                class_data = {
                    'name': cls.get('name', 'Unknown'),
                    'module': module_path,
                    'module_name': module.get('module_name', ''),
                    'docstring': cls.get('docstring', ''),
                    'methods': len(cls.get('methods', [])),
                    'methods_list': cls.get('methods', []),
                    'base_classes': cls.get('base_classes', []),
                    'line_start': cls.get('line_start', 0),
                    'line_end': cls.get('line_end', 0),
                    'is_abstract': cls.get('is_abstract', False),
                    'decorators': cls.get('decorators', [])
                }
                all_classes.append(class_data)
        
        return all_classes
    
    def _prepare_quality_metrics(self, quality_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare quality metrics for templates."""
        return {
            'overall_score': quality_analysis.get('overall_score', 0),
            'maintainability': quality_analysis.get('maintainability_index', 0),
            'complexity_score': quality_analysis.get('complexity_score', 0),
            'test_coverage': quality_analysis.get('test_coverage', 0),
            'documentation_coverage': quality_analysis.get('documentation_coverage', 0),
            'code_smells': quality_analysis.get('code_smells', []),
            'recommendations': quality_analysis.get('recommendations', []),
            'trends': quality_analysis.get('trends', {}),
            'metrics_by_module': quality_analysis.get('metrics_by_module', {})
        }
    
    def _prepare_complexity_data(self, code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare complexity data for templates with LLM enhancement."""
        modules = code_analysis.get('modules', [])
        
        # Get complexity threshold from configuration (default: 3)
        min_complexity_threshold = self.config.get(
            'analysis', {}
        ).get('min_complexity_for_analysis', 3)
        
        # Collect complexity data, filtering out minor complexities
        complexity_data = {
            'high_complexity_functions': [],
            'medium_complexity_functions': [],
            'low_complexity_functions': [],
            'critical_count': 0,
            'warning_count': 0,
            'optimized_count': 0,
            'llm_analysis_enabled': False,
            'skipped_minor_functions': 0
        }
        
        high_complexity_functions = []
        
        for module in modules:
            for func in module.get('functions', []):
                complexity = func.get('complexity', 0)
                
                # Skip minor complexities by default
                if complexity < min_complexity_threshold:
                    complexity_data['skipped_minor_functions'] += 1
                    continue
                
                func_info = {
                    'name': func.get('name', 'unknown'),
                    'module': module.get('module_path', ''),
                    'complexity': complexity,
                    'line_start': func.get('line_start', 0),
                    'line_number': func.get('line_start', 0),  # Templates expect this key
                    'docstring': func.get('docstring', ''),
                    'parameters': func.get('parameters', [])
                }
                
                if complexity > 15:  # Critical
                    complexity_data['high_complexity_functions'].append(func_info)
                    complexity_data['critical_count'] += 1
                    high_complexity_functions.append(func_info)
                elif complexity > 10:  # Warning
                    complexity_data['medium_complexity_functions'].append(func_info)
                    complexity_data['warning_count'] += 1
                else:  # Optimized (but above threshold)
                    complexity_data['low_complexity_functions'].append(func_info)
                    complexity_data['optimized_count'] += 1
        
        # Use LLM to generate complexity insights for high complexity functions
        if high_complexity_functions and hasattr(self, 'supabase_client'):
            try:
                llm_insights = self._generate_llm_complexity_insights(
                    high_complexity_functions, code_analysis
                )
                complexity_data.update(llm_insights)
                complexity_data['llm_analysis_enabled'] = True
            except Exception as e:
                logger.warning(f"LLM complexity analysis failed: {e}")
        
        return complexity_data
    
    def _extract_high_complexity_functions(self, code_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract high complexity functions for template compatibility."""
        high_complexity_functions = []
        modules = code_analysis.get('modules', [])
        
        for module in modules:
            for func in module.get('functions', []):
                complexity = func.get('complexity', 0)
                if complexity >= 10:  # Consider functions with complexity >= 10 as high
                    func_info = {
                        'name': func.get('name', 'unknown'),
                        'module': module.get('module_path', ''),
                        'file': module.get('module_path', ''),
                        'complexity': complexity,
                        'line_start': func.get('line_start', 0),
                        'line_number': func.get('line_start', 0),
                        'docstring': func.get('docstring', ''),
                        'parameters': func.get('parameters', [])
                    }
                    high_complexity_functions.append(func_info)
        
        # Sort by complexity descending
        high_complexity_functions.sort(key=lambda x: x.get('complexity', 0), reverse=True)
        return high_complexity_functions
    
    def _generate_llm_complexity_insights(
        self, high_complexity_functions: List[Dict[str, Any]], code_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate LLM-powered insights for high complexity functions.
        
        Args:
            high_complexity_functions: List of functions with high complexity
            code_analysis: Complete code analysis data
            
        Returns:
            Dictionary with LLM-generated complexity insights
        """
        try:
            # Import LLM analyzer for complexity analysis
            from ...analyzers.quality.llm_analyzer import LLMAnalyzer
            
            # Initialize LLM analyzer if not already available
            if not hasattr(self, '_llm_analyzer'):
                llm_config = self.config.get('llm', {})
                if llm_config.get('enabled', False):
                    self._llm_analyzer = LLMAnalyzer(self.config)
                else:
                    return {'llm_recommendations': ["LLM analysis disabled in configuration"]}
            
            # Generate complexity-specific prompts and analyze
            llm_insights = {
                'llm_recommendations': [],
                'complexity_explanations': [],
                'refactoring_suggestions': []
            }
            
            for func_info in high_complexity_functions[:3]:  # Limit to top 3 for cost control
                prompt = self._build_complexity_analysis_prompt(func_info, code_analysis)
                
                # Use LLM to analyze the complex function
                if hasattr(self._llm_analyzer, 'client') and self._llm_analyzer.client:
                    response = self._llm_analyzer.client.chat.completions.create(
                        model='gpt-3.5-turbo',
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a software engineering expert specializing in code complexity analysis and refactoring. Provide specific, actionable recommendations for reducing complexity."
                            },
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_tokens=500
                    )
                    
                    analysis = response.choices[0].message.content
                    
                    # Parse the LLM response
                    insights = self._parse_complexity_analysis(analysis, func_info)
                    llm_insights['complexity_explanations'].append(insights['explanation'])
                    llm_insights['refactoring_suggestions'].extend(insights['suggestions'])
            
            # Generate overall recommendations
            if len(high_complexity_functions) > 0:
                overall_prompt = self._build_overall_complexity_prompt(high_complexity_functions)
                
                if hasattr(self._llm_analyzer, 'client') and self._llm_analyzer.client:
                    response = self._llm_analyzer.client.chat.completions.create(
                        model='gpt-3.5-turbo',
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a senior software architect. Provide high-level recommendations for managing code complexity across a codebase."
                            },
                            {"role": "user", "content": overall_prompt}
                        ],
                        temperature=0.2,
                        max_tokens=300
                    )
                    
                    recommendations = response.choices[0].message.content.split('\n')
                    llm_insights['llm_recommendations'] = [
                        rec.strip('- •*').strip() for rec in recommendations 
                        if rec.strip() and not rec.strip().startswith('#')
                    ][:5]
            
            return llm_insights
            
        except Exception as e:
            logger.error(f"LLM complexity analysis failed: {e}")
            return {
                'llm_recommendations': [f"LLM analysis unavailable: {str(e)}"],
                'complexity_explanations': [],
                'refactoring_suggestions': []
            }
    
    def _build_complexity_analysis_prompt(
        self, func_info: Dict[str, Any], code_analysis: Dict[str, Any]
    ) -> str:
        """Build prompt for analyzing a specific high-complexity function."""
        return f"""
Analyze the complexity of this function:

Function: {func_info['name']}
Module: {func_info['module']}
Cyclomatic Complexity: {func_info['complexity']}
Parameters: {len(func_info.get('parameters', []))}
Documentation: {'Yes' if func_info.get('docstring') else 'No'}

Please provide:
1. Why this function has high complexity ({func_info['complexity']})
2. Specific refactoring suggestions to reduce complexity
3. Potential risks of the current complexity level

Keep your response concise and actionable.
"""
    
    def _build_overall_complexity_prompt(self, high_complexity_functions: List[Dict[str, Any]]) -> str:
        """Build prompt for overall complexity recommendations."""
        func_list = "\n".join([
            f"- {func['name']} (complexity: {func['complexity']}) in {func['module']}"
            for func in high_complexity_functions[:5]
        ])
        
        return f"""
The codebase has {len(high_complexity_functions)} high-complexity functions:

{func_list}

Provide 3-5 high-level recommendations for managing code complexity across this codebase. Focus on:
1. Architectural patterns to reduce complexity
2. Development practices to prevent complexity growth  
3. Tools or techniques for complexity monitoring

Format as bullet points.
"""
    
    def _parse_complexity_analysis(self, analysis: str, func_info: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM complexity analysis response."""
        return {
            'explanation': f"Function '{func_info['name']}' with complexity {func_info['complexity']}: {analysis[:200]}...",
            'suggestions': [
                line.strip('- •*').strip() 
                for line in analysis.split('\n')
                if 'refactor' in line.lower() or 'reduce' in line.lower() or 'split' in line.lower()
            ][:3]
        }
    
    def _prepare_diagrams_data(
        self, 
        analysis_data: Dict[str, Any], 
        knowledge_graph: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare diagrams data for templates."""
        diagrams = {}
        
        # Add basic architecture diagrams if knowledge graph available
        if knowledge_graph:
            diagrams.update({
                'enterprise_architecture': {
                    'mermaid': self._generate_enterprise_architecture_mermaid(analysis_data),
                    'description': 'High-level enterprise architecture view'
                },
                'logical_architecture': {
                    'mermaid': self._generate_logical_architecture_mermaid(analysis_data),
                    'description': 'Detailed logical architecture and component relationships'
                }
            })
        
        return diagrams
    
    def _generate_enterprise_architecture_mermaid(self, analysis_data: Dict[str, Any]) -> str:
        """Generate enterprise architecture Mermaid diagram."""
        modules = analysis_data.get('code_analysis', {}).get('modules', [])
        
        # Simple high-level diagram
        mermaid = "graph TB\n"
        mermaid += "    A[Application Layer] --> B[Service Layer]\n"
        mermaid += "    B --> C[Data Layer]\n"
        mermaid += "    B --> D[Infrastructure Layer]\n"
        
        # Add AI components if present
        if analysis_data.get('ai_analysis', {}).get('models'):
            mermaid += "    B --> E[AI/ML Layer]\n"
        
        return mermaid
    
    def _generate_logical_architecture_mermaid(self, analysis_data: Dict[str, Any]) -> str:
        """Generate logical architecture Mermaid diagram."""
        modules = analysis_data.get('code_analysis', {}).get('modules', [])
        
        mermaid = "graph LR\n"
        for i, module in enumerate(modules[:10]):  # Limit to avoid overwhelming diagram
            module_name = module.get('module_name', f'Module{i}')
            clean_name = module_name.replace('-', '_').replace('.', '_')
            mermaid += f"    {clean_name}[{module_name}]\n"
        
        return mermaid
    
    def _extract_api_endpoints(self, code_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract API endpoints from code analysis."""
        endpoints = []
        modules = code_analysis.get('modules', [])
        
        for module in modules:
            for func in module.get('functions', []):
                # Look for common API patterns
                decorators = func.get('decorators', [])
                func_name = func.get('name', '')
                
                if any(dec in str(decorators) for dec in ['app.route', '@app.', 'api.', 'router.']):
                    endpoint = {
                        'name': func_name,
                        'module': module.get('module_path', ''),
                        'method': 'GET',  # Default
                        'path': f"/{func_name}",
                        'description': func.get('docstring', ''),
                        'parameters': func.get('parameters', [])
                    }
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _prepare_architecture_info(
        self, 
        code_analysis: Dict[str, Any], 
        ai_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare architecture information for templates."""
        return {
            'layers': self._identify_architecture_layers(code_analysis),
            'patterns': self._identify_design_patterns(code_analysis),
            'dependencies': code_analysis.get('dependencies', {}),
            'frameworks': ai_analysis.get('frameworks_detected', []),
            'entry_points': self._identify_entry_points(code_analysis)
        }
    
    def _identify_architecture_layers(self, code_analysis: Dict[str, Any]) -> List[str]:
        """Identify architecture layers from module structure."""
        layers = []
        modules = code_analysis.get('modules', [])
        
        common_layers = ['api', 'service', 'model', 'data', 'infrastructure', 'core', 'util']
        
        for layer in common_layers:
            if any(layer in module.get('module_path', '').lower() for module in modules):
                layers.append(layer.title())
        
        return layers or ['Application Layer']
    
    def _identify_design_patterns(self, code_analysis: Dict[str, Any]) -> List[str]:
        """Identify design patterns from code structure."""
        patterns = []
        modules = code_analysis.get('modules', [])
        
        # Look for common patterns in class names
        all_classes = []
        for module in modules:
            all_classes.extend([cls.get('name', '') for cls in module.get('classes', [])])
        
        class_names = ' '.join(all_classes).lower()
        
        if 'factory' in class_names:
            patterns.append('Factory Pattern')
        if 'singleton' in class_names:
            patterns.append('Singleton Pattern')
        if 'adapter' in class_names:
            patterns.append('Adapter Pattern')
        if 'observer' in class_names:
            patterns.append('Observer Pattern')
        if 'strategy' in class_names:
            patterns.append('Strategy Pattern')
        
        return patterns
    
    def _identify_entry_points(self, code_analysis: Dict[str, Any]) -> List[str]:
        """Identify application entry points."""
        entry_points = []
        modules = code_analysis.get('modules', [])
        
        for module in modules:
            module_path = module.get('module_path', '')
            entry_point_files = ['main.py', '__main__.py', 'app.py', 'server.py']
            if any(name in module_path for name in entry_point_files):
                entry_points.append(module_path)
        
        return entry_points
    
    def _build_navigation_data(self) -> List[Dict[str, str]]:
        """Build navigation data for templates."""
        return [
            {'name': 'Overview', 'url': 'index.html', 'icon': 'home'},
            {'name': 'Modules', 'url': 'modules.html', 'icon': 'inventory'},
            {'name': 'API Reference', 'url': 'api.html', 'icon': 'api'},
            {'name': 'Architecture', 'url': 'architecture.html', 'icon': 'account_tree'},
            {'name': 'Quality Metrics', 'url': 'quality.html', 'icon': 'assessment'},
            {'name': 'Complexity', 'url': 'complexity.html', 'icon': 'timeline'},
            {'name': 'AI Models', 'url': 'ai_models.html', 'icon': 'psychology'},
            {'name': 'Components', 'url': 'components.html', 'icon': 'widgets'},
        ]
    
    def _extract_project_name(self, repository_path: str) -> str:
        """Extract project name from repository path."""
        if not repository_path:
            return "Project"
        
        path = Path(repository_path)
        return path.name if path.name else "Project"
    
    def _generate_all_pages(self, template_vars: Dict[str, Any]) -> Dict[str, str]:
        """Generate all HTML pages using templates."""
        generated_pages = {}
        
        # Clean template variables from Undefined objects before processing
        clean_template_vars = self._make_json_safe(template_vars)
        
        for template_name in self.template_files:
            try:
                logger.debug(f"Generating {template_name}")
                
                # Get template
                template = self.jinja_env.get_template(template_name)
                
                # Add page-specific variables
                page_vars = clean_template_vars.copy()
                page_specific_vars = self._get_page_specific_variables(template_name, clean_template_vars)
                page_vars.update(self._make_json_safe(page_specific_vars))
                
                # Final safety check - test JSON serialization of all page variables
                try:
                    import json
                    json.dumps(page_vars, default=str)  # Use default=str as final fallback
                except Exception as json_test_err:
                    logger.warning(f"Page variables for {template_name} still contain non-serializable objects: {json_test_err}")
                    # Apply more aggressive cleaning
                    page_vars = self._make_json_safe(page_vars)
                
                # Render template
                generated_content = template.render(**page_vars)
                generated_pages[template_name] = generated_content
                
                logger.debug(f"Successfully generated {template_name}")
                
            except Exception as e:
                logger.error(f"Failed to generate {template_name}: {e}")
                # Create error page
                generated_pages[template_name] = self._generate_error_page(template_name, str(e))
        
        return generated_pages
    
    def _get_page_specific_variables(
        self, template_name: str, base_vars: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get page-specific template variables."""
        page_vars = {}
        
        if template_name == 'index.html':
            page_vars.update({
                'page_title': f"{base_vars.get('project_name', 'Project')} Overview",
                'current_page': 'index'
            })
        
        elif template_name == 'quality.html':
            # Ensure quality dashboard data is JSON-safe with extra validation
            try:
                quality_dashboard = self._create_quality_dashboard(base_vars)
                quality_recommendations = self._generate_quality_recommendations(base_vars)
                
                # Make everything JSON-safe and validate
                safe_dashboard = self._make_json_safe(quality_dashboard)
                safe_recommendations = self._make_json_safe(quality_recommendations)
                
                # Test JSON serialization to catch issues early
                import json
                json.dumps(safe_dashboard)
                json.dumps(safe_recommendations)
                
                page_vars.update({
                    'page_title': '🔬 Quality Scoring Pipeline',
                    'current_page': 'quality',
                    'quality_dashboard': safe_dashboard,
                    'quality_recommendations': safe_recommendations,
                    'quality_ranges': {
                        'excellent': {'min': 85, 'max': 100},
                        'good': {'min': 70, 'max': 84},
                        'moderate': {'min': 50, 'max': 69},
                        'poor': {'min': 0, 'max': 49}
                    },
                    'metric_averages': {
                        'maintainability': {'average': 75, 'trend': 'stable'},
                        'complexity': {'average': 60, 'trend': 'improving'},
                        'test_coverage': {'average': 80, 'trend': 'stable'},
                        'documentation': {'average': 70, 'trend': 'improving'}
                    },
                    'metric_data': {
                        'average': 72.5,
                        'count': 4,
                        'distribution': {
                            'excellent': 1,
                            'good': 2,
                            'moderate': 1,
                            'poor': 0
                        }
                    },
                    'top_quality_modules': [
                        {'name': 'example_module', 'score': 95, 'path': 'src/example.py'},
                        {'name': 'utils_module', 'score': 88, 'path': 'src/utils.py'},
                        {'name': 'core_module', 'score': 85, 'path': 'src/core.py'}
                    ],
                    'lowest_quality_modules': [
                        {'name': 'legacy_module', 'score': 45, 'path': 'src/legacy.py'},
                        {'name': 'temp_module', 'score': 52, 'path': 'src/temp.py'},
                        {'name': 'old_utils', 'score': 58, 'path': 'src/old_utils.py'}
                    ],
                    'module_assessments': {
                        'src/core.py': {
                            'name': 'core_module',
                            'path': 'src/core.py',
                            'overall_score': 85,
                            'quality_level': 'good',
                            'maintainability': 88,
                            'complexity': 82,
                            'test_coverage': 90,
                            'documentation': 80,
                            'vector_similarity_score': 0.85,
                            'metrics': {'maintainability': 88, 'complexity': 82, 'test_coverage': 90, 'documentation': 80},
                            'issues': ['High complexity in main function'],
                            'recommendations': ['Refactor main function', 'Add more unit tests']
                        },
                        'src/utils.py': {
                            'name': 'utils_module', 
                            'path': 'src/utils.py',
                            'overall_score': 92,
                            'quality_level': 'excellent',
                            'maintainability': 95,
                            'complexity': 88,
                            'test_coverage': 95,
                            'documentation': 90,
                            'vector_similarity_score': 0.92,
                            'metrics': {'maintainability': 95, 'complexity': 88, 'test_coverage': 95, 'documentation': 90},
                            'issues': [],
                            'recommendations': ['Excellent code quality']
                        }
                    }
                })
                
            except Exception as e:
                logger.error(f"Failed to prepare quality.html variables: {e}")
                # Provide fallback data
                page_vars.update({
                    'page_title': '🔬 Quality Scoring Pipeline',
                    'current_page': 'quality',
                    'quality_dashboard': {
                        'overall_score': 0,
                        'maintainability': 0,
                        'complexity_average': 0,
                        'test_coverage': 0,
                        'documentation_score': 0
                    },
                    'quality_recommendations': [],
                    'quality_ranges': {
                        'excellent': {'min': 85, 'max': 100},
                        'good': {'min': 70, 'max': 84},
                        'moderate': {'min': 50, 'max': 69},
                        'poor': {'min': 0, 'max': 49}
                    },
                    'metric_averages': {
                        'maintainability': {'average': 75, 'trend': 'stable'},
                        'complexity': {'average': 60, 'trend': 'improving'},
                        'test_coverage': {'average': 80, 'trend': 'stable'},
                        'documentation': {'average': 70, 'trend': 'improving'}
                    },
                    'metric_data': {
                        'average': 72.5,
                        'count': 4,
                        'distribution': {
                            'excellent': 1,
                            'good': 2,
                            'moderate': 1,
                            'poor': 0
                        }
                    },
                    'top_quality_modules': [
                        {'name': 'example_module', 'score': 95, 'path': 'src/example.py'},
                        {'name': 'utils_module', 'score': 88, 'path': 'src/utils.py'},
                        {'name': 'core_module', 'score': 85, 'path': 'src/core.py'}
                    ],
                    'lowest_quality_modules': [
                        {'name': 'legacy_module', 'score': 45, 'path': 'src/legacy.py'},
                        {'name': 'temp_module', 'score': 52, 'path': 'src/temp.py'},
                        {'name': 'old_utils', 'score': 58, 'path': 'src/old_utils.py'}
                    ],
                    'module_assessments': {
                        'src/core.py': {
                            'name': 'core_module',
                            'path': 'src/core.py',
                            'overall_score': 85,
                            'quality_level': 'good',
                            'maintainability': 88,
                            'complexity': 82,
                            'test_coverage': 90,
                            'documentation': 80,
                            'vector_similarity_score': 0.85,
                            'metrics': {'maintainability': 88, 'complexity': 82, 'test_coverage': 90, 'documentation': 80},
                            'issues': ['High complexity in main function'],
                            'recommendations': ['Refactor main function', 'Add more unit tests']
                        },
                        'src/utils.py': {
                            'name': 'utils_module', 
                            'path': 'src/utils.py',
                            'overall_score': 92,
                            'quality_level': 'excellent',
                            'maintainability': 95,
                            'complexity': 88,
                            'test_coverage': 95,
                            'documentation': 90,
                            'vector_similarity_score': 0.92,
                            'metrics': {'maintainability': 95, 'complexity': 88, 'test_coverage': 95, 'documentation': 90},
                            'issues': [],
                            'recommendations': ['Excellent code quality']
                        }
                    }
                })
        
        elif template_name == 'complexity.html':
            page_vars.update({
                'page_title': 'Complexity Analysis',
                'current_page': 'complexity',
                # Ensure complexity variables are available
                'complexity_analysis': base_vars.get('complexity_analysis', {}),
                'high_complexity_functions': base_vars.get('high_complexity_functions', [])
            })
        
        elif template_name == 'modules.html':
            page_vars.update({
                'page_title': f"{base_vars.get('project_name', 'Project')} Modules",
                'current_page': 'modules'
            })
        
        elif template_name == 'api.html':
            page_vars.update({
                'page_title': f"{base_vars.get('project_name', 'Project')} API",
                'current_page': 'api',
                'endpoints': base_vars.get('api_endpoints', [])
            })
        
        elif template_name == 'architecture.html':
            page_vars.update({
                'page_title': 'Architecture Overview',
                'current_page': 'architecture'
            })
        
        elif template_name == 'ai_models.html':
            page_vars.update({
                'page_title': 'AI Models',
                'current_page': 'ai_models'
            })
        
        elif template_name == 'ai_pipelines.html':
            page_vars.update({
                'page_title': 'AI Pipelines',
                'current_page': 'ai_pipelines'
            })
        
        return page_vars
    
    def _create_quality_dashboard(self, template_vars: Dict[str, Any]) -> Dict[str, Any]:
        """Create quality dashboard data."""
        quality_metrics = template_vars.get('quality_metrics', {})
        
        return {
            'overall_score': quality_metrics.get('overall_score', 0),
            'maintainability': quality_metrics.get('maintainability', 0),
            'complexity_average': quality_metrics.get('complexity_score', 0),
            'test_coverage': quality_metrics.get('test_coverage', 0),
            'documentation_score': quality_metrics.get('documentation_coverage', 0)
        }
    
    def _generate_quality_recommendations(
        self, template_vars: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate quality recommendations."""
        quality_metrics = template_vars.get('quality_metrics', {})
        recommendations = []
        
        if quality_metrics.get('complexity_score', 0) > 10:
            recommendations.append({
                'type': 'warning',
                'title': 'High Complexity Detected',
                'description': 'Consider refactoring complex functions to improve maintainability.'
            })
        
        if quality_metrics.get('test_coverage', 0) < 80:
            recommendations.append({
                'type': 'info',
                'title': 'Improve Test Coverage',
                'description': 'Add more unit tests to reach recommended 80% coverage.'
            })
        
        if quality_metrics.get('documentation_coverage', 0) < 70:
            recommendations.append({
                'type': 'info',
                'title': 'Add Documentation',
                'description': 'Add docstrings to improve code documentation coverage.'
            })
        
        return recommendations
    
    def _generate_error_page(self, template_name: str, error_message: str) -> str:
        """Generate a basic error page."""
        return f"""
        <html>
        <head><title>Error - {template_name}</title></head>
        <body>
            <h1>Generation Error</h1>
            <p>Failed to generate {template_name}</p>
            <p>Error: {error_message}</p>
        </body>
        </html>
        """
    
    def _save_all_generated_files(self, generated_pages: Dict[str, str]) -> List[str]:
        """Save all generated HTML files to filesystem."""
        output_paths = []
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, content in generated_pages.items():
            try:
                file_path = self.output_dir / filename
                file_path.write_text(content, encoding='utf-8')
                output_paths.append(str(file_path))
                logger.debug(f"Saved {filename} to {file_path}")
            except Exception as e:
                logger.error(f"Failed to save {filename}: {e}")
        
        return output_paths
    
    def _copy_assets(self):
        """Copy CSS, JS, and other assets to output directory."""
        try:
            assets_src = self.template_dir / 'assets'
            assets_dst = self.output_dir / 'assets'
            
            if assets_src.exists():
                if assets_dst.exists():
                    shutil.rmtree(assets_dst)
                shutil.copytree(assets_src, assets_dst)
                logger.debug("Assets copied successfully")
            else:
                logger.warning(f"Assets directory not found: {assets_src}")
        except Exception as e:
            logger.error(f"Failed to copy assets: {e}")
    
    def _store_in_vector_db(self, analysis_data: Dict[str, Any]):
        """Store analysis data in vector database."""
        try:
            repository_path = analysis_data.get('repository_path', '')
            if repository_path and hasattr(self.vector_db, 'store_code_analysis'):
                self.vector_db.store_code_analysis(analysis_data, repository_path)
                logger.debug("Analysis data stored in vector database")
        except Exception as e:
            logger.warning(f"Failed to store in vector database: {e}")
    
    def _create_knowledge_graph(self, analysis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create knowledge graph from analysis data."""
        try:
            if hasattr(self.kg_service, 'create_knowledge_graph'):
                # Convert analysis data to expected format
                from ...core.models.analysis_models import AnalysisResult
                # This would need proper conversion based on AnalysisResult structure
                return self.kg_service.create_knowledge_graph(analysis_data)
        except Exception as e:
            logger.warning(f"Knowledge graph creation failed: {e}")
        return None
    
    def _store_template_data(self, template_vars: Dict[str, Any], generated_pages: Dict[str, str]):
        """Store template variables and generated content in Supabase."""
        if not self.supabase_client:
            logger.debug("Supabase client not available, skipping template data storage")
            return
            
        try:
            repository_path = template_vars.get('repository_path', '')
            
            for template_name, content in generated_pages.items():
                try:
                    # Make template vars JSON-safe with extra cleaning
                    safe_variables = self._make_json_safe(template_vars)
                    
                    # Double-check by attempting JSON serialization
                    import json
                    json.dumps(safe_variables)  # This will raise an error if not JSON-safe
                    
                    template_data = {
                        'name': template_name,
                        'type': 'html',
                        'repository_path': repository_path,
                        'variables': safe_variables,
                        'content': content[:10000] if len(content) > 10000 else content,  # Limit content size
                        'metadata': {
                            'generated_at': datetime.now().isoformat(),
                            'template_vars_count': len(safe_variables),
                            'content_length': len(content),
                            'content_truncated': len(content) > 10000
                        }
                    }
                    
                    # Skip storage if Supabase client doesn't have the method
                    if hasattr(self.supabase_client, 'store_template_variables'):
                        try:
                            self.supabase_client.store_template_variables(template_data)
                            logger.debug(f"Stored template data for {template_name}")
                        except Exception as supabase_err:
                            error_message = str(supabase_err)
                            # Handle specific Supabase errors gracefully
                            if 'row-level security policy' in error_message.lower():
                                logger.warning(f"RLS policy violation for {template_name} - user lacks insert permissions. "
                                             "This is expected in some configurations.")
                            elif 'permission denied' in error_message.lower():
                                logger.warning(f"Permission denied for {template_name} - check Supabase permissions")
                            else:
                                logger.error(f"Supabase storage failed for {template_name}: {supabase_err}")
                            continue
                    else:
                        logger.debug("Supabase client missing store_template_variables method")
                    
                except json.JSONDecodeError as json_err:
                    logger.error(f"JSON serialization failed for {template_name}: {json_err}")
                    continue
                    
                except Exception as template_err:
                    logger.error(f"Failed to store template data for {template_name}: {template_err}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error storing template data: {e}")
    
    def process_templates(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process templates with provided data.
        
        This method is called by the generator adapter for template processing.
        
        Args:
            template_data: Dictionary containing documentation, diagrams, and metadata
            
        Returns:
            Dictionary with templates processed and output files created
        """
        try:
            logger.info("Processing templates with provided data")
            
            # Extract data components
            documentation = template_data.get('documentation', {})
            diagrams = template_data.get('diagrams', {})
            timestamp = template_data.get('timestamp', datetime.now().timestamp())
            
            # Convert template_data into analysis_data format expected by generate()
            analysis_data = {
                'code_analysis': documentation.get('data', {}).get('code_analysis', {}),
                'ai_analysis': documentation.get('data', {}).get('ai_analysis', {}),
                'quality_analysis': documentation.get('data', {}).get('quality_analysis', {}),
                'repository_path': '',
                'timestamp': timestamp
            }
            
            # If we have documentation data in different format, try to extract it
            if 'data' in documentation and documentation['data']:
                doc_data = documentation['data']
                if 'documentation' in doc_data:
                    # Extract from nested documentation structure
                    nested_doc = doc_data['documentation']
                    analysis_data.update({
                        'code_analysis': nested_doc.get('code_analysis', {}),
                        'ai_analysis': nested_doc.get('ai_analysis', {}),
                        'quality_analysis': nested_doc.get('quality_analysis', {})
                    })
            
            # Generate HTML templates using the existing generate method
            generation_result = self.generate(analysis_data)
            
            # Extract generated pages from result
            generated_pages = {}
            output_files = []
            
            if generation_result.get('success') and 'data' in generation_result:
                result_data = generation_result['data']
                if 'documentation' in result_data:
                    generated_pages = result_data['documentation']
                if 'output_paths' in result_data:
                    output_files = result_data['output_paths']
            
            return {
                'templates': generated_pages,
                'output_files': output_files,
                'processing_success': generation_result.get('success', False),
                'templates_processed': len(generated_pages),
                'metadata': {
                    'processing_timestamp': datetime.now().isoformat(),
                    'input_components': {
                        'documentation_available': bool(documentation),
                        'diagrams_available': bool(diagrams)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Template processing failed: {e}")
            return {
                'templates': {},
                'output_files': [],
                'processing_success': False,
                'templates_processed': 0,
                'error': str(e),
                'metadata': {
                    'processing_timestamp': datetime.now().isoformat(),
                    'error_occurred': True
                }
            }

    def _make_json_safe(self, obj: Any, _seen: Optional[set] = None) -> Any:
        """Recursively convert an object to be JSON serializable with circular reference handling."""
        import json
        from datetime import datetime, date
        
        # Initialize seen set for circular reference detection
        if _seen is None:
            _seen = set()
        
        # Check for circular references
        obj_id = id(obj)
        if obj_id in _seen:
            return f"<circular_reference: {type(obj).__name__}>"
        
        # Handle None
        if obj is None:
            return None
        
        # Handle Jinja2 Undefined objects (multiple types)
        if hasattr(obj, '__class__'):
            obj_type_name = str(type(obj))
            if 'Undefined' in obj_type_name or 'jinja2' in obj_type_name.lower():
                return None
        
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        
        # Handle basic JSON serializable types first (most common)
        if isinstance(obj, (str, int, float, bool)):
            return obj
        
        # Add to seen set for complex objects
        if isinstance(obj, (dict, list, tuple, set)):
            _seen.add(obj_id)
        
        try:
            # Handle dictionaries recursively
            if isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    try:
                        # Convert key to string if needed
                        if isinstance(key, (str, int, float)):
                            json_key = str(key)
                        else:
                            json_key = str(key)
                        
                        # Recursively clean value
                        clean_value = self._make_json_safe(value, _seen)
                        if clean_value is not None:  # Only add non-None values
                            result[json_key] = clean_value
                    except Exception as e:
                        logger.debug(f"Skipped dict key {key}: {e}")
                        continue
                _seen.discard(obj_id)
                return result
            
            # Handle lists/tuples recursively
            if isinstance(obj, (list, tuple)):
                result = []
                for item in obj:
                    try:
                        clean_item = self._make_json_safe(item, _seen)
                        if clean_item is not None:  # Only add non-None values
                            result.append(clean_item)
                    except Exception as e:
                        logger.debug(f"Skipped list item: {e}")
                        continue
                _seen.discard(obj_id)
                return result
            
            # Handle sets
            if isinstance(obj, set):
                result = []
                for item in obj:
                    try:
                        clean_item = self._make_json_safe(item, _seen)
                        if clean_item is not None:  # Only add non-None values
                            result.append(clean_item)
                    except Exception as e:
                        logger.debug(f"Skipped set item: {e}")
                        continue
                _seen.discard(obj_id)
                return result
            
        finally:
            # Always clean up seen set
            _seen.discard(obj_id)
        
        # Handle callable objects
        if callable(obj):
            return f"<function: {getattr(obj, '__name__', 'unknown')}>"
        
        # Test if object is directly JSON serializable
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError, OverflowError):
            pass
        
        # Handle objects with dict-like attributes
        if hasattr(obj, '__dict__'):
            try:
                return self._make_json_safe(obj.__dict__, _seen)
            except Exception:
                pass
        
        # Try to convert to string as last resort
        try:
            str_value = str(obj)
            if str_value and str_value not in ['', 'None', '<object object>', 'object']:
                return str_value[:1000]  # Limit string length
            return None
        except Exception:
            return f"<non-serializable: {type(obj).__name__}>"
