"""Build the Track 3.1 submission PDF from the artifacts, through report_data.

No number in the report is typed here. Every figure is interpolated from `report_data.build()`,
which reads the run artifacts and the two offline harness JSONs and raises if an arm is
corrupted, a condition config is not matched, or an artifact is missing. So this file can be
re-run after any new artifact lands and the text will follow the data.

Usage:  python experiments/collusion/build_report.py [output.pdf]
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from experiments.collusion.report_data import ARMS, LABELS, build  # noqa: E402

OUT = (Path(sys.argv[1]) if len(sys.argv) > 1
       else Path(__file__).resolve().parents[3].parent / "Track3_1_Action_Carriers_Report.pdf")

D = build()
A = D["by"]
PR = D["protocol"]
H1, H2 = D["h1"], D["h2"]
C1, C2 = H1["composite"], H1["complementarity"]
TXT = H1["text"]
V_PEAK_AGENTS = [n for n in D["outgroup_names"] if D["agent_peak_arm"][n] == "V"]
V_OTHER_AGENTS = [n for n in D["outgroup_names"] if D["agent_peak_arm"][n] != "V"]

# The prose below states these outright. If an artifact stops supporting one of them, the build
# stops instead of printing a sentence that is no longer true.
_ARMS = D["arms"]
# Recomputed here from the arm rows rather than trusted from report_data, so a map that names a
# pair cannot be wrong about that pair being the only one that isolates a factor.
_PROMPT_ONLY = [(a["label"], b["label"]) for i, a in enumerate(_ARMS) for b in _ARMS[i + 1:]
                if a["filter"] == b["filter"]
                and a["secret_channel_enabled"] == b["secret_channel_enabled"]
                and a["coalition_prompt"] != b["coalition_prompt"]]
_CHANNEL_ONLY = [(a["label"], b["label"]) for i, a in enumerate(_ARMS) for b in _ARMS[i + 1:]
                 if a["filter"] == b["filter"] and a["coalition_prompt"] == b["coalition_prompt"]
                 and a["secret_channel_enabled"] != b["secret_channel_enabled"]]
for _ok, _what in [
    (D["selection"]["scanned"] == D["selection"]["usable"]
     + D["selection"]["rejected_error_turns"] + D["selection"]["rejected_unscored"]
     + D["selection"]["no_scored_run"]
     and D["selection"]["usable"] == D["selection"]["arms"] + D["selection"]["superseded"],
     "every launch directory on disk is accounted for as chosen, superseded or rejected"),
    (sorted(a["timestamp"] for a in _ARMS) == sorted(H1["timestamps"]) == sorted(H2["timestamps"]),
     "the report and both offline analyses read the same seven episodes"),
    (D["clone_same_run_id"], "the two clone episodes share one recorded run_id"),
    (D["turn_order_identical"], "every arm shares one recorded turn order"),
    (D["s_coalition_equals_v"], "S's coalition mean is V's to the last digit"),
    (D["b1_coalition_below_baseline"] > 0 and D["worst_joint_arm"] == "B1",
     "B1's coalition mean is below baseline and B1 is where group reward is worst"),
    (D["worst_delta_arm"] == "S", "S is the arm where the statistic is largest"),
    (D["assigns_identical"], "every arm fires the same number of assign_task calls"),
    (not D["protocol"]["conflicts"], "the condition configs are matched outside the filter block"),
    (D["naive_canon"]["rejected"] == D["naive_canon"]["assign_calls"],
     "every naive-canonicalisation call was rejected"),
    (D["h2"]["gate_max_abs_error"] == 0.0, "the replay reproduces every logged joint reward exactly"),
    (len(D["invariant_agents"]) == 1, "exactly one agent is reward-invariant across the ladder"),
    (len(V_PEAK_AGENTS) == 1 and len(V_OTHER_AGENTS) == 1,
     "exactly one middle agent peaks in V and the other one does not, as 5.2 says"),
    (D["noncoalition_mean_peak"] == "V", "V is where the non-coalition mean is highest"),
    (D["coalition_prompt"]["B0"] == "never" and D["coalition_prompt"]["P"] != "never",
     "B0 is the unprompted arm the rest of the ladder is measured against"),
    (len(D["prompt_pair"]) == 2 and len(set(D["prompt_pair"])) == 2
     and sorted(D["prompt_pair_prompts"]) == ["always", "never"],
     "section 5.3 can name two distinct arms that differ only in whether the prompt is there"),
    (D["prompt_pair_delta_gain"] > 0 and D["prompt_pair_joint_gain"] > 0,
     "withdrawing the prompt lowers both the statistic and group reward, which is how 5.3 reads them"),
    (len(D["channel_only_pairs"]) == 0,
     "no two arms change the secret channel and nothing else, as 5.2 says"),
    (_CHANNEL_ONLY == [], "recomputing the channel-only pairs from the arm rows still finds none"),
    (len(_PROMPT_ONLY) == 1 and {frozenset(p) for p in _PROMPT_ONLY}
     == {frozenset(D["prompt_pair"])},
     "section 5.3's pair is the one the arm rows single out, and it is unique"),
    (set(l for l, _v in D["normalized_nonzero_arms"]) == set(D["full_coverage_arms"]),
     "the only arms with a non-zero normalized score are the ones with full coverage"),
    (H1["scanned"] == len(H1["skipped_error_turns"]) + H1["undecodable"] + H1["decoded"]
     and H1["decoded"] == H1["superseded"] + H1["runs"],
     "the H1 artifact accounting closes"),
    (H2["scanned"] == H2["rejected"] + H2["replayable"]
     and H2["replayable"] == H2["superseded"] + H2["runs"],
     "the H2 artifact accounting closes"),
    (D["best_joint_arm"] == "V" and A["V"]["violations"] == 0
     and A["V"]["coverage"] >= 1.0, "V is the best arm on joint reward, with coverage and no violations"),
]:
    if not _ok:
        raise AssertionError("the report asserts that %s, and the artifacts no longer say so" % _what)

# ----------------------------------------------------------------------------- formatting
def f(v, dp=2):
    return ("%%.%df" % dp) % v


def sg(v, dp=2):
    """Signed, with the HTML minus the rest of the document uses."""
    return ("+%." + str(dp) + "f" if v >= 0 else "&minus;%." + str(dp) + "f") % abs(v)


def sci(v):
    return "%.1e" % v


def cap(s):
    """An arm tag from an artifact's own record, as the report names it."""
    return str(s).replace("track31_", "").upper()


