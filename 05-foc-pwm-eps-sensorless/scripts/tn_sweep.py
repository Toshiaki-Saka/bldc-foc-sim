"""
TIN Characteristics Sweep
Runs the C++ simulation multiple times while varying the parameter (iq_ref) and
plots the T-n / I-T / P-T / η-T characteristic curves.
"""

import subprocess
import re
import sys
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ── Configuration ─────────────────────────────────────────────────────────────
# Path to the executable (assumed to be in the same directory as this script)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXE_PATH = os.path.join(_SCRIPT_DIR, "BrushlessDCMotor.exe")

# Fixed motor parameters (must match main.cpp)
KT   = 3.5 / 85.0                        # Nm/A
KE   = 3.5 / 85.0                        # V/(rad/s)
R    = 0.015                              # Ohm
B    = 1.0e-2 / (2.0 * np.pi)            # Nm/(rad/s)
V_DC = 400.0                              # assumed DC bus voltage [V] (rough estimate for efficiency calc)

# iq_ref values to sweep [A] (FOC q-axis current command)
IQ_REF_LIST = [20.0, 40.0, 60.0, 85.0]

# Number of T_load points to sample for each iq_ref
N_TLOAD_POINTS = 12

# Simulation span [s] (long enough to reach steady state)
SIM_SPAN = 5.0

# ── Color palette ─────────────────────────────────────────────────────────────
COLORS = ["#FFB800", "#22CC55", "#FF5577", "#4499FF",
          "#AA44FF", "#FF8833", "#00CCCC", "#FF4444"]

# ── Run & parse ──────────────────────────────────────────────────────────────
_RESULT_RE = re.compile(
    r"RESULT omega_ss=([0-9eE+\-.]+)"
    r" iq_ss=([0-9eE+\-.]+)"
    r" id_ss=([0-9eE+\-.]+)"
    r" tload=([0-9eE+\-.]+)"
    r" te_ss=([0-9eE+\-.]+)"
)


def run_sim(iq_ref: float, tload: float) -> dict | None:
    """Run the C++ simulation once and return the steady-state quantities."""
    cmd = [
        EXE_PATH,
        "--iq_ref", str(iq_ref),
        "--tload",  str(tload),
        "--span",   str(SIM_SPAN),
        "--no_csv",
        "--quiet",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        m = _RESULT_RE.search(result.stdout)
        if m is None:
            print(f"  [WARN] RESULT line not found (iq={iq_ref}, tl={tload})")
            print(f"         stdout: {result.stdout.strip()}")
            return None
        return {
            "omega_ss": float(m.group(1)),
            "iq_ss":    float(m.group(2)),
            "id_ss":    float(m.group(3)),
            "tload":    float(m.group(4)),
            "te_ss":    float(m.group(5)),
        }
    except FileNotFoundError:
        print(f"[ERROR] Executable not found: {EXE_PATH}")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"  [WARN] Timeout (iq={iq_ref}, tl={tload})")
        return None


def sweep_iq(iq_ref: float, color: str) -> dict:
    """Fix iq_ref, sweep T_load, and return arrays of each physical quantity."""
    te_max = KT * iq_ref          # theoretical maximum torque [Nm]
    tload_values = np.linspace(0.0, te_max * 0.98, N_TLOAD_POINTS)

    T_list, N_list, I_list, P_list = [], [], [], []

    print(f"  iq_ref = {iq_ref:.1f} A  (Te_max = {te_max:.4f} Nm)")
    for tl in tload_values:
        r = run_sim(iq_ref, tl)
        if r is None:
            continue
        omega = r["omega_ss"]
        iq    = r["iq_ss"]
        id_   = r["id_ss"]
        te    = r["te_ss"]

        n_rpm = omega * 60.0 / (2.0 * np.pi)
        i_rms = np.sqrt(iq**2 + id_**2)
        p_out = te * omega if omega > 0 else 0.0

        T_list.append(te)
        N_list.append(n_rpm)
        I_list.append(i_rms)
        P_list.append(p_out)
        print(f"    tl={tl:6.3f} Nm  ->  "
              f"omega={omega:8.2f} rad/s  N={n_rpm:8.1f} rpm  "
              f"I={i_rms:6.2f} A  P={p_out:7.2f} W")

    T = np.array(T_list)
    N = np.array(N_list)
    I = np.array(I_list)
    P = np.array(P_list)

    # Efficiency (rough estimate: Pout / (V_dc * I_rms) x100)
    pin = V_DC * I
    eta = np.where(pin > 1e-6, np.clip(P / pin * 100.0, 0.0, 100.0), 0.0)

    return {"iq_ref": iq_ref, "T": T, "N": N, "I": I, "P": P, "eta": eta, "color": color}


