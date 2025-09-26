"""
Knowledge Graph Service for creating and managing code relationship graphs.

This service uses LLM analysis and data extraction to create comprehensive
knowledge graphs that represent relationships between code components.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
import json
from datetime import datetime
import networkx as nx

from ..models.analysis_models import AnalysisResult, ModuleAnalysis
from .ai_service import AIService
from ...infrastructure.vector_db import VectorDatabase

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """
    Service for creating and managing knowledge graphs from code analysis.
    
    This service combines static analysis results with LLM-powered insights
    to create comprehensive knowledge graphs representing code relationships.
    """
    
    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        vector_db: Optional[VectorDatabase] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the knowledge graph service.
        
        Args:
            ai_service: AI service for LLM analysis
            vector_db: Vector database for semantic search
            config: Configuration dictionary
        """
        self.ai_service = ai_service
        self.vector_db = vector_db
        self.config = config or {}
        self.graph = nx.DiGraph()  # Directed graph for relationships
        
        # Configuration
        self.kg_config = self.config.get('knowledge_graph', {})
        self.max_llm_calls = self.kg_config.get('max_llm_calls', 50)
        self.similarity_threshold = self.kg_config.get('similarity_threshold', 0.7)
        
        logger.info("Knowledge Graph Service initialized")
    
    def create_knowledge_graph(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """
        Create a comprehensive knowledge graph from analysis results.
        
        Args:
            analysis_result: Complete analysis results
            
        Returns:
            Dictionary containing the knowledge graph and metadata
        """
        try:
            logger.info("Creating knowledge graph from analysis results")
            
            # Initialize graph
            self.graph.clear()
            
            # Step 1: Add static analysis nodes and edges
            self._add_static_analysis_nodes(analysis_result)
            self._add_static_analysis_edges(analysis_result)
            
            # Step 2: Enhance with LLM-powered insights
            if self.ai_service:
                self._enhance_with_llm_insights(analysis_result)
            
            # Step 3: Add semantic relationships using vector database
            if self.vector_db:
                self._add_semantic_relationships(analysis_result)
            
            # Step 4: Calculate graph metrics
            graph_metrics = self._calculate_graph_metrics()
            
            # Step 5: Identify important patterns
            patterns = self._identify_patterns()
            
            # Convert graph to serializable format
            graph_data = self._serialize_graph()
            
            result = {
                'graph': graph_data,
                'metrics': graph_metrics,
                'patterns': patterns,
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'repository_path': analysis_result.repository_path,
                    'total_nodes': self.graph.number_of_nodes(),
                    'total_edges': self.graph.number_of_edges(),
                    'llm_enhanced': bool(self.ai_service),
                    'vector_enhanced': bool(self.vector_db)
                }
            }
            
            logger.info(f"Knowledge graph created with {result['metadata']['total_nodes']} nodes and {result['metadata']['total_edges']} edges")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create knowledge graph: {e}")
            return {
                'error': str(e),
                'graph': {},
                'metrics': {},
                'patterns': {},
                'metadata': {}
            }
    
    def _add_static_analysis_nodes(self, analysis_result: AnalysisResult):
        """Add nodes from static analysis results."""
        # Add repository node
        self.graph.add_node(
            f"repo:{analysis_result.repository_path}",
            type="repository",
            name=Path(analysis_result.repository_path).name,
            path=analysis_result.repository_path,
            project_type=analysis_result.project_type,
            total_files=analysis_result.total_files,
            total_functions=analysis_result.total_functions,
            total_classes=analysis_result.total_classes
        )
        
        # Add module nodes
        for module in analysis_result.modules:
            module_id = f"module:{module.module_path}"
            self.graph.add_node(
                module_id,
                type="module",
                name=module.module_name,
                path=module.module_path,
                module_type=module.module_type,
                description=module.description,
                complexity=module.complexity.cyclomatic_complexity if module.complexity else 0.0,
                lines_of_code=module.metrics.total_lines if module.metrics else 0,
                function_count=len(module.functions),
                class_count=len(module.classes)
            )
            
            # Add function nodes
            for func in module.functions:
                func_id = f"function:{module.module_path}::{func.get('name', '')}"
                self.graph.add_node(
                    func_id,
                    type="function",
                    name=func.get('name', ''),
                    module=module.module_name,
                    signature=func.get('signature', ''),
                    docstring=func.get('docstring', ''),
                    complexity=func.get('complexity', 0.0),
                    line_start=func.get('line_start', 0),
                    line_end=func.get('line_end', 0),
                    parameters=func.get('parameters', []),
                    return_type=func.get('return_type', '')
                )
            
            # Add class nodes
            for cls in module.classes:
                cls_id = f"class:{module.module_path}::{cls.get('name', '')}"
                self.graph.add_node(
                    cls_id,
                    type="class",
                    name=cls.get('name', ''),
                    module=module.module_name,
                    docstring=cls.get('docstring', ''),
                    line_start=cls.get('line_start', 0),
                    line_end=cls.get('line_end', 0),
                    bases=cls.get('bases', []),
                    methods=cls.get('methods', [])
                )
                
                # Add method nodes for classes
                for method in cls.get('methods', []):
                    method_id = f"method:{module.module_path}::{cls.get('name', '')}::{method.get('name', '')}"
                    self.graph.add_node(
                        method_id,
                        type="method",
                        name=method.get('name', ''),
                        class_name=cls.get('name', ''),
                        module=module.module_name,
                        signature=method.get('signature', ''),
                        docstring=method.get('docstring', ''),
                        complexity=method.get('complexity', 0.0),
                        line_start=method.get('line_start', 0),
                        line_end=method.get('line_end', 0)
                    )
    
    def _add_static_analysis_edges(self, analysis_result: AnalysisResult):
        """Add edges from static analysis results."""
        repo_id = f"repo:{analysis_result.repository_path}"
        
        # Connect repository to modules
        for module in analysis_result.modules:
            module_id = f"module:{module.module_path}"
            self.graph.add_edge(repo_id, module_id, relationship="contains", type="containment")
            
            # Connect modules to functions
            for func in module.functions:
                func_id = f"function:{module.module_path}::{func.get('name', '')}"
                self.graph.add_edge(module_id, func_id, relationship="defines", type="definition")
            
            # Connect modules to classes
            for cls in module.classes:
                cls_id = f"class:{module.module_path}::{cls.get('name', '')}"
                self.graph.add_edge(module_id, cls_id, relationship="defines", type="definition")
                
                # Connect classes to methods
                for method in cls.get('methods', []):
                    method_id = f"method:{module.module_path}::{cls.get('name', '')}::{method.get('name', '')}"
                    self.graph.add_edge(cls_id, method_id, relationship="has_method", type="composition")
            
            # Add dependency edges
            for dep in module.dependencies:
                dep_module_id = f"module:{dep}"
                if self.graph.has_node(dep_module_id):
                    self.graph.add_edge(module_id, dep_module_id, relationship="depends_on", type="dependency")
            
            # Add import edges
            for imp in module.imports:
                import_name = imp.get('name', '') if isinstance(imp, dict) else str(imp)
                # Try to find the imported module in our graph
                for node_id in self.graph.nodes():
                    node_data = self.graph.nodes[node_id]
                    if (node_data.get('type') == 'module' and 
                        (node_data.get('name') == import_name or 
                         import_name in node_data.get('path', ''))):
                        self.graph.add_edge(module_id, node_id, relationship="imports", type="import")
                        break
        
        # Add inheritance edges
        for module in analysis_result.modules:
            for cls in module.classes:
                cls_id = f"class:{module.module_path}::{cls.get('name', '')}"
                for base in cls.get('bases', []):
                    # Find the base class in our graph
                    for node_id in self.graph.nodes():
                        node_data = self.graph.nodes[node_id]
                        if node_data.get('type') == 'class' and node_data.get('name') == base:
                            self.graph.add_edge(cls_id, node_id, relationship="inherits_from", type="inheritance")
                            break
    
    def _enhance_with_llm_insights(self, analysis_result: AnalysisResult):
        """Enhance the graph with LLM-powered insights."""
        if not self.ai_service:
            return
        
        logger.info("Enhancing knowledge graph with LLM insights")
        
        try:
            # Get high-level architectural insights
            architectural_prompt = self._create_architectural_analysis_prompt(analysis_result)
            architectural_insights = self.ai_service.analyze_with_context(
                prompt=architectural_prompt,
                context="architectural_analysis",
                max_tokens=2000
            )
            
            if architectural_insights and architectural_insights.get('success'):
                self._process_architectural_insights(architectural_insights.get('content', ''))
            
            # Analyze key components for detailed insights
            key_components = self._identify_key_components()
            llm_calls_made = 0
            
            for component_id in key_components:
                if llm_calls_made >= self.max_llm_calls:
                    break
                
                component_data = self.graph.nodes[component_id]
                component_prompt = self._create_component_analysis_prompt(component_id, component_data)
                
                component_insights = self.ai_service.analyze_with_context(
                    prompt=component_prompt,
                    context="component_analysis",
                    max_tokens=1000
                )
                
                if component_insights and component_insights.get('success'):
                    self._process_component_insights(component_id, component_insights.get('content', ''))
                
                llm_calls_made += 1
            
            logger.info(f"Made {llm_calls_made} LLM calls for knowledge graph enhancement")
            
        except Exception as e:
            logger.error(f"Failed to enhance with LLM insights: {e}")
    
    def _add_semantic_relationships(self, analysis_result: AnalysisResult):
        """Add semantic relationships using vector database."""
        if not self.vector_db:
            return
        
        logger.info("Adding semantic relationships using vector database")
        
        try:
            # Find semantically similar components
            for node_id in self.graph.nodes():
                node_data = self.graph.nodes[node_id]
                
                # Skip repository nodes
                if node_data.get('type') == 'repository':
                    continue
                
                # Get related components from vector database
                related = self.vector_db.get_related_components(node_id, n_results=5)
                
                for related_component in related:
                    related_id = related_component['id']
                    distance = related_component.get('distance', 1.0)
                    
                    # Only add edge if similarity is above threshold
                    similarity = 1.0 - distance  # Convert distance to similarity
                    if similarity >= self.similarity_threshold and related_id in self.graph.nodes():
                        self.graph.add_edge(
                            node_id, 
                            related_id, 
                            relationship="semantically_similar", 
                            type="semantic",
                            similarity=similarity
                        )
            
        except Exception as e:
            logger.error(f"Failed to add semantic relationships: {e}")
    
    def _calculate_graph_metrics(self) -> Dict[str, Any]:
        """Calculate various metrics for the knowledge graph."""
        try:
            metrics = {
                'basic_metrics': {
                    'total_nodes': self.graph.number_of_nodes(),
                    'total_edges': self.graph.number_of_edges(),
                    'density': nx.density(self.graph),
                    'is_connected': nx.is_weakly_connected(self.graph)
                },
                'node_metrics': {
                    'avg_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0,
                    'max_degree': max(dict(self.graph.degree()).values()) if self.graph.number_of_nodes() > 0 else 0
                },
                'centrality_metrics': {},
                'component_metrics': {
                    'weakly_connected_components': nx.number_weakly_connected_components(self.graph),
                    'strongly_connected_components': nx.number_strongly_connected_components(self.graph)
                }
            }
            
            # Calculate centrality metrics (can be expensive for large graphs)
            if self.graph.number_of_nodes() < 1000:  # Only for reasonably sized graphs
                try:
                    degree_centrality = nx.degree_centrality(self.graph)
                    betweenness_centrality = nx.betweenness_centrality(self.graph)
                    
                    # Find most central nodes
                    most_central_degree = max(degree_centrality, key=degree_centrality.get) if degree_centrality else None
                    most_central_betweenness = max(betweenness_centrality, key=betweenness_centrality.get) if betweenness_centrality else None
                    
                    metrics['centrality_metrics'] = {
                        'most_central_degree': {
                            'node': most_central_degree,
                            'score': degree_centrality.get(most_central_degree, 0) if most_central_degree else 0
                        },
                        'most_central_betweenness': {
                            'node': most_central_betweenness,
                            'score': betweenness_centrality.get(most_central_betweenness, 0) if most_central_betweenness else 0
                        }
                    }
                except Exception as e:
                    logger.warning(f"Failed to calculate centrality metrics: {e}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate graph metrics: {e}")
            return {}
    
    def _identify_patterns(self) -> Dict[str, Any]:
        """Identify important patterns in the knowledge graph."""
        patterns = {
            'architectural_patterns': [],
            'design_patterns': [],
            'complexity_hotspots': [],
            'dependency_issues': [],
            'semantic_clusters': []
        }
        
        try:
            # Identify complexity hotspots
            complexity_nodes = []
            for node_id, node_data in self.graph.nodes(data=True):
                complexity = node_data.get('complexity', 0.0)
                if complexity > 10.0:  # High complexity threshold
                    complexity_nodes.append({
                        'node': node_id,
                        'complexity': complexity,
                        'type': node_data.get('type'),
                        'name': node_data.get('name')
                    })
            
            patterns['complexity_hotspots'] = sorted(complexity_nodes, key=lambda x: x['complexity'], reverse=True)[:10]
            
            # Identify dependency issues (circular dependencies)
            try:
                cycles = list(nx.simple_cycles(self.graph))
                for cycle in cycles[:5]:  # Limit to first 5 cycles
                    if len(cycle) > 1:  # Actual cycle
                        patterns['dependency_issues'].append({
                            'type': 'circular_dependency',
                            'nodes': cycle,
                            'length': len(cycle)
                        })
            except Exception as e:
                logger.warning(f"Failed to detect cycles: {e}")
            
            # Identify highly connected nodes (potential architectural components)
            degree_dict = dict(self.graph.degree())
            high_degree_nodes = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:5]
            
            for node_id, degree in high_degree_nodes:
                node_data = self.graph.nodes[node_id]
                patterns['architectural_patterns'].append({
                    'pattern': 'hub_component',
                    'node': node_id,
                    'name': node_data.get('name'),
                    'type': node_data.get('type'),
                    'connections': degree,
                    'description': f"Highly connected {node_data.get('type')} with {degree} connections"
                })
            
            # Identify semantic clusters using community detection
            try:
                # Only consider semantic edges for clustering
                semantic_graph = nx.DiGraph()
                for u, v, data in self.graph.edges(data=True):
                    if data.get('type') == 'semantic':
                        semantic_graph.add_edge(u, v, **data)
                
                if semantic_graph.number_of_nodes() > 0:
                    # Convert to undirected for community detection
                    undirected_semantic = semantic_graph.to_undirected()
                    
                    # Simple clustering based on connected components
                    components = list(nx.connected_components(undirected_semantic))
                    for i, component in enumerate(components):
                        if len(component) > 2:  # Only meaningful clusters
                            patterns['semantic_clusters'].append({
                                'cluster_id': i,
                                'nodes': list(component),
                                'size': len(component),
                                'description': f"Semantic cluster of {len(component)} related components"
                            })
            
            except Exception as e:
                logger.warning(f"Failed to identify semantic clusters: {e}")
            
        except Exception as e:
            logger.error(f"Failed to identify patterns: {e}")
        
        return patterns
    
    def _serialize_graph(self) -> Dict[str, Any]:
        """Convert NetworkX graph to serializable format."""
        try:
            return {
                'nodes': [
                    {'id': node_id, **node_data}
                    for node_id, node_data in self.graph.nodes(data=True)
                ],
                'edges': [
                    {'source': u, 'target': v, **edge_data}
                    for u, v, edge_data in self.graph.edges(data=True)
                ]
            }
        except Exception as e:
            logger.error(f"Failed to serialize graph: {e}")
            return {'nodes': [], 'edges': []}
    
    def _create_architectural_analysis_prompt(self, analysis_result: AnalysisResult) -> str:
        """Create prompt for architectural analysis."""
        return f"""
Analyze the following codebase architecture and identify key architectural patterns, design decisions, and relationships:

Repository: {analysis_result.repository_path}
Project Type: {analysis_result.project_type}
Total Files: {analysis_result.total_files}
Total Functions: {analysis_result.total_functions}
Total Classes: {analysis_result.total_classes}

Key Modules:
{chr(10).join([f"- {m.module_name}: {m.description}" for m in analysis_result.modules[:10]])}

Please identify:
1. Overall architectural pattern (MVC, microservices, layered, etc.)
2. Key architectural components and their roles
3. Main data flow patterns
4. Design patterns used
5. Potential architectural issues or improvements

Provide a structured analysis focusing on high-level relationships and patterns.
"""
    
    def _create_component_analysis_prompt(self, component_id: str, component_data: Dict[str, Any]) -> str:
        """Create prompt for individual component analysis."""
        return f"""
Analyze this code component and its role in the system:

Component: {component_data.get('name', 'Unknown')}
Type: {component_data.get('type', 'Unknown')}
Module: {component_data.get('module', 'Unknown')}
Complexity: {component_data.get('complexity', 0)}

{f"Docstring: {component_data.get('docstring', '')}" if component_data.get('docstring') else ""}
{f"Signature: {component_data.get('signature', '')}" if component_data.get('signature') else ""}

Please analyze:
1. Primary purpose and responsibility
2. Relationships with other components
3. Design patterns implemented
4. Potential issues or improvements
5. Architectural significance

Provide concise insights about this component's role in the system.
"""
    
    def _process_architectural_insights(self, insights: str):
        """Process and store architectural insights from LLM."""
        # Add architectural insights as graph metadata
        if not hasattr(self.graph, 'graph'):
            self.graph.graph = {}
        
        self.graph.graph['architectural_insights'] = insights
        
        # TODO: Parse insights and add specific nodes/edges for architectural patterns
        # This could involve NLP to extract specific patterns and relationships
    
    def _process_component_insights(self, component_id: str, insights: str):
        """Process and store component insights from LLM."""
        # Add insights to the component node
        if self.graph.has_node(component_id):
            self.graph.nodes[component_id]['llm_insights'] = insights
    
    def _identify_key_components(self) -> List[str]:
        """Identify key components that would benefit from LLM analysis."""
        # Select components based on various criteria
        key_components = []
        
        # High complexity components
        for node_id, node_data in self.graph.nodes(data=True):
            complexity = node_data.get('complexity', 0.0)
            if complexity > 5.0:  # Moderate complexity threshold
                key_components.append(node_id)
        
        # Highly connected components
        degree_dict = dict(self.graph.degree())
        high_degree_nodes = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:10]
        key_components.extend([node_id for node_id, _ in high_degree_nodes])
        
        # Remove duplicates and limit
        return list(set(key_components))[:self.max_llm_calls]
    
    def export_graph(self, output_path: str, format: str = 'json') -> bool:
        """
        Export the knowledge graph to a file.
        
        Args:
            output_path: Path to save the graph
            format: Export format ('json', 'gexf', 'graphml')
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format == 'json':
                graph_data = self._serialize_graph()
                with open(output_file, 'w') as f:
                    json.dump(graph_data, f, indent=2)
            elif format == 'gexf':
                nx.write_gexf(self.graph, output_file)
            elif format == 'graphml':
                nx.write_graphml(self.graph, output_file)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Knowledge graph exported to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export knowledge graph: {e}")
            return False