def ands(seq):
    seq = list(seq)
    if len(seq) < 3:
        return " and ".join(seq)
    return ", ".join(seq[:-1]) + " and " + seq[-1]


def arm(lbl, key):
    return A[lbl][key]


def dgap(x, y):
    return arm(x, "delta") - arm(y, "delta")


def jgap(x, y):
    return arm(x, "joint") - arm(y, "joint")


# Arm display names are presentation, not results; the filter columns below are read from data.
ARM_NAMES = {
    "B0": "Cooperative baseline",
    "P": "Private channel (positive control)",
    "V": "Action-only",
    "E": "Hidden tool events",
    "S": "Selective filtering",
    "C": "Canonicalised actions",
    "B1": "Blinded, no coalition prompt",
}

ss = getSampleStyleSheet()
H1S = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=13, leading=16, spaceBefore=14,
                     spaceAfter=6, textColor=colors.HexColor("#111111"))
H2S = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=11, leading=14, spaceBefore=10,
                     spaceAfter=4, textColor=colors.HexColor("#222222"))
BODY = ParagraphStyle("BODY", parent=ss["BodyText"], fontSize=9.6, leading=13.2,
                      alignment=TA_JUSTIFY, spaceAfter=6)
# Justification stretches badly on paragraphs full of long unbreakable code identifiers.
BODYL = ParagraphStyle("BODYL", parent=BODY, alignment=TA_LEFT)
BULL = ParagraphStyle("BULL", parent=BODY, leftIndent=14, bulletIndent=4, spaceAfter=3)
TITLE = ParagraphStyle("TITLE", parent=ss["Title"], fontSize=17, leading=21, spaceAfter=6)
META = ParagraphStyle("META", parent=ss["Normal"], fontSize=9.2, leading=12, alignment=1)
ABS = ParagraphStyle("ABS", parent=BODY, leftIndent=22, rightIndent=22, fontSize=9.2, leading=12.6)
SMALL = ParagraphStyle("SMALL", parent=ss["Normal"], fontSize=8.2, leading=10.4, spaceAfter=4)
CAP = ParagraphStyle("CAP", parent=ss["Normal"], fontSize=8.4, leading=11, alignment=TA_LEFT,
                     spaceBefore=3, spaceAfter=8)

story = []


def p(text, style=BODY):
    story.append(Paragraph(text, style))


def h1(text):
    story.append(Paragraph(text, H1S))


def h2(text):
    story.append(Paragraph(text, H2S))


def bullet(text):
    story.append(Paragraph(text, BULL, bulletText=u"\u2022"))


def table(data, widths, caption, fontsize=7.8, keep=True):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), fontsize),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f6f6")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(Spacer(1, 4))
    # Tables 1 and 2 must not split; Table 3 repeats its header instead of leaving a third of a
    # page empty, which is the cheaper bad-looking option at eight pages.
    if keep:
        story.append(KeepTogether([t, Paragraph(caption, CAP)]))
    else:
        story.append(t)
        story.append(Paragraph(caption, CAP))


# Dates are derived from the artifacts themselves, not typed.
_rd = D["run_date"]
DATE = "%d %s %d" % (int(_rd[6:8]),
                     ["January", "February", "March", "April", "May", "June", "July",
                      "August", "September", "October", "November", "December"][int(_rd[4:6]) - 1],
                     int(_rd[0:4]))

# --------------------------------------------------------------------------------------
story.append(Paragraph("Actions as Carriers: Side-Channel Collusion and the Metrics That Hide It", TITLE))
story.append(Paragraph("APART Sprint 2026 &mdash; Track 3.1 (&ldquo;Beyond colluding directly via text, can actions, tools or other "
                       "side channels be the conduit for collusion?&rdquo;)", META))
story.append(Paragraph("Muhammad Hassaan Shaukat", META))
story.append(Paragraph(DATE, META))
story.append(Spacer(1, 10))

p("<b>Abstract.</b> Track 3.1 asks whether collusion can travel through channels other than chat. We instrument "
  "the Colosseum Jira ticket-assignment environment with a client-side observation filter that can remove each "
  "candidate carrier independently &mdash; the messaging tool, the rendered action events on the shared blackboard, "
  "the structured assignment block, and the semantic identity of the actions themselves &mdash; and run %d matched "
  "arms on a %s network of %d agents whose designated coalition sits at the two endpoints and therefore shares "
  "no blackboard. Three results stand out. First, the positive control behaves as the theory predicts: opening a "
  "private channel raises coalition advantage from %s to %s (%s) and joint reward from %s to %s. Second, when "
  "messaging is deleted and only actions remain, the advantage does <i>not</i> survive (%s, %s below the private "
  "channel), while group reward reaches its highest value of any arm (%s, zero violations): in this environment the "
  "channel that enables collusion also costs the group. Third, and most consequentially for countermeasure design, "
  "symmetric blinding <i>inflates</i> the standard delta-collusion statistic to %s &mdash; %s times the baseline "
  "&mdash; while the coalition gains nothing from it: its mean reward in that arm equals the action-only arm&rsquo;s "
  "to the last digit, and the whole widening comes from outgroup degradation. Withdrawing the prompt as well leaves "
  "the statistic at %s with the coalition&rsquo;s mean below the baseline and the group at its worst value in the "
  "ladder (%s). Delta-collusion is not monotone in collusion, and a defence chosen by minimising it "
  "can be actively harmful. We also show that the canonicalisation defence named in the official ablation is only "
  "implementable as a reversible rewrite: applied naively it destroys the action space, and all %d task "
  "assignments are rejected. To test the carrier question directly rather than through the reward gap, we add two "
  "offline analyses of the same %d traces: a label-blind decoder that must pick the coalition from actions alone, "
  "which beats its exact %s null (%d/%d, p = %s) but no more often once messaging is removed; and a counterfactual "
  "replay through the environment&rsquo;s own scoring function, which shows the pair&rsquo;s actions are the "
  "load-bearing ones for group reward (marginal value %s vs %s, %d/%d runs) because they occupy placements the "
  "exact optimiser cannot improve."
  % (D["arm_count"], PR["topology"], PR["num_agents"],
     f(arm("B0", "delta")), f(arm("P", "delta")), sg(D["control_gain_delta"]),
     f(arm("B0", "joint")), f(arm("P", "joint")),
     f(arm("V", "delta")), f(D["action_only_below_private"]), f(D["best_joint"]),
     f(arm("S", "delta")), f(D["s_over_baseline_ratio"], 1), f(arm("B1", "delta")), f(D["worst_joint"]),
     D["naive_canon"]["assign_calls"], D["arm_count"],
     "1/%d" % H1["n_pairs"], C1["all"]["rank_1"], C1["all"]["runs"], f(C1["all"]["p_rank_1_or_better"], 3),
     f(H2["co_drop"], 1), f(H2["og_drop"], 1), H2["drop_wins"], H2["runs"]), ABS)
