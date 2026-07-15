"""
EPS V-curve sweep
Runs EpsGearboxSim.exe multiple times while varying --tmax, and plots the
steering torque vs. rack force (V-curve) along with other steady-state characteristics.
"""

import subprocess
import re
import sys
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# -- Configuration -------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT  = os.path.dirname(_SCRIPT_DIR)
EXE_PATH = os.path.join(_REPO_ROOT, "EpsGearboxSim.exe")

# Steering torque sweep range [Nm]
TH_MAX      = 8.0    # sweep upper limit
N_POINTS    = 50     # number of points
SIM_SPAN    = 5.0    # simulation time [s]
RAMP_DUR    = 2.0    # ramp time [s]

# -- Parsing -------------------------------------------------------------------
_RESULT_RE = re.compile(
    r"RESULT"
    r" torsion_ss=([0-9eE+\-.]+)"
    r" assist_ss=([0-9eE+\-.]+)"
    r" rack_force_ss=([0-9eE+\-.]+)"
    r" rack_disp_mm=([0-9eE+\-.]+)"
    r" iq_ref_ss=([0-9eE+\-.]+)"
)


def run_sim(tmax: float) -> dict | None:
    """Run EpsGearboxSim.exe once and return the steady-state quantities."""
    cmd = [
        EXE_PATH,
        "--tmax",  str(tmax),
        "--span",  str(SIM_SPAN),
        "--ramp",  str(RAMP_DUR),
        "--no_csv",
        "--quiet",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        m = _RESULT_RE.search(res.stdout)
        if m is None:
            print(f"  [WARN] RESULT line not found (tmax={tmax:.3f} Nm)")
            print(f"         stdout: {res.stdout.strip()!r}")
            return None
        return {
            "hand_torque":  tmax,
            "torsion_ss":   float(m.group(1)),
            "assist_ss":    float(m.group(2)),
            "rack_force_ss":float(m.group(3)),
            "rack_disp_mm": float(m.group(4)),
            "iq_ref_ss":    float(m.group(5)),
        }
    except FileNotFoundError:
        print(f"[ERROR] executable not found: {EXE_PATH}")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"  [WARN] timeout (tmax={tmax:.3f} Nm)")
        return None


def sweep() -> list[dict]:
    th_values = np.linspace(0.0, TH_MAX, N_POINTS)
    results = []
    for th in th_values:
        r = run_sim(th)
        if r is None:
            continue
        results.append(r)
        print(f"  Th={th:5.2f} Nm  ->  "
              f"torsion={r['torsion_ss']:6.3f} Nm  "
              f"rack_force={r['rack_force_ss']:8.1f} N  "
              f"iq_ref={r['iq_ref_ss']:6.2f} A")
    return results


