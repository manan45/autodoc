"""
Vector database integration using ChromaDB for embeddings and semantic search.

This module provides vector database functionality for storing and retrieving
code embeddings, enabling semantic search and knowledge graph generation.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
import hashlib
from datetime import datetime

# Disable ChromaDB telemetry before import
os.environ.setdefault('ANONYMIZED_TELEMETRY', 'false')
os.environ.setdefault('CHROMA_CLIENT_AUTH_PROVIDER', '')
os.environ.setdefault('CHROMA_CLIENT_AUTH_CREDENTIALS', '')

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logger = logging.getLogger(__name__)


class VectorDatabase:
    """
    Vector database for storing and retrieving code embeddings.
    
    Uses ChromaDB as the underlying vector database for semantic search
    and knowledge graph generation capabilities.
    """
    
    def __init__(self, db_path: str = "vector_db", collection_name: str = "code_analysis"):
        """
        Initialize the vector database.
        
        Args:
            db_path: Path to store the vector database
            collection_name: Name of the collection to use
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is required. Install with: pip install chromadb")
        
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
        # Create database directory
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self._initialize_client()
        
        logger.info(f"Vector database initialized at {self.db_path}")
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create persistent client with all telemetry disabled
            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True,
                    chroma_client_auth_provider=None,
                    chroma_client_auth_credentials=None
                )
            )
            
            # Use OpenAI embeddings if available, otherwise default
            try:
                embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                    model_name="text-embedding-3-small"
                )
            except Exception:
                # Fallback to sentence transformers
                try:
                    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name="all-MiniLM-L6-v2"
                    )
                except Exception:
                    # Use default embedding function
                    embedding_function = embedding_functions.DefaultEmbeddingFunction()
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=embedding_function
                )
                logger.info(f"Using existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=embedding_function,
                    metadata={"created_at": datetime.now().isoformat()}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def store_code_analysis(self, analysis_data: Dict[str, Any], repository_path: str) -> bool:
        """
        Store code analysis results in the vector database.
        
        Args:
            analysis_data: Analysis results to store
            repository_path: Path to the analyzed repository
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First, delete existing data for this repository to avoid duplicates
            try:
                self.delete_repository(repository_path)
                logger.info(f"Cleared existing data for repository: {repository_path}")
            except Exception as e:
                logger.warning(f"Could not clear existing repository data: {e}")
            
            documents = []
            metadatas = []
            ids = []
            
            # Store overall repository information
            repo_id = self._generate_id("repo", repository_path, repository_path)
            repo_doc = self._create_repository_document(analysis_data, repository_path)
            
            documents.append(repo_doc)
            metadatas.append({
                "type": "repository",
                "repository_path": repository_path,
                "timestamp": datetime.now().isoformat(),
                "total_files": analysis_data.get("total_files", 0),
                "total_functions": analysis_data.get("total_functions", 0),
                "total_classes": analysis_data.get("total_classes", 0),
                "project_type": analysis_data.get("project_type", "unknown")
            })
            ids.append(repo_id)
            
            # Store module-level information
            modules = analysis_data.get("modules", [])
            for module in modules:
                module_id = self._generate_id("module", module.get("module_path", ""), repository_path)
                module_doc = self._create_module_document(module)
                
                documents.append(module_doc)
                metadatas.append({
                    "type": "module",
                    "repository_path": repository_path,
                    "module_path": module.get("module_path", ""),
                    "module_name": module.get("module_name", ""),
                    "module_type": module.get("module_type", "module"),
                    "timestamp": datetime.now().isoformat(),
                    "function_count": len(module.get("functions", [])),
                    "class_count": len(module.get("classes", [])),
                    "complexity": module.get("complexity", {}).get("cyclomatic_complexity", 0.0)
                })
                ids.append(module_id)
                
                # Store function-level information
                functions = module.get("functions", [])
                for func_idx, func in enumerate(functions):
                    # Add function index to ensure uniqueness for functions with same name
                    func_identifier = f"{module.get('module_path', '')}::{func.get('name', '')}::{func.get('line_start', func_idx)}"
                    func_id = self._generate_id("function", func_identifier, repository_path)
                    func_doc = self._create_function_document(func, module)
                    
                    documents.append(func_doc)
                    metadatas.append({
                        "type": "function",
                        "repository_path": repository_path,
                        "module_path": module.get("module_path", ""),
                        "function_name": func.get("name", ""),
                        "timestamp": datetime.now().isoformat(),
                        "complexity": func.get("complexity", 0.0),
                        "line_start": func.get("line_start", 0),
                        "line_end": func.get("line_end", 0)
                    })
                    ids.append(func_id)
                
                # Store class-level information
                classes = module.get("classes", [])
                for cls_idx, cls in enumerate(classes):
                    # Add class index to ensure uniqueness for classes with same name
                    cls_identifier = f"{module.get('module_path', '')}::{cls.get('name', '')}::{cls.get('line_start', cls_idx)}"
                    cls_id = self._generate_id("class", cls_identifier, repository_path)
                    cls_doc = self._create_class_document(cls, module)
                    
                    documents.append(cls_doc)
                    metadatas.append({
                        "type": "class",
                        "repository_path": repository_path,
                        "module_path": module.get("module_path", ""),
                        "class_name": cls.get("name", ""),
                        "timestamp": datetime.now().isoformat(),
                        "method_count": len(cls.get("methods", [])),
                        "line_start": cls.get("line_start", 0),
                        "line_end": cls.get("line_end", 0)
                    })
                    ids.append(cls_id)
            
            # Ensure all IDs are unique before adding
            unique_docs = []
            unique_metas = []
            unique_ids = []
            seen_ids = set()
            duplicate_count = 0
            
            for i, doc_id in enumerate(ids):
                if doc_id not in seen_ids:
                    unique_docs.append(documents[i])
                    unique_metas.append(metadatas[i])
                    unique_ids.append(doc_id)
                    seen_ids.add(doc_id)
                else:
                    duplicate_count += 1
                    # Log at debug level instead of warning to reduce noise
                    logger.debug(f"Skipping duplicate ID: {doc_id} (metadata: {metadatas[i].get('type', 'unknown')})")
            
            # Summary log if duplicates were found
            if duplicate_count > 0:
                logger.info(f"Skipped {duplicate_count} duplicate documents during batch processing")
            
            # Add to collection
            if unique_ids:
                self.collection.add(
                    documents=unique_docs,
                    metadatas=unique_metas,
                    ids=unique_ids
                )
            
            logger.info(f"Stored {len(unique_ids)} unique documents in vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store code analysis: {e}")
            return False
    
    def semantic_search(self, query: str, n_results: int = 10, 
                       filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform semantic search on stored code analysis.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_type: Optional filter by document type (repository, module, function, class)
            
        Returns:
            List of search results with metadata
        """
        try:
            where_clause = {}
            if filter_type:
                where_clause["type"] = filter_type
            
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def get_related_components(self, component_id: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Find components related to a given component.
        
        Args:
            component_id: ID of the component to find relations for
            n_results: Number of related components to return
            
        Returns:
            List of related components
        """
        try:
            # Get the original component
            original = self.collection.get(ids=[component_id])
            if not original['documents']:
                return []
            
            # Use the document content for similarity search
            document_content = original['documents'][0]
            
            results = self.collection.query(
                query_texts=[document_content],
                n_results=n_results + 1  # +1 to exclude the original
            )
            
            # Filter out the original component and format results
            formatted_results = []
            for i, result_id in enumerate(results['ids'][0]):
                if result_id != component_id:
                    formatted_results.append({
                        'id': result_id,
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })
            
            return formatted_results[:n_results]
            
        except Exception as e:
            logger.error(f"Failed to get related components: {e}")
            return []
    
    def get_repository_overview(self, repository_path: str) -> Optional[Dict[str, Any]]:
        """
        Get overview of a repository from the vector database.
        
        Args:
            repository_path: Path to the repository
            
        Returns:
            Repository overview or None if not found
        """
        try:
            results = self.collection.query(
                query_texts=["repository overview"],
                where={"type": "repository", "repository_path": repository_path},
                n_results=1
            )
            
            if results['documents'] and results['documents'][0]:
                return {
                    'id': results['ids'][0][0],
                    'document': results['documents'][0][0],
                    'metadata': results['metadatas'][0][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get repository overview: {e}")
            return None
    
    def delete_repository(self, repository_path: str) -> bool:
        """
        Delete all data for a repository.
        
        Args:
            repository_path: Path to the repository to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get all documents for this repository
            results = self.collection.get(
                where={"repository_path": repository_path}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} documents for repository {repository_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete repository data: {e}")
            return False
    
    def _generate_id(self, doc_type: str, identifier: str, repository_path: str = "", additional_context: str = "") -> str:
        """Generate a unique ID for a document."""
        # Use a more unique identifier by including repository path, doc type, and additional context
        # This ensures uniqueness across repos while keeping IDs stable for duplicate detection
        
        # Ensure identifier is not empty
        if not identifier.strip():
            identifier = f"unknown_{hash(str(repository_path) + doc_type) % 10000:04d}"
        
        # Clean the repository path to make it more stable
        repo_name = Path(repository_path).name if repository_path else "unknown_repo"
        
        # Build unique content string
        content_parts = [doc_type, repo_name, identifier]
        if additional_context:
            content_parts.append(additional_context)
        
        content = ":".join(content_parts)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _create_repository_document(self, analysis_data: Dict[str, Any], repository_path: str) -> str:
        """Create a document string for repository-level data."""
        doc_parts = [
            f"Repository: {repository_path}",
            f"Project Type: {analysis_data.get('project_type', 'unknown')}",
            f"Total Files: {analysis_data.get('total_files', 0)}",
            f"Total Functions: {analysis_data.get('total_functions', 0)}",
            f"Total Classes: {analysis_data.get('total_classes', 0)}",
            f"Languages: {', '.join(analysis_data.get('languages_detected', []))}",
        ]
        
        # Add AI components if present
        ai_components = analysis_data.get('metadata', {}).get('ai_components', {})
        if ai_components:
            frameworks = ai_components.get('frameworks_detected', [])
            if frameworks:
                doc_parts.append(f"AI/ML Frameworks: {', '.join(frameworks)}")
        
        return "\n".join(doc_parts)
    
    def _create_module_document(self, module: Dict[str, Any]) -> str:
        """Create a document string for module-level data."""
        doc_parts = [
            f"Module: {module.get('module_name', '')}",
            f"Path: {module.get('module_path', '')}",
            f"Type: {module.get('module_type', 'module')}",
            f"Description: {module.get('description', '')}",
        ]
        
        # Add metrics information
        metrics = module.get('metrics', {})
        if metrics:
            doc_parts.append(f"Lines of Code: {metrics.get('total_lines', 0)}")
            doc_parts.append(f"Functions: {metrics.get('function_count', 0)}")
            doc_parts.append(f"Classes: {metrics.get('class_count', 0)}")
        
        # Add complexity information
        complexity = module.get('complexity', {})
        if complexity:
            doc_parts.append(f"Cyclomatic Complexity: {complexity.get('cyclomatic_complexity', 0.0)}")
        
        # Add docstrings
        docstrings = module.get('docstrings', {})
        if docstrings:
            module_docstring = docstrings.get('module', '')
            if module_docstring:
                doc_parts.append(f"Documentation: {module_docstring}")
        
        return "\n".join(doc_parts)
    
    def _create_function_document(self, func: Dict[str, Any], module: Dict[str, Any]) -> str:
        """Create a document string for function-level data."""
        doc_parts = [
            f"Function: {func.get('name', '')}",
            f"Module: {module.get('module_name', '')}",
            f"Signature: {func.get('signature', '')}",
            f"Docstring: {func.get('docstring', '')}",
            f"Complexity: {func.get('complexity', 0.0)}",
            f"Lines: {func.get('line_start', 0)}-{func.get('line_end', 0)}",
        ]
        
        # Add parameters information
        params = func.get('parameters', [])
        if params:
            param_names = [p.get('name', '') for p in params]
            doc_parts.append(f"Parameters: {', '.join(param_names)}")
        
        # Add return type
        return_type = func.get('return_type', '')
        if return_type:
            doc_parts.append(f"Returns: {return_type}")
        
        return "\n".join(doc_parts)
    
    def _create_class_document(self, cls: Dict[str, Any], module: Dict[str, Any]) -> str:
        """Create a document string for class-level data."""
        doc_parts = [
            f"Class: {cls.get('name', '')}",
            f"Module: {module.get('module_name', '')}",
            f"Docstring: {cls.get('docstring', '')}",
            f"Lines: {cls.get('line_start', 0)}-{cls.get('line_end', 0)}",
        ]
        
        # Add inheritance information
        bases = cls.get('bases', [])
        if bases:
            doc_parts.append(f"Inherits from: {', '.join(bases)}")
        
        # Add methods information
        methods = cls.get('methods', [])
        if methods:
            method_names = [m.get('name', '') for m in methods]
            doc_parts.append(f"Methods: {', '.join(method_names)}")
        
        return "\n".join(doc_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database."""
        try:
            # Get collection info
            collection_count = self.collection.count()
            
            # Get breakdown by type
            type_counts = {}
            for doc_type in ['repository', 'module', 'function', 'class']:
                try:
                    results = self.collection.get(where={"type": doc_type})
                    type_counts[doc_type] = len(results['ids']) if results['ids'] else 0
                except Exception:
                    type_counts[doc_type] = 0
            
            return {
                'total_documents': collection_count,
                'document_types': type_counts,
                'database_path': str(self.db_path),
                'collection_name': self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
