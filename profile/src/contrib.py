"""Contribution-graph candidates, all drawn from the last year of the owner's contribution calendar.

  scope     an oscilloscope: the year as an amplitude-modulated signal swept by a phosphor beam
  skyline   an oblique city of days whose columns rise and fall in a wave
  timeline  an editing timeline: streaks as clips, days as an audio waveform, a scrubbing playhead
  scan      a terminal port scan over the calendar that prints the busiest days as open ports

Writes profile/contrib-<style>-{dark,light}.svg. The README uses skyline.
In Actions: python contrib.py skyline, with GITHUB_TOKEN and GITHUB_REPOSITORY_OWNER set.
Locally: python contrib.py [style ...] calendar.json
"""
import json
import math
import os
import random
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent

THEMES = {
    "dark": {"fg": "#E6EDF3", "muted": "#7D8590", "guide": "#30363D", "faint": "#161B22", "bg": "#0D1117", "side": "#484F58"},
    "light": {"fg": "#1F2328", "muted": "#656D76", "guide": "#D0D7DE", "faint": "#F6F8FA", "bg": "#FFFFFF", "side": "#AFB8C1"},
}
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', 'Liberation Mono', monospace"
QUERY = """query($login: String!) { user(login: $login) { contributionsCollection { contributionCalendar {
  totalContributions weeks { contributionDays { date contributionCount weekday } } } } } }"""


def load(path=None):
    if path:
        data = json.loads(Path(path).read_text())
    else:
        body = json.dumps({"query": QUERY, "variables": {"login": os.environ["GITHUB_REPOSITORY_OWNER"]}}).encode()
        req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json",
        })
        data = json.load(urllib.request.urlopen(req))
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [
        (date.fromisoformat(d["date"]), d["contributionCount"], d["weekday"])
        for w in cal["weeks"] for d in w["contributionDays"]
    ]
    return cal["totalContributions"], days


def kf(name, loop, stops):
    """stops: (seconds, declarations, timing function for the segment that starts at this stop)."""
    body = " ".join(
        f"{100 * t / loop:.3f}% {{ {decl};{f' animation-timing-function: {ease};' if ease else ''} }}"
        for t, decl, ease in stops
    )
    return f"@keyframes {name} {{ {body} }}"


def show(name, loop, on, off, fade=.06):
    return kf(name, loop, [
        (0, "opacity: 0", None), (on, "opacity: 0", None), (on + fade, "opacity: 1", None),
        (off, "opacity: 1", None), (off + .25, "opacity: 0", None), (loop, "opacity: 0", None),
    ])


def nice_date(d):
    return f"{d:%b} {d.day}, {d.year}"