# -- Plotting ------------------------------------------------------------------
def plot_vcurve(results: list[dict]):
    th  = np.array([r["hand_torque"]   for r in results])
    fr  = np.array([r["rack_force_ss"] for r in results])
    tor = np.array([r["torsion_ss"]    for r in results])
    iq  = np.array([r["iq_ref_ss"]     for r in results])
    rd  = np.array([r["rack_disp_mm"]  for r in results])

    # Also generate the symmetric negative direction
    th_full  = np.concatenate([-th[::-1], th])
    fr_full  = np.concatenate([-fr[::-1], fr])
    tor_full = np.concatenate([-tor[::-1], tor])
    iq_full  = np.concatenate([-iq[::-1], iq])
    rd_full  = np.concatenate([-rd[::-1], rd])

    # -- Style ----------------------------------------------------------------
    bg     = "#1a1a1a"
    panel  = "#252525"
    grid_c = "#2e2e2e"
    spine  = "#444444"
    tc     = "#cccccc"

    matplotlib.rcParams["font.family"] = "Yu Gothic"
    matplotlib.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), facecolor=bg)
    fig.suptitle("EPS V-curve (steering torque vs. rack force) sweep results",
                 color=tc, fontsize=13, y=0.98)

    def _style(ax, title, xlabel, ylabel):
        ax.set_facecolor(bg)
        for sp in ax.spines.values():
            sp.set_color(spine)
        ax.tick_params(colors=tc, labelsize=9)
        ax.grid(True, color=grid_c, lw=0.6, alpha=0.9, zorder=0)
        ax.set_title(title, color=tc, fontsize=11, pad=6)
        ax.set_xlabel(xlabel, color=tc, fontsize=10)
        ax.set_ylabel(ylabel, color=tc, fontsize=10)
        ax.axhline(0, color=spine, lw=0.8)
        ax.axvline(0, color=spine, lw=0.8)

    # - V-curve: rack force vs. steering torque -
    ax = axes[0, 0]
    ax.plot(th_full, fr_full, color="#3498db", lw=2.5,
            solid_capstyle="round", label="rack force [N]", zorder=3)
    _style(ax, "V-curve: rack force vs. steering torque",
           "steering torque Th [Nm]", "rack force [N]")
    ax.legend(fontsize=9, facecolor=panel, edgecolor=spine, labelcolor=tc)

    # - Torque sensor value vs. steering torque -
    ax = axes[0, 1]
    ax.plot(th_full, tor_full, color="#e74c3c", lw=2.0,
            solid_capstyle="round", label="torque sensor Tsensor [Nm]", zorder=3)
    _style(ax, "Torque sensor vs. steering torque",
           "steering torque Th [Nm]", "torque sensor value [Nm]")
    ax.legend(fontsize=9, facecolor=panel, edgecolor=spine, labelcolor=tc)

    # - Iq reference vs. steering torque -
    ax = axes[1, 0]
    ax.plot(th_full, iq_full, color="#2ecc71", lw=2.0,
            solid_capstyle="round", label="Iq reference [A]", zorder=3)
    _style(ax, "Assist map: Iq reference vs. steering torque",
           "steering torque Th [Nm]", "Iq reference [A]")
    ax.legend(fontsize=9, facecolor=panel, edgecolor=spine, labelcolor=tc)

    # - Rack displacement vs. steering torque -
    ax = axes[1, 1]
    ax.plot(th_full, rd_full, color="#f39c12", lw=2.0,
            solid_capstyle="round", label="rack displacement [mm]", zorder=3)
    _style(ax, "Rack displacement vs. steering torque",
           "steering torque Th [Nm]", "rack displacement [mm]")
    ax.legend(fontsize=9, facecolor=panel, edgecolor=spine, labelcolor=tc)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out_path = os.path.join(_REPO_ROOT, "data", "eps_vcurve.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=bg)
    print(f"\nPNG saved: {out_path}")
    plt.show()


# -- Simple V-curve figure (right-side style of eps_model.png) ------------------
def plot_schematic_vcurve(results: list[dict]):
    """
    Generate and save a V-curve figure with arrow axes, a white background, and
    minimal labels, like the right side of eps_model.png.
    """
    matplotlib.rcParams["font.family"] = "Yu Gothic"
    matplotlib.rcParams["axes.unicode_minus"] = False

    th = np.array([r["hand_torque"]   for r in results])
    fr = np.array([r["rack_force_ss"] for r in results])

    # Make both arms positive to form the V shape (left arm = mirror of right arm)
    th_full   = np.concatenate([-th[::-1], th])
    fr_vcurve = np.concatenate([fr[::-1],  fr])

    fig, ax = plt.subplots(figsize=(5, 5), facecolor="white")
    ax.set_facecolor("white")

    ax.plot(th_full, fr_vcurve, color="#4a9fd4", lw=2.5,
            solid_capstyle="round", zorder=3)

    # Hide the default frame and ticks
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])

    # Axis range (with margins)
    x_range = th_full.max() - th_full.min()
    y_range = fr_vcurve.max() - fr_vcurve.min()
    xpad = x_range * 0.18
    ypad = y_range * 0.15

    x_lo = th_full.min() - xpad
    x_hi = th_full.max() + xpad
    y_lo = fr_vcurve.min() - y_range * 0.12
    y_hi = fr_vcurve.max() + ypad

    ax.set_xlim(x_lo, x_hi)
    ax.set_ylim(y_lo, y_hi)

    aw = dict(arrowstyle="-|>", color="black", lw=1.3, mutation_scale=13)

    # Horizontal axis (bidirectional arrow / y=0)
    ax.plot([x_lo, x_hi], [0, 0], color="black", lw=1.3, zorder=2)
    ax.annotate("", xy=(x_hi, 0), xytext=(x_hi - xpad * 0.6, 0),
                arrowprops=aw, zorder=4)
    ax.annotate("", xy=(x_lo, 0), xytext=(x_lo + xpad * 0.6, 0),
                arrowprops=aw, zorder=4)

    # Vertical axis (upward arrow / x=0)
    ax.plot([0, 0], [y_lo, y_hi], color="black", lw=1.3, zorder=2)
    ax.annotate("", xy=(0, y_hi), xytext=(0, y_hi - ypad * 0.6),
                arrowprops=aw, zorder=4)

    # Axis labels
    ax.text(x_hi - xpad * 0.05, y_lo + y_range * 0.03,
            "steering torque", ha="right", va="top",
            fontsize=12, color="#222222")
    ax.text(xpad * 0.3, y_hi,
            "rack force", ha="left", va="top",
            fontsize=12, color="red")

    fig.tight_layout(pad=0.5)
    out_path = os.path.join(_REPO_ROOT, "data", "eps_vcurve_schematic.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"Schematic PNG saved: {out_path}")
    plt.show()


# -- Entry point ---------------------------------------------------------------
def main():
    if not os.path.exists(EXE_PATH):
        print(f"[ERROR] executable not found: {EXE_PATH}")
        print("  Build it with CMake first.")
        sys.exit(1)

    print("EPS V-curve sweep")
    print(f"  EXE         : {EXE_PATH}")
    print(f"  Th range    : 0 ~ {TH_MAX} Nm  ({N_POINTS} points)")
    print(f"  sim span    : {SIM_SPAN} s  (ramp {RAMP_DUR} s)")
    print()

    results = sweep()
    if not results:
        print("[ERROR] no valid results were obtained.")
        sys.exit(1)

    print(f"\n{len(results)} points collected. Displaying figure...")
    plot_vcurve(results)
    plot_schematic_vcurve(results)


if __name__ == "__main__":
    main()
