# chart-2-global-current-accounts
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
NAME = "chart-2-global-current-accounts"
# Current account balances, percent of world GDP. IMF World Economic Outlook, October 2026 (BCA and NGDPD,
# DataMapper API); projections from 2026. Discrepancy is minus the sum of all recorded balances.
CA_YEARS = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031]
# Country groups (IMF codes); emerging and developing is every other economy in the WEO
# CHINA: CHN
# OTHER_EAST_ASIA: JPN KOR TWN SGP HKG
# GERMANY_NETHERLANDS: DEU NLD
# REST_OF_EUROPE: AUT BEL CYP EST FIN FRA GRC IRL ITA LVA LTU LUX MLT PRT SVK SVN ESP HRV CHE NOR SWE DNK ISL CZE POL HUN ROU BGR
# OIL_EXPORTERS: SAU ARE QAT KWT OMN BHR IRQ IRN LBY DZA KAZ AZE RUS NGA AGO BRN TKM
# OTHER_ADVANCED: GBR CAN AUS NZL ISR MAC AND SMR
# US: USA
CHINA = [0.06, 0.051, 0.101, 0.109, 0.155, 0.275, 0.444, 0.599, 0.65, 0.397, 0.354, 0.182, 0.284, 0.19, 0.294, 0.386, 0.248, 0.23, 0.028, 0.102, 0.26, 0.302, 0.393, 0.239, 0.41, 0.611, 0.674, 0.662, 0.673, 0.653, 0.64, 0.613]
OTHER_EAST_ASIA = [0.487, 0.378, 0.468, 0.558, 0.603, 0.517, 0.507, 0.562, 0.357, 0.443, 0.531, 0.349, 0.273, 0.289, 0.3, 0.504, 0.567, 0.537, 0.458, 0.431, 0.476, 0.533, 0.339, 0.384, 0.5, 0.572, 0.797, 0.764, 0.736, 0.664, 0.619, 0.531]
GERMANY_NETHERLANDS = [-0.081, 0.003, 0.132, 0.155, 0.387, 0.359, 0.437, 0.461, 0.376, 0.366, 0.37, 0.4, 0.417, 0.41, 0.454, 0.415, 0.483, 0.453, 0.487, 0.425, 0.35, 0.417, 0.238, 0.336, 0.33, 0.278, 0.284, 0.268, 0.251, 0.24, 0.231, 0.223]
REST_OF_EUROPE = [0.096, 0.113, 0.101, 0.089, 0.034, -0.075, -0.158, -0.335, -0.459, -0.146, -0.055, -0.08, 0.105, 0.295, 0.263, 0.271, 0.243, 0.222, 0.198, 0.149, 0.099, 0.301, 0.138, 0.243, 0.366, 0.259, 0.229, 0.23, 0.252, 0.251, 0.259, 0.258]
OIL_EXPORTERS = [0.392, 0.241, 0.169, 0.235, 0.404, 0.733, 0.834, 0.668, 0.833, 0.243, 0.475, 0.803, 0.781, 0.603, 0.381, -0.065, -0.079, 0.088, 0.366, 0.162, -0.068, 0.315, 0.708, 0.27, 0.228, 0.124, 0.124, 0.181, 0.155, 0.123, 0.104, 0.086]
OTHER_ADVANCED = [-0.097, -0.075, -0.115, -0.141, -0.166, -0.154, -0.215, -0.281, -0.253, -0.236, -0.226, -0.157, -0.264, -0.265, -0.257, -0.305, -0.274, -0.188, -0.186, -0.09, -0.084, 0.012, -0.074, -0.09, -0.122, -0.138, -0.147, -0.134, -0.122, -0.11, -0.093, -0.08]
US = [-1.128, -1.112, -1.266, -1.293, -1.402, -1.528, -1.54, -1.224, -1.045, -0.592, -0.615, -0.582, -0.52, -0.412, -0.436, -0.515, -0.492, -0.425, -0.481, -0.457, -0.685, -0.868, -0.946, -0.868, -1.071, -0.993, -0.986, -0.976, -0.911, -0.887, -0.862, -0.856]
EMERGING_DEVELOPING = [-0.144, -0.111, 0.017, 0.095, 0.041, -0.005, 0.035, -0.08, -0.286, -0.165, -0.343, -0.443, -0.576, -0.543, -0.446, -0.409, -0.301, -0.336, -0.417, -0.251, -0.052, -0.256, -0.406, -0.24, -0.203, -0.19, -0.284, -0.249, -0.249, -0.251, -0.264, -0.291]
DISCREPANCY = [0.416, 0.512, 0.392, 0.194, -0.055, -0.122, -0.345, -0.37, -0.172, -0.309, -0.491, -0.474, -0.499, -0.566, -0.552, -0.283, -0.395, -0.582, -0.452, -0.471, -0.297, -0.757, -0.39, -0.276, -0.438, -0.523, -0.691, -0.746, -0.785, -0.683, -0.634, -0.485]
FIRST_PROJ = 2026
# name, data, fill, label colour
SERIES = [("China", CHINA, RED, RED),
          ("Other East Asia", OTHER_EAST_ASIA, GOLD, "#A87A1C"),
          ("Germany and\nNetherlands", GERMANY_NETHERLANDS, SKY, "#3E6FA8"),
          ("Rest of Europe", REST_OF_EUROPE, "#A9C4E6", "#6F93C2"),
          ("Oil exporters", OIL_EXPORTERS, "#3A8F85", "#2E7A71"),
          ("United States", US, NAVY, NAVY),
          ("Other advanced", OTHER_ADVANCED, "#8E7CC3", "#6E5BA8"),
          ("Emerging and\ndeveloping", EMERGING_DEVELOPING, "#B08B62", "#8A6A45"),
          ("Statistical\ndiscrepancy", DISCREPANCY, "#D3D3D3", "#8A8A8A")]

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    x = np.array(CA_YEARS)
    ax.axvspan(FIRST_PROJ - 0.5, x[-1] + 0.5, color=BAND, lw=0, zorder=0)
    pos, neg = np.zeros(len(x)), np.zeros(len(x))
    mids = {}
    for name, v, c, tc in SERIES:
        v = np.array(v); base = np.where(v >= 0, pos, neg)
        ax.bar(x, v, 0.74, bottom=base, color=c, zorder=3)
        mids[name] = base[-1] + v[-1] / 2
        pos, neg = np.where(v >= 0, pos + v, pos), np.where(v < 0, neg + v, neg)
    order = sorted(mids, key=lambda k: mids[k]); ys = [mids[k] for k in order]
    nl = [k.count("\n") + 1 for k in order]
    for i in range(1, len(ys)):
        ys[i] = max(ys[i], ys[i - 1] + 0.1 * (nl[i] + nl[i - 1]) + 0.04)
    shift = (np.mean([mids[k] for k in order]) - np.mean(ys))
    for k, yv in zip(order, ys):
        tc = [s[3] for s in SERIES if s[0] == k][0]
        ax.text(x[-1] + 0.85, yv + shift, k, color=tc, fontfamily=CALIBRI, fontweight="bold", fontsize=S_LABEL,
                ha="left", va="center", linespacing=1.0)
    top, bot = pos.max(), neg.min()
    ax.text((FIRST_PROJ + x[-1]) / 2, top + 0.42, "IMF\nprojection", color=LABEL, fontfamily=CALIBRI,
            fontweight="bold", fontsize=S_HEAD, ha="center", va="center", linespacing=1.1)
    ax.set_xlim(x[0] - 0.6, x[-1] + 0.6); ax.set_ylim(bot - 0.12, top + 0.7)
    zero_line(ax)
    t = [v / 2 for v in range(int(np.ceil(bot * 2)), int(np.floor(top * 2)) + 1)]
    ax.set_yticks(t); ax.set_yticklabels([f"{v:.1f}".replace("-0.0", "0.0") for v in t])
    ax.set_xticks([2000, 2005, 2010, 2015, 2020, 2025, 2030])

compose(plot, "Imbalances take two to tango",
        "Current account balances, percent of world GDP",
        "Source: IMF, World Economic Outlook, October 2026.\n"
        "Note: Other East Asia is Japan, Korea, Taiwan Province of China, Singapore and Hong Kong SAR. Oil exporters "
        "include the Gulf states and Russia; other advanced includes the UK, Canada and Australia. The statistical "
        "discrepancy is the amount by which world balances fail to sum to zero.\n"
        "Read more: movingfrontiers.substack.com/consumer-class-asia",
        os.path.join(HERE, NAME + ".png"))
write_csv(os.path.join(HERE, NAME + ".csv"), ["year"] + [s[0].replace("\n", " ") for s in SERIES] + ["IMF projection"],
          [[y] + [s[1][i] for s in SERIES] + [y >= FIRST_PROJ] for i, y in enumerate(CA_YEARS)])
