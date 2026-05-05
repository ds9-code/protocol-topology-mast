"""Rebuild results.tsv from runs/*.json. Run when results.tsv has been truncated."""
import os, json, glob, datetime

HEADER = ["timestamp", "protocol", "topology", "n_agents", "task_type",
          "n_trials", "fc1_rate", "fc2_rate", "fc3_rate",
          "total_failures", "avg_time_s", "wall_time_s", "status"]

rows = []
for path in sorted(glob.glob("runs/*.json")):
    with open(path) as f: d = json.load(f)
    cfg = d["config"]
    s = d["summary"]
    n_trials = cfg.get("n_trials", 5)
    total_failures = int(s.get("total_failures", 0))
    avg_time = s.get("avg_time", 0)
    # Use the file mtime as a proxy timestamp (sortable approximation)
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(path)).isoformat(timespec="seconds")
    rows.append([
        mt, cfg["protocol"], cfg["topology"], str(cfg["n_agents"]), cfg["task_type"],
        str(n_trials),
        f"{s.get('fc1_rate', 0):.3f}", f"{s.get('fc2_rate', 0):.3f}", f"{s.get('fc3_rate', 0):.3f}",
        str(total_failures), f"{avg_time:.1f}", "", "ok",
    ])

rows.sort(key=lambda r: (r[1], r[2], int(r[3]), r[4]))

with open("results.tsv","w") as f:
    f.write("\t".join(HEADER) + "\n")
    for r in rows:
        f.write("\t".join(r) + "\n")
print(f"wrote {len(rows)} rows")
