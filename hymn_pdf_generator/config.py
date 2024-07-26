from dataclasses import dataclass, field

from reportlab.lib.units import inch


@dataclass
class Configuration:
    """Constant values used in multiple classes."""
    pagesize: tuple = field(default=(4 * inch, 6 * inch))
    margin: float = field(default=0.5 * inch)
    font_name: str = field(default='DejaVuSans')
    title_font_size: int = field(default=14)
    default_body_font_size: int = field(default=14)
    pagenumber_font_size: int = field(default=12)
