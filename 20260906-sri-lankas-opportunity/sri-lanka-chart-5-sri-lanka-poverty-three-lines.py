# =============================================================================
# Sri Lanka: poverty at the three global lines, chained across MPO vintages, 2017-2028
#
# Provenance, frozen vintage. Nothing is read from disk or the network; the seven
# outlook tables are embedded below and the chain is computed in this script.
#   April 2020, 2021, 2022 : World Bank Macro Poverty Outlook for Sri Lanka,
#                            poverty rows at the 2011 PPP lines ($1.90, $3.20, $5.50).
#   April 2023, 2024, 2025 : same, at the 2017 PPP lines ($2.15, $3.65, $6.85).
#   April 2026             : same, at the 2021 PPP lines ($3.00, $4.20, $8.30).
#   Vintage freeze date    : 29 August 2026. The chart is pinned to these editions;
#                            do not swap the embedded tables for a live source.
#
# Construction. Each year is taken from the most recent edition that reports it in
# an unflagged column (neither 'e' estimate nor 'f' forecast); 2025-2028 exist only
# flagged and come from April 2026. Changes of line definition are bridged at the
# oldest unflagged year the two vintages share: the 2017 PPP series is scaled to
# the 2021 PPP lines by the April 2026 / April 2025 ratio in 2023, and the 2011 PPP
# series is carried through it by the April 2023 / April 2022 ratio in 2020.
#
# The companion csv ships alongside as the published data file; asserts below pin
# its rows to the values this script derives.
# =============================================================================
"""Sri Lanka: poverty headcount at the global poverty lines, chained across seven
Macro Poverty Outlook vintages and expressed at the 2021 PPP lines.

Writes chart-sri-lanka-poverty-three-lines.png.
Run from inside this folder:  python3 chart-sri-lanka-poverty-three-lines-build.py
"""
import numpy as np
from matplotlib.lines import Line2D

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


def place_marks(fig, ax, YY, series, marks, fontsize=10.5, pad_frac=0.008, align_x=None, override=None, dots=True, dotsize=8.5):
    """Put a value label near its point, clear of every series and every other label."""
    inv=ax.transData.inverted()
    span=ax.get_ylim()[1]-ax.get_ylim()[0]
    pad=span*pad_frac
    out=[]; fixed=[]
    def box(t):
        bb=t.get_window_extent(fig.canvas.get_renderer())
        (a0,b0)=inv.transform((bb.x0,bb.y0)); (a1,b1)=inv.transform((bb.x1,bb.y1))
        return a0,a1,min(b0,b1),max(b0,b1)
    def bad(b,skip=None):
        a0,a1,lo,hi=b
        if a1>ax.get_xlim()[1] or a0<ax.get_xlim()[0]: return True
        if hi>ax.get_ylim()[1] or lo<ax.get_ylim()[0]: return True
        xs=[q for q in YY if a0-0.35<=q<=a1+0.35]
        for s in series:
            if any(lo-pad<=s[YY.index(q)]<=hi+pad for q in xs): return True
        gx,gy=0.4,span*0.018
        for j,ot in enumerate(out):
            if j==skip: continue
            ob=box(ot)
            if a0-gx<ob[1] and ob[0]<a1+gx and lo-gy<ob[3] and ob[2]<hi+gy: return True
        return False
    for item in marks:
        yr,txt,prefer,own,col=item
        yv=own[YY.index(yr)]
        if dots:
            ax.plot([yr],[yv],'o',color=col,ms=dotsize,zorder=30,
                    markeredgecolor='white',markeredgewidth=1.1,clip_on=False)
        cands=[]
        if override and (col,yr) in override:
            ox,oy,oha,ova=override[(col,yr)]; cands=[(ox,oy,oha,ova)]
        elif align_x is not None and yr in align_x:
            lx,ha=align_x[yr]
            for st in (0.045,0.065,0.088,0.113,0.140,0.170,0.203,0.240,0.280):
                for side in ([1,-1] if prefer=='above' else [-1,1]):
                    cands.append((lx,yv+side*span*st,ha,'bottom' if side>0 else 'top'))
            cands.append((lx,yv,ha,'center'))
        else:
            for st in (0.050,0.070,0.095,0.125,0.160,0.200,0.245):
                for side in ([1,-1] if prefer=='above' else [-1,1]):
                    for dx,ha in ((-0.3,'right'),(0.3,'left'),(0.0,'center'),
                                  (1.2,'left'),(-1.2,'right'),(2.4,'left'),(-2.4,'right'),
                                  (3.8,'left'),(-3.8,'right')):
                        xr=min(max(yr+dx,YY[0]),YY[-1])
                        cands.append((xr,own[YY.index(int(round(xr)))]+side*span*st,ha,
                                      'bottom' if side>0 else 'top'))
        t=ax.text(0,0,txt,fontsize=fontsize,fontweight='bold',color=col,linespacing=1.25,zorder=9)
        out.append(t)
        if override and (col,yr) in override:
            lx,ly,ha,va=cands[0]
            t.set_position((lx,ly)); t.set_ha(ha); t.set_va(va); fig.canvas.draw()
            fixed.append(len(out)-1); continue
        ok=False
        for lx,ly,ha,va in cands:
            t.set_position((lx,ly)); t.set_ha(ha); t.set_va(va); fig.canvas.draw()
            if not bad(box(t),skip=len(out)-1): ok=True; break
        if not ok:
            lx,ly,ha,va=cands[0]
            t.set_position((lx,ly)); t.set_ha(ha); t.set_va(va); fig.canvas.draw()
    for _ in range(60):
        fig.canvas.draw(); moved=False
        for i,t in enumerate(out):
            if i in fixed: continue
            if bad(box(t),skip=i):
                x,y=t.get_position(); up=t.get_va()!='top'
                ny=y+(span*0.030 if up else -span*0.030)
                if ax.get_ylim()[0]<ny<ax.get_ylim()[1]: t.set_y(ny); moved=True
        if not moved: break
    return out


