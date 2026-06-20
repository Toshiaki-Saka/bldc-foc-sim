"""
Motor Characteristics Map GUI
Displays Speed (N), Current (I), Output Power (P), Efficiency (η) vs Torque (T)
Styled after Mabuchi Motor TIN-format characteristic charts.
"""

import os
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Color palette ─────────────────────────────────────────────────────────────
C = {
    'bg':         '#1a1a1a',
    'panel':      '#222222',
    'grid':       '#2e2e2e',
    'spine':      '#444444',
    'text':       '#cccccc',
    'speed':      '#FFB800',   # N  yellow
    'current':    '#22CC55',   # I  green
    'power':      '#FF5577',   # P  red-pink
    'efficiency': '#4499FF',   # η  blue
    'entry_bg':   '#2d2d2d',
    'entry_fg':   '#00ee88',
}

PARAMS = [
    # (label,                     key,   default,   lo,      hi,    step)
    # Defaults chosen for a physically consistent 12 V / 50 mN·m motor
    # R = V/Is = 6 Ω, Ke ≈ 0.025 V·s/rad → N0 ≈ 4 500 rpm
    ('Voltage  V  (V)',           'V',    12.0,     1.0,    48.0,   0.5),
    ('No-load Speed  N₀  (rpm)', 'N0',  4500.0,  100.0, 50000.0, 100.0),
    ('No-load Current  I₀  (A)', 'I0',    0.05,  0.001,    2.0,  0.005),
    ('Stall Torque  Ts  (mN·m)', 'Ts',   50.0,    1.0,  500.0,    1.0),
    ('Stall Current  Is  (A)',   'Is',    2.0,    0.1,   20.0,    0.1),
]


# ── Motor physics ──────────────────────────────────────────────────────────────
def calculate(V, N0, I0, Ts, Is, n_pts=600):
    """Return (T_mNm, N_rpm, I_A, P_W, eta_pct, consistent) arrays + flag."""
    T   = np.linspace(0.0, Ts, n_pts)          # mN·m
    N   = N0 * (1.0 - T / Ts)                  # rpm
    I   = I0 + (Is - I0) * (T / Ts)            # A
    P   = (T * 1e-3) * (N * 2.0 * np.pi / 60) # W
    Pin = V * I                                  # W
    eta_raw = np.where(Pin > 1e-9, P / Pin * 100.0, 0.0)  # %
    # Physical consistency: P_out ≤ P_in at every operating point
    consistent = bool(np.all(P <= Pin + 1e-6))
    eta = np.clip(eta_raw, 0.0, 100.0)        # cap display; flag if violated
    return T, N, I, P, eta, consistent


