from typing import List

from config import Configuration
from models import Hymn
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Flowable,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from hymn_pdf_generator.repetition_bar_allocator import RepetitionBarXAxisAllocator

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

    def __init__(self, hymns: List[Hymn], filename: str, intro_name: str, name: str, owner: str, cover_image_path: str):
        """
        Initialize the HymnPDFGenerator with hymns, output filename, and cover page details.

        :param hymns: A list of Hymn instances.
        :param filename: The output PDF filename.
        :param intro_name: Introduction name for the cover page.
        :param name: Name for the cover page.
        :param owner: Owner name for the cover page.
        :param cover_image_path: Background image for the cover page.
        """
        self.hymns = hymns
        self.filename = filename
        self.intro_name = intro_name
        self.name = name
        self.owner = owner
        self.cover_image_path = cover_image_path
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

        # creating a frame for the template
        frame = Frame(self.margin,
                      self.margin,
                      self.pagesize[0] - 2 * self.margin,
                      self.pagesize[1] - 2 * self.margin,
                      id='normal')

        template = PageTemplate(id='background',
                                frames=frame,
                                onPage=self._background_image)
        doc.addPageTemplates([template])

        elements = self._build_elements()
        doc.build(elements, canvasmaker=PageNumCanvas)

    def _background_image(self, canvas, doc):
        """
        Add background image to the canvas.
        """
        img = ImageReader(self.cover_image_path)
        img_width, img_height = img.getSize()

        # Calculates aspect ratio of image and document
        aspect = img_width / float(img_height)
        page_width, page_height = self.pagesize

        # Sets the width and height according to the aspect ratio
        if aspect > 1:
            width = page_width
            height = width / aspect
        else:
            height = page_height
            width = height * aspect

        # Position the image in the center of the page
        x = (page_width - width) / 2
        y = (page_height - height) / 2

        canvas.drawImage(self.cover_image_path,
                         x,
                         y,
                         width=width,
                         height=height,
                         preserveAspectRatio=True,
                         mask='auto')

        # Adds a semi-transparent rectangle over the image
        canvas.setFillColorRGB(1, 1, 1, alpha=0.5)  # Semi-transparent white (50% opacity)
        canvas.rect(0, 0, page_width, page_height, fill=1)

    def _build_vertical_lines(self, hymn: Hymn) -> List[VerticalLine]:
        """
        Create vertical line elements based on hymn bars repetitions.

        :param hymn: The hymn instance.
        :return: A list of VerticalLine elements.
        """
        elements = []
        allocator = RepetitionBarXAxisAllocator()
        bar_positions = allocator.get_entries_with_levels(hymn.repetitions)

        resize_factor = hymn.adjusted_font_size / self.default_body_font_size
        def resize(number: float) -> float:
            """Adjust in casa the font was resized to fit in page"""
            return number * resize_factor

        # Y padding
        y_padding = -8 + resize(-4)
        # X distance between bars
        x_bars_distance = resize(6)
        # Bar hight for one line
        one_line = resize(7)
        # Bar hight for one blank line
        one_blank_line = resize(8.5)
        # Distance between two lines
        between_lines = resize(9)

        for bar in bar_positions:
            start = bar['start'] - 1  # Start from 0
            end = bar['end'] - 1  # Start from 0
            level = bar['level']

            blanks_before = hymn.count_blank_lines(0, start)
            blanks_up_to_end = hymn.count_blank_lines(0, end)

            # Calculate the bar vertical start and end positions
            y_start = (
                y_padding
                - (start * one_line
                   + start * between_lines)
                - (blanks_before * one_blank_line)
            )

            y_end = (
                y_padding
                - ((end + 1) * one_line
                   + end * between_lines)
                - (blanks_up_to_end * one_blank_line)
            )
            x_position = -(level * x_bars_distance)

            elements.append(
                VerticalLine(x_position, y_start, y_end))

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
        Ensure the last elements are kept together with the last body paragraphs according to specific rules.

        :param body_paragraphs: The body paragraphs of the hymn.
        :param last_elements: The elements to be kept together with the last body paragraphs.
        :return: A list of paragraphs wrapped in KeepTogether.
        """
        elements = []
        rules = {
            5: 2,
            6: 3,
            7: 3,
            8: 2,
            9: 2,
        }
        default_keep_together = 1

        num_paragraphs = len(body_paragraphs)
        keep_together_count = rules.get(num_paragraphs, default_keep_together)

        if num_paragraphs > keep_together_count:
            elements.extend(KeepTogether(paragraph) for paragraph in body_paragraphs[:-keep_together_count])
            elements.append(KeepTogether(body_paragraphs[-keep_together_count:] + last_elements))
        else:
            elements.append(KeepTogether(body_paragraphs + last_elements))

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
