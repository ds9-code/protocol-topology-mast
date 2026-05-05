"""Pick top-3 (protocol, topology) cells from sweep 1 by FC2 rate, generate sweep 2 config
varying N_AGENTS in {2,4,5} for each. Writes sweep2.tsv."""
import pandas as pd

df = pd.read_csv("results.tsv", sep="\t")
df = df[(df.status == "ok") & (df.task_type == "code") & (df.n_agents == 3)]
agg = (df.groupby(["protocol","topology"])["fc2_rate"]
         .mean()
         .sort_values()
         .reset_index())
top3 = agg.head(3)
print("Top 3 cells by FC2 rate (ascending):")
print(top3.to_string(index=False))

with open("sweep2.tsv","w") as f:
    for _, row in top3.iterrows():
        for n in [2, 4, 5]:
            f.write(f"{row.protocol}\t{row.topology}\t{n}\tcode\t5\n")
print("wrote sweep2.tsv")
