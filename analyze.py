"""Trial-level statistical analysis on the sweep 1 cells.

Reads runs/*.json (each contains 5 trials with per-trial fc1/fc2/fc3 counts), filters to
sweep 1 (n_agents=3, task_type=code), and runs:
  - per-cell summary (mean/std)
  - one-way ANOVA on FC2 by protocol
  - one-way ANOVA on FC2 by topology
  - two-way ANOVA via OLS on the trial-level data
  - Welch t-test of best cell vs worst cell
"""
import os, json, glob, sys
import pandas as pd
import numpy as np
from scipy import stats

PROTOCOLS = ["native", "mcp", "a2a"]
TOPOLOGIES = ["centralized", "chain", "fully_connected"]

def load_trials():
    rows = []
    for path in sorted(glob.glob("runs/*.json")):
        with open(path) as f: d = json.load(f)
        cfg = d["config"]
        if cfg.get("n_agents") != 3 or cfg.get("task_type") != "code":
            continue  # only sweep 1
        for t in d["trials"]:
            rows.append({
                "protocol": cfg["protocol"], "topology": cfg["topology"],
                "n_agents": cfg["n_agents"], "task_type": cfg["task_type"],
                "model": cfg.get("model"), "trial": t["i"],
                "fc1": t["fc1"], "fc2": t["fc2"], "fc3": t["fc3"],
                "success": t["success"], "elapsed": t.get("elapsed", 0),
            })
    return pd.DataFrame(rows)

def main():
    df = load_trials()
    print(f"# trials in sweep 1: {len(df)} from {df.groupby(['protocol','topology']).ngroups} cells")
    if df.empty:
        print("no data"); return

    print("\n## Per-cell FC2 summary (mean +/- std over 5 trials)")
    cells = df.groupby(["protocol","topology"])["fc2"].agg(["mean","std","count"])
    print(cells)

    print("\n## Marginal FC2 by protocol")
    print(df.groupby("protocol")["fc2"].agg(["mean","std","count"]))
    print("\n## Marginal FC2 by topology")
    print(df.groupby("topology")["fc2"].agg(["mean","std","count"]))

    # One-way ANOVA on trials
    groups_p = [df[df.protocol==p]["fc2"].values for p in PROTOCOLS if (df.protocol==p).any()]
    groups_t = [df[df.topology==t]["fc2"].values for t in TOPOLOGIES if (df.topology==t).any()]
    if len(groups_p) >= 2:
        F, p = stats.f_oneway(*groups_p)
        print(f"\n## One-way ANOVA FC2 ~ protocol: F={F:.3f} p={p:.4f}")
    if len(groups_t) >= 2:
        F, p = stats.f_oneway(*groups_t)
        print(f"## One-way ANOVA FC2 ~ topology: F={F:.3f} p={p:.4f}")

    # Best vs worst cell t-test
    cell_means = cells["mean"].sort_values()
    if len(cell_means) >= 2:
        best = cell_means.index[0]; worst = cell_means.index[-1]
        b = df[(df.protocol==best[0]) & (df.topology==best[1])]["fc2"].values
        w = df[(df.protocol==worst[0]) & (df.topology==worst[1])]["fc2"].values
        T, p = stats.ttest_ind(b, w, equal_var=False)
        print(f"\n## Welch t-test best ({best}) vs worst ({worst}): T={T:.3f} p={p:.4f}")

    # Two-way ANOVA via OLS
    try:
        import statsmodels.api as sm
        from statsmodels.formula.api import ols
        model = ols("fc2 ~ C(protocol) + C(topology) + C(protocol):C(topology)", data=df).fit()
        anova = sm.stats.anova_lm(model, typ=2)
        print(f"\n## Two-way ANOVA (Type II)")
        print(anova)
    except Exception as e:
        print(f"\n(skip two-way: {e})")

    # FC1 and FC3 analysis
    print("\n## FC1 (specification) marginals")
    print(df.groupby("protocol")["fc1"].agg(["mean","std","count"]))
    print(df.groupby("topology")["fc1"].agg(["mean","std","count"]))
    if len(groups_p := [df[df.protocol==p]["fc1"].values for p in PROTOCOLS if (df.protocol==p).any()]) >= 2:
        F, p = stats.f_oneway(*groups_p)
        print(f"FC1 ~ protocol: F={F:.3f} p={p:.4f}")
    if len(groups_t := [df[df.topology==t]["fc1"].values for t in TOPOLOGIES if (df.topology==t).any()]) >= 2:
        F, p = stats.f_oneway(*groups_t)
        print(f"FC1 ~ topology: F={F:.3f} p={p:.4f}")

    print("\n## FC3 (verification) marginals")
    print(df.groupby("protocol")["fc3"].agg(["mean","std","count"]))
    print(df.groupby("topology")["fc3"].agg(["mean","std","count"]))
    if len(groups_p := [df[df.protocol==p]["fc3"].values for p in PROTOCOLS if (df.protocol==p).any()]) >= 2:
        F, p = stats.f_oneway(*groups_p)
        print(f"FC3 ~ protocol: F={F:.3f} p={p:.4f}")
    if len(groups_t := [df[df.topology==t]["fc3"].values for t in TOPOLOGIES if (df.topology==t).any()]) >= 2:
        F, p = stats.f_oneway(*groups_t)
        print(f"FC3 ~ topology: F={F:.3f} p={p:.4f}")

    # Save summary
    out = {
        "n_trials": int(len(df)),
        "per_cell": {f"{p}|{t}": {
                        "fc2_mean": float(df[(df.protocol==p)&(df.topology==t)]["fc2"].mean()),
                        "fc2_std":  float(df[(df.protocol==p)&(df.topology==t)]["fc2"].std()),
                        "fc1_mean": float(df[(df.protocol==p)&(df.topology==t)]["fc1"].mean()),
                        "fc3_mean": float(df[(df.protocol==p)&(df.topology==t)]["fc3"].mean()),
                        "n":    int(((df.protocol==p)&(df.topology==t)).sum()),
                    } for p in PROTOCOLS for t in TOPOLOGIES
                    if ((df.protocol==p)&(df.topology==t)).any()},
        "marginal_protocol_fc2": df.groupby("protocol")["fc2"].mean().to_dict(),
        "marginal_topology_fc2": df.groupby("topology")["fc2"].mean().to_dict(),
        "marginal_protocol_fc1": df.groupby("protocol")["fc1"].mean().to_dict(),
        "marginal_topology_fc1": df.groupby("topology")["fc1"].mean().to_dict(),
        "marginal_protocol_fc3": df.groupby("protocol")["fc3"].mean().to_dict(),
        "marginal_topology_fc3": df.groupby("topology")["fc3"].mean().to_dict(),
    }
    with open("analysis_summary.json","w") as f:
        json.dump(out, f, indent=2, default=str)
    print("\nwrote analysis_summary.json")

if __name__ == "__main__":
    main()
