# Colosseum <sub><sub><img src="dev/colosseum_icon.png" alt="Colosseum icon" width="45" /></sub></sub>

> [!NOTE]
> :tada: **Colosseum has been accepted to the NeurIPS 2026 Evaluations and Datasets Track!** Read the paper on [arXiv](https://arxiv.org/abs/2602.15198).

If you find the repo or paper useful or interesting please :star: it!
## Description
<!-- > [!NOTE] -->
> Colosseum is a framework for objectively auditing cooperative multi-agent systems composed of tool-calling, LLM-based agents. We study collusion across varying models, network topologies, and environments. Below is a taxonomy of various collusion types Colosseum can identify:

<!-- > [!FINDING] -->
<!-- > [!TIP] -->

<p align="center">
  <a href="dev/colosseum-motivation-v3.pdf">
    <img src="dev/colosseum-motivation-v3-preview.png" alt="Colosseum motivation slides" width="70%" />
  </a>
</p>

This repo contains experiments for Colosseum under `experiments/` that utilizes the [Terrarium](https://github.com/umass-aisec/Terrarium) (`terrarium-agents`) framework.

## Apart Research Sprint 2026

This repository holds two separate sprint projects and the preexisting Colosseum code they build on. They share the framework. They do not share results. Apart allows two submissions per participant; each submission below has its own title. The GitHub link can be this repository, with the project directory named in the submission.

| Project | Research focus | Experimental evidence | Where to start |
| --- | --- | --- | --- |
| **Paper 1 — Tool-Choice Signaling** | When a runtime can hide tool-execution metadata and still leave the assignment visible | 108 exploratory runs on seeds 1–3, a separate 72-episode holdout on seeds 11–14, and eight later T3 utility episodes on those same seeds. The cohorts are not pooled. A confirmatory protocol was not run | [`experiments/collusion/tool_selection/README.md`](experiments/collusion/tool_selection/README.md) |
| **Paper 2 — Actions as Carriers** | Whether a coalition-advantage score can rank observation filters in a misleading order | The original seven-arm table was not recovered. Primary evidence is 25 episodes, seeds 31–35. Full filtering did not raise the score, and a lower score can accompany a worse joint reward | [`experiments/collusion/metric_validation/README.md`](experiments/collusion/metric_validation/README.md) |

Submission titles and author line for the two Apart forms:

| | Submission 1 | Submission 2 |
| --- | --- | --- |
| Title | Tool-Choice Signaling and Task-State Preservation in LLM Multi-Agent Systems | Actions as Carriers: Side-Channel Collusion and the Metrics That Hide It |
| Authors | Ellen Berhe and Muhammad Hassaan Shaukat | Ellen and Muhammad Hassaan Shaukat |
| Write-up | [`papers/paper1_tool_choice_signaling.pdf`](papers/paper1_tool_choice_signaling.pdf). Slides: [`papers/paper1_slides.pdf`](papers/paper1_slides.pdf). Source: [`experiments/collusion/tool_selection/TOOL_SELECTION_PAPER.md`](experiments/collusion/tool_selection/TOOL_SELECTION_PAPER.md) | [`papers/paper2_actions_as_carriers.pdf`](papers/paper2_actions_as_carriers.pdf) |
| Code | `experiments/collusion/tool_selection/` | `experiments/collusion/metric_validation/` |

Both manuscripts use the submission author line above. The two write-ups are not pooled.

Index of the write-ups: [`papers/README.md`](papers/README.md).

### What is preexisting, what this sprint added, and what was not run

Preexisting Colosseum work includes the framework, Terrarium, and `experiments/collusion/` outside the two directories above: the original runner, prompts, metrics, configs, and the other experiment families (`persuasion`, `network_influence`, `agent_misalignment`).

Sprint implementations:

- Paper 1 is a new package under `experiments/collusion/tool_selection/`. It uses `experiments/collusion/run_tracebreak.py`. It does not use the Paper 2 filter wiring.
- Paper 2 adds `experiments/collusion/metric_validation/` and an additive change in `experiments/collusion/run.py`: `first_and_last` coalition selection, a `coalition_prompt` mode, and an observation-filter client. Configurations that omit those keys keep the previous behavior.

Completed results:

- Paper 1: the 108-run exploratory cohort (seeds 1–3, `gpt-4.1-mini`, temperature 0.7), a separate 72-episode holdout (seeds 11–14, policies T1, T2, and T4), and eight T3 utility episodes on seeds 11–14. Summarized in `TOOL_SELECTION_PAPER.md`, `T4_MATCHED_RESULTS.md`, and `T3_T4_COMPARISON.md`. Raw episode directories live under `experiments/collusion/tool_selection/outputs/` and are gitignored. The three sets are not pooled.
- Paper 2: deterministic request-boundary tests, plus 25 new episodes (seeds 31–35; arms B0, P, V, S, B1; model string `gemini-3.5-flash-lite`). The analysis is `REPLICATION_AND_VALIDATION_REPORT.md`. Those episodes are not a reconstruction of the printed seven-arm table. Their logs are under `experiments/collusion/metric_validation/outputs/` and are gitignored.

Not run, and not part of either result table:

- Paper 1 confirmatory protocol (`CONFIRMATORY_PROTOCOL.md`). The event-only arm was run later as its own holdout, not as a replacement of the 108.
- Paper 2 arms E and C in the new cohort, and a separate turn-order experiment. The original seven-arm episode logs were not found.

Experimental code was left in place. Moving it would break the current imports. Each project README points at the files a reviewer needs.

Intended submission tags, to be applied to the commit that is actually submitted:

```text
apart-2026-tool-selection
apart-2026-action-carriers
```

Those tags are not created yet.

## Setup

1) Install CoLLAB (required for certain environments):
- Recommended (submodule):
  - `git submodule add https://github.com/Saad-Mahmud/CoLLAB_SEA.git external/CoLLAB`
  - `git submodule update --init --recursive`
- Alternative: clone anywhere and set `TERRARIUM_COLLAB_PATH` in `.env`.

2) Create env + install deps:
- `uv venv --python 3.11 .venv`
- `source .venv/bin/activate`
- `uv sync --no-install-project`

