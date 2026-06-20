"""
BrushlessDCMotor Simulation Output Viewer (04-foc-pwm-sensorless)
モータパラメータ / センサーレスオブザーバ設定を GUI で変更し、
シミュレーションを直接実行して結果を表示する。
sim_output.csv / pwm_waveform.csv の結果を PyQt6 GUI で可視化。
"""

import sys
import os
import math
import subprocess

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Yu Gothic"
plt.rcParams["axes.unicode_minus"] = False
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QTabWidget, QPushButton, QFileDialog, QLabel,
    QTableWidget, QTableWidgetItem, QStatusBar, QGroupBox, QCheckBox,
    QScrollArea, QSizePolicy, QHeaderView, QDoubleSpinBox, QSpinBox,
    QLineEdit,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


RESOLUTION = 0.00025  # 250 usec (calculation step)

CHART_GROUPS = [
    ("3相電流 (出力)", [
        ("U", "U相電流 [A]", "#e74c3c"),
        ("V", "V相電流 [A]", "#2ecc71"),
        ("W", "W相電流 [A]", "#3498db"),
    ]),
    ("dq軸電流", [
        ("id", "d軸電流 id [A]", "#9b59b6"),
        ("iq", "q軸電流 iq [A]", "#e67e22"),
    ]),
    ("トルク", [
        ("Te", "電磁トルク Te [N·m]", "#e74c3c"),
        ("Tm", "機械トルク Tm [N·m]", "#3498db"),
    ]),
    ("角速度", [
        ("omega", "角速度 ω [rad/s]", "#1abc9c"),
    ]),
    ("電気角・機械角", [
        ("ElecDeg", "電気角 [rad]", "#f39c12"),
        ("MechDeg", "機械角 [rad]", "#8e44ad"),
    ]),
    ("角度誤差", [
        ("AngleError", "角度誤差 [rad]", "#c0392b"),
    ]),
    ("PWM duty比 (三相)", [
        ("DutyU_pct", "U相 duty比 [%]", "#e74c3c"),
        ("DutyV_pct", "V相 duty比 [%]", "#2ecc71"),
        ("DutyW_pct", "W相 duty比 [%]", "#3498db"),
    ]),
    ("印加電圧 (三相)", [
        ("Vu", "U相電圧 Vu [V]", "#e74c3c"),
        ("Vv", "V相電圧 Vv [V]", "#2ecc71"),
        ("Vw", "W相電圧 Vw [V]", "#3498db"),
    ]),
]

REQUIRED_COLUMNS = ["U", "V", "W", "ElecDeg", "Te", "id", "iq", "omega", "Tm", "MechDeg", "AngleError"]
ALL_COLUMNS = REQUIRED_COLUMNS + ["DutyU", "DutyV", "DutyW", "Vu", "Vv", "Vw"]

# ── Dark theme ─────────────────────────────────────────────────────────────────
_DARK = {
    'fig_bg':    '#1a1a1a',
    'ax_bg':     '#1e1e1e',
    'grid':      '#2e2e2e',
    'spine':     '#444444',
    'text':      '#cccccc',
    'legend_bg': '#252525',
}