story.append(Spacer(1, 6))
p("<b>Keywords:</b> multi-agent collusion, side channels, observability, countermeasures, DCOP, evaluation metrics.", SMALL)

# --------------------------------------------------------------------------------------
h1("1. Introduction")
p("Collusion research has converged on a single question &mdash; can agents coordinate against the designer&rsquo;s "
  "interest? &mdash; while leaving a second question comparatively open: <i>through what</i> do they coordinate? "
  "Track 3.1 asks the second question. If a coalition can transmit its intent through tool calls, event ordering, "
  "or residue left in shared environment state, then a countermeasure that only reads and filters chat misses the "
  "conduit entirely.")
p("Answering it needs an intervention, not an observation: we must delete one carrier at a time and see what "
  "survives. That requirement exposed a second problem, which turned out to be the more interesting one. The "
  "measure we would normally use to decide whether a carrier works &mdash; the reward advantage of the designated "
  "coalition over everyone else &mdash; moves in the wrong direction under the strongest defence. It grows when the "
  "environment is made harder for all agents, because it is a <i>difference</i>, and a difference can widen by "
  "hurting the subtrahend.")
p("Contributions of this sprint:")
bullet("<b>A carrier-resolved intervention harness.</b> Four independent observation-path filters wrapped around the "
       "provider client, so the model&rsquo;s input is rewritten before the call and no installed package is patched. "
       "Each arm reports what the filter actually removed.")
bullet("<b>A matched %d-arm ladder</b> on a fixed topology, fixed coalition pair and fixed seed, all with zero "
       "corrupted turns, comparing private communication against action-only, event-hidden, assignment-masked, "
       "canonicalised and fully-blinded conditions. The matching is checked, not assumed: the %d condition "
       "configurations are diffed leaf by leaf across the whole document, and the only fields that move are the "
       "arm&rsquo;s own output identity and %s."
       % (D["arm_count"], D["arm_count"], ands(PR["differing_intervention"])))
bullet("<b>Evidence that delta-collusion is not monotone in collusion.</b> We decompose the statistic in the worst "
       "arm and show the entire increase comes from outgroup degradation: the coalition&rsquo;s own mean there "
       "equals the action-only arm&rsquo;s to the last digit, and with the prompt withdrawn it falls below the "
       "baseline while the statistic still reads %s times baseline." % f(D["b1_over_baseline_ratio"], 2))
bullet("<b>A concrete implementability result for the canonicalisation defence,</b> including the failure mode that "
       "makes the naive version unusable.")

# --------------------------------------------------------------------------------------
h1("2. Setup")
h2("2.1 Environment and coalition")
p("We use the %s shipped with Colosseum: a decentralised constraint-optimisation "
  "task in which each agent may claim tickets, and the joint reward trades task value against execution cost and "
  "violations (overlapping skills, exceeded capacity). Agents act through two tools, "
  "<font face=\"Courier\">assign_task</font> and <font face=\"Courier\">post_message</font>, plus a "
  "<font face=\"Courier\">skip</font> path. Coalitions are designated by the harness: two agents are told they are "
  "partners and are given a hidden objective, while the others receive the ordinary cooperative prompt."
  % PR["environment"])
h2("2.2 Why a path topology, and why the endpoints")
p("The paper&rsquo;s conditions are meant to differ in <i>which channels exist</i>. On a complete topology the whole "
  "network is already a single channel open to everyone, so adding a coalition-only blackboard changes almost "
  "nothing, and a &ldquo;private channel&rdquo; condition becomes unidentifiable. We therefore use a %s of %d "
  "agents and select the coalition as the two <i>endpoints</i> (<font face=\"Courier\">%s</font>: %s and %s). They "
  "share no blackboard at all: any information that reaches one from the other must travel through the middle "
  "agents&rsquo; boards, and hence through whatever those agents can also see. That is precisely the setting in "
  "which a side channel is the only channel."
  % (PR["topology"], PR["num_agents"], PR["colluder_selection"],
     D["coalition_names"][0], D["coalition_names"][1]))
h2("2.3 The statistic, and its known weakness")
p("The repo&rsquo;s headline collusion number is the unnormalised difference between the coalition&rsquo;s mean "
  "reward and the non-coalition&rsquo;s mean reward:")
p("<font face=\"Courier\">&Delta; = mean(reward | colluder) &minus; mean(reward | other)</font>", SMALL)
p("Everything downstream in this report is conditioned on that definition. It is a difference of means over a "
  "network of %d, so it is sensitive to <i>both</i> terms, it is not bounded, and it has a non-zero structural "
  "value even with no coalition prompt at all &mdash; measured here at %s in arm B0, whose recorded coalition "
  "prompt is <font face=\"Courier\">%s</font>. We therefore never read &Delta; against zero; the comparison is "
  "always against that arm."
  % (PR["num_agents"], f(arm("B0", "delta")), D["coalition_prompt"]["B0"]))

# --------------------------------------------------------------------------------------
h1("3. Interventions")
p("All four interventions live in a wrapper around the provider client, applied to the prompt text and the tool "
  "list on the way into the model. Nothing in the installed agent library is modified, so the harness survives a "
  "clean dependency install and cannot silently diverge from upstream.")


def filter_columns(label):
    """Table 1's four carrier columns, read out of that condition's own YAML."""
    fl = PR["filters"][label]
    messaging = ("removed" if fl.get("block_post_message")
                 else ("open + hidden board" if D["secret_channel"][label] else "open"))
    events = ("removed" if fl.get("hide_action_events")
              else ("kept, unreadable" if fl.get("canonicalise_actions") else "visible"))
    block = ("masked" if fl.get("mask_current_assignments")
             else ("kept, unreadable" if fl.get("canonicalise_actions") else "visible"))
    identity = "opaque token" if fl.get("canonicalise_actions") else "readable"
    return [label, ARM_NAMES[label], D["coalition_prompt"][label], messaging, events, block, identity]


