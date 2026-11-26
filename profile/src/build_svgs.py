"""Builds the README hero (the name drawn as its own vector construction, rendered by a sweeping playhead)
the gray tool/social icons and the Ko-fi button.

Writes profile/hero-{dark,light}.svg, profile/kofi-{dark,light}.svg and profile/icons/*.svg. Needs fonttools, network access and Bricolage Grotesque:
  curl -L -o Bricolage.ttf "https://github.com/google/fonts/raw/main/ofl/bricolagegrotesque/BricolageGrotesque%5Bopsz,wdth,wght%5D.ttf"
  python build_svgs.py Bricolage.ttf
"""
import re
import sys
import urllib.request
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

OUT = Path(__file__).resolve().parent.parent

# GitHub's own foreground / muted / border colors, so the hero sits on the page instead of in a box.
THEMES = {
    "dark": {"fg": "#E6EDF3", "muted": "#7D8590", "guide": "#30363D", "border": "#3D444D"},
    "light": {"fg": "#1F2328", "muted": "#8C959F", "guide": "#D0D7DE", "border": "#D0D7DE"},
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


def text_path(font, text, size, x, baseline):
    """Outlines `text` starting at x; returns (path d, advance width)."""
    cmap, hmtx, glyphs = font.getBestCmap(), font["hmtx"], font.getGlyphSet()
    scale = size / font["head"].unitsPerEm
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}")
    start = x
    for ch in text:
        name = cmap[ord(ch)]
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, baseline)))
        x += hmtx[name][0] * scale
    return pen.getCommands(), x - start


def kofi_button(theme, font):
    """A quiet outlined pill: the Ko-fi cup plus "Buy me a coffee" in the hero's typeface."""
    c = THEMES[theme]
    cup = re.search(r' d="([^"]+)"', Path(OUT, "icons", "kofi.svg").read_text()).group(1)
    size, icon, gap, pad_x, h = 18, 20, 12, 26, 52
    _, text_w = text_path(font, "Buy me a coffee", size, 0, 0)
    w = round(pad_x * 2 + icon + gap + text_w)
    d, _ = text_path(font, "Buy me a coffee", size, pad_x + icon + gap, h / 2 + size * .36)
    s = icon / 24
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Buy me a coffee on Ko-fi">
  <title>Buy me a coffee on Ko-fi</title>
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{(h - 1) / 2}" fill="none" stroke="{c['border']}"/>
  <path transform="translate({pad_x} {(h - icon) / 2}) scale({s})" d="{cup}" fill="{c['fg']}"/>
  <path d="{d}" fill="{c['fg']}"/>
</svg>
"""


# simple-icons 9 is the last release with the Adobe, Ableton and LinkedIn marks; Hyprland arrived later.
ICONS = {
    "react": 9, "nextdotjs": 9, "javascript": 9, "tailwindcss": 9, "css3": 9, "vite": 9,
    "python": 9, "cplusplus": 9, "openjdk": 9, "git": 9, "linux": 9, "archlinux": 9, "hyprland": 13,
    "figma": 9, "adobephotoshop": 9, "adobeaftereffects": 9, "adobepremierepro": 9, "abletonlive": 9,
    "linkedin": 9, "telegram": 9, "instagram": 9, "gmail": 9, "discord": 9, "kofi": 9,
}
ICON_GRAY = "#8B949E"  # GitHub's muted gray; readable on both the light and dark page


def icons():
    out = Path(OUT, "icons")
    out.mkdir(exist_ok=True)
    for slug, version in ICONS.items():
        url = f"https://cdn.jsdelivr.net/npm/simple-icons@{version}/icons/{slug}.svg"
        src = urllib.request.urlopen(url).read().decode()
        title = re.search(r"<title>(.*?)</title>", src).group(1)
        d = re.search(r'<path d="([^"]+)"', src).group(1)
        Path(out, f"{slug}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" role="img" aria-label="{title}">'
            f'<title>{title}</title><path fill="{ICON_GRAY}" d="{d}"/></svg>\n'
        )


if __name__ == "__main__":
    icons()
    font = load_font()
    parts = build(font)
    for theme in THEMES:
        Path(OUT, f"hero-{theme}.svg").write_text(hero(theme, *parts))
        Path(OUT, f"kofi-{theme}.svg").write_text(kofi_button(theme, font))
