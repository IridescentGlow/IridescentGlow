"""Builds the hand-made README SVGs (hero, now panel, section labels, ko-fi button).

Text is converted to outlines so it renders identically everywhere GitHub shows the image.
Needs fonttools and the Syne variable font:
  curl -L -o Syne.ttf "https://github.com/google/fonts/raw/main/ofl/syne/Syne%5Bwght%5D.ttf"
  python build_svgs.py Syne.ttf
"""
import random
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

OUT = Path(__file__).resolve().parent.parent

INK = "#0E0B24"
PANEL = "#15112E"
BORDER = "#2A2450"
MIST = "#CFC8EA"
DIM = "#8A82B0"
VIOLET, TEAL, GOLD, ROSE = "#7C5CFF", "#2EE6D6", "#F5D06F", "#FF5FA2"

_fonts = {}


def font(weight):
    if weight not in _fonts:
        _fonts[weight] = instantiateVariableFont(TTFont(sys.argv[1]), {"wght": weight})
    return _fonts[weight]


def text_width(text, size, weight, tracking=0):
    f = font(weight)
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    scale = size / f["head"].unitsPerEm
    return sum(hmtx[cmap[ord(c)]][0] * scale + tracking for c in text) - tracking


def text_path(text, size, weight, x, y, tracking=0, anchor="start"):
    """Returns an SVG path `d` for `text` with its baseline at y."""
    f = font(weight)
    cmap, hmtx, glyphs = f.getBestCmap(), f["hmtx"], f.getGlyphSet()
    scale = size / f["head"].unitsPerEm
    if anchor == "middle":
        x -= text_width(text, size, weight, tracking) / 2
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}")
    for c in text:
        name = cmap[ord(c)]
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
        x += hmtx[name][0] * scale + tracking
    return pen.getCommands()


IRIDESCENT_STOPS = f"""
      <stop offset="0" stop-color="{VIOLET}"/>
      <stop offset=".32" stop-color="{TEAL}"/>
      <stop offset=".6" stop-color="{GOLD}"/>
      <stop offset=".85" stop-color="{ROSE}"/>
      <stop offset="1" stop-color="{VIOLET}"/>"""

REDUCED_MOTION = "@media (prefers-reduced-motion: reduce) { * { animation: none !important; } }"


