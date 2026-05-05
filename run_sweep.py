"""
Sweep runner. Reads a list of (protocol, topology, n_agents, task_type) configs
from stdin (one per line, tab-separated), runs train.py for each, parses the result,
appends to results.tsv. Logs per-cell stdout into runs/<cell>.log.

Stdin format: protocol\ttopology\tn_agents\ttask_type   (n_trials defaults to 5)
"""
import os, sys, subprocess, time, datetime, csv, re

RESULTS_TSV = "results.tsv"
RUN_DIR = "runs"
os.makedirs(RUN_DIR, exist_ok=True)

HEADER = ["timestamp", "protocol", "topology", "n_agents", "task_type",
          "n_trials", "fc1_rate", "fc2_rate", "fc3_rate",
          "total_failures", "avg_time_s", "wall_time_s", "status"]

if not os.path.exists(RESULTS_TSV):
    with open(RESULTS_TSV, "w") as f:
        f.write("\t".join(HEADER) + "\n")

RESULT_RE = re.compile(
    r"^result:\s*FC2_rate=([\d\.]+)\s+FC1_rate=([\d\.]+)\s+FC3_rate=([\d\.]+)\s+"
    r"total_failures=(\d+)\s+avg_time=([\d\.]+)s\s+protocol=(\S+)\s+topology=(\S+)\s+"
    r"n_agents=(\d+)\s+task=(\S+)"
)

def run_one(protocol, topology, n_agents, task_type, n_trials=5, timeout_s=1200):
    env = os.environ.copy()
    env.update({
        "PROTOCOL": protocol, "TOPOLOGY": topology,
        "N_AGENTS": str(n_agents), "TASK_TYPE": task_type,
        "N_TRIALS": str(n_trials),
        "RUN_OUT_DIR": RUN_DIR,
    })
    cell_id = f"{protocol}_{topology}_n{n_agents}_{task_type}"
    # Allow distinguishing replicate runs via SUFFIX env (so we don't overwrite the JSON)
    suffix = os.environ.get("CELL_SUFFIX", "")
    if suffix:
        cell_id = f"{cell_id}_{suffix}"
    log_path = os.path.join(RUN_DIR, f"{cell_id}.log")
    t0 = time.time()
    status = "ok"
    parsed = None
    try:
        proc = subprocess.run(
            ["uv", "run", "train.py"],
            env=env, capture_output=True, text=True, timeout=timeout_s,
        )
        wall = time.time() - t0
        with open(log_path, "w") as f:
            f.write(proc.stdout)
            f.write("\n--- STDERR ---\n")
            f.write(proc.stderr)
        if proc.returncode != 0:
            status = f"exit{proc.returncode}"
        for line in proc.stdout.splitlines():
            m = RESULT_RE.match(line)
            if m:
                parsed = m.groups()
                break
        if parsed is None and status == "ok":
            status = "no_result_line"
    except subprocess.TimeoutExpired:
        wall = time.time() - t0
        status = "timeout"
        with open(log_path, "w") as f:
            f.write(f"timeout after {timeout_s}s\n")

    ts = datetime.datetime.now().isoformat(timespec="seconds")
    if parsed:
        fc2_rate, fc1_rate, fc3_rate, tot_fail, avg_time, p, t, na, tt = parsed
        row = [ts, p, t, na, tt, str(n_trials),
               fc1_rate, fc2_rate, fc3_rate, tot_fail, avg_time,
               f"{wall:.1f}", status]
    else:
        row = [ts, protocol, topology, str(n_agents), task_type, str(n_trials),
               "", "", "", "", "", f"{wall:.1f}", status]

    with open(RESULTS_TSV, "a") as f:
        f.write("\t".join(row) + "\n")

    print(f"[{ts}] {cell_id} status={status} wall={wall:.1f}s "
          f"fc1={row[6]} fc2={row[7]} fc3={row[8]} fails={row[9]}")
    sys.stdout.flush()
    return status, row

def main():
    configs = []
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith("#"): continue
        parts = line.split("\t")
        if len(parts) < 4:
            print(f"skip bad line: {line!r}", file=sys.stderr); continue
        protocol, topology, n_agents, task_type = parts[:4]
        n_trials = int(parts[4]) if len(parts) >= 5 else 5
        configs.append((protocol, topology, int(n_agents), task_type, n_trials))

    print(f"Running {len(configs)} configs")
    for cfg in configs:
        run_one(*cfg)

if __name__ == "__main__":
    main()
