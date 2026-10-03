import struct, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

stl_back = '/home/indra/src/3D-models/out/dl380_back_case.stl'
out_png = '/home/indra/src/3D-models/print_service_package/psu_center_support_view.png'

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

tris = load_stl(stl_back)

fig = plt.figure(figsize=(14, 8), facecolor='#0d1117')
ax = fig.add_subplot(1, 1, 1, projection='3d', facecolor='#0d1117')

# Filter triangles in the rear lower region (PSU window region)
mask = (np.mean(tris[:, :, 0], axis=1) <= 92.0) & \
       (np.mean(tris[:, :, 1], axis=1) <= 65.0) & \
       (np.mean(tris[:, :, 2], axis=1) >= 140.0)
tris_sub = tris[mask]

poly = Poly3DCollection(tris_sub, alpha=0.55, edgecolor='#d97706', linewidths=0.2, facecolor='#f59e0b')
ax.add_collection3d(poly)

ax.set_xlim(0, 95)
ax.set_ylim(0, 60)
ax.set_zlim(140, 216)

# Looking from rear into the case: azim=-90 (from +Z looking to -Z), slight elevation to see depth
ax.view_init(elev=5, azim=-90)

ax.set_title("DL380 Back Case: Center Support Column in Power Supply Hole (X = 52.0 mm)\nTriple-Column Symmetrical Support (Left @ 40mm, Center @ 52mm, Right @ 64mm)", 
             color='#58a6ff', fontsize=12, fontweight='bold', pad=15)
ax.set_xlabel('Chassis X (mm)', color='#8b949e')
ax.set_ylabel('Chassis Y (mm)', color='#8b949e')
ax.set_zlabel('Chassis Z (Depth mm)', color='#8b949e')
ax.tick_params(colors='#8b949e')

plt.tight_layout()
plt.savefig(out_png, dpi=200, facecolor='#0d1117', bbox_inches='tight')
print(f"Rendered: {out_png}")
