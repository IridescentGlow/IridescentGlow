"""Builds the README hero, the gray tool icons, the animated social icons and the Ko-fi button.

The hero builds the name the way a type designer would, then lets it go again, on a loop:
guides draw in, each glyph's on/off-curve points are plotted along the contour, the control
polygon connects them, a pen traces the real outline, the letter is engraved with diagonal hatch
lines, and the hatching thickens until it merges into solid ink. After a hold the ink splits back
into hatching, the hatch lines slide away and the outline lets go.

Writes profile/hero-{dark,light}.svg, profile/kofi-{dark,light}.svg, profile/icons/*.svg and profile/icons/social-*.svg.
Needs fonttools, network access and Bricolage Grotesque:
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

NAME = "SolarisX"
W = 1200
MARGIN = 24
TRACKING = -0.025  # in em

# Timeline, in seconds of one loop. Every glyph runs the same timeline, offset by LETTER_STAGGER.
LOOP = 13.0
LETTER_STAGGER = 0.1
POINT_STAGGER = 0.01
IN_OUT = "cubic-bezier(.65,0,.35,1)"
TRACE = "cubic-bezier(.45,0,.55,1)"
TRACE_SPLINE = ".45 0 .55 1"  # same curve for the SMIL pen so it stays on the tip of the CSS-drawn line
POP = "cubic-bezier(.34,1.56,.64,1)"
SWELL = "cubic-bezier(.5,0,.25,1)"
TRACE_START, TRACE_END = 1.8, 3.8
HATCH_GAP = 7  # perpendicular distance between hatch lines
HATCH_INK = HATCH_GAP + 1.5  # stroke width at which neighbouring hatch lines overlap into solid
HATCH_STAGGER = 0.012


def load_font():
    return instantiateVariableFont(TTFont(sys.argv[1]), {"opsz": 96, "wdth": 100, "wght": 700})


def build(font):
    """Lays the name out across the full width. Returns per-glyph geometry, guide heights and the SVG height."""
    cmap, hmtx, glyf = font.getBestCmap(), font["hmtx"], font["glyf"]
    glyphs, upem, os2 = font.getGlyphSet(), font["head"].unitsPerEm, font["OS/2"]
    names = [cmap[ord(ch)] for ch in NAME]

    advance = sum(hmtx[n][0] / upem + TRACKING for n in names) - TRACKING
    size = (W - 2 * MARGIN) / advance
    scale, tracking = size / upem, TRACKING * size
    y_max = max(glyf[n].yMax for n in names) * scale
    y_min = min(glyf[n].yMin for n in names) * scale
    baseline = MARGIN + y_max

    letters, x = [], MARGIN
    for n in names:
        pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}")
        glyphs[n].draw(TransformPen(pen, (scale, 0, 0, -scale, x, baseline)))
        d = pen.getCommands()
        coords, end_pts, flags = glyf[n].getCoordinates(glyf)
        points, start = [], 0
        for end in end_pts:
            points.append([
                (x + px * scale, baseline - py * scale, bool(flags[i] & 1))
                for i, (px, py) in enumerate(coords[start:end + 1], start)
            ])
            start = end + 1
        xs = [px for c in points for px, _, _ in c]
        ys = [py for c in points for _, py, _ in c]
        letters.append({
            "d": d,
            "bbox": (min(xs), min(ys), max(xs), max(ys)),
            "contours": ["M" + c for c in d.split("M") if c],  # one path per contour so each draws at its own pace
            "points": points,
        })
        x += hmtx[n][0] * scale + tracking
    guides = [baseline - os2.sCapHeight * scale, baseline - os2.sxHeight * scale, baseline]
    return letters, guides, round(baseline - y_min + MARGIN)


def keyframes(name, stops):
    """stops: (seconds, declarations, timing function for the segment that starts at this stop)."""
    body = " ".join(
        f"{100 * t / LOOP:.2f}% {{ {decl};{f' animation-timing-function: {ease};' if ease else ''} }}"
        for t, decl, ease in stops
    )
    return f"@keyframes {name} {{ {body} }}"


def styles():
    return "\n    ".join([
        f".guide {{ stroke-dasharray: 1 1; animation: guide {LOOP}s infinite both; }}",
        f".pt {{ transform-box: fill-box; transform-origin: center; animation: pt {LOOP}s infinite both; }}",
        f".poly {{ stroke-dasharray: 1 1; animation: poly {LOOP}s infinite both; }}",
        f".trace {{ stroke-dasharray: 1 1; animation: trace {LOOP}s infinite both; }}",
        f".pen {{ animation: pen {LOOP}s linear infinite both; }}",
        f".hatch {{ stroke-dasharray: 1 1; animation: hatch {LOOP}s infinite both; }}",
        f".solid {{ animation: solid {LOOP}s linear infinite both; }}",
        keyframes("guide", [
            (0, "stroke-dashoffset: 1", IN_OUT), (1.0, "stroke-dashoffset: 0", None),
            (11.6, "stroke-dashoffset: 0", IN_OUT), (12.4, "stroke-dashoffset: -1", None),
            (LOOP, "stroke-dashoffset: -1", None),
        ]),
        keyframes("pt", [
            (0, "transform: scale(0)", POP), (0.35, "transform: scale(1)", None),
            # Points leave in the same contour order they arrived, finishing before the solid fill takes over.
            (4.2, "transform: scale(1)", IN_OUT), (4.6, "transform: scale(0)", None),
            (LOOP, "transform: scale(0)", None),
        ]),
        keyframes("poly", [
            (0, "stroke-dashoffset: 1; opacity: 1", None),
            (0.9, "stroke-dashoffset: 1; opacity: 1", IN_OUT), (2.0, "stroke-dashoffset: 0; opacity: 1", None),
            (4.6, "stroke-dashoffset: 0; opacity: 1", None), (5.2, "stroke-dashoffset: 0; opacity: 0", None),
            (LOOP, "stroke-dashoffset: 0; opacity: 0", None),
        ]),
        keyframes("trace", [
            (0, "stroke-dashoffset: 1", None),
            (TRACE_START, "stroke-dashoffset: 1", TRACE), (TRACE_END, "stroke-dashoffset: 0", None),
            (10.4, "stroke-dashoffset: 0", IN_OUT), (11.4, "stroke-dashoffset: -1", None),
            (LOOP, "stroke-dashoffset: -1", None),
        ]),
        keyframes("pen", [
            (0, "opacity: 0", None), (TRACE_START - .05, "opacity: 0", None), (TRACE_START + .05, "opacity: 1", None),
            (TRACE_END, "opacity: 1", None), (TRACE_END + .15, "opacity: 0", None), (LOOP, "opacity: 0", None),
        ]),
        # Each hatch line shoots across the letter, then thickens until it overlaps its neighbours.
        keyframes("hatch", [
            (0, "stroke-dashoffset: 1; stroke-width: 1px", None),
            (3.9, "stroke-dashoffset: 1; stroke-width: 1px", IN_OUT),
            (4.25, "stroke-dashoffset: 0; stroke-width: 1px", None),
            (4.6, "stroke-dashoffset: 0; stroke-width: 1px", SWELL),
            (5.1, f"stroke-dashoffset: 0; stroke-width: {HATCH_INK}px", None),
            (9.4, f"stroke-dashoffset: 0; stroke-width: {HATCH_INK}px", IN_OUT),
            (9.8, "stroke-dashoffset: 0; stroke-width: 1px", IN_OUT),
            (10.15, "stroke-dashoffset: -1; stroke-width: 1px", None),
            (LOOP, "stroke-dashoffset: -1; stroke-width: 1px", None),
        ]),
        # The real fill takes over once the last hatch line has merged, and hands back before any of them thin out.
        keyframes("solid", [
            (0, "opacity: 0", None), (5.65, "opacity: 0", None), (5.75, "opacity: 1", None),
            (9.39, "opacity: 1", None), (9.4, "opacity: 0", None), (LOOP, "opacity: 0", None),
        ]),
        """@media (prefers-reduced-motion: reduce) {
      .guide, .solid { animation: none; }
      .pt, .poly, .trace, .pen, .hatch { display: none; }
    }""",
    ])


def hatch_lines(bbox):
    """Diagonal lines (bottom-left to top-right) covering the box, ordered from the top-left corner.
    The box is padded so the butt ends of fully thickened lines still clear the glyph."""
    pad = HATCH_INK + 2
    x0, y0, x1, y1 = bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad
    step = HATCH_GAP * 2 ** .5  # lines are x + y = C; this step gives HATCH_GAP between them
    lines, C = [], x0 + y0 + step / 2
    while C < x1 + y1:
        xa, xb = max(x0, C - y1), min(x1, C - y0)
        if xb - xa > 1:
            lines.append(f"M{xa:.1f} {C - xa:.1f}L{xb:.1f} {C - xb:.1f}")
        C += step
    return lines


def letter_svg(k, letter, c):
    delay = k * LETTER_STAGGER
    late = f' style="animation-delay: {delay:.2f}s"'
    polys, traces, pens, pts = [], [], [], []
    for contour in letter["points"]:
        polys.append(
            f'<path class="poly" pathLength="1"{late} d="M'
            + "L".join(f"{x:.1f} {y:.1f}" for x, y, _ in contour) + 'Z"/>'
        )
    for i, (x, y, on) in enumerate(p for contour in letter["points"] for p in contour):
        style = f' style="animation-delay: {0.3 + delay + i * POINT_STAGGER:.3f}s"'
        if on:
            pts.append(f'<path class="pt"{style} d="M{x - 2.5:.1f} {y - 2.5:.1f}h5v5h-5z"/>')
        else:
            pts.append(f'<circle class="pt"{style} cx="{x:.1f}" cy="{y:.1f}" r="2" fill="{c["muted"]}" stroke="none"/>')
    for d in letter["contours"]:
        traces.append(f'<path class="trace" pathLength="1"{late} d="{d}"/>')
        pens.append(
            f'<circle class="pen" r="3"{late}><animateMotion path="{d}" begin="{delay:.2f}s" dur="{LOOP}s" '
            f'repeatCount="indefinite" calcMode="spline" keyPoints="0;0;1;1" '
            f'keyTimes="0;{TRACE_START / LOOP:.4f};{TRACE_END / LOOP:.4f};1" '
            f'keySplines="0 0 1 1;{TRACE_SPLINE};0 0 1 1"/></circle>'
        )
    hatches = "".join(
        f'<path class="hatch" pathLength="1" style="animation-delay: {delay + j * HATCH_STAGGER:.3f}s" d="{d}"/>'
        for j, d in enumerate(hatch_lines(letter["bbox"]))
    )
    return f"""
  <g>
    <clipPath id="g{k}"><path d="{letter['d']}"/></clipPath>
    <g fill="none" stroke="{c['muted']}" stroke-width=".75">{''.join(polys)}</g>
    <g fill="none" stroke="{c['fg']}" clip-path="url(#g{k})">{hatches}</g>
    <path class="solid"{late} d="{letter['d']}" fill="{c['fg']}"/>
    <g fill="none" stroke="{c['fg']}" stroke-width="1.25">{''.join(traces)}</g>
    <g fill="none" stroke="{c['fg']}" stroke-width="1">{''.join(pts)}</g>
    <g fill="{c['fg']}">{''.join(pens)}</g>
  </g>"""


def hero(theme, letters, guides, h):
    c = THEMES[theme]
    guide_paths = "".join(
        f'<path class="guide" pathLength="1" style="animation-delay: {i * .12:.2f}s" d="M0 {y:.1f}H{W}"/>'
        for i, y in enumerate(guides)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-labelledby="title">
  <title id="title">{NAME}</title>
  <style>
    {styles()}
  </style>
  <g fill="none" stroke="{c['guide']}" stroke-width="1">{guide_paths}</g>{''.join(letter_svg(k, l, c) for k, l in enumerate(letters))}
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


# Brand colours each social icon briefly wipes into: (gradient stops, gradient direction x1 y1 x2 y2).
SOCIALS = {
    "linkedin": (["#2E86DE", "#0A66C2"], (0, 0, 1, 1)),
    "telegram": (["#37AEE2", "#1E96C8"], (0, 0, 0, 1)),
    "instagram": (["#FEDA75", "#FA7E1E", "#D62976", "#962FBF", "#4F5BD5"], (0, 1, 1, 0)),
    "gmail": (["#4285F4", "#EA4335", "#FBBC05", "#34A853"], (0, 0, 1, 0)),
    "discord": (["#7983F5", "#5865F2"], (0, 0, 1, 1)),
    "kofi": (["#FF8A7A", "#FF5E5B"], (0, 0, 1, 1)),
}
SOCIAL_LOOP = 4.0
SOCIAL_STAGGER = 0.12  # the colour ripples across the row, one icon after the next


def social_icons():
    """Gray icon with a brand-coloured copy on top, revealed by a quick feathered wipe every SOCIAL_LOOP seconds."""
    for i, (slug, (colors, (x1, y1, x2, y2))) in enumerate(SOCIALS.items()):
        src = Path(OUT, "icons", f"{slug}.svg").read_text()
        title = re.search(r"<title>(.*?)</title>", src).group(1)
        d = re.search(r' d="([^"]+)"', src).group(1)
        stops = "".join(
            f'<stop offset="{j / (len(colors) - 1):.2f}" stop-color="{col}"/>' for j, col in enumerate(colors)
        )
        pct = lambda t: f"{100 * t / SOCIAL_LOOP:.1f}%"
        Path(OUT, "icons", f"social-{slug}.svg").write_text(f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" role="img" aria-label="{title}">
  <title>{title}</title>
  <style>
    .wipe {{ animation: wipe {SOCIAL_LOOP}s infinite both; animation-delay: {i * SOCIAL_STAGGER:.2f}s; }}
    @keyframes wipe {{
      0%, {pct(1.6)} {{ transform: translateX(0); animation-timing-function: cubic-bezier(.3,0,.2,1); }}
      {pct(1.9)}, {pct(2.5)} {{ transform: translateX(32px); animation-timing-function: cubic-bezier(.6,0,.8,1); }}
      {pct(2.8)}, 100% {{ transform: translateX(64px); }}
    }}
    @media (prefers-reduced-motion: reduce) {{ .wipe {{ animation: none; }} }}
  </style>
  <defs>
    <linearGradient id="brand" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{stops}</linearGradient>
    <linearGradient id="edge">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".2" stop-color="#fff"/>
      <stop offset=".8" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <mask id="reveal" maskUnits="userSpaceOnUse" x="-2" y="-2" width="28" height="28">
      <rect class="wipe" x="-40" y="-4" width="40" height="32" fill="url(#edge)"/>
    </mask>
  </defs>
  <path fill="{ICON_GRAY}" d="{d}"/>
  <path fill="url(#brand)" mask="url(#reveal)" d="{d}"/>
</svg>
""")


if __name__ == "__main__":
    icons()
    social_icons()
    font = load_font()
    parts = build(font)
    for theme in THEMES:
        Path(OUT, f"hero-{theme}.svg").write_text(hero(theme, *parts))
        Path(OUT, f"kofi-{theme}.svg").write_text(kofi_button(theme, font))