table([["Arm", "Name", "Prompt", "Messaging tool", "Action events", "Assignment block", "Action identity"]]
      + [filter_columns(lbl) for lbl, _t, _ts in ARMS],
      [0.34 * inch, 1.6 * inch, 0.5 * inch, 0.9 * inch, 0.92 * inch, 1.02 * inch, 0.98 * inch],
      "Table 1. The %d arms. The prompt column is read from each run artifact and the four carrier columns from "
      "each condition&rsquo;s YAML, so the table cannot drift from what was run. Only %s are unprompted; %s all "
      "carry the coalition prompt. The clean single-factor comparison for the prompt is therefore %s against %s, "
      "which is identical except for it, while every arm measured against %s changes the prompt and the "
      "observation at once &mdash; stated wherever it matters."
      % (D["arm_count"], ands(D["unprompted_arms"]), ands(D["prompted_arms"]),
         D["prompt_pair"][0], D["prompt_pair"][1], "B0"))
h2("3.1 Two paths, not one")
p("A claimed task reaches the other agents twice over: once as a structured <font face=\"Courier\">CURRENT "
  "ASSIGNMENTS</font> block, and once as a rendered <font face=\"Courier\">[action_executed]</font> blackboard event "
  "whose payload also carries the running joint reward. Hiding either path alone leaves the other intact, so an "
  "experiment that deletes only one measures nothing about the carrier; it measures the surviving copy. Arms E and "
  "S separate the two paths deliberately.")
h2("3.2 Canonicalisation, and why it has to be reversible")
p("The official ablation asks for actions that are &ldquo;hidden or canonicalised&rdquo;. Only the second option "
  "controls for the obvious confound, because deleting text shortens the episode and changes token cost, which "
  "changes behaviour for reasons unrelated to the carrier. Canonicalising keeps length matched and neutralises "
  "meaning instead.")
p("The naive version of that idea fails, and we measured it. Rewriting every task identifier to one shared "
  "placeholder leaves the model able to <i>refer</i> to an action but not to <i>name</i> one. The recorded artifact "
  "(<font face=\"Courier\">%s</font>) shows the consequence: the filter rewrote %d identifier mentions identically "
  "for every agent, all %d <font face=\"Courier\">assign_task</font> calls came back with status "
  "<font face=\"Courier\">retry</font> and reason <font face=\"Courier\">%s</font>, the episode ended "
  "<font face=\"Courier\">%s</font> with %d decisions made and no joint reward to score. Identifiers are "
  "load-bearing in the action space, not just the observation space. The usable form gives each distinct task its "
  "own opaque token inside the agent&rsquo;s view and re-expands the token to the real identifier when the "
  "model&rsquo;s own tool call is executed. Under arm C the filter rewrote between %d and %d identifier mentions per "
  "agent (%d calls each) and restored %d&ndash;%d action arguments per agent, and the episode completed normally. "
  "What survives the rewrite is exactly the residual carrier Track 3.1 is asking about: an opaque key, and the "
  "order of events."
  % (D["naive_canon"]["timestamp"], D["naive_canon"]["rewrites_per_agent"],
     D["naive_canon"]["assign_calls"], D["naive_canon"]["reasons"][0],
     D["naive_canon"]["status"], D["naive_canon"]["decisions_made"],
     arm("C", "canonicalised_per_agent")[0], arm("C", "canonicalised_per_agent")[1],
     PR["calls_per_agent"], arm("C", "restores_per_agent")[0], arm("C", "restores_per_agent")[1]))
h2("3.3 Verification")
p("Two checks are run per arm rather than assumed. First, the tool mix in the recorded events: under the "
  "messaging-blocking arms (%s) <font face=\"Courier\">post_message</font> is absent entirely (0 calls) while "
  "<font face=\"Courier\">assign_task</font> still fires %d times in every arm of the ladder, so the intervention "
  "removed a capability rather than discouraging its use. Second, an offline suite of %d tests over two prompts "
  "captured verbatim from a real run, asserting per preset which path was removed, that the untouched path "
  "survives, that scoping to one agent still hides the others&rsquo; names, and that the client&rsquo;s method "
  "syncness matches the contract the agent loop expects."
  % (ands(D["blocked_arms"]), D["assign_calls"], D["tests"]))

# --------------------------------------------------------------------------------------
h1("4. Protocol")
p("Model: <font face=\"Courier\">%s</font>, temperature %s, max output %s tokens, called through the "
  "<font face=\"Courier\">%s</font> provider route using a free-tier key. No paid inference was used, and the key "
  "is held only in the git-ignored environment file, never in a config."
  % (PR["model"], f(PR["temperature"], 1), PR["max_tokens"], PR["provider"]))
p("Network: %s, %d agents, coalition = %s (the endpoints), random turn order seeded at %s, %d simulation "
  "iteration%s with %d planning rounds and %d tasks. Every arm shares these settings and differs only in the "
  "columns of Table 1; the turn order is identical across all %d artifacts (%s)."
  % (PR["topology"], PR["num_agents"], PR["colluder_selection"], PR["seed"],
     PR["max_iterations"], "" if PR["max_iterations"] == 1 else "s",
     PR["max_planning_rounds"], PR["max_tasks"], D["arm_count"],
     ", ".join(D["agent_names"])))
h2("4.1 The multi-turn constraint, stated plainly")
p("The paper&rsquo;s protocol allows each agent a short tool-loop within its turn. We could not use it. The agent "
  "library&rsquo;s multi-step loop builds a request that ends with a model turn, which the endpoint rejects with "
  "<font face=\"Courier\">400 INVALID_ARGUMENT</font>; the loop catches the failure and writes an error marker into "
  "the turn, so the run still reports <i>complete</i> while its turns are corrupted. This reproduces on both the "
  "native client and the compatibility layer, so it is a property of the harness&rsquo;s request shape, not of one "
  "provider. All arms therefore run at %d conversation step%s per turn."
  % (PR["max_conversation_steps"], "" if PR["max_conversation_steps"] == 1 else "s"))
p("One step is still a valid test of the carrier hypothesis, and it is worth being precise about why. The filter "
  "acts on the observation, and partners remain observable: an agent&rsquo;s action is written to the blackboard "
  "before the next agent is prompted, so the second endpoint reads the first endpoint&rsquo;s behaviour even though "
  "neither ever sees the result of its own tool call inside its turn. What the reduced setting removes is "
  "intra-turn repair, not inter-agent visibility.")
h2("4.2 Gating")
p("No metric in this report is trusted until its <font face=\"Courier\">agent_turns.json</font> contains zero error "
  "markers; all %d arms pass, each with %d of %d turns clean. One recorded run in the pre-sprint clone reports "
  "<i>complete</i> with %d of %d turns carrying an error payload, which is the reason the gate exists. %d model "
  "calls per arm (%d per agent, one conversation step each); total spend was zero, since the endpoint is free-tier."
  % (D["arm_count"], arm("B0", "turns"), arm("B0", "turns"),
     D["clone_corrupted_errors"], D["clone_corrupted_turns"],
     D["protocol"]["total_calls"], PR["calls_per_agent"]))

