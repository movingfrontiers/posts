
"""
chart-4-fdi-attraction-efficiency-relative-to-peers.py
Sri Lanka's FDI-attraction efficiency against structural peers and regional comparators.

Self-contained: the data are embedded below, so this script runs on its own.
The companion CSV holds the same numbers plus each country's structural distance
from Sri Lanka.

Technical efficiency is the share of frontier FDI a country actually attains,
where the frontier is the maximum inflow observed for economies with the same
fundamentals. It comes from a stochastic frontier model (half-normal
inefficiency, log FDI/GDP) estimated on 124 economies over 2010-2024; war years
are excluded so the comparison reflects normal-time investment climate.

LEFT PANEL  - structural peers: the economies closest to Sri Lanka on five
              standardised characteristics (economy size, income per capita,
              government effectiveness, access to surrounding markets, trade
              openness), ranked by straight-line distance in that space.
RIGHT PANEL - regional comparators: the Asian economies policy discussion most
              often invokes. Several are structurally quite unlike Sri Lanka.

Run:  python chart-4-fdi-attraction-efficiency-relative-to-peers.py
Out:  chart-4-fdi-attraction-efficiency-relative-to-peers.png
"""

# -- Moving Frontiers chart template (embedded so each script is self-contained) --
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as _np
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import os
from PIL import Image, ImageDraw, ImageFont

DPI      = 200
# -- vivid palette, the house default. Roles per the chart standard, section 3. --
C_RED    = "#C62828"   # subject economy / actual series
C_BLUE   = "#283593"   # benchmark / reference series
C_LBLU   = "#00897B"   # peers / gap fill
C_GOLD   = "#F9A825"   # third series
C_LMTXT  = "#B8860B"   # lower-middle label, legible off the fill
C_MUTE   = "#555555"
INK      = "#141414"
PAPER    = "#FFFFFF"
C_CONNECT = "#D5D5D5"  # connectors between paired marks
C_GRID    = "#EDEDED"

BOX_ASPECT = 0.798     # plot area 1.253:1, width over height

# ---- caption and watermark constants (Moving Frontiers standard) ----
CAP_FS       = 8.5                          # Source/Note font size
CAP_COLOR    = "#555555"
WM_FS        = CAP_FS * 1.2                 # watermark is 1.2x the caption
WM_TXT       = "movingfrontiers.substack.com"
WM_COLOR     = "#999999"
CAP_X        = 0.012                        # caption left edge, figure fraction
CAP_RIGHT_PX = 27                           # caption block right margin
WM_RIGHT_PX  = 12                           # watermark right margin
GAP_ABOVE_PX = 60                           # white space above the Source line, ink to ink
SUB_GAP_PX   = 70                           # white space below the subtitle, ink to ink
WM_GAP_TOP   = 20                           # white space between the last caption line
                                            # and the watermark, ink to ink
WM_GAP_BOT   = 10                           # white space below the watermark, ink to canvas
LINESPACING  = 1.32

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 13,
    "axes.labelsize": 13, "xtick.labelsize": 12, "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "axes.edgecolor": "#888888", "axes.linewidth": 1.0,
    "figure.facecolor": "white", "axes.facecolor": "white",
})


def _font_path(bold=False):
    """DejaVu from matplotlib's bundled data, with a system-path fallback."""
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    cands = [os.path.join(os.path.dirname(matplotlib.__file__),
                          "mpl-data", "fonts", "ttf", name),
             "/usr/share/fonts/truetype/dejavu/" + name]
    for p in cands:
        if os.path.exists(p):
            return p
    raise AssertionError("DejaVu font not found: " + name)


def _renderer(fig):
    fig.canvas.draw()
    return fig.canvas.get_renderer()


def _measurer(fig, fontsize):
    """Pixel width of a string at a given size, measured by rendering a probe."""
    r = _renderer(fig)
    cache = {}

    def width(s):
        if s not in cache:
            t = fig.text(0.0, 0.0, s, fontsize=fontsize)
            cache[s] = t.get_window_extent(r).width
            t.remove()
        return cache[s]
    return width


def _metrics(fig, fontsize):
    """Ascent and descent in px, measured against a planted baseline."""
    r = _renderer(fig)
    Hpx = fig.get_size_inches()[1] * fig.dpi
    t = fig.text(0.5, 0.5, "Agy", fontsize=fontsize, va="baseline")
    bb = t.get_window_extent(r)
    t.remove()
    base = 0.5 * Hpx
    return bb.y1 - base, base - bb.y0


