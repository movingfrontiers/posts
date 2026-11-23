# chart-9-biggest-gains
# ---- house style (inlined) -------------------------------------------------
import csv, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image, ImageDraw, ImageFont, ImageChops

W, H, M, DPI = 2160, 2160, 150, 200
PX = 72 / DPI
GAP_TITLE_UNIT, GAP_UNIT_EXPL, GAP_HEAD_PLOT, GAP_PLOT_CAP, GAP_CAP_MARK = 34, 22, 70, 70, 90
NAVY, RED, SKY, GOLD = "#0B2265", "#D0412F", "#5B8FCC", "#C9962B"
INK, GREY_TXT, LABEL, BAND = "#111111", "#555555", "#333333", "#E6EAF2"
T_TITLE, T_UNIT, T_SOFT = (17, 17, 17), (34, 34, 34), (95, 95, 95)
FD = "/usr/share/fonts/truetype/"
F_REG, F_BOLD = FD + "liberation/LiberationSans-Regular.ttf", FD + "liberation/LiberationSans-Bold.ttf"
F_CAL, F_CALB = FD + "crosextra/Carlito-Regular.ttf", FD + "crosextra/Carlito-Bold.ttf"
for f in (F_REG, F_BOLD, F_CAL, F_CALB):
    fm.fontManager.addfont(f)
ARIAL, CALIBRI = "Liberation Sans", "Carlito"
S_TICK, S_LABEL, S_VALUE, S_HEAD = 42 * PX, 46 * PX, 47 * PX, 54 * PX
plt.rcParams.update({"font.family": ARIAL, "font.size": S_TICK, "axes.unicode_minus": False})

def style_axes(ax, yticks=False):
    ax.grid(False)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(INK); ax.spines["bottom"].set_linewidth(1.6)
    ax.tick_params(axis="x", direction="out", length=12, width=1.6, pad=10, colors=INK, labelsize=S_TICK)
    ax.tick_params(axis="y", length=0, pad=10, colors=LABEL, labelsize=S_TICK)
    if not yticks:
        ax.set_yticks([])

def zero_line(ax, x0=None, x1=None):
    lo, hi = ax.get_xlim()
    ax.plot([lo if x0 is None else x0, hi if x1 is None else x1], [0, 0], color=INK, lw=2.6,
            dashes=(1, 1.6), zorder=1)
    ax.set_xlim(lo, hi)

def _wrap(d, text, font, width):
    out = []
    for para in text.split("\n"):
        line = ""
        for w in para.split(" "):
            t = (line + " " + w).strip()
            if d.textlength(t, font=font) <= width or not line:
                line = t
            else:
                out.append(line); line = w
        out.append(line)
    return "\n".join(out)

def _block(d, text, font, ls, y, fill, x=M, draw=True):
    sp = (ls - 1) * font.size
    b = d.multiline_textbbox((0, 0), text, font=font, spacing=sp)
    if draw:
        d.multiline_text((x - b[0], y - b[1]), text, font=font, spacing=sp, fill=fill)
    return int(round(y + (b[3] - b[1])))

def _ink(im):
    return ImageChops.difference(im.convert("RGB"), Image.new("RGB", im.size, "white")).getbbox()

def compose(plot_fn, title, unit, caption, out, expl=None):
    canvas = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(canvas)
    ft, fu, fe = ImageFont.truetype(F_BOLD, 92), ImageFont.truetype(F_REG, 54), ImageFont.truetype(F_REG, 42)
    fc, fw = ImageFont.truetype(F_REG, 37), ImageFont.truetype(F_BOLD, 48)
    cw = W - 2 * M
    y = _block(d, _wrap(d, title, ft, cw), ft, 1.18, M, T_TITLE)
    y = _block(d, _wrap(d, unit, fu, cw), fu, 1.3, y + GAP_TITLE_UNIT, T_UNIT)
    if expl:
        y = _block(d, _wrap(d, expl, fe, cw), fe, 1.42, y + GAP_UNIT_EXPL, T_SOFT)
    mark = "Moving Frontiers"
    mb = d.textbbox((0, 0), mark, font=fw)
    cap = _wrap(d, caption, fc, cw - GAP_CAP_MARK - (mb[2] - mb[0]))
    ch = _block(d, cap, fc, 1.42, 0, T_SOFT, draw=False)
    cap_top = int(H - M - ch)
    _block(d, cap, fc, 1.42, cap_top, T_SOFT)
    d.text((int(W - M - mb[2]), int(H - M - mb[3])), mark, font=fw, fill=NAVY)
    top, th = y + GAP_HEAD_PLOT, cap_top - GAP_PLOT_CAP - (y + GAP_HEAD_PLOT)
    fw_in, fh_in = cw / DPI, th / DPI
    tmp = out + ".tmp.png"
    for _ in range(6):
        fig = plt.figure(figsize=(fw_in, fh_in), dpi=DPI)
        plot_fn(fig)
        fig.savefig(tmp, dpi=DPI, facecolor="white", bbox_inches="tight", pad_inches=0.05); plt.close(fig)
        im = Image.open(tmp).convert("RGB"); b = _ink(im)
        iw, ih = b[2] - b[0], b[3] - b[1]
        if abs(iw - cw) <= 2 and 0 <= th - ih <= 8:
            break
        fw_in += (cw - iw) / DPI; fh_in += (th - 3 - ih) / DPI
    b = (b[0], b[1], min(b[2], b[0] + cw), b[3])
    canvas.paste(im.crop(b), (M, top)); os.remove(tmp)
    canvas.save(out, dpi=(DPI, DPI))
    verify(out, top, ih, cap_top)

