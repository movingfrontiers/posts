# =============================================================================
# Chart 3.2: What past decades tell us about Sri Lanka's high-income horizon
#
# Provenance, frozen vintage. Nothing is read from disk or the network.
#   GNI per capita        : World Bank WDI, July 2026 vintage, Atlas method, current US$.
#   Thresholds 1990-2025  : World Bank OGHIST, 1 July 2026, Thresholds worksheet,
#                           official values as published, no smoothing.
#   Classifications       : World Bank OGHIST, 1 July 2026, Country Analytical History.
#   Vintage freeze date   : 1 July 2026. The chart is pinned to this vintage; do not swap
#                           the embedded data for a live API call.
#
# Reduction: val() is called only for 1990-2025 and TH[y] only for 1990-2025. The OGHIST
# panel is used only for Sri Lanka's own classification row, scanned across its year
# columns to date the transitions, so the pickle reduces to that one row.
# =============================================================================
"""Sri Lanka, two panels: the same extrapolation on two successive decades of growth."""
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


import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from PIL import Image, ImageDraw, ImageFont

OUT=''
# ---- embedded series, see the provenance header ----
# Sri Lanka GNI per capita, Atlas method, current US$, 1990-2025
GNI={1990:490.0,1991:530.0,1992:580.0,1993:630.0,1994:670.0,1995:720.0,1996:760.0,1997:810.0,1998:810.0,1999:830.0,2000:860.0,2001:810.0,2002:820.0,2003:910.0,2004:1030.0,2005:1170.0,2006:1320.0,2007:1500.0,2008:1740.0,2009:1950.0,2010:2360.0,2011:2830.0,2012:3340.0,2013:3630.0,2014:3810.0,2015:3920.0,2016:4020.0,2017:4220.0,2018:4350.0,2019:4220.0,2020:3880.0,2021:4010.0,2022:3620.0,2023:3550.0,2024:3870.0,2025:4670.0}
# official operational thresholds [low, lower-middle, upper-middle], 1990-2025
TH={1990:[610.0, 2465.0, 7620.0],1991:[635.0, 2555.0, 7910.0],1992:[675.0, 2695.0, 8355.0],1993:[695.0, 2785.0, 8625.0],1994:[725.0, 2895.0, 8955.0],1995:[765.0, 3035.0, 9385.0],1996:[785.0, 3115.0, 9645.0],1997:[785.0, 3125.0, 9655.0],1998:[760.0, 3030.0, 9360.0],1999:[755.0, 2995.0, 9265.0],2000:[755.0, 2995.0, 9265.0],2001:[745.0, 2975.0, 9205.0],2002:[735.0, 2935.0, 9075.0],2003:[765.0, 3035.0, 9385.0],2004:[825.0, 3255.0, 10065.0],2005:[875.0, 3465.0, 10725.0],2006:[905.0, 3595.0, 11115.0],2007:[935.0, 3705.0, 11455.0],2008:[975.0, 3855.0, 11905.0],2009:[995.0, 3945.0, 12195.0],2010:[1005.0, 3975.0, 12275.0],2011:[1025.0, 4035.0, 12475.0],2012:[1035.0, 4085.0, 12615.0],2013:[1045.0, 4125.0, 12745.0],2014:[1045.0, 4125.0, 12735.0],2015:[1025.0, 4035.0, 12475.0],2016:[1005.0, 3955.0, 12235.0],2017:[995.0, 3895.0, 12055.0],2018:[1025.0, 3995.0, 12375.0],2019:[1035.0, 4045.0, 12535.0],2020:[1045.0, 4095.0, 12695.0],2021:[1085.0, 4255.0, 13205.0],2022:[1135.0, 4465.0, 13845.0],2023:[1145.0, 4515.0, 14005.0],2024:[1135.0, 4495.0, 13935.0],2025:[1175.0, 4635.0, 14375.0]}
# Sri Lanka's OGHIST classification row, 1987-2025, None where unclassified
OG={1987:'L',1988:'L',1989:'L',1990:'L',1991:'L',1992:'L',1993:'L',1994:'L',1995:'L',1996:'L',1997:'LM',1998:'LM',1999:'LM',2000:'LM',2001:'LM',2002:'LM',2003:'LM',2004:'LM',2005:'LM',2006:'LM',2007:'LM',2008:'LM',2009:'LM',2010:'LM',2011:'LM',2012:'LM',2013:'LM',2014:'LM',2015:'LM',2016:'LM',2017:'LM',2018:'UM',2019:'LM',2020:'LM',2021:'LM',2022:'LM',2023:'LM',2024:'LM',2025:'UM'}
def val(y): return GNI[y]
DRIFT=0.01244
YR=list(range(1990,2051))
S={y:val(y) for y in range(1990,2026)}
def thr(y,j): return TH[y][j] if y<=2025 else TH[2025][j]*(1+DRIFT)**(y-2025)
tL=[thr(y,0) for y in YR]; tM=[thr(y,1) for y in YR]; tU=[thr(y,2) for y in YR]

