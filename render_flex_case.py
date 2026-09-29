#!/usr/bin/env python3
"""
render_flex_case.py - Multi-View Visualizer for DL380 Ultra-Smooth Double-Decker Enclosure
Calibrated to High-Precision Digital Caliper Measurements.
Generates orthographic and isometric projections of the CAD assembly.
"""

import struct
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

stl_body = '/home/indra/src/3D-models/out/dl380_flex_case_body.stl'
stl_lid  = '/home/indra/src/3D-models/out/dl380_flex_case_lid.stl'
out_png  = '/home/indra/src/3D-models/docs/dl380_flex_case_views.png'

def load_stl(path):
    with open(path, 'rb') as f:
        f.seek(80)
        count = struct.unpack('<I', f.read(4))[0]
        tris = []
        for _ in range(count):
            data = f.read(50)
            floats = struct.unpack('<12fH', data)
            tris.append([floats[3:6], floats[6:9], floats[9:12]])
    return np.array(tris)

tris_b = load_stl(stl_body)
tris_l = load_stl(stl_lid)

fig = plt.figure(figsize=(20, 15), facecolor='#0d1117')

# Color palette
COLOR_BODY  = '#1f6feb'
COLOR_LID   = '#58a6ff'
COLOR_EDGE  = '#0b2942'
COLOR_GRID  = '#21262d'
COLOR_TEXT  = '#c9d1d9'
COLOR_ACC   = '#58a6ff'
COLOR_VENT  = '#f78166'

# ------------------------------------------------------------------------------
# 1. Isometric 3D View
# ------------------------------------------------------------------------------
ax1 = fig.add_subplot(2, 2, 1, projection='3d', facecolor='#0d1117')
poly_b = Poly3DCollection(tris_b, alpha=0.25, edgecolor='#388bfd', linewidths=0.12, facecolor='#1f6feb')
poly_l = Poly3DCollection(tris_l, alpha=0.60, edgecolor='#79c0ff', linewidths=0.25, facecolor='#58a6ff')
ax1.add_collection3d(poly_b)
ax1.add_collection3d(poly_l)

ax1.set_xlim([0, 190])
ax1.set_ylim([0, 220])
ax1.set_zlim([0, 160])
ax1.set_xlabel('X (Width: 186.0 mm)', color=COLOR_TEXT, labelpad=8)
ax1.set_ylabel('Z (Depth: 215.0 mm)', color=COLOR_TEXT, labelpad=8)
ax1.set_zlabel('Y (Height: 151.5 mm)', color=COLOR_TEXT, labelpad=8)
ax1.tick_params(colors=COLOR_TEXT)
ax1.view_init(elev=28, azim=-55)
ax1.set_title('Isometric View: Calibrated Double-Decker Enclosure\n180mm Bezel Socket + 146mm Metal Guide Bay | 92mm Fan Dual-Cradle | Flex-ATX PSU',
              color='#ffffff', fontsize=12, fontweight='bold', pad=12)

# ------------------------------------------------------------------------------
# 2. Front View (Looking at Z = 0)
# ------------------------------------------------------------------------------
ax2 = fig.add_subplot(2, 2, 2, facecolor='#161b22')
front = tris_b[tris_b[:, :, 2].mean(axis=1) < 15.0]
for t in front:
    ax2.plot(t[[0,1,2,0], 0], t[[0,1,2,0], 1], color='#388bfd', lw=0.45, alpha=0.85)

ax2.set_xlim([-5, 192])
ax2.set_ylim([-5, 158])
ax2.set_xlabel('X (Width across case, mm)', color=COLOR_TEXT, fontsize=10)
ax2.set_ylabel('Y (Height from desk, mm)', color=COLOR_TEXT, fontsize=10)
ax2.set_aspect('equal')
ax2.tick_params(colors=COLOR_TEXT)
ax2.grid(True, linestyle='--', color=COLOR_GRID, alpha=0.7)
ax2.set_title('Front Bezel (Z = 0 mm)\nUpper: 180x86mm Bezel Pocket & 146mm Guide Mouth | Lower: 16mm Switch & PSU Vents',
              color='#ffffff', fontsize=11, fontweight='bold', pad=10)

# Annotations
ax2.text(93.0, 93.5, 'HP 180x86mm Bezel Pocket\n(146.0mm inner cage guide + stud grooves)',
         color='#79c0ff', fontsize=9, ha='center', va='center', bbox=dict(boxstyle='round,pad=0.3', facecolor='#0d1117', edgecolor='#388bfd', alpha=0.8))
ax2.text(45.7, 26.0, 'PSU Intake Vents', color=COLOR_VENT, fontsize=8, ha='center', va='center')
ax2.text(145.0, 26.0, '16mm Switch', color='#7ee787', fontsize=8, ha='center', va='center')
ax2.axhline(54.0, color='#d29922', linestyle=':', lw=1.2, label='Mid-Deck Shelf (Y=54.0mm)')
ax2.legend(loc='upper right', facecolor='#0d1117', edgecolor='#30363d', labelcolor=COLOR_TEXT, fontsize=8)

# ------------------------------------------------------------------------------
# 3. Rear View (Looking at Z = 215 mm)
# ------------------------------------------------------------------------------
ax3 = fig.add_subplot(2, 2, 3, facecolor='#161b22')
rear = tris_b[tris_b[:, :, 2].mean(axis=1) > 200.0]
for t in rear:
    ax3.plot(t[[0,1,2,0], 0], t[[0,1,2,0], 1], color='#f78166', lw=0.45, alpha=0.85)