def verify(out, top, ih, cap_top):
    b = _ink(Image.open(out))
    assert b[0] == M and b[1] == M and b[3] == H - M and b[2] <= W - M, ("margins", b)
    assert 0 <= cap_top - (top + ih) - GAP_PLOT_CAP <= 8, ("plot to caption gap", cap_top - top - ih)

def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)

HERE = os.path.dirname(os.path.abspath(__file__))
# ---- end house style -------------------------------------------------------
import json
READ = "Read more: movingfrontiers.substack.com/china-shock"
SRC = "Source: CEPII BACI (HS six-digit products)."
REDS = ["#F6D9D3", "#EBAA9F", "#DE7566", RED]
NAVS = ["#D3D8E8", "#9BA6CC", "#5568A6", NAVY]
BINS = [5, 10, 20, 30]
BINLAB = ["under 5", "5 to 10", "10 to 20", "20 to 30", "over 30"]
RED5 = ["#FBEDEA", "#F3C6BE", "#E79585", "#D85F4C", "#A82C1C"]
NAV5 = ["#ECEFF6", "#C2C9E0", "#8D9AC6", "#4F62A3", NAVY]
NODATA, CHINA = "#E3E3E3", "#8A8A8A"

def rows(name):
    with open(os.path.join(HERE, name + ".csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))

def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")

def lab(ax, x, y, text, col, ha="left", va="center", bold=True, size=None, **kw):
    return ax.text(x, y, text, color=col, fontfamily=CALIBRI, fontweight="bold" if bold else "normal",
                   fontsize=size or S_VALUE, ha=ha, va=va, linespacing=1.05, **kw)

def line(ax, x, y, col, lw=5.5, ms=13, label=None, dy=0, size=None):
    ax.plot(x, y, color=col, lw=lw, solid_capstyle="round", zorder=3)
    ax.plot(x[-1], y[-1], "o", color=col, ms=ms, zorder=6, clip_on=False)
    if label is not None:
        ax.annotate(label, (x[-1], y[-1]), xytext=(14, dy), textcoords="offset points", color=col,
                    fontfamily=CALIBRI, fontweight="bold", fontsize=size or S_VALUE, va="center", annotation_clip=False)

# ---- Robinson projection and a plain world map from Natural Earth (1:110m) --------------------
_RX = [1, .9986, .9954, .99, .9822, .973, .96, .9427, .9216, .8962, .8679, .835, .7986, .7597, .7186, .6732, .6213, .5722, .5322]
_RY = [0, .062, .124, .186, .248, .31, .372, .434, .4958, .5571, .6176, .6769, .7346, .7903, .8435, .8936, .9394, .9761, 1]
def robinson(lon, lat):
    lon, lat = np.asarray(lon, float), np.asarray(lat, float)
    a = np.abs(lat); k = np.arange(0, 91, 5)
    return 0.8487 * np.interp(a, k, _RX) * np.radians(lon), 1.3523 * np.interp(a, k, _RY) * np.sign(lat)

FIX = {"SOL": "SOM", "CYN": "CYP", "KOS": "XKX", "SDS": "SSD", "PSX": "PSE", "TWN": "CHN"}
def world():
    with open(os.path.join(HERE, "ne110.geojson"), encoding="utf-8") as f:
        g = json.load(f)
    out = []
    for ft in g["features"]:
        iso = ft["properties"]["ADM0_A3"]; iso = FIX.get(iso, iso)
        if iso == "ATA":
            continue
        geom = ft["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for p in polys:
            xy = np.array(p[0]); out.append((iso, np.column_stack(robinson(xy[:, 0], xy[:, 1]))))
    return out

def draw_map(ax, shapes, colour):
    from matplotlib.patches import Polygon
    for iso, xy in shapes:
        c = CHINA if iso == "CHN" else colour(iso)
        ax.add_patch(Polygon(xy, closed=True, fc=c, ec="white", lw=0.5))
    ax.set_xlim(-2.45, 2.72); ax.set_ylim(-1.05, 1.34); ax.set_aspect("equal"); ax.axis("off")

def binof(v):
    return sum(v >= b for b in BINS)

def swatches(ax, cols, labels, x0, y, dx, w=0.035, h=0.5, size=None):
    from matplotlib.patches import Rectangle
    for i, (c, t) in enumerate(zip(cols, labels)):
        ax.add_patch(Rectangle((x0 + i * dx, y - h / 2), w, h, fc=c, ec="none", transform=ax.transAxes, clip_on=False))
        ax.text(x0 + i * dx + w + 0.008, y, t, transform=ax.transAxes, va="center", ha="left", color=LABEL,
                fontfamily=CALIBRI, fontsize=size or S_LABEL)

S1, S2 = (2001, 2008), (2018, 2024)          # Shock 1.0 and Shock 2.0 (dating follows the Federal Reserve note of May 2026)
def bands(ax, end=None, labels=True, ytxt=0.965, size=None):
    for (a, b), t in ((S1, "Shock 1.0"), ((S2[0], end or S2[1]), "Shock 2.0")):
        ax.axvspan(a, b, color=BAND, zorder=0, lw=0)
        if labels:
            ax.text((a + b) / 2, ytxt, t, transform=ax.get_xaxis_transform(), ha="center", va="top", color=GREY_TXT,
                    fontfamily=CALIBRI, fontweight="bold", fontsize=size or S_TICK * 0.82, zorder=5)

def yname(ax, y, text, **kw):
    ax.text(-0.03, y, text, transform=ax.get_yaxis_transform(), ha="right", va="center", color=LABEL, fontfamily=CALIBRI, fontsize=kw.get("size", S_LABEL))

def ends(ax, x, items, gap, size=None, fmt="{:.0f}", dx=14):
    """End-of-line labels that do not collide: items = [(value, colour, text)]."""
    items = sorted(items, key=lambda e: e[0]); pos = [e[0] for e in items]
    for k in range(1, len(pos)):
        pos[k] = max(pos[k], pos[k - 1] + gap)
    for (v, col, text), p in zip(items, pos):
        ax.annotate(text, (x, p), xytext=(dx, 0), textcoords="offset points", color=col, fontfamily=CALIBRI, fontweight="bold",
                    fontsize=size or S_VALUE, va="center", annotation_clip=False)
NAME, DATA = "chart-9-biggest-gains", "chart-9-biggest-gains"
# The ten largest gains in China's world export share in each shock, among HS six-digit products (1992 nomenclature)
# with world trade above $20 billion in the end year. Shock 1.0: 2001 to 2008. Shock 2.0: 2018 to 2024.
D = rows(DATA)
def panel(ax, s, head, col):
    style_axes(ax); d = [r for r in D if r["shock"] == s]
    for y, r in enumerate(d):
        a, b = num(r["start"]), num(r["end"])
        ax.plot([a, b], [y, y], color=col, lw=9, solid_capstyle="butt", zorder=2, alpha=0.35)
        ax.plot(a, y, "o", clip_on=False, ms=12, mfc="white", mec=GREY_TXT, mew=2.4, zorder=4); ax.plot(b, y, "o", clip_on=False, ms=13.5, color=col, zorder=5)
        lab(ax, b + 3, y, f"{b:.0f}", col); yname(ax, y, r["product"], size=S_TICK)
    ax.set_xlim(0, 88); ax.set_xticks([0, 25, 50, 75]); ax.set_ylim(len(d) - 0.4, -1.5); lab(ax, 0, -1.05, head, INK, size=S_LABEL)
def plot(fig):
    panel(fig.add_axes([0.36, 0.55, 0.6, 0.44]), "Shock 1.0", "Shock 1.0: 2001 to 2008", NAVY); panel(fig.add_axes([0.36, 0.04, 0.6, 0.44]), "Shock 2.0", "Shock 2.0: 2018 to 2024", RED)
compose(plot, "From gadgets to heavy industry", "China's share of world exports at the start and end of each shock, percent",
        SRC + "\nNote: The ten largest gains among products with world trade above $20 billion.\n" + READ, os.path.join(HERE, NAME + ".png"))
