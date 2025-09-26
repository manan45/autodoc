"""
Markdown documentation generator.

This module generates Markdown documentation from analysis results
suitable for GitHub, GitLab, and other Markdown-based documentation systems.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from ..base.base_generator import BaseGenerator


class MarkdownGenerator(BaseGenerator):
    """
    Generator that creates Markdown documentation.
    """
    
    def __init__(self, config: Dict[str, Any], output_dir: str = "docs"):
        # Initialize with proper parameter order for BaseGenerator  
        super().__init__(template_dir="markdown_templates", output_dir=output_dir, config=config)
    
    def generate(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Markdown documentation from analysis data.
        
        Args:
            analysis_data: Combined analysis results
            
        Returns:
            Dictionary containing generated documentation
        """
        self.log_generation_start("Markdown Documentation")
        
        result = self.create_result_template()
        result['timestamp'] = datetime.now().isoformat()
        
        try:
            # Extract different types of analysis data
            code_analysis = analysis_data.get('code_analysis', {})
            ai_analysis = analysis_data.get('ai_analysis', {})
            quality_analysis = analysis_data.get('quality_analysis', {})
            
            # Generate different markdown files
            documentation = {}
            
            # Main README
            documentation['README.md'] = self.generate_readme(
                code_analysis, ai_analysis, quality_analysis
            )
            
            # Architecture documentation
            documentation['ARCHITECTURE.md'] = self.generate_architecture_doc(
                code_analysis, ai_analysis
            )
            
            # API reference
            documentation['API.md'] = self.generate_api_doc(code_analysis)
            
            # Quality report
            documentation['QUALITY.md'] = self.generate_quality_doc(quality_analysis)
            
            # AI models documentation
            if ai_analysis.get('models'):
                documentation['AI_MODELS.md'] = self.generate_ai_models_doc(ai_analysis)
            
            result['results'] = {
                'documentation': documentation,
                'pages_generated': len(documentation),
                'output_directory': str(self.output_dir)
            }
            
            self.log_generation_complete("Markdown Documentation", len(documentation))
            
        except Exception as e:
            result['errors'].append(f"Markdown generation failed: {str(e)}")
            self.logger.error(f"Markdown generation error: {e}")
        
        return result
    
    def generate_readme(self, code_analysis: Dict[str, Any], 
                       ai_analysis: Dict[str, Any], 
                       quality_analysis: Dict[str, Any]) -> str:
        """Generate the main README.md file."""
        overview = code_analysis.get('overview', {})
        
        md = f"""# Project Documentation
        
*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## 📊 Project Overview

- **Total Files**: {overview.get('total_files', 0)}
- **Total Lines**: {overview.get('total_lines', 0):,}
- **Total Functions**: {overview.get('total_functions', 0)}
- **Total Classes**: {overview.get('total_classes', 0)}
- **Project Type**: {overview.get('project_type', 'Unknown')}

"""
        
        # Add languages if available
        languages = overview.get('languages_detected', [])
        if languages:
            md += f"- **Languages**: {', '.join(languages)}\n"
        
        # Add AI/ML section if relevant
        if ai_analysis.get('frameworks_detected'):
            md += f"""
## 🤖 AI/ML Components

- **Frameworks**: {', '.join(ai_analysis['frameworks_detected'])}
- **Models Found**: {len(ai_analysis.get('models', []))}
- **Pipelines**: {len(ai_analysis.get('pipelines', []))}
"""
        
        # Add quality summary
        quality_overview = quality_analysis.get('overview', {})
        if quality_overview:
            md += f"""
## 🔬 Code Quality

- **Average Quality Score**: {quality_overview.get('average_quality_score', 0):.3f}
- **Total Modules Analyzed**: {quality_overview.get('total_modules', 0)}
"""
        
        # Add navigation
        md += """
## 📚 Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [API Reference](API.md)
- [Code Quality Report](QUALITY.md)
"""
        
        if ai_analysis.get('models'):
            md += "- [AI/ML Models](AI_MODELS.md)\n"
        
        # Add getting started section
        md += """
## 🚀 Getting Started

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Usage

```bash
# Basic usage
python main.py

# With specific options
python main.py --config config.yaml --output ./docs
```

## 📋 Project Structure

```
"""
        
        # Add basic project structure
        md += self.generate_project_structure(code_analysis)
        
        md += """```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
"""
        
        return md
    
    def generate_architecture_doc(self, code_analysis: Dict[str, Any], 
                                ai_analysis: Dict[str, Any]) -> str:
        """Generate architecture documentation."""
        md = f"""# Architecture Overview

*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## System Architecture

This document provides an overview of the system architecture and design patterns used in this project.

## 📦 Modules Overview

"""
        
        modules = code_analysis.get('modules', [])
        for module in modules[:10]:  # Limit to first 10 modules
            md += f"""### {module.get('name', 'Unknown Module')}

**Path**: `{module.get('path', 'Unknown')}`

**Description**: {module.get('description', 'No description available')}

**Statistics**:
- Functions: {len(module.get('functions', []))}
- Classes: {len(module.get('classes', []))}
- Lines of Code: {module.get('lines_of_code', 0)}

"""
        
        # Add dependencies section
        dependencies = code_analysis.get('dependencies', {})
        if dependencies:
            md += """## 🔗 Dependencies

### External Dependencies
"""
            external_deps = dependencies.get('external_dependencies', [])
            for dep in external_deps[:10]:  # Limit to first 10
                md += f"- `{dep}`\n"
            
            md += "\n### Internal Dependencies\n"
            internal_deps = dependencies.get('internal_dependencies', [])
            for dep in internal_deps[:10]:  # Limit to first 10
                md += f"- `{dep}`\n"
        
        # Add AI components if available
        if ai_analysis.get('frameworks_detected'):
            md += f"""
## 🤖 AI/ML Architecture

### Frameworks Used
{chr(10).join(f'- **{framework}**' for framework in ai_analysis['frameworks_detected'])}

### Model Components
"""
            models = ai_analysis.get('models', [])
            for model in models[:5]:  # Limit to first 5 models
                md += f"""
#### {model.get('name', 'Unknown Model')}
- **Type**: {model.get('model_type', 'Unknown')}
- **Framework**: {model.get('framework', 'Unknown')}
- **Location**: Line {model.get('line_start', 'Unknown')}
"""
        
        return md
    
    def generate_api_doc(self, code_analysis: Dict[str, Any]) -> str:
        """Generate API reference documentation."""
        md = f"""# API Reference

*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

This document provides a comprehensive reference for all public APIs in this project.

"""
        
        modules = code_analysis.get('modules', [])
        
        for module in modules:
            functions = module.get('functions', [])
            classes = module.get('classes', [])
            
            if not functions and not classes:
                continue
                
            md += f"""## {module.get('name', 'Unknown Module')}

**Module Path**: `{module.get('path', 'Unknown')}`

"""
            
            # Document classes
            if classes:
                md += "### Classes\n\n"
                for cls in classes:
                    md += f"""#### `{cls.get('name', 'Unknown')}`

**Line**: {cls.get('line_start', 'Unknown')}

**Description**: {cls.get('docstring', 'No description available')}

**Methods**: {len(cls.get('methods', []))}

"""
                    # List methods
                    methods = cls.get('methods', [])
                    if methods:
                        for method in methods[:5]:  # Limit to first 5 methods
                            md += f"- `{method.get('name', 'unknown')}()` - {method.get('docstring', 'No description')[:100]}...\n"
                        md += "\n"
            
            # Document functions
            if functions:
                md += "### Functions\n\n"
                for func in functions:
                    md += f"""#### `{func.get('name', 'unknown')}()`

**Line**: {func.get('line_start', 'Unknown')}

**Arguments**: {func.get('args_count', 0)}

**Description**: {func.get('docstring', 'No description available')}

"""
        
        return md
    
    def generate_quality_doc(self, quality_analysis: Dict[str, Any]) -> str:
        """Generate quality report documentation."""
        md = f"""# Code Quality Report

*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## 📊 Quality Overview

"""
        
        overview = quality_analysis.get('overview', {})
        if overview:
            md += f"""- **Total Modules Analyzed**: {overview.get('total_modules', 0)}
- **Average Quality Score**: {overview.get('average_quality_score', 0):.3f}
- **Median Quality Score**: {overview.get('median_quality_score', 0):.3f}
- **Highest Quality Score**: {overview.get('max_quality_score', 0):.3f}
- **Lowest Quality Score**: {overview.get('min_quality_score', 0):.3f}

"""
        
        # Quality distribution
        distribution = quality_analysis.get('quality_distribution', {})
        if distribution:
            ranges = distribution.get('quality_ranges', {})
            md += """## 📈 Quality Distribution

| Quality Level | Module Count | Percentage |
|---------------|--------------|------------|
"""
            for level, count in ranges.items():
                percentage = distribution.get('distribution_percentages', {}).get(level, 0)
                md += f"| {level.title()} | {count} | {percentage:.1f}% |\n"
        
        # Module assessments
        assessments = quality_analysis.get('module_assessments', {})
        if assessments:
            md += "\n## 📋 Module Quality Details\n\n"
            
            # Sort by quality score
            sorted_modules = sorted(
                assessments.items(), 
                key=lambda x: x[1].get('overall_score', 0), 
                reverse=True
            )
            
            for module_path, assessment in sorted_modules[:10]:  # Top 10 modules
                score = assessment.get('overall_score', 0)
                grade = assessment.get('grade', 'F')
                metrics = assessment.get('metrics', {})
                
                md += f"""### {module_path}

**Quality Score**: {score:.3f} (Grade: {grade})

**Metrics**:
- Lines of Code: {metrics.get('lines_of_code', 0)}
- Functions: {metrics.get('function_count', 0)}
- Classes: {metrics.get('class_count', 0)}
- Documentation Coverage: {metrics.get('documentation_coverage', 0):.1%}
- Average Complexity: {metrics.get('avg_complexity', 0):.2f}

**Issues Found**: {len(assessment.get('issues', []))}

"""
                
                # List top issues
                issues = assessment.get('issues', [])
                if issues:
                    md += "**Top Issues**:\n"
                    for issue in issues[:3]:  # Top 3 issues
                        md += f"- Line {issue.get('line', '?')}: {issue.get('message', 'Unknown issue')}\n"
                    md += "\n"
        
        return md
    
    def generate_ai_models_doc(self, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI/ML models documentation."""
        md = f"""# AI/ML Models Documentation

*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## 🤖 Overview

This document provides detailed information about the AI/ML models and components found in this project.

## 🔧 Frameworks Detected

"""
        
        frameworks = ai_analysis.get('frameworks_detected', [])
        for framework in frameworks:
            md += f"- **{framework}**\n"
        
        md += "\n## 🧠 Models\n\n"
        
        models = ai_analysis.get('models', [])
        for model in models:
            md += f"""### {model.get('name', 'Unknown Model')}

**Type**: {model.get('model_type', 'Unknown')}
**Framework**: {model.get('framework', 'Unknown')}
**Location**: Line {model.get('line_start', 'Unknown')}

**Description**: {model.get('docstring', 'No description available')}

**Base Classes**: {', '.join(model.get('base_classes', []))}

**Methods**: {len(model.get('methods', []))}
**Attributes**: {len(model.get('attributes', []))}

"""
        
        # Add pipelines if available
        pipelines = ai_analysis.get('pipelines', [])
        if pipelines:
            md += "\n## 🔄 Pipelines\n\n"
            for pipeline in pipelines:
                md += f"""### {pipeline.get('name', 'Unknown Pipeline')}

**Type**: {pipeline.get('type', 'Unknown')}
**Steps**: {len(pipeline.get('steps', []))}

**Description**: {pipeline.get('docstring', 'No description available')}

"""
        
        return md
    
    def generate_project_structure(self, code_analysis: Dict[str, Any]) -> str:
        """Generate a basic project structure representation."""
        structure = ""
        modules = code_analysis.get('modules', [])
        
        # Group modules by directory
        directories = {}
        for module in modules:
            path = module.get('path', '')
            if '/' in path:
                dir_name = '/'.join(path.split('/')[:-1])
                if dir_name not in directories:
                    directories[dir_name] = []
                directories[dir_name].append(module)
            else:
                if 'root' not in directories:
                    directories['root'] = []
                directories['root'].append(module)
        
        # Build structure representation
        for dir_name, dir_modules in list(directories.items())[:5]:  # Limit to 5 directories
            if dir_name == 'root':
                for module in dir_modules[:3]:  # Limit to 3 files per directory
                    structure += f"{module.get('path', 'unknown')}\n"
            else:
                structure += f"{dir_name}/\n"
                for module in dir_modules[:3]:
                    filename = module.get('path', '').split('/')[-1]
                    structure += f"  {filename}\n"
        
        return structure
    
    def save_documentation(self, documentation: Dict[str, str]):
        """
        Save generated documentation to files.
        
        Args:
            documentation: Dictionary mapping filenames to content
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, content in documentation.items():
            output_path = self.output_dir / filename
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.logger.info(f"Saved {filename} to {output_path}")
            except Exception as e:
                self.logger.error(f"Failed to save {filename}: {e}")
