"""Build visual figures and PowerPoint presentation for the AI Control 7-line NormalDist calculation."""

from __future__ import annotations

import os
from pathlib import Path
from statistics import NormalDist

# Ensure writable MPLCONFIGDIR inside scratch before importing matplotlib
SCRATCH_MPL = Path(
    r"C:\Users\Baskaran.Nagavel\.gemini\antigravity\brain\c8301381-c31f-449c-9a2a-3653b4183650\scratch\mpl"
)
SCRATCH_MPL.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(SCRATCH_MPL))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

# Output paths
PROJECT_ROOT = Path(r"C:\Bask\00.AI\017.Anthropic_prog\ai-control-project")
FIG_DIR_PROJ = PROJECT_ROOT / "results" / "figures"
FIG_DIR_ART = Path(
    r"C:\Users\Baskaran.Nagavel\.gemini\antigravity\brain\c8301381-c31f-449c-9a2a-3653b4183650"
)
PPTX_PATH = PROJECT_ROOT / "docs" / "AI_Control_Statistics_Walkthrough.pptx"

FIG_DIR_PROJ.mkdir(parents=True, exist_ok=True)
FIG_DIR_ART.mkdir(parents=True, exist_ok=True)
PPTX_PATH.parent.mkdir(parents=True, exist_ok=True)

# Exact calculation from the 7-line snippet
nd = NormalDist()  # mean 0, standard deviation 1
budget, sep, p_ok = 0.02, 2.0, 0.5
t = nd.inv_cdf(1 - budget)  # threshold -> ~2.0537
c = 1 - nd.cdf(t - sep)  # caught -> ~0.4785
s = (1 - c) * p_ok  # slipped+won -> ~0.2607
safety = c / (c + s)  # safety -> ~0.6473

# Global plot styling (1600x900 at 150 DPI)
FIG_SIZE = (1600 / 150, 900 / 150)
DPI = 150

C_BLUE = "#2563EB"
C_BLUE_LIGHT = "#93C5FD"
C_ORANGE = "#EA580C"
C_ORANGE_LIGHT = "#FDBA74"
C_RED = "#DC2626"
C_RED_LIGHT = "#FCA5A5"
C_GREEN = "#16A34A"
C_GREEN_LIGHT = "#86EFAC"
C_AMBER = "#D97706"
C_AMBER_LIGHT = "#FDE68A"
C_GREY = "#64748B"
C_GREY_LIGHT = "#CBD5E1"
C_DARK = "#0F172A"
C_BG = "#FFFFFF"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.edgecolor": "#CBD5E1",
        "axes.linewidth": 1.0,
        "figure.facecolor": C_BG,
        "axes.facecolor": C_BG,
    }
)


def norm_pdf(x: np.ndarray, mu: float = 0.0, sigma: float = 1.0) -> np.ndarray:
    return (1.0 / (sigma * np.sqrt(2.0 * np.pi))) * np.exp(
        -0.5 * ((x - mu) / sigma) ** 2
    )


def save_fig(fig: plt.Figure, filename: str) -> list[Path]:
    paths = [FIG_DIR_PROJ / filename, FIG_DIR_ART / filename]
    for p in paths:
        fig.savefig(p, dpi=DPI, facecolor=C_BG)
    plt.close(fig)
    return paths