def svg(w, h, title, style, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title">
  <title id="title">{title}</title>
  <style>
    {style}
  </style>
{body}
</svg>
"""


# --- scope -------------------------------------------------------------------------------------------

def scope(theme, total, days):
    c = THEMES[theme]
    W, H, L, R, T, B = 1200, 300, 40, 1160, 22, 278
    cy, loop, sweep, carrier = (T + B) / 2, 6.0, 3.0, 12
    counts = [n for _, n, _ in days]
    n = len(counts)
    env = []
    for i in range(n):
        near = [(math.exp(-((i - j) ** 2) / 2), counts[j]) for j in range(max(0, i - 4), min(n, i + 5))]
        env.append(sum(w * v for w, v in near) / sum(w for w, _ in near))
    emax, amp = max(env) or 1, (B - T) / 2 - 14

    def y_at(x):
        t = (x - L) / (R - L) * (n - 1)
        i = min(int(t), n - 2)
        a = env[i] + (env[i + 1] - env[i]) * (t - i)
        return cy - amp * math.sqrt(a / emax) * math.sin(2 * math.pi * (x - L) / carrier)

    noise = random.Random(7)
    pts = [(x, y_at(x) + noise.uniform(-.9, .9)) for x in range(L, R + 1)]
    trace = "M" + "L".join(f"{x} {y:.1f}" for x, y in pts)
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    samples = 160  # the beam rides the trace at constant horizontal speed, like a real time base
    key_points = [cum[round(k * (len(pts) - 1) / samples)] / cum[-1] for k in range(samples + 1)] + [1]
    key_times = [k / samples * sweep / loop for k in range(samples + 1)] + [1]

    div_w, div_h = (R - L) / 10, (B - T) / 8
    grid = "".join(f'<path d="M{L + k * div_w:.1f} {T}V{B}"/>' for k in range(1, 10)) + "".join(
        f'<path d="M{L} {T + k * div_h:.1f}H{R}"/>' for k in range(1, 8))
    ticks = "".join(f'<path d="M{L + k * div_w / 5:.1f} {cy - 3}v6"/>' for k in range(1, 50)) + "".join(
        f'<path d="M{(L + R) / 2 - 3} {T + k * div_h / 5:.1f}h6"/>' for k in range(1, 40))
    first, last = days[0][0], days[-1][0]
    label = f'font-family="{MONO}" font-size="12" fill="{c["muted"]}"'
    style = "\n    ".join([
        f".sweep {{ animation: sweep {loop}s linear infinite; }}",
        f".glowsweep {{ animation: glowsweep {loop}s linear infinite; }}",
        f".persist {{ animation: persist {loop}s linear infinite; }}",
        f".beam {{ animation: beam {loop}s linear infinite; }}",
        kf("sweep", loop, [(0, "transform: translateX(0)", None), (sweep, f"transform: translateX({R - L}px)", None),
                           (loop, f"transform: translateX({R - L}px)", None)]),
        kf("glowsweep", loop, [(0, "transform: translateX(0)", None),
                               (sweep * (R - L + 300) / (R - L), f"transform: translateX({R - L + 300}px)", None),
                               (loop, f"transform: translateX({R - L + 300}px)", None)]),
        kf("persist", loop, [(0, "opacity: .42", None), (loop - .7, "opacity: .42", None), (loop - .2, "opacity: 0", None),
                             (loop, "opacity: 0", None)]),
        kf("beam", loop, [(0, "opacity: 1", None), (sweep, "opacity: 1", None), (sweep + .05, "opacity: 0", None),
                          (loop, "opacity: 0", None)]),
        f"""@media (prefers-reduced-motion: reduce) {{
      .sweep {{ animation: none; transform: translateX({R - L}px); }}
      .persist {{ animation: none; opacity: .8; }}
      .glowsweep {{ animation: none; transform: translateX({R - L + 300}px); }}
      .beam {{ display: none; }}
    }}""",
    ])
    body = f"""  <defs>
    <path id="trace" d="{trace}"/>
    <clipPath id="swept"><rect class="sweep" x="{L - (R - L) - 4}" y="0" width="{R - L + 4}" height="{H}"/></clipPath>
    <linearGradient id="fade"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient>
    <mask id="glow" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
      <rect class="glowsweep" x="{L - 300}" y="0" width="300" height="{H}" fill="url(#fade)"/>
    </mask>
    <filter id="bloom" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="2.5"/></filter>
  </defs>
  <rect x="{L}" y="{T}" width="{R - L}" height="{B - T}" rx="4" fill="none" stroke="{c['guide']}"/>
  <g stroke="{c['guide']}" stroke-width=".8" stroke-dasharray="1 4">{grid}</g>
  <g stroke="{c['guide']}"><path d="M{L} {cy}H{R}M{(L + R) / 2} {T}V{B}"/>{ticks}</g>
  <path d="M{L - 12} {cy - 5}L{L - 4} {cy}L{L - 12} {cy + 5}Z" fill="{c['muted']}"/>
  <text x="{L + 12}" y="{T + 20}" {label}>CH1</text>
  <text x="{R - 12}" y="{T + 20}" {label} text-anchor="end">{total} contributions</text>
  <text x="{L + 12}" y="{B - 12}" {label}>{nice_date(first)}</text>
  <text x="{R - 12}" y="{B - 12}" {label} text-anchor="end">{nice_date(last)}</text>
  <g clip-path="url(#swept)">
    <use class="persist" href="#trace" xlink:href="#trace" fill="none" stroke="{c['fg']}" stroke-width="1.2"/>
  </g>
  <g mask="url(#glow)" fill="none" stroke="{c['fg']}">
    <use href="#trace" xlink:href="#trace" stroke-width="3.5" opacity=".45" filter="url(#bloom)"/>
    <use href="#trace" xlink:href="#trace" stroke-width="1.5"/>
  </g>
  <g class="beam">
    <circle r="9" fill="{c['fg']}" opacity=".16"/>
    <circle r="2.8" fill="{c['fg']}"/>
    <animateMotion dur="{loop}s" repeatCount="indefinite" calcMode="linear"
      keyPoints="{';'.join(f'{p:.4f}' for p in key_points)}"
      keyTimes="{';'.join(f'{t:.4f}' for t in key_times)}"><mpath href="#trace" xlink:href="#trace"/></animateMotion>
  </g>"""
    return svg(W, H, f"{total} contributions in the last year, drawn as a signal on an oscilloscope", style, body)


# --- skyline -----------------------------------------------------------------------------------------

def skyline(theme, total, days):
    c = THEMES[theme]
    W, H, loop = 1200, 380, 9.0
    U, V, HMAX, GAP = (19.0, 3.3), (6.2, -5.0), 95, .12
    start = days[0][0] - timedelta(days=days[0][2])
    cells = [((d - start).days // 7, wd, n, d) for d, n, wd in days]
    weeks = cells[-1][0] + 1
    top_n = max(n for _, _, n, _ in cells) or 1
    first_active = min((w for w, _, n, _ in cells if n), default=0)  # the wave starts at the first busy week, not on empty floor
    x0 = (W - (weeks * U[0] + 7 * V[0])) / 2
    y0 = H - 46 - weeks * U[1]
    # Side faces stand on edges that run along U or V. Drawn as rects inside a skewY group, their base stays
    # on that edge while a plain CSS scaleY grows them, so no per-frame path morphing is needed.
    tan_u, tan_v = U[1] / U[0], V[1] / V[0]
    skew_u, skew_v = math.degrees(math.atan(tan_u)), math.degrees(math.atan(tan_v))

    def P(w, d, h=0.0):
        return x0 + w * U[0] + d * V[0], y0 + w * U[1] + d * V[1] - h

    def quad(points):
        return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in points) + "Z"

    def side(p, q, h, tan, skew, cls):
        return (f'<g transform="skewY({skew:.3f})"><rect class="{cls}" x="{p[0]:.1f}" y="{p[1] - p[0] * tan - h:.1f}" '
                f'width="{q[0] - p[0]:.1f}" height="{h:.1f}"/></g>')

    floor = {}
    columns = []
    for w, d, n, day in sorted(cells, key=lambda c: (-c[1], c[0])):
        a, b, cc, e = (w + GAP, d + GAP), (w + 1 - GAP, d + GAP), (w + 1 - GAP, d + 1 - GAP), (w + GAP, d + 1 - GAP)
        floor.setdefault(w, []).append(quad([P(*a), P(*b), P(*cc), P(*e)]))
        if not n:
            continue
        h = max(6, HMAX * math.sqrt(n / top_n))
        delay = .6 + (w - first_active) * .035 + (6 - d) * .02
        columns.append(
            f'<g style="--d: {delay:.2f}s; --h: {h:.1f}px">'
            + side(P(*a), P(*b), h, tan_u, skew_u, "f")
            + side(P(*b), P(*cc), h, tan_v, skew_v, "r")
            + f'<path class="t" d="{quad([P(*a, h), P(*b, h), P(*cc, h), P(*e, h)])}"/></g>'
        )
    tiles = "".join(
        f'<path class="tile" style="animation-delay: {w * .02:.2f}s" d="{"".join(paths)}"/>' for w, paths in sorted(floor.items())
    )
    months = "".join(
        f'<text x="{P(w + .5, -1.6)[0]:.1f}" y="{P(w + .5, -1.6)[1]:.1f}">{day:%b}</text>'
        for w, _, _, day in cells if day.day == 1
    )
    style = "\n    ".join([
        ".f, .r, .t { vector-effect: non-scaling-stroke; }",
        f".f, .r {{ transform-box: fill-box; transform-origin: 50% 100%; animation: rise {loop}s infinite both; animation-delay: var(--d); }}",
        f".t {{ animation: lift {loop}s infinite both; animation-delay: var(--d); }}",
        f".tile {{ animation: tile {loop}s infinite both; }}",
        kf("rise", loop, [(0, "transform: scaleY(0)", "cubic-bezier(.2,.9,.3,1)"), (.75, "transform: scaleY(1)", None),
                          (6.0, "transform: scaleY(1)", "cubic-bezier(.6,0,.9,.4)"), (6.6, "transform: scaleY(0)", None),
                          (loop, "transform: scaleY(0)", None)]),
        # The roof starts on the floor as the day's footprint and rides up with the walls.
        kf("lift", loop, [(0, "transform: translateY(var(--h))", "cubic-bezier(.2,.9,.3,1)"), (.75, "transform: translateY(0)", None),
                          (6.0, "transform: translateY(0)", "cubic-bezier(.6,0,.9,.4)"), (6.6, "transform: translateY(var(--h))", None),
                          (loop, "transform: translateY(var(--h))", None)]),
        kf("tile", loop, [(0, "opacity: 0", None), (.35, "opacity: 1", None), (8.2, "opacity: 1", None),
                          (8.6, "opacity: 0", None), (loop, "opacity: 0", None)]),
        "@media (prefers-reduced-motion: reduce) { .f, .r, .t, .tile { animation: none; } }",
    ])
    body = f"""  <defs>
    <pattern id="hatch" width="3.2" height="3.2" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="3.2" height="3.2" fill="{c['bg']}"/><path d="M0 0V3.2" stroke="{c['fg']}" stroke-width="1.1"/>
    </pattern>
  </defs>
  <text x="{x0:.0f}" y="28" font-family="{MONO}" font-size="12" fill="{c['muted']}">{total} contributions in the last year</text>
  <g fill="none" stroke="{c['muted']}" stroke-opacity=".38" stroke-width=".8">{tiles}</g>
  <g stroke="{c['fg']}" stroke-width=".6" stroke-linejoin="round">
    <style>.f {{ fill: url(#hatch); }} .r {{ fill: {c['side']}; }} .t {{ fill: {c['fg']}; }}</style>
    {''.join(columns)}
  </g>
  <g font-family="{MONO}" font-size="11" fill="{c['muted']}" text-anchor="middle">{months}</g>"""
    return svg(W, H, f"{total} contributions in the last year, as a city of days", style, body)


# --- timeline ----------------------------------------------------------------------------------------

def timeline(theme, total, days):
    c = THEMES[theme]
    W, H, loop, play = 1200, 258, 8.0, 7.2
    X0, X1 = 100, 1184
    RULER, V1, A1, A2 = (14, 40), (50, 88), (98, 182), (192, 242)
    counts = [n for _, n, _ in days]
    n, top_n = len(counts), max(counts) or 1
    px = (X1 - X0) / n

    clips, i = [], 0  # streaks of activity, allowing one quiet day inside a clip
    while i < n:
        if not counts[i]:
            i += 1
            continue
        j = i
        while j < n and (counts[j] or (j + 1 < n and counts[j + 1])):
            j += 1
        clips.append((i, j, sum(counts[i:j])))
        i = j
    avg = [sum(counts[max(0, k - 3):k + 4]) / len(counts[max(0, k - 3):k + 4]) for k in range(n)]
    avg_top = max(avg) or 1

    def layer(stroke, fill, text, wave, fill_opacity):
        out = []
        for a, b, s in clips:
            x, w = X0 + a * px, max(3, (b - a) * px - 1)
            out.append(f'<rect x="{x:.1f}" y="{V1[0] + 2}" width="{w:.1f}" height="{V1[1] - V1[0] - 4}" rx="3" '
                       f'fill="{fill}" fill-opacity="{fill_opacity}" stroke="{stroke}"/>')
            if w >= 24:
                out.append(f'<text x="{x + 5:.1f}" y="{(V1[0] + V1[1]) / 2 + 4:.1f}" fill="{text}">{s}</text>')
        mid, half = (A1[0] + A1[1]) / 2, (A1[1] - A1[0]) / 2 - 4
        bars = "".join(
            f"M{X0 + k * px + .4:.1f} {mid - hh:.1f}h{px - .8:.2f}v{2 * hh:.1f}h{-(px - .8):.2f}z"
            for k, v in enumerate(counts) for hh in [max(.6, half * math.sqrt(v / top_n))]
        )
        out.append(f'<path d="{bars}" fill="{wave}"/>')
        mid2, half2 = (A2[0] + A2[1]) / 2, (A2[1] - A2[0]) / 2 - 3
        top = [(X0 + (k + .5) * px, mid2 - max(.5, half2 * math.sqrt(v / avg_top))) for k, v in enumerate(avg)]
        bed = top + [(x, 2 * mid2 - y) for x, y in reversed(top)]
        out.append(f'<path d="M{"L".join(f"{x:.1f} {y:.1f}" for x, y in bed)}Z" fill="{wave}" fill-opacity=".8"/>')
        return "".join(out)

    ruler = [f'<path d="M{X0} {RULER[1]}H{X1}" stroke="{c["guide"]}"/>']
    for k, (d, _, wd) in enumerate(days):
        x = X0 + k * px
        if d.day == 1:
            ruler.append(f'<path d="M{x:.1f} {RULER[1] - 11}V{RULER[1]}" stroke="{c["muted"]}"/>'
                         f'<text x="{x + 3:.1f}" y="{RULER[1] - 5}">{d:%b}</text>')
        elif wd == 0:
            ruler.append(f'<path d="M{x:.1f} {RULER[1] - 4}V{RULER[1]}" stroke="{c["guide"]}"/>')
    busiest = sorted(range(n), key=lambda k: -counts[k])[:5]
    markers = "".join(f'<path d="M{X0 + (k + .5) * px - 4:.1f} {RULER[0]}h8v5l-4 4l-4-4z"/>' for k in busiest)

    frames = int(loop * 24)
    tc = "".join(
        f'<tspan x="14" dy="{0 if k == 0 else 14}">00:00:{k // 24:02d}:{k % 24:02d}</tspan>' for k in range(frames)
    )
    lanes = "".join(f'<rect x="{X0}" y="{a}" width="{X1 - X0}" height="{b - a}" rx="3"/>' for a, b in (V1, A1, A2))
    heads = "".join(f'<text x="86" y="{(a + b) / 2 + 4:.0f}" text-anchor="end">{t}</text>'
                    for t, (a, b) in (("V1", V1), ("A1", A1), ("A2", A2)))
    span = X1 - X0
    style = "\n    ".join([
        f".play {{ animation: play {loop}s linear infinite; }}",
        f".tc {{ animation: tc {loop}s steps({frames}) infinite; }}",
        kf("play", loop, [(0, f"transform: translateX(-{span}px)", None), (play, "transform: translateX(0)", None),
                          (loop, "transform: translateX(0)", None)]),
        f"@keyframes tc {{ from {{ transform: translateY(0); }} to {{ transform: translateY(-{frames * 14}px); }} }}",
        """@media (prefers-reduced-motion: reduce) {
      .play, .tc { animation: none; }
      .head { display: none; }
    }""",
    ])
    body = f"""  <defs>
    <clipPath id="played"><rect class="play" x="{X0 - 2}" y="0" width="{span + 4}" height="{H}"/></clipPath>
    <clipPath id="tcwin"><rect x="10" y="{RULER[0] + 6}" width="84" height="16"/></clipPath>
  </defs>
  <g fill="{c['faint']}">{lanes}</g>
  <g font-family="{MONO}" font-size="11" fill="{c['muted']}">{heads}{''.join(ruler)}</g>
  <g fill="{c['muted']}">{markers}</g>
  <g font-family="{MONO}" font-size="10" stroke-width=".8" opacity=".55">{layer(c['muted'], c['muted'], c['muted'], c['muted'], .18)}</g>
  <g clip-path="url(#played)" font-family="{MONO}" font-size="10" stroke-width=".8">{layer(c['fg'], c['fg'], c['fg'], c['fg'], .2)}</g>
  <g class="head">
    <g class="play"><g transform="translate({span} 0)">
      <path d="M{X0 - 6} {RULER[0] - 4}h12v7l-6 6l-6-6z" fill="{c['fg']}"/>
      <path d="M{X0} {RULER[0] + 9}V{H - 6}" stroke="{c['fg']}" stroke-width="1.25"/>
    </g></g>
  </g>
  <g clip-path="url(#tcwin)"><text class="tc" y="{RULER[0] + 18}" font-family="{MONO}" font-size="11" fill="{c['fg']}">{tc}</text></g>"""
    return svg(W, H, f"{total} contributions in the last year, laid out as an editing timeline", style, body)


# --- scan --------------------------------------------------------------------------------------------

def scan(theme, total, days):
    c = THEMES[theme]
    W, H, loop, cw = 1200, 290, 10.0, 7.83  # cw: advance of a 13px monospace glyph
    t_scan, dt, t_out = 1.1, .045, 9.4
    gx, gy, pitch, cell = 28, 104, 16, 12
    start = days[0][0] - timedelta(days=days[0][2])
    top_n = max(n for _, n, _ in days) or 1
    weeks = (days[-1][0] - start).days // 7 + 1
    active = sum(1 for _, n, _ in days if n)

    def col_of(d):
        return (d - start).days // 7

    styles, cols = [], []
    for k in range(weeks):
        cells = []
        for d, n, wd in days:
            if col_of(d) != k:
                continue
            x, y = gx + k * pitch, gy + wd * pitch
            if n:
                op = .3 + .7 * math.sqrt(n / top_n)
                cells.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{c["fg"]}" fill-opacity="{op:.2f}"/>')
            else:
                cells.append(f'<circle cx="{x + cell / 2}" cy="{y + cell / 2}" r="1.3" fill="{c["muted"]}"/>')
        cols.append(f'<g class="c{k}">{"".join(cells)}</g>')
        styles.append(f".c{k} {{ animation: c{k} {loop}s infinite both; }}")
        styles.append(show(f"c{k}", loop, t_scan + k * dt + .02, t_out, fade=.04))

    hits = sorted(sorted(days, key=lambda d: -d[1])[:6], key=lambda d: d[0])
    rx, ry, lh = 912, 116, 16
    lines = [f'<text class="r0" x="{rx}" y="{ry}" xml:space="preserve" fill="{c["muted"]}">DAY         STATE  COUNT</text>']
    styles += [f".r0 {{ animation: r0 {loop}s infinite both; }}", show("r0", loop, t_scan - .1, t_out)]
    for i, (d, n, _) in enumerate(hits, 1):
        lines.append(f'<text class="r{i}" x="{rx}" y="{ry + i * lh}" xml:space="preserve" fill="{c["fg"]}">'
                     f'{d.isoformat()}  open   {n}</text>')
        styles += [f".r{i} {{ animation: r{i} {loop}s infinite both; }}",
                   show(f"r{i}", loop, t_scan + col_of(d) * dt + .1, t_out)]

    cmd = "nmap -sV --days 365 iridescentglow"
    typed = len("$ " + cmd)
    t_done = t_scan + weeks * dt + .2
    styles += [
        f".type {{ animation: type {loop}s infinite both; }}",
        kf("type", loop, [(0, f"transform: translateX(-{typed * cw:.0f}px)", None),
                          (.15, f"transform: translateX(-{typed * cw:.0f}px)", f"steps({typed}, jump-none)"),
                          (.8, "transform: translateX(0)", None), (t_out, "transform: translateX(0)", None),
                          (t_out + .01, f"transform: translateX(-{typed * cw:.0f}px)", None),
                          (loop, f"transform: translateX(-{typed * cw:.0f}px)", None)]),
        f".l2 {{ animation: l2 {loop}s infinite both; }}", show("l2", loop, .9, t_out),
        f".done {{ animation: done {loop}s infinite both; }}", show("done", loop, t_done, t_out),
        f".prompt {{ animation: prompt {loop}s infinite both; }}", show("prompt", loop, t_done + .25, t_out),
        ".blink { animation: blink 1s steps(1) infinite; }",
        "@keyframes blink { 50% { opacity: 0; } }",
        f".cursor {{ animation: cursor {loop}s infinite both; }}",
        show("cursor", loop, t_scan, t_scan + weeks * dt - .25, fade=.02),
        f".step {{ animation: step {loop}s infinite both; }}",
        kf("step", loop, [(0, "transform: translateX(0)", None),
                          (t_scan, "transform: translateX(0)", f"steps({weeks}, jump-none)"),
                          (t_scan + weeks * dt, f"transform: translateX({(weeks - 1) * pitch}px)", None),
                          (loop, f"transform: translateX({(weeks - 1) * pitch}px)", None)]),
        """@media (prefers-reduced-motion: reduce) {
      * { animation: none !important; }
      .cursor { display: none; }
    }""",
    ]
    body = f"""  <defs><clipPath id="typed"><rect class="type" x="24" y="40" width="{typed * cw + 4:.0f}" height="26"/></clipPath></defs>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="{c['guide']}"/>
  <path d="M0 32H{W}" stroke="{c['guide']}"/>
  <g fill="{c['guide']}"><circle cx="20" cy="16" r="5"/><circle cx="37" cy="16" r="5"/><circle cx="54" cy="16" r="5"/></g>
  <g font-family="{MONO}" font-size="13">
    <text x="{W / 2}" y="21" text-anchor="middle" font-size="12" fill="{c['muted']}">solarisx@arch: ~</text>
    <text x="28" y="60" clip-path="url(#typed)" fill="{c['fg']}"><tspan fill="{c['muted']}">$ </tspan>{cmd}</text>
    <text class="l2" x="28" y="84" fill="{c['muted']}">Scanning {len(days)} days of github.com/IridescentGlow</text>
    <g class="cursor"><rect class="step" x="{gx - 2}" y="{gy - 4}" width="{cell + 4}" height="{7 * pitch + 4}" rx="3" fill="{c['guide']}" fill-opacity=".7"/></g>
    {''.join(cols)}
    {''.join(lines)}
    <text class="done" x="28" y="{gy + 7 * pitch + 30}" fill="{c['muted']}">Done: <tspan fill="{c['fg']}">{len(days)} days scanned, {active} open, {total} contributions</tspan></text>
    <g class="prompt"><text x="28" y="{gy + 7 * pitch + 54}" fill="{c['muted']}">$</text>
      <rect class="blink" x="{28 + 2 * cw:.0f}" y="{gy + 7 * pitch + 43}" width="8" height="14" fill="{c['fg']}"/></g>
  </g>"""
    return svg(W, H, f"{total} contributions in the last year, scanned day by day like ports", "\n    ".join(styles), body)


STYLES = {"scope": scope, "skyline": skyline, "timeline": timeline, "scan": scan}

if __name__ == "__main__":
    # python contrib.py [style ...] [calendar.json]; with no style named, builds them all.
    args = sys.argv[1:]
    total, days = load(next((a for a in args if a.endswith(".json")), None))
    for name in [a for a in args if a in STYLES] or STYLES:
        for theme in THEMES:
            Path(OUT, f"contrib-{name}-{theme}.svg").write_text(STYLES[name](theme, total, days))
