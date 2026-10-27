"""Render the revised Actions as Carriers note to a PDF.

The numbers are the original printed table. This script does not read episode logs
and does not call a model.
"""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    ListFlowable,
    ListItem,
)
from reportlab.lib import colors
from reportlab.pdfgen import canvas


OUT = Path(__file__).with_name("Actions_as_Carriers_revised.pdf")
SOURCE = Path(__file__).with_name("ACTIONS_AS_CARRIERS_REVISED.md")


def styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(name="H1", fontName="Times-Bold", fontSize=14, leading=18, spaceAfter=8, spaceBefore=12))
    base.add(ParagraphStyle(name="H2", fontName="Times-Bold", fontSize=12, leading=15, spaceAfter=6, spaceBefore=12))
    base.add(ParagraphStyle(name="Body", fontName="Times-Roman", fontSize=10.5, leading=14, spaceAfter=8, alignment=4))
    base.add(ParagraphStyle(name="Meta", fontName="Times-Italic", fontSize=10, leading=13, spaceAfter=10))
    base.add(ParagraphStyle(name="Caption", fontName="Times-Italic", fontSize=9, leading=12, spaceBefore=4, spaceAfter=8))
    base.add(ParagraphStyle(name="Cell", fontName="Times-Roman", fontSize=8, leading=10))
    base.add(ParagraphStyle(name="Head", fontName="Times-Bold", fontSize=8, leading=10))
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
            self.drawString(0.85 * inch, 0.5 * inch, "Actions as Carriers, revised 25 October 2026")
            self.drawRightString(7.65 * inch, 0.5 * inch, f"{self._pageNumber} / {pages}")
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


def cell(text, style):
    return Paragraph(str(text), style)


