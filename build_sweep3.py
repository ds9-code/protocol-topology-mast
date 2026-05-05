"""Pick the single best (protocol, topology, n_agents) cell from sweeps 1+2 by FC2 rate,
generate sweep 3 varying TASK_TYPE in {qa, planning}. Writes sweep3.tsv."""
import pandas as pd

df = pd.read_csv("results.tsv", sep="\t")
df = df[(df.status == "ok") & (df.task_type == "code")]
agg = (df.groupby(["protocol","topology","n_agents"])["fc2_rate"]
         .mean()
         .sort_values()
         .reset_index())
best = agg.iloc[0]
print(f"Best cell: protocol={best.protocol} topology={best.topology} n_agents={best.n_agents} fc2={best.fc2_rate:.3f}")

with open("sweep3.tsv","w") as f:
    for tt in ["qa", "planning"]:
        f.write(f"{best.protocol}\t{best.topology}\t{int(best.n_agents)}\t{tt}\t5\n")
print("wrote sweep3.tsv")
