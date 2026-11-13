# Chart 12: share of world manufacturing value added
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
NAME = "chart-12-share-of-world-manufacturing"
# Manufacturing value added, current US$ billion. World Bank WDI, NV.IND.MANF.CD.
# China from 2004, US to 2021 (latest in WDI).
MV = {'CHN': {2004: 625.2, 2005: 733.7, 2006: 893.1, 2007: 1149.7, 2008: 1475.7, 2009: 1611.9, 2010: 1924.3, 2011: 2421.4, 2012: 2690.1, 2013: 2935.4, 2014: 3184.2, 2015: 3202.5, 2016: 3153.1, 2017: 3460.3, 2018: 3868.5, 2019: 3823.4, 2020: 3836.2, 2021: 4845.6, 2022: 4758.8, 2023: 4570.2, 2024: 4652.7, 2025: 4822.7}, 'USA': {1997: 1379.9, 1998: 1429.6, 1999: 1488.9, 2000: 1549.4, 2001: 1472.9, 2002: 1470.3, 2003: 1525.6, 2004: 1609.5, 2005: 1692.9, 2006: 1794.7, 2007: 1848.3, 2008: 1804.4, 2009: 1693.8, 2010: 1791.7, 2011: 1863.7, 2012: 1927.3, 2013: 1987.2, 2014: 2045.6, 2015: 2123.2, 2016: 2098.3, 2017: 2192.9, 2018: 2330.1, 2019: 2364.3, 2020: 2238.5, 2021: 2497.1}, 'JPN': {1997: 1066.9, 1998: 942.0, 1999: 1033.3, 2000: 1118.2, 2001: 938.1, 2002: 874.0, 2003: 948.0, 2004: 1036.1, 2005: 1027.5, 2006: 983.0, 2007: 1005.7, 2008: 1098.7, 2009: 1017.0, 2010: 1213.2, 2011: 1235.9, 2012: 1249.8, 2013: 1011.3, 2014: 967.6, 2015: 910.2, 2016: 1023.5, 2017: 1014.9, 2018: 1047.9, 2019: 1052.0, 2020: 1026.6, 2021: 1028.3, 2022: 837.3, 2023: 854.5, 2024: 788.5}, 'DEU': {1997: 441.4, 1998: 451.5, 1999: 437.1, 2000: 399.0, 2001: 395.0, 2002: 409.5, 2003: 495.6, 2004: 564.5, 2005: 572.0, 2006: 619.6, 2007: 715.3, 2008: 752.4, 2009: 603.1, 2010: 673.6, 2011: 769.4, 2012: 721.0, 2013: 752.3, 2014: 797.3, 2015: 689.7, 2016: 722.0, 2017: 756.6, 2018: 803.2, 2019: 764.6, 2020: 730.2, 2021: 808.9, 2022: 769.7, 2023: 864.1, 2024: 843.7, 2025: 889.6}, 'WLD': {1997: 6145.6, 1998: 5970.2, 1999: 6094.4, 2000: 6251.7, 2001: 5853.8, 2002: 5919.4, 2003: 6570.4, 2004: 7343.7, 2005: 7845.6, 2006: 8491.0, 2007: 9557.2, 2008: 10339.7, 2009: 9447.1, 2010: 10698.8, 2011: 11978.4, 2012: 12224.1, 2013: 12449.4, 2014: 12899.4, 2015: 12420.2, 2016: 12491.0, 2017: 13344.1, 2018: 14304.0, 2019: 14180.0, 2020: 13742.9, 2021: 16155.9, 2022: 16159.7, 2023: 16366.9, 2024: 16622.5, 2025: 17601.1}}
SER = [("CHN", "China", RED), ("USA", "United States", GOLD), ("JPN", "Japan", NAVY), ("DEU", "Germany", SKY)]

def end_label(ax, x, y, text, col, dy=0, dx=0.6):
    ax.text(x + dx, y + dy, text, color=col, fontfamily=CALIBRI, fontweight="bold",
            fontsize=S_VALUE, va="center", ha="left", linespacing=1.05)

def share(iso):
    yrs = [y for y in sorted(MV[iso]) if y in MV["WLD"]]
    return yrs, [100 * MV[iso][y] / MV["WLD"][y] for y in yrs]

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    DY = {"JPN": -1.0, "DEU": 0.9}
    for iso, name, col in SER:
        x, y = share(iso)
        ax.plot(x, y, color=col, lw=5.5, solid_capstyle="round", zorder=3)
        ax.plot(x[-1], y[-1], "o", color=col, ms=13, zorder=4)
        end_label(ax, x[-1], y[-1], f"{name} {y[-1]:.0f}", col, dy=DY.get(iso, 0), dx=0.9)
    ax.set_xlim(1996, 2033.5); ax.set_ylim(0, 32)
    ax.set_xticks(range(2000, 2026, 5)); ax.set_yticks(range(0, 31, 5))

compose(plot, "China makes 27 percent of manufactures",
        "Share of world manufacturing value added, percent, current US dollars",
        "Source: World Bank, World Development Indicators.\nNote: China's series starts in 2004. The US series ends in 2021, the latest year in the source.\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
rows = []
for iso, name, col in SER:
    x, y = share(iso)
    rows += [[yy, name, round(v, 2)] for yy, v in zip(x, y)]
write_csv(os.path.join(HERE, NAME + ".csv"), ["year", "economy", "share of world manufacturing value added (%)"], rows)