# ---------------------------------------------------------------- embedded data

TITLE="After crisis surge, poverty is receding only slowly"
SUB=("Poverty rates at the $3.00 extreme poverty line, the $4.20 lower-middle-income line, and the $8.30 upper-middle-income "
"line (2021 PPP prices), percent")

# The poverty rows of each edition's Table 2, exactly as published. Flags follow the
# column headers: '' plain, 'e' estimate, 'f' forecast. Values are (low, mid, high)
# at that edition's line set.
LINESET={'apr2020':'2011 PPP','apr2021':'2011 PPP','apr2022':'2011 PPP',
         'apr2023':'2017 PPP','apr2024':'2017 PPP','apr2025':'2017 PPP',
         'apr2026':'2021 PPP'}
EDITIONS=['apr2020','apr2021','apr2022','apr2023','apr2024','apr2025','apr2026']
RAW={
 'apr2020':{2017:('',0.7,9.5,39.0),2018:('',0.6,8.9,37.6),2019:('e',0.5,8.5,36.5),
            2020:('f',1.2,11.3,41.7),2021:('f',1.0,11.0,41.1),2022:('f',0.9,10.2,39.7)},
 'apr2021':{2018:('',0.7,9.6,39.5),2019:('',0.6,9.2,38.6),2020:('e',1.2,11.7,42.3),
            2021:('f',1.1,10.9,40.7),2022:('f',1.0,10.4,39.7),2023:('f',0.9,10.0,38.9)},
 'apr2022':{2019:('',0.7,9.5,39.3),2020:('',1.2,11.7,42.3),2021:('e',1.0,10.9,40.9),
            2022:('f',1.0,10.8,40.8),2023:('f',1.0,10.8,40.7),2024:('f',1.0,10.7,40.6)},
 'apr2023':{2020:('',1.6,12.7,49.9),2021:('',1.5,13.1,51.1),2022:('e',5.8,25.0,65.0),
            2023:('f',6.6,27.4,67.2),2024:('f',6.4,26.9,66.9),2025:('f',6.1,26.1,66.0)},
 'apr2024':{2021:('',1.5,13.1,51.2),2022:('',4.1,22.7,64.4),2023:('e',5.2,25.9,66.6),
            2024:('f',4.7,24.8,65.8),2025:('f',4.1,23.2,65.6),2026:('f',3.8,22.2,64.4)},
 'apr2025':{2022:('',4.1,22.7,64.4),2023:('',5.4,27.1,68.0),2024:('e',4.6,24.5,65.9),
            2025:('f',3.9,22.7,65.0),2026:('f',3.7,21.9,64.1),2027:('f',3.5,21.2,63.2)},
 'apr2026':{2023:('',10.8,27.6,71.1),2024:('',9.3,25.0,69.3),2025:('e',7.9,22.1,66.7),
            2026:('f',6.9,20.1,65.4),2027:('f',6.5,19.5,64.5),2028:('f',6.2,18.9,63.4)},
}

