# Chart 15: scientific articles
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
NAME = "chart-15-scientific-output"
# Scientific and technical journal articles, thousands. World Bank WDI (US National Science Foundation),
# IP.JRN.ARTC.SC. Fractional counting by author country.
AR = {'CHN': {2000: 53.3, 2001: 70.7, 2002: 74.9, 2003: 87.6, 2004: 120.9, 2005: 165.3, 2006: 192.0, 2007: 213.0, 2008: 247.0, 2009: 284.5, 2010: 307.8, 2011: 321.0, 2012: 326.4, 2013: 351.5, 2014: 379.5, 2015: 401.1, 2016: 430.4, 2017: 464.2, 2018: 513.6, 2019: 608.6, 2020: 671.7, 2021: 756.2, 2022: 886.0, 2023: 932.7}, 'USA': {2000: 306.5, 2001: 306.7, 2002: 321.6, 2003: 332.5, 2004: 356.2, 2005: 385.0, 2006: 387.8, 2007: 390.2, 2008: 392.6, 2009: 397.8, 2010: 407.4, 2011: 420.4, 2012: 425.2, 2013: 427.4, 2014: 428.0, 2015: 429.3, 2016: 431.8, 2017: 435.4, 2018: 441.1, 2019: 442.7, 2020: 453.9, 2021: 471.4, 2022: 447.5, 2023: 430.8}, 'IND': {2000: 21.4, 2001: 22.5, 2002: 23.7, 2003: 26.1, 2004: 28.0, 2005: 32.1, 2006: 37.0, 2007: 41.3, 2008: 46.5, 2009: 51.9, 2010: 58.3, 2011: 69.1, 2012: 75.6, 2013: 80.2, 2014: 88.3, 2015: 94.8, 2016: 104.7, 2017: 115.0, 2018: 123.1, 2019: 128.6, 2020: 145.7, 2021: 173.1, 2022: 200.5, 2023: 228.2}, 'JPN': {2000: 96.6, 2001: 96.1, 2002: 98.7, 2003: 101.1, 2004: 103.6, 2005: 111.9, 2006: 112.7, 2007: 108.6, 2008: 106.6, 2009: 107.5, 2010: 107.2, 2011: 109.0, 2012: 107.5, 2013: 107.0, 2014: 103.4, 2015: 100.6, 2016: 101.2, 2017: 101.9, 2018: 102.0, 2019: 100.2, 2020: 100.4, 2021: 106.3, 2022: 102.4, 2023: 96.5}}
SER = [("CHN", "China", RED), ("USA", "United States", GOLD), ("IND", "India", SKY), ("JPN", "Japan", NAVY)]

def end_label(ax, x, y, text, col, dy=0, dx=0.6):
    ax.text(x + dx, y + dy, text, color=col, fontfamily=CALIBRI, fontweight="bold",
            fontsize=S_VALUE, va="center", ha="left", linespacing=1.05)

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    for iso, name, col in SER:
        x = sorted(AR[iso]); y = [AR[iso][k] for k in x]
        ax.plot(x, y, color=col, lw=5.5, solid_capstyle="round", zorder=3)
        ax.plot(x[-1], y[-1], "o", color=col, ms=13, zorder=4)
        end_label(ax, x[-1], y[-1], f"{name} {y[-1]:,.0f}", col, dx=0.5)
    ax.set_xlim(1999, 2033); ax.set_ylim(0, 1000)
    ax.set_xticks(range(2000, 2021, 5)); ax.set_yticks(range(0, 1001, 200))

compose(plot, "China out-publishes the US and Japan",
        "Scientific and technical journal articles, thousands",
        "Source: World Bank, World Development Indicators (US National Science Foundation).\nNote: Articles are counted fractionally by the country of each author.\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
write_csv(os.path.join(HERE, NAME + ".csv"), ["year"] + [s[1] for s in SER],
          [[y] + [AR[s[0]].get(y) for s in SER] for y in sorted(AR["CHN"])])
