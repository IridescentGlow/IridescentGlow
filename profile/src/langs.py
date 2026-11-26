"""Builds a monochrome "Languages" card from the owner's non-fork repos.

Writes profile/langs-dark.svg and profile/langs-light.svg (same size as the streak card).
Run in Actions with GITHUB_TOKEN and GITHUB_REPOSITORY_OWNER set; stdlib only.
"""
import json
import os
import urllib.request
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
THEMES = {
    "dark": {"fg": "#E6EDF3", "muted": "#7D8590"},
    "light": {"fg": "#1F2328", "muted": "#59636E"},
}
SHADES = [1, .72, .52, .38, .27, .18]  # one ink at falling opacity instead of language colors
W, H, PAD = 495, 195, 25
FONT = "-apple-system, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"


def get(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json",
    })
    return json.load(urllib.request.urlopen(req))


def totals(owner):
    repos = get(f"https://api.github.com/users/{owner}/repos?per_page=100&type=owner")
    sums = {}
    for repo in repos:
        if repo["fork"]:
            continue
        for lang, size in get(repo["languages_url"]).items():
            sums[lang] = sums.get(lang, 0) + size
    return sums


def card(theme, top, total):
    c = THEMES[theme]
    inner = W - 2 * PAD
    x, bar = PAD, []
    shown = sum(size for _, size in top)
    for i, (_, size) in enumerate(top):
        w = inner * size / shown
        bar.append(f'<rect x="{x:.1f}" y="62" width="{max(w - 3, 1):.1f}" height="8" rx="2" fill="{c["fg"]}" fill-opacity="{SHADES[i]}"/>')
        x += w
    legend = []
    col_w = inner / 2
    for i, (lang, size) in enumerate(top):
        lx, ly = PAD + (i % 2) * col_w, 108 + (i // 2) * 28
        legend.append(
            f'<rect x="{lx}" y="{ly - 9}" width="10" height="10" rx="2" fill="{c["fg"]}" fill-opacity="{SHADES[i]}"/>'
            f'<text x="{lx + 18}" y="{ly}" fill="{c["fg"]}">{escape(lang)}</text>'
            f'<text x="{lx + col_w - 24}" y="{ly}" fill="{c["muted"]}" text-anchor="end">{100 * size / total:.1f}%</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title">
  <title id="title">Languages: {", ".join(f"{lang} {100 * size / total:.1f}%" for lang, size in top)}</title>
  <g font-family="{FONT}" font-size="13">
    <text x="{PAD}" y="40" fill="{c["fg"]}" font-size="15" font-weight="600">Languages</text>
    {"".join(bar)}
    {"".join(legend)}
  </g>
</svg>
"""


if __name__ == "__main__":
    sums = totals(os.environ["GITHUB_REPOSITORY_OWNER"])
    total = sum(sums.values())
    top = sorted(sums.items(), key=lambda kv: kv[1], reverse=True)[:len(SHADES)]
    for theme in THEMES:
        Path(OUT, f"langs-{theme}.svg").write_text(card(theme, top, total))
