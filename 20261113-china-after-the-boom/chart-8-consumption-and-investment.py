# Chart 8: household consumption and investment shares of GDP
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
NAME = "chart-8-consumption-and-investment"
# Percent of GDP. World Bank WDI: household final consumption (NE.CON.PRVT.ZS) and
# gross capital formation (NE.GDI.TOTL.ZS), China, 1980-2024.
CO = {1980: 50.85, 1981: 53.14, 1982: 53.26, 1983: 53.39, 1984: 50.59, 1985: 50.76, 1986: 50.92, 1987: 49.59, 1988: 49.53, 1989: 51.01, 1990: 49.9, 1991: 47.82, 1992: 45.2, 1993: 43.95, 1994: 44.07, 1995: 45.76, 1996: 46.89, 1997: 45.94, 1998: 45.53, 1999: 46.23, 2000: 46.75, 2001: 45.57, 2002: 44.98, 2003: 42.81, 2004: 40.75, 2005: 39.81, 2006: 38.0, 2007: 36.62, 2008: 35.54, 2009: 35.58, 2010: 34.6, 2011: 35.25, 2012: 35.71, 2013: 36.13, 2014: 36.99, 2015: 38.06, 2016: 39.16, 2017: 38.95, 2018: 38.94, 2019: 39.35, 2020: 38.17, 2021: 38.37, 2022: 37.78, 2023: 39.57, 2024: 39.97}
IV = {1980: 34.54, 1981: 32.89, 1982: 31.92, 1983: 31.86, 1984: 34.31, 1985: 38.99, 1986: 37.66, 1987: 37.26, 1988: 39.01, 1989: 37.14, 1990: 34.09, 1991: 35.54, 1992: 39.31, 1993: 43.48, 1994: 40.28, 1995: 39.09, 1996: 37.78, 1997: 35.74, 1998: 34.99, 1999: 34.23, 2000: 33.63, 2001: 35.52, 2002: 36.07, 2003: 39.43, 2004: 41.63, 2005: 40.18, 2006: 39.69, 2007: 40.22, 2008: 41.96, 2009: 44.93, 2010: 46.1, 2011: 46.27, 2012: 45.82, 2013: 45.92, 2014: 45.31, 2015: 42.73, 2016: 42.14, 2017: 42.55, 2018: 43.31, 2019: 42.67, 2020: 42.57, 2021: 42.68, 2022: 42.36, 2023: 41.13, 2024: 40.48}

def end_label(ax, x, y, text, col, dy=0, dx=0.6):
    ax.text(x + dx, y + dy, text, color=col, fontfamily=CALIBRI, fontweight="bold",
            fontsize=S_VALUE, va="center", ha="left", linespacing=1.05)

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    for d, col, name in [(CO, NAVY, "Household\nconsumption"), (IV, RED, "Investment")]:
        x = sorted(d); y = [d[k] for k in x]
        ax.plot(x, y, color=col, lw=5.5, solid_capstyle="round", zorder=3)
        ax.plot(x[-1], y[-1], "o", color=col, ms=13, zorder=4)
        end_label(ax, x[-1], y[-1], f"{name}\n{y[-1]:.1f}", col, dy=(2.2 if col == RED else -2.6))
    ax.set_xlim(1979, 2033); ax.set_ylim(25, 60)
    ax.set_xticks(range(1980, 2021, 10)); ax.set_yticks(range(25, 61, 5))

compose(plot, "Investment still rivals consumption",
        "China's household consumption and investment, percent of GDP",
        "Source: World Bank, World Development Indicators.\nNote: Investment is gross capital formation.\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
write_csv(os.path.join(HERE, NAME + ".csv"), ["year", "household consumption (% GDP)", "investment (% GDP)"],
          [[y, CO.get(y), IV.get(y)] for y in sorted(CO)])
