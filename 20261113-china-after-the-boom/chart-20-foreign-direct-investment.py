# Chart 20: foreign direct investment inflows, China and Japan
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
NAME = "chart-20-foreign-direct-investment"
# Foreign direct investment, net inflows, percent of GDP. World Bank WDI, BX.KLT.DINV.WD.GD.ZS.
FD = {'CHN': {1979: 0.0, 1980: 0.03, 1981: 0.14, 1982: 0.21, 1983: 0.28, 1984: 0.48, 1985: 0.54, 1986: 0.62, 1987: 0.85, 1988: 1.02, 1989: 0.97, 1990: 0.96, 1991: 1.14, 1992: 2.6, 1993: 6.16, 1994: 5.96, 1995: 4.86, 1996: 4.63, 1997: 4.7, 1998: 4.4, 1999: 3.72, 2000: 3.44, 2001: 3.47, 2002: 3.56, 2003: 3.44, 2004: 3.43, 2005: 4.49, 2006: 4.44, 2007: 4.34, 2008: 3.68, 2009: 2.53, 2010: 3.94, 2011: 3.65, 2012: 2.78, 2013: 2.99, 2014: 2.51, 2015: 2.15, 2016: 1.53, 2017: 1.32, 2018: 1.66, 2019: 1.29, 2020: 1.69, 2021: 1.89, 2022: 1.04, 2023: 0.28, 2024: 0.23, 2025: 0.41}, 'JPN': {1970: 0.04, 1971: 0.08, 1972: 0.05, 1973: -0.01, 1974: 0.04, 1975: 0.04, 1976: 0.02, 1977: 0.0, 1978: 0.0, 1979: 0.02, 1980: 0.02, 1981: 0.01, 1982: 0.04, 1983: 0.03, 1984: -0.0, 1985: 0.04, 1986: 0.01, 1987: 0.04, 1988: -0.02, 1989: -0.03, 1990: 0.06, 1991: 0.03, 1992: 0.07, 1993: 0.0, 1994: 0.02, 1995: 0.0, 1996: -0.0, 1997: 0.05, 1998: 0.06, 1999: 0.32, 2000: 0.21, 2001: 0.11, 2002: 0.27, 2003: 0.19, 2004: 0.15, 2005: 0.11, 2006: -0.05, 2007: 0.47, 2008: 0.48, 2009: 0.23, 2010: 0.13, 2011: -0.01, 2012: 0.01, 2013: 0.2, 2014: 0.4, 2015: 0.12, 2016: 0.8, 2017: 0.37, 2018: 0.49, 2019: 0.76, 2020: 1.21, 2021: 0.67, 2022: 1.08, 2023: 0.46, 2024: 0.45, 2025: 1.03}}

def end_label(ax, x, y, text, col, dy=0, dx=0.6):
    ax.text(x + dx, y + dy, text, color=col, fontfamily=CALIBRI, fontweight="bold",
            fontsize=S_VALUE, va="center", ha="left", linespacing=1.05)

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    for iso, name, col, dy in [("CHN", "China", RED, 0.25), ("JPN", "Japan", NAVY, -0.15)]:
        x = sorted(FD[iso]); y = [FD[iso][k] for k in x]
        ax.plot(x, y, color=col, lw=5.5, solid_capstyle="round", zorder=3)
    ax.text(1994.5, 6.35, "China", color=RED, fontfamily=CALIBRI, fontweight="bold", fontsize=S_VALUE, ha="center", va="bottom")
    ax.text(1975, 0.3, "Japan", color=NAVY, fontfamily=CALIBRI, fontweight="bold", fontsize=S_VALUE, ha="center", va="bottom")
    ax.set_xlim(1969, 2026.5); ax.set_ylim(-0.3, 7.2)
    zero_line(ax)
    ax.set_xticks(range(1970, 2021, 10)); ax.set_yticks(range(0, 8, 1))

compose(plot, "China drew far more foreign investment",
        "Foreign direct investment, net inflows, percent of GDP",
        "Source: World Bank, World Development Indicators.\nNote: China's series starts in 1979.\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
write_csv(os.path.join(HERE, NAME + ".csv"), ["year", "China", "Japan"],
          [[y, FD["CHN"].get(y), FD["JPN"].get(y)] for y in range(1970, 2026)])
