# Protocol x Topology x MAST

How does the choice of inter-agent communication **protocol** (`native` vs MCP vs A2A)
crossed with the **topology** of agent communication (centralized vs chain vs fully
connected) shape multi-agent LLM failure modes, scored against the MAST taxonomy?

This is the experiment-1 repo for the FAGEN workshop submission (ICML 2026, deadline
2026-05-08). It builds on the [karpathy/autoresearch](https://github.com/karpathy/autoresearch)
harness — the agent program is in `program.md` and the trainable / runnable code is in
`train.py`.

## Headline results

- 9-cell 3x3 sweep, 110 trials at temperature 0.7: **topology has a significant main
  effect on FC2 (inter-agent misalignment)**, F(2,107) = 3.83, p = 0.025. Protocol
  does not (p = 0.38). Best cell is `a2a x centralized` (FC2 = 0.07 over 15 trials);
  worst is `native x chain` (FC2 = 0.53 over 15 trials).
- Replication-of-best-vs-worst Welch t-test: T = -2.62, p = 0.017.
- **Temperature ablation: 8 of 9 cells collapse to FC2 = 0 at temperature 0.0.** Most
  of the topology effect at T = 0.7 is sampling-variance amplification, not a structural
  coordination property.
- The single non-zero T = 0 cell is `mcp x centralized` (FC2 = 0.25 across 8 valid
  trials pooled over four independent re-runs), confirmed by inspection of traces:
  the orchestrator wraps its own integration step in MCP envelopes addressed back to
  itself, and executors mis-parse partial envelopes.
- FC1 (specification) and FC3 (verification) ANOVAs find no protocol or topology effect
  (all p > 0.4) — a clean dissociation: communication structure governs FC2 specifically.
- Best-cell FC2 transfers from CODE → QA but collapses on PLANNING (FC2 = 1.6),
  driven by under-specified subtask decompositions.
- `a2a x centralized` shows monotonic FC2 increase with N: 0.0 / 0.0 / 0.2 / 0.4 for
  N = 2, 3, 4, 5.

See `paper/paper.md` for the full draft and `figures/*.png` for the plots.

## Repository layout

- `train.py` — protocol/topology agent harness (no autogen dependency; calls OpenAI directly).
- `run_sweep.py` — multi-cell sweep runner. Reads TSV configs from stdin, runs
  `train.py` per cell, writes `results.tsv`, auto-commits and pushes after each cell.
- `prepare.py`, `pyproject.toml`, `uv.lock` — inherited from the autoresearch upstream.
- `analyze.py` — trial-level ANOVA, Welch t-test, FC1/FC3 marginals.
- `make_figures.py` — generates `figures/fig1..fig5.png`.
- `update_paper.py` — drops live numbers into `paper/paper.md` between
  `<!-- BEGIN-SWEEP1-TABLE -->` markers.
- `rebuild_results.py` — rebuilds `results.tsv` from `runs/*.json`.
- `program.md` — agent-level instructions (the user's contract with the agent).
- `paper/paper.md`, `paper/main.tex`, `paper/sections/*.tex`, `paper/references.bib`
  — the draft.
- `runs/<cell>.json` — per-trial annotated trace summary for every cell run.
- `results.tsv` — one row per cell completion.

## Reproducing

```
uv sync
uv run run_sweep.py < sweep1.tsv > sweep1.out 2>&1
uv run analyze.py
uv run make_figures.py
```

Free-tier OpenAI accounts will hit the 200 RPD limit on a single model partway
through. The harness has a model-cascade fallback (`gpt-4.1-mini` → `gpt-4o` →
`gpt-4.1` → `gpt-4o-mini` → `gpt-4.1-nano` → `gpt-3.5-turbo`); set
`WORKER_FALLBACKS` in `train.py` if you need to re-order.

## Notes

- The OpenAI annotator (`agentdash.annotator`) defaults to `o1-mini`; this repo
  overrides it to `gpt-3.5-turbo` because most accounts lack o1-mini access.
- All experimentation runs on a Harvard FASRC login node (the underlying compute
  is the OpenAI API, not local GPU), per the protocol in `~/AGENT_README.md`.