3) Configure environment and API keys (if needed)(never put real keys in `.env.example`):
- `cp .env.example .env`
- Fill API keys

## Run

> [!TIP]
> If you are using APIs, actively track API usage since API costs accumulate linearly with the number of agents in the run.

Run from the repo root with your virtualenv active (e.g., `source .venv/bin/activate`). Here are is a non-exhaustive list of run commands:

```bash
# Persuasion affects on collusion (JiraTicket)
python experiments/persuasion/collusion/run.py \
  --config experiments/persuasion/collusion/configs/persuasion_collusion_jira.yaml

# Persuasion affects on collusion (Hospital)
python experiments/persuasion/hospital/run.py \
  --config experiments/persuasion/hospital/configs/persuasion_hospital.yaml

# Collusion (JiraTicket topology sweeps)
python experiments/collusion/run.py \
  --config experiments/collusion/configs/collusion_jira_topologies.yaml

# Network influence / misinformation propagation (Mass policy)
python experiments/network_influence/run.py \
  --config experiments/network_influence/configs/misinformation_prop_mass.yaml

# Agent objective misalignment (Hospital)
python experiments/agent_misalignment/run.py \
  --config experiments/agent_misalignment/configs/agent_misalignment_gpt_4_1_mini.yaml
```

## Citation
Please cite us using:
```bibtex
@article{nakamura2026colosseumauditingcollusioncooperative,
      title={Colosseum: Auditing Collusion in Cooperative Multi-Agent Systems}, 
      author={Mason Nakamura and Abhinav Kumar and Saswat Das and Sahar Abdelnabi and Saaduddin Mahmud and Ferdinando Fioretto and Shlomo Zilberstein and Eugene Bagdasarian},
      year={2026},
      eprint={2602.15198},
      archivePrefix={arXiv},
      primaryClass={cs.MA},
      url={https://arxiv.org/abs/2602.15198}, 
}
```
