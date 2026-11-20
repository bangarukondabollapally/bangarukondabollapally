#!/usr/bin/env python3
"""Render the profile README cards as animated SVGs into cards/.

Design: "Three Worlds" (paper, ink, blue / red / yellow; Instrument Serif, Geist,
Geist Mono), as in avivashishta.com's GitHub README write-up.
Every card is a standalone SVG shown through <img>: inline CSS keyframes, SMIL
and fonts embedded as data URIs. No JavaScript, no external requests.
Fonts in fonts/ are subset WOFFs (SIL OFL).

Run:     python scripts/fetch_contributions.py && python scripts/render_readme_cards.py
Preview: STATIC=1 python scripts/render_readme_cards.py   (every animation at its end state)
"""
import base64
import datetime
import json
import os
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")
STATIC = bool(os.environ.get("STATIC"))

# ---- profile content (edit here) -------------------------------------------
NAME_FIRST, NAME_LAST = "Bangaru", "Konda"
EYEBROW = "FRONTEND DEVELOPER  /  BUILDING WITH AI"
TAGLINE = ["I rebuild interfaces I admire, then make", "them mine. AI is my build partner."]
SITE = "bangarukonda.vercel.app"
SITE_URL = "https://bangarukonda.vercel.app"
GH = "https://github.com/bangarukondabollapally"
STEPS = ["See it", "Rebuild it", "Understand it", "Modify it", "Make it mine"]

TILES = [  # label, big text, small text, colour, link  (counts are hand-set: 18 public repos, HireTrack's two repos count as one project)
    ("BUILDS", "16 projects", "Full-stack, AI and frontend work, from HireTrack to a RAG assistant.", "blue", GH + "?tab=repositories"),
    ("APPLIED AI", "6 AI projects", "LangChain and Groq apps, RAG and an ML diagnosis model.", "red", GH + "/rag-document-assistant"),
    ("ON GITHUB", "18 repos", "All public: projects, JavaScript practice and frontend challenges.", "yellow", GH + "?tab=repositories"),
]


REPOS = [  # name, description, stack line
    ("hiretrack-frontend", "Placement drives from opening to offer, with an AI assistant for resumes.", "React 19 · Spring Boot · MySQL"),
    ("rag-document-assistant", "Upload documents, ask questions, get answers grounded in the source passages.", "Python · LangChain · ChromaDB · Streamlit"),
    ("kanban-board", "Drag-and-drop task board in vanilla JavaScript, saved to localStorage.", "JavaScript · HTML · CSS"),
]

# ---- brand tokens -----------------------------------------------------------
PAPER, PAPER_DEEP, INK, INK_SOFT, MUTED, RULE = "#f3f3f1", "#e2e2de", "#111111", "#3a3a3c", "#6e6e73", "#dcdcd7"
BLUE, RED, YELLOW = "#2f55ff", "#ef3b2d", "#ffc81a"
ACCENT = "#ff6a1a"
COLORS = {"blue": BLUE, "red": RED, "yellow": YELLOW}
# ---- type scale (px). One size per role, so hierarchy is consistent across cards ----
DISPLAY = 124   # hero name
H1 = 56         # activity headline
H2 = 44         # section title
H3 = 40         # hero steps, stat numbers, tile headline
H4 = 32         # footer line
LEAD = 18       # hero tagline
CARD_TITLE = 17 # repo names
BODY = 14       # descriptions, stat labels, site link, buttons
LABEL = 12      # every mono eyebrow, tick, meta line
W = 880
GAP = 12
COL = W / 3

SERIF = "'Instrument Serif', Georgia, serif"
SANS = "Geist, system-ui, -apple-system, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace"
FONT_FILES = {
    "serif": ("Instrument Serif", "normal", 400, "serif-400.woff"),
    "serif-i": ("Instrument Serif", "italic", 400, "serif-italic.woff"),
    "sans": ("Geist", "normal", 400, "geist-400.woff"),
    "sans-b": ("Geist", "normal", 600, "geist-600.woff"),
    "mono": ("Geist Mono", "normal", 400, "geistmono-400.woff"),
}

