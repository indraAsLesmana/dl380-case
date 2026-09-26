import struct
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

stl_path = '/home/indra/src/3D-models/out/dl380_flex_case_body.stl'
out_png  = '/home/indra/src/3D-models/docs/dl380_flex_case_views.png'

with open(stl_path, 'rb') as f:
    f.seek(80)
    count = struct.unpack('<I', f.read(4))[0]
    tris = []
    for _ in range(count):
        data = f.read(50)
        floats = struct.unpack('<12fH', data)
        tris.append([floats[3:6], floats[6:9], floats[9:12]])
tris = np.array(tris)

fig = plt.figure(figsize=(18, 14))

# 1. Isometric 3D View
ax1 = fig.add_subplot(2, 2, 1, projection='3d')
poly = Poly3DCollection(tris, alpha=0.35, edgecolor='#1b263b', linewidths=0.15, facecolor='#415a77')
ax1.add_collection3d(poly)
ax1.set_xlim([0, 240])
ax1.set_ylim([0, 210])
ax1.set_zlim([0, 105])
ax1.set_xlabel('X (Width: Left Cage / Right PSU, mm)')
ax1.set_ylabel('Z (Depth: Front to Rear, mm)')
ax1.set_zlabel('Y (Height, mm)')
ax1.view_init(elev=32, azim=-60)
ax1.set_title('Dual-Chamber Enclosure: Left Drive Bay + Right Flex-ATX PSU')

# 2. Top View (Down onto floor Z vs X)
ax2 = fig.add_subplot(2, 2, 2)
# Select floor & mid-height features
top_tris = tris[tris[:, :, 1].mean(axis=1) < 95.0]
for t in top_tris[::2]:
    ax2.plot(t[[0,1,2,0], 0], t[[0,1,2,0], 2], '#1b4965', lw=0.35, alpha=0.6)
ax2.set_xlim([-5, 245])
ax2.set_ylim([-5, 215])
ax2.set_xlabel('X (Width across case, mm)')
ax2.set_ylabel('Z (Depth from front mouth to rear, mm)')
ax2.set_aspect('equal')
ax2.set_title('Top Plan View: Left Drive Bay (145.8 mm) | Right Flex-ATX (82.5 mm)')
ax2.grid(True, linestyle='--', alpha=0.5)

# 3. Rear View (Z = 205 mm looking at back panel)
ax3 = fig.add_subplot(2, 2, 3)
rear = tris[tris[:, :, 2].mean(axis=1) > 195.0]
for t in rear:
    ax3.plot(t[[0,1,2,0], 0], t[[0,1,2,0], 1], '#c1121f', lw=0.45, alpha=0.7)
ax3.set_xlim([-5, 245])
ax3.set_ylim([-5, 105])
ax3.set_xlabel('X (Width, mm)')
ax3.set_ylabel('Y (Height, mm)')
ax3.set_aspect('equal')
ax3.set_title('Rear Panel: 92mm Fan Honeycomb Grille (Left) + Flex-ATX C14 / 40mm Fan (Right)')
ax3.grid(True, linestyle='--', alpha=0.5)

# 4. Front View (Z = 0 mm looking at front bezel)
ax4 = fig.add_subplot(2, 2, 4)
front = tris[tris[:, :, 2].mean(axis=1) < 10.0]
for t in front:
    ax4.plot(t[[0,1,2,0], 0], t[[0,1,2,0], 1], '#0077b6', lw=0.45, alpha=0.7)
ax4.set_xlim([-5, 245])
ax4.set_ylim([-5, 105])
ax4.set_xlabel('X (Width, mm)')
ax4.set_ylabel('Y (Height, mm)')
ax4.set_aspect('equal')
ax4.set_title('Front Bezel: HP 8-Bay SFF Mouth (Left) + 16mm Power Switch & Intake Grille (Right)')
ax4.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig(out_png, dpi=160)
print('Saved dual-chamber view rendering to', out_png)