# ---- construction: pick, bridge, chain ----
def pick(year):
    """Most recent edition with the year unflagged; else most recent edition with it at all."""
    for ed in reversed(EDITIONS):
        if year in RAW[ed] and RAW[ed][year][0]=='': return ed
    for ed in reversed(EDITIONS):
        if year in RAW[ed]: return ed
    raise KeyError(year)

# link factors at the oldest unflagged year the two line sets share
assert RAW['apr2026'][2023][0]=='' and RAW['apr2025'][2023][0]=='', 'the 2021/2017 PPP bridge year must be unflagged in both'
assert RAW['apr2023'][2020][0]=='' and RAW['apr2022'][2020][0]=='', 'the 2017/2011 PPP bridge year must be unflagged in both'
F1=tuple(a/b for a,b in zip(RAW['apr2026'][2023][1:],RAW['apr2025'][2023][1:]))   # 2021 PPP per 2017 PPP, at 2023
F2=tuple(a/b for a,b in zip(RAW['apr2023'][2020][1:],RAW['apr2022'][2020][1:]))   # 2017 PPP per 2011 PPP, at 2020
FACTOR={'2021 PPP':(1.0,1.0,1.0),'2017 PPP':F1,'2011 PPP':tuple(a*b for a,b in zip(F1,F2))}

YY=list(range(2017,2029))
KEYS=('P300','P420','P830')
S={k:[] for k in KEYS}; META=[]
for y in YY:
    ed=pick(y); flag=RAW[ed][y][0]; raw=RAW[ed][y][1:]; f=FACTOR[LINESET[ed]]
    v=tuple(round(a*b,1) for a,b in zip(raw,f))
    for k,x in zip(KEYS,v): S[k].append(x)
    META.append((y,ed,LINESET[ed],flag,raw,v))

# ---- the chart's stated numbers must follow from the embedded tables ----
assert [m[1] for m in META]==['apr2020','apr2021','apr2022','apr2023','apr2024','apr2025',
                              'apr2026','apr2026','apr2026','apr2026','apr2026','apr2026'], 'edition per year'
assert [m[3] for m in META]==['']*9+['f','f','f'] if False else True
assert [m[3] for m in META][:8]==['']*8 and [m[3] for m in META][8:]==['e','f','f','f'], 'flags per year'
for _y,_v in ((2017,(1.9,10.5,48.1)),(2021,(3.0,13.3,53.5)),(2023,(10.8,27.6,71.1)),(2028,(6.2,18.9,63.4))):
    _i=YY.index(_y)
    assert tuple(S[k][_i] for k in KEYS)==_v, 'labels at %d'%_y
# link factors as documented in the note
assert (round(F1[0],2),round(F1[1],3),round(F1[2],3))==(2.0,1.018,1.046), 'F1'
assert (round(F2[0],3),round(F2[1],3),round(F2[2],3))==(1.333,1.085,1.180), 'F2'
# the title's claim: at the $4.20 line poverty more than doubled into 2023 and the
# 2028 forecast remains above the pre-crisis level
assert S['P420'][YY.index(2023)]>2*S['P420'][YY.index(2021)], 'more than doubled'
assert S['P420'][YY.index(2028)]>S['P420'][YY.index(2021)], 'still above pre-crisis'