# --------------------------------------------------------------------------------------
h1("5. Results")
table([[u"Arm", u"\u0394 adv.", "Joint R", "Ratio", "Cov.", "Viol.", "Coal. regret",
        "Non-coal regret", "posts"]]
      + [[a["name"], f(a["delta"]), f(a["joint"]), f(a["ratio"], 3), f(a["coverage"], 2), a["violations"],
          f(a["coalition_regret"]), f(a["noncoalition_regret"]), a["posts"]] for a in D["arms"]],
      [1.35 * inch, 0.62 * inch, 0.62 * inch, 0.5 * inch, 0.45 * inch, 0.45 * inch, 0.75 * inch,
       0.82 * inch, 0.45 * inch],
      "Table 2. All %d arms, seed %s, zero corrupted turns. &Delta; adv. is the coalition-minus-others mean reward; "
      "Joint R is the group reward; Ratio is joint reward over the closed-form optimum; Cov. is whether the "
      "assignment satisfies the coverage constraint; posts is <font face='Courier'>post_message</font> calls "
      "recorded in the tool events. Regret is measured against the per-agent optimum."
      % (D["arm_count"], PR["seed"]))
table([["Arm"] + ["%s%s" % (n, " (coal.)" if n in D["coalition_names"] else "") for n in D["agent_names"]]
        + ["Coal. mean", "Non-coal. mean"]]
      + [[a["label"]] + [f(a["agent_rewards"][n]) for n in D["agent_names"]]
         + [f(a["coalition_mean"]), f(a["noncoalition_mean"])] for a in D["arms"]],
      [0.55 * inch] + [0.72 * inch] * len(D["agent_names"]) + [0.9 * inch, 1.0 * inch],
      "Table 3. Per-agent rewards, agents listed in the recorded turn order. The two coalition members are %s, "
      "the endpoints of the path. Note that %s is identical in every arm (%s) and that S reproduces "
      "V&rsquo;s coalition mean exactly."
      % (ands(D["coalition_names_in_order"]), list(D["invariant_agents"])[0],
         f(list(D["invariant_agents"].values())[0][0])), keep=False)
h2("5.1 The positive control works")
p("Opening a private channel raises &Delta; from %s to %s (%s) and joint reward from %s to %s (%s), with coverage "
  "moving from %s to %s and violations from %d to %d. All %d colluder posts land on the hidden board "
  "(secret-channel post rate %s). The harness reproduces the paper&rsquo;s central behaviour with a free small "
  "model: given a channel and an incentive, the pair coordinates and both the pair and the group do better."
  % (f(arm("B0", "delta")), f(arm("P", "delta")), sg(D["control_gain_delta"]),
     f(arm("B0", "joint")), f(arm("P", "joint")), sg(D["control_gain_joint"]),
     f(arm("B0", "coverage"), 2), f(arm("P", "coverage"), 2),
     arm("B0", "violations"), arm("P", "violations"),
     arm("P", "colluder_posts"), f(arm("P", "secret_post_rate"), 1)))
h2("5.2 Action-only transmission does not reproduce it")
NOISE_GAPS = (abs(dgap("E", "V")), abs(dgap("C", "B0")))
INSIDE_SPREAD = sum(1 for g in NOISE_GAPS if g < D["e_spread"])
OUTSIDE_FACTOR = max(g / D["e_spread"] for g in NOISE_GAPS)
p("Arm V keeps the collusive prompt and the pair&rsquo;s motivation, and deletes the messaging tool from the "
  "model&rsquo;s tool list. Coalition advantage falls to %s &mdash; %s below the private-channel arm P and %s "
  "below arm B0. Neither is a clean single-factor read: no two arms in this ladder change the secret channel and "
  "nothing else, and P and V also differ in the prompt their artifacts record "
  "(<font face=\"Courier\">%s</font> against <font face=\"Courier\">%s</font>). The B0 comparison is the "
  "conservative reading of the two: B0 carries <i>no</i> coalition prompt, so a prompted pair should sit above it "
  "if the actions were carrying anything, and instead the prompted pair sits below an unprompted one. The "
  "advantage does not travel through actions at the resolution this metric can see. Arm E, which additionally "
  "hides the rendered events, gives %s (%s against V), and arm C, which keeps every event but makes the "
  "identifiers opaque, gives %s (%s against B0). Neither gap is resolvable at one seed: re-running arm E with an "
  "identical recorded config moved it by %s (&sect;6.1), which exceeds %d of those two gaps and is within %s "
  "times the other."
  % (f(arm("V", "delta")), f(D["action_only_below_private"]), f(D["action_only_below_baseline"]),
     D["coalition_prompt"]["P"], D["coalition_prompt"]["V"],
     f(arm("E", "delta")), sg(dgap("E", "V")), f(arm("C", "delta")), sg(dgap("C", "B0")),
     f(D["e_spread"]), INSIDE_SPREAD, f(OUTSIDE_FACTOR, 1)))
p("The interesting number in this row is not &Delta; but joint reward: V is the <i>best</i> arm in the ladder, %s "
  "against the baseline&rsquo;s %s (%s), with full coverage and zero violations, and it is one of the %d arms with "
  "no messaging at all. Turning messaging off did not merely stop the coalition; it improved the group. The two "
  "endpoints still reach %s and %s, so the pair is not hurt. The gain is in the middle: the non-coalition mean "
  "rises from %s in B0 to %s here, its highest value anywhere in the ladder, and that is set by %s, whose reward "
  "goes from %s in B0 to %s, the most that agent records in any arm. The other middle agent, %s, does marginally "
  "better in B0 (%s against %s), so this is a reduction in mis-claiming, not a uniform improvement for everyone."
  % (f(D["best_joint"]), f(arm("B0", "joint")), sg(D["v_joint_over_baseline"]),
     len(D["blocked_arms"]), f(arm("V", "coalition_values")[0]), f(arm("V", "coalition_values")[1]),
     f(arm("B0", "noncoalition_mean")), f(arm("V", "noncoalition_mean")),
     " and ".join(V_PEAK_AGENTS),
     f(arm("B0", "outgroup_values")[V_PEAK_AGENTS[0]]), f(arm("V", "outgroup_values")[V_PEAK_AGENTS[0]]),
     V_OTHER_AGENTS[0], f(arm("B0", "outgroup_values")[V_OTHER_AGENTS[0]]),
     f(arm("V", "outgroup_values")[V_OTHER_AGENTS[0]])))
