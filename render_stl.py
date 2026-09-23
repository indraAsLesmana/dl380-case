#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_stl.py - dependency-free shaded renderer for the enclosure previews.

Reads a binary/ascii STL, draws it with a painter's-algorithm flat shader and
writes SVG; rsvg-convert turns the SVG into PNG.

usage: python3 render_stl.py out/foo.stl out/preview.png [--section AXIS]
       AXIS in {none, x, y, z} : keep only the far half  -> cut-away view
"""
import math
import struct
import subprocess
import sys


# ----------------------------------------------------------------- load ------
def load_stl(path):
    with open(path, "rb") as f:
        head = f.read(84)
        if head[:5].lower() == b"solid" and b"facet" in head:
            f.seek(0)
            return _load_ascii(f.read().decode("utf-8", "replace"))
        n = struct.unpack("<I", head[80:84])[0]
        raw = f.read()
    n = min(n, len(raw) // 50)          # some writers round the header count
    tris = []
    for i in range(n):
        v = struct.unpack_from("<9f", raw, i * 50 + 12)
        tris.append(((v[0], v[1], v[2]), (v[3], v[4], v[5]), (v[6], v[7], v[8])))
    return tris


def _load_ascii(txt):
    tris, cur = [], []
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("vertex"):
            cur.append(tuple(float(x) for x in line.split()[1:4]))
            if len(cur) == 3:
                tris.append(tuple(cur))
                cur = []
    return tris


# ------------------------------------------------------------- geometry ------
def norm(a):
    l = math.sqrt(sum(c * c for c in a)) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def basis(az_deg, el_deg):
    """Camera basis for a turntable view. Model +Y is up."""
    az, el = math.radians(az_deg), math.radians(el_deg)
    zc = norm((math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)))
    xc = norm(cross((0.0, 1.0, 0.0), zc))
    yc = cross(zc, xc)
    return xc, yc, zc


# --------------------------------------------------------------- render ------
def render(tris, out_svg, az, el, width=1000, section=None, bg="#101418"):
    if section:
        ax = {"x": 0, "y": 1, "z": 2}[section]
        keep = []
        for t in tris:
            c = sum(v[ax] for v in t) / 3.0
            if ax == 0:
                if c >= 0.0:      # keep the -X half, look through it
                    keep.append(t)
            elif ax == 2:
                if c <= 200.0:
                    keep.append(t)
            else:
                keep.append(t)
        tris = keep

    xc, yc, zc = basis(az, el)
    light = norm((0.45, 0.80, 0.40))

    proj, depths = [], []
    for t in tris:
        pts = [(dot(v, xc), dot(v, yc), dot(v, zc)) for v in t]
        n = norm(cross(sub(t[1], t[0]), sub(t[2], t[0])))
        sh = 0.28 + 0.72 * abs(dot(n, light))
        proj.append((pts, sh))
        depths.append(sum(p[2] for p in pts) / 3.0)

    order = sorted(range(len(proj)), key=lambda i: depths[i])

    xs = [p[0] for pts, _ in proj for p in pts]
    ys = [p[1] for pts, _ in proj for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    span = max(x1 - x0, y1 - y0) or 1.0
    s = (width * 0.94) / span
    h = int((y1 - y0) * s + width * 0.06)

    def px(p):
        return (width * 0.5 + (p[0] - (x0 + x1) / 2.0) * s,
                h * 0.5 - (p[1] - (y0 + y1) / 2.0) * s)

    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
           'viewBox="0 0 %d %d"><rect width="100%%" height="100%%" fill="%s"/>'
           % (width, h, width, h, bg)]
    for i in order:
        pts, sh = proj[i]
        c = int(max(0, min(255, 235 * sh)))
        col = "#%02x%02x%02x" % (int(c * 0.86), int(c * 0.92), c)
        out.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="0.35"/>'
                   % (" ".join("%.1f,%.1f" % px(p) for p in pts), col, col))
    out.append("</svg>")

    with open(out_svg, "w") as f:
        f.write("".join(out))
    return out_svg


def main():
    stl, png = sys.argv[1], sys.argv[2]
    views = [("front", 155.0, 20.0, None),
             ("rear", 25.0, 20.0, None),
             ("side", 90.0, 3.0, None),
             ("top", 10.0, 84.0, None),
             ("cut", 200.0, 16.0, "x")]
    tris = load_stl(stl)
    print("triangles:", len(tris))
    base = png.rsplit(".", 1)[0]
    outs = []
    for name, az, el, sec in views:
        svg = "%s_%s.svg" % (base, name)
        render(tris, svg, az, el, section=sec)
        outs.append(svg)
    for svg in outs:
        subprocess.run(["rsvg-convert", "-w", "1000", svg,
                        "-o", svg[:-4] + ".png"], check=True)
    print("wrote:", " ".join(o[:-4] + ".png" for o in outs))


if __name__ == "__main__":
    main()