def _ink_metrics(s, fontsize, dpi):
    """Ink height above and below the baseline, in px. Tight, unlike a text bbox."""
    tp = TextPath((0, 0), s, size=fontsize,
                  prop=FontProperties(family="DejaVu Sans"))
    bb = tp.get_extents()
    k = dpi / 72.0
    return bb.y1 * k, -bb.y0 * k


def _wrap_lines(paragraphs, width, limit_for):
    """Greedy wrap. Each paragraph starts on a new line. Limit varies by line index.

    Returns the lines and, for each line, the index of the paragraph it came from,
    so a line that ends because its paragraph ended can be told apart from one that
    ends because the next word would not fit.
    """
    lines, owner = [], []
    for p, words in enumerate(paragraphs):
        cur = ""
        for w in words:
            trial = (cur + " " + w).strip()
            if not cur or width(trial) <= limit_for(len(lines)):
                cur = trial
            else:
                lines.append(cur); owner.append(p)
                cur = w
        if cur:
            lines.append(cur); owner.append(p)
    return lines, owner


def caption_layout(fig, source, note, closers=()):
    """Wrap the caption in pixels and return the geometry of the whole block.

    Every line runs the full width of the caption block. The watermark is not
    inline: it sits on its own line below the caption, right-aligned, with
    WM_GAP_TOP of white space between the lowest caption ink and the top of the
    watermark's ink, and WM_GAP_BOT below it to the canvas edge. Nothing wraps
    around it, so `closers` is accepted for compatibility but is not needed.
    """
    Wpx  = fig.get_size_inches()[0] * fig.dpi
    wcap = _measurer(fig, CAP_FS)

    x0   = CAP_X * Wpx
    full = (Wpx - CAP_RIGHT_PX) - x0                    # width of the caption block

    paras = [("Source: " + source).split(), ("Note: " + note).split()]
    lines, owner = _wrap_lines(paras, wcap, lambda i: full)

    # every line but the last must be maximally full
    for i in range(len(lines) - 1):
        if owner[i + 1] == owner[i]:
            nxt = lines[i + 1].split()[0]
            assert wcap(lines[i] + " " + nxt) > full, \
                f"caption line {i} is not filled to the full width"

    cap_desc = _metrics(fig, CAP_FS)[1]
    lh = CAP_FS * LINESPACING * fig.dpi / 72.0          # uniform leading throughout

    ink_asc   = _ink_metrics(lines[0], CAP_FS, fig.dpi)[0]     # ink top of the Source line
    ink_desc  = _ink_metrics(lines[-1], CAP_FS, fig.dpi)[1]    # ink bottom of the last line
    wm_asc, wm_desc = _ink_metrics(WM_TXT, WM_FS, fig.dpi)

    wm_base = WM_GAP_BOT + wm_desc                      # watermark baseline above the canvas
    height  = (GAP_ABOVE_PX + ink_asc + (len(lines) - 1) * lh + ink_desc
               + WM_GAP_TOP + wm_asc + wm_base)

    return dict(lines=lines, owner=owner, closer="", lh=lh, ink_asc=ink_asc,
                ink_desc=ink_desc, gap=GAP_ABOVE_PX, wm_base=wm_base,
                wm_asc=wm_asc, wm_desc=wm_desc, cap_desc=cap_desc,
                full=full, height=height, x0=x0, Wpx=Wpx)


def lowest_px(fig, artists):
    """Lowest ink (px from figure bottom) among the given text artists.

    A text bbox carries the font's full descent whether or not the string has
    descenders, so it is not where the type visibly ends. Recover the baseline
    from the bbox and the font descent, then drop by the string's own ink descent.
    """
    r = _renderer(fig)
    out = []
    for a in artists:
        bb = a.get_window_extent(r)
        fs = a.get_fontsize()
        baseline = bb.y0 + _metrics(fig, fs)[1]
        out.append(baseline - _ink_metrics(a.get_text(), fs, fig.dpi)[1])
    return min(out)


def fit_caption_space(fig, lay, anchor_artists, apply):
    """Reserve exactly lay['height'] below the anchor element.

    `apply(bottom_fraction)` is however this figure lays itself out: a tight_layout
    rect, a subplots_adjust, or both. Either way the anchor moves one for one with
    the reserve, but the layout engine adds a pad of its own, so apply the reserve,
    measure the residual, and re-apply corrected. That lands the block bottom on
    the canvas edge.
    """
    Hpx = fig.get_size_inches()[1] * fig.dpi
    b = lay["height"] / Hpx
    apply(b)
    for _ in range(12):
        delta = lowest_px(fig, anchor_artists) - lay["height"]
        if abs(delta) < 0.25:
            return lowest_px(fig, anchor_artists)
        b -= delta / Hpx               # one step when the anchor tracks the reserve one
        apply(b)                       # for one, a few more when a fixed box aspect damps it
    raise AssertionError(f"caption reserve did not settle, off by {delta:.2f}px")