BASE_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(4px)}}
@keyframes nudgeup{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
@keyframes tilein{0%{opacity:0;transform:translateY(90px) scale(.6) rotate(-9deg)}55%{opacity:1;transform:translateY(-10px) scale(1.05) rotate(2deg)}75%{transform:translateY(3px) scale(.98) rotate(-.8deg)}100%{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-26px)}to{opacity:1;transform:none}}
@keyframes sheen{0%{transform:translateX(-260px) skewX(-20deg)}22%,100%{transform:translateX(420px) skewX(-20deg)}}
@keyframes ring{0%{opacity:.7;transform:scale(.2)}100%{opacity:0;transform:scale(2.4)}}
.r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
.live{animation:pulse 1.6s ease-in-out infinite}
.n{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudgeup 1.8s ease-in-out infinite}
.ti{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:tilein 1.1s cubic-bezier(.2,.8,.2,1) both}
.sl{opacity:0;transform-box:fill-box;animation:slidein .6s cubic-bezier(.2,.7,.2,1) both}
.sh{animation:sheen 5s ease-in-out infinite}
.rg{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 1s ease-out both}
@media (prefers-reduced-motion: reduce){.r,.f,.g,.p,.live,.n,.nu,.ti,.sl,.rg{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}}
"""
STATIC_CSS = ".r,.f,.g,.p,.live,.n,.nu,.ti,.sl{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}"


def font_face(keys):
    out = []
    for k in keys:
        fam, style, weight, fn = FONT_FILES[k]
        b64 = base64.b64encode(open(os.path.join(FONTS, fn), "rb").read()).decode()
        out.append(f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
                   f"src:url(data:font/woff;base64,{b64}) format('woff')}}")
    return "".join(out)


def svg(w, h, body, fonts, label, extra_css="", left=0, right=0, bottom=GAP):
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    w, h = w + left + right, h + bottom
    css = font_face(fonts) + BASE_CSS + extra_css + (STATIC_CSS if STATIC else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{h}" viewBox="0 0 {w:.3f} {h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title><style>{css}</style>{body}</svg>')


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote cards/{name} ({len(content) // 1024} KB)")


def d(s):
    return f'style="animation-delay:{s:.2f}s"'


def wrap(text, n):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > n:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def lines_svg(x, y, lines, lh, attrs, delay=0, step=0.08, cls="r"):
    return "".join(f'<text class="{cls}" {d(delay + i * step)} x="{x}" y="{y + i * lh}" {attrs}>{escape(l)}</text>'
                   for i, l in enumerate(lines))


def load():
    if not os.path.exists(DATA):
        raise SystemExit("data/contributions.json missing: run scripts/fetch_contributions.py first")
    return json.load(open(DATA))


# ------------------------------------------------------------------ hero
def hero():
    h = 432
    body = [f'<rect width="{W}" height="{h}" rx="18" fill="{PAPER}"/>']
    body.append(f'<rect class="f live" x="48" y="42" width="9" height="9" rx="2" fill="{ACCENT}"/>')
    body.append(f'<text class="f" x="68" y="51" font-family="{MONO}" font-size="{LABEL}" letter-spacing="1.3" fill="{MUTED}" xml:space="preserve">{escape(EYEBROW)}</text>')
    body.append(f'<text class="r" {d(.15)} x="44" y="186" font-family="{SERIF}" font-size="{DISPLAY}" fill="{INK}">{NAME_FIRST}</text>')
    body.append(f'<text class="r" {d(.35)} x="44" y="290" font-family="{SERIF}" font-style="italic" font-size="{DISPLAY}" fill="{INK}">{NAME_LAST}</text>')
    body.append(lines_svg(48, 340, TAGLINE, 27, f'font-family="{SANS}" font-size="{LEAD}" fill="{INK_SOFT}"', .8, .12))
    body.append(f'<text class="f" {d(1.2)} x="48" y="398" font-family="{MONO}" font-size="{BODY}" fill="{INK}">{SITE}</text>')
    ax = 48 + len(SITE) * 8.4 + 14
    body.append(f'<path class="f nu" {d(1.2)} d="M{ax:.0f} 396 L{ax + 9:.0f} 387 M{ax + 2:.0f} 387 L{ax + 9:.0f} 387 L{ax + 9:.0f} 394" fill="none" stroke="{ACCENT}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
    # right column: the five steps, a real sequence
    x0, y0, rh = 540, 78, 64
    for i, s in enumerate(STEPS):
        y = y0 + i * rh
        last = i == len(STEPS) - 1
        color = ACCENT if last else INK
        style = "italic" if last else "normal"
        body.append(f'<text class="sl" {d(.9 + i * .18)} x="{x0}" y="{y + 40}" font-family="{MONO}" font-size="{LABEL}" fill="{MUTED}">0{i + 1}</text>')
        body.append(f'<text class="sl" {d(.9 + i * .18)} x="{x0 + 46}" y="{y + 44}" font-family="{SERIF}" font-style="{style}" font-size="{H3}" fill="{color}">{s}</text>')
        if not last:
            body.append(f'<rect class="f" {d(1.0 + i * .18)} x="{x0}" y="{y + rh - 4}" width="300" height="1" fill="{RULE}"/>')
    write("hero.svg", svg(W, h, "".join(body), ["serif", "serif-i", "sans", "mono"],
                          f"{NAME_FIRST} {NAME_LAST}. Frontend developer building with AI. See it, rebuild it, understand it, modify it, make it mine."))


# ------------------------------------------------------------------ blue heatmap
def heatmap(data):
    days = data["days"]
    shades = ["#e2e2de", "#ffd9c2", "#ffb88a", "#ff9456", ACCENT]
    h = 186
    body = [f'<rect width="{W}" height="{h}" rx="18" fill="{PAPER}"/>']
    body.append(f'<text class="f" x="28" y="38" font-family="{MONO}" font-size="{LABEL}" letter-spacing="1.3" fill="{MUTED}">CONTRIBUTIONS ON GITHUB, LAST 12 MONTHS</text>')
    first = datetime.date.fromisoformat(days[0]["date"])
    start_dow = (first.weekday() + 1) % 7  # Sunday = 0
    cols = (len(days) + start_dow + 6) // 7
    pitch = (W - 56) / cols
    cell = pitch - 3.2
    for i, day in enumerate(days):
        j = i + start_dow
        wk, dow = divmod(j, 7)
        x = 28 + wk * pitch
        y = 56 + dow * pitch
        body.append(f'<rect class="p" style="animation-delay:{.2 + wk * .022:.3f}s" x="{x:.2f}" y="{y:.2f}" width="{cell:.2f}" height="{cell:.2f}" rx="2.5" fill="{shades[day["level"]]}"/>')
    write("heatmap.svg", svg(W, h, "".join(body), ["mono"], "Contribution graph in blue, last 12 months, refreshed daily"))


# ------------------------------------------------------------------ activity
def activity(data):
    h = 340
    today = datetime.date.today()
    keys = []
    y, m = today.year, today.month
    for _ in range(12):
        keys.append(f"{y}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    keys.reverse()
    vals = [data["months"].get(k, 0) for k in keys]
    total = sum(vals)
    best = max(range(12), key=lambda i: vals[i]) if any(vals) else -1
    mx = max(vals) or 1
    mnames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    body = [f'<rect width="{W}" height="{h}" rx="18" fill="{PAPER}"/>']
    body.append(f'<text class="f" x="40" y="53" font-family="{MONO}" font-size="{LABEL}" letter-spacing="1.3" fill="{MUTED}">THE LAST 12 MONTHS ON GITHUB</text>')
    body.append(f'<text class="r" {d(.1)} x="38" y="110" font-family="{SERIF}" font-size="{H1}" fill="{INK}">{total:,} <tspan font-style="italic">contributions</tspan></text>')
    base, top = 292, 160
    bw, bp = 38, 47.4
    for i, (k, v) in enumerate(zip(keys, vals)):
        bh = max(6, (base - top) * v / mx)
        x = 40 + i * bp
        fill = ACCENT if i == best else ("#c8c8c2" if i == 11 else INK)
        body.append(f'<rect class="g" style="animation-delay:{.3 + i * .05:.2f}s" x="{x:.1f}" y="{base - bh:.1f}" width="{bw}" height="{bh:.1f}" rx="4" fill="{fill}"/>')
        body.append(f'<text class="f" {d(.5 + i * .05)} x="{x + bw / 2:.1f}" y="{base + 20}" text-anchor="middle" font-family="{MONO}" font-size="{LABEL}" fill="{MUTED}">{mnames[int(k[5:]) - 1]}</text>')
        if i == best:
            body.append(f'<text class="f" {d(1.0)} x="{x + bw / 2:.1f}" y="{base - bh - 8:.1f}" text-anchor="middle" font-family="{MONO}" font-size="{LABEL}" fill="{MONO}">{v:,}</text>')
    stats = [
        (f'{data["current_streak"]}', "day" if data["current_streak"] == 1 else "days", "current streak", False),
        (f'{data["active_days"]}', f'/ {data["span_days"]}', "days with a commit", True),
        (f'{data["best_day"]}', "", "on the busiest day", False),
    ]
    for i, (big, tail, label, soft) in enumerate(stats):
        y = 108 + i * 92
        tail_svg = f' <tspan fill="{"#a0a09b" if soft else INK}" font-style="{"normal" if soft else "italic"}">{tail}</tspan>' if tail else ""
        body.append(f'<text class="r" {d(.5 + i * .15)} x="650" y="{y}" font-family="{SERIF}" font-size="{H3}" fill="{INK}">{big}{tail_svg}</text>')
        body.append(f'<text class="r" {d(.6 + i * .15)} x="650" y="{y + 22}" font-family="{SANS}" font-size="{BODY}" fill="{MUTED}">{label}</text>')
        if i < 2:
            body.append(f'<rect class="f" {d(.7 + i * .15)} x="650" y="{y + 38}" width="190" height="1" fill="{RULE}"/>')
    write("activity.svg", svg(W, h, "".join(body), ["serif", "serif-i", "sans", "mono"],
                              f"{total} contributions in the last 12 months, by month, with streak and busiest day"))


# ------------------------------------------------------------------ tiles
def tiles():
    th = 210
    ws = [COL - 6, COL - 12, COL - 6]
    lefts, rights = [0, 6, 6], [6, 6, 0]
    names = ["build", "ai", "github"]
    for i, (label, big, small, col, _link) in enumerate(TILES):
        c = COLORS[col]
        fg = INK if col == "yellow" else "#ffffff"
        w = ws[i]
        base_delay = .6 + i * .3
        body = [f'<clipPath id="c{i}"><rect width="{w:.2f}" height="{th}" rx="18"/></clipPath>']
        g = [f'<rect width="{w:.2f}" height="{th}" rx="18" fill="{c}"/>']
        g.append(f'<text x="24" y="36" font-family="{MONO}" font-size="{LABEL}" letter-spacing="1.2" fill="{fg}">{label}</text>')
        g.append(f'<text class="ai n" x="{w - 36:.1f}" y="37" font-family="{MONO}" font-size="{BODY}" fill="{fg}">→</text>')
        g.append(f'<circle class="rg" {d(base_delay + 1.0)} cx="{w - 28:.1f}" cy="33" r="15" fill="none" stroke="{fg}" stroke-width="1.3"/>')
        g.append(f'<text class="r" {d(base_delay + .5)} x="22" y="105" font-family="{SERIF}" font-style="italic" font-size="{H3}" fill="{fg}">{escape(big)}</text>')
        g.append(lines_svg(24, 142, wrap(small, 34), 20, f'font-family="{SANS}" font-size="{BODY}" fill="{fg}"', base_delay + .7, .1))
        g.append(f'<g clip-path="url(#c{i})"><rect class="sh" x="0" y="-20" width="60" height="{th + 40}" fill="#fff" opacity=".16"/></g>')
        body.append(f'<g class="ti" {d(base_delay)}>{"".join(g)}</g>')
        write(f"tile-{names[i]}.svg", svg(w, th, "".join(body), ["serif-i", "sans", "mono"], f"{label}: {big}. {small}",
                                          left=lefts[i], right=rights[i]).replace('width="%.3f"' % (w + lefts[i] + rights[i]), 'width="%.3f"' % COL, 1))


# ------------------------------------------------------------------ section title (light + dark)
def title(text, name):
    for mode, color in (("light", INK), ("dark", "#f3f3f1")):
        body = (f'<text class="r" x="6" y="46" font-family="{SERIF}" font-size="{H2}" fill="{color}">{escape(text)}</text>'
                f'<rect class="f live" x="{W - 24}" y="30" width="9" height="9" rx="2" fill="{ACCENT}"/>')
        write(f"title-{name}-{mode}.svg", svg(W, 76, body, ["serif"], text, bottom=0))


# ------------------------------------------------------------------ repo cards
def repos():
    ch = 184
    ws = [COL - 6, COL - 12, COL - 6]
    lefts, rights = [0, 6, 6], [6, 6, 0]
    for i, (name, desc, meta) in enumerate(REPOS):
        w = ws[i]
        dl = .2 + i * .2
        body = [f'<rect width="{w:.2f}" height="{ch}" rx="18" fill="{PAPER}"/>',
                f'<rect class="f" {d(dl)} x="24" y="26" width="9" height="9" rx="2" fill="{ACCENT}"/>',
                f'<text class="r" {d(dl)} x="40" y="36" font-family="{SANS}" font-weight="600" font-size="{CARD_TITLE}" fill="{INK}">{escape(name)}</text>',
                lines_svg(24, 68, wrap(desc, 34), 20, f'font-family="{SANS}" font-size="{BODY}" fill="{INK_SOFT}"', dl + .1, .08),
                lines_svg(24, ch - 36, wrap(meta, 32), 16, f'font-family="{MONO}" font-size="{LABEL}" fill="{MUTED}"', dl + .5, .08)]
        write(f"repo-{name}.svg", svg(w, ch, "".join(body), ["sans", "sans-b", "mono"], f"{name}. {desc}",
                                       left=lefts[i], right=rights[i]).replace('width="%.3f"' % (w + lefts[i] + rights[i]), 'width="%.3f"' % COL, 1))


# ------------------------------------------------------------------ footer
def footer():
    h = 128
    body = [f'<rect width="{W}" height="{h}" rx="18" fill="{PAPER}"/>',
            f'<text class="f" x="24" y="36" font-family="{MONO}" font-size="{LABEL}" letter-spacing="1.2" fill="{MUTED}">END OF TRANSMISSION</text>',
            f'<text class="r" x="24" y="78" font-family="{SERIF}" font-style="italic" font-size="{H4}" fill="{INK}">See you around.</text>',
            f'<text class="r" {d(.2)} x="24" y="106" font-family="{SANS}" font-size="{BODY}" fill="{INK_SOFT}">Building, learning and making things better, one project at a time.</text>']
    write("footer.svg", svg(W, h, "".join(body), ["serif-i", "sans", "mono"], "See you around."))


# ------------------------------------------------------------------ link buttons (one SVG each, so each is its own link)
BUTTONS = [("portfolio", "Portfolio", True), ("linkedin", "LinkedIn", False), ("github", "GitHub", False)]


def buttons():
    h, pad = 44, 6
    for i, (name, label, primary) in enumerate(BUTTONS):
        w = round(len(label) * 8.4 + 66)
        bg = ACCENT if primary else INK
        edge = "none" if primary else "#55555a"
        body = (f'<g class="r" {d(.1 + i * .12)}>'
                f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="21.5" fill="{bg}" stroke="{edge}"/>'
                f'<text x="24" y="27.5" font-family="{MONO}" font-size="{BODY}" fill="#ffffff">{label}</text>'
                f'<path class="nu" d="M{w - 31} 28 L{w - 22} 19 M{w - 29} 19 L{w - 22} 19 L{w - 22} 26" fill="none" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
                f'</g>')
        write(f"btn-{name}.svg", svg(w, h, body, ["mono"], label, left=pad, right=pad, bottom=0))


if __name__ == "__main__":
    data = load()
    hero()
    heatmap(data)
    activity(data)
    tiles()
    title("What I'm coding", "coding")
    repos()
    footer()
    buttons()