# ── Plot ──────────────────────────────────────────────────────────────────────
_LINE_STYLES = ["-", "--", "-.", ":"]

# (key, ylabel, peak_marker, title)
_PLOT_DEFS = [
    ("N",   "SPEED  n  (r/min)",  False, "T-n Characteristics"),
    ("I",   "CURRENT  I  (A)",    False, "I-T Characteristics"),
    ("P",   "OUTPUT  P  (W)",     True,  "P-T Characteristics"),
    ("eta", "EFFICIENCY  η  (%)", True,  "η-T Characteristics"),
]
_METRIC_COLOR = {"N": "#4499FF", "I": "#22CC55", "P": "#FF5577", "eta": "#FFB800"}


def plot_tin(results: list[dict]):
    t_max_mNm = max(res["T"].max() * 1000.0 for res in results if len(res["T"]) > 0)

    bg     = "#1a1a1a"
    panel  = "#252525"
    grid_c = "#2e2e2e"
    spine  = "#444444"
    text_c = "#cccccc"

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), facecolor=bg)
    fig.suptitle("FOC Motor Characteristics Sweep", color=text_c, fontsize=13, y=0.98)
    axes_flat = axes.flatten()

    for ax_idx, (key, ylabel, peak_marker, title) in enumerate(_PLOT_DEFS):
        ax = axes_flat[ax_idx]
        color = _METRIC_COLOR[key]

        ax.set_facecolor(bg)
        for sp in ax.spines.values():
            sp.set_color(spine)
        ax.tick_params(colors=text_c, labelsize=9)
        ax.grid(True, color=grid_c, lw=0.6, alpha=0.9, zorder=0)
        ax.set_title(title, color=text_c, fontsize=11, pad=6)

        for ri, res in enumerate(results):
            if len(res["T"]) == 0:
                continue
            T_mNm = res["T"] * 1000.0
            vals  = res[key]
            ls    = _LINE_STYLES[ri % len(_LINE_STYLES)]
            ax.plot(T_mNm, vals, color=color, lw=2.0, ls=ls,
                    label=f"iq* = {res['iq_ref']:.0f} A",
                    solid_capstyle="round", zorder=3)
            if peak_marker and len(vals) > 0:
                idx = int(np.argmax(vals))
                ax.plot(T_mNm[idx], vals[idx], "o", color=color,
                        ms=6, zorder=5, mew=1.2, mec="white")

        ax.set_xlabel("TORQUE  T  (mN·m)", color=text_c, fontsize=10)
        ax.set_ylabel(ylabel, color=text_c, fontsize=10)
        ax.set_xlim(0, t_max_mNm * 1.05)
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%g"))
        ax.legend(fontsize=8, loc="best",
                  facecolor=panel, edgecolor=spine, labelcolor=text_c)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    if not os.path.exists(EXE_PATH):
        print(f"[ERROR] Executable not found: {EXE_PATH}")
        print("  Build with CMake first.")
        sys.exit(1)

    print(f"BrushlessDCMotor TIN Sweep")
    print(f"  EXE        : {EXE_PATH}")
    print(f"  iq_ref vals: {IQ_REF_LIST}")
    print(f"  T_load pts : {N_TLOAD_POINTS} points/curve")
    print(f"  Sim span   : {SIM_SPAN} s")
    print()

    results = []
    for iq_ref, color in zip(IQ_REF_LIST, COLORS):
        res = sweep_iq(iq_ref, color)
        results.append(res)
        print()

    print("Displaying plot...")
    plot_tin(results)


if __name__ == "__main__":
    main()
