"""Render TOOL_SELECTION_PAPER.md to a PDF. Does not recompute results."""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String, Circle, Line
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import CondPageBreak, Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", r"C:\Windows\Fonts\ariali.ttf"))
pdfmetrics.registerFont(TTFont("Georgia", r"C:\Windows\Fonts\georgia.ttf"))
pdfmetrics.registerFont(TTFont("Georgia-Bold", r"C:\Windows\Fonts\georgiab.ttf"))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-Bold")
pdfmetrics.registerFontFamily("Georgia", normal="Georgia", bold="Georgia-Bold", italic="Georgia", boldItalic="Georgia-Bold")

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "TOOL_SELECTION_PAPER.md"
OUT = HERE / "TOOL_SELECTION_PAPER.pdf"
TITLE = "Tool-Choice Signaling and Task-State Preservation in LLM Multi-Agent Systems"


def styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(name="H2", fontName="Georgia-Bold", fontSize=12, leading=15, spaceBefore=8, spaceAfter=2, textColor=colors.black))
    base.add(ParagraphStyle(name="H3", fontName="Georgia-Bold", fontSize=11, leading=13, spaceBefore=5, spaceAfter=2))
    base.add(ParagraphStyle(name="Body", fontName="Arial", fontSize=10, leading=12.2, spaceAfter=3, alignment=4))
    base.add(ParagraphStyle(name="CodeX", fontName="Courier", fontSize=8, leading=10, leftIndent=8, spaceAfter=1))
    base.add(ParagraphStyle(name="Cell", fontName="Arial", fontSize=7.5, leading=9))
    base.add(ParagraphStyle(name="Head", fontName="Arial-Bold", fontSize=7.5, leading=9, textColor=colors.white))
    return base


class TitleBlock(Flowable):
    """Title page block from the Apart submission template."""

    def __init__(self, width: float):
        super().__init__()
        self.block_width = width
        self.width = width
        self.title_lines = wrap(
            TITLE,
            "Georgia-Bold",
            16,
            width - 14,
        )
        self.height = 22 + len(self.title_lines) * 20 + 46

    def draw(self):
        canvas_ = self.canv
        y = self.height - 18
        for index, line in enumerate(self.title_lines):
            canvas_.setFillColor(colors.black)
            canvas_.setFont("Georgia-Bold", 16)
            canvas_.drawString(0, y, line)
            if index == len(self.title_lines) - 1:
                canvas_.setFont("Arial", 8)
                canvas_.drawString(pdfmetrics.stringWidth(line, "Georgia-Bold", 16) + 2, y + 8, "1")
            y -= 20
        y -= 8
        canvas_.setFont("Arial", 11)
        canvas_.drawString(0, y, "Ellen Berhe")
        canvas_.drawString(2.7 * inch, y, "Muhammad Hassaan Shaukat")
        canvas_.setFont("Arial-Italic", 9)
        canvas_.drawRightString(self.block_width, y + 12, "With")
        canvas_.setFont("Arial-Bold", 11)
        canvas_.drawRightString(self.block_width, y, "Apart Research")


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        pages = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self.setFillColor(colors.black)
            self.setFont("Arial", 8)
            if self._pageNumber == 1:
                self.setStrokeColor(colors.black)
                self.setLineWidth(0.4)
                self.line(0.7 * inch, 0.58 * inch, 7.8 * inch, 0.58 * inch)
                self.drawString(0.7 * inch, 0.40 * inch, "1")
                self.drawString(0.82 * inch, 0.38 * inch, "Research conducted at the AI Collusion Research Sprint, October 2026.")
            self.drawRightString(7.8 * inch, 0.38 * inch, f"{self._pageNumber} / {pages}")
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


