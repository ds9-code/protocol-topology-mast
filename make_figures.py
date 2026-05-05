"""Generate figures from results.tsv. Run after each sweep."""
import os, sys, json, argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROTOCOLS = ["native", "mcp", "a2a"]
TOPOLOGIES = ["centralized", "chain", "fully_connected"]

def load(path="results.tsv"):
    return pd.read_csv(path, sep="\t")

def fig1_heatmap(df, out="figures/fig1_fc2_heatmap.png", task_type="code", n_agents=3):
    sub = df[(df.task_type==task_type) & (df.n_agents==n_agents) & (df.status=="ok")]
    grid = np.full((len(PROTOCOLS), len(TOPOLOGIES)), np.nan)
    for i, p in enumerate(PROTOCOLS):
        for j, t in enumerate(TOPOLOGIES):
            r = sub[(sub.protocol==p) & (sub.topology==t)]
            if len(r):
                grid[i, j] = r.fc2_rate.mean()
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    im = ax.imshow(grid, cmap="RdYlGn_r", aspect="auto", vmin=0)
    ax.set_xticks(range(len(TOPOLOGIES))); ax.set_xticklabels(TOPOLOGIES)
    ax.set_yticks(range(len(PROTOCOLS))); ax.set_yticklabels(PROTOCOLS)
    ax.set_xlabel("Topology"); ax.set_ylabel("Protocol")
    ax.set_title(f"FC2 rate (inter-agent misalignment) — {task_type}, N={n_agents}")
    for i in range(len(PROTOCOLS)):
        for j in range(len(TOPOLOGIES)):
            v = grid[i, j]
            ax.text(j, i, "n/a" if np.isnan(v) else f"{v:.2f}",
                    ha="center", va="center", color="black", fontsize=11)
    plt.colorbar(im, ax=ax, label="FC2 rate (lower = better)")
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"wrote {out}")
    return grid

def fig2_failure_breakdown(df, out="figures/fig2_failure_breakdown.png",
                           task_type="code", n_agents=3):
    sub = df[(df.task_type==task_type) & (df.n_agents==n_agents) & (df.status=="ok")]
    rows = []
    for p in PROTOCOLS:
        r = sub[sub.protocol==p]
        rows.append({
            "protocol": p,
            "FC1": r.fc1_rate.mean() if len(r) else 0,
            "FC2": r.fc2_rate.mean() if len(r) else 0,
            "FC3": r.fc3_rate.mean() if len(r) else 0,
        })
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    x = np.arange(len(rows))
    fc1 = [r["FC1"] for r in rows]
    fc2 = [r["FC2"] for r in rows]
    fc3 = [r["FC3"] for r in rows]
    ax.bar(x, fc1, label="FC1 (specification)", color="#4c72b0")
    ax.bar(x, fc2, bottom=fc1, label="FC2 (inter-agent)", color="#dd8452")
    ax.bar(x, fc3, bottom=[a+b for a,b in zip(fc1,fc2)], label="FC3 (verification)", color="#55a868")
    ax.set_xticks(x); ax.set_xticklabels([r["protocol"] for r in rows])
    ax.set_ylabel("Mean failure rate (per trial)")
    ax.set_title(f"Failure mode breakdown by protocol — {task_type}, N={n_agents}")
    ax.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"wrote {out}")

def fig3_interaction(df, out="figures/fig3_interaction.png",
                     task_type="code", n_agents=3):
    sub = df[(df.task_type==task_type) & (df.n_agents==n_agents) & (df.status=="ok")]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for p in PROTOCOLS:
        ys = []
        for t in TOPOLOGIES:
            r = sub[(sub.protocol==p) & (sub.topology==t)]
            ys.append(r.fc2_rate.mean() if len(r) else np.nan)
        ax.plot(TOPOLOGIES, ys, marker="o", label=p, linewidth=2)
    ax.set_xlabel("Topology"); ax.set_ylabel("FC2 rate")
    ax.set_title(f"Protocol x Topology interaction — {task_type}, N={n_agents}")
    ax.legend(title="Protocol")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"wrote {out}")

def fig4_n_scaling(df, out="figures/fig4_n_scaling.png", task_type="code"):
    """Plot FC2 vs N_AGENTS for the top-3 cells from sweep 2."""
    sub = df[(df.task_type == task_type) & (df.status == "ok")].copy()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for (p, t) in [("a2a","centralized"), ("a2a","fully_connected"), ("native","fully_connected")]:
        r = sub[(sub.protocol==p) & (sub.topology==t)].sort_values("n_agents")
        if len(r):
            ax.plot(r.n_agents.astype(int), r.fc2_rate, marker="o", label=f"{p} x {t}", linewidth=2)
    ax.set_xlabel("N_AGENTS"); ax.set_ylabel("FC2 rate")
    ax.set_title("FC2 rate vs N_AGENTS for top-3 cells")
    ax.set_xticks([2,3,4,5])
    ax.legend(); ax.grid(True, alpha=0.3)
    plt.tight_layout(); plt.savefig(out, dpi=150, bbox_inches="tight"); plt.close()
    print(f"wrote {out}")

def fig5_task_generalization(df, out="figures/fig5_task_generalization.png"):
    """FC1/FC2/FC3 for the best cell across task types."""
    sub = df[(df.protocol=="a2a") & (df.topology=="centralized") & (df.n_agents==3) & (df.status=="ok")]
    if len(sub) < 2: return
    rows = sub.sort_values("task_type")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(rows))
    fc1 = rows.fc1_rate.values; fc2 = rows.fc2_rate.values; fc3 = rows.fc3_rate.values
    w = 0.25
    ax.bar(x - w, fc1, w, label="FC1 (specification)", color="#4c72b0")
    ax.bar(x,     fc2, w, label="FC2 (inter-agent)", color="#dd8452")
    ax.bar(x + w, fc3, w, label="FC3 (verification)", color="#55a868")
    ax.set_xticks(x); ax.set_xticklabels(rows.task_type.values)
    ax.set_ylabel("Mean failure rate (per trial)")
    ax.set_title("a2a x centralized x N=3 across task types")
    ax.legend()
    plt.tight_layout(); plt.savefig(out, dpi=150, bbox_inches="tight"); plt.close()
    print(f"wrote {out}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", default="1,2,3,4,5")
    ap.add_argument("--task_type", default="code")
    ap.add_argument("--n_agents", type=int, default=3)
    args = ap.parse_args()
    os.makedirs("figures", exist_ok=True)
    df = load()
    if "1" in args.which: fig1_heatmap(df, task_type=args.task_type, n_agents=args.n_agents)
    if "2" in args.which: fig2_failure_breakdown(df, task_type=args.task_type, n_agents=args.n_agents)
    if "3" in args.which: fig3_interaction(df, task_type=args.task_type, n_agents=args.n_agents)
    if "4" in args.which: fig4_n_scaling(df, task_type=args.task_type)
    if "5" in args.which: fig5_task_generalization(df)

if __name__ == "__main__":
    main()