def make_fig1() -> None:
    """fig1_cdf_vs_invcdf.png: The Bell Curve & Two Functions (cdf vs inv_cdf)."""
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=DPI)
    x = np.linspace(-3.6, 3.6, 800)
    y = norm_pdf(x, 0.0, 1.0)
    x_cut = 1.0
    p_left = nd.cdf(x_cut)
    p_right = 1.0 - p_left

    ax.plot(x, y, color=C_DARK, linewidth=2.5)
    mask_l = x <= x_cut
    mask_r = x >= x_cut
    ax.fill_between(
        x[mask_l], 0, y[mask_l], color=C_BLUE_LIGHT, alpha=0.65, label="Left Area = nd.cdf(x)"
    )
    ax.fill_between(
        x[mask_r],
        0,
        y[mask_r],
        color=C_ORANGE_LIGHT,
        alpha=0.75,
        label="Right Area = 1 - nd.cdf(x)",
    )
    ax.axvline(x_cut, color=C_RED, linestyle="--", linewidth=2.4)
    ax.axhline(0, color="#94A3B8", linewidth=1.0)

    # Labels inside shaded regions
    ax.text(
        -0.35,
        0.16,
        f"Area to the LEFT\n= nd.cdf({x_cut:.1f})\n= {p_left:.3f} ({p_left*100:.1f}%)",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="#1E3A8A",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=C_BLUE, alpha=0.92),
    )
    ax.annotate(
        f"Area to the RIGHT\n= 1 - nd.cdf({x_cut:.1f})\n= {p_right:.3f} ({p_right*100:.1f}%)",
        xy=(1.55, 0.06),
        xytext=(2.35, 0.21),
        ha="center",
        fontsize=11.5,
        fontweight="bold",
        color="#9A3412",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=C_ORANGE, alpha=0.92),
        arrowprops=dict(arrowstyle="->", color=C_ORANGE, lw=2.0),
    )
    ax.annotate(
        f"Cutoff Score x = {x_cut:.1f}\n(nd.inv_cdf({p_left:.3f}) = {x_cut:.1f})",
        xy=(x_cut, 0.28),
        xytext=(1.30, 0.35),
        ha="left",
        fontsize=10.5,
        fontweight="bold",
        color=C_RED,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=C_RED, alpha=0.92),
        arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.8),
    )

    # Callout boxes at top-left
    callout = (
        "Total Area Under Curve = 1.00 (100%)\n"
        "-----------------------------------------\n"
        "1) nd.cdf(x)     : Score (x)     -> Left Area (p)\n"
        "2) nd.inv_cdf(p) : Left Area (p) -> Cutoff Score (x)\n"
        "Right Area = 1 - Left Area"
    )
    ax.text(
        -3.45,
        0.49,
        callout,
        ha="left",
        va="top",
        fontsize=10.5,
        family="monospace",
        color=C_DARK,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#F8FAFC", edgecolor="#94A3B8", lw=1.2),
    )

    ax.set_xlim(-3.6, 3.6)
    ax.set_ylim(0, 0.52)
    ax.set_xlabel("Suspicion Score (x)", fontsize=12, fontweight="bold", labelpad=8)
    ax.set_ylabel("Probability Density", fontsize=12, fontweight="bold", labelpad=8)
    ax.set_title(
        "The Standard Bell Curve N(0, 1): Converting Between Score (x) and Area (p)",
        fontsize=14,
        fontweight="bold",
        pad=14,
        color=C_DARK,
    )
    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=10.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=1.6)
    save_fig(fig, "fig1_cdf_vs_invcdf.png")


def make_fig2() -> None:
    """fig2_threshold_t.png: Line 4: t = nd.inv_cdf(1 - budget) -> 2.054."""
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=DPI)
    x = np.linspace(-3.6, 3.8, 900)
    y = norm_pdf(x, 0.0, 1.0)

    ax.plot(x, y, color=C_BLUE, linewidth=2.5, label="Honest Code Scores ~ N(0, 1)")
    mask_l = x <= t
    mask_r = x >= t
    ax.fill_between(x[mask_l], 0, y[mask_l], color=C_BLUE_LIGHT, alpha=0.55)
    ax.fill_between(x[mask_r], 0, y[mask_r], color=C_RED_LIGHT, alpha=0.85)
    ax.axvline(t, color=C_RED, linestyle="--", linewidth=2.6)
    ax.axhline(0, color="#94A3B8", linewidth=1.0)

    ax.text(
        0.0,
        0.17,
        "98% Ignored (Left of t)\n1 - budget = 0.98\n(~980 of 1,000 honest tasks)",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="#1E3A8A",
        bbox=dict(boxstyle="round,pad=0.45", facecolor="white", edgecolor=C_BLUE, alpha=0.92),
    )

    ax.annotate(
        f"2% Audited by Humans\n(budget = {budget:.2f})\n~20 of 1,000 honest tasks",
        xy=(2.45, 0.018),
        xytext=(2.65, 0.16),
        ha="center",
        fontsize=11,
        fontweight="bold",
        color="#991B1B",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FEF2F2", edgecolor=C_RED, lw=1.4),
        arrowprops=dict(arrowstyle="->", color=C_RED, lw=2.0),
    )

    ax.annotate(
        f"Alarm Threshold\nt = nd.inv_cdf(1 - 0.02)\n  = nd.inv_cdf(0.98)\n  = {t:.3f}",
        xy=(t, 0.34),
        xytext=(0.70, 0.42),
        ha="left",
        va="center",
        fontsize=11,
        family="monospace",
        fontweight="bold",
        color=C_RED,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="white", edgecolor=C_RED, lw=1.4),
        arrowprops=dict(arrowstyle="->", color=C_RED, lw=2.0),
    )

    ax.text(
        -3.45,
        0.44,
        "NDI Analogy:\nBackground eddy-current noise on good\nfastener holes is centered at 0.\nSet alarm t so only 2% false alarms occur.",
        ha="left",
        va="top",
        fontsize=10.5,
        color=C_DARK,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#F8FAFC", edgecolor="#94A3B8"),
    )

    ax.set_xlim(-3.6, 3.8)
    ax.set_ylim(0, 0.49)
    ax.set_xlabel("Monitor Suspicion Score (x)", fontsize=12, fontweight="bold", labelpad=8)
    ax.set_ylabel("Probability Density", fontsize=12, fontweight="bold", labelpad=8)
    ax.set_title(
        f"Line 4: Setting the Alarm Threshold (t = nd.inv_cdf(1 - budget) = {t:.3f})",
        fontsize=14,
        fontweight="bold",
        pad=14,
        color=C_DARK,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=1.6)
    save_fig(fig, "fig2_threshold_t.png")