def place_caption(fig, lay, anchor_px):
    """Draw the caption lines, then the watermark on its own line below them."""
    Wpx = lay["Wpx"]
    Hpx = fig.get_size_inches()[1] * fig.dpi
    lines, lh = lay["lines"], lay["lh"]

    first_base = anchor_px - lay["gap"] - lay["ink_asc"]
    arts = [fig.text(CAP_X, (first_base - i * lh) / Hpx, ln, fontsize=CAP_FS,
                     color=CAP_COLOR, ha="left", va="baseline")
            for i, ln in enumerate(lines)]
    wm = fig.text((Wpx - WM_RIGHT_PX) / Wpx, lay["wm_base"] / Hpx, WM_TXT,
                  fontsize=WM_FS, color=WM_COLOR, ha="right", va="baseline")

    # -- verification --
    r = _renderer(fig)
    bbs = [a.get_window_extent(r) for a in arts]
    wbb = wm.get_window_extent(r)
    ink_top = first_base + lay["ink_asc"]
    assert abs((anchor_px - ink_top) - lay["gap"]) < 0.6, \
        f"caption top gap is {anchor_px - ink_top:.2f}px, expected {lay['gap']}"
    assert abs(bbs[0].x0 - CAP_X * Wpx) < 0.6, "caption left edge off x=0.012"
    assert abs((Wpx - wbb.x1) - WM_RIGHT_PX) < 0.6, \
        f"watermark right margin is {Wpx - wbb.x1:.2f}px, expected {WM_RIGHT_PX}"
    for i, bb in enumerate(bbs):
        assert bb.x1 <= Wpx - CAP_RIGHT_PX + 0.6, f"caption line {i} overruns the right margin"
    last_ink_bot = (first_base - (len(lines) - 1) * lh) - lay["ink_desc"]
    wm_ink_top = lay["wm_base"] + lay["wm_asc"]
    # these two carry the snap's sub-pixel correction, so the binding check is the
    # pixel-row count in place_caption_snapped; here just catch gross errors
    assert abs((last_ink_bot - wm_ink_top) - WM_GAP_TOP) < 2.6, \
        f"gap above the watermark is {last_ink_bot - wm_ink_top:.2f}px, expected {WM_GAP_TOP}"
    assert abs((lay["wm_base"] - lay["wm_desc"]) - WM_GAP_BOT) < 2.6, \
        "white space below the watermark is wrong"
    return arts, wm


def _ink_rows_of(fig, art):
    """First and last rows the artist actually marks, searched inside its own bbox."""
    r = _renderer(fig)
    bb = art.get_window_extent(r)
    buf = _np.asarray(fig.canvas.buffer_rgba())
    H, W = buf.shape[:2]
    ink = buf[:, :, :3].mean(axis=2) < 250
    x0, x1 = max(int(bb.x0), 0), min(int(bb.x1) + 1, W)
    top = max(H - 1 - (int(bb.y1) + 1), 0)
    bot = min(H - 1 - int(bb.y0) + 1, H - 1)
    rows = _np.where(ink[top:bot + 1, x0:x1].any(1))[0]
    assert len(rows), "artist left no ink"
    return top + rows[0], top + rows[-1], H


def _blank_rows_above(fig, art):
    """Blank pixel rows between the given text artist's ink and the nearest ink above it."""
    r = _renderer(fig)
    bb = art.get_window_extent(r)
    buf = _np.asarray(fig.canvas.buffer_rgba())
    H, W = buf.shape[:2]
    ink = buf[:, :, :3].mean(axis=2) < 250
    x0, x1 = max(int(bb.x0), 0), min(int(bb.x1) + 1, W)
    top = max(H - 1 - (int(bb.y1) + 1), 0)
    bot = min(H - 1 - int(bb.y0), H - 1)
    rows = _np.where(ink[top:bot + 1, x0:x1].any(1))[0]
    assert len(rows), "the caption line left no ink"
    first = top + rows[0]
    above = _np.where(ink[:first, x0:x1].any(1))[0]
    assert len(above), "nothing above the caption to measure the gap from"
    return first - above[-1] - 1


