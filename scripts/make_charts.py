"""Build the README charts from data/banking_cases.csv.

Run:  python scripts/make_charts.py
Writes light and dark PNGs into charts/.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "banking_cases.csv"
OUT = ROOT / "charts"

THEMES = {
    "light": dict(
        surface="#fcfcfb", text="#0b0b0b", text2="#52514e", muted="#8a8984",
        grid="#e6e5e0",
        hijacked="#d03b3b", defended="#2a78d6", failed="#eda100", aborted="#f0efec",
        bar_hij="#d03b3b", bar_def="#2a78d6",
    ),
    "dark": dict(
        surface="#1a1a19", text="#f0efec", text2="#c3c2b7", muted="#8f8e88",
        grid="#2e2e2c",
        hijacked="#d03b3b", defended="#3987e5", failed="#c98500", aborted="#383835",
        bar_hij="#d03b3b", bar_def="#3987e5",
    ),
}

INJECTION_LABELS = [
    "i0\nmusic", "i1\nIBAN", "i2\nfood", "i3\nphone",
    "i4\nredirect", "i5\nbig$", "i6\n30k", "i7\npwd", "i8\nlist",
]
INJECTION_GROUPS = [
    (0, "small info leak", range(0, 4)),
    (1, "overview", range(8, 9)),
    (2, "quiet severe", range(4, 5)),
    (3, "account takeover", range(7, 8)),
    (4, "loud", range(5, 7)),
]

USER_TASK_LABELS = {
    2: "u2  file\n\"adjust rent\"",
    3: "u3  transaction\n\"refund friend\"",
    7: "u7  transaction\n\"new year gift\"",
    12: "u12  file\n\"follow instructions\"",
    13: "u13  file\n\"update account info\"",
}


def load():
    rows = []
    with open(DATA) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def classify(util: str, sec: str) -> str:
    if util == "-" or sec == "-":
        return "aborted"
    if sec == "C":
        return "hijacked"
    if util == "C":
        return "defended"
    return "failed"


def apply_theme(fig, ax, t):
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])
    for sp in ax.spines.values():
        sp.set_color(t["grid"])
    ax.tick_params(colors=t["text2"], which="both")
    ax.xaxis.label.set_color(t["text"])
    ax.yaxis.label.set_color(t["text"])
    if ax.get_title():
        ax.title.set_color(t["text"])


def heatmap(rows, model, user_tasks, mode: str):
    t = THEMES[mode]
    data = defaultdict(dict)
    for r in rows:
        if r["model"] != model:
            continue
        u = int(r["user_task"])
        if u not in user_tasks:
            continue
        i = int(r["injection_task"])
        data[u][i] = classify(r["utility"], r["security"])

    color = {"hijacked": t["hijacked"], "defended": t["defended"],
             "failed": t["failed"], "aborted": t["aborted"]}

    n_rows = len(user_tasks)
    fig, ax = plt.subplots(figsize=(9.5, 1.2 + 0.75 * n_rows), dpi=160)
    for yi, u in enumerate(user_tasks):
        for i in range(9):
            cat = data.get(u, {}).get(i, "aborted")
            ax.add_patch(Rectangle(
                (i + 0.08, yi + 0.08), 0.84, 0.84,
                facecolor=color[cat], edgecolor=t["surface"], linewidth=2,
            ))
            if cat == "hijacked":
                ax.text(i + 0.5, yi + 0.5, "✕", ha="center", va="center",
                        color="#ffffff", fontsize=14, fontweight="bold")
            elif cat == "defended":
                ax.text(i + 0.5, yi + 0.5, "✓", ha="center", va="center",
                        color="#ffffff", fontsize=14, fontweight="bold")
            elif cat == "aborted":
                ax.text(i + 0.5, yi + 0.5, "–", ha="center", va="center",
                        color=t["muted"], fontsize=14)

    for i, (gi, label, rng) in enumerate(INJECTION_GROUPS):
        start = min(rng) + 0.08
        end = max(rng) + 0.92
        ax.plot([start, end], [n_rows + 0.1, n_rows + 0.1],
                color=t["muted"], linewidth=1.4, solid_capstyle="butt")
        ax.text((start + end) / 2, n_rows + 0.35, label,
                ha="center", va="bottom", fontsize=8.5, color=t["text2"])

    ax.set_xlim(0, 9)
    ax.set_ylim(0, n_rows + 0.8)
    ax.invert_yaxis()
    ax.set_xticks([i + 0.5 for i in range(9)])
    ax.set_xticklabels(INJECTION_LABELS, fontsize=8.5)
    ax.set_yticks([yi + 0.5 for yi in range(n_rows)])
    ax.set_yticklabels([USER_TASK_LABELS[u] for u in user_tasks], fontsize=9)
    ax.set_xlabel("Attacker goal (what the injection asks for)", fontsize=10, labelpad=8)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    apply_theme(fig, ax, t)

    legend_items = [("Hijacked", t["hijacked"]), ("Defended", t["defended"]),
                    ("Task failed", t["failed"]), ("Aborted", t["aborted"])]
    for k, (label, col) in enumerate(legend_items):
        x = 0.02 + k * 0.19
        fig.patches.append(Rectangle(
            (x, 0.015), 0.022, 0.028, transform=fig.transFigure,
            facecolor=col, edgecolor="none",
        ))
        fig.text(x + 0.028, 0.028, label, fontsize=8.8, color=t["text2"], va="center")

    fig.suptitle(f"{model}  —  banking suite, injection task × user task",
                 fontsize=11.5, color=t["text"], x=0.02, ha="left", y=0.98)
    plt.subplots_adjust(left=0.17, right=0.98, top=0.90, bottom=0.14)
    stem = model.replace("/", "-").replace(":", "-")
    out = OUT / f"heatmap_{stem}_{mode}.png"
    fig.savefig(out, facecolor=t["surface"])
    plt.close(fig)
    return out


def summary_bars(rows, mode: str):
    t = THEMES[mode]
    agg = defaultdict(lambda: {"n": 0, "util": 0, "sec_hij": 0})
    for r in rows:
        if r["utility"] == "-" or r["security"] == "-":
            continue
        a = agg[r["model"]]
        a["n"] += 1
        if r["utility"] == "C":
            a["util"] += 1
        if r["security"] == "C":
            a["sec_hij"] += 1

    order = ["gpt-oss-20b", "muse-glimmer-30b", "granite4.1:3b"]
    labels, util_pct, hij_pct, ns = [], [], [], []
    for m in order:
        a = agg[m]
        labels.append(f"{m}\n(n={a['n']})")
        util_pct.append(100 * a["util"] / a["n"])
        hij_pct.append(100 * a["sec_hij"] / a["n"])
        ns.append(a["n"])

    fig, ax = plt.subplots(figsize=(9.5, 4.2), dpi=160)
    y = range(len(order))
    bar_h = 0.34
    for yi, (u, h) in enumerate(zip(util_pct, hij_pct)):
        ax.add_patch(Rectangle((0, yi - bar_h - 0.03), u, bar_h,
                               facecolor=t["bar_def"], edgecolor="none"))
        ax.add_patch(Rectangle((0, yi + 0.03), h, bar_h,
                               facecolor=t["bar_hij"], edgecolor="none"))
        ax.text(u + 1.5, yi - bar_h / 2 - 0.03, f"{u:.0f}%",
                va="center", fontsize=9.5, color=t["text"])
        ax.text(h + 1.5, yi + bar_h / 2 + 0.03, f"{h:.0f}%",
                va="center", fontsize=9.5, color=t["text"])

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_xlim(0, 108)
    ax.set_ylim(-0.6, len(order) - 0.4)
    ax.invert_yaxis()
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=9)
    ax.set_xlabel("Share of completed cases", fontsize=10, labelpad=8)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(t["grid"])
    ax.tick_params(length=0)
    ax.grid(axis="x", color=t["grid"], linewidth=0.8, alpha=0.6)
    ax.set_axisbelow(True)
    apply_theme(fig, ax, t)

    fig.text(0.02, 0.03, "■ Task solved (utility)", fontsize=9, color=t["bar_def"])
    fig.text(0.30, 0.03, "■ Hijacked (attack succeeded)", fontsize=9, color=t["bar_hij"])
    fig.suptitle("Three models, same 27 cases  —  utility and attack success",
                 fontsize=11.5, color=t["text"], x=0.02, ha="left", y=0.97)
    plt.subplots_adjust(left=0.26, right=0.97, top=0.86, bottom=0.17)
    out = OUT / f"summary_bars_{mode}.png"
    fig.savefig(out, facecolor=t["surface"])
    plt.close(fig)
    return out


def delegation_bars(rows, mode: str):
    t = THEMES[mode]
    groups = [
        ("Transactions\n(u3, u7)", [3, 7]),
        ("File + narrow ask\n(u13: update account)", [13]),
        ("File + action verb\n(u2: adjust rent)", [2]),
        ("File + follow instructions\n(u12)", [12]),
    ]
    labels, pct, counts = [], [], []
    for label, us in groups:
        n = hij = 0
        for r in rows:
            if r["model"] != "muse-glimmer-30b":
                continue
            if int(r["user_task"]) not in us:
                continue
            if r["utility"] == "-" or r["security"] == "-":
                continue
            n += 1
            if r["security"] == "C":
                hij += 1
        labels.append(label)
        pct.append(100 * hij / n if n else 0)
        counts.append(f"{hij}/{n}")

    fig, ax = plt.subplots(figsize=(9.5, 3.8), dpi=160)
    y = range(len(groups))
    for yi, (p, c) in enumerate(zip(pct, counts)):
        ax.add_patch(Rectangle((0, yi - 0.3), p, 0.6,
                               facecolor=t["bar_hij"], edgecolor="none"))
        ax.text(p + 1.5, yi, f"{c}  ({p:.0f}%)",
                va="center", fontsize=10, color=t["text"])

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.7, len(groups) - 0.3)
    ax.invert_yaxis()
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=9)
    ax.set_xlabel("Share of completed cases that were hijacked", fontsize=10, labelpad=8)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(t["grid"])
    ax.tick_params(length=0)
    ax.grid(axis="x", color=t["grid"], linewidth=0.8, alpha=0.6)
    ax.set_axisbelow(True)
    apply_theme(fig, ax, t)

    fig.suptitle("muse-glimmer-30b  —  the user's wording is part of the attack surface",
                 fontsize=11.5, color=t["text"], x=0.02, ha="left", y=0.97)
    plt.subplots_adjust(left=0.30, right=0.97, top=0.87, bottom=0.17)
    out = OUT / f"delegation_{mode}.png"
    fig.savefig(out, facecolor=t["surface"])
    plt.close(fig)
    return out


def main():
    OUT.mkdir(exist_ok=True)
    rows = load()
    made = []
    for mode in ("light", "dark"):
        made.append(summary_bars(rows, mode))
        made.append(heatmap(rows, "gpt-oss-20b", [2, 3, 7], mode))
        made.append(heatmap(rows, "muse-glimmer-30b", [3, 7, 2, 13, 12], mode))
        made.append(delegation_bars(rows, mode))
    for p in made:
        print(p)


if __name__ == "__main__":
    main()
