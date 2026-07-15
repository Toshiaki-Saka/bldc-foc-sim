"""
BrushlessDCMotor Simulation Output Viewer
Configure motor parameters in a GUI, run the simulation directly, and display the results.
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
    QLineEdit, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


RESOLUTION = 0.00025  # 250 usec (calculation step)

# Chart group definitions: (tab name, [(column name, display name, color), ...])
CHART_GROUPS = [
    ("3-phase current (output)", [
        ("U", "U-phase current [A]", "#e74c3c"),
        ("V", "V-phase current [A]", "#2ecc71"),
        ("W", "W-phase current [A]", "#3498db"),
    ]),
    ("dq-axis current", [
        ("id", "d-axis current id [A]", "#9b59b6"),
        ("iq", "q-axis current iq [A]", "#e67e22"),
    ]),
    ("Torque", [
        ("Te", "electromagnetic torque Te [N·m]", "#e74c3c"),
        ("Tm", "mechanical torque Tm [N·m]", "#3498db"),
    ]),
    ("Angular velocity", [
        ("omega", "angular velocity ω [rad/s]", "#1abc9c"),
    ]),
    ("Electrical / mechanical angle", [
        ("ElecDeg", "electrical angle [rad]", "#f39c12"),
        ("MechDeg", "mechanical angle [rad]", "#8e44ad"),
    ]),
    ("Angle error", [
        ("AngleError", "angle error [rad]", "#c0392b"),
    ]),
]

ALL_COLUMNS = ["U", "V", "W", "ElecDeg", "Te", "id", "iq", "omega", "Tm", "MechDeg", "AngleError"]

# ── Dark theme ──────────────────────────────────────────────────────────────
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
                       border: 1px solid #00aa55; font-weight: bold;
                       padding: 4px 18px; border-radius: 3px; }
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


# ── PlotCanvas ───────────────────────────────────────────────────────────────

class PlotCanvas(QWidget):
    """Canvas widget for a single chart group"""

    def __init__(self, group_name: str, signals: list, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.signals = signals
        self.df = None
        self.visible = {col: True for col, _, _ in signals}

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
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self._setup_axes()

    def _setup_axes(self):
        self.ax.set_xlabel("time [s]")
        self.ax.set_ylabel("value")
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
    """Widget that displays a numeric table"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        info_label = QLabel("Showing the first 500 rows")
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


# ── SimRunner (QThread) ──────────────────────────────────────────────────────

class SimRunner(QThread):
    """Thread that runs the simulation exe in the background"""

    # Note: QThread already has a built-in finished() signal, so avoid a name clash
    result_ready = pyqtSignal(str)   # CSV path on success
    error        = pyqtSignal(str)   # error message
    log          = pyqtSignal(str)   # status update

    def __init__(self, exe_path: str, args: list, csv_path: str, work_dir: str):
        super().__init__()
        self._exe_path = exe_path
        self._args     = args
        self._csv_path = csv_path
        self._work_dir = work_dir

    def run(self):
        try:
            cmd = [self._exe_path] + self._args
            self.log.emit("Running simulation...")
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
                    f"exe exited with code {result.returncode}\n{stderr}"
                )
                return
            self.result_ready.emit(self._csv_path)
        except FileNotFoundError:
            self.error.emit(f"Executable not found:\n{self._exe_path}")
        except subprocess.TimeoutExpired:
            self.error.emit("Timeout: did not complete within 300 seconds")
        except Exception as exc:
            self.error.emit(str(exc))


# ── SettingsTab ──────────────────────────────────────────────────────────────

