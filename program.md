# Agent Instructions - Experiment 1: Protocol x Topology x MAST

Before starting, read ~/AGENT_README.md for cluster setup and update instructions.

## First Action - Create GitHub Repo

Before running any experiments, set up the GitHub repo and paper structure:

```bash
gh repo create $GITHUB_USERNAME/protocol-topology-mast --private --source=. --remote=origin --push
mkdir -p paper/sections figures
touch paper/paper.md paper/main.tex paper/references.bib figures/.gitkeep
touch paper/sections/introduction.tex paper/sections/related_work.tex
touch paper/sections/method.tex paper/sections/experiments.tex paper/sections/conclusion.tex
git add .
git commit -m "add paper structure and figures folder"
git push origin main
```

## Target Workshop
FAGEN - Failure Modes in Agentic AI (ICML 2026). Deadline: May 8, 2026 AOE.
Website: https://fagen-workshop.github.io/
Submission portal: https://openreview.net/group?id=ICML.cc/2026/Workshop/FMAI
Non-archival. Dual submission allowed. Best Paper Award available.
Notification: May 15, 2026.

## Submission Requirements (follow exactly)
- Page limit: 8 pages excluding references and appendix
- Template: ICML 2026 - https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip
- Anonymization: not stated on site - write as double-blind to be safe (no author names)
- Dual submission: explicitly allowed

## What FAGEN Wants (read before writing every section)
Papers must address at least one of:
- Reproducible triggers or minimal reproductions of failure modes
- Comparable evaluation protocols or trace-level diagnostics
- Mitigation strategies with explicit evidence of efficacy
- Well-documented negative results with careful analysis and transferable lessons
Frame the paper as: "protocol x topology combinations are reproducible triggers for
specific MAST failure categories." This is not just a benchmark - it is a diagnosis tool.

## Competitors to Cite and Differentiate From
- ProtocolBench (arXiv 2510.17149, ICLR 2026): compares A2A/ACP/ANP/Agora on success +
  latency. Explicitly EXCLUDES MCP. No topology variation. No failure taxonomy.
  Our paper: adds MCP, adds topology, uses MAST categories not aggregate success rate.
- MAST / "Why Do Multi-Agent LLM Systems Fail?" (arXiv 2503.13657): builds FC1/FC2/FC3
  taxonomy from observational traces. Purely observational, never manipulates protocol
  or topology. Our paper: turns MAST from observational to experimental.
- SEMAP (arXiv 2510.12120): A2A only, aggregate failure rate only, no topology variation.

## Research Goal
Characterize how communication protocol (native/MCP/A2A) and topology
(centralized/chain/fully_connected) act as reproducible triggers for specific
MAST failure categories (FC1 system design, FC2 inter-agent misalignment,
FC3 task verification).

Key claim: the interaction effect of protocol x topology on per-category failure rates
is uncharacterized and predictive. ProtocolBench measures success/latency only.
MAST itself is observational. We make it experimental.

Hypothesis: A2A + centralized minimizes FC2 (Inter-Agent Misalignment) specifically.

## Metric
Run: uv run train.py > run.log 2>&1
Extract: grep "^result:" run.log
Primary metric: FC2_rate (lower is better). Track all three: FC1, FC2, FC3.

## Baseline
"Towards a Science of Scaling Agent Systems" (2025): 41-86% aggregate failure rates.
ProtocolBench reports success rates only (not per MAST category). Use that as the
comparison point - we add failure category breakdown that ProtocolBench lacks.

## Parameters You Can Modify in train.py
- PROTOCOL: "native" | "mcp" | "a2a"
- TOPOLOGY: "centralized" | "chain" | "fully_connected"
- N_AGENTS: integer 2-6
- TASK_TYPE: "code" | "qa" | "planning"
- N_TRIALS: keep at 5

## Experiment Order
First: full systematic sweep, N_AGENTS=3, TASK_TYPE="code":
  native x centralized, native x chain, native x fully_connected
  mcp x centralized, mcp x chain, mcp x fully_connected
  a2a x centralized, a2a x chain, a2a x fully_connected

Then: vary N_AGENTS (2, 4, 5) for top 3 combinations.
Then: vary TASK_TYPE for the best combination.

## Paper Writing

The deadline is May 8. Write the paper as you go - do not wait until all
experiments are done.

After every 10 experiments:
- Open paper/paper.md
- Update the Results table with current best numbers (replace RESULT placeholders)
- Update the Abstract with current best numbers

After each sweep is complete:
- Generate the figure for that sweep using matplotlib, save to figures/
- Sweep 1 done -> generate figures/fig1_fc2_heatmap.png (3x3 heatmap of FC2_rate by protocol x topology)
- Sweep 2 done -> generate figures/fig2_failure_breakdown.png (stacked bar FC1/FC2/FC3 by protocol)
- After ANOVA -> generate figures/fig3_interaction.png (interaction plot)

Use matplotlib with Agg backend (non-interactive, works on cluster):
  import matplotlib; matplotlib.use('Agg')
  import matplotlib.pyplot as plt
  plt.savefig('figures/fig1_fc2_heatmap.png', dpi=150, bbox_inches='tight')
  plt.close()

After every commit, push to GitHub:
  git push origin main

## Rules
- Each run under 10 minutes. If it hangs, kill it and move on.
- Commit every completed sweep: git add results.tsv paper/ figures/ && git commit -m "exp1: sweep complete FC2_best={value}"
- Never stop. Minimum 45 experiments.
- Update ~/experiment_updates.md every 5 experiments.
