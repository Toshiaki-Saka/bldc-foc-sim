"""
BrushlessDCMotor / EPS Gearbox Simulation Viewer (05-foc-pwm-eps-sensorless)
sim_output.csv / eps_output.csv の結果を表示する PyQt6 GUI
シミュレーション実行 (BrushlessDCMotor.exe / EpsGearboxSim.exe) にも対応。
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
    QLineEdit, QRadioButton,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


RESOLUTION = 0.00025  # 250 usec (motor calculation step)

# ── Motor sim chart groups ─────────────────────────────────────────────────────
CHART_GROUPS_MOTOR = [
    ("3相電流 (出力)", [
        ("U",  "U相電流 [A]", "#e74c3c"),
        ("V",  "V相電流 [A]", "#2ecc71"),
        ("W",  "W相電流 [A]", "#3498db"),
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
        ("ElecDeg", "電気角 [rad]",  "#f39c12"),
        ("MechDeg", "機械角 [rad]",  "#8e44ad"),
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

REQUIRED_MOTOR_COLS = ["U", "V", "W", "ElecDeg", "Te", "id", "iq", "omega", "Tm", "MechDeg", "AngleError"]
ALL_MOTOR_COLS      = REQUIRED_MOTOR_COLS + ["DutyU", "DutyV", "DutyW", "Vu", "Vv", "Vw"]

# ── EPS sim chart groups ───────────────────────────────────────────────────────
CHART_GROUPS_EPS = [
    ("操舵トルク / センサ", [
        ("hand_torque",    "ドライバ操舵トルク Th [Nm]",  "#e74c3c"),
        ("torsion_torque", "トルクセンサ値 Tsensor [Nm]", "#3498db"),
        ("sensor_filt",    "センサLPF出力 [Nm]",          "#2ecc71"),
    ]),
    ("電流 / アシスト", [
        ("iq_ref",        "Iq 指令 [A]",                   "#9b59b6"),
        ("iq_actual",     "Iq 実際 (q電流) [A]",           "#e67e22"),
        ("assist_torque", "アシストトルク (ピニオン) [Nm]", "#2ecc71"),
    ]),
    ("ラック推力 / 変位", [
        ("rack_force", "ラック推力 (バネ) [N]", "#f39c12"),
        ("rack_disp",  "ラック変位 [m]",         "#1abc9c"),
    ]),
    ("角度 (EPS)", [
        ("theta_sw",  "ステアリングホイール角度 θsw [rad]", "#e74c3c"),
        ("theta_col", "ピニオン角度 θcol [rad]",           "#3498db"),
    ]),
    ("角速度 (EPS)", [
        ("omega_sw",  "ステアリングホイール角速度 [rad/s]", "#e74c3c"),
        ("omega_col", "ピニオン角速度 [rad/s]",             "#3498db"),
    ]),
    ("モーター動態", [
        ("omega_motor", "モータ角速度 [rad/s]", "#e74c3c"),
        ("d_current",   "d軸電流 Id [A]",        "#3498db"),
        ("mech_deg",    "機械角 [deg]",           "#2ecc71"),
    ]),
]

REQUIRED_EPS_COLS = [
    "time", "hand_torque", "torsion_torque", "sensor_filt", "iq_ref", "iq_actual",
    "motor_torque", "assist_torque", "theta_sw", "theta_col",
    "omega_sw", "omega_col", "rack_disp", "rack_vel", "rack_force",
]

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
QTabBar::tab { background-color: #2d2d2d; color: #aaaaaa; padding: 6px 12px;
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
QRadioButton { color: #cccccc; spacing: 6px; }
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


# ── PlotCanvas (motor time-domain) ────────────────────────────────────────────
class PlotCanvas(QWidget):
    def __init__(self, group_name: str, signals: list, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.signals    = signals
        self.df         = None
        self.visible    = {col: True for col, _, _ in signals}

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

        self.fig    = Figure(figsize=(10, 4), dpi=96, tight_layout=True, facecolor=_DARK['fig_bg'])
        self.ax     = self.fig.add_subplot(111)
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


# ── DataTableWidget ───────────────────────────────────────────────────────────
class DataTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(QLabel("先頭 500 行を表示"))
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

    def load_data(self, df: pd.DataFrame, has_time_col: bool = False):
        MAX_ROWS = 500
        display_df = df.head(MAX_ROWS).reset_index(drop=True)
        if not has_time_col:
            time_col = pd.Series(np.arange(len(display_df)) * RESOLUTION, name="Time [s]")
            display_df = pd.concat([time_col, display_df], axis=1)

        self.table.setColumnCount(len(display_df.columns))
        self.table.setRowCount(len(display_df))
        self.table.setHorizontalHeaderLabels(list(display_df.columns))
        for row in range(len(display_df)):
            for col_idx in range(len(display_df.columns)):
                val  = display_df.iloc[row, col_idx]
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

        self.fig    = Figure(figsize=(12, 6), dpi=96, tight_layout=True, facecolor=_DARK['fig_bg'])
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def load_data(self, df_pwm: pd.DataFrame):
        self.df_pwm = df_pwm
        if not df_pwm.empty:
            self.t_start.setRange(0.0, df_pwm["Time_s"].iloc[-1] * 1000.0)
        self.refresh()

    def refresh(self):
        if self.df_pwm is None or self.df_pwm.empty:
            return
        t0   = self.t_start.value() / 1000.0
        t1   = t0 + self.t_span.value() / 1000.0
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


# ── VCurveCanvas (EPS V-curve) ────────────────────────────────────────────────
class VCurveCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.df = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.fig    = Figure(figsize=(8, 6), dpi=96, tight_layout=True, facecolor=_DARK['fig_bg'])
        self.ax     = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self._draw_empty()

    def _draw_empty(self):
        self.ax.cla()
        self.ax.set_xlabel("操舵トルク Th [Nm]")
        self.ax.set_ylabel("ラック推力 [N]")
        self.ax.set_title("V字カーブ: ラック推力 vs 操舵トルク")
        _dark_ax(self.ax)
        self.canvas.draw()

    def load_data(self, df: pd.DataFrame):
        self.df = df
        self.refresh()

    def refresh(self):
        if self.df is None:
            return
        self.ax.cla()
        th = self.df["hand_torque"].values
        fr = self.df["rack_force"].values
        self.ax.plot( th, fr, color="#3498db", linewidth=1.5, label="ラック推力 (正方向)")
        self.ax.plot(-th, fr, color="#e74c3c", linewidth=1.5, linestyle="--",
                     label="ラック推力 (負方向 ※鏡像)")
        self.ax.set_xlabel("操舵トルク Th [Nm]")
        self.ax.set_ylabel("ラック推力 [N]")
        self.ax.set_title("V字カーブ: ラック推力 vs 操舵トルク")
        self.ax.axhline(0, color=_DARK['spine'], linewidth=0.5)
        self.ax.axvline(0, color=_DARK['spine'], linewidth=0.5)
        _dark_ax(self.ax)
        _style_legend(self.ax.legend())
        self.canvas.draw()


# ── EpsTimeChart (EPS time-domain) ────────────────────────────────────────────
class EpsTimeChart(QWidget):
    def __init__(self, group_name: str, signals: list, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.signals    = signals
        self.df         = None
        self.visible    = {col: True for col, _, _ in signals}

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

        self.fig    = Figure(figsize=(10, 4), dpi=96, tight_layout=True, facecolor=_DARK['fig_bg'])
        self.ax     = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self._setup_axes()

    def _setup_axes(self):
        self.ax.set_xlabel("時間 [s]")
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
        t = self.df["time"].values
        for col, label, color in self.signals:
            if col in self.df.columns and self.visible.get(col, True):
                self.ax.plot(t, self.df[col].values, label=label, color=color, linewidth=1.0)
        _style_legend(self.ax.legend())
        self.canvas.draw()

    def _on_toggle(self, col: str, state: int):
        self.visible[col] = (state == Qt.CheckState.Checked.value)
        self.refresh()


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
            self.log.emit("シミュレーション実行中...")
            result = subprocess.run(
                [self._exe_path] + self._args,
                capture_output=True,
                text=True,
                cwd=self._work_dir,
                timeout=300,
            )
            if result.returncode != 0:
                stderr = result.stderr[:600] if result.stderr else "(no stderr)"
                self.error.emit(f"exe がコード {result.returncode} で終了しました\n{stderr}")
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
    _B_DEFAULT = 1.0e-2 / (2.0 * math.pi)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # helpers ──────────────────────────────────────────────────────────────────
    def _dspin(self, value, lo, hi, decimals, suffix="") -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(lo, hi)
        sb.setDecimals(decimals)
        sb.setValue(value)
        sb.setStepType(QDoubleSpinBox.StepType.AdaptiveDecimalStepType)
        sb.setMinimumWidth(170)
        if suffix:
            sb.setSuffix(f"  {suffix}")
        return sb

    def _info_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #888888; font-family: monospace;")
        return lbl

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(12)
        lay.setContentsMargins(10, 10, 10, 10)

        # ── シミュレーションモード ─────────────────────────────────────
        mode_grp = QGroupBox("シミュレーションモード")
        mode_lay = QHBoxLayout(mode_grp)
        self.mode_motor = QRadioButton("モータ単体  (BrushlessDCMotor.exe)")
        self.mode_eps   = QRadioButton("EPS 統合  (EpsGearboxSim.exe)")
        self.mode_motor.setChecked(True)
        mode_lay.addWidget(self.mode_motor)
        mode_lay.addWidget(self.mode_eps)
        mode_lay.addStretch()
        lay.addWidget(mode_grp)

        # ── モータ物理定数 (コンパイル時定数、参照用) ──────────────────
        minfo_grp = QGroupBox("モータパラメータ  (コンパイル時定数 — 参照用)")
        minfo_form = QFormLayout(minfo_grp)
        minfo_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        for label, val in [
            ("Kt — トルク定数:",       "0.0533  Nm/A"),
            ("Ke — 逆起電力定数:",     "0.0533  V·s/rad"),
            ("R  — 相抵抗:",           "0.1  Ω"),
            ("L  — 相インダクタンス:", "0.0001  H"),
            ("B  — 粘性抵抗:",         f"{self._B_DEFAULT:.8f}  Nm·s/rad"),
            ("J  — 慣性モーメント:",   "3.5e-4  kg·m²"),
            ("極対数:",                "4  pair"),
        ]:
            minfo_form.addRow(label, self._info_label(val))
        lay.addWidget(minfo_grp)

        # ── PI 電流制御 (コンパイル時定数、参照用) ────────────────────
        pi_grp = QGroupBox("PI電流制御チューニング  (参照用: Kp = 2ζωnL − R,  Ki = ωn²L)")
        pi_form = QFormLayout(pi_grp)
        pi_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        wn, zeta, L, R = 1000.0, 1.0, 0.0001, 0.1
        kp_val = 2.0 * zeta * wn * L - R
        ki_val = wn * wn * L
        for label, val in [
            ("ωn:",                "1000.0  rad/s"),
            ("ζ:",                 "1.0"),
            ("→ Kp [V/A]:",        f"{kp_val:.6f}"),
            ("→ Ki [V/(A·s)]:",    f"{ki_val:.6f}"),
            ("BEMF LPF:",          "2000.0  rad/s"),
            ("PLL Kp:",            "500.0  rad/s/V"),
            ("PLL Ki:",            "100000  rad/s²/V"),
        ]:
            lbl = QLabel(val)
            lbl.setStyleSheet("color: #00cc88; font-family: monospace;")
            pi_form.addRow(label, lbl)
        lay.addWidget(pi_grp)

        # ── モータシミュレーション条件 ────────────────────────────────
        self.motor_cond_grp = QGroupBox("モータシミュレーション条件")
        mc_form = QFormLayout(self.motor_cond_grp)
        mc_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.iqref_sb    = self._dspin(85.0,  -5000.0, 5000.0, 2, "A")
        self.tload_sb    = self._dspin(4.3,    0.0,    1000.0, 3, "Nm")
        self.span_sb     = self._dspin(5.0,    0.1,    3600.0, 1, "s")
        self.vdc_sb      = self._dspin(48.0,   1.0,     800.0, 1, "V")
        self.midpoint_cb = QCheckBox("ミッドポイント変調 (SVPWM)")
        self.decouple_cb = QCheckBox("dq 軸非干渉制御 (デカップリング)")
        mc_form.addRow("IqRef — q軸電流指令:", self.iqref_sb)
        mc_form.addRow("Tload — 負荷トルク:",  self.tload_sb)
        mc_form.addRow("Span  — 計算時間:",    self.span_sb)
        mc_form.addRow("Vdc   — DC電圧:",      self.vdc_sb)
        mc_form.addRow("",                      self.midpoint_cb)
        mc_form.addRow("",                      self.decouple_cb)
        lay.addWidget(self.motor_cond_grp)

        # ── iq ステップ変化 ───────────────────────────────────────────
        self.step_grp = QGroupBox("iq ステップ変化  (モータシミュレーション)")
        step_form = QFormLayout(self.step_grp)
        step_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.step_en_cb   = QCheckBox("iq ステップを有効にする")
        self.step_time_sb = self._dspin(2.0, 0.0, 3600.0, 2, "s")
        self.step_val_sb  = self._dspin(0.0, -5000.0, 5000.0, 1, "A")
        self.step_time_sb.setEnabled(False)
        self.step_val_sb.setEnabled(False)
        self.step_en_cb.stateChanged.connect(self._toggle_step)
        step_form.addRow("",               self.step_en_cb)
        step_form.addRow("ステップ時刻:",  self.step_time_sb)
        step_form.addRow("ステップ後 iq:", self.step_val_sb)
        lay.addWidget(self.step_grp)

        # ── EPS シミュレーション条件 ──────────────────────────────────
        self.eps_cond_grp = QGroupBox("EPS シミュレーション条件")
        eps_form = QFormLayout(self.eps_cond_grp)
        eps_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.eps_span_sb = self._dspin(5.0,  0.1,  3600.0, 1, "s")
        self.eps_tmax_sb = self._dspin(5.0,  0.1,   100.0, 2, "Nm")
        self.eps_ramp_sb = self._dspin(2.0,  0.1,   600.0, 2, "s")
        self.eps_mid_cb  = QCheckBox("ミッドポイント変調 (SVPWM)")
        self.eps_dec_cb  = QCheckBox("dq 軸非干渉制御 (デカップリング)")
        eps_form.addRow("Span    — 計算時間:",         self.eps_span_sb)
        eps_form.addRow("Tmax    — 最大操舵トルク:",   self.eps_tmax_sb)
        eps_form.addRow("RampDur — トルクランプ時間:", self.eps_ramp_sb)
        eps_form.addRow("",                             self.eps_mid_cb)
        eps_form.addRow("",                             self.eps_dec_cb)
        lay.addWidget(self.eps_cond_grp)

        # ── 実行ファイル設定 ──────────────────────────────────────────
        exe_grp = QGroupBox("実行ファイル設定")
        exe_form = QFormLayout(exe_grp)
        exe_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.motor_exe_edit = QLineEdit(self._default_exe("BrushlessDCMotor.exe"))
        self.eps_exe_edit   = QLineEdit(self._default_exe("EpsGearboxSim.exe"))
        for edit, label_text in [
            (self.motor_exe_edit, "BrushlessDCMotor.exe:"),
            (self.eps_exe_edit,   "EpsGearboxSim.exe:"),
        ]:
            browse_btn = QPushButton("参照...")
            browse_btn.clicked.connect(lambda _, e=edit: self._browse_exe(e))
            row_w   = QWidget()
            row_lay = QHBoxLayout(row_w)
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.addWidget(edit, 1)
            row_lay.addWidget(browse_btn)
            exe_form.addRow(label_text, row_w)
        lay.addWidget(exe_grp)

        lay.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.mode_motor.toggled.connect(self._on_mode_changed)
        self._on_mode_changed()

    def _on_mode_changed(self):
        motor = self.mode_motor.isChecked()
        self.motor_cond_grp.setEnabled(motor)
        self.step_grp.setEnabled(motor)
        self.eps_cond_grp.setEnabled(not motor)

    def _toggle_step(self, state):
        enabled = (state == Qt.CheckState.Checked.value)
        self.step_time_sb.setEnabled(enabled)
        self.step_val_sb.setEnabled(enabled)

    def _browse_exe(self, edit: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(
            self, "実行ファイルを選択", "", "Executable (*.exe);;All Files (*)"
        )
        if path:
            edit.setText(path)

    @staticmethod
    def _default_exe(name: str) -> str:
        return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", name))

    # public interface ─────────────────────────────────────────────────────────
    def is_motor_mode(self) -> bool:
        return self.mode_motor.isChecked()

    def exe_path(self) -> str:
        return self.motor_exe_edit.text().strip() if self.is_motor_mode() \
               else self.eps_exe_edit.text().strip()

    def csv_out(self) -> str:
        return "data/sim_output.csv" if self.is_motor_mode() else "data/eps_output.csv"

    def build_args(self) -> list:
        if self.is_motor_mode():
            args = [
                "--iq_ref", str(self.iqref_sb.value()),
                "--tload",  str(self.tload_sb.value()),
                "--span",   str(self.span_sb.value()),
                "--vdc",    str(self.vdc_sb.value()),
            ]
            if self.midpoint_cb.isChecked():
                args.append("--midpoint")
            if self.decouple_cb.isChecked():
                args.append("--decoupling")
            if self.step_en_cb.isChecked():
                args += ["--iq_step",
                         str(self.step_time_sb.value()),
                         str(self.step_val_sb.value())]
            return args
        else:
            args = [
                "--span", str(self.eps_span_sb.value()),
                "--tmax", str(self.eps_tmax_sb.value()),
                "--ramp", str(self.eps_ramp_sb.value()),
            ]
            if self.eps_mid_cb.isChecked():
                args.append("--midpoint")
            if self.eps_dec_cb.isChecked():
                args.append("--decoupling")
            return args


# ── MainWindow ────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BrushlessDCMotor / EPS Simulation Viewer")
        self.resize(1280, 820)
        self.df_motor: pd.DataFrame | None = None
        self.df_eps:   pd.DataFrame | None = None
        self._runner: SimRunner | None = None
        self._current_path = ""

        self._build_ui()
        self._try_load_defaults()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 4)

        # ── ツールバー ────────────────────────────────────────────────
        toolbar_row = QHBoxLayout()
        self.run_btn = QPushButton("▶  Simulation Run")
        self.run_btn.setObjectName("run_btn")
        self.run_btn.setFixedHeight(34)
        self.run_btn.clicked.connect(self._run_simulation)
        reload_btn   = QPushButton("再読込")
        reload_btn.clicked.connect(self._reload)
        save_png_btn = QPushButton("PNG保存")
        save_png_btn.clicked.connect(self._save_png)
        csv_btn      = QPushButton("CSV読込")
        csv_btn.clicked.connect(self._open_file)
        self.file_label = QLabel("ファイル未選択")
        self.file_label.setFont(QFont("", 9))
        toolbar_row.addWidget(self.run_btn)
        toolbar_row.addWidget(reload_btn)
        toolbar_row.addWidget(save_png_btn)
        toolbar_row.addWidget(csv_btn)
        toolbar_row.addWidget(self.file_label, 1)
        root.addLayout(toolbar_row)

        self.stats_label = QLabel("")
        self.stats_label.setFont(QFont("", 9))
        self.stats_label.setStyleSheet("color:#888888;")
        root.addWidget(self.stats_label)

        # ── タブ ──────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        # Motor chart tabs
        self.plot_canvases = []
        for group_name, signals in CHART_GROUPS_MOTOR:
            w = PlotCanvas(group_name, signals)
            self.plot_canvases.append(w)
            self.tabs.addTab(w, group_name)

        self.tabs.addTab(self._build_overview_tab(), "全波形")

        self.pwm_widget = PwmWaveformWidget()
        self.tabs.addTab(self.pwm_widget, "PWM波形 (三相)")

        self.motor_table = DataTableWidget()
        self.tabs.addTab(self.motor_table, "データ (モータ)")

        # EPS tabs
        self.vcurve = VCurveCanvas()
        self.tabs.addTab(self.vcurve, "V字カーブ")

        self.eps_charts = []
        for group_name, signals in CHART_GROUPS_EPS:
            w = EpsTimeChart(group_name, signals)
            self.eps_charts.append(w)
            self.tabs.addTab(w, group_name)

        self.eps_table = DataTableWidget()
        self.tabs.addTab(self.eps_table, "データ (EPS)")

        # Settings tab
        self.settings_tab = SettingsTab()
        self.tabs.addTab(self.settings_tab, "⚙ 設定")

        self.status = QStatusBar()
        self.setStatusBar(self.status)

    # ── overview tab ──────────────────────────────────────────────────────────
    def _build_overview_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        self.overview_fig = Figure(figsize=(12, 10), dpi=96, tight_layout=True,
                                   facecolor=_DARK['fig_bg'])
        self.overview_cw  = FigureCanvas(self.overview_fig)
        self.overview_cw.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar = NavigationToolbar(self.overview_cw, widget)
        layout.addWidget(toolbar)
        scroll = QScrollArea()
        scroll.setWidget(self.overview_cw)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll, 1)
        return widget

    def _refresh_overview(self):
        if self.df_motor is None:
            return
        self.overview_fig.clf()
        self.overview_fig.set_facecolor(_DARK['fig_bg'])
        n    = len(CHART_GROUPS_MOTOR)
        time = np.arange(len(self.df_motor)) * RESOLUTION
        for i, (group_name, signals) in enumerate(CHART_GROUPS_MOTOR):
            ax = self.overview_fig.add_subplot(n, 1, i + 1)
            for col, label, color in signals:
                if col in self.df_motor.columns:
                    ax.plot(time, self.df_motor[col].values,
                            label=label, color=color, linewidth=0.8)
            ax.set_title(group_name, fontsize=9)
            ax.set_ylabel("値", fontsize=8)
            if i == n - 1:
                ax.set_xlabel("時間 [s]", fontsize=8)
            _dark_ax(ax)
            _style_legend(ax.legend(fontsize=7, loc="upper right"))
        self.overview_cw.draw()

    # ── Simulation Run ────────────────────────────────────────────────────────
    def _run_simulation(self):
        if self._runner and self._runner.isRunning():
            self.status.showMessage("シミュレーション実行中です — 完了をお待ちください", 3000)
            return

        exe = self.settings_tab.exe_path()
        if not os.path.isfile(exe):
            self.status.showMessage(
                f"実行ファイルが見つかりません: {exe}  (⚙ 設定タブで確認してください)", 7000)
            return

        work_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        csv_path = os.path.join(work_dir, self.settings_tab.csv_out())
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
        if "eps_output" in csv_path:
            self._load_eps_csv(csv_path)
        else:
            self._load_motor_csv(csv_path)

    def _on_sim_error(self, msg: str):
        self._reset_run_btn()
        self.status.showMessage(f"エラー: {msg.splitlines()[0][:120]}", 10_000)

    def _reset_run_btn(self):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("▶  Simulation Run")

    # ── CSV loading ───────────────────────────────────────────────────────────
    def _try_load_defaults(self):
        base = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        motor_csv = os.path.join(base, "data", "sim_output.csv")
        eps_csv   = os.path.join(base, "data", "eps_output.csv")
        if os.path.exists(motor_csv):
            self._load_motor_csv(motor_csv)
        if os.path.exists(eps_csv):
            self._load_eps_csv(eps_csv)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "CSV を選択", "", "CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        try:
            cols = pd.read_csv(path, nrows=0).columns.tolist()
            if "hand_torque" in cols:
                self._load_eps_csv(path)
            else:
                self._load_motor_csv(path)
        except Exception as e:
            self.status.showMessage(f"読込エラー: {e}", 8000)

    def _reload(self):
        if not self._current_path:
            return
        cols = []
        try:
            cols = pd.read_csv(self._current_path, nrows=0).columns.tolist()
        except Exception:
            pass
        if "hand_torque" in cols:
            self._load_eps_csv(self._current_path)
        else:
            self._load_motor_csv(self._current_path)

    def _load_motor_csv(self, path: str):
        try:
            df = pd.read_csv(path)
            missing = [c for c in REQUIRED_MOTOR_COLS if c not in df.columns]
            if missing:
                self.status.showMessage(f"列が見つかりません: {missing}", 5000)
                return

            available = [c for c in ALL_MOTOR_COLS if c in df.columns]
            self.df_motor = df[available].copy()
            for col in ["DutyU", "DutyV", "DutyW"]:
                if col in self.df_motor.columns:
                    self.df_motor[f"{col}_pct"] = self.df_motor[col] * 100.0

            self._current_path = path
            self.file_label.setText(os.path.basename(path))

            rows       = len(self.df_motor)
            total_time = rows * RESOLUTION
            duty_u_val = self.df_motor["DutyU_pct"].iloc[-1] if "DutyU_pct" in self.df_motor.columns else float("nan")
            vu_val     = self.df_motor["Vu"].iloc[-1]         if "Vu" in self.df_motor.columns         else float("nan")
            duty_str   = f"  |  U相 duty: {duty_u_val:.1f} %" if not pd.isna(duty_u_val) else ""
            vu_str     = f"  |  U相電圧: {vu_val:.2f} V"       if not pd.isna(vu_val)     else ""
            self.stats_label.setText(
                f"[モータ]  行数: {rows:,}  |  計算時間: {total_time:.4f} s  |  "
                f"ステップ: {RESOLUTION*1e6:.0f} μs{duty_str}{vu_str}"
            )

            for canvas in self.plot_canvases:
                canvas.load_data(self.df_motor)
            self._refresh_overview()
            self.motor_table.load_data(self.df_motor)

            pwm_path = os.path.join(os.path.dirname(path), "pwm_waveform.csv")
            if os.path.exists(pwm_path):
                try:
                    df_pwm = pd.read_csv(pwm_path)
                    self.pwm_widget.load_data(df_pwm)
                    self.status.showMessage(
                        f"読込完了: {os.path.basename(path)}  (PWM: {len(df_pwm):,} 行)", 4000)
                except Exception as e_pwm:
                    self.status.showMessage(
                        f"読込完了: {os.path.basename(path)}  (PWM CSVエラー: {e_pwm})", 6000)
            else:
                self.status.showMessage(f"読込完了: {os.path.basename(path)}", 3000)

            self.tabs.setCurrentIndex(0)
        except Exception as e:
            self.status.showMessage(f"読込エラー: {e}", 8000)

    def _load_eps_csv(self, path: str):
        try:
            df = pd.read_csv(path)
            missing = [c for c in REQUIRED_EPS_COLS if c not in df.columns]
            if missing:
                self.status.showMessage(f"EPS 列が見つかりません: {missing}", 5000)
                return

            self.df_eps        = df
            self._current_path = path
            self.file_label.setText(os.path.basename(path))

            rows   = len(df)
            t_end  = df["time"].iloc[-1] if rows > 0 else 0.0
            fr_max = df["rack_force"].max()
            th_max = df["hand_torque"].max()
            self.stats_label.setText(
                f"[EPS]  行数: {rows:,}  |  時間: {t_end:.3f} s  |  "
                f"最大操舵: {th_max:.2f} Nm  |  最大ラック推力: {fr_max:.1f} N"
            )

            self.vcurve.load_data(df)
            for chart in self.eps_charts:
                chart.load_data(df)
            self.eps_table.load_data(df, has_time_col=True)
            self.status.showMessage(f"読込完了: {os.path.basename(path)}", 3000)

            self.tabs.setCurrentIndex(self.tabs.indexOf(self.vcurve))
        except Exception as e:
            self.status.showMessage(f"EPS 読込エラー: {e}", 8000)

    # ── PNG保存 ───────────────────────────────────────────────────────────────
    def _save_png(self):
        if self.df_motor is None and self.df_eps is None:
            self.status.showMessage("データが読み込まれていません", 4000)
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "PNG保存先を選択", "sim_output.png", "PNG Files (*.png)")
        if not path:
            return
        if self.df_motor is not None:
            self._save_motor_png(path)
        else:
            self._save_eps_png(path)

    def _save_motor_png(self, path: str):
        with plt.style.context("dark_background"):
            n   = len(CHART_GROUPS_MOTOR)
            fig, axes = plt.subplots(n, 1, figsize=(14, 3 * n), dpi=150)
            fig.patch.set_facecolor("#1a1a2e")
            time = np.arange(len(self.df_motor)) * RESOLUTION
            for i, (group_name, signals) in enumerate(CHART_GROUPS_MOTOR):
                ax = axes[i]
                ax.set_facecolor("#16213e")
                for col, label, color in signals:
                    if col in self.df_motor.columns:
                        ax.plot(time, self.df_motor[col].values,
                                label=label, color=color, linewidth=0.8,
                                marker=".", markersize=1.5,
                                markevery=max(1, len(self.df_motor) // 500))
                ax.set_title(group_name, fontsize=9, color="white")
                ax.set_ylabel("値", fontsize=8, color="white")
                ax.tick_params(colors="white", labelsize=7)
                ax.grid(True, alpha=0.25, color="gray")
                ax.legend(fontsize=7, loc="upper right",
                          facecolor="#0f3460", edgecolor="gray", labelcolor="white")
                for sp in ax.spines.values():
                    sp.set_edgecolor("gray")
                if i == n - 1:
                    ax.set_xlabel("時間 [s]", fontsize=8, color="white")
            fig.tight_layout(rect=[0, 0, 1, 0.97])
            fig.suptitle("BrushlessDCMotor Simulation Output (Sensorless)",
                         fontsize=11, color="white", y=0.99)
            fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
            plt.close(fig)
        self.status.showMessage(f"PNG保存完了: {path}", 4000)

    def _save_eps_png(self, path: str):
        n   = 1 + len(CHART_GROUPS_EPS)
        fig, axes = plt.subplots(n, 1, figsize=(14, 4 * n), dpi=150)
        t = self.df_eps["time"].values
        ax = axes[0]
        ax.plot(self.df_eps["hand_torque"].values, self.df_eps["rack_force"].values,
                color="#3498db", linewidth=1.5, label="ラック推力 (正方向)")
        ax.plot(-self.df_eps["hand_torque"].values, self.df_eps["rack_force"].values,
                color="#e74c3c", linewidth=1.5, linestyle="--", label="ラック推力 (負方向 ※鏡像)")
        ax.set_title("V字カーブ: ラック推力 vs 操舵トルク", fontsize=9)
        ax.set_xlabel("操舵トルク [Nm]")
        ax.set_ylabel("ラック推力 [N]")
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        for i, (group_name, signals) in enumerate(CHART_GROUPS_EPS):
            ax = axes[i + 1]
            for col, label, color in signals:
                if col in self.df_eps.columns:
                    ax.plot(t, self.df_eps[col].values, label=label, color=color, linewidth=0.9)
            ax.set_title(group_name, fontsize=9)
            ax.set_xlabel("時間 [s]")
            ax.legend(fontsize=7, loc="upper right")
            ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.suptitle("EPS Gearbox Simulation Output", fontsize=11, y=1.01)
        fig.savefig(path, dpi=150, bbox_inches="tight")
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
