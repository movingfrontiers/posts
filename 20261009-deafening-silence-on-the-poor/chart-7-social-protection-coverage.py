"""Chart 7: social protection coverage.
Self-contained: house style and data are embedded. Requires numpy, matplotlib and Pillow.
Run: python chart-7-social-protection-coverage.py  -> writes chart-7-social-protection-coverage.png and chart-7-social-protection-coverage.csv
"""
# ---- Moving Frontiers house style (inlined) -------------------------------
# Plot in matplotlib on a transparent canvas, then compose() lays out title,
# subtitle, plot, caption and watermark in PIL with every gap measured ink to
# ink, and verify() re-measures the finished PNG and asserts the gaps.
import io, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

RED, GOLD, GREEN, BLUE, GREY = "#C62828", "#F9A825", "#00897B", "#283593", "#888888"
INK, PAPER = "#141414", "#FFFFFF"
def palette(n):
    return [[BLUE], [BLUE, RED], [BLUE, RED, GREEN], [BLUE, RED, GREEN, GOLD]][n - 1]

REF_W = 1980
GAP_TITLE_SUB, GAP_SUB_PLOT, GAP_PLOT_CAP, GAP_CAP_MARK, BORDER = 25, 70, 60, 20, 70
TITLE_PX, SUB_PX, CAP_PX = 61, 40, 30          # at REF_W; title ~3.1% of width
TITLE_RGB, SUB_RGB, CAP_RGB = (45, 45, 45), (100, 100, 100), (102, 102, 102)
WATERMARK = "movingfrontiers.substack.com"

_fp = font_manager.findfont("DejaVu Sans")
_fpb = font_manager.findfont(font_manager.FontProperties(family="DejaVu Sans", weight="bold"))
def _font(px, bold=False):
    return ImageFont.truetype(_fpb if bold else _fp, px)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 15,
    "xtick.labelsize": 14, "ytick.labelsize": 14, "legend.fontsize": 14,
    "axes.labelsize": 15, "axes.edgecolor": "#888888", "axes.linewidth": 1.0,
    "axes.facecolor": PAPER, "figure.facecolor": "none", "savefig.facecolor": "none",
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": "#444444", "ytick.color": "#444444", "text.color": INK,
})

def new_figure(w_in=9.2, h_in=7.34, dpi=200):
    fig = plt.figure(figsize=(w_in, h_in), dpi=dpi)
    return fig

