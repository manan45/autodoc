"""
Documentation server for serving generated documentation.

This module provides a Flask-based web server for serving the generated
HTML documentation with additional features like search and analytics.
"""

import logging
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

try:
    from flask import Flask, render_template_string, send_from_directory, jsonify, request
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

logger = logging.getLogger(__name__)


class DocumentationServer:
    """
    Flask-based server for serving generated documentation.
    
    Provides a web interface for viewing documentation with additional
    features like semantic search and analytics.
    """
    
    def __init__(self, docs_dir: str, host: str = '127.0.0.1', 
                 port: int = 8000, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the documentation server.
        
        Args:
            docs_dir: Directory containing generated documentation
            host: Host to bind to
            port: Port to serve on
            config: Optional configuration dictionary
        """
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required for the documentation server. Install with: pip install flask flask-cors")
        
        self.docs_dir = Path(docs_dir)
        self.host = host
        self.port = port
        self.config = config or {}
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'auto-doc-generator-secret-key'
        
        # Enable CORS for API endpoints
        CORS(self.app)
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"Documentation server initialized for {self.docs_dir}")
    
    def _setup_routes(self):
        """Setup Flask routes for the documentation server."""
        
        @self.app.route('/')
        def index():
            """Serve the main documentation index."""
            index_path = self.docs_dir / 'index.html'
            if index_path.exists():
                return send_from_directory(str(self.docs_dir), 'index.html')
            else:
                return self._create_directory_listing()
        
        @self.app.route('/<path:filename>')
        def serve_file(filename):
            """Serve static documentation files."""
            try:
                return send_from_directory(str(self.docs_dir), filename)
            except Exception as e:
                logger.error(f"Error serving file {filename}: {e}")
                return f"File not found: {filename}", 404
        
        @self.app.route('/api/search')
        def search():
            """API endpoint for searching documentation."""
            query = request.args.get('q', '')
            if not query:
                return jsonify({'error': 'No query provided'}), 400
            
            try:
                results = self._search_documentation(query)
                return jsonify({
                    'query': query,
                    'results': results,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Search error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/repository-data')
        def repository_data():
            """Basic repository data for frontend widgets."""
            try:
                data = self._get_repository_data()
                return jsonify(data)
            except Exception as e:
                logger.error(f"Repository data error: {e}")
                return jsonify({'error': f'Repository data unavailable: {e}'}), 500
        
        @self.app.route('/search/search_index.json')
        def search_index():
            """Provide a lightweight search index for client-side search."""
            try:
                index = self._build_search_index()
                return jsonify(index)
            except Exception as e:
                logger.error(f"Search index error: {e}")
                return jsonify({'error': f'Search index unavailable: {e}'}), 500
        
        @self.app.route('/api/stats')
        def stats():
            """API endpoint for documentation statistics."""
            try:
                stats_data = self._get_documentation_stats()
                return jsonify(stats_data)
            except Exception as e:
                logger.error(f"Stats error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/health')
        def health():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'docs_dir': str(self.docs_dir),
                'files_count': len(list(self.docs_dir.glob('*.html'))) if self.docs_dir.exists() else 0
            })
        
        @self.app.errorhandler(404)
        def not_found(error):
            """Handle 404 errors."""
            return self._create_404_page(), 404
        
        @self.app.errorhandler(500)
        def server_error(error):
            """Handle 500 errors."""
            return self._create_500_page(str(error)), 500
    
    def _create_directory_listing(self) -> str:
        """Create a directory listing page when index.html is not found."""
        html_files = list(self.docs_dir.glob('*.html')) if self.docs_dir.exists() else []
        
        return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation Directory</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 40px; 
            background-color: #f5f5f5; 
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }
        h1 { color: #333; margin-bottom: 30px; }
        .file-list { list-style: none; padding: 0; }
        .file-list li { 
            margin: 10px 0; 
            padding: 15px; 
            background: #f8f9fa; 
            border-radius: 5px; 
            border-left: 4px solid #007bff; 
        }
        .file-list a { 
            text-decoration: none; 
            color: #007bff; 
            font-weight: 500; 
        }
        .file-list a:hover { text-decoration: underline; }
        .no-files { 
            text-align: center; 
            color: #6c757d; 
            font-style: italic; 
            padding: 40px; 
        }
        .api-info {
            margin-top: 30px;
            padding: 20px;
            background: #e3f2fd;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Documentation Files</h1>
        
        {% if html_files %}
            <ul class="file-list">
            {% for file in html_files %}
                <li>
                    <a href="/{{ file.name }}">{{ file.name }}</a>
                    <small style="color: #6c757d; float: right;">
                        {{ file.stat().st_size | filesizeformat }}
                    </small>
                </li>
            {% endfor %}
            </ul>
        {% else %}
            <div class="no-files">
                <h3>No documentation files found</h3>
                <p>Run the documentation generator first to create HTML files.</p>
            </div>
        {% endif %}
        
        <div class="api-info">
            <h3>🔧 API Endpoints</h3>
            <ul>
                <li><code>GET /api/search?q=query</code> - Search documentation</li>
                <li><code>GET /api/stats</code> - Get documentation statistics</li>
                <li><code>GET /api/health</code> - Health check</li>
            </ul>
        </div>
    </div>
</body>
</html>
        ''', html_files=html_files)
    
    def _create_404_page(self) -> str:
        """Create a custom 404 error page."""
        return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Not Found</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; padding: 0; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; height: 100vh; 
            display: flex; align-items: center; justify-content: center;
        }
        .error-container { text-align: center; }
        h1 { font-size: 6rem; margin: 0; opacity: 0.8; }
        h2 { font-size: 2rem; margin: 20px 0; }
        p { font-size: 1.2rem; opacity: 0.9; }
        a { color: #fff; text-decoration: underline; }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>404</h1>
        <h2>Page Not Found</h2>
        <p>The requested documentation page could not be found.</p>
        <p><a href="/">← Back to Documentation Home</a></p>
    </div>
</body>
</html>
        ''')
    
    def _create_500_page(self, error_message: str) -> str:
        """Create a custom 500 error page."""
        return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Server Error</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; padding: 0; 
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white; height: 100vh; 
            display: flex; align-items: center; justify-content: center;
        }
        .error-container { text-align: center; max-width: 600px; padding: 20px; }
        h1 { font-size: 4rem; margin: 0; opacity: 0.8; }
        h2 { font-size: 2rem; margin: 20px 0; }
        p { font-size: 1.2rem; opacity: 0.9; }
        .error-details { 
            background: rgba(0,0,0,0.2); 
            padding: 20px; 
            border-radius: 5px; 
            margin: 20px 0; 
            font-family: monospace; 
        }
        a { color: #fff; text-decoration: underline; }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>500</h1>
        <h2>Server Error</h2>
        <p>An internal server error occurred while processing your request.</p>
        <div class="error-details">{{ error_message }}</div>
        <p><a href="/">← Back to Documentation Home</a></p>
    </div>
</body>
</html>
        ''', error_message=error_message)
    
    def _search_documentation(self, query: str) -> list:
        """
        Search through documentation files for the given query.
        
        This is a simple text-based search. In a full implementation,
        this could use the vector database for semantic search.
        """
        results = []
        
        if not self.docs_dir.exists():
            return results
        
        # Search through HTML files
        for html_file in self.docs_dir.glob('*.html'):
            try:
                content = html_file.read_text(encoding='utf-8')
                
                # Simple case-insensitive search
                if query.lower() in content.lower():
                    # Extract a snippet around the match
                    content_lower = content.lower()
                    query_lower = query.lower()
                    match_index = content_lower.find(query_lower)
                    
                    if match_index != -1:
                        start = max(0, match_index - 100)
                        end = min(len(content), match_index + len(query) + 100)
                        snippet = content[start:end].strip()
                        
                        results.append({
                            'file': html_file.name,
                            'title': self._extract_title(content),
                            'snippet': snippet,
                            'url': f'/{html_file.name}'
                        })
                        
            except Exception as e:
                logger.error(f"Error searching file {html_file}: {e}")
        
        return results[:10]  # Limit to 10 results
    
    def _extract_title(self, html_content: str) -> str:
        """Extract title from HTML content."""
        try:
            import re
            title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
            if title_match:
                return title_match.group(1).strip()
        except Exception:
            pass
        return "Untitled"
    
    def _get_documentation_stats(self) -> Dict[str, Any]:
        """Get statistics about the documentation."""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'docs_directory': str(self.docs_dir),
            'total_files': 0,
            'html_files': 0,
            'css_files': 0,
            'js_files': 0,
            'total_size': 0,
            'files': []
        }
        
        if not self.docs_dir.exists():
            return stats
        
        try:
            for file_path in self.docs_dir.rglob('*'):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    stats['total_files'] += 1
                    stats['total_size'] += file_size
                    
                    # Count by file type
                    if file_path.suffix.lower() == '.html':
                        stats['html_files'] += 1
                    elif file_path.suffix.lower() == '.css':
                        stats['css_files'] += 1
                    elif file_path.suffix.lower() == '.js':
                        stats['js_files'] += 1
                    
                    # Add to files list (limit to 50 for performance)
                    if len(stats['files']) < 50:
                        stats['files'].append({
                            'name': file_path.name,
                            'path': str(file_path.relative_to(self.docs_dir)),
                            'size': file_size,
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
        
        except Exception as e:
            logger.error(f"Error getting documentation stats: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def _get_repository_data(self) -> Dict[str, Any]:
        """Assemble minimal repository data from available outputs."""
        result = {
            'modules': [],
            'totalFiles': 0,
            'totalFunctions': 0,
            'totalClasses': 0
        }
        
        if not self.docs_dir.exists():
            return result
        
        try:
            # Prefer a precomputed data file if present
            for candidate in ['repository_data.json', 'analysis.json', 'modules.json', 'quality_data.json']:
                candidate_path = self.docs_dir / candidate
                if candidate_path.exists():
                    with candidate_path.open('r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Normalize into expected structure if possible
                        if isinstance(data, dict) and 'modules' in data:
                            result.update({
                                'modules': data.get('modules') or [],
                                'totalFiles': data.get('totalFiles') or data.get('total_files') or 0,
                                'totalFunctions': data.get('totalFunctions') or data.get('total_functions') or 0,
                                'totalClasses': data.get('totalClasses') or data.get('total_classes') or 0,
                            })
                            return result
                        # quality_data.json may store module-like entries
                        if isinstance(data, dict) and 'files' in data:
                            files = data.get('files') or []
                            modules = []
                            for item in files:
                                if not isinstance(item, dict):
                                    continue
                                modules.append({
                                    'name': item.get('module') or item.get('name') or item.get('path') or 'Unknown',
                                    'path': item.get('path') or item.get('module') or item.get('name') or '',
                                    'functions': item.get('functions') or [],
                                    'classes': item.get('classes') or [],
                                    'description': item.get('docstring') or ''
                                })
                            result['modules'] = modules
                            result['totalFiles'] = len(modules)
                            return result
            
            # Fallback: infer modules from HTML files present
            for html_path in sorted(self.docs_dir.glob('*.html')):
                if html_path.name in {'index.html', 'api.html', 'architecture.html', 'components.html'}:
                    continue
                try:
                    content = html_path.read_text(encoding='utf-8')
                    title = self._extract_title(content)
                    result['modules'].append({
                        'name': title or html_path.stem,
                        'path': html_path.name,
                        'functions': [],
                        'classes': [],
                        'description': ''
                    })
                except Exception:
                    continue
            result['totalFiles'] = len(result['modules'])
            return result
        except Exception as e:
            logger.error(f"Failed assembling repository data: {e}")
            raise Exception(f"Repository data assembly failed: {e}")
    
    def _build_search_index(self) -> list:
        """Build a simple search index from HTML files in docs directory."""
        index = []
        if not self.docs_dir.exists():
            return index
        try:
            import re
            tag_re = re.compile(r'<[^>]+>')
            ws_re = re.compile(r'\s+')
            
            for html_path in sorted(self.docs_dir.glob('*.html')):
                try:
                    content = html_path.read_text(encoding='utf-8')
                    title = self._extract_title(content)
                    # Very basic body extraction
                    body_match = re.search(r'<body[\s\S]*?>([\s\S]*?)</body>', content, re.IGNORECASE)
                    body_html = body_match.group(1) if body_match else content
                    text = tag_re.sub(' ', body_html)
                    text = ws_re.sub(' ', text).strip()
                    snippet = text[:2000]
                    index.append({
                        'title': title or html_path.stem,
                        'content': snippet,
                        'path': html_path.name
                    })
                except Exception:
                    continue
            return index
        except Exception as e:
            logger.error(f"Failed building search index: {e}")
            raise Exception(f"Search index build failed: {e}")
    
    def run(self, debug: bool = False):
        """
        Start the documentation server.
        
        Args:
            debug: Enable Flask debug mode
        """
        try:
            logger.info(f"Starting documentation server at http://{self.host}:{self.port}")
            self.app.run(
                host=self.host,
                port=self.port,
                debug=debug,
                use_reloader=False  # Disable reloader to avoid issues
            )
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise
