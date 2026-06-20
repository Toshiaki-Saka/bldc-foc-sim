"""
EPS V字カーブ スイープ
--tmax を変化させながら EpsGearboxSim.exe を複数回実行し、
操舵トルク対ラック推力 (V字カーブ) ほか定常特性を描画する。
"""

import subprocess
import re
import sys
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ── 設定 ──────────────────────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT  = os.path.dirname(_SCRIPT_DIR)
EXE_PATH = os.path.join(_REPO_ROOT, "EpsGearboxSim.exe")

# 操舵トルク スイープ範囲 [Nm]
TH_MAX      = 8.0    # スイープ上限
N_POINTS    = 50     # 点数
SIM_SPAN    = 5.0    # シミュレーション時間 [s]
RAMP_DUR    = 2.0    # ランプ時間 [s]

# ── パース ────────────────────────────────────────────────────────────────────
_RESULT_RE = re.compile(
    r"RESULT"
    r" torsion_ss=([0-9eE+\-.]+)"
    r" assist_ss=([0-9eE+\-.]+)"
    r" rack_force_ss=([0-9eE+\-.]+)"
    r" rack_disp_mm=([0-9eE+\-.]+)"
    r" iq_ref_ss=([0-9eE+\-.]+)"
)


def run_sim(tmax: float) -> dict | None:
    """EpsGearboxSim.exe を 1 回実行し、定常状態量を返す。"""
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
            print(f"  [WARN] RESULT 行が見つかりません (tmax={tmax:.3f} Nm)")
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
        print(f"[ERROR] 実行ファイルが見つかりません: {EXE_PATH}")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"  [WARN] タイムアウト (tmax={tmax:.3f} Nm)")
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