def hero():
    w, h = 1200, 420
    cx, cy = 905, 210
    rng = random.Random(7)
    stars = "".join(
        f'<circle cx="{rng.uniform(0, w):.0f}" cy="{rng.uniform(0, h):.0f}" '
        f'r="{rng.uniform(.5, 1.4):.1f}" opacity="{rng.uniform(.15, .6):.2f}"/>'
        for _ in range(70)
    )

    name = "Solarisx"
    size = 132
    while text_width(name, size, 800, -2) > 700:
        size -= 2
    name_d = text_path(name, size, 800, 70, 235, tracking=-2)
    handle_d = text_path("@IridescentGlow", 17, 600, 72, 64)
    line1_d = text_path("Front-end developer and EE student", 28, 600, 72, 296)
    line2_d = text_path("7+ years of video editing, now learning offensive security", 20, 500, 72, 336)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title">
  <title id="title">Solarisx: front-end developer and EE student with 7+ years of video editing, now learning offensive security</title>
  <style>
    .corona {{ transform-origin: {cx}px {cy}px; animation: spin 48s linear infinite; }}
    .rim {{ transform-origin: {cx}px {cy}px; animation: spin 70s linear infinite reverse; }}
    .film {{ animation: drift 16s linear infinite; }}
    .glint {{ transform-origin: {cx}px {cy}px; animation: glint 6s ease-in-out infinite; }}
    .rise {{ animation: rise 1.4s cubic-bezier(.2,.7,.2,1) both; }}
    .rise2 {{ animation: rise 1.4s .25s cubic-bezier(.2,.7,.2,1) both; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    @keyframes drift {{ to {{ transform: translateX(-1200px); }} }}
    @keyframes glint {{ 0%, 100% {{ opacity: .55; }} 50% {{ opacity: 1; }} }}
    @keyframes rise {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}
    {REDUCED_MOTION}
  </style>
  <defs>
    <clipPath id="frame"><rect width="{w}" height="{h}" rx="22"/></clipPath>
    <linearGradient id="film" x1="0" y1="0" x2="600" y2="0" gradientUnits="userSpaceOnUse" spreadMethod="reflect">{IRIDESCENT_STOPS}
    </linearGradient>
    <linearGradient id="ringA" x1="0" y1="0" x2="1" y2="1">{IRIDESCENT_STOPS}
    </linearGradient>
    <linearGradient id="ringB" x1="1" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{GOLD}"/>
      <stop offset=".5" stop-color="{VIOLET}" stop-opacity=".2"/>
      <stop offset="1" stop-color="{TEAL}"/>
    </linearGradient>
    <radialGradient id="halo">
      <stop offset=".45" stop-color="{VIOLET}" stop-opacity=".38"/>
      <stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/>
    </radialGradient>
    <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="16"/></filter>
    <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>
    <clipPath id="name"><path d="{name_d}"/></clipPath>
  </defs>
  <g clip-path="url(#frame)">
    <rect width="{w}" height="{h}" fill="{INK}"/>
    <g fill="{MIST}">{stars}</g>
    <circle cx="{cx}" cy="{cy}" r="330" fill="url(#halo)"/>
    <g class="corona">
      <circle cx="{cx}" cy="{cy}" r="146" fill="none" stroke="url(#ringA)" stroke-width="34" filter="url(#blur)"/>
      <circle cx="{cx}" cy="{cy}" r="136" fill="none" stroke="url(#ringA)" stroke-width="7" filter="url(#soft)"/>
    </g>
    <g class="rim">
      <circle cx="{cx}" cy="{cy}" r="130" fill="none" stroke="url(#ringB)" stroke-width="2.5"/>
    </g>
    <circle cx="{cx}" cy="{cy}" r="128" fill="#08061A"/>
    <g class="glint">
      <circle cx="{cx + 92}" cy="{cy - 90}" r="10" fill="#FFF6DA" filter="url(#soft)"/>
      <circle cx="{cx + 92}" cy="{cy - 90}" r="3.5" fill="#FFFFFF"/>
    </g>
    <path class="rise" d="{handle_d}" fill="{DIM}"/>
    <g class="rise" clip-path="url(#name)">
      <rect class="film" width="2400" height="{h}" fill="url(#film)"/>
    </g>
    <g class="rise2">
      <path d="{line1_d}" fill="{MIST}"/>
      <path d="{line2_d}" fill="{DIM}"/>
    </g>
  </g>
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="21.5" fill="none" stroke="{BORDER}"/>
</svg>
"""


def now_panel():
    items = [
        "Learning offensive security, working through VulnHub boxes",
        "Building a small home lab",
        "Building a premium developer portfolio with Next.js and Tailwind",
    ]
    w, top, step = 1200, 112, 52
    h = top + step * (len(items) - 1) + 52
    rows = []
    for i, item in enumerate(items):
        y = top + i * step
        rows.append(
            f'<circle cx="90" cy="{y - 7}" r="8" fill="none" stroke="url(#iri)" stroke-width="3"/>'
            f'<path d="{text_path(item, 22, 500, 120, y)}" fill="{MIST}"/>'
        )
    title_d = text_path("Right now", 26, 700, 72, 62)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title">
  <title id="title">Right now: {"; ".join(items)}</title>
  <defs>
    <linearGradient id="iri" x1="0" y1="0" x2="1" y2="1">{IRIDESCENT_STOPS}
    </linearGradient>
  </defs>
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="21.5" fill="{PANEL}" stroke="{BORDER}"/>
  <path d="{title_d}" fill="{GOLD}"/>
  {"".join(rows)}
</svg>
"""


def label(text, name):
    """Writes label-<name>.svg (gold, for dark mode) and label-<name>-light.svg (violet, for light mode)."""
    size, weight = 26, 700
    w = round(text_width(text, size, weight)) + 4
    d = text_path(text, size, weight, 2, 30)
    for suffix, color in (("", GOLD), ("-light", "#4B2FB8")):
        Path(OUT, f"label-{name}{suffix}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="40" viewBox="0 0 {w} 40" role="img" aria-label="{text}">'
            f'<path d="{d}" fill="{color}"/></svg>\n'
        )


def kofi():
    w, h = 360, 64
    d = text_path("Buy me a coffee on Ko-fi", 20, 600, w / 2, 39, anchor="middle")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Buy me a coffee on Ko-fi">
  <style>
    .film {{ animation: drift 10s linear infinite; }}
    @keyframes drift {{ to {{ transform: translateX(-720px); }} }}
    {REDUCED_MOTION}
  </style>
  <defs>
    <linearGradient id="film" x1="0" y1="0" x2="360" y2="0" gradientUnits="userSpaceOnUse" spreadMethod="reflect">{IRIDESCENT_STOPS}
    </linearGradient>
    <clipPath id="pill"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{(h - 2) / 2}"/></clipPath>
  </defs>
  <g clip-path="url(#pill)">
    <rect class="film" width="{w * 4}" height="{h}" fill="url(#film)"/>
    <rect x="3" y="3" width="{w - 6}" height="{h - 6}" rx="{(h - 6) / 2}" fill="{PANEL}"/>
  </g>
  <path d="{d}" fill="{MIST}"/>
</svg>
"""


if __name__ == "__main__":
    Path(OUT, "hero.svg").write_text(hero())
    Path(OUT, "now.svg").write_text(now_panel())
    Path(OUT, "kofi.svg").write_text(kofi())
    label("Tools I use", "tools")
    label("Activity", "activity")
    label("Featured work", "featured")
