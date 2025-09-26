"""
Documentation generation-related exceptions.

This module defines exceptions that can occur during documentation generation.
"""


class GenerationError(Exception):
    """Base exception for documentation generation errors."""
    
    def __init__(self, message: str, template_name: str = None, output_path: str = None, details: dict = None):
        """
        Initialize generation error.
        
        Args:
            message: Error message
            template_name: Optional template name where error occurred
            output_path: Optional output path where error occurred
            details: Optional additional error details
        """
        self.template_name = template_name
        self.output_path = output_path
        self.details = details or {}
        
        context_info = []
        if template_name:
            context_info.append(f"template: {template_name}")
        if output_path:
            context_info.append(f"output: {output_path}")
        
        if context_info:
            message = f"{message} ({', '.join(context_info)})"
        
        super().__init__(message)


class TemplateError(GenerationError):
    """Exception for template processing errors."""
    pass


class OutputError(GenerationError):
    """Exception for output file generation errors."""
    pass


class DiagramGenerationError(GenerationError):
    """Exception for diagram generation errors."""
    pass


class AssetGenerationError(GenerationError):
    """Exception for asset file generation errors."""
    pass


class RenderingError(GenerationError):
    """Exception for template rendering errors."""
    pass
