# Chart 19: income relative to the US, China and Japan
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
NAME = "chart-19-income-relative-to-us"
# GDP per capita, 2011 international dollars. Maddison Project Database 2023 (via Our World in Data).
MD = {'CHN': {1950: 799.0, 1951: 950.0, 1952: 1047.0, 1953: 1157.0, 1954: 1049.0, 1955: 1119.0, 1956: 1189.0, 1957: 1195.0, 1958: 1173.0, 1959: 1117.0, 1960: 1057.0, 1961: 874.0, 1962: 926.0, 1963: 1034.0, 1964: 1152.0, 1965: 1253.0, 1966: 1261.0, 1967: 1237.0, 1968: 1178.0, 1969: 1264.0, 1970: 1398.0, 1971: 1446.0, 1972: 1431.0, 1973: 1513.0, 1974: 1519.0, 1975: 1594.0, 1976: 1519.0, 1977: 1583.0, 1978: 1744.0, 1979: 1859.0, 1980: 1930.0, 1981: 1962.0, 1982: 2128.0, 1983: 2227.0, 1984: 2444.0, 1985: 2619.0, 1986: 2748.0, 1987: 2931.0, 1988: 3045.0, 1989: 3022.0, 1990: 2982.0, 1991: 3051.3, 1992: 3227.7, 1993: 3506.5, 1994: 3730.2, 1995: 3999.7, 1996: 4219.6, 1997: 4310.8, 1998: 4309.8, 1999: 4466.7, 2000: 4730.4, 2001: 4995.1, 2002: 5343.1, 2003: 5649.5, 2004: 6067.6, 2005: 6626.6, 2006: 7271.0, 2007: 7895.7, 2008: 8190.1, 2009: 8734.0, 2010: 9658.4, 2011: 10221.0, 2012: 10946.8, 2013: 11731.3, 2014: 12515.2, 2015: 13325.4, 2016: 14139.0, 2017: 15030.4, 2018: 15977.0, 2019: 16879.5, 2020: 17226.0, 2021: 18666.6, 2022: 19238.2}, 'JPN': {1950: 3062.0, 1951: 3389.0, 1952: 3724.0, 1953: 3944.0, 1954: 4116.0, 1955: 4417.0, 1956: 4699.0, 1957: 4999.0, 1958: 5243.0, 1959: 5665.0, 1960: 6354.0, 1961: 7055.0, 1962: 7614.0, 1963: 8176.0, 1964: 9035.0, 1965: 9459.0, 1966: 10370.0, 1967: 11400.0, 1968: 12725.0, 1969: 14145.0, 1970: 15484.0, 1971: 16004.0, 1972: 17110.0, 1973: 18226.0, 1974: 17765.0, 1975: 18082.0, 1976: 18600.0, 1977: 19230.0, 1978: 20060.0, 1979: 20982.0, 1980: 21404.0, 1981: 21924.0, 1982: 22440.0, 1983: 22805.0, 1984: 23548.0, 1985: 24437.0, 1986: 24992.0, 1987: 25904.0, 1988: 27393.0, 1989: 28601.0, 1990: 29949.0, 1991: 30837.4, 1992: 30977.8, 1993: 30920.7, 1994: 31135.4, 1995: 31887.3, 1996: 32784.2, 1997: 33038.3, 1998: 32558.2, 1999: 32394.5, 2000: 33210.8, 2001: 33246.4, 2002: 33195.4, 2003: 33619.9, 2004: 34313.6, 2005: 34857.8, 2006: 35333.1, 2007: 35892.7, 2008: 35496.2, 2009: 33590.0, 2010: 35011.4, 2011: 34979.0, 2012: 35537.4, 2013: 36312.3, 2014: 36440.2, 2015: 37053.2, 2016: 37384.6, 2017: 38079.0, 2018: 38403.7, 2019: 38332.9, 2020: 36826.6, 2021: 37678.3, 2022: 38268.8}, 'USA': {1950: 15240.0, 1951: 16125.0, 1952: 16444.0, 1953: 16917.0, 1954: 16512.0, 1955: 17370.0, 1956: 17397.0, 1957: 17406.0, 1958: 16946.0, 1959: 17900.0, 1960: 18057.0, 1961: 18175.0, 1962: 18976.0, 1963: 19514.0, 1964: 20360.0, 1965: 21390.0, 1966: 22529.0, 1967: 22842.0, 1968: 23691.0, 1969: 24195.0, 1970: 23958.0, 1971: 24394.0, 1972: 25414.0, 1973: 26602.0, 1974: 26286.0, 1975: 25956.0, 1976: 27058.0, 1977: 28001.0, 1978: 29286.0, 1979: 29949.0, 1980: 29611.0, 1981: 30056.0, 1982: 29210.0, 1983: 30158.0, 1984: 32076.0, 1985: 33023.0, 1986: 33850.0, 1987: 34730.0, 1988: 35863.0, 1989: 36756.0, 1990: 36982.0, 1991: 36464.0, 1992: 37240.3, 1993: 37761.5, 1994: 38807.3, 1995: 39390.6, 1996: 40412.8, 1997: 41722.7, 1998: 43072.8, 1999: 44575.8, 2000: 45886.5, 2001: 45878.0, 2002: 46266.3, 2003: 47158.0, 2004: 48492.7, 2005: 49654.8, 2006: 50489.9, 2007: 50901.7, 2008: 50275.7, 2009: 48452.9, 2010: 49266.9, 2011: 49675.0, 2012: 50436.4, 2013: 51010.8, 2014: 51796.6, 2015: 52808.2, 2016: 53301.0, 2017: 54152.4, 2018: 55454.7, 2019: 56469.3, 2020: 54379.2, 2021: 57522.7, 2022: 58487.5}}