def make_fig3() -> None:
    """fig3_caught_c.png: Line 5: c = 1 - nd.cdf(t - sep) -> 0.478 (Two Subplots)."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=FIG_SIZE, dpi=DPI, height_ratios=[1.15, 1.0])

    # Top subplot: Actual Scores [-3.5, 5.5]
    x1 = np.linspace(-3.5, 5.5, 900)
    y_hon = norm_pdf(x1, 0.0, 1.0)
    y_att = norm_pdf(x1, sep, 1.0)

    ax1.plot(x1, y_hon, color=C_BLUE, linestyle="--", linewidth=2.0, label="Honest Curve N(0, 1)")
    ax1.plot(x1, y_att, color=C_RED, linewidth=2.5, label=f"Attack Curve N({sep:.1f}, 1)")
    ax1.fill_between(
        x1[x1 <= t], 0, y_att[x1 <= t], color=C_AMBER_LIGHT, alpha=0.75, label=f"Slipped past audit: 1 - c = {(1-c)*100:.1f}%"
    )
    ax1.fill_between(
        x1[x1 >= t], 0, y_att[x1 >= t], color=C_GREEN_LIGHT, alpha=0.80, label=f"Caught & audited: c = {c*100:.1f}%"
    )
    ax1.axvline(t, color=C_DARK, linestyle="--", linewidth=2.2)
    ax1.axvline(sep, color=C_RED, linestyle=":", linewidth=1.6)

    ax1.annotate(
        f"Alarm t = {t:.3f}",
        xy=(t, 0.40),
        xytext=(t - 0.35, 0.42),
        ha="right",
        fontsize=10.5,
        fontweight="bold",
        color=C_DARK,
        arrowprops=dict(arrowstyle="->", color=C_DARK, lw=1.5),
    )
    ax1.annotate(
        f"Gap t - sep\n= {t:.3f} - {sep:.1f} = {t-sep:.3f}",
        xy=((sep + t) / 2, 0.04),
        xytext=(-1.6, 0.25),
        ha="center",
        fontsize=10,
        fontweight="bold",
        color="#7C2D12",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#FFF7ED", edgecolor=C_AMBER),
        arrowprops=dict(arrowstyle="->", color=C_AMBER, lw=1.6),
    )
    ax1.text(1.25, 0.14, f"Slipped\n{(1-c)*100:.1f}%", ha="center", fontweight="bold", color="#92400E", fontsize=10.5)
    ax1.text(2.85, 0.14, f"Caught\n{c*100:.1f}%", ha="center", fontweight="bold", color="#14532D", fontsize=10.5)

    ax1.set_xlim(-3.5, 5.5)
    ax1.set_ylim(0, 0.48)
    ax1.set_ylabel("Density", fontsize=11, fontweight="bold")
    ax1.set_title(
        f"Line 5: How Many Attacks Are Caught?  c = 1 - nd.cdf(t - sep) = {c:.3f} ({c*100:.1f}%)",
        fontsize=13.5,
        fontweight="bold",
        pad=10,
        color=C_DARK,
    )
    ax1.legend(loc="upper right", fontsize=9.5, frameon=True, facecolor="white")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # Bottom subplot: Shifted coordinates (Score - sep) so attack curve is centered at 0
    x2 = np.linspace(-5.5, 3.5, 900)
    y_shift = norm_pdf(x2, 0.0, 1.0)
    t_shift = t - sep
    ax2.plot(x2, y_shift, color=C_RED, linewidth=2.5, label="Same Attack Curve Shifted to Center 0 (nd = NormalDist())")
    ax2.fill_between(x2[x2 <= t_shift], 0, y_shift[x2 <= t_shift], color=C_AMBER_LIGHT, alpha=0.75)
    ax2.fill_between(x2[x2 >= t_shift], 0, y_shift[x2 >= t_shift], color=C_GREEN_LIGHT, alpha=0.80)
    ax2.axvline(0.0, color=C_RED, linestyle=":", linewidth=1.6)
    ax2.axvline(t_shift, color=C_DARK, linestyle="--", linewidth=2.2)

    ax2.text(
        -0.95,
        0.16,
        f"Left of (t - sep)\nnd.cdf({t_shift:.3f}) = {1-c:.3f}\n({(1-c)*100:.1f}% slipped)",
        ha="center",
        va="center",
        fontsize=10.5,
        fontweight="bold",
        color="#92400E",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor=C_AMBER, alpha=0.92),
    )
    ax2.text(
        1.15,
        0.16,
        f"Right of (t - sep)\n1 - nd.cdf({t_shift:.3f}) = {c:.3f}\n({c*100:.1f}% caught)",
        ha="center",
        va="center",
        fontsize=10.5,
        fontweight="bold",
        color="#14532D",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor=C_GREEN, alpha=0.92),
    )
    ax2.annotate(
        f"Shifted threshold\nt - sep = {t_shift:.3f}",
        xy=(t_shift, 0.41),
        xytext=(1.0, 0.42),
        fontsize=10,
        fontweight="bold",
        color=C_DARK,
        arrowprops=dict(arrowstyle="->", color=C_DARK, lw=1.5),
    )

    ax2.set_xlim(-5.5, 3.5)
    ax2.set_ylim(0, 0.48)
    ax2.set_xlabel("Shifted Axis: (Score - sep)  [Why we pass t - sep into nd.cdf()]", fontsize=11, fontweight="bold", labelpad=6)
    ax2.set_ylabel("Density", fontsize=11, fontweight="bold")
    ax2.set_title(
        "Why (t - sep)? Shifting by -sep puts the Attack Curve at 0 so nd.cdf() can measure it",
        fontsize=11.5,
        fontweight="bold",
        color="#334155",
    )
    ax2.legend(loc="upper left", fontsize=9.5, frameon=True, facecolor="white")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout(pad=1.5)
    save_fig(fig, "fig3_caught_c.png")


def _draw_box(
    ax: plt.Axes,
    cx: float,
    cy: float,
    w: float,
    h: float,
    title: str,
    subtitle: str,
    facecolor: str,
    edgecolor: str,
    title_color: str = C_DARK,
) -> None:
    box = FancyBboxPatch(
        (cx - w / 2, cy - h / 2),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=2.2,
    )
    ax.add_patch(box)
    ax.text(cx, cy + h * 0.14, title, ha="center", va="center", fontsize=12.5, fontweight="bold", color=title_color)
    ax.text(cx, cy - h * 0.18, subtitle, ha="center", va="center", fontsize=10.5, color="#1E293B")


def make_fig4() -> None:
    """fig4_attack_tree.png: Line 6: s = (1 - c) * p_ok -> 0.261 (Fate of 100 Attacks)."""
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=DPI)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5,
        0.95,
        f"Line 6: Fate of 100 Backdoor Attacks  (s = (1 - c) * p_ok = {s:.3f})",
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        color=C_DARK,
    )

    # Top root node
    _draw_box(
        ax,
        0.50,
        0.81,
        0.38,
        0.13,
        "100 Backdoor Attacks Attempted",
        "Each scored by monitor (N(2.0, 1)) against threshold t = 2.054",
        "#EFF6FF",
        C_BLUE,
    )

    # Arrows from root to Caught & Slipped
    ax.annotate("", xy=(0.24, 0.59), xytext=(0.42, 0.74), arrowprops=dict(arrowstyle="->", lw=2.4, color=C_GREEN))
    ax.annotate("", xy=(0.72, 0.59), xytext=(0.58, 0.74), arrowprops=dict(arrowstyle="->", lw=2.4, color=C_AMBER))
    ax.text(0.28, 0.67, f"Score >= {t:.3f}\nc = {c:.3f}", ha="center", va="center", fontsize=10.5, fontweight="bold", color="#166534", bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=C_GREEN))
    ax.text(0.70, 0.67, f"Score < {t:.3f}\n1 - c = {1-c:.3f}", ha="center", va="center", fontsize=10.5, fontweight="bold", color="#92400E", bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=C_AMBER))

    # Left: Caught
    _draw_box(
        ax,
        0.24,
        0.50,
        0.34,
        0.16,
        f"{c*100:.1f} CAUGHT (Blue Wins!)",
        "Audited by humans -> AI shut down.\nGame ends immediately in Blue's favor.",
        "#DCFCE7",
        C_GREEN,
        "#14532D",
    )

    # Right: Slipped Past
    _draw_box(
        ax,
        0.72,
        0.50,
        0.36,
        0.16,
        f"{(1-c)*100:.1f} SLIPPED PAST AUDIT",
        f"Not inspected by humans.\nNow test if exploit works (p_ok = {p_ok:.1f}).",
        "#FEF3C7",
        C_AMBER,
        "#78350F",
    )

    # Arrows from Slipped to Succeeded & Dud
    ax.annotate("", xy=(0.50, 0.25), xytext=(0.64, 0.41), arrowprops=dict(arrowstyle="->", lw=2.4, color=C_RED))
    ax.annotate("", xy=(0.84, 0.25), xytext=(0.78, 0.41), arrowprops=dict(arrowstyle="->", lw=2.4, color=C_GREY))
    ax.text(0.53, 0.34, f"Works\np_ok = {p_ok:.1f}", ha="center", va="center", fontsize=10, fontweight="bold", color="#991B1B", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=C_RED))
    ax.text(0.84, 0.34, f"Fizzles\n1 - p_ok = {1-p_ok:.1f}", ha="center", va="center", fontsize=10, fontweight="bold", color="#334155", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=C_GREY))

    # Bottom leaves
    _draw_box(
        ax,
        0.50,
        0.16,
        0.30,
        0.16,
        f"{s*100:.1f} SUCCEEDED (Red Wins!)",
        f"s = (1 - c) * p_ok = {1-c:.3f} * {p_ok:.1f} = {s:.3f}\nGame ends immediately in Red's favor.",
        "#FEE2E2",
        C_RED,
        "#7F1D1D",
    )
    _draw_box(
        ax,
        0.84,
        0.16,
        0.25,
        0.16,
        f"{(1-c)*(1-p_ok)*100:.1f} DUD / FIZZLED",
        "Buggy backdoor; no harm.\nGame simply continues.",
        "#F1F5F9",
        C_GREY,
        "#334155",
    )

    # Summary strip at bottom left
    ax.text(
        0.02,
        0.16,
        "Only 2 outcomes end the game:\n"
        f"• Blue wins: {c*100:.1f} / 100\n"
        f"• Red wins:  {s*100:.1f} / 100\n"
        f"• Duds ({(1-c)*(1-p_ok)*100:.1f}) don't end the game.",
        ha="left",
        va="center",
        fontsize=10.5,
        color=C_DARK,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#F8FAFC", edgecolor="#94A3B8", lw=1.4),
    )

    fig.tight_layout(pad=1.2)
    save_fig(fig, "fig4_attack_tree.png")


def make_fig5() -> None:
    """fig5_safety_race.png: Line 7: safety = c / (c + s) -> 0.647 (The Race)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIG_SIZE, dpi=DPI, width_ratios=[1.0, 1.15])

    dud = (1.0 - c) * (1.0 - p_ok)
    decisive = c + s

    # Left panel: All 100 attacks
    labels1 = ["Caught\n(Blue Wins)", "Succeeded\n(Red Wins)", "Dud / Fizzled\n(Game Continues)"]
    vals1 = [c * 100, s * 100, dud * 100]
    cols1 = [C_GREEN, C_RED, C_GREY_LIGHT]
    bars1 = ax1.bar(labels1, vals1, color=cols1, edgecolor=[C_GREEN, C_RED, C_GREY], linewidth=1.8, width=0.55)
    for b, v in zip(bars1, vals1):
        ax1.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=12, fontweight="bold", color=C_DARK)
    ax1.set_ylim(0, 62)
    ax1.set_ylabel("Percentage of All Attacks (%)", fontsize=11.5, fontweight="bold")
    ax1.set_title("Step A: All 100 Attacks\n(Duds do not end the game)", fontsize=13, fontweight="bold", pad=12, color=C_DARK)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # Right panel: Decisive race only (c + s = 73.9%)
    red_share = s / decisive
    ax2.barh(["Game-Ending\nRace"], [safety * 100], color=C_GREEN, height=0.38, label=f"Blue Wins First: {safety*100:.1f}%")
    ax2.barh(["Game-Ending\nRace"], [red_share * 100], left=[safety * 100], color=C_RED, height=0.38, label=f"Red Wins First: {red_share*100:.1f}%")

    ax2.text(safety * 50, 0, f"BLUE TEAM WINS\n{c*100:.1f} / {decisive*100:.1f}\n= {safety*100:.1f}%", ha="center", va="center", fontsize=13, fontweight="bold", color="white")
    ax2.text(safety * 100 + red_share * 50, 0, f"RED WINS\n{s*100:.1f} / {decisive*100:.1f}\n= {red_share*100:.1f}%", ha="center", va="center", fontsize=12, fontweight="bold", color="white")

    formula_text = (
        "Why divide by (c + s)?\n"
        "The first decisive attack decides the winner.\n"
        f"Decisive attacks = {c:.3f} + {s:.3f} = {decisive:.3f} ({decisive*100:.1f}%)\n\n"
        f"Safety = c / (c + s) = {c:.3f} / {decisive:.3f} = {safety:.3f} ({safety*100:.1f}%)"
    )
    ax2.text(
        50,
        -0.42,
        formula_text,
        ha="center",
        va="top",
        fontsize=11,
        color=C_DARK,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#F8FAFC", edgecolor=C_BLUE, lw=1.5),
    )

    ax2.set_xlim(0, 100)
    ax2.set_ylim(-0.85, 0.55)
    ax2.set_xlabel("Share of Game-Ending (Decisive) Outcomes (%)", fontsize=11.5, fontweight="bold")
    ax2.set_title(f"Step B: The Race Among {decisive*100:.1f} Decisive Outcomes\nSafety = c / (c + s) = {safety:.3f}", fontsize=13, fontweight="bold", pad=12, color=C_DARK)
    ax2.legend(loc="upper center", ncol=2, frameon=True, facecolor="white", fontsize=10.5)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.spines["left"].set_visible(False)
    ax2.set_yticks([])

    fig.suptitle(
        f"Line 7: Overall Safety = c / (c + s) = {safety:.3f} (64.7%)",
        fontsize=15,
        fontweight="bold",
        y=0.98,
        color=C_DARK,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94], pad=1.6)
    save_fig(fig, "fig5_safety_race.png")


