"""
Experiment 1: How do protocol (native/MCP/A2A) and topology (centralized/chain/fully_connected)
interact to produce different MAST failure mode distributions?

Self-contained: no autogen dependency. Each agent is an OpenAI chat completion with a role
system message. Protocols differ in the system-prompt scaffolding (capability discovery,
message envelopes); topologies differ in the message routing graph.
"""

import os, time, json, sys, traceback

# PARAMETERS - read from env if present, otherwise defaults. The sweep runner sets these.
PROTOCOL  = os.environ.get("PROTOCOL",  "native")        # "native" | "mcp" | "a2a"
TOPOLOGY  = os.environ.get("TOPOLOGY",  "centralized")   # "centralized" | "chain" | "fully_connected"
N_AGENTS  = int(os.environ.get("N_AGENTS", "3"))         # 2-6
TASK_TYPE = os.environ.get("TASK_TYPE", "code")          # "code" | "qa" | "planning"
N_TRIALS  = int(os.environ.get("N_TRIALS", "5"))

WORKER_MODEL = os.environ.get("WORKER_MODEL", "gpt-4.1-mini")
ANNOT_MODEL  = os.environ.get("ANNOT_MODEL",  "gpt-3.5-turbo")
# Free-tier accounts hit RPD limits. We cascade through equivalent small models so the
# sweep keeps making progress instead of spending an entire cell crashing on 429s.
WORKER_FALLBACKS = [WORKER_MODEL, "gpt-4.1-mini", "gpt-4o", "gpt-4.1",
                    "gpt-4o-mini", "gpt-4.1-nano", "gpt-3.5-turbo"]
ANNOT_FALLBACKS  = [ANNOT_MODEL,  "gpt-3.5-turbo", "gpt-4.1-mini", "gpt-4o-mini"]
# de-duplicate while preserving order
def _uniq(seq):
    seen = set(); out = []
    for x in seq:
        if x not in seen: out.append(x); seen.add(x)
    return out
WORKER_FALLBACKS = _uniq(WORKER_FALLBACKS)
ANNOT_FALLBACKS  = _uniq(ANNOT_FALLBACKS)
_RPD_BANNED = set()  # models we know are exhausted within this run

TASKS = {
    "code": [
        "Write a Python function that finds all prime numbers up to N using the Sieve of Eratosthenes.",
        "Write a function that merges two sorted lists into one sorted list.",
        "Write a function that detects cycles in a linked list.",
    ],
    "qa": [
        "What are the main differences between supervised and unsupervised learning?",
        "Explain why gradient descent can get stuck in local minima.",
        "What is the vanishing gradient problem and how does batch normalization help?",
    ],
    "planning": [
        "Plan the steps to deploy a web application from development to production.",
        "Plan how to migrate a PostgreSQL database to a new server with zero downtime.",
        "Plan the steps to set up a CI/CD pipeline for a Python project.",
    ],
}

PROTOCOL_PREAMBLE = {
    "native": (
        "Communication uses native function calls inside one process; messages are plain text. "
        "There is no capability registry — assume the other agents are reachable directly."
    ),
    "mcp": (
        "Communication uses the Model Context Protocol (MCP). Each agent advertises tools via a "
        "tools/list registry; messages are JSON-RPC envelopes. Before sending substantive output, "
        "briefly acknowledge which tool/role you are invoking, then provide the content."
    ),
    "a2a": (
        "Communication uses the Agent-to-Agent (A2A) protocol. Each agent has an Agent Card "
        "(name, role, capabilities). Address peers by their card name, and prefix replies with "
        "[from <your-name> -> <recipient-name>]. Use the structured envelope so peers can route."
    ),
}

from openai import OpenAI
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def role_for(i, n):
    if i == 0: return "orchestrator"
    return f"executor_{i}"

def system_message(role, n_agents, protocol):
    others = [role_for(j, n_agents) for j in range(n_agents)]
    return (
        f"You are agent '{role}' in a {n_agents}-agent system. "
        f"Peers: {', '.join(others)}. "
        f"{PROTOCOL_PREAMBLE[protocol]} "
        f"Stay focused on the assigned task. Reply concisely (under 200 words). "
        f"If you are the orchestrator, decompose the task and delegate clearly. "
        f"If you are an executor, finish your part and clearly mark when you are done."
    )