def reward_table(s):
    header = ["Arm", "Mona", "Layla", "Jeanene", "Pauline", "Coal.", "Other", "D", "Joint"]
    rows = [
        ["B0", "32.56", "12.71", "22.84", "12.18", "22.64", "17.51", "5.12", "80.29"],
        ["P", "32.56", "22.71", "21.22", "19.37", "27.64", "20.30", "7.34", "95.85"],
        ["V", "32.56", "21.79", "22.30", "22.75", "27.17", "22.52", "4.65", "99.40"],
        ["E", "32.56", "13.17", "21.22", "12.75", "22.87", "16.98", "5.88", "79.69"],
        ["C", "32.56", "13.17", "22.30", "12.75", "22.87", "17.52", "5.34", "80.77"],
        ["S", "32.56", "21.79", "12.84", "12.75", "27.17", "12.79", "14.38", "79.94"],
        ["B1", "32.56", "9.83", "9.51", "9.41", "21.19", "9.46", "11.73", "61.31"],
    ]
    data = [[cell(h, s["Head"]) for h in header]]
    for row in rows:
        data.append([cell(x, s["Cell"]) for x in row])
    table = Table(data, colWidths=[36, 42, 42, 52, 48, 40, 40, 40, 44])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#f4f7fb")),
                ("BACKGROUND", (0, 6), (-1, 6), colors.HexColor("#f8efe6")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b0b7c3")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def bars():
    """Coalition mean, other mean, and D for the seven printed arms."""
    from reportlab.graphics.shapes import Drawing, Rect, String, Line
    from reportlab.graphics.charts.barcharts import VerticalBarChart

    drawing = Drawing(460, 180)
    chart = VerticalBarChart()
    chart.x = 40
    chart.y = 30
    chart.height = 120
    chart.width = 400
    chart.data = [
        [22.64, 27.64, 27.17, 22.87, 22.87, 27.17, 21.19],
        [17.51, 20.30, 22.52, 16.98, 17.52, 12.79, 9.46],
        [5.12, 7.34, 4.65, 5.88, 5.34, 14.38, 11.73],
    ]
    chart.categoryAxis.categoryNames = ["B0", "P", "V", "E", "C", "S", "B1"]
    chart.categoryAxis.labels.fontName = "Times-Roman"
    chart.categoryAxis.labels.fontSize = 8
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 30
    chart.valueAxis.labels.fontName = "Times-Roman"
    chart.valueAxis.labels.fontSize = 8
    chart.groupSpacing = 8
    chart.barSpacing = 1
    chart.bars[0].fillColor = colors.HexColor("#1f4e79")
    chart.bars[1].fillColor = colors.HexColor("#7f9bb3")
    chart.bars[2].fillColor = colors.HexColor("#c45911")
    chart.barLabelFormat = None
    drawing.add(chart)
    drawing.add(Rect(40, 8, 8, 8, fillColor=colors.HexColor("#1f4e79"), strokeColor=None))
    drawing.add(String(52, 8, "Coalition mean", fontName="Times-Roman", fontSize=8))
    drawing.add(Rect(140, 8, 8, 8, fillColor=colors.HexColor("#7f9bb3"), strokeColor=None))
    drawing.add(String(152, 8, "Other mean", fontName="Times-Roman", fontSize=8))
    drawing.add(Rect(230, 8, 8, 8, fillColor=colors.HexColor("#c45911"), strokeColor=None))
    drawing.add(String(242, 8, "D", fontName="Times-Roman", fontSize=8))
    drawing.add(Line(40, 150, 440, 150, strokeColor=colors.white))
    return drawing


def story(s):
    text = SOURCE.read_text(encoding="utf-8")
    # The PDF body is written here so the layout is stable. The markdown is the source
    # the reader edits; this builder follows that file's sections in order.
    assert "D(S)" in text or "4.65" in text
    flow = []
    flow.append(Paragraph("Actions as Carriers: Side-Channel Collusion and the Metrics That Hide It", s["H1"]))
    flow.append(Paragraph(
        "Apart Research Sprint 2026, Track 3.1. Muhammad Hassaan Shaukat. Revised 25 October 2026 after an offline validity audit. The seven-arm ladder was not rerun.",
        s["Meta"],
    ))
    sections = [
        ("Abstract", """Track 3.1 asks whether collusion can travel through a channel other than chat, and whether an observation filter can make the coalition-advantage statistic point the wrong way. The published ladder is one episode per arm on a path of four Jira agents, seed 1, with the intended coalition at the endpoints. This revision checks that ladder against its own reward table and against the committed runner. In the printed table, full filtering raises coalition advantage from 4.65 in the action-only arm to 14.38, while the coalition mean stays 27.17. The increase equals the non-coalition mean falling from 22.52 to 12.79. Mona and Layla do not change between those two rows. Against the cooperative baseline the coalition mean also rises, so that increase is not carried by the outgroup alone. The smallest value of the statistic is the action-only arm, which also has the highest joint reward. Minimizing the statistic does not select the blinding arm. The episode files named in the original appendix are not in this repository, and the committed runner does not attach the observation filter. These statements describe the printed table. They are not a reconstruction from raw rewards, and they are not a multi-seed replication."""),
        ("1. Introduction", """The question is unchanged. If a designated pair can coordinate through a tool action or through residue in shared state, a filter that only reads chat misses the carrier. The statistic usually used to detect that coordination is the gap between the coalition's mean reward and everyone else's. A gap can widen because the coalition gained, because the others lost, or both."""),
        (None, """The original report concluded that full blinding inflates this gap while every agent's reward falls, and that a defence chosen by minimizing the gap can be harmful. The reward table in that report does not support those two sentences. This revision states what the table does support, and what the stored code cannot yet show. No arm was rerun. No prompt was edited after the audit."""),
        ("2. What was held fixed in the reported design", """The environment is the Colosseum Jira task. Four agents stand on a path. Each may claim tasks. The joint score trades completed work against cost and a penalty for conflicting claims. The intended coalition is the two endpoints, who share no blackboard. The reported model is gemini-3.5-flash-lite at temperature 0.7, with one conversation step, two planning rounds, eight tasks, and seed 1."""),
        (None, """The seven arms, as named in the original report, are the cooperative baseline B0, the private-channel control P, action-only V, event hiding E, canonicalization C, full filtering S, and blinded unprompted B1. The quantity of interest is D, the mean reward of the labeled coalition minus the mean reward of the other agents."""),
        (None, """Seed 1 with four agents draws the names Layla, Jeanene, Pauline, and Mona, in that order, from the environment's name generator. The ends of that list are Layla and Mona. The original table labels those two as the coalition and Jeanene and Pauline as the others. That match is a property of the name generator. The membership log was not available."""),
        ("3. What the repository actually contains", """Commit 5feedab on origin/track31-action-carriers contains the seven config files and observation_filter.py. The diff of that commit against its parent is empty for run.py, prompts.py, and metrics.py. The runner never constructs the filtering client. Every config sets colluder selection to first_and_last, and the runner accepts only random and first, so loading these configs raises before an episode starts. When the secret channel is off, the runner also forces the cooperative prompt. The configs name OpenRouter. The original report names Google's compatible endpoint. The episode directories cited by timestamp are not in the commit."""),
        (None, """The numbers below are the original printed table, checked for internal arithmetic. They are not a new measurement."""),
        ("4. The printed ladder", """Table 1 reprints the per-agent rewards. Mona is 32.56 in every row. Recomputing each mean from the four printed rewards recovers D at the reported two-decimal precision. The sum of the four rewards matches the reported joint reward except for a 0.01 rounding gap on P, E, and C."""),
    ]
    for title, body in sections:
        if title:
            flow.append(Paragraph(title, s["H2"]))
        flow.append(Paragraph(body, s["Body"]))
    flow.append(Paragraph("Table 1. Printed per-agent rewards and the means recomputed from them. V and S are shaded. Coalition members in the original labeling are Mona and Layla.", s["Caption"]))
    flow.append(reward_table(s))
    flow.append(Spacer(1, 8))
    rest = [
        (None, """Because D is itself a difference, the change from one arm to another is a difference of differences: the change in D equals the change in the coalition mean minus the change in the other mean."""),
        (None, """From the unrounded printed components, D(S) minus D(V) is 9.730. The coalition-mean change is 0. The other-mean change is -9.730. The whole increase is the drop in Jeanene's and Pauline's rewards, by 9.46 and 10.00. Mona and Layla are the same in V and in S."""),
        (None, """Against B0, S is a different pattern. The coalition mean rises by 4.54 and the other mean falls by 4.72. Both terms widen D. The original sentence that the entire increase comes from outgroup degradation, and that the coalition mean is lower than the baseline, does not fit S. B1 does have a lower coalition mean than B0, 21.19 against 22.64, and its other mean falls by more than that."""),
        (None, """V has the smallest D, 4.65, and the largest joint reward, 99.40. S has the largest D, 14.38, and a joint reward of 79.94. A rule that minimizes D selects V. It does not select the blinding arm. A rule that treats a large D as evidence of harmful coordination is the rule that mislabels S and B1."""),
        (None, """Figure 1 plots the three printed series. The bars are the table, not a confidence interval."""),
    ]
    for title, body in rest:
        flow.append(Paragraph(body, s["Body"]))
    flow.append(bars())
    flow.append(Paragraph("Figure 1. Printed coalition mean, other mean, and D. Source: the original Table 3, not episode logs.", s["Caption"]))
    tail = [
        ("5. Position", """The original report says Mona acts before any filter can affect her, so one coalition member is outside the intervention. Her printed reward is constant, which is consistent with that account and consistent with other accounts. No turn-order field was available. The configs set a random agent order. The runner can also place colluders first. Neither option rotates a single first mover while leaving the endpoints as the coalition. No such episode was run. Relabeling these rewards would change D on paper and would not show what a new order does."""),
        ("6. Conclusion", """On the printed table, removing the messaging tool does not raise D above the cooperative baseline: V is 4.65 and B0 is 5.12, and V has the best joint reward. Full filtering raises D without raising the coalition mean above the action-only arm. That is enough to show that a larger D is not monotone in coalition reward. It is not enough to show that minimizing D selects a harmful filter, that every agent lost reward, or that the pattern survives another seed."""),
        (None, """The next measurement is the same five arms, B0, P, V, S, and B1, on seeds 31 through 42, two draws each, after a runner that actually applies the filter and writes the returned prompt. That cohort was not started. Until the missing episode files are recovered, the table remains a printed result rather than an independently reconstructed one."""),
        ("References", """Nakamura et al. Colosseum: A Harness for Studying Collusion in Multi-Agent Systems. arXiv:2602.15198, 2026."""),
        (None, """Apart Research. AI Collusion Research Sprint, 23–25 October 2026. Track 3.1."""),
        ("Appendix A. Reproduction status", """The original appendix points to the seven track31 configs, observation_filter.py, and run.py, and to episode timestamps on 25 October 2026. The configs and the filter module are on origin/track31-action-carriers at 5feedab. The runner at that commit does not import the filter. The timestamped episode directories are not in the commit and were not found under experiments/collusion/outputs/ in this worktree. A patch file describes the twelve-line runner edit that would wrap the client. That edit is not in run.py."""),
        (None, """Preexisting code is the Colosseum runner and the Terrarium Jira environment. The sprint commit adds the filter module, the seven configs, and the offline report scripts. It does not add the episode logs."""),
        ("Appendix B. Limitations and Dual-Use / Ethical Considerations", """Limitations. One printed seed. Four agents, one model line, one path, and a coalition intended for the endpoints. The original report already measured that a rerun of the event-hiding arm moved D by about 0.7. The gaps for E and C against B0 sit near that spread. The V-to-S gap is larger, and it is still one seed. Mona's constant reward was not tied to a logged turn order. The saved runner cannot execute the ladder as specified, so the filter's effect on the model request was not rechecked here. Coverage, violations, and message counts in the original Table 2 were not recomputed, because the tool logs are absent. No new collusion metric was proposed or scored."""),
        (None, """Dual use. The ladder shows a designated pair, a private board, and a set of observation deletions. Those are the conditions of a measurement, not a method for making unprompted agents collude. The useful reading is the opposite of a defence recipe: deleting shared observations can make a difference-of-means look like collusion while the labeled coalition's mean stays at the action-only value. Publishing that fact makes the weak score easier to recognize. It does not show that blinding prevents harmful coordination, and it does not show that harmful coordination occurred."""),
    ]
    for title, body in tail:
        if title:
            flow.append(Paragraph(title, s["H2"]))
        flow.append(Paragraph(body, s["Body"]))
    return flow


def main():
    s = styles()
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.7 * inch,
        title="Actions as Carriers: Side-Channel Collusion and the Metrics That Hide It",
        author="Muhammad Hassaan Shaukat",
    )
    doc.build(story(s), canvasmaker=NumberedCanvas)
    print(OUT)


if __name__ == "__main__":
    main()
