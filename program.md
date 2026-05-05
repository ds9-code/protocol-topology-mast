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

## Research Goal
Measure how protocol (native/MCP/A2A) and topology (centralized/chain/fully_connected)
interact to produce different MAST failure mode distributions.

Hypothesis: A2A + centralized minimizes FC2 (Inter-Agent Misalignment) specifically.

## Metric
Run: uv run train.py > run.log 2>&1
Extract: grep "^result:" run.log
Primary metric: FC2_rate (lower is better). Track all three: FC1, FC2, FC3.

## Baseline
"Towards a Science of Scaling Agent Systems" (2025): 41-86% aggregate failure rates.

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