def _call_with_fallback(messages, fallbacks, max_tokens, temperature=0.7):
    last_err = None
    for m in fallbacks:
        if m in _RPD_BANNED: continue
        try:
            resp = client.chat.completions.create(
                model=m, messages=messages, max_tokens=max_tokens,
                temperature=temperature, timeout=60,
            )
            return resp.choices[0].message.content.strip(), m
        except Exception as e:
            last_err = e
            es = str(e)
            if "RPD" in es or ("requests per day" in es) or ("rate_limit_exceeded" in es and "Limit 200" in es):
                _RPD_BANNED.add(m)
                print(f"!! RPD-banning {m}, trying next fallback", flush=True)
                continue
            if "429" in es:
                # Per-minute rate limit - the OpenAI client already retried; if still 429, try next model
                print(f"!! {m} still RPM-limited after retries, trying next", flush=True)
                continue
            raise
    raise last_err if last_err else RuntimeError("no models available")

def call_agent(role, history, protocol, n_agents, model=None, max_tokens=400):
    msgs = [{"role": "system", "content": system_message(role, n_agents, protocol)}] + history
    out, used = _call_with_fallback(msgs, WORKER_FALLBACKS, max_tokens=max_tokens)
    return out

def envelope(protocol, sender, recipient, body):
    if protocol == "a2a":
        return f"[from {sender} -> {recipient}]\n{body}"
    if protocol == "mcp":
        return f"<mcp:message from=\"{sender}\" to=\"{recipient}\">\n{body}\n</mcp:message>"
    return f"{sender} -> {recipient}: {body}"

def run_centralized(task, n_agents, protocol):
    """Orchestrator (agent 0) sends subtasks to each executor in parallel-style turns."""
    transcript = [f"TASK: {task}"]
    # Orchestrator decomposes
    history = [{"role": "user", "content": f"You received this task from the user: {task}\n"
                                            f"Please decompose it into one subtask per executor "
                                            f"({', '.join(role_for(i,n_agents) for i in range(1,n_agents))}). "
                                            f"List one short subtask per executor."}]
    plan = call_agent(role_for(0, n_agents), history, protocol, n_agents)
    transcript.append(envelope(protocol, role_for(0, n_agents), "all", plan))
    # Each executor responds to the plan
    for i in range(1, n_agents):
        ex = role_for(i, n_agents)
        ex_hist = [{"role": "user", "content":
            f"Original task: {task}\n"
            f"Plan from orchestrator:\n{plan}\n\n"
            f"You are {ex}. Carry out your part of the plan now and present your output."}]
        out = call_agent(ex, ex_hist, protocol, n_agents)
        transcript.append(envelope(protocol, ex, role_for(0, n_agents), out))
    # Orchestrator integrates
    integrate_hist = [{"role": "user", "content":
        f"Original task: {task}\n"
        f"Executor outputs:\n" + "\n\n".join(transcript[2:]) +
        f"\n\nIntegrate these into a final coherent answer to the original task."}]
    final = call_agent(role_for(0, n_agents), integrate_hist, protocol, n_agents)
    transcript.append(envelope(protocol, role_for(0, n_agents), "user", final))
    return "\n\n".join(transcript), final

def run_chain(task, n_agents, protocol):
    """Sequential pipeline: 0 -> 1 -> 2 -> ... -> n-1 produces final."""
    transcript = [f"TASK: {task}"]
    current = task
    for i in range(n_agents):
        sender = role_for(i, n_agents)
        next_role = role_for(i+1, n_agents) if i+1 < n_agents else "user"
        if i == 0:
            user_msg = (f"You are the first stage of a {n_agents}-stage pipeline. "
                        f"Task: {task}\nProduce your stage output. The next stage is {next_role}.")
        else:
            user_msg = (f"You are stage {i+1} of {n_agents}. Previous stage output:\n{current}\n\n"
                        f"Produce your stage output. The next recipient is {next_role}.")
        out = call_agent(sender, [{"role":"user","content":user_msg}], protocol, n_agents)
        transcript.append(envelope(protocol, sender, next_role, out))
        current = out
    return "\n\n".join(transcript), current

def run_fully_connected(task, n_agents, protocol):
    """Group chat: each round, every agent sees all prior messages and contributes."""
    transcript = [f"TASK: {task}"]
    shared = []  # list of (role, content)
    n_rounds = 2
    for r in range(n_rounds):
        for i in range(n_agents):
            role = role_for(i, n_agents)
            convo = "\n".join(f"{rl}: {ct}" for rl, ct in shared) or "(no messages yet)"
            user_msg = (f"Group chat. Original task: {task}\n"
                        f"Round {r+1}/{n_rounds}. Conversation so far:\n{convo}\n\n"
                        f"You are {role}. Add your contribution. If the task is complete, say 'DONE: <final answer>'.")
            out = call_agent(role, [{"role":"user","content":user_msg}], protocol, n_agents)
            shared.append((role, out))
            transcript.append(envelope(protocol, role, "all", out))
            if "DONE:" in out and r > 0:
                final = out.split("DONE:", 1)[1].strip()
                return "\n\n".join(transcript), final
    final = shared[-1][1] if shared else ""
    return "\n\n".join(transcript), final

