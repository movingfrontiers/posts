# =============================================================================
# Chart: Sri Lanka FDI as share of GDP, 1970-2024
#
# Provenance, frozen vintage. Nothing is read from disk or the network.
#   Data: World Bank WDI, series BX.KLT.DINV.WD.GD.ZS
#         (Foreign direct investment, net inflows, % of GDP), July 2026 release.
#   Country: Sri Lanka
#   Vintage freeze date: August 2026.
# =============================================================================
import numpy as np

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


SRC = ("Source: World Bank World Development Indicators (BX.KLT.DINV.WD.GD.ZS), July 2026 release." + chr(10))
NOTE = ("Note: FDI net inflows as a share of GDP, Sri Lanka, 1970\u20132024. "
        "The dashed line is the 1970\u20132024 average (0.91% of GDP). "
        "Peak inflows of 2.8% of GDP were recorded in 1997. "
        "Negative values in 1970\u201378 reflect near-zero or net-outflow years.")

TITLE = "Sri Lanka\u2019s FDI inflows have remained persistently low"
SUB   = "Foreign direct investment, net inflows as a share of GDP, percent, 1970\u20132024"

# ---- embedded data, frozen from FDI.csv (World Bank WDI, July 2026) ----
DATA = {
    1970: -0.01306, 1971: 0.01266, 1972: 0.01175, 1973: 0.01739, 1974: 0.03917,
    1975: 0.00376,  1976: 0.00003, 1977: -0.02969, 1978: 0.05394, 1979: 1.39427,
    1980: 1.06868,  1981: 1.11563, 1982: 1.33300,  1983: 0.73103, 1984: 0.53963,
    1985: 0.43761,  1986: 0.46405, 1987: 0.89049,  1988: 0.65520, 1989: 0.28253,
    1990: 0.53974,  1991: 0.53719, 1992: 1.26379,  1993: 1.88108, 1994: 1.42020,
    1995: 0.42975,  1996: 0.86255, 1997: 2.84958,  1998: 1.22725, 1999: 1.12278,
    2000: 1.04207,  2001: 1.09075, 2002: 1.18828,  2003: 1.21133, 2004: 1.12668,
    2005: 1.11613,  2006: 1.69701, 2007: 1.86397,  2008: 1.84753, 2009: 0.96039,
    2010: 0.81445,  2011: 1.41088, 2012: 1.33592,  2013: 1.21148, 2014: 1.08278,
    2015: 0.79875,  2016: 1.01937, 2017: 1.45463,  2018: 1.70889, 2019: 0.83537,
    2020: 0.51470,  2021: 0.66883, 2022: 1.19249,  2023: 0.84802, 2024: 0.76408,
}

years = sorted(DATA.keys())
vals  = [DATA[y] for y in years]
avg   = float(np.mean(vals))

# ---- assertions: numbers stated in caption must follow from the data ----
assert round(avg, 2) == 0.91, 'caption states 1970-2024 average is 0.91%'
peak_yr  = max(DATA, key=DATA.get)
peak_val = DATA[peak_yr]
assert peak_yr == 1997,         'caption states peak in 1997'
assert round(peak_val, 1) == 2.8, 'caption states peak 2.8%'

INDIGO = C_BLUE    # benchmark hue carries the series here
RED    = C_RED

# ------------------------------------------------------------------ build chart
PNG = 'chart-1-sri-lanka-fdi.png'

plt.rcParams.update({'font.size': 14, 'xtick.labelsize': 12, 'ytick.labelsize': 12})

fig, ax = plt.subplots(figsize=(8, 6.6), dpi=DPI)

# panel style (single panel, no projection band, no gridlines)
style_ax(ax)
ax.set_xlim(1969, 2026)
ax.set_ylim(-0.3, 3.4)
ax.set_xticks([1970, 1980, 1990, 2000, 2010, 2020])
ax.set_yticks([0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
ax.set_yticklabels(['0', '0.5', '1.0', '1.5', '2.0', '2.5', '3.0%'])
# no x-axis title, no y-axis title

# zero reference
ax.axhline(0, color='#aaa', lw=0.8, zorder=1)

# 1970-2024 average (dashed red)
ax.axhline(avg, color=RED, lw=1.3, ls=(0, (5, 3)), zorder=3)
ax.text(1970.3, avg + 0.07, '1970\u20132024\navg: %.2f%%' % avg,
        fontsize=10, color=RED, ha='left', va='bottom', zorder=7,
        fontweight='bold', linespacing=1.25)

# main line
ax.plot(years, vals, color=INDIGO, lw=2.9, zorder=5, solid_capstyle='round')

# peak marker: 1997
ax.plot([peak_yr], [peak_val], 'o', mfc='white', mec=INDIGO, mew=2.6, ms=13,
        zorder=30, clip_on=False)
ax.text(peak_yr + 0.8, peak_val + 0.06, '%.1f%%\n%d' % (peak_val, peak_yr),
        fontsize=10.5, fontweight='bold', color=INDIGO,
        ha='left', va='bottom', linespacing=1.25, zorder=9)

# 2024 endpoint — label below the dot, shifted right of it
ax.plot([2024], [DATA[2024]], 'o', mfc=INDIGO, mec=INDIGO, ms=9,
        zorder=30, clip_on=False)
ax.text(2024.6, DATA[2024] - 0.14, '%.1f%%\n%d' % (DATA[2024], 2024),
        fontsize=10.5, fontweight='bold', color=INDIGO,
        ha='left', va='top', linespacing=1.25, zorder=9)

ax.set_box_aspect(BOX_ASPECT)          # plot area pinned to 1.253:1

SOURCE = SRC.replace('Source: ', '').strip()
NOTE_T = NOTE.replace('Note: ', '').strip()
lay = caption_layout(fig, SOURCE, NOTE_T)


def apply(bottom):
    fig.subplots_adjust(left=0.115, right=0.885, top=0.985, bottom=bottom + 0.055)


place_caption_snapped(fig, lay, [t for t in ax.get_xticklabels() if t.get_text()], apply)
fig.savefig(PNG, dpi=DPI, facecolor='white'); plt.close(fig)
add_title_band(PNG, TITLE, SUB)
