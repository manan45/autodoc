"""
Serve command implementation.

This module implements the serve command for the CLI.
"""

import argparse
from typing import Dict, Any
from pathlib import Path

from ...core.repositories.file_repository import FileRepository
from ..utils.output_formatter import OutputFormatter


class ServeCommand:
    """Command for serving documentation."""
    
    def __init__(self, file_repository: FileRepository, config: Dict[str, Any]):
        """
        Initialize serve command.
        
        Args:
            file_repository: Repository for file operations
            config: Application configuration
        """
        self.file_repository = file_repository
        self.config = config
        self.formatter = OutputFormatter(config)
    
    def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Execute the serve command.
        
        Args:
            args: Command line arguments
            
        Returns:
            Dictionary with execution results
        """
        try:
            output_path = Path(args.output).resolve()
            port = args.port
            
            self.formatter.print_header("DOCUMENTATION SERVER")
            self.formatter.print_info(f"Serving from: {output_path}")
            self.formatter.print_info(f"Port: {port}")
            
            # Check if documentation exists
            if not output_path.exists():
                self.formatter.print_warning(f"Documentation directory not found: {output_path}")
                self.formatter.print_info("Run with --analyze --generate first to create documentation")
                return {
                    'success': False,
                    'error': 'Documentation not found'
                }
            
            # Import and start the documentation server
            try:
                from ...web.documentation_server import DocumentationServer
                
                host = getattr(args, 'host', '127.0.0.1')
                
                # Create and start the documentation server
                server = DocumentationServer(
                    docs_dir=str(output_path),
                    host=host,
                    port=port,
                    config=self.config
                )
                
                self.formatter.print_success(f"🚀 Starting server at http://{host}:{port}")
                self.formatter.print_info("Press Ctrl+C to stop the server")
                
                # Start the server (this will block)
                server.run()
                
            except ImportError as e:
                self.formatter.print_error(f"Flask is required for the server: {e}")
                self.formatter.print_info("Install with: pip install flask flask-cors")
                return {
                    'success': False,
                    'error': 'Flask not available'
                }
            except KeyboardInterrupt:
                self.formatter.print_info("🛑 Server stopped by user")
            
            return {
                'success': True,
                'stats': {
                    'port': port,
                    'output_directory': str(output_path),
                }
            }
            
        except Exception as e:
            self.formatter.print_error(f"Server failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
