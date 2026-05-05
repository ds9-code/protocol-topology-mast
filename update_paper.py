"""Update paper/paper.md results table with current numbers from results.tsv."""
import pandas as pd, re, sys, os

PROTOCOLS = ["native", "mcp", "a2a"]
TOPOLOGIES = ["centralized", "chain", "fully_connected"]

df = pd.read_csv("results.tsv", sep="\t")
sweep1 = df[(df.status == "ok") & (df.task_type == "code") & (df.n_agents == 3)]

# Build the markdown table rows
rows = []
best_cell = None
best_fc2 = float("inf")
worst_fc2 = -1.0
for p in PROTOCOLS:
    for t in TOPOLOGIES:
        r = sweep1[(sweep1.protocol == p) & (sweep1.topology == t)]
        if len(r):
            mean = r.iloc[-1]  # latest run for this cell
            fc1 = f"{mean.fc1_rate:.2f}"
            fc2 = f"{mean.fc2_rate:.2f}"
            fc3 = f"{mean.fc3_rate:.2f}"
            tf = f"{int(mean.total_failures)}"
            at = f"{mean.avg_time_s:.1f}"
            if mean.fc2_rate < best_fc2:
                best_fc2 = mean.fc2_rate; best_cell = f"{p} x {t}"
            if mean.fc2_rate > worst_fc2:
                worst_fc2 = mean.fc2_rate
        else:
            fc1 = fc2 = fc3 = tf = at = "RESULT"
        rows.append(f"| {p} | {t} | {fc1} | {fc2} | {fc3} | {tf} | {at} |")

with open("paper/paper.md", "r") as f:
    content = f.read()

# Replace the whole sweep1 table block between the two header markers
table_md = "\n".join([
    "| Protocol | Topology | FC1 | FC2 | FC3 | Total fail | Avg time (s) |",
    "|----------|----------|-----|-----|-----|------------|--------------|",
] + rows)

new_content = re.sub(
    r"\| Protocol \| Topology[\s\S]*?(?=\nSee `figures/fig1)",
    table_md + "\n\n",
    content,
    count=1,
)

# Update the abstract placeholder if we have at least one cell completed
if best_cell is not None and worst_fc2 > 0:
    abstract_line = (f"**Primary result:** the best protocol x topology cell ({best_cell}) "
                     f"achieves FC2 = {best_fc2:.2f}, versus {worst_fc2:.2f} for the worst cell "
                     f"({(worst_fc2/best_fc2 if best_fc2>0 else float('inf')):.1f}x reduction).")
    new_content = re.sub(
        r"\*\*Primary result \(placeholder\):\*\*[^\n]*",
        abstract_line.replace("**Primary result:**", "**Primary result (live update):**"),
        new_content,
    )

with open("paper/paper.md", "w") as f:
    f.write(new_content)

print(f"updated paper/paper.md: {len(sweep1)} sweep1 cells; best={best_cell} fc2={best_fc2}")
