# Chart 21: share of world merchandise exports
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
NAME = "chart-21-share-of-world-exports"
# Merchandise exports, current US$ billion. World Bank WDI (WTO), TX.VAL.MRCH.CD.WT.
XS = {'CHN': {1960: 2.57, 1961: 1.94, 1962: 1.91, 1963: 2.03, 1964: 2.25, 1965: 2.56, 1966: 2.68, 1967: 2.39, 1968: 2.34, 1969: 2.43, 1970: 2.31, 1971: 2.78, 1972: 3.69, 1973: 5.88, 1974: 7.11, 1975: 7.69, 1976: 6.94, 1977: 7.52, 1978: 9.96, 1979: 13.61, 1980: 18.1, 1981: 22.01, 1982: 22.32, 1983: 22.23, 1984: 26.14, 1985: 27.35, 1986: 30.94, 1987: 39.44, 1988: 47.52, 1989: 52.54, 1990: 62.09, 1991: 71.91, 1992: 84.94, 1993: 91.74, 1994: 121.01, 1995: 148.78, 1996: 151.05, 1997: 182.79, 1998: 183.71, 1999: 194.93, 2000: 249.2, 2001: 266.1, 2002: 325.6, 2003: 438.23, 2004: 593.33, 2005: 761.95, 2006: 968.98, 2007: 1220.46, 2008: 1430.69, 2009: 1201.61, 2010: 1577.75, 2011: 1898.38, 2012: 2048.71, 2013: 2209.01, 2014: 2342.29, 2015: 2273.47, 2016: 2097.63, 2017: 2263.35, 2018: 2486.7, 2019: 2499.46, 2020: 2589.95, 2021: 3316.02, 2022: 3544.43, 2023: 3379.04, 2024: 3575.8, 2025: 3771.84}, 'JPN': {1960: 4.05, 1961: 4.24, 1962: 4.92, 1963: 5.45, 1964: 6.67, 1965: 8.45, 1966: 9.78, 1967: 10.44, 1968: 12.97, 1969: 15.99, 1970: 19.32, 1971: 24.0, 1972: 29.09, 1973: 37.02, 1974: 55.47, 1975: 55.82, 1976: 67.3, 1977: 81.08, 1978: 98.21, 1979: 102.3, 1980: 130.44, 1981: 151.5, 1982: 138.38, 1983: 146.97, 1984: 169.7, 1985: 177.16, 1986: 210.76, 1987: 231.29, 1988: 264.86, 1989: 273.93, 1990: 287.58, 1991: 314.79, 1992: 339.88, 1993: 362.24, 1994: 397.0, 1995: 443.12, 1996: 410.9, 1997: 420.96, 1998: 387.93, 1999: 417.61, 2000: 479.25, 2001: 403.5, 2002: 416.73, 2003: 471.82, 2004: 565.67, 2005: 594.94, 2006: 646.73, 2007: 714.33, 2008: 781.41, 2009: 580.72, 2010: 769.77, 2011: 823.18, 2012: 798.57, 2013: 715.1, 2014: 690.2, 2015: 624.92, 2016: 645.05, 2017: 698.33, 2018: 738.14, 2019: 705.56, 2020: 641.32, 2021: 756.03, 2022: 746.82, 2023: 717.26, 2024: 707.01, 2025: 738.34}, 'USA': {1960: 19.63, 1961: 20.19, 1962: 20.97, 1963: 22.43, 1964: 25.69, 1965: 26.7, 1966: 29.38, 1967: 30.93, 1968: 34.06, 1969: 37.33, 1970: 43.23, 1971: 43.55, 1972: 49.2, 1973: 70.82, 1974: 99.44, 1975: 108.86, 1976: 116.79, 1977: 123.18, 1978: 145.85, 1979: 186.36, 1980: 225.57, 1981: 238.72, 1982: 216.44, 1983: 205.64, 1984: 223.98, 1985: 218.81, 1986: 227.16, 1987: 254.12, 1988: 322.43, 1989: 363.81, 1990: 393.59, 1991: 421.73, 1992: 448.16, 1993: 464.77, 1994: 512.63, 1995: 584.74, 1996: 625.07, 1997: 689.18, 1998: 682.14, 1999: 695.8, 2000: 781.92, 2001: 729.1, 2002: 693.1, 2003: 724.77, 2004: 814.88, 2005: 901.08, 2006: 1025.97, 2007: 1148.2, 2008: 1287.44, 2009: 1056.04, 2010: 1278.49, 2011: 1482.51, 2012: 1545.7, 2013: 1579.59, 2014: 1620.53, 2015: 1502.57, 2016: 1451.01, 2017: 1546.27, 2018: 1663.98, 2019: 1643.16, 2020: 1424.93, 2021: 1754.3, 2022: 2065.16, 2023: 2018.06, 2024: 2061.69, 2025: 2185.22}, 'DEU': {1960: 11.42, 1961: 12.65, 1962: 13.24, 1963: 14.58, 1964: 16.23, 1965: 17.91, 1966: 20.16, 1967: 21.76, 1968: 24.89, 1969: 28.85, 1970: 34.23, 1971: 38.84, 1972: 46.74, 1973: 67.56, 1974: 89.37, 1975: 90.18, 1976: 102.16, 1977: 118.07, 1978: 142.45, 1979: 171.8, 1980: 192.86, 1981: 176.05, 1982: 176.42, 1983: 169.42, 1984: 171.74, 1985: 183.93, 1986: 243.33, 1987: 294.37, 1988: 323.32, 1989: 341.23, 1990: 421.1, 1991: 402.84, 1992: 430.04, 1993: 380.1, 1994: 426.94, 1995: 523.46, 1996: 524.65, 1997: 512.89, 1998: 543.75, 1999: 543.54, 2000: 551.81, 2001: 571.64, 2002: 615.83, 2003: 751.56, 2004: 909.89, 2005: 970.91, 2006: 1108.11, 2007: 1321.21, 2008: 1446.17, 2009: 1120.04, 2010: 1258.92, 2011: 1473.98, 2012: 1401.11, 2013: 1445.07, 2014: 1494.21, 2015: 1326.21, 2016: 1334.36, 2017: 1448.19, 2018: 1560.54, 2019: 1489.41, 2020: 1382.53, 2021: 1627.38, 2022: 1676.47, 2023: 1702.28, 2024: 1676.41, 2025: 1764.19}, 'WLD': {1960: 122.83, 1961: 128.24, 1962: 133.94, 1963: 146.82, 1964: 165.03, 1965: 178.98, 1966: 195.9, 1967: 206.83, 1968: 229.95, 1969: 262.56, 1970: 301.92, 1971: 338.17, 1972: 400.22, 1973: 555.73, 1974: 815.28, 1975: 845.13, 1976: 956.96, 1977: 1086.12, 1978: 1259.04, 1979: 1604.78, 1980: 1973.52, 1981: 1952.17, 1982: 1808.58, 1983: 1759.7, 1984: 1876.14, 1985: 1896.18, 1986: 2067.47, 1987: 2436.84, 1988: 2795.26, 1989: 3033.53, 1990: 3463.21, 1991: 3547.83, 1992: 3804.6, 1993: 3810.07, 1994: 4343.82, 1995: 5183.46, 1996: 5433.65, 1997: 5629.04, 1998: 5528.03, 1999: 5748.94, 2000: 6485.09, 2001: 6225.45, 2002: 6531.46, 2003: 7627.88, 2004: 9268.0, 2005: 10576.56, 2006: 12203.9, 2007: 14113.06, 2008: 16273.25, 2009: 12648.87, 2010: 15381.26, 2011: 18432.02, 2012: 18605.84, 2013: 19055.46, 2014: 19104.31, 2015: 16646.11, 2016: 16128.62, 2017: 17825.25, 2018: 19643.74, 2019: 19101.9, 2020: 17734.59, 2021: 22400.02, 2022: 25037.93, 2023: 24020.26, 2024: 24622.13, 2025: 26386.78}}
SER = [("CHN", "China", RED), ("USA", "United States", GOLD), ("DEU", "Germany", SKY), ("JPN", "Japan", NAVY)]