WIN=[(2016,2025,'Last decade, 2016 to 2025'),
     (2006,2015,'Previous decade, 2006 to 2015')]
RATE=[float(np.median([S[y]/S[y-1]-1 for y in range(a,z+1)])) for a,z,_ in WIN]

# official transitions from OGHIST, never inferred from the plotted line
TRANS=[]; prev=None
for y in sorted(OG):
    if OG[y] is None: continue
    if OG[y]!=prev and prev is not None and y>=1990: TRANS.append(y)
    prev=OG[y]
print('  OGHIST transitions in window:',TRANS)
# ---- the caption's stated numbers must follow from the embedded data ----
assert round(DRIFT*100,3)==1.244, 'caption states a 1.244 percent threshold drift'
assert TRANS==[1997,2018,2019,2025], 'caption states 1997, a single year at upper-middle in 2018, 2019 and 2025'
assert OG[2018]=='UM' and OG[2019]=='LM' and OG[2025]=='UM', (
    'caption states upper-middle for one year in 2018, back to lower-middle in 2019, upper-middle again in 2025')
assert [round(100*r,1) for r in RATE]==[2.8,13.2], 'panel titles state 2.8 and 13.2 percent'


PATHS={}      # panel label -> {year: GNI}, the exact series each panel plots
CROSS={}      # panel label -> first year the path clears the high-income line, else None

BAND={'L':C_RED,'LM':C_GOLD,'UM':C_LBLU,'H':C_BLUE}
plt.rcParams.update({'font.size':14,'xtick.labelsize':12,'ytick.labelsize':12})
fig,axs=plt.subplots(1,2,figsize=(11.2,7.1),dpi=DPI,sharey=True)
YLO,YHI=380,150000
for ax,(rate,(a,z,lab)) in zip(axs,zip(RATE,WIN)):
    P=dict(S)
    for y in range(2026,2051): P[y]=P[y-1]*(1+rate)
    ser=[P[y] for y in YR]
    PATHS[lab]=dict(P)
    ax.fill_between(YR,YLO,tL,color=BAND['L'],zorder=0)
    ax.fill_between(YR,tL,tM,color=BAND['LM'],zorder=0)
    ax.fill_between(YR,tM,tU,color=BAND['UM'],zorder=0)
    ax.fill_between(YR,tU,YHI,color=BAND['H'],zorder=0)
    for t in (tL,tM,tU): ax.plot(YR,t,ls='--',lw=1.3,color='white',alpha=0.85,zorder=2)
    ax.axvline(2025.5,ls=':',lw=1.8,color='white',zorder=3)
    n=YR.index(2025)+1
    ax.plot(YR[:n],ser[:n],color=PAPER,lw=3.0,zorder=5,solid_capstyle='round',
            path_effects=[pe.Stroke(linewidth=6.0,foreground=INK),pe.Normal()])
    ax.plot(YR[n-1:],ser[n-1:],color=PAPER,lw=2.8,ls=(0,(5,2.4)),zorder=5,
            path_effects=[pe.Stroke(linewidth=5.8,foreground=INK),pe.Normal()])
    ax.set_yscale('log'); ax.set_ylim(YLO,YHI); ax.set_xlim(1990,2050)
    ax.set_box_aspect(1)          # square plotting area, independent of data ranges
    ax.set_xticks([1990,2000,2025,2050])
    yt=[500,1000,2000,5000,10000,20000,50000,100000]
    ax.set_yticks(yt); ax.set_yticklabels(['$%s'%format(t,',') for t in yt]); ax.minorticks_off()
    for s in ('top','right'): ax.spines[s].set_visible(False)
    ax.set_title('%s\n%.1f%% a year'%(lab,100*rate),fontsize=12,fontweight='bold',color='#333',
                 pad=9,linespacing=1.35)
    # historical transitions, all three panels identical
    # identical in every panel: same anchor, same offset, same size
    MK={1997:(1.6,0.62,'left'),2018:(-1.6,1.70,'right'),2019:(1.6,0.60,'left'),2025:(1.6,1.62,'left')}
    for yr,(dx,fy,ha) in MK.items():
        ax.plot([yr],[S[yr]],'o',mfc=PAPER,mec=INK,mew=2.4,ms=10,zorder=8,clip_on=False)
        ax.text(yr+dx,S[yr]*fy,str(yr),fontsize=11,fontweight='bold',color=INK,ha=ha,va='center',
                zorder=9,bbox=dict(boxstyle='round,pad=0.24',facecolor=PAPER,edgecolor='none'))
    # the high-income crossing, if it happens by 2050
    hit=next((y for y in range(2026,2051) if P[y]>thr(y,2)),None)
    CROSS[lab]=hit
    if hit:
        ax.plot([hit],[P[hit]],'o',mfc=PAPER,mec=INK,mew=2.8,ms=13,zorder=8,clip_on=False)
        ax.text(hit-1.6,P[hit]*1.70,'%d'%hit,fontsize=11,fontweight='bold',color=INK,ha='right',
                va='center',zorder=9,bbox=dict(boxstyle='round,pad=0.24',facecolor=PAPER,edgecolor='none'))
    else:
        n2=np.log(thr(2025,2)/P[2025])/np.log((1+rate)/(1+DRIFT)) if rate>DRIFT else None
        msg='high income\nnot reached\nby 2050' if n2 is None else 'high income\nnot until %d'%(2025+int(np.ceil(n2)))
        ax.text(1991.5,118000,msg,fontsize=11,fontweight='bold',color=PAPER,ha='left',va='top',
                linespacing=1.3,zorder=9)
