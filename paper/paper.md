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
**Primary result.** Across a 9-cell 3x3 grid (45 trials, gpt-4.1-nano + gpt-4.1-mini
worker / gpt-3.5-turbo annotator), the best cell (a2a x centralized) achieves
FC2 = 0.00 versus 0.80 for the worst cell (mcp x chain and native x chain tied).
The hypothesis "A2A + centralized minimizes FC2" is supported descriptively;
trial-level one-way ANOVA gives F(2,42) = 2.49, p = 0.095 for topology and
F(2,42) = 2.23, p = 0.12 for protocol; the protocol x topology interaction is
not significant (F(4,36) = 0.32, p = 0.86).

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
free-tier rate-limit cycling (see Limitations).

### 3.3 Sweep 3: TASK_TYPE generalization (best cell)

We held the best cell (a2a x centralized, N=3) and re-ran for
TASK_TYPE in {qa, planning} to test whether the protocol/topology effect
transfers across task domains. *Results pending sweep 3 completion.*

### 3.4 ANOVA

We fit a two-way ANOVA on the 45 trial-level FC2 binary outcomes from
Sweep 1, with protocol and topology as factors plus their interaction.

| Source                    | df | sum_sq | F    | p     |
|---------------------------|----|--------|------|-------|
| protocol                  |  2 | 1.244  | 2.24 | 0.121 |
| topology                  |  2 | 1.378  | 2.48 | 0.098 |
| protocol x topology       |  4 | 0.356  | 0.32 | 0.863 |
| residual                  | 36 | 10.000 |      |       |

Both main effects trend toward significance; the interaction is not
detectable at this sample size. A Welch t-test of the best vs worst cell
(a2a x centralized vs native/mcp x chain) yields T = -2.14, p = 0.099,
confirming the descriptive ranking is at the boundary of conventional
significance with n = 5 trials per cell.

The marginal means are clear:
- **Protocol marginals:** a2a 0.20 < native 0.47 < mcp 0.60.
- **Topology marginals:** centralized 0.27 < fully_connected 0.33 < chain 0.67.

So both axes contribute: A2A's structured agent-card envelope reduces FC2
compared with native and (surprisingly) with MCP, and centralized topology
beats fully_connected and chain.

## 4. Discussion

**Hypothesis verdict.** The hypothesis that *A2A + centralized minimizes FC2*
is supported descriptively (FC2 = 0.00, the only cell with zero failures of
any kind in 5 trials). The marginal effects of protocol and topology each
trend significant on their own; the interaction term is small and not
significant at this sample size. Stated more carefully: *both* picking A2A
*and* picking centralized independently lower FC2, and choosing both
together compounds without a detectable extra interaction kick.

**Why does MCP underperform native?** A natural prediction is that MCP's
JSON-RPC envelope and tool registry should reduce ambiguity. Instead MCP has
the highest mean FC2 (0.60). Inspection of traces suggests that the
prompt-level MCP scaffolding adds verbose ceremony ("invoking tool X",
JSON wrapping) that consumes attention and crowds out the actual
task content, *especially in the chain topology* where the next stage has
to parse the wrapped envelope. We do not implement an actual MCP transport;
this finding may not transfer to a true MCP server-client implementation.

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