class SettingsTab(QWidget):
    """Settings tab for motor parameters and simulation conditions"""

    # Keep in sync with the default values in sim_params.hpp
    _B_DEFAULT = 1.0e-2 / (2.0 * math.pi)   # ≈ 0.00159155

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ── helpers ─────────────────────────────────────────────────────────────

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

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(12)
        lay.setContentsMargins(10, 10, 10, 10)

        # ── Motor parameters ──────────────────────────────────────────
        grp = QGroupBox("Motor parameters")
        form = QFormLayout(grp)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.kt_sb = self._dspin(0.0533,             1e-6,  100.0, 6, "Nm/A")
        self.ke_sb = self._dspin(0.0533,             1e-6,  100.0, 6, "V·s/rad")
        self.r_sb  = self._dspin(0.1,                1e-5, 1000.0, 5, "Ω")
        self.l_sb  = self._dspin(0.0001,             1e-8,   10.0, 7, "H")
        self.b_sb  = self._dspin(self._B_DEFAULT,    0.0,    10.0, 8, "Nm·s/rad")
        self.j_sb  = self._dspin(3.5e-4,             1e-8,  100.0, 7, "kg·m²")
        self.pp_sb = self._ispin(4, 1, 50,                          "pair")
        form.addRow("Kt — torque constant:",         self.kt_sb)
        form.addRow("Ke — back-EMF constant:",       self.ke_sb)
        form.addRow("R  — phase resistance:",        self.r_sb)
        form.addRow("L  — phase inductance:",        self.l_sb)
        form.addRow("B  — viscous friction:",        self.b_sb)
        form.addRow("J  — moment of inertia:",       self.j_sb)
        form.addRow("number of pole pairs:",         self.pp_sb)
        lay.addWidget(grp)

        # ── Current-control tuning ─────────────────────────────────────
        grp2 = QGroupBox("PI current-control tuning  (Kp = 2ζωnL − R,  Ki = ωn²L)")
        form2 = QFormLayout(grp2)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.wn_sb   = self._dspin(1000.0, 10.0, 1_000_000.0, 1, "rad/s")
        self.zeta_sb = self._dspin(1.0,    0.01,        10.0, 3, "")
        self.kp_label = QLabel("---")
        self.ki_label = QLabel("---")
        for lbl in (self.kp_label, self.ki_label):
            lbl.setStyleSheet("color: #00cc88; font-family: monospace;")
        form2.addRow("ωn — natural angular frequency:", self.wn_sb)
        form2.addRow("ζ  — damping ratio:",             self.zeta_sb)
        form2.addRow("→ Kp [V/A]:",       self.kp_label)
        form2.addRow("→ Ki [V/(A·s)]:",   self.ki_label)
        lay.addWidget(grp2)

        # ── Simulation conditions ──────────────────────────────────────
        grp3 = QGroupBox("Simulation conditions")
        form3 = QFormLayout(grp3)
        form3.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.iqref_sb    = self._dspin(85.0,  -5000.0, 5000.0, 2, "A")
        self.tload_sb    = self._dspin(4.3,    0.0,    1000.0, 3, "Nm")
        self.span_sb     = self._dspin(5.0,    0.1,    3600.0, 1, "s")
        self.midpoint_cb = QCheckBox("midpoint modulation (SVPWM)")
        self.decouple_cb = QCheckBox("dq-axis decoupling control")
        form3.addRow("IqRef — q-axis current reference:", self.iqref_sb)
        form3.addRow("Tload — load torque:",              self.tload_sb)
        form3.addRow("Span  — computation time:",         self.span_sb)
        form3.addRow("",                     self.midpoint_cb)
        form3.addRow("",                     self.decouple_cb)
        lay.addWidget(grp3)

        # ── iq step change ─────────────────────────────────────────────
        grp4 = QGroupBox("iq step change")
        form4 = QFormLayout(grp4)
        form4.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.step_en_cb   = QCheckBox("enable iq step")
        self.step_time_sb = self._dspin(2.0,  0.0,  3600.0, 2, "s")
        self.step_val_sb  = self._dspin(0.0, -5000.0, 5000.0, 1, "A")
        self.step_time_sb.setEnabled(False)
        self.step_val_sb.setEnabled(False)
        self.step_en_cb.stateChanged.connect(self._toggle_step)
        form4.addRow("",               self.step_en_cb)
        form4.addRow("step time:",       self.step_time_sb)
        form4.addRow("iq after step:",   self.step_val_sb)
        lay.addWidget(grp4)

        # ── Executable path ────────────────────────────────────────────
        grp5 = QGroupBox("Executable settings")
        form5 = QFormLayout(grp5)
        form5.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.exe_edit = QLineEdit()
        self.exe_edit.setText(self._default_exe())
        browse_btn = QPushButton("Browse...")
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

        # Initialize the Kp/Ki display and connect signals
        for sb in (self.wn_sb, self.zeta_sb, self.l_sb, self.r_sb):
            sb.valueChanged.connect(self._update_pi_display)
        self._update_pi_display()

    # ── slots ────────────────────────────────────────────────────────────────

    def _update_pi_display(self):
        """Compute Kp/Ki from ωn/ζ/L/R and display them"""
        l    = self.l_sb.value()
        r    = self.r_sb.value()
        wn   = self.wn_sb.value()
        zeta = self.zeta_sb.value()
        kp   = 2.0 * zeta * wn * l - r
        ki   = wn * wn * l
        self.kp_label.setText(f"{kp:.6f}")
        self.ki_label.setText(f"{ki:.6f}")

    def _toggle_step(self, state: int):
        enabled = (state == Qt.CheckState.Checked.value)
        self.step_time_sb.setEnabled(enabled)
        self.step_val_sb.setEnabled(enabled)

    def _browse_exe(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select executable", "", "Executable (*.exe);;All Files (*)"
        )
        if path:
            self.exe_edit.setText(path)

    # ── public API ───────────────────────────────────────────────────────────

    @staticmethod
    def _default_exe() -> str:
        return os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "BrushlessDCMotor.exe")
        )

    def exe_path(self) -> str:
        return self.exe_edit.text().strip()

    def build_args(self) -> list:
        """Build the CLI argument list from the current settings"""
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
            "--iq_ref",     str(self.iqref_sb.value()),
            "--tload",      str(self.tload_sb.value()),
            "--span",       str(self.span_sb.value()),
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


