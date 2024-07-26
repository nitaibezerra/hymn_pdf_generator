from typing import List

from config import Configuration
from models import Hymn
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from hymn_pdf_generator.repetition_bar_allocator import LevelAllocator

# Register the DejaVu Sans font
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

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


class PageNumCanvas(canvas.Canvas, Configuration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Configuration.__init__(self)  # Initialize Configuration

    def showPage(self):
        self.draw_page_number()
        super().showPage()

    def draw_page_number(self):
        page_num = self.getPageNumber() - 1  # Subtract 1 for the cover page
        if page_num > 0:
            self.setFont(self.font_name, self.pagenumber_font_size)
            self.drawRightString(self.pagesize[0] - self.margin,
                                 self.margin,
                                 str(page_num))

    def save(self):
        self.draw_page_number()
        super().save()


class HymnPDFGenerator(Configuration):
    """
    A class to generate a PDF for a given hymn.
    """

    def __init__(self, hymns: List[Hymn], filename: str, intro_name: str, name: str, owner: str):
        """
        Initialize the HymnPDFGenerator with hymns, output filename, and cover page details.

        :param hymns: A list of Hymn instances.
        :param filename: The output PDF filename.
        :param intro_name: Introduction name for the cover page.
        :param name: Name for the cover page.
        :param owner: Owner name for the cover page.
        """
        self.hymns = hymns
        self.filename = filename
        self.intro_name = intro_name
        self.name = name
        self.owner = owner
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """
        Set up custom paragraph styles.
        """
        self.cover_intro_style = ParagraphStyle(
            'CoverIntroStyle',
            parent=self.styles['Title'],
            fontName=self.font_name,
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=34
        )

        self.cover_name_style = ParagraphStyle(
            'CoverNameStyle',
            parent=self.styles['Title'],
            fontName=self.font_name,
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=34
        )

        self.cover_owner_style = ParagraphStyle(
            'CoverOwnerStyle',
            parent=self.styles['Title'],
            fontName=self.font_name,
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=24
        )

        self.title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Title'],
            fontSize=self.title_font_size,
            fontName=self.font_name,
            leading=20,
            spaceAfter=0
        )

        self.details_on_top_style = ParagraphStyle(
            'RightAlignStyle',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            alignment=2,  # Right align
            leading=12,
            spaceAfter=8
        )

        self.body_style = ParagraphStyle(
            'BodyStyle',
            parent=self.styles['BodyText'],
            fontName=self.font_name,
            fontSize=self.default_body_font_size,
            leading=16,  # Increased line spacing
            spaceAfter=0.12 * inch
        )

        self.davi_star_style = ParagraphStyle(
            'DaviStarStyle',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=0.2 * inch
        )

        self.symbols_style = ParagraphStyle(
            'SymbolsStyle',
            parent=self.styles['Normal'],
            fontName='DejaVuSans',
            fontSize=14,
            alignment=TA_CENTER,
            textColor='black',
            spaceBefore=0.3 * inch,
            spaceAfter=0.2 * inch
        )

        self.received_at_style = ParagraphStyle(
            'ReceivedAtStyle',
            parent=self.styles['Normal'],
            fontName=self.font_name,
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
        doc.build(elements, canvasmaker=PageNumCanvas)
        # doc.build(elements)

    def _build_vertical_lines(self, hymn: Hymn) -> List[VerticalLine]:
        """
        Create vertical line elements based on hymn repetitions.

        :param hymn: The hymn instance.
        :return: A list of VerticalLine elements.
        """
        elements = []
        allocator = LevelAllocator()
        line_positions = allocator.get_entries_with_levels(hymn.repetitions)

        resize_factor = hymn.adjusted_font_size / self.default_body_font_size

        base_y_start = -8 + (-4 * resize_factor)
        one_line_height = 7 * resize_factor
        space_between_lines = 9 * resize_factor
        levels_distance = 6 * resize_factor

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

    def _build_cover_page(self) -> List[Paragraph]:
        """
        Build the cover page elements.

        :return: A list of Paragraph objects for the cover page.
        """
        def br_replacement(text: str) -> Paragraph:
            return Paragraph(text.replace("\n", "<br/>"),
                             self.cover_intro_style)
        elements = [
            Spacer(1, 70),
            br_replacement(self.intro_name),
            br_replacement(self.name),
            br_replacement(self.owner),
            PageBreak(),
        ]

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
        elements.append(HRFlowable(width="100%", thickness=1, color="black", spaceAfter=2))
        return elements

    def _build_details_on_top(self, hymn: Hymn) -> List[Paragraph]:
        """
        Build the elements for the hymn offered_to, extra_instructions
        and style.

        :param hymn: The hymn instance.
        :return: A list of elements for this section.
        """
        offered_style = []
        if hymn.offered_to:
            offered_style.append(f'Ofertado a {hymn.offered_to}')
        if hymn.extra_instructions:
            offered_style.append(hymn.extra_instructions)
        if hymn.style:
            offered_style.append(hymn.style)

        style = self.details_on_top_style
        resize_factor = hymn.adjusted_font_size / self.default_body_font_size
        adjusted_style = ParagraphStyle(
            name=style.name,
            parent=style,
            fontName=self.font_name,
            spaceAfter=style.spaceAfter * resize_factor,
        )
        if offered_style:
            return [
                Paragraph(' - '.join(offered_style), adjusted_style)
            ]
        else:
            return [
                Spacer(1, 12 * resize_factor + 8)
            ]

    def _build_body_paragraphs(self, hymn: Hymn) -> List[Paragraph]:
        """
        Build the body paragraphs for a hymn with adjusted font size.

        :param hymn: The hymn instance.
        :return: A list of elements for the body paragraphs.
        """
        elements = []
        paragraphs = hymn.text.strip().split("\n\n")
        font_size = hymn.adjusted_font_size

        adjusted_style = ParagraphStyle(
            name=self.body_style.name,
            parent=self.body_style,
            fontName=self.font_name,
            fontSize=font_size,
            leading=font_size + 2
        )

        for paragraph in paragraphs:
            elements.append(Paragraph(paragraph.replace("\n", "<br/>"), adjusted_style))
        return elements

    def _build_davi_star(self) -> Paragraph:
        """
        Build the Davi star symbol element.

        :return: A Paragraph element containing the Davi star symbol.
        """
        return Paragraph("&#x2721;", self.davi_star_style)

    def _build_additional_symbols(self) -> Paragraph:
        """
        Build the additional symbols element (sun, moon, star).

        :return: A Paragraph element containing the sun, moon, and star symbols.
        """
        sun_symbol = "☀"
        moon_symbol = "☾"
        star_symbol = "★"
        symbols = f"{sun_symbol} {moon_symbol} {star_symbol}"
        return Paragraph(symbols, self.symbols_style)

    def _build_after_hymn_symbol(self, idx: int) -> Paragraph:
        """
        Pick the appropriate symbol to append based on the index.

        :param idx: The index of the hymn.
        :return: A Paragraph element containing the chosen symbol.
        """
        if idx % 3 != 0:
            return self._build_davi_star()
        else:
            return self._build_additional_symbols()

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

    def _keep_together_elements(self, body_paragraphs: List[Paragraph], last_elements: List[Paragraph]) -> List[Paragraph]:
        """
        Ensure the last elements are kept together with the last body paragraph.

        :param body_paragraphs: The body paragraphs of the hymn.
        :param last_elements: The elements to be kept together with the last body paragraph.
        :return: A list of paragraphs wrapped in KeepTogether.
        """
        elements = []
        elements.extend(KeepTogether(paragraph) for paragraph in body_paragraphs[:-1])
        elements.append(KeepTogether([body_paragraphs[-1], *last_elements]))
        return elements


    def _build_elements(self) -> List[Paragraph]:
        """
        Build the PDF elements from the hymn content.

        :return: A list of Paragraph objects for the PDF.
        """
        elements = []

        elements.extend(self._build_cover_page())

        for idx, hymn in enumerate(self.hymns, start=1):
            elements.extend(self._build_title_and_header(idx, hymn))
            elements.extend(self._build_details_on_top(hymn))
            elements.extend(self._build_vertical_lines(hymn))

            body_paragraphs = self._build_body_paragraphs(hymn)
            last_elements = [
                self._build_after_hymn_symbol(idx),
                *self._build_received_at(hymn)
            ]
            elements.extend(self._keep_together_elements(body_paragraphs, last_elements))

            elements.append(PageBreak())

        return elements
