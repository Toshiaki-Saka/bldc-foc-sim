"""
EPS Gearbox Simulation Viewer
data/eps_output.csv の結果を表示する PyQt6 GUI
メインタブ: V字カーブ (ラック推力 vs 操舵トルク)
"""

import sys
import os
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
    QTabWidget, QPushButton, QFileDialog, QLabel, QSplitter,
    QStatusBar, QSizePolicy, QHeaderView, QTableWidget, QTableWidgetItem,
    QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

DEFAULT_CSV = "data/eps_output.csv"

# Time-domain chart definitions: (tab_name, [(column, label, color), ...])
CHART_GROUPS = [
    ("操舵トルク / センサ", [
        ("hand_torque",    "ドライバ操舵トルク Th [Nm]",       "#e74c3c"),
        ("torsion_torque", "トルクセンサ値 Tsensor [Nm]",      "#3498db"),
        ("sensor_filt",    "センサLPF出力 [Nm]",               "#2ecc71"),
    ]),
    ("電流 / アシスト", [
        ("iq_ref",        "Iq 指令 [A]",                        "#9b59b6"),
        ("iq_actual",     "Iq 実際 (q電流) [A]",               "#e67e22"),
        ("assist_torque", "アシストトルク (ピニオン) [Nm]",     "#2ecc71"),
    ]),
    ("ラック推力 / 変位", [
        ("rack_force", "ラック推力 (バネ) [N]",   "#f39c12"),
        ("rack_disp",  "ラック変位 [m]",           "#1abc9c"),
    ]),
    ("角度", [
        ("theta_sw",  "ステアリングホイール角度 θsw [rad]",  "#e74c3c"),
        ("theta_col", "ピニオン角度 θcol [rad]",            "#3498db"),
    ]),
    ("角速度", [
        ("omega_sw",  "ステアリングホイール角速度 [rad/s]",  "#e74c3c"),
        ("omega_col", "ピニオン角速度 [rad/s]",              "#3498db"),
    ]),
    ("モーター動態", [
        ("omega_motor", "モータ角速度 [rad/s]",  "#e74c3c"),
        ("d_current",   "d軸電流 Id [A]",         "#3498db"),
        ("mech_deg",    "機械角 [deg]",            "#2ecc71"),
    ]),
]