def make_fig6() -> None:
    """fig6_sensitivity_sep.png: What Happens When the Monitor Improves (sep = 1, 2, 3)."""
    fig, axes = plt.subplots(3, 1, figsize=FIG_SIZE, dpi=DPI, sharex=True)
    x = np.linspace(-3.5, 7.6, 900)
    y_hon = norm_pdf(x, 0.0, 1.0)

    for ax, sp in zip(axes, (1.0, 2.0, 3.0)):
        c_i = 1.0 - nd.cdf(t - sp)
        s_i = (1.0 - c_i) * p_ok
        saf_i = c_i / (c_i + s_i)
        y_att = norm_pdf(x, sp, 1.0)

        ax.plot(x, y_hon, color=C_BLUE, linestyle="--", linewidth=1.8, label="Honest N(0, 1)")
        ax.plot(x, y_att, color=C_RED, linewidth=2.2, label=f"Attack N({sp:.1f}, 1)")
        ax.fill_between(x[x <= t], 0, y_att[x <= t], color=C_AMBER_LIGHT, alpha=0.70)
        ax.fill_between(x[x >= t], 0, y_att[x >= t], color=C_GREEN_LIGHT, alpha=0.80)
        ax.axvline(t, color=C_DARK, linestyle="--", linewidth=2.0)

        badge = f"sep = {sp:.1f}\nCaught c = {c_i*100:.1f}%\nSafety = {saf_i*100:.1f}%"
        ax.text(
            7.35,
            0.39,
            badge,
            ha="right",
            va="top",
            fontsize=11,
            fontweight="bold",
            color=C_DARK,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#F8FAFC", edgecolor=C_DARK, lw=1.2),
        )
        ax.set_ylim(0, 0.46)
        ax.set_ylabel("Density", fontsize=10.5, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        if sp == 1.0:
            ax.legend(loc="upper left", fontsize=9.5, frameon=True, facecolor="white")
            ax.text(t + 0.10, 0.41, f"Alarm t = {t:.3f}", fontsize=10, fontweight="bold", color=C_DARK)

    axes[-1].set_xlim(-3.5, 7.6)
    axes[-1].set_xlabel("Monitor Suspicion Score (Fixed 2% Audit Budget -> Fixed Threshold t = 2.054)", fontsize=11.5, fontweight="bold", labelpad=8)
    fig.suptitle(
        "Big Takeaway: Pushing the Curves Apart (Monitor Quality sep) Dramatically Boosts Safety",
        fontsize=14.5,
        fontweight="bold",
        y=0.98,
        color=C_DARK,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95], pad=1.2)
    save_fig(fig, "fig6_sensitivity_sep.png")


