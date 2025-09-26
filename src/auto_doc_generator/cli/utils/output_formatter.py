"""
Output formatting utilities for CLI.

This module provides utilities for formatting and displaying output
in the command-line interface.
"""

import sys
from typing import Dict, Any, List
from datetime import datetime


class OutputFormatter:
    """Formats output for CLI display."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize output formatter.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.verbose = self.config.get('verbose', False)
    
    def print_header(self, title: str) -> None:
        """Print a formatted header."""
        print("=" * 60)
        print(f"🚀 {title}")
        print("=" * 60)
    
    def print_section(self, title: str) -> None:
        """Print a section header."""
        print(f"\n📊 {title}")
        print("-" * 40)
    
    def print_success(self, message: str) -> None:
        """Print a success message."""
        print(f"✅ {message}")
    
    def print_error(self, message: str) -> None:
        """Print an error message."""
        print(f"❌ {message}", file=sys.stderr)
    
    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        print(f"⚠️ {message}")
    
    def print_info(self, message: str) -> None:
        """Print an info message."""
        print(f"ℹ️ {message}")
    
    def print_stats(self, stats: Dict[str, Any], title: str = "Statistics") -> None:
        """Print formatted statistics."""
        self.print_section(title)
        
        for key, value in stats.items():
            formatted_key = key.replace('_', ' ').title()
            if isinstance(value, (int, float)):
                if isinstance(value, float):
                    print(f"   • {formatted_key}: {value:.2f}")
                else:
                    print(f"   • {formatted_key}: {value:,}")
            else:
                print(f"   • {formatted_key}: {value}")
    
    def print_list(self, items: List[str], title: str, bullet: str = "•") -> None:
        """Print a formatted list."""
        if not items:
            return
        
        self.print_section(title)
        for item in items:
            print(f"   {bullet} {item}")
    
    def print_table(self, data: List[Dict[str, Any]], headers: List[str]) -> None:
        """Print a simple table."""
        if not data or not headers:
            return
        
        # Calculate column widths
        widths = {}
        for header in headers:
            widths[header] = len(header)
        
        for row in data:
            for header in headers:
                value_len = len(str(row.get(header, '')))
                widths[header] = max(widths[header], value_len)
        
        # Print header
        header_row = " | ".join(h.ljust(widths[h]) for h in headers)
        print(header_row)
        print("-" * len(header_row))
        
        # Print data rows
        for row in data:
            data_row = " | ".join(str(row.get(h, '')).ljust(widths[h]) for h in headers)
            print(data_row)
    
    def print_progress(self, current: int, total: int, message: str = "") -> None:
        """Print progress indicator."""
        if total == 0:
            return
        
        percentage = (current / total) * 100
        bar_length = 30
        filled_length = int(bar_length * current // total)
        
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        progress_msg = f"\r[{bar}] {percentage:.1f}% ({current}/{total})"
        if message:
            progress_msg += f" {message}"
        
        print(progress_msg, end="", flush=True)
        
        if current == total:
            print()  # New line when complete
    
    def print_analysis_summary(self, analysis_result: Dict[str, Any]) -> None:
        """Print analysis result summary."""
        self.print_header("ANALYSIS SUMMARY")
        
        overview = analysis_result.get('overview', {})
        
        # Basic statistics
        stats = {
            'Total Files': overview.get('total_files', 0),
            'Total Lines': overview.get('total_lines', 0),
            'Total Functions': overview.get('total_functions', 0),
            'Total Classes': overview.get('total_classes', 0),
            'Project Type': overview.get('project_type', 'Unknown'),
        }
        
        self.print_stats(stats, "Code Statistics")
        
        # Languages
        languages = overview.get('languages_detected', [])
        if languages:
            self.print_list(languages, "Languages Detected")
        
        # Quality metrics if available
        if 'quality' in analysis_result:
            quality = analysis_result['quality']
            quality_stats = {
                'Average Quality Score': quality.get('average_score', 0),
                'Modules Analyzed': quality.get('total_modules', 0),
            }
            self.print_stats(quality_stats, "Quality Metrics")
    
    def print_generation_summary(self, result: Dict[str, Any]) -> None:
        """Print documentation generation summary."""
        self.print_header("GENERATION SUMMARY")
        
        stats = {
            'Pages Generated': result.get('total_pages', 0),
            'Diagrams Created': result.get('total_diagrams', 0),
            'Assets Copied': result.get('total_assets', 0),
            'Output Format': result.get('format', 'Unknown'),
            'Output Directory': result.get('output_directory', ''),
        }
        
        self.print_stats(stats, "Generation Statistics")
        
        # Errors and warnings
        errors = result.get('errors', [])
        warnings = result.get('warnings', [])
        
        if errors:
            self.print_list(errors, "Errors", "❌")
        
        if warnings:
            self.print_list(warnings, "Warnings", "⚠️")
        
        if not errors:
            self.print_success("Documentation generated successfully!")
    
    def print_timestamp(self, label: str = "Completed") -> None:
        """Print current timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"⏰ {label}: {timestamp}")
