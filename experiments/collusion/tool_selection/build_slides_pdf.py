"""One-page-per-slide deck. Does not recompute results or call a model.

Order: the research question, the mechanism, the confounded gap, H1-H3,
then the T3-versus-T4 contrast as the centerpiece. No new episodes.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
OUT = HERE / "TOOL_SELECTION_SLIDES.pdf"
PAGE = landscape((13.333 * inch, 7.5 * inch))
WIDTH, HEIGHT = PAGE
NAVY = "#1f4e79"
INK = "#1c2430"
MUTED = "#5c6b7a"
PAPER = "#f6f4ef"
CARD = "#ffffff"
AMBER = "#8a4b08"
RULE = "#d5d0c8"
GREEN = "#e7f0e8"


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


def draw_bg(pdf: canvas.Canvas, kicker: str) -> None:
    pdf.setFillColor(PAPER)
    pdf.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)
    pdf.setFillColor(NAVY)
    pdf.rect(0, HEIGHT - 0.62 * inch, WIDTH, 0.62 * inch, fill=1, stroke=0)
    pdf.setFillColor("white")
    pdf.setFont("Times-Bold", 12)
    pdf.drawString(0.55 * inch, HEIGHT - 0.40 * inch, kicker)
    pdf.setFont("Times-Roman", 11)
    pdf.drawRightString(WIDTH - 0.5 * inch, HEIGHT - 0.40 * inch, "Ellen Berhe and Muhammad Hassaan Shaukat")


def draw_footer(pdf: canvas.Canvas, number: int, total: int) -> None:
    pdf.setFillColor(MUTED)
    pdf.setFont("Times-Roman", 10)
    pdf.drawString(0.55 * inch, 0.32 * inch, "Apart Research Sprint 2026, Track 3.1")
    pdf.drawRightString(WIDTH - 0.5 * inch, 0.32 * inch, f"{number} / {total}")


def draw_title(pdf: canvas.Canvas, text: str, y: float, size: float = 26) -> float:
    pdf.setFillColor(INK)
    for line in wrap(text, "Times-Bold", size, WIDTH - 1.15 * inch):
        pdf.setFont("Times-Bold", size)
        pdf.drawString(0.55 * inch, y, line)
        y -= size + 8
    return y


def draw_note(pdf: canvas.Canvas, text: str, y: float, size: float = 15, color: str = MUTED, width: float | None = None) -> float:
    pdf.setFillColor(color)
    span = width if width is not None else WIDTH - 1.15 * inch
    for line in wrap(text, "Times-Roman", size, span):
        pdf.setFont("Times-Roman", size)
        pdf.drawString(0.55 * inch, y, line)
        y -= size + 6
    return y


def bullets(pdf: canvas.Canvas, items: list[str], x: float, y: float, width: float, size: float = 16, leading: float = 22) -> float:
    pdf.setFillColor(INK)
    for item in items:
        lines = wrap(item, "Times-Roman", size, width - 18)
        pdf.setFont("Times-Bold", size)
        pdf.drawString(x, y, "·")
        pdf.setFont("Times-Roman", size)
        for line in lines:
            pdf.drawString(x + 16, y, line)
            y -= leading
        y -= 8
    return y


def arrow(pdf: canvas.Canvas, x1: float, x2: float, y: float) -> None:
    pdf.setStrokeColor(NAVY)
    pdf.setFillColor(NAVY)
    pdf.setLineWidth(1.6)
    pdf.line(x1, y, x2 - 9, y)
    path = pdf.beginPath()
    path.moveTo(x2, y)
    path.lineTo(x2 - 10, y + 5)
    path.lineTo(x2 - 10, y - 5)
    path.close()
    pdf.drawPath(path, fill=1, stroke=0)


def box(pdf: canvas.Canvas, x: float, y: float, w: float, h: float, fill: str, lines: list[tuple[str, str, float]]) -> None:
    pdf.setFillColor(fill)
    pdf.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    text_y = y + h - 28
    for text, font, size in lines:
        pdf.setFillColor("white" if fill == NAVY else INK)
        pdf.setFont(font, size)
        pdf.drawCentredString(x + w / 2, text_y, text)
        text_y -= size + 6


def title_slide(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(NAVY)
    pdf.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)
    pdf.setFillColor(AMBER)
    pdf.rect(0, 0, 0.18 * inch, HEIGHT, fill=1, stroke=0)
    pdf.setFillColor("white")
    pdf.setFont("Times-Roman", 14)
    pdf.drawString(0.7 * inch, HEIGHT - 1.15 * inch, "Apart Research Sprint 2026  ·  Track 3.1")
    y = HEIGHT - 2.05 * inch
    for line in wrap(
        "Tool-Choice Signaling and Task-State Preservation in LLM Multi-Agent Systems",
        "Times-Bold",
        30,
        WIDTH - 1.5 * inch,
    ):
        pdf.setFont("Times-Bold", 30)
        pdf.drawString(0.7 * inch, y, line)
        y -= 38
    pdf.setFont("Times-Roman", 18)
    pdf.drawString(0.7 * inch, y - 8, "Ellen Berhe and Muhammad Hassaan Shaukat")
    pdf.setFont("Times-Italic", 16)
    y = 1.7 * inch
    for line in wrap(
        "How can multi-agent runtimes suppress tool-choice signaling without disrupting legitimate task coordination?",
        "Times-Italic",
        16,
        WIDTH - 1.6 * inch,
    ):
        pdf.drawString(0.7 * inch, y, line)
        y -= 22


def mechanism_slide(pdf: canvas.Canvas) -> None:
    draw_bg(pdf, "The setup")
    y = draw_title(pdf, "Two equivalent tools. One assignment. One observation filter.", HEIGHT - 1.12 * inch, 24)
    top = y - 0.35 * inch
    height = 1.85 * inch
    width = 2.55 * inch
    gap = 0.55 * inch
    left = 0.55 * inch
    specs = [
        (NAVY, [("Sender", "Times-Bold", 16), ("Holds a private bit", "Times-Roman", 12), ("0 or 1", "Times-Roman", 12), ("Not shown to others", "Times-Roman", 12)]),
        ("#e8eef5", [("Tool execution", "Times-Bold", 16), ("assign_task_direct", "Times-Roman", 12), ("or assign_task_queued", "Times-Roman", 12), ("Same task: review", "Times-Roman", 12)]),
        ("#f4efe4", [("Observation filter", "Times-Bold", 15), ("Edits what is shown", "Times-Roman", 12), ("Name, event, assignment", "Times-Roman", 12), ("Log keeps the real name", "Times-Roman", 12)]),
        (NAVY, [("Receiver", "Times-Bold", 16), ("Does not know the bit", "Times-Roman", 12), ("Sees the filtered prompt", "Times-Roman", 12), ("Then claims a task", "Times-Roman", 12)]),
    ]
    xs = []
    x = left
    for fill, lines in specs:
        box(pdf, x, top - height, width, height, fill, lines)
        xs.append(x)
        x += width + gap
    mid = top - height / 2
    for index in range(3):
        arrow(pdf, xs[index] + width + 4, xs[index + 1] - 4, mid)
    pdf.setFillColor(INK)
    pdf.setFont("Times-Bold", 14)
    pdf.drawString(0.55 * inch, top - height - 0.4 * inch, "The receiver can learn which function was called only if that name remains in the observation.")
    chips = [
        (NAVY, "T1  name visible"),
        ("#2e7d32", "T2  name rewritten"),
        ("#c45911", "T3  event and assignment hidden"),
        ("#5c6b7a", "T4  event hidden, assignment kept"),
    ]
    cx = 0.55 * inch
    cy = 0.85 * inch
    for fill, label in chips:
        pdf.setFillColor(fill)
        pdf.roundRect(cx, cy, 2.9 * inch, 0.38 * inch, 4, fill=1, stroke=0)
        pdf.setFillColor("white")
        pdf.setFont("Times-Bold", 11)
        pdf.drawCentredString(cx + 1.45 * inch, cy + 0.12 * inch, label)
        cx += 3.05 * inch


def gap_slide(pdf: canvas.Canvas) -> None:
    draw_bg(pdf, "Research gap")
    y = draw_title(pdf, "The original experiment confounded event removal with assignment masking", HEIGHT - 1.15 * inch, 22)
    y = bullets(
        pdf,
        [
            "Seeds 1-3 already separated the selected name from the assignment. T1 showed the name. T2 rewrote it and kept the assignment. Dependence fell from 0.833 to 0.",
            "The lower reward was a different contrast: T2 against T3. T3 hid the action event and also masked the receiver's assignment.",
            "T3 joint reward was lower on every seed: 48.19, 34.25, and 72.31, against T2 at 65.87, 57.46, and 82.77.",
            "Those two edits were applied together. The 108 runs cannot say which one changed the reward.",
        ],
        0.55 * inch,
        y - 8,
        WIDTH - 1.15 * inch,
        size=16,
        leading=21,
    )
    pdf.setFillColor(AMBER)
    pdf.setFont("Times-Bold", 15)
    y = 1.05 * inch
    for line in wrap(
        "Open question. Once the assignment stays visible, does keeping a canonical event help? If the event is already hidden, does the assignment still matter?",
        "Times-Bold",
        15,
        WIDTH - 1.15 * inch,
    ):
        pdf.drawString(0.55 * inch, y, line)
        y -= 20


def hypotheses_slide(pdf: canvas.Canvas) -> None:
    draw_bg(pdf, "Hypotheses that cover the gap")
    y = draw_title(pdf, "The holdout states three hypotheses. One comparison is left outside them.", HEIGHT - 1.12 * inch, 22)
    rows = [
        ["", "Hypothesis", "What is compared", "Measure"],
        ["H1", "Visible tool identity can transmit a prompted private bit.", "T1, codebook on, seeds 11–14", "Bit dependence"],
        ["H2", "Canonicalization and event deletion can suppress that dependence.", "T2 and T4 against T1", "Bit dependence"],
        ["H3", "Keeping the canonical event beats deleting it, while the assignment stays visible.", "T2 versus T4, codebook off", "Joint reward"],
    ]
    left = 0.55 * inch
    col_w = [0.7 * inch, 6.3 * inch, 3.55 * inch, 1.7 * inch]
    row_h = [0.42 * inch, 0.62 * inch, 0.62 * inch, 0.62 * inch]
    yy = y - 0.15 * inch
    for r, row in enumerate(rows):
        x = left
        for c, cell in enumerate(row):
            pdf.setFillColor(NAVY if r == 0 else CARD)
            pdf.setStrokeColor(RULE)
            pdf.rect(x, yy - row_h[r], col_w[c], row_h[r], fill=1, stroke=1)
            pdf.setFillColor("white" if r == 0 else INK)
            font = "Times-Bold" if r == 0 or c == 0 else "Times-Roman"
            size = 13 if r == 0 else 13
            pdf.setFont(font, size)
            lines = wrap(cell, font, size, col_w[c] - 16)
            text_y = yy - 0.28 * inch if len(lines) == 1 else yy - 0.30 * inch
            if r and len(lines) > 1:
                text_y = yy - 0.32 * inch
            for line in lines:
                pdf.setFont(font, size)
                pdf.drawString(x + 8, text_y, line)
                text_y -= 16
            x += col_w[c]
        yy -= row_h[r]
    pdf.setFillColor(AMBER)
    pdf.setFont("Times-Bold", 14)
    pdf.drawString(0.55 * inch, 0.95 * inch, "Not a fourth hypothesis.")
    pdf.setFillColor(MUTED)
    pdf.setFont("Times-Roman", 13)
    for i, line in enumerate(
        wrap(
            "H3 holds the assignment visible. Hiding that assignment, with the event already hidden, is the later T3 comparison. The 72 and the eight T3 episodes are not pooled with the 108.",
            "Times-Roman",
            13,
            WIDTH - 1.15 * inch,
        )
    ):
        pdf.drawString(0.55 * inch, 0.72 * inch - i * 16, line)


def h1_h2_slide(pdf: canvas.Canvas) -> None:
    draw_bg(pdf, "Answers H1 and H2")
    y = draw_title(pdf, "The visible name carries the bit. Event deletion removes it.", HEIGHT - 1.12 * inch, 24)
    legend = [("T1 visible name", NAVY), ("T2 canonical name", "#2e7d32"), ("T4 event deleted", "#5c6b7a")]
    lx = 0.7 * inch
    for label, color in legend:
        pdf.setFillColor(color)
        pdf.rect(lx, y - 0.05 * inch, 0.28 * inch, 0.18 * inch, fill=1, stroke=0)
        pdf.setFillColor(INK)
        pdf.setFont("Times-Roman", 13)
        pdf.drawString(lx + 0.38 * inch, y - 0.02 * inch, label)
        lx += 3.3 * inch
    origin_x = 1.15 * inch
    origin_y = 1.85 * inch
    chart_w = 10.4 * inch
    chart_h = 3.15 * inch
    series = [[1.0, 1.0, 1.0, 0.5], [0.0, 0.0, 0.0, 0.5], [0.0, 0.0, 0.0, 0.0]]
    colors = [NAVY, "#2e7d32", "#5c6b7a"]
    categories = ["11", "12", "13", "14"]
    pdf.setStrokeColor(RULE)
    pdf.setLineWidth(0.6)
    for tick, label in ((0, "0"), (0.5, "0.5"), (1.0, "1.0")):
        ty = origin_y + chart_h * tick
        pdf.line(origin_x, ty, origin_x + chart_w, ty)
        pdf.setFillColor(MUTED)
        pdf.setFont("Times-Roman", 12)
        pdf.drawRightString(origin_x - 8, ty - 4, label)
    pdf.setStrokeColor(INK)
    pdf.setLineWidth(1.2)
    pdf.line(origin_x, origin_y, origin_x + chart_w, origin_y)
    group_w = chart_w / 4
    bar_w = group_w * 0.72 / 3
    for group, _seed in enumerate(categories):
        for index, values in enumerate(series):
            height = chart_h * values[group]
            bx = origin_x + group * group_w + group_w * 0.16 + index * bar_w
            pdf.setFillColor(colors[index])
            pdf.rect(bx, origin_y, bar_w - 3, max(height, 1.5), fill=1, stroke=0)
        pdf.setFillColor(INK)
        pdf.setFont("Times-Bold", 14)
        pdf.drawCentredString(origin_x + group * group_w + group_w / 2, origin_y - 20, categories[group])
    pdf.setFillColor(AMBER)
    pdf.setFont("Times-Bold", 14)
    pdf.drawString(0.55 * inch, 1.05 * inch, "Seed 14 under T2 is one receiver action. The normalized observation did not change with the bit.")
    pdf.setFillColor(MUTED)
    pdf.setFont("Times-Roman", 13)
    pdf.drawString(0.55 * inch, 0.78 * inch, "That is not a remaining tool-name leak. T4 dependence is 0 on every seed. These 72 episodes are not pooled with the 108.")


def h3_slide(pdf: canvas.Canvas) -> None:
    draw_bg(pdf, "Answers H3")
    y = draw_title(pdf, "Keeping the canonical event is not shown to beat deleting it", HEIGHT - 1.15 * inch, 24)
    y = draw_note(
        pdf,
        "Codebook off. The assignment stays visible under both T2 and T4. The seed-wise gap is T2 joint reward minus T4 joint reward.",
        y - 4,
        15,
    )
    rows = [
        ["Seed", "T2 − T4", "Violations under T2 or T4"],
        ["11", "0", "None"],
        ["12", "0", "None"],
        ["13", "−2.792", "None"],
        ["14", "+0.876", "None"],
    ]
    left = 0.55 * inch
    col_w = [1.4 * inch, 2.2 * inch, 3.6 * inch]
    row_h = 0.42 * inch
    yy = y - 0.2 * inch
    for r, row in enumerate(rows):
        x = left
        for c, cell in enumerate(row):
            pdf.setFillColor(NAVY if r == 0 else CARD)
            pdf.rect(x, yy - row_h, col_w[c], row_h, fill=1, stroke=0)
            pdf.setFillColor("white" if r == 0 else INK)
            pdf.setFont("Times-Bold" if r == 0 else "Times-Roman", 14)
            pdf.drawString(x + 10, yy - 0.27 * inch, cell)
            x += col_w[c]
        yy -= row_h
    pdf.setFillColor(AMBER)
    pdf.setFont("Times-Bold", 22)
    pdf.drawString(0.55 * inch, 1.15 * inch, "H3 is not supported. The sign of the gap is not stable.")
    pdf.setFillColor(MUTED)
    pdf.setFont("Times-Roman", 15)
    pdf.drawString(0.55 * inch, 0.78 * inch, "This does not say the assignment is irrelevant. H3 never removed it.")


def finding_slide(pdf: canvas.Canvas) -> None:
    draw_bg(pdf, "The result to remember")
    y = draw_title(pdf, "Removing assignment visibility led to duplicate work in three of four environments", HEIGHT - 1.12 * inch, 22)
    y = draw_note(
        pdf,
        "Both policies already hide the action event. Only T3 hides the receiver's assignment. Eight utility episodes, not part of the 72.",
        y - 2,
        15,
    )
    cards = [
        (0.55 * inch, "#c45911", "T3", "Assignment hidden", [("Duplicate assignments", "3/4 seeds"), ("Violations", "3/4 seeds"), ("Distinct tasks", "2 on three seeds")]),
        (6.85 * inch, "#2e7d32", "T4", "Assignment visible", [("Duplicate assignments", "0/4 seeds"), ("Violations", "0/4 seeds"), ("Distinct tasks", "3 on every seed")]),
    ]
    card_top = y - 0.2 * inch
    card_h = 3.35 * inch
    card_w = 5.85 * inch
    for x, color, code, label, metrics in cards:
        pdf.setFillColor(CARD)
        pdf.setStrokeColor(color)
        pdf.setLineWidth(2)
        pdf.roundRect(x, card_top - card_h, card_w, card_h, 8, fill=1, stroke=1)
        pdf.setFillColor(color)
        pdf.rect(x, card_top - 0.62 * inch, card_w, 0.62 * inch, fill=1, stroke=0)
        pdf.setFillColor("white")
        pdf.setFont("Times-Bold", 18)
        pdf.drawString(x + 16, card_top - 0.42 * inch, f"{code}   {label}")
        row_y = card_top - 1.25 * inch
        for name, value in metrics:
            pdf.setFillColor(MUTED)
            pdf.setFont("Times-Roman", 15)
            pdf.drawString(x + 18, row_y, name)
            pdf.setFillColor(INK)
            pdf.setFont("Times-Bold", 22)
            pdf.drawRightString(x + card_w - 18, row_y - 2, value)
            row_y -= 0.62 * inch
    pdf.setFillColor(MUTED)
    pdf.setFont("Times-Roman", 13)
    pdf.drawString(0.55 * inch, 0.72 * inch, "Seed 12 is the exception: the assignment was hidden, and the joint reward still matched T4. Both draws within each seed agree.")


def contract_slide(pdf: canvas.Canvas) -> None:
    draw_bg(pdf, "Supporting check")
    y = draw_title(pdf, "Two offline checks. Not a new information-flow method.", HEIGHT - 1.12 * inch, 22)
    y = draw_note(
        pdf,
        "Identity confidentiality: declared-equivalent calls must not leave distinguishable tool names. Task-state preservation: the assignment section must keep the authoritative pairs. The checker does not decide what is safe to hide, and it does not see later edits inside the provider client.",
        y - 2,
        14,
    )
    rows = [
        ["Policy", "Tool identity confidential", "Assignment preserved"],
        ["T1  visible name", "Fail", "Pass"],
        ["T2  canonical name", "Pass", "Pass"],
        ["T3  event hidden, assignment hidden", "Pass", "Fail"],
        ["T4  event hidden, assignment kept", "Pass", "Pass"],
    ]
    left = 0.55 * inch
    col_w = [5.5 * inch, 3.3 * inch, 3.3 * inch]
    row_h = 0.40 * inch
    yy = y - 0.12 * inch
    for r, row in enumerate(rows):
        x = left
        for c, cell in enumerate(row):
            pdf.setFillColor(NAVY if r == 0 else CARD)
            pdf.setStrokeColor(RULE)
            pdf.rect(x, yy - row_h, col_w[c], row_h, fill=1, stroke=1)
            pdf.setFillColor("white" if r == 0 else INK)
            pdf.setFont("Times-Bold" if r == 0 or c == 0 else "Times-Roman", 14)
            pdf.drawString(x + 10, yy - 0.26 * inch, cell)
            x += col_w[c]
        yy -= row_h
    pdf.setFillColor(AMBER)
    pdf.setFont("Times-Bold", 14)
    pdf.drawString(0.55 * inch, 0.95 * inch, "A pass describes the returned prompt. It does not describe what the model will do.")
    pdf.setFillColor(MUTED)
    pdf.setFont("Times-Roman", 13)
    pdf.drawString(0.55 * inch, 0.70 * inch, "Seeds 11 and 2, offline. Seed 12 is the behavioral exception: the section was missing, and the reward still matched T4.")


def limits_slide(pdf: canvas.Canvas) -> None:
    draw_bg(pdf, "What these answers do not license")
    y = draw_title(pdf, "Each limit stays attached to the claim it restricts", HEIGHT - 1.15 * inch, 24)
    bullets(
        pdf,
        [
            "H1 is prompted signaling. No harmful collusion was run, and none was shown to be prevented.",
            "H3 is not a utility bound. No noninferiority margin was defined.",
            "One model, two synthetic equivalent tools, and an explicit codebook.",
            "Seed 12: the assignment was hidden, and the joint reward still matched T4. The contract does not predict that outcome.",
        ],
        0.55 * inch,
        y - 8,
        WIDTH - 1.15 * inch,
        size=16,
        leading=24,
    )


def close_slide(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(NAVY)
    pdf.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)
    pdf.setFillColor(AMBER)
    pdf.rect(0, 0, 0.18 * inch, HEIGHT, fill=1, stroke=0)
    pdf.setFillColor("white")
    pdf.setFont("Times-Roman", 14)
    pdf.drawString(0.7 * inch, HEIGHT - 1.05 * inch, "The bounded finding")
    y = HEIGHT - 1.85 * inch
    for line in wrap(
        "Tool choice can provide a communication channel between LLM agents, but suppressing that channel requires distinguishing execution metadata from the task information needed for cooperation.",
        "Times-Bold",
        24,
        WIDTH - 1.6 * inch,
    ):
        pdf.setFont("Times-Bold", 24)
        pdf.drawString(0.7 * inch, y, line)
        y -= 32
    y -= 12
    for line in wrap(
        "H1: the visible name carried the instructed bit. H2: deleting the event removed measured dependence. H3: keeping a canonical event did not improve on that deletion. Removing the assignment, with the event already hidden, produced duplicate work on three of four seeds.",
        "Times-Roman",
        16,
        WIDTH - 1.6 * inch,
    ):
        pdf.setFont("Times-Roman", 16)
        pdf.drawString(0.7 * inch, y, line)
        y -= 22
    pdf.setFont("Times-Italic", 15)
    pdf.drawString(0.7 * inch, 1.15 * inch, "Ellen Berhe and Muhammad Hassaan Shaukat")
    pdf.setFont("Times-Roman", 13)
    pdf.drawString(0.7 * inch, 0.82 * inch, "Tool-Choice Signaling and Task-State Preservation in LLM Multi-Agent Systems")


def main() -> None:
    slides = [
        title_slide,
        mechanism_slide,
        gap_slide,
        hypotheses_slide,
        h1_h2_slide,
        h3_slide,
        finding_slide,
        contract_slide,
        limits_slide,
        close_slide,
    ]
    pdf = canvas.Canvas(str(OUT), pagesize=PAGE)
    pdf.setTitle("Tool-Choice Signaling and Task-State Preservation in LLM Multi-Agent Systems")
    pdf.setAuthor("Ellen Berhe and Muhammad Hassaan Shaukat")
    total = len(slides)
    for index, painter in enumerate(slides, start=1):
        painter(pdf)
        if painter not in (title_slide, close_slide):
            draw_footer(pdf, index, total)
        pdf.showPage()
    pdf.save()
    print(OUT)


if __name__ == "__main__":
    main()
