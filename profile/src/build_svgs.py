"""Builds the README hero: the name drawn as its own vector construction, rendered by a sweeping playhead.

Writes profile/hero-dark.svg and profile/hero-light.svg. Needs fonttools and Bricolage Grotesque:
  curl -L -o Bricolage.ttf "https://github.com/google/fonts/raw/main/ofl/bricolagegrotesque/BricolageGrotesque%5Bopsz,wdth,wght%5D.ttf"
  python build_svgs.py Bricolage.ttf
"""
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

OUT = Path(__file__).resolve().parent.parent

# GitHub's own foreground / muted / border colors, so the hero sits on the page instead of in a box.
THEMES = {
    "dark": {"fg": "#E6EDF3", "muted": "#7D8590", "guide": "#30363D"},
    "light": {"fg": "#1F2328", "muted": "#8C959F", "guide": "#D0D7DE"},
}

NAME = "Solarisx"
W = 1200
X0, TOP = 20, 64  # TOP leaves room for the playhead's head above the cap height
TRACKING = -0.025  # in em
LOOP = "11s"


def load_font():
    return instantiateVariableFont(TTFont(sys.argv[1]), {"opsz": 96, "wdth": 100, "wght": 700})


def build(font):
    """Returns the outline path, on/off-curve points per contour, guide heights and the name's width."""
    cmap, hmtx, glyf = font.getBestCmap(), font["hmtx"], font["glyf"]
    glyphs, upem = font.getGlyphSet(), font["head"].unitsPerEm

    os2 = font["OS/2"]
    # Fit the name to the full width, leaving room on the right for the playhead to park.
    advance = sum(hmtx[cmap[ord(ch)]][0] / upem + TRACKING for ch in NAME) - TRACKING
    size = (W - X0 - 56) / advance
    scale, tracking = size / upem, TRACKING * size
    baseline = TOP + os2.sCapHeight * scale
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}")
    contours = []
    x = X0
    for ch in NAME:
        name = cmap[ord(ch)]
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, baseline)))
        coords, end_pts, flags = glyf[name].getCoordinates(glyf)
        start = 0
        for end in end_pts:
            contours.append([
                (x + px * scale, baseline - py * scale, bool(flags[i] & 1))
                for i, (px, py) in enumerate(coords[start:end + 1], start)
            ])
            start = end + 1
        x += hmtx[name][0] * scale + tracking
    guides = {
        "cap": baseline - os2.sCapHeight * scale,
        "x": baseline - os2.sxHeight * scale,
        "base": baseline,
    }
    return pen.getCommands(), contours, guides, x - tracking - X0


def wireframe(contours):
    """Control polygons plus anchor (square) and handle (circle) markers, like a font editor's outline view."""
    polys, anchors, handles = [], [], []
    for pts in contours:
        polys.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y, _ in pts) + "Z")
        for x, y, on in pts:
            if on:
                anchors.append(f"M{x - 2.5:.1f} {y - 2.5:.1f}h5v5h-5z")
            else:
                handles.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2"/>')
    return "".join(polys), "".join(anchors), "".join(handles)


def hero(theme, outline, contours, guides, name_w):
    c = THEMES[theme]
    polys, anchors, handles = wireframe(contours)
    end = X0 + name_w + 28  # where the playhead parks
    H = round(guides["base"] + 56)
    guide_lines = "".join(
        f'<line x1="0" x2="{W}" y1="{y:.1f}" y2="{y:.1f}"/>' for y in guides.values()
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title">
  <title id="title">Solarisx</title>
  <style>
    .sweep {{ animation: sweep {LOOP} cubic-bezier(.65,0,.35,1) infinite; }}
    .rewind {{ animation: rewind {LOOP} cubic-bezier(.65,0,.35,1) infinite; }}
    .solid {{ animation: solid {LOOP} ease-in-out infinite; }}
    .wire {{ animation: wire {LOOP} ease-in-out infinite; }}
    .head {{ animation: sweep {LOOP} cubic-bezier(.65,0,.35,1) infinite, head {LOOP} linear infinite; }}
    @keyframes sweep {{ 0%, 12% {{ transform: translateX(0); }} 52%, 100% {{ transform: translateX({end}px); }} }}
    @keyframes rewind {{ 0%, 12% {{ transform: translateX(0); }} 52%, 86% {{ transform: translateX({end}px); }} 86.1%, 100% {{ transform: translateX(0); }} }}
    @keyframes head {{ 0%, 6% {{ opacity: 0; }} 10%, 54% {{ opacity: 1; }} 60%, 100% {{ opacity: 0; }} }}
    @keyframes solid {{ 0%, 87% {{ opacity: 1; }} 99%, 100% {{ opacity: 0; }} }}
    @keyframes wire {{ 0%, 52% {{ opacity: 1; }} 53%, 86% {{ opacity: 0; }} 99%, 100% {{ opacity: 1; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .sweep, .rewind {{ animation: none; transform: translateX({end}px); }}
      .solid {{ animation: none; }}
      .head {{ display: none; }}
    }}
  </style>
  <defs>
    <clipPath id="done"><rect class="sweep" x="-{W}" width="{W}" height="{H}"/></clipPath>
    <clipPath id="todo"><rect class="rewind" x="0" width="{W * 2}" height="{H}"/></clipPath>
  </defs>
  <g stroke="{c['guide']}" stroke-width="1">{guide_lines}</g>
  <g clip-path="url(#todo)">
   <g class="wire">
    <path d="{outline}" fill="none" stroke="{c['muted']}" stroke-width="1"/>
    <path d="{polys}" fill="none" stroke="{c['guide']}" stroke-width="1"/>
    <path d="{anchors}" fill="none" stroke="{c['fg']}" stroke-width="1"/>
    <g fill="{c['muted']}">{handles}</g>
   </g>
  </g>
  <g clip-path="url(#done)">
    <path class="solid" d="{outline}" fill="{c['fg']}"/>
  </g>
  <g class="head">
    <path d="M-6 8h12v8l-6 6l-6-6z" fill="{c['fg']}"/>
    <line x1="0" x2="0" y1="22" y2="{H - 8}" stroke="{c['fg']}" stroke-width="1"/>
  </g>
</svg>
"""


if __name__ == "__main__":
    parts = build(load_font())
    for theme in THEMES:
        Path(OUT, f"hero-{theme}.svg").write_text(hero(theme, *parts))
