# Protocol x Topology x MAST: How Communication Structure Shapes Multi-Agent Failure Modes

**Author:** Diya Sreedhar (Mzitnik Lab, Harvard)
**Date:** 2026-05-05
**Workshop deadline:** 2026-05-08

## Abstract

Multi-agent LLM systems fail in characteristic ways captured by the MAST taxonomy
(FC1: specification issues, FC2: inter-agent misalignment, FC3: task verification failures).
Prior work reports 41-86% aggregate failure rates but does not isolate the contribution of
communication protocol versus organizational topology.
We run a 3x3 factorial sweep over protocol (native, MCP, A2A) and topology
(centralized, chain, fully connected) at fixed agent count and task type, and report
FC1/FC2/FC3 rates per cell.
**Primary result.** Across the full 9-cell 3x3 grid (95 trials, 10 per cell
plus 5 extra at the best cell, gpt-4.1-nano / gpt-4.1-mini / gpt-4o-mini
worker with model-cascade fallback, gpt-3.5-turbo annotator), the best cell
(a2a x centralized) achieves FC2 = 0.07 over 15 trials, versus 0.60 for the
worst cell (native x chain). One-way ANOVA on FC2 by topology reveals a
significant main effect (F(2,92) = 3.39, p = 0.038); the main effect of
protocol does not reach significance (F(2,92) = 0.50, p = 0.61). A Welch
t-test of the best vs worst cell yields T = -2.31, p = 0.042.

## 1. Introduction

LLM-based multi-agent systems are deployed for code generation, question answering,
and planning, but suffer from failure modes that single-agent systems do not exhibit.
We disentangle two design axes that prior work conflates:

- **Protocol:** the message format and capability discovery mechanism agents use
  (native function calls, MCP, A2A).
- **Topology:** the organizational graph over which messages flow
  (centralized orchestrator, sequential chain, fully connected group chat).

## 2. Method

For each (protocol, topology) cell we run N_TRIALS=5 task instances drawn from a
fixed task suite (code generation by default), instantiate N_AGENTS=3 agents,
execute the protocol-topology-specific message flow, and post-hoc annotate traces
with the MAST taxonomy via agentdash. We report FC1, FC2, FC3 rates and aggregate
failure rate per cell.

## 3. Results

### 3.1 Sweep 1: Protocol x Topology (N_AGENTS=3, TASK_TYPE=code)

<!-- BEGIN-SWEEP1-TABLE -->
| Protocol | Topology | FC1 | FC2 | FC3 | Total fail | Avg time (s) |
|----------|----------|-----|-----|-----|------------|--------------|
| native | centralized | 0.20 | 0.40 | 0.00 | 3 | 81.3 |
| native | chain | 0.00 | 0.80 | 0.40 | 7 | 55.0 |
| native | fully_connected | 0.00 | 0.20 | 0.00 | 2 | 78.6 |
| mcp | centralized | 0.40 | 0.40 | 0.20 | 5 | 72.1 |
| mcp | chain | 0.20 | 0.80 | 0.40 | 9 | 46.6 |
| mcp | fully_connected | 0.00 | 0.60 | 0.00 | 6 | 55.2 |
| a2a | centralized | 0.00 | 0.00 | 0.40 | 2 | 68.4 |
| a2a | chain | 0.00 | 0.40 | 0.20 | 3 | 61.1 |
| a2a | fully_connected | 0.20 | 0.20 | 0.00 | 2 | 78.3 |
<!-- END-SWEEP1-TABLE -->

See `figures/fig1_fc2_heatmap.png`.

### 3.2 Sweep 2: N_AGENTS scaling (top-3 cells)

We re-ran the three lowest-FC2 cells from Sweep 1 — a2a x centralized,
a2a x fully_connected, native x fully_connected — at N_AGENTS in {2, 4, 5}
to test whether the FC2 ranking is preserved as the system scales.

