"""
compare_modulation.py
=====================
Tool to compare the waveform differences between midpoint (min-max) modulation
and dq-axis decoupling control being ON/OFF.

It runs the same simulation under the following 4 conditions and overlays the
iq / Te / omega / id waveforms so the effect of each feature can be checked visually.

    1. baseline      : midpoint OFF, decoupling OFF  (conventional behavior)
    2. midpoint      : midpoint ON,  decoupling OFF
    3. decoupling    : midpoint OFF, decoupling ON
    4. both          : midpoint ON,  decoupling ON

Usage:
    python scripts/compare_modulation.py
    python scripts/compare_modulation.py --span 2.0 --iq_ref 100
    python scripts/compare_modulation.py --exe ./BrushlessDCMotor --no-show

CLI arguments:
    --exe   PATH   path to the executable (default: auto-detect built BrushlessDCMotor)
    --span  SEC    simulation time [s]         (default 2.0)
    --iq_ref AMP   q-axis current reference [A] (default 85)
    --tload  NM    load torque [Nm]            (default 4.3)
    --out   PATH   output path for the figure image (default data/compare_modulation.png)
    --no-show      save the image only, without opening a window
"""

import argparse
import csv
import os
import subprocess
import sys
import tempfile

import matplotlib
import matplotlib.pyplot as plt

RESOLUTION = 0.00025  # 250 us / step

# The 4 conditions to compare: (label, midpoint, decoupling, color)
CONDITIONS = [
    ("baseline (both OFF)", False, False, "#7f8c8d"),
    ("midpoint ON",         True,  False, "#e74c3c"),
    ("decoupling ON",       False, True,  "#2980b9"),
    ("both ON",             True,  True,  "#27ae60"),
]

# Waveforms to display: (CSV column name, title, y-axis label)
SIGNALS = [
    ("iq",    "q-axis current",        "iq [A]"),
    ("Te",    "electromagnetic torque", "Te [Nm]"),
    ("omega", "angular velocity",       "omega [rad/s]"),
    ("id",    "d-axis current",         "id [A]"),
]


def find_executable() -> str:
    """Search for the built executable."""
    candidates = [
        "./BrushlessDCMotor",
        "./BrushlessDCMotor.exe",
        "./build/BrushlessDCMotor",
        "./build/Release/BrushlessDCMotor.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    sys.exit(
        "ERROR: BrushlessDCMotor executable not found.\n"
        "       Build the project first, or pass --exe PATH explicitly."
    )


def run_simulation(exe, span, iq_ref, tload, midpoint, decoupling):
    """Run the simulation for one condition, read the CSV, and return per-column arrays."""
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    tmp.close()
    csv_path = tmp.name

    cmd = [
        exe,
        "--span", str(span),
        "--iq_ref", str(iq_ref),
        "--tload", str(tload),
        "--csv_out", csv_path,
        "--quiet",
    ]
    if midpoint:
        cmd.append("--midpoint")
    if decoupling:
        cmd.append("--decoupling")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(f"ERROR: simulation failed (midpoint={midpoint}, decoupling={decoupling})")

    data = {}
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for name in reader.fieldnames:
            data[name] = []
        for row in reader:
            for name in reader.fieldnames:
                try:
                    data[name].append(float(row[name]))
                except (ValueError, KeyError):
                    pass

    os.unlink(csv_path)

    # Also grab the RESULT line (at the end of stdout)
    summary = ""
    for line in result.stdout.splitlines():
        if line.startswith("RESULT"):
            summary = line
    return data, summary


def main():
    ap = argparse.ArgumentParser(description="Compare mid-point modulation / decoupling ON-OFF")
    ap.add_argument("--exe", default=None, help="path to BrushlessDCMotor executable")
    ap.add_argument("--span", type=float, default=2.0, help="simulation time [s]")
    ap.add_argument("--iq_ref", type=float, default=85.0, help="q-axis current reference [A]")
    ap.add_argument("--tload", type=float, default=4.3, help="load torque [Nm]")
    ap.add_argument("--out", default="data/compare_modulation.png", help="output image path")
    ap.add_argument("--no-show", action="store_true", help="save image without opening a window")
    args = ap.parse_args()

    if args.no_show:
        matplotlib.use("Agg")

    exe = args.exe or find_executable()
    print(f"Executable : {exe}")
    print(f"Conditions : span={args.span}s, iq_ref={args.iq_ref}A, tload={args.tload}Nm")
    print()

    # Run all 4 conditions
    runs = []
    for label, midpoint, decoupling, color in CONDITIONS:
        data, summary = run_simulation(
            exe, args.span, args.iq_ref, args.tload, midpoint, decoupling
        )
        runs.append((label, color, data))
        print(f"  [{label:22s}] {summary}")

    # Overlay the waveforms in a 2x2 grid
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    axes = axes.ravel()

    for ax, (col, title, ylabel) in zip(axes, SIGNALS):
        for label, color, data in runs:
            if col not in data or not data[col]:
                continue
            y = data[col]
            t = [i * RESOLUTION for i in range(len(y))]
            ax.plot(t, y, label=label, color=color, lw=1.4)
        ax.set_title(title)
        ax.set_xlabel("time [s]")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="best")

    fig.suptitle(
        "Mid-point modulation / dq decoupling - ON/OFF comparison",
        fontsize=13,
    )
    fig.tight_layout()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fig.savefig(args.out, dpi=120)
    print(f"\nSaved comparison figure to: {args.out}")

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()