DARK_QSS = """
QWidget { background-color: #1a1a1a; color: #cccccc; }
QPushButton { background-color: #2d2d2d; color: #cccccc; border: 1px solid #444444;
              padding: 4px 10px; border-radius: 3px; }
QPushButton:hover { background-color: #3a3a3a; }
QPushButton:pressed { background-color: #505050; }
QPushButton#run_btn { background-color: #0d3320; color: #00ff88;
                       border: 2px solid #00cc66; font-weight: bold; font-size: 13px;
                       padding: 6px 20px; border-radius: 4px; }
QPushButton#run_btn:hover { background-color: #144428; }
QPushButton#run_btn:pressed { background-color: #1a5530; }
QPushButton#run_btn:disabled { background-color: #1a2a1a; color: #447755;
                                border-color: #336644; }
QTabWidget::pane { border: 1px solid #444444; background-color: #1e1e1e; }
QTabBar::tab { background-color: #2d2d2d; color: #aaaaaa; padding: 6px 14px;
               border: 1px solid #444444; border-bottom: none; }
QTabBar::tab:selected { background-color: #1a1a1a; color: #ffffff; }
QTabBar::tab:hover { background-color: #3a3a3a; }
QLabel { color: #cccccc; background-color: transparent; }
QTableWidget { background-color: #1e1e1e; color: #cccccc; gridline-color: #333333;
               alternate-background-color: #252525; selection-background-color: #2a4a6a; }
QHeaderView::section { background-color: #2d2d2d; color: #aaaaaa;
                        border: 1px solid #444444; padding: 2px 4px; }
QScrollBar:vertical { background: #252525; width: 10px; border: none; }
QScrollBar::handle:vertical { background: #555555; border-radius: 5px; }
QScrollBar:horizontal { background: #252525; height: 10px; border: none; }
QScrollBar::handle:horizontal { background: #555555; border-radius: 5px; }
QCheckBox { color: #cccccc; spacing: 6px; }
QCheckBox::indicator { background-color: #2d2d2d; border: 1px solid #555555;
                        width: 14px; height: 14px; }
QCheckBox::indicator:checked { background-color: #4499FF; border-color: #4499FF; }
QStatusBar { background-color: #222222; color: #aaaaaa; }
QDoubleSpinBox { background-color: #2d2d2d; color: #00ee88;
                  border: 1px solid #444444; padding: 2px 4px; }
QSpinBox { background-color: #2d2d2d; color: #00ee88;
            border: 1px solid #444444; padding: 2px 4px; }
QLineEdit { background-color: #2d2d2d; color: #cccccc;
             border: 1px solid #444444; padding: 2px 4px; }
QScrollArea { background-color: #1a1a1a; border: none; }
QGroupBox { border: 1px solid #444444; border-radius: 4px;
             margin-top: 10px; padding-top: 6px; color: #aaaaaa; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
"""


def _dark_ax(ax):
    ax.set_facecolor(_DARK['ax_bg'])
    for sp in ax.spines.values():
        sp.set_color(_DARK['spine'])
    ax.tick_params(colors=_DARK['text'], labelsize=8)
    ax.xaxis.label.set_color(_DARK['text'])
    ax.yaxis.label.set_color(_DARK['text'])
    ax.title.set_color(_DARK['text'])
    ax.grid(True, color=_DARK['grid'], lw=0.6, alpha=0.9)


def _style_legend(leg):
    if leg is None:
        return
    leg.get_frame().set_facecolor(_DARK['legend_bg'])
    leg.get_frame().set_edgecolor(_DARK['spine'])
    for text in leg.get_texts():
        text.set_color(_DARK['text'])


# ── PlotCanvas ────────────────────────────────────────────────────────────────