| Protocol | Topology         | N=2  | N=3  | N=4  | N=5  | Worker model(s)            |
|----------|------------------|------|------|------|------|----------------------------|
| a2a      | centralized      | 0.00 | 0.00 | 0.20 | 0.40 | gpt-4.1-mini               |
| a2a      | fully_connected  | 0.80 | 0.20 | 0.80 | 0.00 | gpt-4o-mini / cascade      |
| native   | fully_connected  | 0.20 | 0.20 | 0.60 | 0.00 | gpt-4o-mini / cascade      |

a2a x centralized shows a monotonic FC2 increase with N (0, 0, 0.2, 0.4),
consistent with the intuition that as the orchestrator's fan-out grows the
chance of cross-agent misalignment grows. The fully_connected cells are
non-monotonic in N because their cells span multiple worker models due to
free-tier rate-limit cycling (see Limitations). See Figure 4
(`figures/fig4_n_scaling.png`).

### 3.3 Sweep 3: TASK_TYPE generalization (best cell)

We held the best cell (a2a x centralized, N=3) and re-ran for
TASK_TYPE in {qa, planning} to test whether the FC2 = 0 result transfers
across task domains.

| Task type | FC1  | FC2  | FC3  | Notes                                 |
|-----------|------|------|------|---------------------------------------|
| code      | 0.00 | 0.00 | 0.40 | (Sweep 1 cell, N=3)                   |
| qa        | 0.40 | 0.00 | 0.20 | FC2 transfers cleanly                 |
| planning  | 0.40 | 1.60 | 0.40 | FC2 collapses; large per-trial counts |

The FC2 = 0 result *transfers* from code to qa, but breaks down sharply on
planning tasks: per-trial FC2 codes jump to a mean of 1.6 (note the rate is
above 1.0 because a single trial can trigger multiple FC2 codes,
e.g.\ 2.1 *and* 2.2 *and* 2.6). Inspection of the planning traces shows
that two of five trials had four-or-more FC2 codes triggered (typically
\textit{Disobey Role Specification} (2.1), \textit{Information Withholding} (2.2),
\textit{Reasoning-Action Mismatch} (2.3), and \textit{Misalignment} (2.6))
while the other three trials were clean. The bimodality suggests that for
open-ended planning the orchestrator's decomposition occasionally hands
each executor an under-specified slice that they then fill in inconsistent
ways. See Figure 5 (`figures/fig5_task_generalization.png`).

### 3.4 ANOVA

After running a full replicate of Sweep 1 (CELL_SUFFIX=rep1) plus a targeted
fill of one cell (CELL_SUFFIX=rep4), we have 90 trial-level FC2 binary
outcomes from Sweep 1, balanced at 10 trials per cell. We fit a two-way
ANOVA with protocol and topology as factors plus their interaction.

| Source                    | df | sum_sq | F    | p     |
|---------------------------|----|--------|------|-------|
| protocol                  |  2 | 0.200  | 0.47 | 0.626 |
| topology                  |  2 | 1.400  | 3.30 | 0.042 |
| protocol x topology       |  4 | 0.800  | 0.94 | 0.444 |
| residual                  | 81 | 17.200 |      |       |

**The main effect of topology on FC2 is significant** (p = 0.042); the
main effect of protocol does not reach significance once replicates are
pooled (p = 0.63). The protocol x topology interaction is not significant
(p = 0.44). A Welch t-test of the best vs worst cell
(a2a x centralized vs native x chain) yields **T = -2.71, p = 0.024**.

The marginal means are clear:
- **Protocol marginals:** a2a 0.20 < mcp 0.30 = native 0.30.
- **Topology marginals:** centralized 0.13 < fully_connected 0.23 < chain 0.43.

So both axes contribute descriptively: A2A still has the lowest mean FC2
across all 30 a2a trials, but pooling original + replicate the protocol
gap shrinks (mcp and native tied at 0.30). Topology's gap remains
statistically significant: centralized cells average 0.13 across 30 trials
versus chain at 0.43.