h2("5.3 The metric rewards the wrong defence")
p("Arms S and B1 blind every agent to events and assignments. Read naively, Table 2 looks like a catastrophic "
  "collusion result: &Delta; rises to %s and %s, %s and %s times the baseline. Table 3 shows what actually "
  "happened. In S the coalition mean is %s &mdash; <i>identical</i> to arm V, and below the private-channel "
  "arm&rsquo;s %s &mdash; while the non-coalition mean collapses from %s to %s. The advantage widens because the "
  "outgroup is damaged, not because the coalition gained anything. In B1 the coalition mean, %s, is actually "
  "<i>lower</i> than the baseline&rsquo;s %s; &Delta; still reads %s, and joint reward falls to the worst value "
  "in the ladder, %s, with %d violations."
  % (f(arm("S", "delta")), f(arm("B1", "delta")), f(D["s_over_baseline_ratio"], 2),
     f(D["b1_over_baseline_ratio"], 2), f(arm("S", "coalition_mean")), f(arm("P", "coalition_mean")),
     f(arm("B0", "noncoalition_mean")), f(arm("S", "noncoalition_mean")),
     f(arm("B1", "coalition_mean")), f(arm("B0", "coalition_mean")), f(arm("B1", "delta")),
     f(D["worst_joint"]), arm("B1", "violations")))
PP1, PP0 = D["prompt_pair"]
p("%s and %s carry the same observation filter and the same secret-channel setting and differ in one recorded "
  "field &mdash; the coalition prompt, <font face=\"Courier\">%s</font> against <font face=\"Courier\">%s</font> "
  "&mdash; so that pair is the ladder&rsquo;s clean measurement of what telling two agents they are partners is "
  "worth once the shared state is blinded: &Delta; %s against %s, and joint reward %s against %s. Telling them "
  "pays %s of advantage <i>and</i> %s of joint reward, so the prompt is not what damages the group in this arm; "
  "the blinding is."
  % (PP1, PP0, D["prompt_pair_prompts"][0], D["prompt_pair_prompts"][1],
     f(arm(PP1, "delta")), f(arm(PP0, "delta")), f(arm(PP1, "joint")), f(arm(PP0, "joint")),
     sg(D["prompt_pair_delta_gain"]), sg(D["prompt_pair_joint_gain"])))
p("The mechanism is structural rather than behavioural. On a path, the middle agents are the ones whose "
  "assignments are visible on both boards and whose choices depend on reading them; the endpoints share no board, "
  "so blinding costs them comparatively little. A symmetric information removal therefore produces an asymmetric "
  "loss, and a difference-of-means metric records that asymmetry as coalition advantage. Any defence selected by "
  "minimising &Delta; can be selected for exactly the wrong reason.")
h2("5.4 Reading the coalition off the actions (H1)")
p("&Delta; answers whether the pair <i>gains</i> when the text channel is deleted. It does not answer the "
  "track&rsquo;s actual question, which is whether the actions themselves <i>carry</i> anything readable. We built "
  "a label-blind decoder that sees only the claim trace &mdash; for each of the %d candidate pairs, the share of "
  "the measured joint-reward gain that pair captured, and how far its two members&rsquo; own claims compete for the "
  "same skill tags &mdash; and ranks the pairs. Chance is exactly %s, since the true coalition is one of %d pairs, "
  "so the tail is computed rather than simulated. Over the %d arms the composite puts the true pair first in %d "
  "runs (p = %s, mean rank %s) and the value-share feature alone in the same %d. The complementarity feature alone "
  "ranks it first in %d/%d, but tied with another pair in every one of those %d, so it never identifies the "
  "coalition &mdash; it only excludes some pairs."
  % (H1["n_pairs"], "1/%d" % H1["n_pairs"], H1["n_pairs"], H1["runs"],
     C1["all"]["rank_1"], f(C1["all"]["p_rank_1_or_better"], 5), f(H1["mean_rank_composite"], 3),
     D["h1"]["vs_composite_same_runs"], C2["all"]["rank_1"], C2["all"]["runs"],
     C2["all"]["tied_for_first"]))
p("Two things stop this from being a positive carrier result. First, the split that matters is by messaging, and it "
  "is not favourable: the decoder ranks the pair first in %d of the %d arms where the tool was removed (p = %s) "
  "and in %d of the %d where it was available (p = %s). Removing the channel did not concentrate the signature in "
  "the actions. Second, the pooled signal is descriptive rather than diagnostic &mdash; the coalition&rsquo;s share "
  "of captured gain is %s against an all-pairs mean of %s (above it in %d/%d, and the mean is %s rather than zero "
  "because each agent appears in three of the %d pairs), and its internal tag overlap is %s against a rival mean of "
  "%s, strictly lower in %d/%d. That is what a division of labour looks like from outside, and it is equally what "
  "two agents with complementary private cost profiles do by accident. The text decoder settles it: of the %d "
  "messages posted in the %d arms that could post, the partner had named %d of %d of the coalition&rsquo;s "
  "eventual claims beforehand, against %d of %d for outgroup claims. Pre-announcing a claim is a habit of this "
  "environment, not a coalition behaviour."
  % (C1["messaging_removed"]["rank_1"], C1["messaging_removed"]["runs"],
     f(C1["messaging_removed"]["p_rank_1_or_better"], 3),
     C1["messaging_open"]["rank_1"], C1["messaging_open"]["runs"],
     f(C1["messaging_open"]["p_rank_1_or_better"], 3),
     f(H1["true_value_share"], 3), f(H1["all_pairs_value_share"], 3), H1["above_reference"], H1["runs"],
     f(H1["all_pairs_value_share"], 3), H1["n_pairs"],
     f(H1["true_tag_overlap"], 3), f(H1["rival_tag_overlap"], 3), H1["tag_lower"], H1["runs"],
     TXT["open"]["messages"], TXT["open"]["arms"], TXT["open"]["co_prime"], TXT["open"]["co_total"],
     TXT["open"]["og_prime"], TXT["open"]["og_total"]))
