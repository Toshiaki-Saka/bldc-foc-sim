import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Yu Gothic'
plt.rcParams['axes.unicode_minus'] = False

_BG    = '#1a1a1a'
_AX    = '#1e1e1e'
_GRID  = '#2e2e2e'
_SPINE = '#444444'
_TEXT  = '#cccccc'
_LEG   = '#252525'


def _dark_ax(ax):
    ax.set_facecolor(_AX)
    for sp in ax.spines.values():
        sp.set_color(_SPINE)
    ax.tick_params(colors=_TEXT, labelsize=9)
    ax.xaxis.label.set_color(_TEXT)
    ax.yaxis.label.set_color(_TEXT)
    ax.title.set_color(_TEXT)
    ax.grid(True, color=_GRID, lw=0.6, alpha=0.9)


def _style_legend(leg):
    if leg is None:
        return
    leg.get_frame().set_facecolor(_LEG)
    leg.get_frame().set_edgecolor(_SPINE)
    for text in leg.get_texts():
        text.set_color(_TEXT)


import os as _os
_ROOT = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")
df = pd.read_csv(_os.path.join(_ROOT, 'data', 'sim_output.csv'))
t = np.arange(len(df)) * 0.00025

fig, axes = plt.subplots(2, 1, figsize=(10, 7), tight_layout=True, facecolor=_BG)

ax = axes[0]
ax.plot(t, df['iq'], color='#e67e22', label='q軸電流 iq [A]', linewidth=1.2)
ax.plot(t, df['id'], color='#9b59b6', label='d軸電流 id [A]', linewidth=1.2)
ax.axhline(85.0, color='#888888', linestyle='--', linewidth=0.8, label='iq目標値 85A')
ax.set_title('dq軸電流  (Tload=4.3 Nm, iq*=85 A)')
ax.set_xlabel('時間 [s]')
ax.set_ylabel('電流 [A]')
_dark_ax(ax)
_style_legend(ax.legend())
ax.set_xlim(0, 5)

ax2 = axes[1]
ax2.plot(t, df['Te'], color='#e74c3c', label='電磁トルク Te [Nm]', linewidth=1.2)
ax2.plot(t, df['Tm'], color='#3498db', label='機械トルク Tm [Nm]', linewidth=1.2)
ax2.set_title('トルク')
ax2.set_xlabel('時間 [s]')
ax2.set_ylabel('トルク [Nm]')
_dark_ax(ax2)
_style_legend(ax2.legend())
ax2.set_xlim(0, 5)

_out = _os.path.join(_ROOT, 'docs', 'result_tload43.png')
fig.savefig(_out, dpi=120, bbox_inches='tight', facecolor=_BG)
print(f'PNG saved: {_out}')

checkpoints = [
    (0,     't=0ms'),
    (40,    't=10ms'),
    (100,   't=25ms'),
    (332,   't=83ms (omega転換)'),
    (1000,  't=250ms'),
    (4000,  't=1s'),
    (19999, 't=5s (定常)'),
]
print()
print('=== 過渡応答サマリ (Tload=4.3 Nm) ===')
for step, label in checkpoints:
    if step < len(df):
        row = df.iloc[step]
        iq_val = row['iq']
        om_val = row['omega']
        te_val = row['Te']
        tm_val = row['Tm']
        print(f'  {label}: iq={iq_val:.2f}A, omega={om_val:.2f} rad/s, Te={te_val:.3f}Nm, Tm={tm_val:.4f}Nm')