BANDLAB=[('HIGH\nINCOME',np.sqrt(tU[-1]*YHI),'#283593'),
         ('UPPER-\nMIDDLE',np.sqrt(tM[-1]*tU[-1]),'#00897B'),
         ('LOWER-\nMIDDLE',np.sqrt(tL[-1]*tM[-1]),'#B8860B'),
         ('LOW\nINCOME',np.sqrt(YLO*tL[-1]),'#C62828')]
for lab,yv,cc in BANDLAB:
    axs[-1].text(1.015,yv,lab,transform=axs[-1].get_yaxis_transform(),fontsize=11,fontweight='bold',
                color=cc,ha='left',va='center',linespacing=1.25,clip_on=False,zorder=6)
fig.tight_layout(rect=[0,0.300,0.960,0.985]); fig.subplots_adjust(wspace=0.16)

CAPFS=7.8
SOURCE = 'World Bank OGHIST and World Development Indicators, July 2026 release, for the income classifications, the official thresholds and GNI per capita (Atlas method, current US$).'
NOTE = "This is not a forecast. Each panel carries a single past growth rate forward from 2025 and makes no allowance for policy, demography, technology or shocks. The rate is the median of Sri Lanka's annual growth in GNI per capita over the decade named above the panel. Thresholds beyond 2025 rise at 1.244 percent a year, the median annual increase of the past decade. Sri Lanka held upper-middle income for a single year, 2018, fell back to lower-middle in 2019, and regained upper-middle in 2025."
TITLE = 'Sri Lanka’s path to high income'
SUB = "GNI per capita extrapolated to 2050 on the median growth of two successive decades (current US$, Atlas)"

# Aspect: two-panel figure, so the 1.253:1 plot-area ratio is not pinned; the canvas
# is sized to the panels (chart standard, section 4).
lay = caption_layout(fig, SOURCE, NOTE)


def apply(bottom):
    fig.subplots_adjust(left=0.085, right=0.905, top=0.925, bottom=bottom + 0.055,
                        wspace=0.16)


place_caption_snapped(fig, lay,
                      [t for t in axs[0].get_xticklabels() if t.get_text()], apply)

