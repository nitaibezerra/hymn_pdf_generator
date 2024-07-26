from dataclasses import dataclass
from typing import Optional

from config import Configuration
from reportlab.pdfbase.pdfmetrics import stringWidth


@dataclass
class MetaHymn:
    """
    Meta class representing a hymn. It's necessary so the Hymn is
    composed by Configuration and MetaHymn in this order since
    Configuration has default properties and can't be after non-default
    properties.
    """
    number: int
    title: str
    style: Optional[str]
    offered_to: Optional[str]
    extra_instructions: Optional[str]
    text: str
    repetitions: Optional[str]
    received_at: Optional[str]


@dataclass
class Hymn(Configuration, MetaHymn):
    """
    Data class representing a hymn.
    """
    @property
    def adjusted_font_size(self) -> int:
        """
        Calculate the adjusted font size to fit the text within the given width.

        :return: The adjusted font size.
        """
        font_size = self.default_body_font_size
        max_width = self.pagesize[0] - 2 * self.margin
        max_width -= 14  # Adjust for the leading

        for line in self.text.split("\n"):
            while stringWidth(line, self.font_name, font_size) > max_width and font_size > 6:
                font_size -= 1

        return font_size
