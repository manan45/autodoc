#!/usr/bin/env python3
"""
Auto Documentation Generation System - New Architecture

This is the new main entry point using the scalable architecture.
It provides a clean separation of concerns and improved maintainability.
"""

import argparse
import sys
import logging
import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Disable ChromaDB telemetry to prevent telemetry errors
os.environ['ANONYMIZED_TELEMETRY'] = 'false'

# Core imports
from .core.services.analysis_service import AnalysisService
from .core.repositories.file_repository import FileRepository
from .core.repositories.cache_repository import CacheRepository
from .core.exceptions.analysis_exceptions import AnalysisError
from .core.exceptions.generation_exceptions import GenerationError

# Infrastructure imports
from .infrastructure.config.settings import Settings
from .infrastructure.config.logging_config import setup_logging
from .infrastructure.supabase_client import initialize_supabase

# CLI imports  
from .cli.commands.analyze_command import AnalyzeCommand
from .cli.commands.generate_command import GenerateCommand
from .cli.commands.serve_command import ServeCommand
from .cli.commands.coordinate_command import CoordinateCommand
from .cli.utils.argument_parser import create_argument_parser
from .cli.utils.output_formatter import OutputFormatter

# Analyzer imports
from .analyzers.code.ast_analyzer import ASTAnalyzer
from .analyzers.ai.framework_detector import FrameworkDetector
from .analyzers.quality.metrics_analyzer import MetricsAnalyzer

logger = logging.getLogger(__name__)


class AutoDocGenerator:
    """
    Main application class for the auto documentation generator.
    
    This class orchestrates the entire documentation generation process
    using the new scalable architecture.
    """
    
    def __init__(self, config_path: str = "documentor.yaml"):
        """
        Initialize the auto doc generator.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.settings = Settings(config_path)
        self.config = self.settings.get_config()
        
        # Setup logging
        setup_logging(self.config)
        
        # Initialize Supabase early
        self._initialize_supabase()
        
        # Initialize repositories
        self.file_repository = FileRepository()
        self.cache_repository = CacheRepository(self.config.get('cache', {}))
        
        # Initialize services
        self.analysis_service = AnalysisService(
            file_repository=self.file_repository,
            cache_repository=self.cache_repository,
            config=self.config
        )
        
        # Initialize and inject analyzers
        self._setup_analyzers()
        
        # Initialize output formatter
        self.output_formatter = OutputFormatter(self.config)
        
        # Initialize commands
        self.commands = {
            'analyze': AnalyzeCommand(self.analysis_service, self.output_formatter),
            'generate': GenerateCommand(self.analysis_service, self.output_formatter),
            'serve': ServeCommand(self.file_repository, self.config),
            'coordinate': CoordinateCommand(self.config, self.output_formatter),
        }
    
    def _initialize_supabase(self):
        """Initialize Supabase client early in the application lifecycle."""
        try:
            success = initialize_supabase(self.config)
            if success:
                logger.info("✅ Supabase initialized successfully")
            else:
                logger.info("ℹ️  Supabase not configured - using memory storage")
        except Exception as e:
            logger.warning(f"Supabase initialization failed: {e}")
    
    def _setup_analyzers(self):
        """Initialize and inject analyzers into the analysis service."""
        try:
            # Create analyzer config with exclude patterns
            analyzer_config = {
                'analysis': {
                    'include_patterns': self.analysis_service.include_patterns,
                    'exclude_patterns': self.analysis_service.exclude_patterns,
                    **self.config.get('analysis', {})
                }
            }
            
            # Initialize code analyzer
            code_analyzer = ASTAnalyzer(analyzer_config)
            
            # Initialize AI analyzer (framework detector)
            ai_analyzer = FrameworkDetector(analyzer_config)
            
            # Initialize quality analyzer
            quality_analyzer = MetricsAnalyzer(analyzer_config)
            
            # Inject analyzers into the analysis service
            self.analysis_service.set_analyzers(
                code_analyzer=code_analyzer,
                ai_analyzer=ai_analyzer,
                quality_analyzer=quality_analyzer
            )
            
            logger.info("Analyzers initialized and injected successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup analyzers: {e}")
            # Continue without analyzers - will result in limited analysis
    
    def run(self, args: argparse.Namespace) -> int:
        """
        Run the application with given arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            start_time = datetime.now()
            
            logger.info("🚀 Auto Documentation Generation System")
            logger.info(f"📁 Repository: {Path(args.repo).resolve()}")
            logger.info(f"📊 Output: {Path(args.output).resolve()}")
            logger.info(f"⏰ Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Determine which commands to run
            commands_to_run = self._determine_commands(args)
            
            # Execute commands
            results = {}
            for command_name in commands_to_run:
                if command_name in self.commands:
                    logger.info(f"Executing command: {command_name}")
                    result = self.commands[command_name].execute(args)
                    results[command_name] = result
                else:
                    logger.warning(f"Unknown command: {command_name}")
            
            # Print summary
            self._print_summary(results, start_time)
            
            return 0
            
        except (AnalysisError, GenerationError) as e:
            logger.error(f"❌ {type(e).__name__}: {e}")
            return 1
        except KeyboardInterrupt:
            logger.info("🛑 Process interrupted by user")
            return 130
        except Exception as e:
            logger.exception(f"❌ Unexpected error: {e}")
            return 1
    
    def _determine_commands(self, args: argparse.Namespace) -> list:
        """Determine which commands to run based on arguments."""
        commands = []
        
        # If no specific action, default to coordinated workflow
        if not any([args.analyze, args.generate, args.serve, args.coordinate, getattr(args, 'debug', False)]):
            commands.append('coordinate')
        else:
            # When coordinate is requested, treat it as the default orchestrator
            # for analysis and generation, and run it BEFORE serving.
            if args.coordinate:
                commands.append('coordinate')
            else:
                if args.analyze:
                    commands.append('analyze')
                if args.generate:
                    commands.append('generate')
            
            # Serve should come after generation/coordinator
            if args.serve:
                commands.append('serve')
            
            # Debug interface last
            if getattr(args, 'debug', False):
                commands.append('debug')
        
        return commands
    
    def _print_summary(self, results: Dict[str, Any], start_time: datetime):
        """Print execution summary."""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info("📊 EXECUTION SUMMARY")
        logger.info("=" * 60)
        
        for command_name, result in results.items():
            if result.get('success', True):
                logger.info(f"✅ {command_name.title()}: Success")
                if 'stats' in result:
                    stats = result['stats']
                    for key, value in stats.items():
                        logger.info(f"   • {key.replace('_', ' ').title()}: {value}")
            else:
                logger.error(f"❌ {command_name.title()}: Failed")
                if 'error' in result:
                    logger.error(f"   Error: {result['error']}")
        
        logger.info(f"⏰ Total Duration: {duration:.2f} seconds")
        logger.info(f"🎉 Process completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Main entry point."""
    try:
        # Parse arguments
        parser = create_argument_parser()
        args = parser.parse_args()
        
        # Create and run application
        app = AutoDocGenerator(args.config)
        return app.run(args)
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
