from dataclasses import dataclass
from typing import List, Optional

import yaml
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from hymn_pdf_generator.repetition_bar_allocator import LevelAllocator

# from astral_shelve.pdf_generator.repetition_bar_allocator import LevelAllocator


@dataclass
class Hymn:
    """
    Data class representing a hymn.
    """
    number: int
    title: str
    style: Optional[str]
    offered_to: Optional[str]
    text: str
    repetitions: Optional[str]
    received_at: Optional[str]


class VerticalLine(Flowable):
    def __init__(self, x, y_start, y_end, thickness=0.7):
        Flowable.__init__(self)
        self.x = x
        self.y_start = y_start
        self.y_end = y_end
        self.thickness = thickness

    def draw(self):
        self.canv.setLineWidth(self.thickness)
        self.canv.line(self.x, self.y_start, self.x, self.y_end)


class HymnPDFGenerator:
    """
    A class to generate a PDF for a given hymn.
    """

    def __init__(self, hymns: List[Hymn], filename: str):
        """
        Initialize the HymnPDFGenerator with a hymn and output filename.

        :param hymn: An instance of the Hymn data class.
        :param filename: The output PDF filename.
        """
        self.hymns = hymns
        self.filename = filename
        self.pagesize = (288, 432)  # Width: 288 points (4 inches), Height: 432 points (6 inches)
        self.margin = 0.5 * inch
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """
        Set up custom paragraph styles.
        """
        self.title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Title'],
            fontName='Times-Roman',
            fontSize=14,
            leading=20,
            spaceAfter=0
        )

        self.body_style = ParagraphStyle(
            'BodyStyle',
            parent=self.styles['BodyText'],
            fontName='Times-Roman',
            fontSize=14,
            leading=16,  # Increased line spacing
            spaceAfter=0.12 * inch
        )

        self.hymn_style_style = ParagraphStyle(
            'RightAlignStyle',
            parent=self.styles['Normal'],
            fontName='Times-Roman',
            fontSize=12,
            alignment=2,  # Right align
            leading=0,
            spaceAfter=22
        )

        self.hymn_offered_to_style = ParagraphStyle(
            'LeftAlignStyle',
            parent=self.styles['Normal'],
            fontName='Times-Roman',
            fontSize=12,
            alignment=0,  # Left align
            leading=0,
            spaceAfter=22
        )

        self.received_at_style = ParagraphStyle(
            'ReceivedAtStyle',
            parent=self.styles['Normal'],
            fontName='Times-Roman',
            fontSize=10,
            alignment=2,  # Center align
            leading=12,
            spaceBefore=20
        )

    def create_pdf(self):
        """
        Create a PDF with the hymn content.
        """
        doc = SimpleDocTemplate(
            self.filename,
            pagesize=self.pagesize,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=20,
            bottomMargin=self.margin
        )

        elements = self._build_elements()
        doc.build(elements)

    def _add_vertical_lines(self, elements, hymn):
        allocator = LevelAllocator()
        line_positions = allocator.get_entries_with_levels(hymn.repetitions)

        base_y_start = -12
        one_line_height = 7
        space_between_lines = 9
        levels_distance = 6

        for line in line_positions:
            start_line = line['start'] - 1
            end_line = line['end'] - 1
            level = line['level']

            y_start = (
                base_y_start
                - (start_line * one_line_height
                   + start_line * space_between_lines)
            )
            y_end = (
                base_y_start
                - (end_line * one_line_height
                   + end_line * space_between_lines + one_line_height)
            )

            elements.append(
                VerticalLine(-(level * levels_distance), y_start, y_end))

    def _adjust_font_size(self, text: str, style: ParagraphStyle) -> ParagraphStyle:
        """
        Adjust the font size of the paragraph style to fit the text within the given width.

        :param text: The text to measure.
        :param style: The initial paragraph style.
        :param max_width: The maximum width allowed for the text.
        :return: A new ParagraphStyle with the adjusted font size.
        """
        font_size = style.fontSize
        max_width = self.pagesize[0] - 2 * self.margin
        max_width -= 16  # Adjust for the leading

        for line in text.split("\n"):
            while (stringWidth(line, style.fontName, font_size) > max_width
                   and font_size > 6):
                font_size -= 1

        new_style = ParagraphStyle(
            name=style.name,
            parent=style,
            fontName=style.fontName,
            fontSize=font_size,
            leading=font_size + 2
        )
        return new_style

    def _build_elements(self) -> List[Paragraph]:
        """
        Build the PDF elements from the hymn content.

        :return: A list of Paragraph objects for the PDF.
        """
        elements = []

        for idx, hymn in enumerate(self.hymns, start=1):
            # Add number and title
            title = f"{idx:02d}. {hymn.title} ({hymn.number:02d})"
            elements.append(Paragraph(title, self.title_style))

            # Add horizontal line
            elements.append(
                HRFlowable(width="100%", thickness=1, color="black", spaceAfter=0))

            paragraphs = hymn.text.strip().split("\n\n")

            # Add hymn offered_to aligned to the left
            offered_style = []
            if hymn.offered_to:
                offered_style.append(f'Ofertado a {hymn.offered_to}')
            if hymn.style:
                offered_style.append(hymn.style)

            # Add hymn style aligned to the right
            elements.append(
                Paragraph(' - '.join(offered_style), self.hymn_style_style))

            # Add vertical lines
            self._add_vertical_lines(elements, hymn)

            # Add body paragraphs with adjusted font size
            adjusted_style = self._adjust_font_size('\n'.join(paragraphs),
                                                    self.body_style)
            for paragraph in paragraphs:
                elements.append(
                    Paragraph(paragraph.replace("\n", "<br/>"), adjusted_style))

            # Add the received_at attribute at the bottom
            if hymn.received_at:
                elements.append(
                    Paragraph(hymn.received_at.strftime("(%d/%m/%Y)"),
                              self.received_at_style))

            # Add a page break after each hymn
            elements.append(PageBreak())

        return elements


if __name__ == "__main__":
    # Load hymns from YAML file
    with open('input/selecao_aniversario_ingrid.yaml', 'r') as file:
        data = yaml.safe_load(file)

    hymns = [
        Hymn(
            number=hymn.get('number'),
            title=hymn.get('title'),
            style=hymn.get('style'),
            offered_to=hymn.get('offered_to'),
            text=hymn.get('text'),
            repetitions=hymn.get('repetitions'),
            received_at=hymn.get('received_at')
        )
        for hymn in data['hymns']
    ]
    # Output filename
    output_filename = "output/selecao_aniversario_ingrid.pdf"

    # Create the PDF
    generator = HymnPDFGenerator(hymns, output_filename)
    generator.create_pdf()
