"""
EPS Gearbox Simulation Viewer
PyQt6 GUI that displays the results in data/eps_output.csv
Main tab: V-curve (rack force vs steering torque)
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
    ("Steering torque / sensor", [
        ("hand_torque",    "Driver steering torque Th [Nm]",   "#e74c3c"),
        ("torsion_torque", "Torque sensor value Tsensor [Nm]", "#3498db"),
        ("sensor_filt",    "Sensor LPF output [Nm]",           "#2ecc71"),
    ]),
    ("Current / assist", [
        ("iq_ref",        "Iq command [A]",                     "#9b59b6"),
        ("iq_actual",     "Iq actual (q-axis current) [A]",     "#e67e22"),
        ("assist_torque", "Assist torque (pinion) [Nm]",        "#2ecc71"),
    ]),
    ("Rack force / displacement", [
        ("rack_force", "Rack force (spring) [N]",  "#f39c12"),
        ("rack_disp",  "Rack displacement [m]",     "#1abc9c"),
    ]),
    ("Angle", [
        ("theta_sw",  "Steering wheel angle theta_sw [rad]", "#e74c3c"),
        ("theta_col", "Pinion angle theta_col [rad]",        "#3498db"),
    ]),
    ("Angular velocity", [
        ("omega_sw",  "Steering wheel angular velocity [rad/s]", "#e74c3c"),
        ("omega_col", "Pinion angular velocity [rad/s]",         "#3498db"),
    ]),
    ("Motor dynamics", [
        ("omega_motor", "Motor angular velocity [rad/s]",  "#e74c3c"),
        ("d_current",   "d-axis current Id [A]",           "#3498db"),
        ("mech_deg",    "Mechanical angle [deg]",          "#2ecc71"),
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
    """Widget that draws the V-curve of rack force vs steering torque"""

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
        self.ax.set_xlabel("Steering torque Th [Nm]")
        self.ax.set_ylabel("Rack force [N]")
        self.ax.set_title("V-curve: rack force vs steering torque")
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
        self.ax.plot(th,  fr, color="#3498db", linewidth=1.5, label="Rack force (positive direction)")
        self.ax.plot(-th, fr, color="#e74c3c", linewidth=1.5, linestyle="--", label="Rack force (negative direction, mirrored)")

        self.ax.set_xlabel("Steering torque Th [Nm]")
        self.ax.set_ylabel("Rack force [N]")
        self.ax.set_title("V-curve: rack force vs steering torque")
        self.ax.axhline(0, color=_DARK['spine'], linewidth=0.5)
        self.ax.axvline(0, color=_DARK['spine'], linewidth=0.5)
        _dark_ax(self.ax)
        _style_legend(self.ax.legend())
        self.canvas.draw()


class TimeChart(QWidget):
    """Time-domain display widget for a single chart group"""

    def __init__(self, group_name: str, signals: list, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.signals    = signals
        self.df         = None
        self.visible    = {col: True for col, _, _ in signals}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        check_row = QHBoxLayout()
        check_row.addWidget(QLabel("Toggle display:"))
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
        self.ax.set_xlabel("Time [s]")
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
        layout.addWidget(QLabel("Showing the first 500 rows"))
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
        load_btn   = QPushButton("Open CSV")
        reload_btn = QPushButton("Reload")
        save_btn   = QPushButton("Save PNG")
        load_btn.clicked.connect(self._open_file)
        reload_btn.clicked.connect(self._reload)
        save_btn.clicked.connect(self._save_png)
        self.file_label = QLabel("No file selected")
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
        self.tabs.addTab(self.vcurve, "V-curve")

        # Time-domain tabs
        self.time_charts = []
        for group_name, signals in CHART_GROUPS:
            w = TimeChart(group_name, signals)
            self.time_charts.append(w)
            self.tabs.addTab(w, group_name)

        # Data table
        self.data_table = DataTableWidget()
        self.tabs.addTab(self.data_table, "Data table")

        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def _try_load_default(self):
        default = os.path.join(os.path.dirname(__file__), DEFAULT_CSV)
        if os.path.exists(default):
            self._load_csv(default)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select eps_output.csv", "", "CSV Files (*.csv);;All Files (*)")
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
                self.status.showMessage(f"Columns not found: {missing}", 6000)
                return
            self.df = df
            self._current_path = path
            self.file_label.setText(path)

            rows      = len(df)
            t_end     = df["time"].iloc[-1] if not df.empty else 0.0
            fr_max    = df["rack_force"].max()
            th_max    = df["hand_torque"].max()
            self.stats_label.setText(
                f"Rows: {rows:,}  |  Simulation time: {t_end:.3f} s  |  "
                f"Max steering torque: {th_max:.2f} Nm  |  Max rack force: {fr_max:.1f} N"
            )

            self.vcurve.load_data(df)
            for chart in self.time_charts:
                chart.load_data(df)
            self.data_table.load_data(df)
            self.status.showMessage(f"Load complete: {path}", 3000)
        except Exception as e:
            self.status.showMessage(f"Load error: {e}", 8000)

    def _save_png(self):
        if self.df is None:
            self.status.showMessage("No data loaded", 4000)
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Select PNG destination", "eps_output.png", "PNG Files (*.png)")
        if not path:
            return

        n = 1 + len(CHART_GROUPS)
        fig, axes = plt.subplots(n, 1, figsize=(14, 4 * n), dpi=150)
        t = self.df["time"].values

        # V-curve
        ax = axes[0]
        ax.plot(self.df["hand_torque"].values, self.df["rack_force"].values,
                color="#3498db", linewidth=1.5, label="Rack force (positive direction)")
        ax.plot(-self.df["hand_torque"].values, self.df["rack_force"].values,
                color="#e74c3c", linewidth=1.5, linestyle="--", label="Rack force (negative direction, mirrored)")
        ax.set_title("V-curve: rack force vs steering torque", fontsize=9)
        ax.set_xlabel("Steering torque [Nm]", fontsize=8)
        ax.set_ylabel("Rack force [N]", fontsize=8)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

        # Time-domain charts
        for i, (group_name, signals) in enumerate(CHART_GROUPS):
            ax = axes[i + 1]
            for col, label, color in signals:
                if col in self.df.columns:
                    ax.plot(t, self.df[col].values, label=label, color=color, linewidth=0.9)
            ax.set_title(group_name, fontsize=9)
            ax.set_xlabel("Time [s]", fontsize=8)
            ax.legend(fontsize=7, loc="upper right")
            ax.grid(True, alpha=0.3)

        fig.tight_layout()
        fig.suptitle("EPS Gearbox Simulation Output", fontsize=11, y=1.01)
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        self.status.showMessage(f"PNG saved: {path}", 4000)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_QSS)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