TOPOLOGY_RUNNERS = {
    "centralized": run_centralized,
    "chain": run_chain,
    "fully_connected": run_fully_connected,
}

def run_trial(task):
    runner = TOPOLOGY_RUNNERS[TOPOLOGY]
    start = time.time()
    try:
        trace, final = runner(task, N_AGENTS, PROTOCOL)
        success = True
        err = None
    except Exception as e:
        trace = f"TASK: {task}\nERROR: {e}\n{traceback.format_exc()}"
        final = ""
        success = False
        err = str(e)
    elapsed = time.time() - start
    return elapsed, success, trace, final, err

def annotate_with_mast(trace_text):
    """Run agentdash MAST taxonomy on a single trace; return (fc1, fc2, fc3, ids) where
    fc{1,2,3} are counts of detected failure modes in each MAST category and ids is the
    list of triggered codes (e.g. '1.1', '2.3').
    """
    try:
        from agentdash import annotator
        ann = annotator(os.environ["OPENAI_API_KEY"])
        ann.model = ANNOT_MODEL  # override default o1-mini
        result = ann.produce_taxonomy(trace_text)
        fc1 = fc2 = fc3 = 0
        ids = []
        if isinstance(result, dict) and "failure_modes" in result:
            for code, val in result["failure_modes"].items():
                if val:  # 1 / true
                    ids.append(code)
                    if code.startswith("1."): fc1 += 1
                    elif code.startswith("2."): fc2 += 1
                    elif code.startswith("3."): fc3 += 1
        return fc1, fc2, fc3, ids
    except Exception as e:
        print(f"MAST annotation failed: {e}")
        return 0, 0, 0, []

def main():
    tasks = TASKS[TASK_TYPE]
    fc1_total = fc2_total = fc3_total = crash_total = 0
    total_time = 0.0
    per_trial = []
    for i in range(N_TRIALS):
        task = tasks[i % len(tasks)]
        elapsed, success, trace, final, err = run_trial(task)
        total_time += elapsed
        if not success:
            crash_total += 1
            fc2_total += 1  # crashes counted as FC2 (inter-agent flow broke)
            fc1 = 0; fc2 = 1; fc3 = 0; ids = ["CRASH"]
        else:
            fc1, fc2, fc3, ids = annotate_with_mast(trace)
            fc1_total += fc1; fc2_total += fc2; fc3_total += fc3
        per_trial.append({"i": i, "task": task[:60], "elapsed": elapsed,
                          "success": success, "fc1": fc1, "fc2": fc2, "fc3": fc3,
                          "ids": ids, "err": err})
        print(f"Trial {i+1}/{N_TRIALS} done in {elapsed:.1f}s success={success} fc1={fc1} fc2={fc2} fc3={fc3} ids={ids}")
        sys.stdout.flush()

    fc1_rate = fc1_total / N_TRIALS
    fc2_rate = fc2_total / N_TRIALS
    fc3_rate = fc3_total / N_TRIALS
    total_failures = fc1_total + fc2_total + fc3_total + crash_total
    avg_time = total_time / N_TRIALS

    print(f"result: FC2_rate={fc2_rate:.3f} FC1_rate={fc1_rate:.3f} FC3_rate={fc3_rate:.3f} "
          f"total_failures={total_failures} avg_time={avg_time:.1f}s "
          f"protocol={PROTOCOL} topology={TOPOLOGY} n_agents={N_AGENTS} task={TASK_TYPE}")

    # also dump per-trial json for downstream analysis
    out_dir = os.environ.get("RUN_OUT_DIR", "runs")
    os.makedirs(out_dir, exist_ok=True)
    cell_id = f"{PROTOCOL}_{TOPOLOGY}_n{N_AGENTS}_{TASK_TYPE}"
    with open(os.path.join(out_dir, f"{cell_id}.json"), "w") as f:
        json.dump({
            "config": {"protocol": PROTOCOL, "topology": TOPOLOGY,
                       "n_agents": N_AGENTS, "task_type": TASK_TYPE,
                       "n_trials": N_TRIALS, "model": WORKER_MODEL,
                       "annot_model": ANNOT_MODEL},
            "summary": {"fc1_rate": fc1_rate, "fc2_rate": fc2_rate, "fc3_rate": fc3_rate,
                        "total_failures": total_failures, "avg_time": avg_time,
                        "crash_total": crash_total},
            "trials": per_trial,
        }, f, indent=2)

if __name__ == "__main__":
    main()