def render_plot(fig):
    """Rasterise the figure on a transparent background and crop to its ink."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=fig.dpi, transparent=True, bbox_inches="tight", pad_inches=0.05)
    buf.seek(0)
    im = Image.open(buf).convert("RGBA")
    bbox = im.getchannel("A").getbbox()
    return im.crop(bbox)

def _text_layer(text, px, rgb, bold=False, width_px=None, align="left", linespacing=1.25):
    """Render wrapped text on a transparent layer cropped to its ink."""
    font = _font(px, bold)
    if width_px:
        # wrap by measured width
        lines = []
        for para in text.split("\n"):
            words, cur = para.split(), ""
            for w in words:
                t = (cur + " " + w).strip()
                if font.getlength(t) <= width_px or not cur:
                    cur = t
                else:
                    lines.append(cur); cur = w
            lines.append(cur)
    else:
        lines = text.split("\n")
    lh = int(round(px * linespacing))
    H = lh * len(lines) + px
    W = int(max(font.getlength(l) for l in lines)) + px
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, l in enumerate(lines):
        x = 0 if align == "left" else W - px - font.getlength(l)
        d.text((x, i * lh), l, font=font, fill=rgb + (255,))
    return layer.crop(layer.getchannel("A").getbbox())

def compose(plot_im, title, subtitle, source, note=None, out="chart.png", csv=None, csv_rows=None, W=REF_W):
    s = W / REF_W
    inner = W - 2 * BORDER
    # scale the plot to the inner width
    pw, ph = plot_im.size
    if pw != inner:
        plot_im = plot_im.resize((inner, int(ph * inner / pw)), Image.LANCZOS)
    t_layer = _text_layer(title, int(TITLE_PX * s), TITLE_RGB, bold=True, width_px=inner)
    s_layer = _text_layer(subtitle, int(SUB_PX * s), SUB_RGB, width_px=inner)
    cap = "Source: " + source + ("\nNote: " + note if note else "")
    c_layer = _text_layer(cap, int(CAP_PX * s), CAP_RGB, width_px=inner)
    m_layer = _text_layer(WATERMARK, int(CAP_PX * 1.2 * s), CAP_RGB)
    H = (BORDER + t_layer.height + GAP_TITLE_SUB + s_layer.height + GAP_SUB_PLOT + plot_im.height
         + GAP_PLOT_CAP + c_layer.height + GAP_CAP_MARK + m_layer.height + BORDER)
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    y = BORDER
    canvas.paste(t_layer, (BORDER, y), t_layer); y += t_layer.height + GAP_TITLE_SUB
    canvas.paste(s_layer, (BORDER, y), s_layer); y += s_layer.height + GAP_SUB_PLOT
    canvas.paste(plot_im, (BORDER, y), plot_im); y += plot_im.height + GAP_PLOT_CAP
    canvas.paste(c_layer, (BORDER, y), c_layer); y += c_layer.height + GAP_CAP_MARK
    canvas.paste(m_layer, (W - BORDER - m_layer.width, y), m_layer)
    canvas.save(out, dpi=(200, 200))
    if csv and csv_rows:
        import csv as _csv
        with open(csv, "w", newline="") as f:
            _csv.writer(f).writerows(csv_rows)
    verify(out, (t_layer.height, s_layer.height, plot_im.height, c_layer.height, m_layer.height))
    return out

def verify(path, heights):
    """Scan rows of the finished PNG for ink and assert the vertical gaps."""
    a = np.asarray(Image.open(path).convert("L"))
    ink_rows = np.where((a < 250).any(axis=1))[0]
    ink_cols = np.where((a < 250).any(axis=0))[0]
    assert ink_rows[0] == BORDER and ink_cols[0] == BORDER, ("border", ink_rows[0], ink_cols[0])
    assert a.shape[0] - 1 - ink_rows[-1] == BORDER, ("bottom border", a.shape[0] - 1 - ink_rows[-1])
    # blocks of ink separated by white gaps
    gaps, prev = [], ink_rows[0]
    for r in ink_rows[1:]:
        if r - prev > 1:
            gaps.append(r - prev - 1)
        prev = r
    expected = [GAP_TITLE_SUB, GAP_SUB_PLOT, GAP_PLOT_CAP, GAP_CAP_MARK]
    found = [g for g in gaps if g >= GAP_CAP_MARK - 1]
    # the four structural gaps must be present in order (text lines create smaller gaps)
    ok = [g for g in found if g in expected or g - 1 in expected or g + 1 in expected]
    assert len(ok) >= 4, ("structural gaps", found)
    print(f"verified {path}: size {a.shape[1]}x{a.shape[0]}, gaps {found}")
# ---------------------------------------------------------------------------

# ILO, World Social Protection Report 2024-26. Share covered by at least one cash benefit, 2023 (%).
income = [("High income", 85.9), ("Upper-middle income", 71.2), ("Lower-middle income", 32.4), ("Low income", 9.7)]
groups = [("Older persons (pension)", 79.6), ("Persons with severe disabilities", 38.9),
          ("Vulnerable persons (social assistance)", 37.3), ("Children (child or family benefit)", 28.2),
          ("Unemployed (unemployment benefit)", 16.7)]
world = 52.4

labels = [g[0] for g in groups][::-1] + [""] + [i[0] for i in income][::-1]
vals = [g[1] for g in groups][::-1] + [0] + [i[1] for i in income][::-1]
cols = [RED if v < world else BLUE for v in vals]

fig = new_figure(9.2, 7.6)
ax = fig.add_subplot(111)
ypos = list(range(len(labels)))
bars = ax.barh(ypos, vals, color=cols, height=0.62)
for y, v in zip(ypos, vals):
    if v:
        ax.text(v + 1.5, y, f"{v:.1f}%", va="center", ha="left", fontsize=14, color=INK, fontweight="bold")
ax.set_yticks(ypos)
ax.set_yticklabels(labels)
ax.axvline(world, color=INK, lw=1.2, ls=(0, (4, 3)))
ax.text(world + 1, len(labels) - 0.35, f"World, all people: {world}%", fontsize=13, color=INK, ha="left", va="center")
ax.set_xlim(0, 100)
ax.set_xticks(range(0, 101, 20))
ax.set_xticklabels([f"{v}%" for v in range(0, 101, 20)])
ax.set_ylim(-0.7, len(labels) + 0.2)
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
# section labels
ax.text(-2, len(labels) - 1 + 0.75, "By country income group", fontsize=13, color="#666", ha="right", va="center", fontstyle="italic")
ax.text(-2, len(groups) - 1 + 0.75, "By population group, world", fontsize=13, color="#666", ha="right", va="center", fontstyle="italic")

compose(render_plot(fig),
        title="Social protection reaches one in ten people in low-income countries",
        subtitle="Share of the population covered by at least one social protection cash benefit, 2023",
        source="ILO, World Social Protection Report 2024-26 (SDG indicator 1.3.1).",
        note="Effective coverage counts people actually receiving a benefit or actively contributing to a scheme, excluding health. About 3.8 billion people, 47.6 percent of the world population, received no benefit at all in 2023. Low-income countries spend 0.8 percent of GDP on social protection excluding health, against 16.2 percent in high-income countries.",
        out="chart-7-social-protection-coverage.png", csv="chart-7-social-protection-coverage.csv",
        csv_rows=[["group", "coverage_pct_2023"]] + [[i[0], i[1]] for i in income] + [[g[0], g[1]] for g in groups] + [["World, all people", world]])