# ── Main application ───────────────────────────────────────────────────────────
class MotorCharacteristicsApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title('Motor Characteristics Map')
        root.configure(bg=C['panel'])
        root.geometry('1200x740')
        root.minsize(900, 580)

        self.vars: dict[str, tk.DoubleVar] = {}
        self.sim_data: dict | None = None

        self._build_figure()
        self._build_layout()
        self._try_autoload_csv()
        self._update()

    # ── Figure / axes setup ──────────────────────────────────────────────────
    def _build_figure(self):
        self.fig = Figure(figsize=(8, 5.5), dpi=100, facecolor=C['bg'])
        self.fig.subplots_adjust(left=0.28, right=0.71, top=0.91, bottom=0.13)

        # Primary axis: Speed (left spine)
        self.ax_n   = self.fig.add_subplot(111)
        # Twin axes on right: current, power, efficiency
        self.ax_i   = self.ax_n.twinx()
        self.ax_p   = self.ax_n.twinx()
        self.ax_eta = self.ax_n.twinx()

        # Offset right spines so they don't overlap
        self.ax_p.spines['right'].set_position(('axes', 1.17))
        self.ax_eta.spines['right'].set_position(('axes', 1.34))

        for ax in (self.ax_n, self.ax_i, self.ax_p, self.ax_eta):
            ax.set_facecolor(C['bg'])
            for sp in ax.spines.values():
                sp.set_color(C['spine'])

        for ax in (self.ax_i, self.ax_p, self.ax_eta):
            ax.yaxis.tick_right()
            ax.yaxis.set_label_position('right')
            ax.spines['left'].set_visible(False)

        # Axis labels and ticks — set once here, not in _update()
        self.ax_n.set_xlabel('TORQUE  (mN·m)', color=C['text'], fontsize=10, labelpad=6)

        # Stacked left-side captions (replaces individual y-axis labels)
        _captions = [
            ('Speed N (r/min)',  C['speed']),
            ('Current I (A)',    C['current']),
            ('Output P (W)',     C['power']),
            ('Efficiency η (%)', C['efficiency']),
        ]
        y_mid = (0.13 + 0.91) / 2
        for i, (text, color) in enumerate(_captions):
            self.fig.text(0.13 + i * 0.032, y_mid, text,
                          color=color, fontsize=9,
                          rotation=90, ha='center', va='center')

        self.ax_n.tick_params(axis='both', colors=C['text'],       labelsize=8)
        self.ax_i.tick_params(axis='y',    colors=C['current'],    labelsize=8)
        self.ax_p.tick_params(axis='y',    colors=C['power'],      labelsize=8)
        self.ax_eta.tick_params(axis='y',  colors=C['efficiency'], labelsize=8)
        self.ax_n.xaxis.label.set_color(C['text'])

        self.ax_eta.set_ylim(0, 100)
        self.ax_n.grid(True, color=C['grid'], lw=0.6, alpha=0.9)

        # Persistent line artists (data updated in _update via set_data)
        self.ln_n,   = self.ax_n.plot([], [],   color=C['speed'],      lw=2.0, solid_capstyle='round')
        self.ln_i,   = self.ax_i.plot([], [],   color=C['current'],    lw=2.0, solid_capstyle='round')
        self.ln_p,   = self.ax_p.plot([], [],   color=C['power'],      lw=2.0, solid_capstyle='round')
        self.ln_eta, = self.ax_eta.plot([], [], color=C['efficiency'], lw=2.0, solid_capstyle='round')

        self.mk_p,   = self.ax_p.plot([], [],   'o', color=C['power'],      ms=6, zorder=5, mew=1.5, mec='white')
        self.mk_eta, = self.ax_eta.plot([], [], 'o', color=C['efficiency'], ms=6, zorder=5, mew=1.5, mec='white')

        self._sim_scatters: list = []

    # ── Tkinter layout ───────────────────────────────────────────────────────
    def _build_layout(self):
        left  = tk.Frame(self.root, bg=C['bg'])
        right = tk.Frame(self.root, bg=C['panel'], width=295)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 4), pady=8)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 8), pady=8)
        right.pack_propagate(False)

        self.canvas = FigureCanvasTkAgg(self.fig, master=left)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self._build_controls(right)

    def _build_controls(self, parent):
        tk.Label(parent, text='Motor Parameters',
                 bg=C['panel'], fg='white',
                 font=('Arial', 11, 'bold')).pack(pady=(14, 10))

        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, padx=12, pady=(0, 10))

        for label, key, default, lo, hi, step in PARAMS:
            self._make_row(parent, label, key, default, lo, hi)

        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, padx=12, pady=(14, 8))

        self._build_sim_section(parent)
        self._build_save_section(parent)

        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, padx=12, pady=(10, 8))

        self._build_legend(parent)
        self._build_info_panel(parent)

    # ── PNG export ──────────────────────────────────────────────────────────
    def _build_save_section(self, parent):
        save_btn = tk.Button(
            parent, text='PNG 保存',
            bg='#2a4a2a', fg='#88ff88',
            relief='flat', font=('Arial', 9, 'bold'),
            activebackground='#3a6a3a', activeforeground='white',
            command=self._save_png,
        )
        save_btn.pack(fill=tk.X, padx=14, pady=(6, 4))

    def _save_png(self):
        path = filedialog.asksaveasfilename(
            title='PNG として保存',
            defaultextension='.png',
            filetypes=[('PNG Image', '*.png'), ('All Files', '*.*')],
            initialfile='motor_characteristics.png',
        )
        if not path:
            return
        self.fig.savefig(path, dpi=150, bbox_inches='tight',
                         facecolor=self.fig.get_facecolor())
        messagebox.showinfo('保存完了', f'保存しました:\n{path}')

    def _build_sim_section(self, parent):
        tk.Label(parent, text='Simulation Result (CSV)',
                 bg=C['panel'], fg='white',
                 font=('Arial', 10, 'bold')).pack(anchor='w', padx=14, pady=(0, 4))

        btn_row = tk.Frame(parent, bg=C['panel'])
        btn_row.pack(fill=tk.X, padx=14, pady=(0, 4))

        load_btn = tk.Button(
            btn_row, text='CSVを開く',
            bg='#3a3a3a', fg=C['text'],
            relief='flat', font=('Arial', 8),
            activebackground='#555555', activeforeground='white',
            command=self._open_csv,
        )
        load_btn.pack(side=tk.LEFT)

        clear_btn = tk.Button(
            btn_row, text='クリア',
            bg='#3a3a3a', fg=C['text'],
            relief='flat', font=('Arial', 8),
            activebackground='#555555', activeforeground='white',
            command=self._clear_csv,
        )
        clear_btn.pack(side=tk.LEFT, padx=(6, 0))

        self.sim_status_var = tk.StringVar(value='未読込')
        tk.Label(parent, textvariable=self.sim_status_var,
                 bg=C['panel'], fg='#aaaaaa',
                 font=('Courier', 8), wraplength=260, justify='left',
                 anchor='w').pack(fill=tk.X, padx=14)

    def _make_row(self, parent, label, key, default, lo, hi):
        frame = tk.Frame(parent, bg=C['panel'])
        frame.pack(fill=tk.X, padx=14, pady=3)

        tk.Label(frame, text=label, bg=C['panel'], fg=C['text'],
                 font=('Arial', 9), anchor='w').pack(fill=tk.X)

        row = tk.Frame(frame, bg=C['panel'])
        row.pack(fill=tk.X)

        var = tk.DoubleVar(value=default)
        self.vars[key] = var

        entry = tk.Entry(row, textvariable=var, width=8,
                         bg=C['entry_bg'], fg=C['entry_fg'],
                         relief='flat', font=('Courier', 9),
                         insertbackground='white', bd=1)
        entry.pack(side=tk.RIGHT, padx=(4, 0))
        entry.bind('<Return>',    lambda _e: self._update())
        entry.bind('<FocusOut>',  lambda _e: self._update())

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.Horizontal.TScale',
                         background=C['panel'], troughcolor='#3a3a3a',
                         sliderlength=14, sliderrelief='flat')

        slider = ttk.Scale(row, from_=lo, to=hi, variable=var,
                           orient=tk.HORIZONTAL,
                           style='Dark.Horizontal.TScale',
                           command=lambda _v: self._update())
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _build_legend(self, parent):
        tk.Label(parent, text='Curves', bg=C['panel'], fg='white',
                 font=('Arial', 10, 'bold')).pack(anchor='w', padx=14)

        entries = [
            ('N  Speed     (r/min)', C['speed']),
            ('I  Current   (A)',     C['current']),
            ('P  Output    (W)',     C['power']),
            ('η  Efficiency (%)',    C['efficiency']),
        ]
        for text, color in entries:
            row = tk.Frame(parent, bg=C['panel'])
            row.pack(fill=tk.X, padx=14, pady=1)
            tk.Label(row, text='━━', bg=C['panel'], fg=color,
                     font=('Courier', 13)).pack(side=tk.LEFT)
            tk.Label(row, text=f'  {text}', bg=C['panel'], fg=C['text'],
                     font=('Courier', 9)).pack(side=tk.LEFT)

    def _build_info_panel(self, parent):
        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, padx=12, pady=(10, 8))
        tk.Label(parent, text='Operating Points', bg=C['panel'], fg='white',
                 font=('Arial', 10, 'bold')).pack(anchor='w', padx=14)

        self.info_vars = {k: tk.StringVar(value='—')
                         for k in ('T_Pmax', 'P_max', 'T_etamax', 'eta_max')}
        rows = [
            ('Max Power Torque', 'T_Pmax',   'mN·m'),
            ('Max Power',        'P_max',    'W'),
            ('Max Eff. Torque',  'T_etamax', 'mN·m'),
            ('Max Efficiency',   'eta_max',  '%'),
        ]
        for label, key, unit in rows:
            row = tk.Frame(parent, bg=C['panel'])
            row.pack(fill=tk.X, padx=14, pady=1)
            tk.Label(row, text=f'{label}:', bg=C['panel'], fg=C['text'],
                     font=('Arial', 8), width=17, anchor='w').pack(side=tk.LEFT)
            tk.Label(row, textvariable=self.info_vars[key],
                     bg=C['panel'], fg=C['entry_fg'],
                     font=('Courier', 8)).pack(side=tk.LEFT)
            tk.Label(row, text=unit, bg=C['panel'], fg=C['text'],
                     font=('Arial', 8)).pack(side=tk.LEFT, padx=(2, 0))

        # Warning label for physically inconsistent parameters
        self.warn_var = tk.StringVar(value='')
        self.warn_label = tk.Label(parent, textvariable=self.warn_var,
                                   bg=C['panel'], fg='#FF8800',
                                   font=('Arial', 8), wraplength=260,
                                   justify='left')
        self.warn_label.pack(fill=tk.X, padx=14, pady=(6, 0))

    # ── Simulation CSV ───────────────────────────────────────────────────────
    def _try_autoload_csv(self):
        # data/ ディレクトリはプロジェクトルート（tools/ の一階層上）にある
        default = os.path.join(os.path.dirname(__file__), '..', 'data', 'sim_output.csv')
        if os.path.exists(default):
            self._load_csv(default)

    def _open_csv(self):
        path = filedialog.askopenfilename(
            title='sim_output.csv を選択',
            filetypes=[('CSV Files', '*.csv'), ('All Files', '*.*')],
        )
        if path:
            self._load_csv(path)

    def _clear_csv(self):
        self.sim_data = None
        self.sim_status_var.set('未読込')
        self._update()

    def _load_csv(self, path: str):
        try:
            data = np.genfromtxt(path, delimiter=',', names=True)
            required = ('omega', 'Tm', 'id', 'iq')
            missing = [c for c in required if c not in data.dtype.names]
            if missing:
                messagebox.showerror('列不足', f'列が見つかりません: {missing}')
                return

            omega = data['omega']
            Tm    = data['Tm']
            id_   = data['id']
            iq    = data['iq']

            T_mNm = np.abs(Tm) * 1000
            N_rpm = np.abs(omega) * 60.0 / (2.0 * np.pi)
            I_A   = np.sqrt(id_**2 + iq**2)
            P_W   = np.abs(Tm * omega)

            # 間引き（最大500点）
            step = max(1, len(T_mNm) // 500)
            self.sim_data = {
                'T': T_mNm[::step],
                'N': N_rpm[::step],
                'I': I_A[::step],
                'P': P_W[::step],
            }
            n_pts = len(self.sim_data['T'])
            self.sim_status_var.set(
                f'{os.path.basename(path)}\n'
                f'点数: {n_pts}  T_max: {T_mNm.max():.1f} mN·m'
            )
            self._update()
        except Exception as e:
            messagebox.showerror('読込エラー', str(e))

    def _overlay_sim_data(self):
        for sc in self._sim_scatters:
            sc.remove()
        self._sim_scatters.clear()

        if self.sim_data is None:
            return
        T  = self.sim_data['T']
        kw = dict(s=12, alpha=0.55, zorder=4, linewidths=0)
        self._sim_scatters = [
            self.ax_n.scatter(T, self.sim_data['N'], color=C['speed'],   **kw),
            self.ax_i.scatter(T, self.sim_data['I'], color=C['current'], **kw),
            self.ax_p.scatter(T, self.sim_data['P'], color=C['power'],   **kw),
        ]

    # ── Plot update ──────────────────────────────────────────────────────────
    def _update(self):
        try:
            V  = float(self.vars['V'].get())
            N0 = float(self.vars['N0'].get())
            I0 = float(self.vars['I0'].get())
            Ts = float(self.vars['Ts'].get())
            Is = float(self.vars['Is'].get())
        except (tk.TclError, ValueError):
            return

        if Ts <= 0 or N0 <= 0 or Is <= I0:
            return

        T, N, I, P, eta, consistent = calculate(V, N0, I0, Ts, Is)
        self.warn_var.set(
            '' if consistent else
            '⚠ Parameters violate energy conservation (Pout > Pin).'
            ' η is capped at 100 %. Reduce N₀ or Ts.'
        )

        # ── Update line data in-place (no cla() — avoids axis label reset) ──
        self.ln_n.set_data(T, N)
        self.ln_i.set_data(T, I)
        self.ln_p.set_data(T, P)
        self.ln_eta.set_data(T, eta)

        idx_p   = int(np.argmax(P))
        idx_eta = int(np.argmax(eta))
        self.mk_p.set_data([T[idx_p]],    [P[idx_p]])
        self.mk_eta.set_data([T[idx_eta]], [eta[idx_eta]])

        # ── Simulation overlay ──
        self._overlay_sim_data()

        # ── Axis limits ──
        self.ax_n.set_xlim(0, Ts)
        for ax in (self.ax_n, self.ax_i, self.ax_p):
            ax.relim()
            ax.autoscale_view(scalex=False)
            ax.set_ylim(bottom=0)

        # ── Title ──
        self.fig.suptitle(f'Motor Characteristics  (V = {V:.1f} V)',
                          color=C['text'], fontsize=11, y=0.97)

        # ── Info panel ──
        self.info_vars['T_Pmax'].set(f'{T[idx_p]:.2f}')
        self.info_vars['P_max'].set(f'{P[idx_p]:.3f}')
        self.info_vars['T_etamax'].set(f'{T[idx_eta]:.2f}')
        self.info_vars['eta_max'].set(f'{eta[idx_eta]:.1f}')

        self.canvas.draw_idle()


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    root = tk.Tk()
    app = MotorCharacteristicsApp(root)
    root.mainloop()
