"""
Architecture diagram generator.

This module generates architecture diagrams from code analysis results
using various diagramming libraries and formats.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from ..base.base_generator import BaseGenerator


class ArchitectureDiagramGenerator(BaseGenerator):
    """
    Generator that creates architecture diagrams from analysis data.
    """
    
    def __init__(self, config: Dict[str, Any]):
        # Initialize with proper parameter order for BaseGenerator  
        super().__init__(template_dir="diagram_templates", output_dir="docs", config=config)
        self.diagram_config = config.get('diagrams', {})
        self.output_format = self.diagram_config.get('format', 'mermaid')
        
    def generate(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate architecture diagrams from analysis data.
        
        Args:
            analysis_data: Combined analysis results
            
        Returns:
            Dictionary containing generated diagrams
        """
        self.log_generation_start("Architecture Diagrams")
        
        result = self.create_result_template()
        
        try:
            code_analysis = analysis_data.get('code_analysis', {})
            ai_analysis = analysis_data.get('ai_analysis', {})
            
            diagrams = {}
            
            # Generate system overview diagram
            diagrams['system_overview'] = self.generate_system_overview(code_analysis)
            
            # Generate module dependency diagram
            if code_analysis.get('dependencies'):
                diagrams['module_dependencies'] = self.generate_dependency_diagram(
                    code_analysis['dependencies']
                )
            
            # Generate AI/ML pipeline diagram if AI components exist
            if ai_analysis.get('models') or ai_analysis.get('pipelines'):
                diagrams['ai_pipeline'] = self.generate_ai_pipeline_diagram(ai_analysis)
            
            # Generate component hierarchy diagram
            diagrams['component_hierarchy'] = self.generate_component_hierarchy(code_analysis)
            
            result['results'] = {
                'diagrams': diagrams,
                'format': self.output_format,
                'total_diagrams': len(diagrams)
            }
            
            self.log_generation_complete("Architecture Diagrams", len(diagrams))
            
        except Exception as e:
            result['errors'].append(f"Diagram generation failed: {str(e)}")
            self.logger.error(f"Architecture diagram generation error: {e}")
        
        return result
    
    def generate_system_overview(self, code_analysis: Dict[str, Any]) -> str:
        """Generate a high-level system overview diagram."""
        if self.output_format == 'mermaid':
            return self._generate_mermaid_system_overview(code_analysis)
        elif self.output_format == 'plantuml':
            return self._generate_plantuml_system_overview(code_analysis)
        else:
            return self._generate_text_diagram(code_analysis)
    
    def _generate_mermaid_system_overview(self, code_analysis: Dict[str, Any]) -> str:
        """Generate Mermaid system overview diagram."""
        modules = code_analysis.get('modules', [])
        
        # Group modules by type
        module_types = {}
        for module in modules:
            mod_type = module.get('type', 'module')
            if mod_type not in module_types:
                module_types[mod_type] = []
            module_types[mod_type].append(module)
        
        diagram = """graph TD
    subgraph "System Architecture"
"""
        
        # Add nodes for each module type
        for i, (mod_type, type_modules) in enumerate(module_types.items()):
            type_id = mod_type.upper().replace(' ', '_')
            diagram += f'        {type_id}["{mod_type.title()} Layer<br/>({len(type_modules)} modules)"]\n'
        
        # Add connections between layers
        type_ids = list(module_types.keys())
        for i in range(len(type_ids) - 1):
            from_type = type_ids[i].upper().replace(' ', '_')
            to_type = type_ids[i + 1].upper().replace(' ', '_')
            diagram += f'        {from_type} --> {to_type}\n'
        
        # Add styling
        diagram += """
    classDef apiStyle fill:#e1f5fe
    classDef serviceStyle fill:#e8f5e8
    classDef moduleStyle fill:#fff3e0
    
"""
        
        # Apply styles
        for mod_type in module_types.keys():
            type_id = mod_type.upper().replace(' ', '_')
            if 'api' in mod_type.lower():
                diagram += f'    class {type_id} apiStyle\n'
            elif 'service' in mod_type.lower():
                diagram += f'    class {type_id} serviceStyle\n'
            else:
                diagram += f'    class {type_id} moduleStyle\n'
        
        return diagram
    
    def _generate_plantuml_system_overview(self, code_analysis: Dict[str, Any]) -> str:
        """Generate PlantUML system overview diagram."""
        modules = code_analysis.get('modules', [])
        
        diagram = """@startuml
!define RECTANGLE class
!define ARROW -->

title System Architecture Overview

"""
        
        # Group modules by type
        module_types = {}
        for module in modules:
            mod_type = module.get('type', 'module')
            if mod_type not in module_types:
                module_types[mod_type] = []
            module_types[mod_type].append(module)
        
        # Add components
        for mod_type, type_modules in module_types.items():
            diagram += f'RECTANGLE "{mod_type.title()}" as {mod_type} {{\n'
            diagram += f'  {len(type_modules)} modules\n'
            diagram += '}\n\n'
        
        # Add relationships
        type_list = list(module_types.keys())
        for i in range(len(type_list) - 1):
            diagram += f'{type_list[i]} ARROW {type_list[i + 1]}\n'
        
        diagram += '\n@enduml'
        return diagram
    
    def _generate_text_diagram(self, code_analysis: Dict[str, Any]) -> str:
        """Generate simple text-based diagram."""
        modules = code_analysis.get('modules', [])
        
        diagram = "System Architecture Overview\n"
        diagram += "=" * 30 + "\n\n"
        
        # Group modules by type
        module_types = {}
        for module in modules:
            mod_type = module.get('type', 'module')
            if mod_type not in module_types:
                module_types[mod_type] = []
            module_types[mod_type].append(module)
        
        for mod_type, type_modules in module_types.items():
            diagram += f"📦 {mod_type.title()} Layer ({len(type_modules)} modules)\n"
            for module in type_modules[:3]:  # Show first 3 modules
                diagram += f"   └── {module.get('name', 'Unknown')}\n"
            if len(type_modules) > 3:
                diagram += f"   └── ... and {len(type_modules) - 3} more\n"
            diagram += "\n"
        
        return diagram
    
    def generate_dependency_diagram(self, dependencies: Dict[str, Any]) -> str:
        """Generate module dependency diagram."""
        if self.output_format == 'mermaid':
            return self._generate_mermaid_dependencies(dependencies)
        else:
            return self._generate_text_dependencies(dependencies)
    
    def _generate_mermaid_dependencies(self, dependencies: Dict[str, Any]) -> str:
        """Generate Mermaid dependency diagram."""
        diagram = """graph LR
    subgraph "Module Dependencies"
"""
        
        # Add external dependencies
        external_deps = dependencies.get('external_dependencies', [])[:10]  # Limit to 10
        for i, dep in enumerate(external_deps):
            dep_id = f"EXT_{i}"
            diagram += f'        {dep_id}["{dep}"]\n'
        
        # Add internal dependencies
        internal_deps = dependencies.get('internal_dependencies', [])[:10]  # Limit to 10
        for i, dep in enumerate(internal_deps):
            dep_id = f"INT_{i}"
            diagram += f'        {dep_id}["{dep}"]\n'
        
        # Add connections (simplified)
        if external_deps and internal_deps:
            diagram += f'        EXT_0 --> INT_0\n'
        
        diagram += """    end
    
    classDef external fill:#ffebee
    classDef internal fill:#e8f5e8
    
"""
        
        # Apply styles
        for i in range(len(external_deps)):
            diagram += f'    class EXT_{i} external\n'
        for i in range(len(internal_deps)):
            diagram += f'    class INT_{i} internal\n'
        
        return diagram
    
    def _generate_text_dependencies(self, dependencies: Dict[str, Any]) -> str:
        """Generate text-based dependency diagram."""
        diagram = "Module Dependencies\n"
        diagram += "=" * 20 + "\n\n"
        
        external_deps = dependencies.get('external_dependencies', [])
        internal_deps = dependencies.get('internal_dependencies', [])
        
        if external_deps:
            diagram += "📦 External Dependencies:\n"
            for dep in external_deps[:10]:
                diagram += f"   • {dep}\n"
            diagram += "\n"
        
        if internal_deps:
            diagram += "🏠 Internal Dependencies:\n"
            for dep in internal_deps[:10]:
                diagram += f"   • {dep}\n"
            diagram += "\n"
        
        return diagram
    
    def generate_ai_pipeline_diagram(self, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI/ML pipeline diagram."""
        if self.output_format == 'mermaid':
            return self._generate_mermaid_ai_pipeline(ai_analysis)
        else:
            return self._generate_text_ai_pipeline(ai_analysis)
    
    def _generate_mermaid_ai_pipeline(self, ai_analysis: Dict[str, Any]) -> str:
        """Generate Mermaid AI pipeline diagram."""
        models = ai_analysis.get('models', [])
        pipelines = ai_analysis.get('pipelines', [])
        
        diagram = """graph TD
    subgraph "AI/ML Pipeline"
"""
        
        # Add data input
        diagram += '        DATA[("Data Input")]\n'
        
        # Add preprocessing
        diagram += '        PREP["Data Preprocessing"]\n'
        diagram += '        DATA --> PREP\n'
        
        # Add models
        for i, model in enumerate(models[:5]):  # Limit to 5 models
            model_id = f"MODEL_{i}"
            model_name = model.get('name', f'Model_{i}')
            model_type = model.get('model_type', 'model')
            diagram += f'        {model_id}["{model_name}<br/>({model_type})"]\n'
            diagram += f'        PREP --> {model_id}\n'
        
        # Add output
        diagram += '        OUTPUT[("Predictions/Results")]\n'
        for i in range(len(models[:5])):
            diagram += f'        MODEL_{i} --> OUTPUT\n'
        
        diagram += """    end
    
    classDef data fill:#e3f2fd
    classDef process fill:#e8f5e8
    classDef model fill:#fff3e0
    classDef output fill:#fce4ec
    
    class DATA data
    class PREP process
    class OUTPUT output
"""
        
        # Style models
        for i in range(len(models[:5])):
            diagram += f'    class MODEL_{i} model\n'
        
        return diagram
    
    def _generate_text_ai_pipeline(self, ai_analysis: Dict[str, Any]) -> str:
        """Generate text-based AI pipeline diagram."""
        models = ai_analysis.get('models', [])
        frameworks = ai_analysis.get('frameworks_detected', [])
        
        diagram = "AI/ML Pipeline Overview\n"
        diagram += "=" * 25 + "\n\n"
        
        if frameworks:
            diagram += "🔧 Frameworks:\n"
            for framework in frameworks:
                diagram += f"   • {framework}\n"
            diagram += "\n"
        
        if models:
            diagram += "🤖 Models:\n"
            for model in models:
                model_name = model.get('name', 'Unknown')
                model_type = model.get('model_type', 'model')
                framework = model.get('framework', 'unknown')
                diagram += f"   • {model_name} ({model_type}) - {framework}\n"
            diagram += "\n"
        
        # Simple pipeline flow
        diagram += "📊 Pipeline Flow:\n"
        diagram += "   Data Input → Preprocessing → Model Training/Inference → Output\n"
        
        return diagram
    
    def generate_component_hierarchy(self, code_analysis: Dict[str, Any]) -> str:
        """Generate component hierarchy diagram."""
        modules = code_analysis.get('modules', [])
        
        if self.output_format == 'mermaid':
            return self._generate_mermaid_hierarchy(modules)
        else:
            return self._generate_text_hierarchy(modules)
    
    def _generate_mermaid_hierarchy(self, modules: List[Dict[str, Any]]) -> str:
        """Generate Mermaid component hierarchy diagram."""
        # Group modules by directory structure
        hierarchy = {}
        for module in modules:
            path_parts = module.get('path', '').split('/')
            current = hierarchy
            for part in path_parts[:-1]:  # Exclude filename
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        diagram = """graph TD
    subgraph "Component Hierarchy"
"""
        
        def add_hierarchy_nodes(node_dict, parent_id="ROOT", level=0):
            for name, children in node_dict.items():
                if not name:  # Skip empty names
                    continue
                node_id = f"{parent_id}_{name}".replace('/', '_').replace('.', '_')
                diagram_lines.append(f'        {node_id}["{name}"]')
                if parent_id != "ROOT":
                    diagram_lines.append(f'        {parent_id} --> {node_id}')
                if children:
                    add_hierarchy_nodes(children, node_id, level + 1)
        
        diagram_lines = []
        add_hierarchy_nodes(hierarchy)
        
        diagram += '\n'.join(diagram_lines)
        diagram += "\n    end"
        
        return diagram
    
    def _generate_text_hierarchy(self, modules: List[Dict[str, Any]]) -> str:
        """Generate text-based component hierarchy."""
        diagram = "Component Hierarchy\n"
        diagram += "=" * 20 + "\n\n"
        
        # Group by directory
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
        
        for dir_name, dir_modules in directories.items():
            diagram += f"📁 {dir_name}/\n"
            for module in dir_modules:
                filename = module.get('path', '').split('/')[-1]
                module_type = module.get('type', 'module')
                diagram += f"   └── {filename} ({module_type})\n"
            diagram += "\n"
        
        return diagram
