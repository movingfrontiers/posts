"""
Chart 7. Enterprise Survey obstacles, Sri Lanka 2011 vs 2025.
Built with the Moving Frontiers chart template. Writes the chart PNG and a CSV
of the plotted series.
"""
import pandas as pd, numpy as np

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



OUT = "chart-7-obstacles.png"
CSV = "chart-7-obstacles.csv"

P = {2011: "/mnt/user-data/uploads/SriLanka-2011-full-data-.dta",
     2025: "/mnt/user-data/uploads/SriLanka-2025-full-data.dta"}
D = {y: pd.read_stata(p, convert_categoricals=False).query("wstrict == wstrict")
     for y, p in P.items()}

OBS = {"j30c": "Licensing and permits", "j30b": "Tax administration", "j30a": "Tax rates",
       "k30": "Access to finance", "d30b": "Customs and trade", "e30": "Informal competition",
       "l30b": "Inadequate skills", "l30a": "Labor regulations", "j30f": "Corruption",
       "c30a": "Electricity", "j30e": "Political instability", "i30": "Crime and disorder",
       "g30a": "Access to land", "d30a": "Transport", "h30": "Courts"}


def major(y):
    d = D[y]
    out = {}
    for v, name in OBS.items():
        if v not in d.columns:
            continue
        s = d[d[v].between(0, 4)]
        if len(s):
            out[name] = 100 * s.loc[s[v] >= 3, "wstrict"].sum() / s.wstrict.sum()
    return pd.Series(out)


t = pd.DataFrame({2011: major(2011), 2025: major(2025)}).dropna().sort_values(2025)

csv = t.round(1).sort_values(2025, ascending=False)
csv.index.name = "obstacle"
csv.columns = ["share_2011", "share_2025"]
csv["change"] = (csv.share_2025 - csv.share_2011).round(1)
csv.to_csv(CSV)

fig = plt.figure(figsize=(8, 8), dpi=DPI)
ax = fig.add_subplot(111)
y = np.arange(len(t))

ax.hlines(y, t[2011], t[2025], color="#d5d5d5", lw=2.4, zorder=2)
ax.scatter(t[2011], y, s=95, color=C_BLUE, zorder=3, label="2011")
ax.scatter(t[2025], y, s=95, color=C_RED, zorder=4, label="2025")

ax.set_yticks(y)
ax.set_yticklabels(t.index)
ax.set_xlim(0, 52)
ax.set_xticks([0, 10, 20, 30, 40, 50])
ax.set_ylim(-0.8, len(t) - 0.2)
ax.set_xlabel("Percent of firms reporting a major or very severe obstacle")
style_ax(ax)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.grid(axis="x", color="#ededed", lw=0.8, zorder=0)
ax.set_axisbelow(True)

leg = ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.085), ncol=2,
                frameon=False, scatterpoints=1, handletextpad=0.35,
                columnspacing=2.0)

SOURCE = ("World Bank Enterprise Surveys, Sri Lanka 2011 and 2025 rounds, author's "
          "calculations from firm level microdata weighted by strict eligibility weights.")
NOTE = ("Firms rate each item on a five point scale running from no obstacle to very severe "
        "obstacle, and the chart shows the share choosing major or very severe. The 2011 round "
        "covers 610 firms and the 2025 round 607, both drawn from the formal non-agricultural "
        "private sector. The two rounds are fourteen years apart and are separated by the "
        "aftermath of the war, the pandemic and the sovereign default, so they are better read "
        "as two snapshots than as a trend.")
CLOSERS = ("Establishments that considered Sri Lanka and located elsewhere are outside the "
           "sampling frame.",)

lay = caption_layout(fig, SOURCE, NOTE, closers=CLOSERS)


def apply(bottom):
    fig.subplots_adjust(left=0.262, right=0.985, top=0.985, bottom=bottom)


anchor = [leg.get_texts()[0], leg.get_texts()[1], ax.xaxis.label]
place_caption_snapped(fig, lay, anchor, apply)

fig.savefig(OUT, dpi=DPI, facecolor="white")
plt.close(fig)

add_title_band(OUT,
               "Enterprise surveys suggest increasing obstacles to doing business",
               "Obstacles reported by firms in Sri Lanka, 2011 and 2025")
print("saved", OUT, "and", CSV)