REQUIRED_COLUMNS = [
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
QScrollArea { background-color: #1a1a1a; border: none; }
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


class VCurveCanvas(QWidget):
    """ラック推力 vs 操舵トルク の V 字カーブを描画するウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.df = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.fig = Figure(figsize=(8, 6), dpi=96, tight_layout=True, facecolor=_DARK['fig_bg'])
        self.ax  = self.fig.add_subplot(111)
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
        th  = self.df["hand_torque"].values
        fr  = self.df["rack_force"].values

        # Plot positive side only (symmetric V: also show negative by mirroring label)
        self.ax.plot(th,  fr, color="#3498db", linewidth=1.5, label="ラック推力 (正方向)")
        self.ax.plot(-th, fr, color="#e74c3c", linewidth=1.5, linestyle="--", label="ラック推力 (負方向 ※鏡像)")

        self.ax.set_xlabel("操舵トルク Th [Nm]")
        self.ax.set_ylabel("ラック推力 [N]")
        self.ax.set_title("V字カーブ: ラック推力 vs 操舵トルク")
        self.ax.axhline(0, color=_DARK['spine'], linewidth=0.5)
        self.ax.axvline(0, color=_DARK['spine'], linewidth=0.5)
        _dark_ax(self.ax)
        _style_legend(self.ax.legend())
        self.canvas.draw()


class TimeChart(QWidget):
    """単一チャートグループの時間域表示ウィジェット"""

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

        self.fig = Figure(figsize=(10, 4), dpi=96, tight_layout=True, facecolor=_DARK['fig_bg'])
        self.ax  = self.fig.add_subplot(111)
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
                self.ax.plot(t, self.df[col].values,
                             label=label, color=color, linewidth=1.0)
        _style_legend(self.ax.legend())
        self.canvas.draw()

    def _on_toggle(self, col: str, state: int):
        self.visible[col] = (state == Qt.CheckState.Checked.value)
        self.refresh()


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

    def load_data(self, df: pd.DataFrame):
        display = df.head(500)
        self.table.setColumnCount(len(display.columns))
        self.table.setRowCount(len(display))
        self.table.setHorizontalHeaderLabels(list(display.columns))
        for r in range(len(display)):
            for c, col in enumerate(display.columns):
                val = display.iloc[r, c]
                item = QTableWidgetItem(f"{val:.6g}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(r, c, item)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EPS Gearbox Simulation Viewer")
        self.resize(1280, 800)
        self.df = None
        self._current_path = None
        self._build_ui()
        self._try_load_default()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 4)

        toolbar_row = QHBoxLayout()
        load_btn   = QPushButton("CSV を開く")
        reload_btn = QPushButton("再読込")
        save_btn   = QPushButton("PNG 保存")
        load_btn.clicked.connect(self._open_file)
        reload_btn.clicked.connect(self._reload)
        save_btn.clicked.connect(self._save_png)
        self.file_label = QLabel("ファイル未選択")
        self.file_label.setFont(QFont("", 9))
        toolbar_row.addWidget(load_btn)
        toolbar_row.addWidget(reload_btn)
        toolbar_row.addWidget(save_btn)
        toolbar_row.addWidget(self.file_label, 1)
        root.addLayout(toolbar_row)

        self.stats_label = QLabel("")
        self.stats_label.setFont(QFont("", 9))
        root.addWidget(self.stats_label)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        # V-curve tab (first, most important)
        self.vcurve = VCurveCanvas()
        self.tabs.addTab(self.vcurve, "V字カーブ")

        # Time-domain tabs
        self.time_charts = []
        for group_name, signals in CHART_GROUPS:
            w = TimeChart(group_name, signals)
            self.time_charts.append(w)
            self.tabs.addTab(w, group_name)

        # Data table
        self.data_table = DataTableWidget()
        self.tabs.addTab(self.data_table, "データテーブル")

        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def _try_load_default(self):
        default = os.path.join(os.path.dirname(__file__), DEFAULT_CSV)
        if os.path.exists(default):
            self._load_csv(default)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "eps_output.csv を選択", "", "CSV Files (*.csv);;All Files (*)")
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
                self.status.showMessage(f"列が見つかりません: {missing}", 6000)
                return
            self.df = df
            self._current_path = path
            self.file_label.setText(path)

            rows      = len(df)
            t_end     = df["time"].iloc[-1] if not df.empty else 0.0
            fr_max    = df["rack_force"].max()
            th_max    = df["hand_torque"].max()
            self.stats_label.setText(
                f"行数: {rows:,}  |  シミュレーション時間: {t_end:.3f} s  |  "
                f"最大操舵トルク: {th_max:.2f} Nm  |  最大ラック推力: {fr_max:.1f} N"
            )

            self.vcurve.load_data(df)
            for chart in self.time_charts:
                chart.load_data(df)
            self.data_table.load_data(df)
            self.status.showMessage(f"読込完了: {path}", 3000)
        except Exception as e:
            self.status.showMessage(f"読込エラー: {e}", 8000)

    def _save_png(self):
        if self.df is None:
            self.status.showMessage("データが読み込まれていません", 4000)
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "PNG 保存先を選択", "eps_output.png", "PNG Files (*.png)")
        if not path:
            return

        n = 1 + len(CHART_GROUPS)
        fig, axes = plt.subplots(n, 1, figsize=(14, 4 * n), dpi=150)
        t = self.df["time"].values

        # V-curve
        ax = axes[0]
        ax.plot(self.df["hand_torque"].values, self.df["rack_force"].values,
                color="#3498db", linewidth=1.5, label="ラック推力 (正方向)")
        ax.plot(-self.df["hand_torque"].values, self.df["rack_force"].values,
                color="#e74c3c", linewidth=1.5, linestyle="--", label="ラック推力 (負方向 ※鏡像)")
        ax.set_title("V字カーブ: ラック推力 vs 操舵トルク", fontsize=9)
        ax.set_xlabel("操舵トルク [Nm]", fontsize=8)
        ax.set_ylabel("ラック推力 [N]", fontsize=8)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

        # Time-domain charts
        for i, (group_name, signals) in enumerate(CHART_GROUPS):
            ax = axes[i + 1]
            for col, label, color in signals:
                if col in self.df.columns:
                    ax.plot(t, self.df[col].values, label=label, color=color, linewidth=0.9)
            ax.set_title(group_name, fontsize=9)
            ax.set_xlabel("時間 [s]", fontsize=8)
            ax.legend(fontsize=7, loc="upper right")
            ax.grid(True, alpha=0.3)

        fig.tight_layout()
        fig.suptitle("EPS Gearbox Simulation Output", fontsize=11, y=1.01)
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        self.status.showMessage(f"PNG 保存完了: {path}", 4000)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_QSS)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
