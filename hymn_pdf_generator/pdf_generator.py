from dataclasses import dataclass, field
from functools import cached_property
from typing import List, Optional

import yaml
from reportlab.lib.pagesizes import letter
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
from reportlab.platypus.flowables import HRFlowable

from hymn_pdf_generator.repetition_bar_allocator import LevelAllocator


@dataclass
class Hymn:
    """
    Data class representing a hymn.
    """
    number: int
    title: str
    style: Optional[str]
    offered_to: Optional[str]
    extra_instructions: Optional[str]
    text: str
    repetitions: Optional[str]
    received_at: Optional[str]
    pagesize: tuple = field(default=(288, 432))
    margin: float = field(default=0.5 * inch)

    @cached_property
    def adjusted_font_size(self) -> int:
        """
        Calculate the adjusted font size to fit the text within the given width.

        :return: The adjusted font size.
        """
        font_name = 'Times-Roman'
        font_size = 14
        max_width = self.pagesize[0] - 2 * self.margin
        max_width -= 16  # Adjust for the leading

        for line in self.text.split("\n"):
            while stringWidth(line, font_name, font_size) > max_width and font_size > 6:
                font_size -= 1

        return font_size


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

        :param hymns: A list of Hymn instances.
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

    def _add_vertical_lines(self, hymn: Hymn) -> List[VerticalLine]:
        """
        Create vertical line elements based on hymn repetitions.

        :param hymn: The hymn instance.
        :return: A list of VerticalLine elements.
        """
        elements = []
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

        return elements

    def _build_title_and_header(self, idx: int, hymn: Hymn) -> List[Paragraph]:
        """
        Build the title and header elements for a hymn.

        :param idx: The index of the hymn.
        :param hymn: The hymn instance.
        :return: A list of elements for the title and header.
        """
        elements = []
        title = f"{idx:02d}. {hymn.title} ({hymn.number:02d})"
        elements.append(Paragraph(title, self.title_style))
        elements.append(HRFlowable(width="100%", thickness=1, color="black", spaceAfter=0))
        return elements

    def _build_offered_to_and_style(self, hymn: Hymn) -> List[Paragraph]:
        """
        Build the elements for the hymn offered_to and style.

        :param hymn: The hymn instance.
        :return: A list of elements for the offered_to and style.
        """
        elements = []
        offered_style = []
        if hymn.offered_to:
            offered_style.append(f'Ofertado a {hymn.offered_to}')
        if hymn.style:
            offered_style.append(hymn.style)
        elements.append(Paragraph(' - '.join(offered_style), self.hymn_style_style))
        return elements

    def _build_body_paragraphs(self, hymn: Hymn) -> List[Paragraph]:
        """
        Build the body paragraphs for a hymn with adjusted font size.

        :param hymn: The hymn instance.
        :return: A list of elements for the body paragraphs.
        """
        elements = []
        paragraphs = hymn.text.strip().split("\n\n")
        adjusted_font_size = hymn.adjusted_font_size

        adjusted_style = ParagraphStyle(
            name=self.body_style.name,
            parent=self.body_style,
            fontName=self.body_style.fontName,
            fontSize=adjusted_font_size,
            leading=adjusted_font_size + 2
        )

        for paragraph in paragraphs:
            elements.append(Paragraph(paragraph.replace("\n", "<br/>"), adjusted_style))
        return elements

    def _build_received_at(self, hymn: Hymn) -> List[Paragraph]:
        """
        Build the received_at element for a hymn.

        :param hymn: The hymn instance.
        :return: A list of elements for the received_at.
        """
        elements = []
        if hymn.received_at:
            elements.append(Paragraph(hymn.received_at.strftime("(%d/%m/%Y)"), self.received_at_style))
        return elements

    def _build_elements(self) -> List[Paragraph]:
        """
        Build the PDF elements from the hymn content.

        :return: A list of Paragraph objects for the PDF.
        """
        elements = []

        for idx, hymn in enumerate(self.hymns, start=1):
            elements.extend(self._build_title_and_header(idx, hymn))
            elements.extend(self._build_offered_to_and_style(hymn))
            elements.extend(self._add_vertical_lines(hymn))
            elements.extend(self._build_body_paragraphs(hymn))
            elements.extend(self._build_received_at(hymn))
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
            extra_instructions=hymn.get('extra_instructions'),
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
