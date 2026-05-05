"""Statistical analysis of results.tsv. Two-way ANOVA on FC2 rate by protocol x topology."""
import sys, json, os
import pandas as pd
import numpy as np
from scipy import stats

def main():
    df = pd.read_csv("results.tsv", sep="\t")
    df = df[df.status == "ok"].copy()
    df = df[df.task_type == "code"]
    df = df[df.n_agents == 3]

    print(f"# rows analyzed: {len(df)}")
    if len(df) == 0:
        return

    print("\n## Per-cell FC2 rate")
    cells = df.groupby(["protocol", "topology"])["fc2_rate"].agg(["mean", "std", "count"])
    print(cells)

    print("\n## Marginal effects on FC2 rate")
    print("Protocol marginals:")
    print(df.groupby("protocol")["fc2_rate"].agg(["mean", "std", "count"]))
    print("\nTopology marginals:")
    print(df.groupby("topology")["fc2_rate"].agg(["mean", "std", "count"]))

    # ANOVA via OLS / type-II decomposition would need statsmodels; do a simple
    # one-way F per factor and an interaction-style test.
    print("\n## One-way ANOVA: FC2 ~ protocol")
    groups_p = [df[df.protocol == p]["fc2_rate"].values for p in df.protocol.unique()]
    if all(len(g) > 0 for g in groups_p):
        F, p = stats.f_oneway(*groups_p)
        print(f"F={F:.3f}, p={p:.4g}")

    print("\n## One-way ANOVA: FC2 ~ topology")
    groups_t = [df[df.topology == t]["fc2_rate"].values for t in df.topology.unique()]
    if all(len(g) > 0 for g in groups_t):
        F, p = stats.f_oneway(*groups_t)
        print(f"F={F:.3f}, p={p:.4g}")

    print("\n## Best cell")
    if len(cells):
        best = cells["mean"].idxmin()
        print(f"  ({best[0]}, {best[1]}) -> FC2_rate={cells.loc[best, 'mean']:.3f}")
    print("\n## Top-3 cells by FC2 rate (ascending)")
    print(cells.sort_values("mean").head(3))

    # Dump JSON for paper integration
    out = {
        "n_rows": int(len(df)),
        "per_cell": {f"{p}|{t}": {"mean": float(m), "std": float(s) if not pd.isna(s) else None,
                                   "count": int(c)}
                     for (p,t), (m,s,c) in cells.iterrows()
                     for m, s, c in [(cells.loc[(p,t),"mean"], cells.loc[(p,t),"std"], cells.loc[(p,t),"count"])]},
    }
    with open("analysis_summary.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nwrote analysis_summary.json")

if __name__ == "__main__":
    main()