def wrap(text: str, font: str, size: float, width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if pdfmetrics.stringWidth(trial, font, size) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def markup(text: str) -> str:
    text = text.replace("Δ", "delta").replace("−", "-").replace("—", "-")
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<font face='Courier' size='8'>\1</font>", escaped)
    return escaped


def table_flowable(rows: list[list[str]], style):
    data = []
    for index, row in enumerate(rows):
        cell_style = style["Head"] if index == 0 else style["Cell"]
        data.append([Paragraph(markup(cell), cell_style) for cell in row])
    count = max(len(rows[0]), 1)
    widths = [6.6 * inch / count] * count
    table = Table(data, colWidths=widths, repeatRows=1)
    table.hAlign = "LEFT"
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#b0b7c3")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ]
        )
    )
    return table


def _chart(drawing, x, y, width, height, data, names, ymin, ymax, colors_hex, title):
    chart = VerticalBarChart()
    chart.x = x
    chart.y = y
    chart.width = width
    chart.height = height
    chart.data = data
    chart.categoryAxis.categoryNames = names
    chart.categoryAxis.labels.fontName = "Times-Roman"
    chart.categoryAxis.labels.fontSize = 8
    chart.valueAxis.valueMin = ymin
    chart.valueAxis.valueMax = ymax
    chart.valueAxis.labels.fontName = "Times-Roman"
    chart.valueAxis.labels.fontSize = 7
    chart.barSpacing = 1
    chart.groupSpacing = 8
    chart.strokeColor = colors.HexColor("#d5d0c8")
    for index, hex_color in enumerate(colors_hex):
        chart.bars[index].fillColor = colors.HexColor(hex_color)
    drawing.add(chart)
    drawing.add(String(x, y + height + 14, title, fontName="Times-Bold", fontSize=8, fillColor=colors.HexColor("#1c2430")))
    return drawing


