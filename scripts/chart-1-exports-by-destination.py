# Chart 1: China's exports to its three largest markets
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
NAME = "chart-1-exports-by-destination"
# US$ billion, China customs. Calendar years, then the 12 months to October 2026.
# The last point = 2025 total + (Jan-Oct 2026 minus Jan-Oct 2025), where Jan-Oct 2026 is
# Jan-Oct 2025 scaled by the reported growth rate (ASEAN 30.5%, EU 17.2%, US 12.1%).
X = [2020, 2021, 2022, 2023, 2024, 2025, 2025 + 10 / 12]
XL = ["2020", "2021", "2022", "2023", "2024", "2025", "12m to\nOct 2026"]
JO25 = {"ASEAN": 705.863 / 1.305, "EU": 540.020 / 1.172, "US": 394.603 / 1.121}
G26 = {"ASEAN": 0.305, "EU": 0.172, "US": 0.121}
D = {"ASEAN": [383.7, 483.7, 567.3, 523.7, 586.5, 665.2],
     "EU": [391.0, 518.3, 561.9, 501.2, 516.5, 559.9],
     "US": [451.8, 576.1, 581.8, 500.3, 524.7, 420.05]}
for k in D:
    D[k].append(D[k][-1] + JO25[k] * G26[k])
COL = {"ASEAN": NAVY, "EU": GOLD, "US": RED}

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    for k, v in D.items():
        ax.plot(X, v, color=COL[k], lw=5.5, solid_capstyle="round", zorder=3)
        ax.plot(X[-1], v[-1], "o", color=COL[k], ms=13, zorder=4)
        ax.text(X[-1] + 0.12, v[-1], f"{k}\n{v[-1]:,.0f}", color=COL[k], fontfamily=CALIBRI,
                fontweight="bold", fontsize=S_VALUE, va="center", ha="left", linespacing=1.05)
    ax.set_xlim(2019.8, 2027.0); ax.set_ylim(300, 880)
    ax.set_xticks(X); ax.set_xticklabels(XL)
    ax.set_yticks(range(300, 900, 100))

compose(plot, "The US is now China's third market",
        "China's goods exports by destination, US$ billion",
        "Source: General Administration of Customs of China, preliminary release of 10 November 2026.\n"
        "Note: Calendar years, then the 12 months to October 2026. The final point adds the reported "
        "January to October 2026 growth (ASEAN 30.5 percent, EU 17.2 percent, US 12.1 percent) "
        "to the 2025 total. EU is the 27 members.\n"
        "Read more: movingfrontiers.substack.com",
        os.path.join(HERE, NAME + ".png"),
        expl="Sales to ASEAN have more than doubled since 2020. Sales to the US are back where they were.")
write_csv(os.path.join(HERE, NAME + ".csv"), ["period"] + list(D),
          [[XL[i].replace("\n", " ")] + [round(D[k][i], 1) for k in D] for i in range(len(X))])