def build_pptx() -> None:
    """Build 8-slide 16:9 PowerPoint deck in docs/AI_Control_Statistics_Walkthrough.pptx."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    NAVY = RGBColor(15, 23, 42)
    SLATE = RGBColor(51, 65, 85)
    BLUE = RGBColor(37, 99, 235)
    LIGHT_BG = RGBColor(248, 250, 252)
    WHITE = RGBColor(255, 255, 255)
    BORDER = RGBColor(203, 213, 225)

    def add_header(slide, title: str, subtitle: str) -> None:
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.05))
        bar.fill.solid()
        bar.fill.fore_color.rgb = NAVY
        bar.line.fill.background()

        tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.12), Inches(12.3), Inches(0.85))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(24)
        p1.font.bold = True
        p1.font.color.rgb = WHITE
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(13)
        p2.font.color.rgb = RGBColor(147, 197, 253)

    def add_image_slide(title: str, subtitle: str, img_name: str, bullets: list[str]) -> None:
        slide = prs.slides.add_slide(blank)
        add_header(slide, title, subtitle)

        # Left takeaway card
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.45), Inches(1.3), Inches(3.55), Inches(5.8))
        card.fill.solid()
        card.fill.fore_color.rgb = LIGHT_BG
        card.line.color.rgb = BORDER

        tb = slide.shapes.add_textbox(Inches(0.62), Inches(1.5), Inches(3.2), Inches(5.4))
        tf = tb.text_frame
        tf.word_wrap = True
        first = True
        for b in bullets:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.text = f"• {b}"
            p.font.size = Pt(14)
            p.font.color.rgb = SLATE
            p.space_after = Pt(12)

        # Right figure
        slide.shapes.add_picture(str(FIG_DIR_PROJ / img_name), Inches(4.2), Inches(1.25), width=Inches(8.75))

    # Slide 1: Title & NDI Analogy
    s1 = prs.slides.add_slide(blank)
    bg = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(11.7), Inches(1.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "AI Control Statistics Walkthrough"
    p.font.size = Pt(38)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p2 = tf.add_paragraph()
    p2.text = "Understanding the 7-Line NormalDist Safety Calculation with Visual Figures"
    p2.font.size = Pt(19)
    p2.font.color.rgb = RGBColor(147, 197, 253)

    # Analogy box + code box
    left_box = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.7), Inches(5.7), Inches(4.0))
    left_box.fill.solid()
    left_box.fill.fore_color.rgb = RGBColor(30, 41, 59)
    left_box.line.color.rgb = BLUE
    ltf = left_box.text_frame
    ltf.word_wrap = True
    ltf.margin_left = Inches(0.25)
    ltf.margin_top = Inches(0.25)
    lp0 = ltf.paragraphs[0]
    lp0.text = "Aircraft NDI Analogy (Fastener Hole Inspection)"
    lp0.font.size = Pt(17)
    lp0.font.bold = True
    lp0.font.color.rgb = RGBColor(253, 186, 116)
    for item in [
        "Honest code = good hole (background noise centered at 0)",
        "Backdoored code = cracked hole (signal centered at +2.0)",
        "Monitor score = eddy-current voltage reading",
        "Audit budget (2%) = expensive human teardown limit",
        "Safety = chance crack is caught before failure",
    ]:
        lp = ltf.add_paragraph()
        lp.text = f"• {item}"
        lp.font.size = Pt(14)
        lp.font.color.rgb = WHITE
        lp.space_after = Pt(8)

    right_box = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(2.7), Inches(5.7), Inches(4.0))
    right_box.fill.solid()
    right_box.fill.fore_color.rgb = RGBColor(30, 41, 59)
    right_box.line.color.rgb = RGBColor(22, 163, 74)
    rtf = right_box.text_frame
    rtf.word_wrap = True
    rtf.margin_left = Inches(0.25)
    rtf.margin_top = Inches(0.25)
    rp0 = rtf.paragraphs[0]
    rp0.text = "The 7 Lines We Are Explaining"
    rp0.font.size = Pt(17)
    rp0.font.bold = True
    rp0.font.color.rgb = RGBColor(134, 239, 172)
    code_lines = [
        "from statistics import NormalDist",
        "nd = NormalDist()               # mean 0, std 1",
        "budget, sep, p_ok = 0.02, 2.0, 0.5",
        "t = nd.inv_cdf(1 - budget)      # -> 2.054",
        "c = 1 - nd.cdf(t - sep)         # -> 0.478",
        "s = (1 - c) * p_ok              # -> 0.261",
        "print(t, c, s, c / (c + s))     # -> 0.647",
    ]
    for cl in code_lines:
        rp = rtf.add_paragraph()
        rp.text = cl
        rp.font.name = "Consolas"
        rp.font.size = Pt(12.5)
        rp.font.color.rgb = RGBColor(226, 232, 240)
        rp.space_after = Pt(4)

    # Slides 2-7: Figures
    add_image_slide(
        "Slide 2: The Only Two Statistics Functions",
        "nd.cdf(x) turns a Score into a Left Area; nd.inv_cdf(p) turns a Left Area into a Cutoff Score",
        "fig1_cdf_vs_invcdf.png",
        [
            "Total area under the bell curve = 1.00 (100% of cases).",
            "nd.cdf(x) ALWAYS measures area to the LEFT of x.",
            "Because we audit high scores on the RIGHT, Right Area = 1 - nd.cdf(x).",
            "nd.inv_cdf(p) runs backwards: give it a left area p, get the score x.",
        ],
    )
    add_image_slide(
        "Slide 3: Line 4 — Finding the Alarm Threshold (t)",
        "t = nd.inv_cdf(1 - budget) -> 2.054",
        "fig2_threshold_t.png",
        [
            "budget = 0.02 means humans can audit only the top 2% of honest scores.",
            "If 2% is to the RIGHT of t, then 98% (1 - 0.02 = 0.98) is to the LEFT.",
            "nd.inv_cdf(0.98) = 2.054.",
            "Out of 1,000 honest tasks, ~20 score above 2.054 and trigger an audit.",
        ],
    )
    add_image_slide(
        "Slide 4: Line 5 — How Many Attacks Are Caught (c)",
        "c = 1 - nd.cdf(t - sep) -> 0.478 (47.8%)",
        "fig3_caught_c.png",
        [
            "Attack scores center at sep = 2.0; alarm stays fixed at t = 2.054.",
            "nd only knows curves centered at 0, so we shift both by -sep.",
            "Threshold sits at t - sep = 0.054 above the attack curve center.",
            "Half of a bell curve is above its center; just above it, 47.8% are caught.",
        ],
    )
    add_image_slide(
        "Slide 5: Line 6 — Unaudited Attacks (s)",
        "s = (1 - c) * p_ok -> 0.261 (26.1%)",
        "fig4_attack_tree.png",
        [
            "Out of 100 attacks, 47.8 are audited and caught (Blue wins immediately).",
            "The remaining 52.2 (1 - c) slip past human inspection.",
            "Half of slipped backdoors fail/fizzle; p_ok = 0.5 succeed -> 26.1.",
            "26.1 duds do nothing; the game simply keeps going.",
        ],
    )
    add_image_slide(
        "Slide 6: Line 7 — Why Safety is c / (c + s) = 64.7%",
        "A race between the first Caught attack (c) and first Succeeded attack (s)",
        "fig5_safety_race.png",
        [
            "Duds don't end the game, so only decisive outcomes (c + s) matter.",
            "Decisive probability = 0.478 + 0.261 = 0.739 (73.9%).",
            "Blue's share of decisive outcomes = 0.478 / 0.739 = 0.647 (64.7%).",
            "Red's share = 0.261 / 0.739 = 0.353 (35.3%).",
        ],
    )
    add_image_slide(
        "Slide 7: Why Monitor Quality (sep) Matters Most",
        "Improving separation from 1.0 to 3.0 pushes safety from 25.5% to 90.6%",
        "fig6_sensitivity_sep.png",
        [
            "With budget fixed at 2%, threshold t stays pinned at 2.054.",
            "sep = 1.0 (weak monitor): only 14.6% caught -> 25.5% safety.",
            "sep = 2.0 (medium monitor): 47.8% caught -> 64.7% safety.",
            "sep = 3.0 (strong monitor): 82.8% caught -> 90.6% safety.",
        ],
    )

    # Slide 8: Summary Cheat-Sheet Table
    s8 = prs.slides.add_slide(blank)
    add_header(s8, "Slide 8: Complete 7-Line Code Cheat-Sheet", "Every variable, plain-English meaning, NDI analogy, and exact value")

    rows_data = [
        ["Code", "Plain-English Meaning", "NDI Engineering Analogy", "Value"],
        ["budget = 0.02", "Fraction of honest work humans can audit", "Teardown inspection capacity (2%)", "0.020"],
        ["sep = 2.0", "Gap between attack and honest mean scores", "Flaw signal-to-noise separation (d')", "2.000"],
        ["p_ok = 0.5", "Chance an unaudited attack actually works", "Chance an unfound crack causes failure", "0.500"],
        ["t = nd.inv_cdf(1 - budget)", "Score leaving 98% of honest work below", "Eddy-current alarm threshold", f"{t:.3f}"],
        ["c = 1 - nd.cdf(t - sep)", "Fraction of attacks scoring >= t (caught)", "Probability of Detection (POD)", f"{c:.3f} (47.8%)"],
        ["s = (1 - c) * p_ok", "Fraction of attacks slipping past AND working", "Undetected flaw that causes failure", f"{s:.3f} (26.1%)"],
        ["c / (c + s)", "Chance Blue catches before Red succeeds", "Probability structure stays safe", f"{safety:.3f} (64.7%)"],
    ]

    table_shape = s8.shapes.add_table(len(rows_data), 4, Inches(0.5), Inches(1.35), Inches(12.3), Inches(5.6))
    table = table_shape.table
    col_widths = [Inches(2.8), Inches(4.1), Inches(3.8), Inches(1.6)]
    for i, w in enumerate(col_widths):
        table.columns[i].width = w

    for r_idx, row in enumerate(rows_data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.text = val
            if r_idx == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = BLUE
                p.font.bold = True
                p.font.size = Pt(13)
                p.font.color.rgb = WHITE
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE if r_idx % 2 == 1 else LIGHT_BG
                p.font.size = Pt(12.5)
                p.font.color.rgb = NAVY
                if c_idx == 0:
                    p.font.name = "Consolas"
                    p.font.bold = True
                if c_idx == 3:
                    p.alignment = PP_ALIGN.RIGHT
                    p.font.bold = True

    prs.save(str(PPTX_PATH))


def main() -> None:
    make_fig1()
    make_fig2()
    make_fig3()
    make_fig4()
    make_fig5()
    make_fig6()
    build_pptx()
    print(f"t={t:.4f}, c={c:.4f}, s={s:.4f}, safety={safety:.4f}")
    print(f"Saved PPTX to {PPTX_PATH}")


if __name__ == "__main__":
    main()