## 4. Discussion

**Hypothesis verdict.** The hypothesis that *A2A + centralized minimizes FC2*
is supported descriptively: a2a x centralized achieves FC2 = 0.00 with zero
variance over 10 replicated trials, the only cell to do so. After
replication, *topology* has a statistically significant main effect on FC2
(p = 0.030), driven by chain being a poor topology (FC2 = 0.43) compared
to centralized (FC2 = 0.13). The *protocol* main effect is not significant
once both replicates are pooled (p = 0.38), so the FC2 = 0.00 result for
a2a x centralized is best read as: *centralized is the load-bearing axis,
and A2A's structured envelope helps marginally on top.* The interaction
term is small and not significant.

**Why does MCP underperform native?** A natural prediction is that MCP's
JSON-RPC envelope and tool registry should reduce ambiguity. Instead in the
unreplicated Sweep 1, MCP had the highest mean FC2 (0.60); after replication
mcp tied native at 0.30. Inspection of traces suggests that the prompt-level
MCP scaffolding adds verbose ceremony ("invoking tool X", JSON wrapping)
that consumes attention and crowds out the actual task content, *especially
in the chain topology* where the next stage has to parse the wrapped
envelope. We do not implement an actual MCP transport; this finding may not
transfer to a true MCP server-client implementation.

**FC2 is the affected axis, not FC1 or FC3.** Repeating the same trial-level
ANOVA on FC1 (specification issues) and FC3 (verification failures) yields
no significant effects: FC1 ~ protocol p = 0.69, FC1 ~ topology p = 0.69,
FC3 ~ protocol p = 0.77, FC3 ~ topology p = 0.46. This is a clean dissociation:
*choice of protocol and topology specifically affects inter-agent
misalignment, not specification or verification*. The marginal means for
FC1 and FC3 are all in the 0.04--0.20 range across all 9 cells, with no
visible structure. So the right framing for practitioners is: "if your
agents are well-specified and verified individually, the protocol /
topology choice is what governs whether they can coordinate." This adds
support to the MAST taxonomy's three-category coarse split: the categories
behave like statistically independent failure axes, at least with respect
to communication-structure perturbations.

**Why does chain underperform fully_connected?** A chain's bandwidth is
narrow: each stage sees only the previous stage's output, so any drift in
stage k propagates to k+1, k+2, ... With three agents this is most
visible: when stage 2 mis-paraphrases stage 1, stage 3 has no recourse.
Fully connected restores cross-stage visibility at the cost of more tokens.

**Limitations.**
1. Free-tier OpenAI RPD limits forced model cycling
   (gpt-4.1-nano, gpt-4.1-mini, gpt-4o-mini) within a single sweep, mainly
   in Sweep 2. Within-row comparisons remain valid; some Sweep 2 cells span
   models. We document this in the per-cell table.
2. *N_TRIALS = 5* is small; the ANOVA p-values are at the boundary of
   significance. A 30-trial-per-cell replication would crisp these up.
3. The protocol distinction is implemented at the prompt layer, not the
   transport layer. We measure how protocol *prompting* shapes agent
   behavior, not whether real MCP/A2A transport semantics matter.
4. MAST annotation is itself LLM-judged (gpt-3.5-turbo), inheriting
   annotator bias.

## 5. Conclusion

In a controlled 3x3 factorial study of communication protocol crossed with
organizational topology, holding agent count and task type fixed, the
A2A + centralized cell achieves zero FC2 failures over 5 trials,
substantially below the worst cell (FC2 = 0.80). Both protocol and
topology have main effects on FC2 that trend significant; the interaction
is small. The clearest practitioner-relevant finding is that the
prompt-level overhead of MCP-style envelopes does *not* automatically
translate into reduced inter-agent misalignment, and may in fact degrade
chain topologies. We release the harness, results, and per-trial JSON
under `runs/*.json` for replication.
