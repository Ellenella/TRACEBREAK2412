"""Render ACTIONS_AS_CARRIERS_REVISED.md to a PDF.

The markdown file is the manuscript. This script does not recompute results
and does not call a model.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas


OUT = Path(__file__).with_name("Actions_as_Carriers_revised.pdf")
SOURCE = Path(__file__).with_name("ACTIONS_AS_CARRIERS_REVISED.md")


def styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(name="TitleX", fontName="Times-Bold", fontSize=14, leading=18, spaceAfter=8))
    base.add(ParagraphStyle(name="H2", fontName="Times-Bold", fontSize=12, leading=15, spaceBefore=11, spaceAfter=6))
    base.add(ParagraphStyle(name="Body", fontName="Times-Roman", fontSize=10, leading=13, spaceAfter=7, alignment=4))
    base.add(ParagraphStyle(name="Meta", fontName="Times-Italic", fontSize=10, leading=13, spaceAfter=8))
    base.add(ParagraphStyle(name="Cell", fontName="Times-Roman", fontSize=7, leading=9))
    base.add(ParagraphStyle(name="Head", fontName="Times-Bold", fontSize=7, leading=9, textColor=colors.white))
    return base


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
            self.setFont("Times-Roman", 8)
            self.drawString(0.7 * inch, 0.45 * inch, "Actions as Carriers, 25 October 2026")
            self.drawRightString(7.8 * inch, 0.45 * inch, f"{self._pageNumber} / {pages}")
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def table_flowable(rows: list[list[str]], style):
    data = []
    for index, row in enumerate(rows):
        cell_style = style["Head"] if index == 0 else style["Cell"]
        data.append([Paragraph(esc(cell), cell_style) for cell in row])
    widths = [6.6 * inch / max(len(rows[0]), 1)] * len(rows[0])
    table = Table(data, colWidths=widths, repeatRows=1)
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


def story(style):
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    flow = []
    paragraph: list[str] = []
    table_rows: list[list[str]] = []

    def flush_paragraph():
        nonlocal paragraph
        text = " ".join(part.strip() for part in paragraph).strip()
        paragraph = []
        if text:
            flow.append(Paragraph(esc(text), style["Body"]))

    def flush_table():
        nonlocal table_rows
        if table_rows:
            flow.append(table_flowable(table_rows, style))
            flow.append(Spacer(1, 6))
        table_rows = []

    for raw in lines:
        line = raw.rstrip()
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
            flow.append(Paragraph(esc(line[2:].strip()), style["TitleX"]))
            continue
        if line.startswith("## "):
            flush_paragraph()
            flow.append(Paragraph(esc(line[3:].strip()), style["H2"]))
            continue
        if line.startswith("Apart Research"):
            flush_paragraph()
            flow.append(Paragraph(esc(line.strip()), style["Meta"]))
            continue
        paragraph.append(line)
    flush_paragraph()
    flush_table()
    return flow


def main():
    style = styles()
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title="Actions as Carriers: Side-Channel Collusion and the Metrics That Hide It",
        author="Ellen and Muhammad Hassaan Shaukat",
    )
    doc.build(story(style), canvasmaker=NumberedCanvas)
    print(OUT)


if __name__ == "__main__":
    main()
