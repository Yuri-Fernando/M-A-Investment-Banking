"""Rebuild public README artwork and financial figures from the actual shared engine.

Run from the repository root: py -3.10 scripts/build_readme_assets.py
Needs optional requirements-docs.txt. Screenshots and Office previews are separate
native captures; this script never fabricates application screenshots.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))

import matplotlib  # noqa: E402 - configure local paths/backend before optional imports

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402 - configure local paths/backend before optional imports
from matplotlib import font_manager  # noqa: E402 - configure local paths/backend before optional imports
from PIL import Image, ImageDraw, ImageFont  # noqa: E402 - configure local paths/backend before optional imports

from ma_deallab.services import build_run  # noqa: E402 - configure local paths/backend before optional imports

NAVY = "#142D4E"
TEAL = "#087E8B"
GRAY = "#52657A"
BG = "#F4F7FA"
GOLD = "#D49A2A"
M = 1_000_000


def font(size, bold=False):
    prop = font_manager.FontProperties(family="DejaVu Sans", weight="bold" if bold else "normal")
    return ImageFont.truetype(font_manager.findfont(prop), size)


def hero(run, output):
    image = Image.new("RGB", (1800, 740), NAVY)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((76, 60, 520, 110), radius=10, fill="#1D455E")
    draw.text((98, 69), "PYTHON 3.10  /  LOCAL-FIRST", font=font(25, True), fill="#B8E7E8")
    draw.text((76, 162), "M&A Investment Banking", font=font(77, True), fill="white")
    draw.text((79, 275), "DealLab Brazil", font=font(42), fill="#8BD4D8")
    draw.text(
        (79, 356),
        "Financial modelling  /  Valuation  /  Deal execution simulation",
        font=font(28),
        fill="#DCE7F2",
    )
    metrics = [
        ("LTM REVENUE", run["ltm"]["net_revenue"] / M, "R$ million"),
        ("LTM EBITDA", run["ltm"]["ebitda"] / M, "R$ million"),
        ("BASE DCF EV", run["scenarios"]["base"]["valuation"]["ev"] / M, "R$ million"),
    ]
    for index, (label, value, unit) in enumerate(metrics):
        x = 80 + index * 555
        draw.rounded_rectangle((x, 448, x + 520, 622), radius=15, fill="#1E3A59")
        draw.text((x + 26, 468), label, font=font(23), fill="#B8CBDD")
        draw.text((x + 26, 508), f"{value:,.2f}", font=font(53, True), fill="white")
        draw.text((x + 330, 560), unit, font=font(20), fill="#B8CBDD")
    draw.text(
        (80, 676),
        "SYNTHETIC CASE  |  AS-OF 2026-09-30  |  NOT A REAL TRANSACTION",
        font=font(22),
        fill="#B8CBDD",
    )
    image.save(output / "hero.png", optimize=True)


def architecture(output):
    image = Image.new("RGB", (2000, 1150), BG)
    draw = ImageDraw.Draw(image)
    draw.text((70, 40), "One calculation engine, consistent outputs", font=font(49, True), fill=NAVY)
    draw.text((72, 117), "Financial integrity and provenance before presentation", font=font(27), fill=GRAY)
    boxes = [
        (
            (70, 220, 610, 390),
            "01  INPUTS",
            ["Synthetic CSV fixtures", "Dated public inputs: optional"],
            "#DCE7F2",
        ),
        (
            (730, 220, 1270, 390),
            "02  QUALITY GATES",
            ["Schema / dates / units / scope", "IS + BS + CF reconciliation"],
            "#DCE7F2",
        ),
        (
            (1390, 220, 1930, 390),
            "03  FINANCIAL ENGINE",
            ["LTM / QoE / integrated forecasts", "Downside / base / upside"],
            "#DCE7F2",
        ),
        (
            (1390, 540, 1930, 710),
            "04  VALUATION & TERMS",
            ["Dated FCFF DCF / WACC", "EV to equity / earnout / escrow"],
            "#D8ECEE",
        ),
        (
            (730, 540, 1270, 710),
            "05  FROZEN RUN",
            ["Inputs + assumptions + code hashes", "Metric registry + checksums"],
            "#D8ECEE",
        ),
        (
            (70, 540, 610, 710),
            "06  ANALYST OUTPUTS",
            ["Streamlit / HTML / SQLite", "Excel / PDF / editable PowerPoint"],
            "#D8ECEE",
        ),
    ]
    for (x1, y1, x2, y2), title, lines, color in boxes:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=16, fill=color, outline="#B6CADB", width=2)
        draw.text((x1 + 24, y1 + 22), title, font=font(25, True), fill=NAVY)
        for i, line in enumerate(lines):
            draw.text((x1 + 24, y1 + 76 + i * 37), line, font=font(23), fill=GRAY)

    def arrow(start, end):
        draw.line((start, end), fill=TEAL, width=7)
        x, y = end
        sx, sy = start
        if y == sy:
            d = 1 if x > sx else -1
            draw.polygon([(x, y), (x - d * 20, y - 13), (x - d * 20, y + 13)], fill=TEAL)
        else:
            draw.polygon([(x, y), (x - 13, y - 20), (x + 13, y - 20)], fill=TEAL)

    for start, end in (
        ((610, 305), (722, 305)),
        ((1270, 305), (1382, 305)),
        ((1660, 390), (1660, 532)),
        ((1390, 625), (1278, 625)),
        ((730, 625), (618, 625)),
    ):
        arrow(start, end)
    draw.rounded_rectangle((70, 835, 1930, 1050), radius=17, fill=NAVY)
    draw.text((104, 866), "CONTROL LAYER", font=font(26, True), fill="#8BD4D8")
    draw.text(
        (104, 923),
        "Evidence-based review  /  simulated roles  /  closing conditions  /  immutable exports",
        font=font(28),
        fill="white",
    )
    draw.text(
        (104, 980),
        "No invented public prices. No automatic real-world approval or outreach.",
        font=font(25),
        fill="#DCE7F2",
    )
    image.save(output / "architecture.png", optimize=True)


def figures(run, output):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 12,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelcolor": NAVY,
            "text.color": NAVY,
            "axes.edgecolor": "#CBD5DF",
        }
    )
    names = ["downside", "base", "upside"]
    values = [run["scenarios"][name]["valuation"]["ev"] / M for name in names]
    fig, ax = plt.subplots(figsize=(12, 6), facecolor="white")
    bars = ax.bar(names, values, color=["#B85450", TEAL, NAVY], width=0.55)
    ax.bar_label(bars, labels=[f"R$ {value:,.2f} mi" for value in values], padding=10, fontsize=13)
    ax.axhline(
        run["bridge"]["ev"] / M,
        color=GOLD,
        linestyle="--",
        linewidth=2,
        label="Illustrative bid EV: R$160 mi",
    )
    ax.set_ylim(0, 198)
    ax.set_ylabel("Enterprise value | R$ million")
    ax.set_title("Standalone DCF by scenario", loc="left", fontweight="bold", fontsize=21, pad=25)
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", alpha=0.15)
    ax.set_axisbelow(True)
    fig.text(
        0.08,
        0.02,
        "Synthetic case; scenario range is not a confidence interval. As-of 2026-09-30.",
        fontsize=10,
        color=GRAY,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(output / "valuation-scenarios.png", dpi=160)
    plt.close(fig)
    rows = run["scenarios"]["base"]["forecast"]
    labels = [str(row["year"]) + (" Q4E" if i == 0 else " FYF") for i, row in enumerate(rows)]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.7), facecolor="white")
    x = list(range(len(rows)))
    axes[0].bar(
        [v - 0.18 for v in x], [r["net_revenue"] / M for r in rows], width=0.35, color=NAVY, label="Revenue"
    )
    axes[0].bar(
        [v + 0.18 for v in x], [r["ebitda"] / M for r in rows], width=0.35, color=TEAL, label="EBITDA"
    )
    axes[0].set_xticks(x, labels, rotation=22)
    axes[0].set_title("Operating forecast | R$ mi", loc="left", fontweight="bold", pad=18)
    axes[0].legend(frameon=False)
    axes[1].plot(labels, [r["fcff"] / M for r in rows], marker="o", color=TEAL, linewidth=2.4, label="FCFF")
    axes[1].plot(
        labels, [r["cash"] / M for r in rows], marker="o", color=NAVY, linewidth=2.4, label="End cash"
    )
    axes[1].tick_params(axis="x", rotation=22)
    axes[1].set_title("Cash generation | R$ mi", loc="left", fontweight="bold", pad=18)
    axes[1].legend(frameon=False)
    for ax in axes:
        ax.grid(axis="y", alpha=0.15)
        ax.set_axisbelow(True)
    fig.text(
        0.06,
        0.02,
        "Q4/2026 is one projected quarter; 2027-2031 are complete fiscal years. Synthetic base scenario.",
        fontsize=10,
        color=GRAY,
    )
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(output / "forecast-cashflow.png", dpi=160)
    plt.close(fig)
    labels = ["Operating EV", "Cash", "Financial debt", "Equity"]
    bridge = run["bridge"]
    amounts = [bridge["ev"] / M, bridge["cash"] / M, -bridge["financial_debt"] / M, bridge["equity"] / M]
    bottoms = [0, amounts[0], amounts[3], 0]
    colors = [NAVY, TEAL, "#B85450", TEAL]
    fig, ax = plt.subplots(figsize=(12, 6))
    for i, (amount, bottom, color) in enumerate(zip(amounts, bottoms, colors)):
        height = abs(amount)
        ax.bar(i, height, bottom=bottom, color=color, width=0.58)
        ax.text(
            i,
            bottom + height + 4,
            f"{amount:+.0f}" if i in (1, 2) else str(amount),
            ha="center",
            fontsize=15,
            fontweight="bold",
        )
    ax.set_xticks(range(4), labels)
    ax.set_ylim(0, 195)
    ax.set_ylabel("R$ million")
    ax.set_title(
        "Illustrative bid: enterprise value to equity", loc="left", fontsize=20, fontweight="bold", pad=20
    )
    ax.grid(axis="y", alpha=0.15)
    ax.set_axisbelow(True)
    fig.text(
        0.08,
        0.02,
        "160 + 11 - 18 = 153. Before unagreed NWC true-up, unverified debt-like items and seller fees.",
        fontsize=10,
        color=GRAY,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(output / "equity-bridge.png", dpi=160)
    plt.close(fig)


def main():
    output = ROOT / "docs" / "assets"
    output.mkdir(parents=True, exist_ok=True)
    run = build_run()
    hero(run, output)
    architecture(output)
    figures(run, output)
    evidence = ROOT / "docs" / "evidence"
    evidence.mkdir(exist_ok=True)
    reference = {
        key: run[key]
        for key in (
            "run_id",
            "as_of",
            "currency",
            "unit",
            "ltm",
            "net_debt",
            "operating_nwc",
            "contract_nwc",
            "bridge",
            "consideration",
            "sources",
        )
    }
    reference["scenarios"] = {
        name: {
            "ev": s["valuation"]["ev"],
            "wacc": s["valuation"]["wacc"],
            "terminal_g": s["valuation"]["g"],
            "decision": s["decision"],
        }
        for name, s in run["scenarios"].items()
    }
    (evidence / "model_reference.json").write_text(
        json.dumps(reference, indent=2, sort_keys=True), encoding="utf-8"
    )
    print("Generated README artwork/figures from run", run["run_id"])


if __name__ == "__main__":
    main()