def place_caption_snapped(fig, lay, anchor_artists, apply):
    """Place the caption, then snap the gap above it to exactly GAP_ABOVE_PX blank rows.

    The ink-to-ink target is exact in figure coordinates but lands a pixel either
    side depending on sub-pixel phase, so measure the rendered rows and correct by
    adjusting the reserved height, which moves the axes rather than the caption and
    so leaves the block bottom on the canvas edge.
    """
    drawn = None
    for _ in range(4):
        if drawn:
            for a in drawn:
                a.remove()          # including the watermark, or retries stack copies
        anchor = fit_caption_space(fig, lay, anchor_artists, apply)
        arts, wm = place_caption(fig, lay, anchor)
        drawn = arts + [wm]
        n_top = _blank_rows_above(fig, arts[0])
        cap_bot = _ink_rows_of(fig, arts[-1])[1]
        wm_top, wm_bot, H = _ink_rows_of(fig, wm)
        n_mid = wm_top - cap_bot - 1
        n_bot = H - 1 - wm_bot
        if (n_top, n_mid, n_bot) == (GAP_ABOVE_PX, WM_GAP_TOP, WM_GAP_BOT):
            return drawn
        # three knobs, three gaps: the watermark's own baseline sets the space below it,
        # the reserve moves the axes and so opens the space above the watermark, and the
        # gap moves the caption under the anchor.
        lay["wm_base"] += WM_GAP_BOT - n_bot
        lay["height"] += (GAP_ABOVE_PX - n_top) + (WM_GAP_TOP - n_mid) + (WM_GAP_BOT - n_bot)
        lay["gap"] += GAP_ABOVE_PX - n_top
    raise AssertionError(
        f"caption gaps settled at {(n_top, n_mid, n_bot)}, expected "
        f"{(GAP_ABOVE_PX, WM_GAP_TOP, WM_GAP_BOT)}")


def _wrap_px(words, font, maxw):
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def _ink_rows(img):
    """First and last rows of the image that carry ink."""
    px = img.convert("L").load()
    W, H = img.size
    rows = [y for y in range(H) if any(px[x, y] < 250 for x in range(0, W, 2))]
    assert rows, "image is blank"
    return rows[0], rows[-1]


def _draw_band(canvas, W, title, subtitle, y0=0):
    """Draw the title and subtitle onto canvas starting at y0; return the layout."""
    ts = int(W * 0.030); ss = int(ts * 0.58)
    ft = ImageFont.truetype(_font_path(bold=True), ts)
    fs = ImageFont.truetype(_font_path(), ss)
    x = int(W * 0.025); maxw = W - 2 * x
    tl = _wrap_px(title.split(), ft, maxw)
    sl = _wrap_px(subtitle.split(), fs, maxw)
    pad = int(ts * 0.75); gap = int(ts * 0.35)
    tlh = int(ts * 1.22); slh = int(ss * 1.30)
    d = ImageDraw.Draw(canvas)
    y = y0 + pad
    for ln in tl:
        d.text((x, y), ln, fill=(45, 45, 45), font=ft); y += tlh
    y += gap - int(ts * 0.10)
    for ln in sl:
        d.text((x, y), ln, fill=(100, 100, 100), font=fs); y += slh
    return pad + len(tl) * tlh + gap + len(sl) * slh + pad     # nominal band height


def add_title_band(png_path, title, subtitle, gap_px=SUB_GAP_PX):
    """Bold title + gray subtitle above the plot, with gap_px of white below the subtitle.

    The gap is measured ink to ink: from the last row the subtitle marks to the
    first row the chart marks, so the plot's own top margin is absorbed rather
    than added to it.
    """
    img = Image.open(png_path).convert("RGB"); W, H = img.size
    probe = Image.new("RGB", (W, H), "white")
    bh = _draw_band(probe, W, title, subtitle)
    sub_bottom = _ink_rows(probe.crop((0, 0, W, bh)))[1]        # last row of subtitle ink
    chart_top  = _ink_rows(img)[0]                              # first row of chart ink

    paste_y = sub_bottom + 1 + gap_px - chart_top
    canvas = Image.new("RGB", (W, paste_y + H), "white")
    canvas.paste(img, (0, paste_y))
    _draw_band(canvas, W, title, subtitle)
    canvas.save(png_path)

    check = Image.open(png_path).convert("RGB")
    px = check.convert("L").load()
    blank = 0
    for y in range(sub_bottom + 1, check.size[1]):
        if any(px[x, y] < 250 for x in range(0, W, 2)):
            break
        blank += 1
    assert blank == gap_px, \
        f"white space below the subtitle is {blank}px, expected {gap_px}"


def style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# widen caption wrap to suit the 11-inch two-panel canvas

C_TEAL = "#5B8C85"

