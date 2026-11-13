# Chart 13: technology content of manufactured exports
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
NAME = "chart-13-technology-content-of-exports"
# Medium- and high-tech exports, percent of manufactured exports. World Bank WDI (UNIDO), TX.MNF.TECH.ZS.UN.
MH = {'CHN': {1990: 28.4, 1991: 28.4, 1992: 28.4, 1993: 29.1, 1994: 30.8, 1995: 35.2, 1996: 36.5, 1997: 37.0, 1998: 39.8, 1999: 42.2, 2000: 45.3, 2001: 47.2, 2002: 49.8, 2003: 53.7, 2004: 56.6, 2005: 57.5, 2006: 57.8, 2007: 58.2, 2008: 57.9, 2009: 59.8, 2010: 60.5, 2011: 58.9, 2012: 58.4, 2013: 58.3, 2014: 57.3, 2015: 58.7, 2016: 59.1, 2017: 59.9, 2018: 60.5, 2019: 60.2, 2020: 61.3, 2021: 62.1, 2022: 60.4, 2023: 61.6, 2024: 63.3}, 'JPN': {1990: 83.1, 1991: 83.3, 1992: 83.8, 1993: 84.3, 1994: 84.9, 1995: 84.2, 1996: 84.2, 1997: 84.0, 1998: 84.2, 1999: 84.3, 2000: 85.3, 2001: 84.5, 2002: 84.2, 2003: 84.2, 2004: 83.7, 2005: 82.3, 2006: 82.2, 2007: 81.4, 2008: 79.6, 2009: 78.7, 2010: 79.7, 2011: 78.8, 2012: 79.5, 2013: 78.0, 2014: 78.4, 2015: 79.8, 2016: 81.3, 2017: 81.0, 2018: 80.6, 2019: 80.5, 2020: 81.4, 2021: 79.8, 2022: 78.4, 2023: 79.9, 2024: 80.9}, 'KOR': {1990: 51.1, 1991: 54.4, 1992: 56.3, 1993: 59.2, 1994: 64.4, 1995: 68.7, 1996: 68.9, 1997: 67.6, 1998: 67.0, 1999: 69.4, 2000: 70.4, 2001: 70.0, 2002: 73.2, 2003: 74.8, 2004: 75.9, 2005: 75.3, 2006: 75.1, 2007: 75.1, 2008: 72.6, 2009: 75.8, 2010: 75.8, 2011: 71.8, 2012: 70.6, 2013: 72.3, 2014: 72.4, 2015: 76.1, 2016: 75.9, 2017: 75.5, 2018: 74.2, 2019: 73.8, 2020: 77.6, 2021: 75.8, 2022: 71.8, 2023: 72.6, 2024: 75.7}, 'USA': {1990: 72.4, 1991: 72.9, 1992: 73.0, 1993: 73.2, 1994: 73.2, 1995: 72.3, 1996: 73.5, 1997: 74.6, 1998: 75.7, 1999: 76.0, 2000: 75.5, 2001: 75.3, 2002: 74.9, 2003: 74.2, 2004: 71.6, 2005: 70.3, 2006: 72.2, 2007: 71.5, 2008: 68.9, 2009: 66.4, 2010: 64.7, 2011: 62.1, 2012: 62.5, 2013: 61.7, 2014: 62.3, 2015: 65.2, 2016: 65.7, 2017: 63.5, 2018: 62.2, 2019: 63.5, 2020: 65.0, 2021: 62.5, 2022: 59.5, 2023: 62.3, 2024: 62.4}}
SER = [("JPN", "Japan", NAVY, 0), ("KOR", "Korea", SKY, 0), ("CHN", "China", RED, 2.2), ("USA", "United States", GOLD, -2.2)]

def end_label(ax, x, y, text, col, dy=0, dx=0.6):
    ax.text(x + dx, y + dy, text, color=col, fontfamily=CALIBRI, fontweight="bold",
            fontsize=S_VALUE, va="center", ha="left", linespacing=1.05)

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    for iso, name, col, dy in SER:
        x = sorted(MH[iso]); y = [MH[iso][k] for k in x]
        ax.plot(x, y, color=col, lw=5.5, solid_capstyle="round", zorder=3)
        ax.plot(x[-1], y[-1], "o", color=col, ms=13, zorder=4)
        end_label(ax, x[-1], y[-1], f"{name} {y[-1]:.0f}", col, dy=dy)
    ax.set_xlim(1989, 2035.5); ax.set_ylim(20, 92)
    ax.set_xticks(range(1990, 2021, 10)); ax.set_yticks(range(20, 91, 10))

compose(plot, "China's exports climbed the tech ladder",
        "Medium- and high-tech goods, percent of manufactured exports",
        "Source: World Bank, World Development Indicators (UNIDO).\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
write_csv(os.path.join(HERE, NAME + ".csv"), ["year"] + [s[1] for s in SER],
          [[y] + [MH[s[0]].get(y) for s in SER] for y in sorted(MH["CHN"])])