# ── MainWindow ───────────────────────────────────────────────────────────────

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

        # ── Toolbar row ────────────────────────────────────────────────
        toolbar_row = QHBoxLayout()

        self.run_btn = QPushButton("▶  Simulation Run")
        self.run_btn.setObjectName("run_btn")
        self.run_btn.setFixedHeight(30)
        self.run_btn.clicked.connect(self._run_simulation)

        reload_btn = QPushButton("Reload")
        reload_btn.clicked.connect(self._reload)

        save_png_btn = QPushButton("Save PNG")
        save_png_btn.clicked.connect(self._save_png)

        csv_btn = QPushButton("Load CSV")
        csv_btn.clicked.connect(self._open_file)

        self.file_label = QLabel("No file selected")
        self.file_label.setFont(QFont("", 9))

        toolbar_row.addWidget(self.run_btn)
        toolbar_row.addWidget(reload_btn)
        toolbar_row.addWidget(save_png_btn)
        toolbar_row.addWidget(csv_btn)
        toolbar_row.addWidget(self.file_label, 1)
        root_layout.addLayout(toolbar_row)

        # Statistics label
        self.stats_label = QLabel("")
        self.stats_label.setFont(QFont("", 9))
        root_layout.addWidget(self.stats_label)

        # ── Tab widget ─────────────────────────────────────────────────
        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs, 1)

        # Chart tabs
        self.plot_canvases = []
        for group_name, signals in CHART_GROUPS:
            canvas = PlotCanvas(group_name, signals)
            self.plot_canvases.append(canvas)
            self.tabs.addTab(canvas, group_name)

        # All-waveforms tab (overlay)
        self.tabs.addTab(self._build_overview_tab(), "All waveforms")

        # Data table tab
        self.data_table = DataTableWidget()
        self.tabs.addTab(self.data_table, "Data table")

        # Settings tab
        self.settings_tab = SettingsTab()
        self.tabs.addTab(self.settings_tab, "⚙ Settings")

        # Status bar
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

    # ── Simulation Run ────────────────────────────────────────────────────────

    def _run_simulation(self):
        if self._runner and self._runner.isRunning():
            self.status.showMessage("Simulation is running — please wait for it to finish", 3000)
            return

        exe = self.settings_tab.exe_path()
        if not os.path.isfile(exe):
            self.status.showMessage(
                f"Executable not found: {exe}  (check the Settings tab)", 7000
            )
            return

        work_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        csv_path = os.path.join(work_dir, "data", "sim_output.csv")
        args     = self.settings_tab.build_args()

        self.run_btn.setEnabled(False)
        self.run_btn.setText("⏳ Running...")

        self._runner = SimRunner(exe, args, csv_path, work_dir)
        self._runner.log.connect(lambda msg: self.status.showMessage(msg))
        self._runner.result_ready.connect(self._on_sim_finished)
        self._runner.error.connect(self._on_sim_error)
        self._runner.start()

    def _on_sim_finished(self, csv_path: str):
        self._reset_run_btn()
        self.status.showMessage("Done — loading CSV...", 1000)
        self._load_csv(csv_path)

    def _on_sim_error(self, msg: str):
        self._reset_run_btn()
        short = msg.splitlines()[0][:120]
        self.status.showMessage(f"Error: {short}", 10_000)

    def _reset_run_btn(self):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("▶  Simulation Run")

    # ── CSV ───────────────────────────────────────────────────────────────────

    def _try_load_default(self):
        default_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "sim_output.csv"
        )
        if os.path.exists(default_path):
            self._load_csv(default_path)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select sim_output.csv", "", "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            self._load_csv(path)

    def _reload(self):
        if self._current_path:
            self._load_csv(self._current_path)

    def _load_csv(self, path: str):
        try:
            df = pd.read_csv(path)
            missing = [c for c in ALL_COLUMNS if c not in df.columns]
            if missing:
                self.status.showMessage(f"Columns not found: {missing}", 5000)
                return
            self.df = df[ALL_COLUMNS].copy()
            self._current_path = path
            self.file_label.setText(path)

            rows = len(self.df)
            total_time = rows * RESOLUTION
            self.stats_label.setText(
                f"Rows: {rows:,}  |  Computation time: {total_time:.4f} s  |  "
                f"Step: {RESOLUTION * 1e6:.0f} μs"
            )

            for canvas in self.plot_canvases:
                canvas.load_data(self.df)
            self._refresh_overview()
            self.data_table.load_data(self.df)
            self.status.showMessage(f"Loaded: {path}", 3000)

        except Exception as e:
            self.status.showMessage(f"Load error: {e}", 8000)

    # ── Overview ──────────────────────────────────────────────────────────────

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
            ax.set_ylabel("value", fontsize=8)
            if i == n - 1:
                ax.set_xlabel("time [s]", fontsize=8)
            _dark_ax(ax)
            _style_legend(ax.legend(fontsize=7, loc="upper right"))

        self.overview_canvas_widget.draw()

    # ── Save PNG ────────────────────────────────────────────────────────────────

    def _save_png(self):
        if self.df is None:
            self.status.showMessage("No data loaded", 4000)
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Select PNG destination", "sim_output.png", "PNG Files (*.png)"
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
                ax.set_ylabel("value", fontsize=8, color="white")
                ax.tick_params(colors="white", labelsize=7)
                ax.grid(True, alpha=0.25, color="gray")
                ax.legend(fontsize=7, loc="upper right",
                          facecolor="#0f3460", edgecolor="gray", labelcolor="white")
                for spine in ax.spines.values():
                    spine.set_edgecolor("gray")
                if i == n - 1:
                    ax.set_xlabel("time [s]", fontsize=8, color="white")

            fig.tight_layout(rect=[0, 0, 1, 0.97])
            fig.suptitle("BrushlessDCMotor Simulation Output", fontsize=11, color="white", y=0.99)
            fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
            plt.close(fig)

        self.status.showMessage(f"PNG saved: {path}", 4000)


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