ax3.set_xlim([-5, 192])
ax3.set_ylim([-5, 158])
ax3.set_xlabel('X (Width across case, mm)', color=COLOR_TEXT, fontsize=10)
ax3.set_ylabel('Y (Height from desk, mm)', color=COLOR_TEXT, fontsize=10)
ax3.set_aspect('equal')
ax3.tick_params(colors=COLOR_TEXT)
ax3.grid(True, linestyle='--', color=COLOR_GRID, alpha=0.7)
ax3.set_title('Rear Panel (Z = 215 mm)\nUpper: 92mm Fan Exhaust & SAS Ports | Lower: Flex-ATX C14 & 40mm Fan',
              color='#ffffff', fontsize=11, fontweight='bold', pad=10)

ax3.text(93.0, 101.0, '92mm Fan Grille\n(Ø86mm Honeycomb, 82.5mm pitch)',
         color='#ffa657', fontsize=9, ha='center', va='center', bbox=dict(boxstyle='round,pad=0.3', facecolor='#0d1117', edgecolor='#f78166', alpha=0.8))
ax3.text(45.7, 22.0, 'Flex-ATX C14 / Fan Cutout\n(3-hole flange mount)',
         color='#79c0ff', fontsize=8, ha='center', va='center')
ax3.axhline(54.0, color='#d29922', linestyle=':', lw=1.2, label='Mid-Deck Shelf (Y=54.0mm)')
ax3.legend(loc='upper right', facecolor='#0d1117', edgecolor='#30363d', labelcolor=COLOR_TEXT, fontsize=8)

# ------------------------------------------------------------------------------
# 4. Side Profile / Cross-Section (Looking from Right, X = 186.0 mm)
# ------------------------------------------------------------------------------
ax4 = fig.add_subplot(2, 2, 4, facecolor='#161b22')
mid_slice = tris_b[np.abs(tris_b[:, :, 0].mean(axis=1) - 93.0) < 70.0]
for t in mid_slice[::3]:
    ax4.plot(t[[0,1,2,0], 2], t[[0,1,2,0], 1], color='#a5d6ff', lw=0.25, alpha=0.45)

# Outer boundary outlines
ax4.plot([0, 215, 215, 0, 0], [0, 0, 151.5, 151.5, 0], color='#58a6ff', lw=1.8, label='Chassis Envelope')
ax4.plot([0, 210], [54.0, 54.0], color='#d29922', lw=1.5, linestyle='--', label='Mid-Deck Shelf')
ax4.plot([137.25, 137.25], [54.0, 148.0], color='#7ee787', lw=1.5, linestyle=':', label='Rear Cage Stop (Z=137.25mm)')
ax4.plot([169.25, 169.25], [54.0, 148.0], color='#d2a8ff', lw=1.2, linestyle=':', label='Rear Tab Tip (Z=169.25mm)')
ax4.plot([185.0, 185.0], [54.0, 148.0], color='#f78166', lw=1.5, linestyle='-.', label='92mm Fan Face (Z=185mm)')

# Annotations
ax4.text(74.0, 101.0, 'HP DL380 8-Bay Cage\n(137.25 mm deep on runners)', color='#79c0ff', fontsize=8.5, ha='center', va='center')
ax4.text(153.0, 80.0, 'Tab Bosses &\nM3 Screws', color='#d2a8ff', fontsize=7.5, ha='center', va='center')
ax4.text(177.0, 115.0, '15.75mm Air Gap\n(Zero Interference)', color='#ffa657', fontsize=8, ha='center', va='center')
ax4.text(198.0, 101.0, '92mm Fan in\nDual Cradle', color='#f78166', fontsize=8, ha='center', va='center')
ax4.text(105.0, 26.0, 'Lower Basement: Flex-ATX PSU (150 mm) & 96.5mm Wiring Corridor', color='#e3b341', fontsize=8.5, ha='center', va='center')
ax4.text(187.0, 149.7, 'Lid + Top Stand', color='#58a6ff', fontsize=8, ha='center', va='bottom')

ax4.set_xlim([-5, 225])
ax4.set_ylim([-5, 158])
ax4.set_xlabel('Z (Depth from front mouth to rear, mm)', color=COLOR_TEXT, fontsize=10)
ax4.set_ylabel('Y (Height from desk, mm)', color=COLOR_TEXT, fontsize=10)
ax4.set_aspect('equal')
ax4.tick_params(colors=COLOR_TEXT)
ax4.grid(True, linestyle='--', color=COLOR_GRID, alpha=0.7)
ax4.set_title('Side Profile & Internal Architecture (Z vs Y)\nVertical Stacking: Lower Basement + Upper Drive Bay & Calibrated Plenum',
              color='#ffffff', fontsize=11, fontweight='bold', pad=10)
ax4.legend(loc='lower left', facecolor='#0d1117', edgecolor='#30363d', labelcolor=COLOR_TEXT, fontsize=8)

plt.tight_layout()
plt.savefig(out_png, dpi=180, facecolor=fig.get_facecolor(), edgecolor='none')
print('Saved calibrated double-decker view rendering to', out_png)
