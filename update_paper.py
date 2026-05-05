"""Update paper/paper.md results table with current numbers from results.tsv.

Replaces the block between <!-- BEGIN-SWEEP1-TABLE --> and <!-- END-SWEEP1-TABLE -->.
"""
import pandas as pd, re, sys, os

PROTOCOLS = ["native", "mcp", "a2a"]
TOPOLOGIES = ["centralized", "chain", "fully_connected"]

df = pd.read_csv("results.tsv", sep="\t")
sweep1 = df[(df.status == "ok") & (df.task_type == "code") & (df.n_agents == 3)]

rows = []
best_cell = None; best_fc2 = float("inf")
worst_fc2 = -1.0
for p in PROTOCOLS:
    for t in TOPOLOGIES:
        r = sweep1[(sweep1.protocol == p) & (sweep1.topology == t)]
        if len(r):
            mean = r.iloc[-1]
            fc1 = f"{mean.fc1_rate:.2f}"; fc2 = f"{mean.fc2_rate:.2f}"
            fc3 = f"{mean.fc3_rate:.2f}"; tf = f"{int(mean.total_failures)}"
            at = f"{mean.avg_time_s:.1f}"
            if mean.fc2_rate < best_fc2:
                best_fc2 = mean.fc2_rate; best_cell = f"{p} x {t}"
            if mean.fc2_rate > worst_fc2:
                worst_fc2 = mean.fc2_rate
        else:
            fc1 = fc2 = fc3 = tf = at = "RESULT"
        rows.append(f"| {p} | {t} | {fc1} | {fc2} | {fc3} | {tf} | {at} |")

table = "\n".join([
    "<!-- BEGIN-SWEEP1-TABLE -->",
    "| Protocol | Topology | FC1 | FC2 | FC3 | Total fail | Avg time (s) |",
    "|----------|----------|-----|-----|-----|------------|--------------|",
] + rows + ["<!-- END-SWEEP1-TABLE -->"])

PATH = "paper/paper.md"
if not os.path.exists(PATH) or os.path.getsize(PATH) == 0:
    print(f"!! {PATH} missing or empty, skipping", file=sys.stderr); sys.exit(1)

with open(PATH, "r") as f: content = f.read()
m = re.search(r"<!-- BEGIN-SWEEP1-TABLE -->[\s\S]*?<!-- END-SWEEP1-TABLE -->", content)
if not m:
    print(f"!! sweep1 markers not found in {PATH}; not modifying", file=sys.stderr); sys.exit(1)
new_content = content[:m.start()] + table + content[m.end():]

if best_cell is not None and worst_fc2 > 0 and best_fc2 < worst_fc2:
    abstract_line = (f"**Primary result (live update):** the best protocol x topology cell "
                     f"({best_cell}) achieves FC2 = {best_fc2:.2f}, versus {worst_fc2:.2f} for "
                     f"the worst cell ({worst_fc2/best_fc2:.2f}x reduction).")
    new_content = re.sub(
        r"\*\*Primary result[^*]*?\*\*[^\n]*",
        abstract_line,
        new_content,
        count=1,
    )

with open(PATH, "w") as f: f.write(new_content)
print(f"updated paper/paper.md: {len(sweep1)} sweep1 cells; best={best_cell} fc2={best_fc2}")