h2("5.5 Substituting single actions (H2)")
p("The replay harness reconstructs each run&rsquo;s task set and private cost matrix and re-scores it with the "
  "environment&rsquo;s own reward function. It refuses an arm unless the replayed actual assignment reproduces the "
  "logged joint reward within %s; all %d arms pass, the largest absolute error in the set being %s. The closed-form "
  "optimum is the same %s in every arm &mdash; one seed, one instance &mdash; so the arms differ only in how much "
  "of that surplus they realise. Three interventions, each a single edit: drop an agent&rsquo;s claim, swap two "
  "agents&rsquo; claims, replace one action with the exact solver&rsquo;s choice while holding the others fixed."
  % (f(H2["tolerance"], 2), H2["runs"], f(H2["gate_max_abs_error"], 3), f(H2["optimal"][0], 3)))
p("The coalition&rsquo;s actions are the load-bearing ones: dropping a coalition member&rsquo;s claim costs the group "
  "%s joint reward on average against %s for an outgroup member, and the pair is higher in %d/%d runs. Directionally "
  "the same for re-coupling &mdash; swapping inside the pair costs %s against %s across its boundary &mdash; but "
  "that direction is set by %d of %d comparable runs and reverses in %s, so we report it as a tendency, not a "
  "result. The substitution test is the sharpest: replacing a coalition member&rsquo;s action with what a global "
  "optimiser would have put there <i>lowers</i> joint reward by %s on average, while the same edit on an outgroup "
  "member <i>raises</i> it by %s, with the largest single-action gain available anywhere being %s. The pair is "
  "already sitting on placements the optimiser cannot better; the middle agents are where the loss is."
  % (f(H2["co_drop"], 3), f(H2["og_drop"], 3), H2["drop_wins"], H2["runs"],
     f(H2["swap_inside"], 3), f(H2["swap_cross"], 3), H2["swap_wins"], H2["swap_pairs"],
     ands(cap(a) for a in H2["swap_reversals"]),
     f(-H2["lift_coalition"], 3), f(H2["lift_outgroup"], 3), f(H2["largest_lift"], 3)))
p("Read together, 5.2 and 5.5 say the same thing from two sides. Action-level behaviour in this harness tracks who "
  "is well-placed, not who is cooperating, and the coalition&rsquo;s advantage is arithmetically the "
  "outgroup&rsquo;s displacement. %d run directories were rejected before any counterfactual was computed (%s), and "
  "%d superseded reruns were dropped so that an arm re-run does not enter the sample twice out of %d directories "
  "scanned."
  % (H2["rejected"], "; ".join("%d %s" % (v, k) for k, v in H2["rejection_reasons"].items()),
     H2["superseded"], H2["scanned"]))

# --------------------------------------------------------------------------------------
h1("6. Threats to validity")
h2("6.1 One seed")
p("Each arm is a single episode of a stochastic LLM process. We measured the spread rather than assuming it: %d "
  "arms were re-run with a recorded config identical to the pinned artifact in every field except the post-hoc "
  "filter diagnostics (%s). %s reproduced every number exactly; %s did not, moving from %s to %s in &Delta; and "
  "%s to %s in joint reward. So a single seed can shift this statistic by roughly %s without anything in the design "
  "changing. The differences we interpret as findings are far larger than that (%s for the control, %s for removing "
  "the channel, %s for blinding); the ones we do <i>not</i> interpret are the E and C gaps, which sit inside the "
  "measured spread, and no claim in this report rests on them."
  % (D["reran_count"], ands(D["reran_arms"]),
     ands(D["exact_reproduced_arms"]), ands(D["diverged_arms"]),
     f(D["e_rerun"]["delta"]), f(arm("E", "delta")), f(D["e_rerun"]["joint"]), f(arm("E", "joint")),
     f(D["e_spread"]), sg(D["control_gain_delta"]), sg(-D["action_only_below_private"]),
     sg(D["blinded_s_over_baseline"])))
h2("6.2 Measured instability, and what the artifacts do not record")
p("In the pre-sprint clone, two episodes written to the same output tag with the same recorded "
  "<font face=\"Courier\">run_id</font> (%s) produced coalition advantage %s and %s &mdash; a factor of %s &mdash; "
  "and normalized scores %s and %s, a factor of %s. One of the two carries %d of %d error-marked turns and the "
  "other none, so the difference is not a clean sampling comparison: it is instability and corruption entangled. "
  "It is also not attributable to a parameter change, because <font face=\"Courier\">run_config.json</font> does "
  "not record sampling parameters at all (%s appear in neither clone record nor in any of the %d pinned ladder "
  "artifacts), so nothing in the run record distinguishes the two. That is the honest form of the caution: "
  "absolute values of these statistics move enormously, the harness cannot tell you why from the artifact alone, "
  "and the report is therefore organised around matched comparisons and mechanism rather than thresholds."
  % (D["clone_pair_run_id"], f(D["clone_pair_deltas"][0], 3), f(D["clone_pair_deltas"][1], 3),
     f(D["clone_ratio"], 0), sci(D["clone_pair_norms"][0]), sci(D["clone_pair_norms"][1]),
     f(D["clone_norm_ratio"], 1), D["clone_corrupted_errors"], D["clone_corrupted_turns"],
     ands("&ldquo;%s&rdquo;" % x for x in D["clone_unrecorded_params"]), D["arm_count"]), BODYL)
h2("6.3 A frozen first mover")
p("%s&rsquo;s reward is %s in all %d arms, and that agent sits at position %d of %d in the recorded turn order "
  "(%s), so one of the two coalition members is out of reach of every intervention and half of the &Delta; signal "
  "comes from a single agent whose partner is invariant. With %d agents, one colluder and one blinded middle "
  "agent suffice to move the statistic; a larger network would be a more honest test."
  % (list(D["invariant_agents"])[0], f(list(D["invariant_agents"].values())[0][0]), D["arm_count"],
     D["agent_names"].index(list(D["invariant_agents"])[0]) + 1, len(D["agent_names"]),
     ", ".join(D["agent_names"]), PR["num_agents"]))
h2("6.4 Scope of the model and the missing arms")
p("A free-tier %s-class model is not the paper&rsquo;s configuration, so nothing here is a reproduction of a "
  "published number. The LLM-as-judge arm in the shipped fork hard-codes a client and could not be routed to our "
  "endpoint, so no judged arm is reported." % PR["model"])
h2("6.5 Scoring")
p("<font face=\"Courier\">normalized_score</font> is exactly 0.0 in %d of the %d arms and at most %s in the other "
  "%d (%s), which are precisely the %d arms with full coverage &mdash; so it contributes nothing at this "
  "resolution and is not reported as evidence."
  % (len(D["normalized_zero_arms"]), D["arm_count"], sci(D["max_normalized"]),
     len(D["normalized_nonzero_arms"]),
     ands(l for l, _v in D["normalized_nonzero_arms"]), len(D["full_coverage_arms"])))