# ── left panel: structural peers (name, efficiency) ──
STRUCT = [
    ("Costa Rica",     0.629), ("Dominican Rep.", 0.602), ("Peru",        0.545),
    ("Ghana",          0.538), ("Senegal",        0.461), ("Guatemala",   0.426),
    ("Philippines",    0.389), ("C\u00f4te d\u2019Ivoire", 0.290), ("Paraguay",  0.287),
    ("El Salvador",    0.279), ("Bolivia",        0.250), ("Sri Lanka",   0.237),
    ("Kenya",          0.216), ("Ecuador",        0.168),
]

# ── right panel: regional comparators (name, efficiency) ──
REGION = [
    ("Cambodia",   0.651), ("China",       0.524), ("Indonesia", 0.474),
    ("India",      0.427), ("Vietnam",     0.410), ("Philippines", 0.389),
    ("Malaysia",   0.305), ("Thailand",    0.288), ("Bangladesh", 0.249),
    ("Sri Lanka",  0.237), ("Pakistan",    0.228), ("Korea, Rep.", 0.196),
    ("Nepal",      0.095),
]

HIGHLIGHT = "Sri Lanka"

TITLE    = "Sri Lanka trails both its structural peers and its region"
SUBTITLE = "FDI-attraction efficiency relative to the peacetime frontier, percent, 2010-2024"
SOURCE   = ("World Bank WDI/WGI; CEPII GeoDist; UCDP/PRIO Armed Conflict Dataset v26.1; "
            "author's stochastic frontier estimates.")
NOTE     = ("Technical efficiency is the share of frontier FDI a country actually attains, where the frontier "
            "is the maximum inflow observed for economies with the same fundamentals. Estimated by a stochastic "
            "frontier model (half-normal inefficiency, log FDI/GDP) on 124 economies over 2010-2024; war years "
            "are excluded so that the comparison reflects normal-time investment climate. Structural peers in "
            "the left panel are the economies closest to Sri Lanka on five measured characteristics, namely economy "
            "size, income per capita, government effectiveness, access to surrounding markets and trade "
            "openness, each standardised, with closeness measured as straight-line distance from Sri Lanka in "
            "that five-dimensional space. They are therefore countries a model would expect to attract similar "
            "investment, irrespective of region: Ecuador, the closest of all, matches Sri Lanka on every "
            "dimension. The right panel shows regional comparators for context; several are structurally quite "
            "unlike Sri Lanka (Malaysia, Korea and Vietnam are among the least similar economies in the sample) "
            "but are the ones policy discussion most often invokes. Sri Lanka ranks 103rd of 124 economies "
            "overall.")

OUT = "chart-4-fdi-attraction-efficiency-relative-to-peers.png"

plt.rcParams.update({
    "font.size": 12, "axes.labelsize": 11.5,
    "xtick.labelsize": 11, "ytick.labelsize": 11.5,
})


def panel(ax, rows, heading):
    rows = sorted(rows, key=lambda r: r[1])          # ascending -> best on top
    labels = [r[0] for r in rows]
    vals   = [r[1] * 100 for r in rows]
    cols   = [C_RED if l == HIGHLIGHT else C_BLUE for l in labels]
    ax.barh(labels, vals, color=cols, edgecolor="none", height=0.66)
    for i, v in enumerate(vals):
        ax.text(v + 1.4, i, f"{v:.0f}%", va="center", fontsize=10.5, color="#333333")
    lk = [r[1] for r in rows if r[0] == HIGHLIGHT][0] * 100
    ax.axvline(lk, color=C_RED, lw=1.1, ls="--", alpha=0.45)
    ax.set_xlim(0, 78); ax.set_xticks([0, 20, 40, 60])
    ax.set_xlabel("Technical efficiency (% of frontier attained)", fontsize=11)
    ax.set_title(heading, fontsize=12.5, fontweight="bold", color="#333333", pad=10, loc="left")
    style_ax(ax)


# Aspect: two-panel categorical figure, so the 1.253:1 plot-area ratio is not
# pinned; the canvas is sized to the panels (chart standard, section 4).
fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 8.6), dpi=DPI,
                               gridspec_kw={"wspace": 0.42})
panel(axL, STRUCT, "Structural peers")
panel(axR, REGION, "Regional comparators")

lay = caption_layout(fig, SOURCE, NOTE)


def apply(bottom):
    fig.subplots_adjust(left=0.135, right=0.985, top=0.94, bottom=bottom + 0.075)


place_caption_snapped(fig, lay, [axL.xaxis.label, axR.xaxis.label], apply)
fig.savefig(OUT, dpi=DPI, facecolor="white")
plt.close(fig)
add_title_band(OUT, TITLE, SUBTITLE)
print("wrote", OUT)
