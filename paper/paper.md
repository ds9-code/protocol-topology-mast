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
**Primary result (live update):** the best protocol x topology cell (native x fully_connected) achieves FC2 = 0.20, versus 0.80 for the worst cell (4.00x reduction).
versus RESULT for the worst cell (RESULTx reduction).
Hypothesis under test: A2A + centralized minimizes FC2 specifically.

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
| mcp | centralized | RESULT | RESULT | RESULT | RESULT | RESULT |
| mcp | chain | RESULT | RESULT | RESULT | RESULT | RESULT |
| mcp | fully_connected | RESULT | RESULT | RESULT | RESULT | RESULT |
| a2a | centralized | RESULT | RESULT | RESULT | RESULT | RESULT |
| a2a | chain | RESULT | RESULT | RESULT | RESULT | RESULT |
| a2a | fully_connected | RESULT | RESULT | RESULT | RESULT | RESULT |
<!-- END-SWEEP1-TABLE -->

See `figures/fig1_fc2_heatmap.png`.

### 3.2 Sweep 2: N_AGENTS scaling (top-3 cells)

(pending)

### 3.3 Sweep 3: TASK_TYPE generalization (best cell)

(pending)

### 3.4 ANOVA

(pending)

## 4. Discussion

(pending)

## 5. Conclusion

(pending)