def figure_for(marker: str):
    if "communication_utility" in marker:
        drawing = Drawing(480, 190)
        drawing.add(String(8, 174, "Exploratory cohort only. Dependence against joint reward.", fontName="Times-Bold", fontSize=8))
        drawing.add(Line(36, 24, 430, 24, strokeColor=colors.HexColor("#1c2430"), strokeWidth=0.6))
        drawing.add(Line(36, 24, 36, 155, strokeColor=colors.HexColor("#1c2430"), strokeWidth=0.6))
        points = [
            ("#1f4e79", [(1.0, 65.43), (0.5, 52.31), (1.0, 82.69)]),
            ("#2e7d32", [(0.0, 65.87), (0.0, 57.46), (0.0, 82.77)]),
            ("#c45911", [(0.0, 48.19), (0.0, 34.25), (0.0, 72.31)]),
        ]
        offsets = {"#1f4e79": 0, "#2e7d32": -4, "#c45911": 4}

        def xy(delta, reward, shift):
            return 36 + delta * 360 + shift, 24 + (reward - 30) * (130 / 60)

        for hex_color, series in points:
            for delta, reward in series:
                cx, cy = xy(delta, reward, offsets[hex_color])
                drawing.add(Circle(cx, cy, 3.2, fillColor=colors.HexColor(hex_color), strokeColor=colors.HexColor(hex_color)))
        drawing.add(String(150, 8, "Signal dependence", fontName="Times-Roman", fontSize=8))
        drawing.add(String(440, 150, "T1", fontName="Times-Bold", fontSize=8, fillColor=colors.HexColor("#1f4e79")))
        drawing.add(String(440, 136, "T2", fontName="Times-Bold", fontSize=8, fillColor=colors.HexColor("#2e7d32")))
        drawing.add(String(440, 122, "T3", fontName="Times-Bold", fontSize=8, fillColor=colors.HexColor("#c45911")))
        return drawing
    if "holdout_comparison" in marker:
        drawing = Drawing(500, 168)
        _chart(
            drawing, 28, 18, 210, 112,
            [[1.0, 1.0, 1.0, 0.5], [0, 0, 0, 0.5], [0, 0, 0, 0]],
            ["11", "12", "13", "14"],
            0, 1,
            ["#1f4e79", "#2e7d32", "#5c6b7a"],
            "Holdout dependence. T1, T2, T4.",
        )
        _chart(
            drawing, 270, 18, 200, 112,
            [[87.354, 99.004, 65.050, 90.247], [106.342, 99.004, 83.738, 107.059]],
            ["11", "12", "13", "14"],
            0, 120,
            ["#c45911", "#5c6b7a"],
            "Separate utility joints. T3, T4.",
        )
        return drawing
    rows = [
        ["Policy", "Tool name", "Action event", "Receiver assignment"],
        ["T1 positive control", "Raw name", "Shown", "Shown"],
        ["T2 canonical", "assign_task", "Shown", "Shown"],
        ["T3", "Absent", "Hidden", "Hidden"],
        ["T4", "Absent", "Hidden", "Shown"],
    ]
    data = []
    for index, row in enumerate(rows):
        cell_style = ParagraphStyle("FigHead", fontName="Arial-Bold", fontSize=8, leading=10, textColor=colors.white) if index == 0 else ParagraphStyle("FigCell", fontName="Arial", fontSize=8, leading=10)
        data.append([Paragraph(markup(cell), cell_style) for cell in row])
    table = Table(data, colWidths=[1.7 * inch, 1.5 * inch, 1.5 * inch, 1.9 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#e8eef5")),
                ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#f8efe6")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b0b7c3")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def story(style):
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    flow = []
    paragraph: list[str] = []
    table_rows: list[list[str]] = []
    code_lines: list[str] = []
    in_code = False

    def flush_paragraph():
        nonlocal paragraph
        text = " ".join(part.strip() for part in paragraph).strip()
        paragraph = []
        if text:
            flow.append(Paragraph(markup(text), style["Body"]))

    def flush_table():
        nonlocal table_rows
        if table_rows:
            flow.append(CondPageBreak(0.95 * inch))
            flow.append(table_flowable(table_rows, style))
            flow.append(Spacer(1, 6))
        table_rows = []

    def flush_code():
        nonlocal code_lines
        for item in code_lines:
            flow.append(Paragraph(markup(item) if item else "&nbsp;", style["CodeX"]))
        if code_lines:
            flow.append(Spacer(1, 6))
        code_lines = []

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("```"):
            flush_paragraph()
            flush_table()
            if in_code:
                flush_code()
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
            continue
        if line.startswith("!["):
            flush_paragraph()
            flush_table()
            flow.append(Spacer(1, 4))
            flow.append(figure_for(line))
            flow.append(Spacer(1, 4))
            continue
        if line.startswith("|"):
            flush_paragraph()
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if cells and set("".join(cells)) <= set("-: "):
                continue
            table_rows.append(cells)
            continue
        flush_table()
        if not line.strip():
            flush_paragraph()
            continue
        if line.startswith("# "):
            flush_paragraph()
            flow.append(TitleBlock(6.6 * inch))
            flow.append(Spacer(1, 6))
            continue
        if line.startswith("### "):
            flush_paragraph()
            flow.append(Paragraph(markup(line[4:].strip()), style["H3"]))
            continue
        if line.startswith("## "):
            flush_paragraph()
            flow.append(Paragraph(markup(line[3:].strip()), style["H2"]))
            continue
        if line.startswith(("Ellen", "Muhammad", "With Apart", "Apart Research", "Research conducted")):
            continue
        if re.match(r"^\d+\. ", line):
            flush_paragraph()
            flow.append(Paragraph(markup(line.strip()), style["Body"]))
            continue
        paragraph.append(line)
    flush_paragraph()
    flush_table()
    flush_code()
    return flow


def main() -> None:
    style = styles()
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.58 * inch,
        bottomMargin=0.66 * inch,
        title=TITLE,
        author="Ellen Berhe and Muhammad Hassaan Shaukat",
    )
    doc.build(story(style), canvasmaker=NumberedCanvas)
    print(OUT)


if __name__ == "__main__":
    main()