NH=YY.index(2024)+1            # solid through the last unflagged year
AMBER=C_GOLD; AMBERTXT=C_LMTXT; RED=C_RED; INDIGO=C_BLUE
COL={'P300':RED,'P420':AMBER,'P830':INDIGO}
TXT={'P300':RED,'P420':AMBERTXT,'P830':INDIGO}
NAME={'P300':'$3.00 a day','P420':'$4.20 a day','P830':'$8.30 a day'}

NOTE=("Note: As global poverty line definitions have changed over time, the numbers shown here are chained.")

plt.rcParams.update({'font.size':14,'xtick.labelsize':12,'ytick.labelsize':12})
fig,ax=plt.subplots(figsize=(8,6.6),dpi=DPI)

YMAX=84
ax.axvspan(2025.5,2028.5,color='#F4F4F4',zorder=0)
ax.axvline(2025.5,ls=':',lw=1.4,color='#777',zorder=1)
ax.axvline(2024.5,ls=':',lw=1.2,color='#AAA',zorder=1)
ax.grid(axis='y',color=C_GRID,lw=0.8,zorder=0); ax.set_axisbelow(True)
style_ax(ax)
ax.set_xlim(2016.5,2028.5); ax.set_xticks([2017,2019,2021,2023,2025,2027])
ax.set_ylim(0,YMAX); ax.set_yticks(range(0,81,20))

for k in KEYS:
    ax.plot(YY[:NH],S[k][:NH],color=COL[k],lw=2.9,zorder=5,solid_capstyle='round')
    ax.plot(YY[NH-1:],S[k][NH-1:],color=COL[k],lw=2.5,ls=(0,(4.5,2.2)),zorder=5)
    ax.plot(YY[:NH],S[k][:NH],'o',color=COL[k],ms=4.6,zorder=6,
            markeredgecolor='white',markeredgewidth=0.9)

ax.text(2025.0,YMAX*0.985,'est',fontsize=9.5,color='#777',style='italic',ha='center',va='top')
ax.text(2027.0,YMAX*0.985,'forecast',fontsize=10.5,color='#777',style='italic',ha='center',va='top')

# ---- fully explicit label overrides: x=year, y=value+offset, stacked clear of dots ----
# dot radius in data units ~ YMAX*0.034 ~ 2.9; offset of 4 clears the dot cleanly.
OFF=3.5   # upward offset from the series value (tight, just clears the dot)
OFF2=5.5  # slightly larger where lines are closer together (2023 P300/P420 gap only 16.8)
def lbl(yr,k): return '%.1f%%'%S[k][YY.index(yr)]
def yv(yr,k):  return S[k][YY.index(yr)]

# Exact y positions computed to clear the dot (radius ~2.5 data units) and stack
# labels without overlap (text height ~2.8 data units). All centre-aligned at x=year.
OVR={
  # 2017: P300 dot=1.9, P420 dot=10.5, P830 dot=48.1
  (RED,     2017): (2017.0,  4.4, 'center','bottom'),
  (AMBERTXT,2017): (2017.0, 13.0, 'center','bottom'),
  (INDIGO,  2017): (2017.0, 50.6, 'center','bottom'),
  # 2021: P300 dot=3.0, P420 dot=13.3, P830 dot=53.5
  (RED,     2021): (2020.85,  5.5, 'center','bottom'),
  (AMBERTXT,2021): (2020.85, 15.8, 'center','bottom'),
  (INDIGO,  2021): (2020.85, 56.0, 'center','bottom'),
  # 2023: P300 dot=10.8, P420 dot=27.6, P830 dot=71.1
  (RED,     2023): (2023.0, 13.3, 'center','bottom'),
  (AMBERTXT,2023): (2023.0, 30.1, 'center','bottom'),
  (INDIGO,  2023): (2023.0, 73.6, 'center','bottom'),
  # 2025: P300 dot=7.9, P420 dot=22.1, P830 dot=66.7
  (RED,     2025): (2025.0, 10.4, 'center','bottom'),
  (AMBERTXT,2025): (2025.0, 24.6, 'center','bottom'),
  (INDIGO,  2025): (2025.0, 69.2, 'center','bottom'),
  # 2028: P300 dot=6.2, P420 dot=18.9, P830 dot=63.4
  (RED,     2028): (2028.0,  8.7, 'center','bottom'),
  (AMBERTXT,2028): (2028.0, 21.4, 'center','bottom'),
  (INDIGO,  2028): (2028.0, 65.9, 'center','bottom'),
}
MK=[]
for k in KEYS:
    for yr in (2017,2021,2023,2025,2028):
        MK.append((yr,lbl(yr,k),'above',S[k],TXT[k]))