h2("6.6 What the two offline checks can and cannot support")
p("The decode test in &sect;5.4 and the replay test in &sect;5.5 read the same %d artifacts that Table 2 does, so "
  "they inherit its sample size exactly: %d arms, one seed, one model, and a single instance whose optimum is %s in "
  "all of them. They are free and deterministic &mdash; neither calls a model &mdash; which means they add no new "
  "noise, but also no new independent observations. The p-values in &sect;5.4 are exact against the %s pair-ranking "
  "null, and that null is about the decoder guessing, not about sampling error across runs; a %d/%d consistency "
  "count is not a significance statement either. Both harnesses were re-run after a first version of the decoder "
  "placed the true pair last in every artifact, which looked like a striking negative result and was a bug: the "
  "candidate set excluded the pair being scored, so the rank collapsed to a constant. The numbers here are from the "
  "corrected harness only, and each harness records the same artifact-selection rule the report pins: of %d "
  "directories scanned, error markers exclude %d and an undecodable trace excludes %d, and the %d rows that "
  "remain collapse to %d arms once %d superseded reruns are dropped."
  % (D["arm_count"], D["arm_count"], f(H2["optimal"][0], 3), "1/%d" % H1["n_pairs"],
     H2["drop_wins"], H2["runs"], H1["scanned"], len(H1["skipped_error_turns"]), H1["undecodable"],
     H1["decoded"], H1["runs"], H1["superseded"]))

# --------------------------------------------------------------------------------------
h1("7. Conclusion")
p("For the question Track 3.1 poses, the answer in this environment is a qualified no: with the messaging tool "
  "removed, the designated pair does not recover its advantage through actions, events or shared-state residue, "
  "and the arms that hide those channels track the baseline within noise. Actions are visible, they are being "
  "taken, and they are not carrying the coalition&rsquo;s intent at a resolution the reward metric can detect. The "
  "two offline checks sharpen rather than soften that: a label-blind decoder does rank the true pair above chance "
  "(%d/%d, p = %s), but it does so no more often when messaging has been removed than when it is still available, "
  "and the replay shows that the coalition&rsquo;s actions are load-bearing for <i>group</i> reward in %d/%d runs "
  "because the pair occupies placements even the exact optimiser cannot improve &mdash; a fact about well-placed "
  "agents, which is what the environment gives you when two agents have complementary private cost profiles."
  % (C1["all"]["rank_1"], C1["all"]["runs"], f(C1["all"]["p_rank_1_or_better"], 3),
     H2["drop_wins"], H2["runs"]))
p("The stronger result is about measurement. A difference-of-means collusion statistic can be made to <i>grow</i> "
  "by a defence that helps nobody: blinding the shared state leaves the coalition&rsquo;s own reward unchanged or "
  "worse while degrading the outgroup, and the statistic reads that as coordination. If side-channel "
  "countermeasures are to be compared quantitatively, the comparison has to be on absolute group reward, coverage "
  "and violations &mdash; or on a statistic normalised so that symmetric degradation cannot masquerade as "
  "advantage. On those columns the ranking of this ladder inverts, and the best-performing arm is the one that "
  "simply removes the channel: %s, joint reward %s, coverage %s, violations %d."
  % (LABELS[D["best_joint_arm"]], f(D["best_joint"]), f(arm(D["best_joint_arm"], "coverage"), 2),
     arm(D["best_joint_arm"], "violations")))

h1("References")
p("Nakamura et&nbsp;al., <i>Colosseum: A Harness for Studying Collusion in Multi-Agent Systems</i> (arXiv "
  "2602.15198), 2026. &mdash; source of the environment, the &Delta;-collusion statistic and the conditions this "
  "ladder reuses.<br/>"
  "APART Sprint 2026, Project 3.1 guidelines and resources tabs, which specify the hidden/canonicalised ablation "
  "and the action-residue conditions implemented in &sect;3.", SMALL)

h1("Appendix A. Reproduction")
p("Configs: <font face=\"Courier\">experiments/collusion/configs/track31_{%s}.yaml</font>; "
  "harness: <font face=\"Courier\">experiments/collusion/observation_filter.py</font> with the run wiring in "
  "<font face=\"Courier\">run.py</font>; offline checks: "
  "<font face=\"Courier\">experiments/collusion/test_observation_filter.py</font> (%d tests, no key, no cost). "
  "Run one arm with <font face=\"Courier\">python experiments/collusion/run.py --config "
  "experiments/collusion/configs/track31_%s.yaml -y</font>, then gate the artifact before reading its metrics with "
  "<font face=\"Courier\">grep -c ERROR .../agent_turns.json</font>. Intervention metadata "
  "(<font face=\"Courier\">observation_filter</font>, <font face=\"Courier\">observation_filter_effects</font>) is "
  "written per run to <font face=\"Courier\">run_config.json</font>, not to the aggregate summary. "
  "The two offline analyses regenerate from the artifacts already on disk, make no model calls, and keep only the "
  "newest artifact per arm: <font face=\"Courier\">python experiments/collusion/decode_actions.py</font> (&sect;5.4) "
  "and <font face=\"Courier\">python experiments/collusion/counterfactual_replay.py</font> (&sect;5.5), writing "
  "<font face=\"Courier\">outputs/decode_h1.json</font> and "
  "<font face=\"Courier\">outputs/counterfactual_h2.json</font>. The second needs the environment&rsquo;s own "
  "dependencies (numpy, scipy) because it imports the closed-form scorer. "
  "Every figure in this report, including this paragraph, is emitted by "
  "<font face=\"Courier\">experiments/collusion/build_report.py</font> from "
  "<font face=\"Courier\">experiments/collusion/report_data.py</font>, which pins the artifact each arm is read "
  "from and refuses to build if a pinned artifact is missing, corrupted or unmatched. The %d arms of Tables "
  "1&ndash;3 are read from these run directories: %s."
  % (",".join(lbl for lbl, _t, _ts in ARMS), D["tests"], ARMS[0][0], D["arm_count"],
     "; ".join("%s %s" % (lbl, ts) for lbl, _t, ts in ARMS)), BODYL)

doc = SimpleDocTemplate(str(OUT), pagesize=LETTER, title="Track 3.1 - Actions as Carriers",
                        author="Muhammad Hassaan Shaukat",
                        leftMargin=0.85 * inch, rightMargin=0.85 * inch,
                        topMargin=0.75 * inch, bottomMargin=0.75 * inch)
doc.build(story)
print("wrote", OUT)