FN = 'chart-6-sri-lanka-two-panels.png'
fig.savefig(OUT + FN, dpi=DPI, facecolor='white'); plt.close(fig)
add_title_band(OUT + FN, TITLE, SUB)
for (a2, z2, lab), rt in zip(WIN, RATE):
    print('  %-34s %.2f%%' % (lab, 100 * rt))

# =============================================================================
# Companion csv. Written from the same objects the chart plots, so the file and
# the figure cannot drift: PATHS holds each panel's extrapolated series, thr()
# supplies the thresholds, OG the published classification.
# =============================================================================
LAB1,LAB2=WIN[0][2],WIN[1][2]
R1,R2=RATE[0],RATE[1]

# the "high income not until" year quoted on a panel that never crosses by 2050
def horizon(rate):
    if rate<=DRIFT: return None
    n=np.log(thr(2025,2)/PATHS[LAB1][2025])/np.log((1+rate)/(1+DRIFT))
    return 2025+int(np.ceil(n))
H1=CROSS[LAB1] or horizon(R1)
H2=CROSS[LAB2] or horizon(R2)

# ---- the csv's stated numbers must follow from the embedded data ----
assert PATHS[LAB1][2025]==PATHS[LAB2][2025]==GNI[2025], 'both panels branch from the same 2025 actual'
assert all(PATHS[LAB1][y]==PATHS[LAB2][y]==GNI[y] for y in range(1990,2026)), 'history is identical in both panels'
assert CROSS[LAB1] is None and CROSS[LAB2]==2036, 'panel 1 does not cross by 2050, panel 2 crosses in 2036'
assert H1==2098, 'panel 1 annotation states high income not until 2098'

CSVFN='chart-6-sri-lanka-two-panels.csv'
HDR=(
'# chart,"Sri Lanka: GNI per capita extrapolated to 2050 on the median growth of two successive decades (current US$, Atlas)"\n'
'# source,"World Bank OGHIST and World Development Indicators, July 2026 release: income classifications, official operational thresholds, and GNI per capita (Atlas method, current US$)."\n'
'# vintage,"Frozen 1 July 2026. Values are embedded in the build script, not fetched; do not refresh against a live API."\n'
'# method,"History (1990-2025) is the published GNI per capita series and is identical in both panels. From 2026 each panel compounds the 2025 actual at a single constant rate, the median of Sri Lanka annual growth in GNI per capita over the decade named in the panel: %.4f (%.1f percent) for %s and %.4f (%.1f percent) for %s. Thresholds through 2025 are the official operational values as published; beyond 2025 they rise at %.5f (1.244 percent) a year, the median annual increase of the past decade."\n'
'# note,"This is not a forecast. Neither path makes any allowance for policy, demography, technology or shocks. The classification column is the group as published in OGHIST, which the World Bank assigns on the GNI estimate available at the time; later revisions can move the plotted line across a threshold without changing the classification, as they do in 2016, 2017 and 2019. Sri Lanka held upper-middle income for a single year, 2018, fell back to lower-middle in 2019, and regained upper-middle in 2025."\n'
'# crossing,"%s does not reach the high-income threshold by 2050 (extending the same rate puts it at %d). %s crosses in %d."\n'
'# units,"GNI per capita and thresholds in current US$; classification in OGHIST codes L, LM, UM, H."\n\n'
'year,period,gni_per_capita_usd,oghist_class,is_transition_year,'
'threshold_basis,threshold_low_to_lm_usd,threshold_lm_to_um_usd,threshold_um_to_high_usd,'
'path_last_decade_2016_2025_usd,path_previous_decade_2006_2015_usd\n'
)%(R1,100*R1,LAB1,R2,100*R2,LAB2,DRIFT,LAB1,H1,LAB2,CROSS[LAB2])

with open(OUT+CSVFN,'w') as f:
    f.write(HDR)
    for y in YR:
        hist   = y<=2025
        f.write('%d,%s,%s,%s,%s,%s,%.1f,%.1f,%.1f,%.2f,%.2f\n'%(
            y,
            'actual' if hist else 'extrapolated',
            ('%.1f'%GNI[y]) if hist else '',
            OG.get(y,'') if hist else '',
            'yes' if y in TRANS else 'no',
            'official' if hist else 'projected',
            thr(y,0), thr(y,1), thr(y,2),
            PATHS[LAB1][y], PATHS[LAB2][y]))
print('  %s %d rows'%(CSVFN,len(YR)))