place_marks(fig,ax,YY,[S[k] for k in KEYS],MK,fontsize=10.0,align_x=None,override=OVR)

leg=fig.legend(handles=[Line2D([],[],color=COL[k],lw=3.0,label=NAME[k]) for k in KEYS],
           loc='lower center',bbox_to_anchor=(0.5,0.10),ncol=3,frameon=False,fontsize=12,
           columnspacing=3.0,handlelength=2.2)
ax.set_box_aspect(BOX_ASPECT)          # plot area pinned to 1.253:1

PNG='chart-5-sri-lanka-poverty-three-lines.png'
SRC=("World Bank, Macro Poverty Outlook for Sri Lanka, April 2020 through April 2026 editions; author's calculations.")
SOURCE=SRC
NOTE_T=NOTE.replace('Note: ','').strip()
lay=caption_layout(fig,SOURCE,NOTE_T)


def apply(bottom):
    fig.subplots_adjust(left=0.115,right=0.885,top=0.985,bottom=bottom+0.115)
    leg.set_bbox_to_anchor((0.5,bottom+0.030),transform=fig.transFigure)


place_caption_snapped(fig,lay,[t for t in leg.get_texts()],apply)
fig.savefig(PNG,dpi=DPI,facecolor='white'); plt.close(fig)
add_title_band(PNG,TITLE,SUB)

# ---- companion csv, pinned to the derived values ----
HDR=('# chart,"Sri Lanka: poverty headcount at the global poverty lines, chained across MPO vintages to 2021 PPP, 2017 to 2028"\n'
'# source,"World Bank, Macro Poverty Outlook for Sri Lanka, April 2020 through April 2026 editions, poverty headcount rows; author\'s calculations."\n'
'# method,"Each year is taken from the most recent edition reporting it in an unflagged column (neither e nor f); 2025 to 2028 exist only flagged and come from April 2026. Line-definition changes are bridged at the oldest unflagged year both vintages share: 2017 PPP values are scaled to the 2021 PPP lines by the April 2026 / April 2025 ratio at 2023 (2.000, 1.018, 1.046), and 2011 PPP values are carried through it by the April 2023 / April 2022 ratio at 2020 (1.333, 1.085, 1.180), rounded to one decimal."\n'
'# note,"published_* columns are the values exactly as printed at that edition\'s own line set; the *_eq columns are the chained 2021 PPP equivalents that the chart plots. Each edition\'s actual data end with the 2016 or 2019 HIES, so every row is model-based."\n'
'# rates are percent of population\n\n'
'year,source_edition,line_set,column_flag,published_low,published_mid,published_high,'
'poverty_rate_300eq_percent,poverty_rate_420eq_percent,poverty_rate_830eq_percent\n')
with open('chart-sri-lanka-poverty-three-lines.csv','w') as f:
    f.write(HDR)
    for y,ed,ls,flag,raw,v in META:
        f.write('%d,%s,%s,%s,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f\n'%(
            y,'April '+ed[3:],ls,flag if flag else 'none',*raw,*v))
print('  wrote chart-sri-lanka-poverty-three-lines.csv  %d rows'%len(META))
