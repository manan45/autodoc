"""
Data models for documentation generation results.

This module defines the data structures used to represent documentation
generation results and configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pathlib import Path


class DocumentationType(Enum):
    """Types of documentation that can be generated."""
    
    OVERVIEW = "overview"
    ARCHITECTURE = "architecture"
    API_REFERENCE = "api_reference"
    ONBOARDING = "onboarding"
    AI_MODELS = "ai_models"
    AI_PIPELINES = "ai_pipelines"
    QUALITY_REPORT = "quality_report"
    COMPLEXITY_REPORT = "complexity_report"


class OutputFormat(Enum):
    """Supported output formats for documentation."""
    
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"
    JSON = "json"


@dataclass
class TemplateData:
    """Data structure for template rendering."""
    
    template_name: str
    data: Dict[str, Any] = field(default_factory=dict)
    output_path: str = ""
    format: OutputFormat = OutputFormat.HTML
    
    def add_data(self, key: str, value: Any) -> None:
        """Add data to the template context."""
        self.data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data from the template context."""
        return self.data.get(key, default)


@dataclass
class DocumentSection:
    """A section within a documentation document."""
    
    title: str
    content: str = ""
    subsections: List['DocumentSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    order: int = 0
    
    def add_subsection(self, section: 'DocumentSection') -> None:
        """Add a subsection to this section."""
        self.subsections.append(section)
        # Sort subsections by order
        self.subsections.sort(key=lambda s: s.order)
    
    def get_subsection(self, title: str) -> Optional['DocumentSection']:
        """Get a subsection by title."""
        for section in self.subsections:
            if section.title == title:
                return section
        return None
    
    @property
    def total_content_length(self) -> int:
        """Get total content length including subsections."""
        total = len(self.content)
        for subsection in self.subsections:
            total += subsection.total_content_length
        return total


@dataclass
class DocumentationPage:
    """A complete documentation page."""
    
    page_type: DocumentationType
    title: str
    file_name: str
    sections: List[DocumentSection] = field(default_factory=list)
    template_data: TemplateData = field(default_factory=lambda: TemplateData(""))
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_section(self, section: DocumentSection) -> None:
        """Add a section to the page."""
        self.sections.append(section)
        # Sort sections by order
        self.sections.sort(key=lambda s: s.order)
    
    def get_section(self, title: str) -> Optional[DocumentSection]:
        """Get a section by title."""
        for section in self.sections:
            if section.title == title:
                return section
        return None
    
    @property
    def total_content_length(self) -> int:
        """Get total content length of the page."""
        return sum(section.total_content_length for section in self.sections)
    
    @property
    def section_count(self) -> int:
        """Get total number of sections including subsections."""
        count = len(self.sections)
        for section in self.sections:
            count += len(section.subsections)
        return count


@dataclass
class DiagramData:
    """Data structure for generated diagrams."""
    
    diagram_type: str  # mermaid, plantuml, graphviz, etc.
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_mermaid(self) -> bool:
        """Check if this is a Mermaid diagram."""
        return self.diagram_type.lower() == 'mermaid'
    
    @property
    def is_plantuml(self) -> bool:
        """Check if this is a PlantUML diagram."""
        return self.diagram_type.lower() == 'plantuml'


@dataclass
class AssetFile:
    """Represents a static asset file (CSS, JS, images)."""
    
    file_path: str
    content: str = ""
    file_type: str = ""  # css, js, image, etc.
    is_external: bool = False  # Whether it's an external URL
    
    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return Path(self.file_path).suffix.lower()
    
    @property
    def is_stylesheet(self) -> bool:
        """Check if this is a CSS file."""
        return self.file_extension == '.css' or self.file_type == 'css'
    
    @property
    def is_script(self) -> bool:
        """Check if this is a JavaScript file."""
        return self.file_extension == '.js' or self.file_type == 'js'


@dataclass
class DocumentationResult:
    """Complete result of documentation generation."""
    
    output_directory: str
    format: OutputFormat
    generated_at: datetime = field(default_factory=datetime.now)
    
    # Generated pages
    pages: List[DocumentationPage] = field(default_factory=list)
    
    # Generated diagrams
    diagrams: List[DiagramData] = field(default_factory=list)
    
    # Static assets (CSS, JS, images)
    assets: List[AssetFile] = field(default_factory=list)
    
    # Generation metadata
    generation_stats: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_page(self, page: DocumentationPage) -> None:
        """Add a documentation page."""
        self.pages.append(page)
    
    def get_page(self, page_type: DocumentationType) -> Optional[DocumentationPage]:
        """Get a page by type."""
        for page in self.pages:
            if page.page_type == page_type:
                return page
        return None
    
    def add_diagram(self, diagram: DiagramData) -> None:
        """Add a diagram."""
        self.diagrams.append(diagram)
    
    def add_asset(self, asset: AssetFile) -> None:
        """Add a static asset."""
        self.assets.append(asset)
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    @property
    def total_pages(self) -> int:
        """Get total number of pages generated."""
        return len(self.pages)
    
    @property
    def total_diagrams(self) -> int:
        """Get total number of diagrams generated."""
        return len(self.diagrams)
    
    @property
    def total_assets(self) -> int:
        """Get total number of assets."""
        return len(self.assets)
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate (pages without errors)."""
        if not self.pages:
            return 100.0
        
        successful_pages = len([p for p in self.pages if not self.has_errors])
        return (successful_pages / len(self.pages)) * 100.0
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """Get a summary of the generation process."""
        return {
            'output_directory': self.output_directory,
            'format': self.format.value,
            'generated_at': self.generated_at.isoformat(),
            'stats': {
                'total_pages': self.total_pages,
                'total_diagrams': self.total_diagrams,
                'total_assets': self.total_assets,
                'success_rate': self.success_rate,
                'has_errors': self.has_errors,
                'has_warnings': self.has_warnings,
                'error_count': len(self.errors),
                'warning_count': len(self.warnings),
            },
            'pages': [
                {
                    'type': page.page_type.value,
                    'title': page.title,
                    'file_name': page.file_name,
                    'section_count': page.section_count,
                    'content_length': page.total_content_length,
                }
                for page in self.pages
            ],
            'errors': self.errors,
            'warnings': self.warnings,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.get_generation_summary()
