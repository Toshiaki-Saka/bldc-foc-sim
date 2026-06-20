"""
compare_decoupling_transient.py
================================
dq 軸非干渉制御 (decoupling control) の効果を「過渡応答」で比較するツール。

非干渉制御は dq 軸間の干渉項 (omega_e * L * i) を打ち消す制御である。
干渉項は定常状態 (とくに id ≈ 0) ではほとんど顔を出さないため、
steady-state を見るだけでは効果がほぼ見えない。

そこで本スクリプトは `--iq_step` オプションを使い、シミュレーション途中で
q 軸電流指令をステップ的に変化させて「過渡」を強制的に発生させる。
その過渡区間を decoupling ON / OFF で重ね描きすることで、

  - q 軸電流 iq の整定の速さ・オーバーシュート
  - d 軸電流 id への漏れ込み (cross-coupling = 軸間干渉そのもの)
  - 電磁トルク Te の乱れ

がどう変わるかを可視化する。

使い方:
    python scripts/compare_decoupling_transient.py
    python scripts/compare_decoupling_transient.py --span 1.0 --step_time 0.5 \
        --iq_before 85 --iq_after 30
    python scripts/compare_decoupling_transient.py --no-show

CLI 引数:
    --exe        PATH  実行ファイルのパス (既定: BrushlessDCMotor を自動探索)
    --span       SEC   シミュレーション時間 [s]            (既定 1.0)
    --step_time  SEC   q 軸指令をステップさせる時刻 [s]     (既定 0.5)
    --iq_before  A     ステップ前の q 軸電流指令 [A]        (既定 85)
    --iq_after   A     ステップ後の q 軸電流指令 [A]        (既定 30)
    --tload      NM    負荷トルク [Nm]                      (既定 4.3)
    --out        PATH  グラフ画像の保存先
    --no-show          画面表示せず画像保存のみ

注意:
    このスクリプトは実行ファイルが `--iq_step <time> <iq>` および
    `--decoupling` オプションに対応していることを前提とする。
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

# 比較する 2 条件: (ラベル, decoupling フラグ, 色)
CONDITIONS = [
    ("decoupling OFF", False, "#c0392b"),
    ("decoupling ON",  True,  "#27ae60"),
]

# 表示する波形: (CSV列名, タイトル, y軸ラベル)
SIGNALS = [
    ("iq", "q-axis current  (reference tracking)", "iq [A]"),
    ("id", "d-axis current  (cross-coupling leakage)", "id [A]"),
    ("Te", "electromagnetic torque", "Te [Nm]"),
    ("omega", "angular velocity", "omega [rad/s]"),
]


def find_executable() -> str:
    """ビルド済み実行ファイルを探索する。"""
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


def run_simulation(exe, span, tload, step_time, iq_before, iq_after, decoupling):
    """1 条件分のシミュレーションを実行し、CSV を列ごとの配列で返す。"""
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    tmp.close()
    csv_path = tmp.name

    cmd = [
        exe,
        "--span", str(span),
        "--iq_ref", str(iq_before),
        "--tload", str(tload),
        "--iq_step", str(step_time), str(iq_after),
        "--csv_out", csv_path,
        "--quiet",
    ]
    if decoupling:
        cmd.append("--decoupling")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(f"ERROR: simulation failed (decoupling={decoupling})")

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
    return data


def main():
    ap = argparse.ArgumentParser(
        description="Evaluate dq decoupling control via a q-axis current step transient"
    )
    ap.add_argument("--exe", default=None, help="path to BrushlessDCMotor executable")
    ap.add_argument("--span", type=float, default=1.0, help="simulation time [s]")
    ap.add_argument("--step_time", type=float, default=0.5,
                    help="time at which the q-axis reference steps [s]")
    ap.add_argument("--iq_before", type=float, default=85.0,
                    help="q-axis current reference before the step [A]")
    ap.add_argument("--iq_after", type=float, default=30.0,
                    help="q-axis current reference after the step [A]")
    ap.add_argument("--tload", type=float, default=4.3, help="load torque [Nm]")
    ap.add_argument("--out", default="data/compare_decoupling_transient.png",
                    help="output image path")
    ap.add_argument("--no-show", action="store_true",
                    help="save image without opening a window")
    args = ap.parse_args()

    if args.no_show:
        matplotlib.use("Agg")

    exe = args.exe or find_executable()
    print(f"Executable : {exe}")
    print(f"Scenario   : iq {args.iq_before} A -> {args.iq_after} A "
          f"step at t = {args.step_time} s   (span {args.span} s, tload {args.tload} Nm)")
    print()

    # decoupling OFF / ON の 2 条件を実行
    runs = []
    for label, decoupling, color in CONDITIONS:
        data = run_simulation(
            exe, args.span, args.tload,
            args.step_time, args.iq_before, args.iq_after,
            decoupling,
        )
        runs.append((label, color, data))
        print(f"  [{label}] simulation done ({len(data.get('iq', []))} steps)")

    # 波形を 2x2 で重ね描き
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    axes = axes.ravel()

    for ax, (col, title, ylabel) in zip(axes, SIGNALS):
        for label, color, data in runs:
            if col not in data or not data[col]:
                continue
            y = data[col]
            t = [i * RESOLUTION for i in range(len(y))]
            ax.plot(t, y, label=label, color=color, lw=1.4)
        # ステップ時刻に縦線
        ax.axvline(args.step_time, color="#34495e", ls="--", lw=1,
                   alpha=0.7, label=f"step @ {args.step_time}s")
        ax.set_title(title)
        ax.set_xlabel("time [s]")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="best")

    fig.suptitle(
        "dq decoupling control - transient response to a q-axis current step",
        fontsize=13,
    )
    fig.tight_layout()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fig.savefig(args.out, dpi=120)
    print(f"\nSaved comparison figure to: {args.out}")
    print("Note: focus on the 'id' panel and the transient right after the step.")
    print("      The dq cross-coupling term is omega_e * L * i; its magnitude")
    print("      depends on speed, inductance and the size of the current step,")
    print("      so the visible ON/OFF difference scales with the scenario.")

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()