def end_label(ax, x, y, text, col, dy=0, dx=0.6):
    ax.text(x + dx, y + dy, text, color=col, fontfamily=CALIBRI, fontweight="bold",
            fontsize=S_VALUE, va="center", ha="left", linespacing=1.05)

def rel(iso):
    yrs = sorted(MD[iso]); return yrs, [100 * MD[iso][y] / MD["USA"][y] for y in yrs]

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    for iso, name, col in [("JPN", "Japan", NAVY), ("CHN", "China", RED)]:
        x, y = rel(iso)
        ax.plot(x, y, color=col, lw=5.5, solid_capstyle="round", zorder=3)
        ax.plot(x[-1], y[-1], "o", color=col, ms=13, zorder=4)
        end_label(ax, x[-1], y[-1], f"{name} {y[-1]:.0f}", col, dx=1.6)
    x, y = rel("JPN"); i = int(np.argmax(y))
    ax.plot(x[i], y[i], "o", color=NAVY, ms=13, zorder=4)
    ax.text(x[i], y[i] + 3, f"Japan's peak, {x[i]}: {y[i]:.0f}", color=NAVY, fontfamily=CALIBRI,
            fontweight="bold", fontsize=S_VALUE, ha="center", va="bottom")
    j = min(range(len(x)), key=lambda k: abs(y[k] - rel("CHN")[1][-1]))
    ax.plot(x[j], y[j], "o", color=NAVY, ms=13, zorder=4, mfc="white", mew=3.5)
    ax.text(x[j] + 1.2, y[j] - 1, f"Japan at China's\n2022 level, {x[j]}", color=NAVY, fontfamily=CALIBRI,
            fontweight="bold", fontsize=S_VALUE, ha="left", va="top", linespacing=1.05)
    ax.set_xlim(1948, 2037); ax.set_ylim(0, 100)
    ax.set_xticks(range(1950, 2021, 10)); ax.set_yticks(range(0, 101, 20))

compose(plot, "China slows at a third of US income",
        "GDP per capita relative to the United States, percent",
        "Source: Maddison Project Database 2023, via Our World in Data.\nNote: Purchasing power parity, 2011 international dollars. The series ends in 2022.\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
rows = []
for iso in ["JPN", "CHN"]:
    x, y = rel(iso); rows += [[yy, iso, MD[iso][yy], round(v, 2)] for yy, v in zip(x, y)]
write_csv(os.path.join(HERE, NAME + ".csv"), ["year", "economy", "GDP per capita (2011 int$)", "relative to US (%)"], rows)