# ── プロット ──────────────────────────────────────────────────────────────────
def plot_vcurve(results: list[dict]):
    th  = np.array([r["hand_torque"]   for r in results])
    fr  = np.array([r["rack_force_ss"] for r in results])
    tor = np.array([r["torsion_ss"]    for r in results])
    iq  = np.array([r["iq_ref_ss"]     for r in results])
    rd  = np.array([r["rack_disp_mm"]  for r in results])

    # 対称な負方向も生成
    th_full  = np.concatenate([-th[::-1], th])
    fr_full  = np.concatenate([-fr[::-1], fr])
    tor_full = np.concatenate([-tor[::-1], tor])
    iq_full  = np.concatenate([-iq[::-1], iq])
    rd_full  = np.concatenate([-rd[::-1], rd])

    # ── スタイル ────────────────────────────────────────────────────────────
    bg     = "#1a1a1a"
    panel  = "#252525"
    grid_c = "#2e2e2e"
    spine  = "#444444"
    tc     = "#cccccc"

    matplotlib.rcParams["font.family"] = "Yu Gothic"
    matplotlib.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), facecolor=bg)
    fig.suptitle("EPS V字カーブ (操舵トルク対ラック推力) スイープ結果",
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

    # ─ V字カーブ: ラック推力 vs 操舵トルク ─
    ax = axes[0, 0]
    ax.plot(th_full, fr_full, color="#3498db", lw=2.5,
            solid_capstyle="round", label="ラック推力 [N]", zorder=3)
    _style(ax, "V字カーブ: ラック推力 vs 操舵トルク",
           "操舵トルク Th [Nm]", "ラック推力 [N]")
    ax.legend(fontsize=9, facecolor=panel, edgecolor=spine, labelcolor=tc)

    # ─ トルクセンサ値 vs 操舵トルク ─
    ax = axes[0, 1]
    ax.plot(th_full, tor_full, color="#e74c3c", lw=2.0,
            solid_capstyle="round", label="トルクセンサ Tsensor [Nm]", zorder=3)
    _style(ax, "トルクセンサ vs 操舵トルク",
           "操舵トルク Th [Nm]", "トルクセンサ値 [Nm]")
    ax.legend(fontsize=9, facecolor=panel, edgecolor=spine, labelcolor=tc)

    # ─ Iq指令 vs 操舵トルク ─
    ax = axes[1, 0]
    ax.plot(th_full, iq_full, color="#2ecc71", lw=2.0,
            solid_capstyle="round", label="Iq 指令 [A]", zorder=3)
    _style(ax, "アシストマップ: Iq指令 vs 操舵トルク",
           "操舵トルク Th [Nm]", "Iq 指令 [A]")
    ax.legend(fontsize=9, facecolor=panel, edgecolor=spine, labelcolor=tc)

    # ─ ラック変位 vs 操舵トルク ─
    ax = axes[1, 1]
    ax.plot(th_full, rd_full, color="#f39c12", lw=2.0,
            solid_capstyle="round", label="ラック変位 [mm]", zorder=3)
    _style(ax, "ラック変位 vs 操舵トルク",
           "操舵トルク Th [Nm]", "ラック変位 [mm]")
    ax.legend(fontsize=9, facecolor=panel, edgecolor=spine, labelcolor=tc)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out_path = os.path.join(_REPO_ROOT, "data", "eps_vcurve.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=bg)
    print(f"\nPNG 保存完了: {out_path}")
    plt.show()


# ── シンプルV字カーブ図 (eps_model.png 右側スタイル) ─────────────────────────
def plot_schematic_vcurve(results: list[dict]):
    """
    eps_model.png 右側のような、矢印軸・白背景・最小ラベルの
    V字カーブ図を生成・保存する。
    """
    matplotlib.rcParams["font.family"] = "Yu Gothic"
    matplotlib.rcParams["axes.unicode_minus"] = False

    th = np.array([r["hand_torque"]   for r in results])
    fr = np.array([r["rack_force_ss"] for r in results])

    # 両腕を正値にしてV字形を構成 (左腕 = 右腕の折り返し)
    th_full   = np.concatenate([-th[::-1], th])
    fr_vcurve = np.concatenate([fr[::-1],  fr])

    fig, ax = plt.subplots(figsize=(5, 5), facecolor="white")
    ax.set_facecolor("white")

    ax.plot(th_full, fr_vcurve, color="#4a9fd4", lw=2.5,
            solid_capstyle="round", zorder=3)

    # デフォルトの枠・目盛りを非表示
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])

    # 軸範囲 (余白付き)
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

    # 横軸 (双方向矢印 / y=0)
    ax.plot([x_lo, x_hi], [0, 0], color="black", lw=1.3, zorder=2)
    ax.annotate("", xy=(x_hi, 0), xytext=(x_hi - xpad * 0.6, 0),
                arrowprops=aw, zorder=4)
    ax.annotate("", xy=(x_lo, 0), xytext=(x_lo + xpad * 0.6, 0),
                arrowprops=aw, zorder=4)

    # 縦軸 (上方向矢印 / x=0)
    ax.plot([0, 0], [y_lo, y_hi], color="black", lw=1.3, zorder=2)
    ax.annotate("", xy=(0, y_hi), xytext=(0, y_hi - ypad * 0.6),
                arrowprops=aw, zorder=4)

    # 軸ラベル
    ax.text(x_hi - xpad * 0.05, y_lo + y_range * 0.03,
            "操舵トルク", ha="right", va="top",
            fontsize=12, color="#222222")
    ax.text(xpad * 0.3, y_hi,
            "ラック推力", ha="left", va="top",
            fontsize=12, color="red")

    fig.tight_layout(pad=0.5)
    out_path = os.path.join(_REPO_ROOT, "data", "eps_vcurve_schematic.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"Schematic PNG 保存完了: {out_path}")
    plt.show()


# ── エントリポイント ──────────────────────────────────────────────────────────
def main():
    if not os.path.exists(EXE_PATH):
        print(f"[ERROR] 実行ファイルが見つかりません: {EXE_PATH}")
        print("  先に CMake でビルドしてください。")
        sys.exit(1)

    print("EPS V字カーブ スイープ")
    print(f"  EXE         : {EXE_PATH}")
    print(f"  Th 範囲     : 0 ~ {TH_MAX} Nm  ({N_POINTS} 点)")
    print(f"  シミュスパン  : {SIM_SPAN} s  (ランプ {RAMP_DUR} s)")
    print()

    results = sweep()
    if not results:
        print("[ERROR] 有効な結果が得られませんでした。")
        sys.exit(1)

    print(f"\n{len(results)} 点収集完了。グラフを表示中...")
    plot_vcurve(results)
    plot_schematic_vcurve(results)


if __name__ == "__main__":
    main()