def end_label(ax, x, y, text, col, dy=0, dx=0.6):
    ax.text(x + dx, y + dy, text, color=col, fontfamily=CALIBRI, fontweight="bold",
            fontsize=S_VALUE, va="center", ha="left", linespacing=1.05)

def share(iso):
    yrs = sorted(XS[iso]); return yrs, [100 * XS[iso][y] / XS["WLD"][y] for y in yrs]

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    DY = {"USA": 0.45, "DEU": -0.35}
    for iso, name, col in SER:
        x, y = share(iso)
        ax.plot(x, y, color=col, lw=5.5, solid_capstyle="round", zorder=3)
        ax.plot(x[-1], y[-1], "o", color=col, ms=13, zorder=4)
        end_label(ax, x[-1], y[-1], f"{name} {y[-1]:.0f}", col, dy=DY.get(iso, 0), dx=1.6)
    x, y = share("JPN"); i = int(np.argmax(y))
    ax.plot(x[i], y[i], "o", color=NAVY, ms=13, zorder=4)
    ax.plot([x[i], x[i]], [y[i] + 0.3, 15.0], color=NAVY, lw=2, zorder=2)
    ax.text(x[i], 15.2, f"Japan's peak\n{y[i]:.1f} in {x[i]}", color=NAVY, fontfamily=CALIBRI,
            fontweight="bold", fontsize=S_VALUE, ha="center", va="bottom", linespacing=1.05)
    ax.set_xlim(1958, 2041); ax.set_ylim(0, 18)
    ax.set_xticks(range(1960, 2021, 10)); ax.set_yticks(range(0, 19, 3))

compose(plot, "China's export share tops Japan's peak",
        "Share of world merchandise exports, percent",
        "Source: World Bank, World Development Indicators (World Trade Organization).\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
rows = []
for iso, name, col in SER:
    x, y = share(iso); rows += [[yy, name, round(v, 2)] for yy, v in zip(x, y)]
write_csv(os.path.join(HERE, NAME + ".csv"), ["year", "economy", "share of world merchandise exports (%)"], rows)