class PlotCanvas(QWidget):
    def __init__(self, group_name: str, signals: list, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.signals = signals
        self.df = None
        self.visible = {col: True for col, _, _ in signals}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        check_row = QHBoxLayout()
        check_row.addWidget(QLabel("表示切替:"))
        self.checkboxes = {}
        for col, label, color in signals:
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.stateChanged.connect(lambda state, c=col: self._on_toggle(c, state))
            self.checkboxes[col] = cb
            check_row.addWidget(cb)
        check_row.addStretch()
        layout.addLayout(check_row)

        self.fig = Figure(figsize=(10, 4), dpi=96, tight_layout=True, facecolor=_DARK['fig_bg'])
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self._setup_axes()

    def _setup_axes(self):
        self.ax.set_xlabel("時間 [s]")
        self.ax.set_ylabel("値")
        self.ax.set_title(self.group_name)
        _dark_ax(self.ax)
        _style_legend(self.ax.legend())

    def load_data(self, df: pd.DataFrame):
        self.df = df
        self.refresh()

    def refresh(self):
        if self.df is None:
            return
        self.ax.cla()
        self._setup_axes()
        time = np.arange(len(self.df)) * RESOLUTION
        for col, label, color in self.signals:
            if col in self.df.columns and self.visible.get(col, True):
                self.ax.plot(time, self.df[col].values, label=label, color=color, linewidth=1.0)
        _style_legend(self.ax.legend())
        self.canvas.draw()

    def _on_toggle(self, col: str, state: int):
        self.visible[col] = (state == Qt.CheckState.Checked.value)
        self.refresh()


# ── DataTableWidget ──────────────────────────────────────────────────────────

class DataTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        info_label = QLabel("先頭 500 行を表示")
        info_label.setFont(QFont("", 9))
        layout.addWidget(info_label)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

    def load_data(self, df: pd.DataFrame):
        MAX_ROWS = 500
        display_df = df.head(MAX_ROWS)
        time_col = pd.Series(np.arange(len(display_df)) * RESOLUTION, name="Time [s]")
        display_df = pd.concat([time_col, display_df.reset_index(drop=True)], axis=1)

        self.table.setColumnCount(len(display_df.columns))
        self.table.setRowCount(len(display_df))
        self.table.setHorizontalHeaderLabels(list(display_df.columns))

        for row in range(len(display_df)):
            for col_idx, col_name in enumerate(display_df.columns):
                val = display_df.iloc[row, col_idx]
                item = QTableWidgetItem(f"{val:.6g}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col_idx, item)


# ── PwmWaveformWidget ─────────────────────────────────────────────────────────

class PwmWaveformWidget(QWidget):
    _PHASES = [
        ("PwmU_V", "U相 PWM [V]", "#e74c3c"),
        ("PwmV_V", "V相 PWM [V]", "#2ecc71"),
        ("PwmW_V", "W相 PWM [V]", "#3498db"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.df_pwm = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        ctrl_row = QHBoxLayout()
        ctrl_row.addWidget(QLabel("開始時刻:"))
        self.t_start = QDoubleSpinBox()
        self.t_start.setRange(0.0, 99999.0)
        self.t_start.setDecimals(3)
        self.t_start.setValue(0.0)
        self.t_start.setSuffix(" ms")
        self.t_start.setSingleStep(1.0)
        ctrl_row.addWidget(self.t_start)

        ctrl_row.addWidget(QLabel("  表示幅:"))
        self.t_span = QDoubleSpinBox()
        self.t_span.setRange(0.05, 500.0)
        self.t_span.setDecimals(3)
        self.t_span.setValue(2.0)
        self.t_span.setSuffix(" ms")
        ctrl_row.addWidget(self.t_span)

        refresh_btn = QPushButton("更新")
        refresh_btn.clicked.connect(self.refresh)
        ctrl_row.addWidget(refresh_btn)

        self.info_label = QLabel("")
        self.info_label.setFont(QFont("", 9))
        ctrl_row.addWidget(self.info_label, 1)
        layout.addLayout(ctrl_row)

        self.fig = Figure(figsize=(12, 6), dpi=96, tight_layout=True, facecolor=_DARK['fig_bg'])
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def load_data(self, df_pwm: pd.DataFrame):
        self.df_pwm = df_pwm
        if not df_pwm.empty:
            t_max_ms = df_pwm["Time_s"].iloc[-1] * 1000.0
            self.t_start.setRange(0.0, t_max_ms)
        self.refresh()

    def refresh(self):
        if self.df_pwm is None or self.df_pwm.empty:
            return

        t0 = self.t_start.value() / 1000.0
        t1 = t0 + self.t_span.value() / 1000.0
        mask = (self.df_pwm["Time_s"] >= t0) & (self.df_pwm["Time_s"] < t1)
        view = self.df_pwm[mask]
        self.info_label.setText(f"表示行数: {len(view):,} / {len(self.df_pwm):,}")

        self.fig.clf()
        self.fig.set_facecolor(_DARK['fig_bg'])
        n = len(self._PHASES)
        for i, (col, label, color) in enumerate(self._PHASES):
            ax = self.fig.add_subplot(n, 1, i + 1)
            if col in view.columns and not view.empty:
                t_us = view["Time_s"].values * 1e6
                ax.step(t_us, view[col].values, where="post",
                        color=color, linewidth=1.2, label=label)
            ax.set_ylabel(label, fontsize=9)
            ax.set_ylim(-3, 53)
            ax.set_yticks([0, 48])
            ax.set_yticklabels(["0 V", "Vdc"])
            if i == n - 1:
                ax.set_xlabel("時間 [μs]", fontsize=9)
            _dark_ax(ax)
            _style_legend(ax.legend(fontsize=8, loc="upper right"))

        self.canvas.draw()


# ── SimRunner (QThread) ───────────────────────────────────────────────────────

class SimRunner(QThread):
    result_ready = pyqtSignal(str)
    error        = pyqtSignal(str)
    log          = pyqtSignal(str)

    def __init__(self, exe_path: str, args: list, csv_path: str, work_dir: str):
        super().__init__()
        self._exe_path = exe_path
        self._args     = args
        self._csv_path = csv_path
        self._work_dir = work_dir

    def run(self):
        try:
            cmd = [self._exe_path] + self._args
            self.log.emit("シミュレーション実行中...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self._work_dir,
                timeout=300,
            )
            if result.returncode != 0:
                stderr = result.stderr[:600] if result.stderr else "(no stderr)"
                self.error.emit(
                    f"exe がコード {result.returncode} で終了しました\n{stderr}"
                )
                return
            self.result_ready.emit(self._csv_path)
        except FileNotFoundError:
            self.error.emit(f"実行ファイルが見つかりません:\n{self._exe_path}")
        except subprocess.TimeoutExpired:
            self.error.emit("タイムアウト: 300 秒以内に完了しませんでした")
        except Exception as exc:
            self.error.emit(str(exc))


# ── SettingsTab ───────────────────────────────────────────────────────────────

class SettingsTab(QWidget):
    _B_DEFAULT = 1.0e-2 / (2.0 * math.pi)   # ≈ 0.00159155

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _dspin(self, value: float, lo: float, hi: float,
               decimals: int, suffix: str = "") -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(lo, hi)
        sb.setDecimals(decimals)
        sb.setValue(value)
        sb.setStepType(QDoubleSpinBox.StepType.AdaptiveDecimalStepType)
        sb.setMinimumWidth(170)
        if suffix:
            sb.setSuffix(f"  {suffix}")
        return sb

    def _ispin(self, value: int, lo: int, hi: int, suffix: str = "") -> QSpinBox:
        sb = QSpinBox()
        sb.setRange(lo, hi)
        sb.setValue(value)
        sb.setMinimumWidth(100)
        if suffix:
            sb.setSuffix(f"  {suffix}")
        return sb

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(12)
        lay.setContentsMargins(10, 10, 10, 10)

        # ── モータパラメータ ──────────────────────────────────────────
        grp = QGroupBox("モータパラメータ")
        form = QFormLayout(grp)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.kt_sb = self._dspin(0.0533,          1e-6,  100.0, 6, "Nm/A")
        self.ke_sb = self._dspin(0.0533,          1e-6,  100.0, 6, "V·s/rad")
        self.r_sb  = self._dspin(0.1,             1e-5, 1000.0, 5, "Ω")
        self.l_sb  = self._dspin(0.0001,          1e-8,   10.0, 7, "H")
        self.b_sb  = self._dspin(self._B_DEFAULT, 0.0,    10.0, 8, "Nm·s/rad")
        self.j_sb  = self._dspin(3.5e-4,          1e-8,  100.0, 7, "kg·m²")
        self.pp_sb = self._ispin(4, 1, 50,                       "pair")
        form.addRow("Kt — トルク定数:",        self.kt_sb)
        form.addRow("Ke — 逆起電力定数:",      self.ke_sb)
        form.addRow("R  — 相抵抗:",           self.r_sb)
        form.addRow("L  — 相インダクタンス:",  self.l_sb)
        form.addRow("B  — 粘性抵抗:",         self.b_sb)
        form.addRow("J  — 慣性モーメント:",   self.j_sb)
        form.addRow("極対数:",                self.pp_sb)
        lay.addWidget(grp)

        # ── PI電流制御チューニング ─────────────────────────────────────
        grp2 = QGroupBox("PI電流制御チューニング  (Kp = 2ζωnL − R,  Ki = ωn²L)")
        form2 = QFormLayout(grp2)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.wn_sb    = self._dspin(1000.0, 10.0, 1_000_000.0, 1, "rad/s")
        self.zeta_sb  = self._dspin(1.0,    0.01,        10.0, 3, "")
        self.kp_label = QLabel("---")
        self.ki_label = QLabel("---")
        for lbl in (self.kp_label, self.ki_label):
            lbl.setStyleSheet("color: #00cc88; font-family: monospace;")
        form2.addRow("ωn — 固有角周波数:", self.wn_sb)
        form2.addRow("ζ  — 減衰比:",      self.zeta_sb)
        form2.addRow("→ Kp [V/A]:",       self.kp_label)
        form2.addRow("→ Ki [V/(A·s)]:",   self.ki_label)
        lay.addWidget(grp2)

        # ── シミュレーション条件 ──────────────────────────────────────
        grp3 = QGroupBox("シミュレーション条件")
        form3 = QFormLayout(grp3)
        form3.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.iqref_sb    = self._dspin(85.0,  -5000.0,  5000.0, 2, "A")
        self.tload_sb    = self._dspin(4.3,    0.0,     1000.0, 3, "Nm")
        self.span_sb     = self._dspin(5.0,    0.1,     3600.0, 1, "s")
        self.vdc_sb      = self._dspin(48.0,   1.0,      800.0, 1, "V")
        self.midpoint_cb = QCheckBox("ミッドポイント変調 (SVPWM)")
        self.decouple_cb = QCheckBox("dq 軸非干渉制御 (デカップリング)")
        form3.addRow("IqRef — q軸電流指令:", self.iqref_sb)
        form3.addRow("Tload — 負荷トルク:",  self.tload_sb)
        form3.addRow("Span  — 計算時間:",    self.span_sb)
        form3.addRow("Vdc   — DC電圧:",      self.vdc_sb)
        form3.addRow("",                     self.midpoint_cb)
        form3.addRow("",                     self.decouple_cb)
        lay.addWidget(grp3)

        # ── センサーレスオブザーバ設定 ────────────────────────────────
        grp_obs = QGroupBox("センサーレスオブザーバ設定")
        form_obs = QFormLayout(grp_obs)
        form_obs.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.obs_lpf_sb = self._dspin(2000.0,   1.0,  200000.0, 1, "rad/s")
        self.pll_kp_sb  = self._dspin(500.0,    0.0,  100000.0, 1, "rad/s/V")
        self.pll_ki_sb  = self._dspin(100000.0, 0.0, 10000000.0, 0, "rad/s²/V")
        form_obs.addRow("BEMF LPF カットオフ:", self.obs_lpf_sb)
        form_obs.addRow("PLL Kp:",              self.pll_kp_sb)
        form_obs.addRow("PLL Ki:",              self.pll_ki_sb)
        lay.addWidget(grp_obs)

        # ── iq ステップ変化 ───────────────────────────────────────────
        grp4 = QGroupBox("iq ステップ変化")
        form4 = QFormLayout(grp4)
        form4.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.step_en_cb   = QCheckBox("iq ステップを有効にする")
        self.step_time_sb = self._dspin(2.0,  0.0,   3600.0, 2, "s")
        self.step_val_sb  = self._dspin(0.0, -5000.0, 5000.0, 1, "A")
        self.step_time_sb.setEnabled(False)
        self.step_val_sb.setEnabled(False)
        self.step_en_cb.stateChanged.connect(self._toggle_step)
        form4.addRow("",               self.step_en_cb)
        form4.addRow("ステップ時刻:",  self.step_time_sb)
        form4.addRow("ステップ後 iq:", self.step_val_sb)
        lay.addWidget(grp4)

        # ── 実行ファイルパス ──────────────────────────────────────────
        grp5 = QGroupBox("実行ファイル設定")
        form5 = QFormLayout(grp5)
        form5.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.exe_edit = QLineEdit()
        self.exe_edit.setText(self._default_exe())
        browse_btn = QPushButton("参照...")
        browse_btn.clicked.connect(self._browse_exe)
        exe_row = QHBoxLayout()
        exe_row.addWidget(self.exe_edit, 1)
        exe_row.addWidget(browse_btn)
        exe_row.setContentsMargins(0, 0, 0, 0)
        exe_widget = QWidget()
        exe_widget.setLayout(exe_row)
        form5.addRow("BrushlessDCMotor.exe:", exe_widget)
        lay.addWidget(grp5)

        lay.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        for sb in (self.wn_sb, self.zeta_sb, self.l_sb, self.r_sb):
            sb.valueChanged.connect(self._update_pi_display)
        self._update_pi_display()

    def _update_pi_display(self):
        l    = self.l_sb.value()
        r    = self.r_sb.value()
        wn   = self.wn_sb.value()
        zeta = self.zeta_sb.value()
        self.kp_label.setText(f"{2.0 * zeta * wn * l - r:.6f}")
        self.ki_label.setText(f"{wn * wn * l:.6f}")

    def _toggle_step(self, state: int):
        enabled = (state == Qt.CheckState.Checked.value)
        self.step_time_sb.setEnabled(enabled)
        self.step_val_sb.setEnabled(enabled)

    def _browse_exe(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "実行ファイルを選択", "", "Executable (*.exe);;All Files (*)"
        )
        if path:
            self.exe_edit.setText(path)

    @staticmethod
    def _default_exe() -> str:
        return os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "BrushlessDCMotor.exe")
        )

    def exe_path(self) -> str:
        return self.exe_edit.text().strip()

    def build_args(self) -> list:
        args = [
            "--kt",         str(self.kt_sb.value()),
            "--ke",         str(self.ke_sb.value()),
            "--r",          str(self.r_sb.value()),
            "--l",          str(self.l_sb.value()),
            "--b",          str(self.b_sb.value()),
            "--j",          str(self.j_sb.value()),
            "--pole_pairs", str(self.pp_sb.value()),
            "--wn",         str(self.wn_sb.value()),
            "--zeta",       str(self.zeta_sb.value()),
            "--obs_lpf",    str(self.obs_lpf_sb.value()),
            "--pll_kp",     str(self.pll_kp_sb.value()),
            "--pll_ki",     str(self.pll_ki_sb.value()),
            "--iq_ref",     str(self.iqref_sb.value()),
            "--tload",      str(self.tload_sb.value()),
            "--span",       str(self.span_sb.value()),
            "--vdc",        str(self.vdc_sb.value()),
        ]
        if self.midpoint_cb.isChecked():
            args.append("--midpoint")
        if self.decouple_cb.isChecked():
            args.append("--decoupling")
        if self.step_en_cb.isChecked():
            args += [
                "--iq_step",
                str(self.step_time_sb.value()),
                str(self.step_val_sb.value()),
            ]
        return args


# ── MainWindow ────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BrushlessDCMotor Simulation Viewer")
        self.resize(1280, 820)
        self.df = None
        self._runner: SimRunner | None = None
        self._current_path: str = ""

        self._build_ui()
        self._try_load_default()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(8, 8, 8, 4)

        # ── ツールバー行 ──────────────────────────────────────────────
        toolbar_row = QHBoxLayout()

        self.run_btn = QPushButton("▶  Simulation Run")
        self.run_btn.setObjectName("run_btn")
        self.run_btn.setFixedHeight(34)
        self.run_btn.clicked.connect(self._run_simulation)

        reload_btn = QPushButton("再読込")
        reload_btn.clicked.connect(self._reload)

        save_png_btn = QPushButton("PNG保存")
        save_png_btn.clicked.connect(self._save_png)

        csv_btn = QPushButton("CSV読込")
        csv_btn.clicked.connect(self._open_file)

        self.file_label = QLabel("ファイル未選択")
        self.file_label.setFont(QFont("", 9))

        toolbar_row.addWidget(self.run_btn)
        toolbar_row.addWidget(reload_btn)
        toolbar_row.addWidget(save_png_btn)
        toolbar_row.addWidget(csv_btn)
        toolbar_row.addWidget(self.file_label, 1)
        root_layout.addLayout(toolbar_row)

        # 統計情報ラベル
        self.stats_label = QLabel("")
        self.stats_label.setFont(QFont("", 9))
        self.stats_label.setStyleSheet("color:#888888;")
        root_layout.addWidget(self.stats_label)

        # ── タブウィジェット ──────────────────────────────────────────
        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs, 1)

        self.plot_canvases = []
        for group_name, signals in CHART_GROUPS:
            canvas = PlotCanvas(group_name, signals)
            self.plot_canvases.append(canvas)
            self.tabs.addTab(canvas, group_name)

        self.tabs.addTab(self._build_overview_tab(), "全波形")

        self.pwm_widget = PwmWaveformWidget()
        self.tabs.addTab(self.pwm_widget, "PWM波形 (三相)")

        self.data_table = DataTableWidget()
        self.tabs.addTab(self.data_table, "データテーブル")

        self.settings_tab = SettingsTab()
        self.tabs.addTab(self.settings_tab, "⚙ 設定")

        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def _build_overview_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        self.overview_fig = Figure(figsize=(12, 10), dpi=96, tight_layout=True,
                                   facecolor=_DARK['fig_bg'])
        self.overview_canvas_widget = FigureCanvas(self.overview_fig)
        self.overview_canvas_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar = NavigationToolbar(self.overview_canvas_widget, widget)
        layout.addWidget(toolbar)

        scroll = QScrollArea()
        scroll.setWidget(self.overview_canvas_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll, 1)
        return widget

    def _refresh_overview(self):
        if self.df is None:
            return
        self.overview_fig.clf()
        self.overview_fig.set_facecolor(_DARK['fig_bg'])
        n = len(CHART_GROUPS)
        time = np.arange(len(self.df)) * RESOLUTION

        for i, (group_name, signals) in enumerate(CHART_GROUPS):
            ax = self.overview_fig.add_subplot(n, 1, i + 1)
            for col, label, color in signals:
                if col in self.df.columns:
                    ax.plot(time, self.df[col].values, label=label, color=color, linewidth=0.8)
            ax.set_title(group_name, fontsize=9)
            ax.set_ylabel("値", fontsize=8)
            if i == n - 1:
                ax.set_xlabel("時間 [s]", fontsize=8)
            _dark_ax(ax)
            _style_legend(ax.legend(fontsize=7, loc="upper right"))

        self.overview_canvas_widget.draw()

    # ── Simulation Run ────────────────────────────────────────────────────────

    def _run_simulation(self):
        if self._runner and self._runner.isRunning():
            self.status.showMessage("シミュレーション実行中です — 完了をお待ちください", 3000)
            return

        exe = self.settings_tab.exe_path()
        if not os.path.isfile(exe):
            self.status.showMessage(
                f"実行ファイルが見つかりません: {exe}  (⚙ 設定タブで確認してください)", 7000
            )
            return

        work_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        csv_path = os.path.join(work_dir, "data", "sim_output.csv")
        args     = self.settings_tab.build_args()

        self.run_btn.setEnabled(False)
        self.run_btn.setText("⏳ 実行中...")

        self._runner = SimRunner(exe, args, csv_path, work_dir)
        self._runner.log.connect(lambda msg: self.status.showMessage(msg))
        self._runner.result_ready.connect(self._on_sim_finished)
        self._runner.error.connect(self._on_sim_error)
        self._runner.start()

    def _on_sim_finished(self, csv_path: str):
        self._reset_run_btn()
        self.status.showMessage("完了 — CSV 読み込み中...", 1000)
        self._load_csv(csv_path)

    def _on_sim_error(self, msg: str):
        self._reset_run_btn()
        self.status.showMessage(f"エラー: {msg.splitlines()[0][:120]}", 10_000)

    def _reset_run_btn(self):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("▶  Simulation Run")

    # ── CSV ───────────────────────────────────────────────────────────────────

    def _try_load_default(self):
        default_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "sim_output.csv"
        )
        if os.path.exists(default_path):
            self._load_csv(default_path)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "sim_output.csv を選択", "", "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            self._load_csv(path)

    def _reload(self):
        if self._current_path:
            self._load_csv(self._current_path)

    def _load_csv(self, path: str):
        try:
            df = pd.read_csv(path)
            missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
            if missing:
                self.status.showMessage(f"列が見つかりません: {missing}", 5000)
                return
            available = [c for c in ALL_COLUMNS if c in df.columns]
            self.df = df[available].copy()

            for col in ["DutyU", "DutyV", "DutyW"]:
                if col in self.df.columns:
                    self.df[f"{col}_pct"] = self.df[col] * 100.0

            self._current_path = path
            self.file_label.setText(os.path.basename(path))

            rows = len(self.df)
            total_time = rows * RESOLUTION
            duty_u_val = self.df["DutyU_pct"].iloc[-1] if "DutyU_pct" in self.df.columns else float("nan")
            vu_val     = self.df["Vu"].iloc[-1]         if "Vu" in self.df.columns         else float("nan")
            duty_str = f"  |  U相 duty: {duty_u_val:.1f} %" if not pd.isna(duty_u_val) else ""
            vu_str   = f"  |  U相電圧 Vu: {vu_val:.2f} V"   if not pd.isna(vu_val)     else ""
            self.stats_label.setText(
                f"行数: {rows:,}  |  計算時間: {total_time:.4f} s  |  "
                f"ステップ: {RESOLUTION * 1e6:.0f} μs{duty_str}{vu_str}"
            )

            for canvas in self.plot_canvases:
                canvas.load_data(self.df)

            self._refresh_overview()
            self.data_table.load_data(self.df)

            pwm_path = os.path.join(os.path.dirname(path), "pwm_waveform.csv")
            if os.path.exists(pwm_path):
                try:
                    df_pwm = pd.read_csv(pwm_path)
                    self.pwm_widget.load_data(df_pwm)
                    self.status.showMessage(
                        f"読込完了: {os.path.basename(path)}  (PWM波形: {len(df_pwm):,} 行)", 4000)
                except Exception as e_pwm:
                    self.status.showMessage(
                        f"読込完了: {os.path.basename(path)}  (PWM CSVエラー: {e_pwm})", 6000)
            else:
                self.status.showMessage(f"読込完了: {os.path.basename(path)}", 3000)

        except Exception as e:
            self.status.showMessage(f"読込エラー: {e}", 8000)

    # ── PNG保存 ───────────────────────────────────────────────────────────────

    def _save_png(self):
        if self.df is None:
            self.status.showMessage("データが読み込まれていません", 4000)
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "PNG保存先を選択", "sim_output.png", "PNG Files (*.png)"
        )
        if not path:
            return

        with plt.style.context("dark_background"):
            n = len(CHART_GROUPS)
            fig, axes = plt.subplots(n, 1, figsize=(14, 3 * n), dpi=150)
            fig.patch.set_facecolor("#1a1a2e")
            time = np.arange(len(self.df)) * RESOLUTION

            for i, (group_name, signals) in enumerate(CHART_GROUPS):
                ax = axes[i]
                ax.set_facecolor("#16213e")
                for col, label, color in signals:
                    if col in self.df.columns:
                        ax.plot(time, self.df[col].values,
                                label=label, color=color,
                                linewidth=0.8, marker=".", markersize=1.5,
                                markevery=max(1, len(self.df) // 500))
                ax.set_title(group_name, fontsize=9, color="white")
                ax.set_ylabel("値", fontsize=8, color="white")
                ax.tick_params(colors="white", labelsize=7)
                ax.grid(True, alpha=0.25, color="gray")
                ax.legend(fontsize=7, loc="upper right",
                          facecolor="#0f3460", edgecolor="gray", labelcolor="white")
                for spine in ax.spines.values():
                    spine.set_edgecolor("gray")
                if i == n - 1:
                    ax.set_xlabel("時間 [s]", fontsize=8, color="white")

            fig.tight_layout(rect=[0, 0, 1, 0.97])
            fig.suptitle("BrushlessDCMotor Simulation Output (Sensorless)", fontsize=11,
                         color="white", y=0.99)
            fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
            plt.close(fig)

        self.status.showMessage(f"PNG保存完了: {path}", 4000)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_QSS)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
