"""
Command-line argument parser.

This module creates and configures the argument parser for the CLI.
"""

import argparse


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Auto Documentation Generation System - New Architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --analyze --generate                    # Analyze and generate docs
  %(prog)s --coordinate                            # Run coordinated AI workflow
  %(prog)s --analyze --generate --build            # Analyze, generate, and build site
  %(prog)s --serve                                 # Serve existing documentation
  %(prog)s --repo /path/to/repo --output ./my-docs # Custom paths
        """
    )
    
    parser.add_argument(
        '--repo', 
        default='.',
        help='Path to repository to analyze (default: current directory)'
    )
    
    parser.add_argument(
        '--config',
        default='documentor.yaml',
        help='Path to documentor configuration file'
    )
    
    parser.add_argument(
        '--output',
        default='docs',
        help='Output directory for documentation'
    )
    
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze the codebase'
    )
    
    parser.add_argument(
        '--generate',
        action='store_true', 
        help='Generate documentation'
    )
    
    parser.add_argument(
        '--build',
        action='store_true',
        help='Build MkDocs site'
    )
    
    parser.add_argument(
        '--serve',
        action='store_true',
        help='Serve documentation site'
    )
    
    parser.add_argument(
        '--coordinate',
        action='store_true',
        help='Run coordinated AI workflow (MetaGPT/AutoGPT style)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port for serving site (default: 8000)'
    )
    
    parser.add_argument(
        '--format',
        choices=['html', 'markdown', 'mkdocs'],
        help='Documentation output format (default: html)'
    )
    
    parser.add_argument(
        '--deploy',
        action='store_true',
        help='Deploy to GitHub Pages (requires GitHub Actions)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Start debug interface for Supabase monitoring'
    )
    
    parser.add_argument(
        '--debug-port',
        type=int,
        default=5001,
        help='Port for debug interface (default: 5001)'
    )
    
    return parser
