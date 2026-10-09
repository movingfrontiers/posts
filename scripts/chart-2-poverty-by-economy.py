"""Chart 2: poverty by economy.
Self-contained: house style and data are embedded. Requires numpy, matplotlib and Pillow.
Run: python chart-2-poverty-by-economy.py  -> writes chart-2-poverty-by-economy.png and .csv
"""
# ---- Moving Frontiers house style (inlined) -------------------------------
# Plot in matplotlib on a transparent canvas, then compose() lays out title,
# subtitle, plot, caption and watermark in PIL with every gap measured ink to
# ink, and verify() re-measures the finished PNG and asserts the gaps.
import io, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

RED, GOLD, GREEN, BLUE, GREY = "#C62828", "#F9A825", "#00897B", "#283593", "#888888"
INK, PAPER = "#141414", "#FFFFFF"
def palette(n):
    return [[BLUE], [BLUE, RED], [BLUE, RED, GREEN], [BLUE, RED, GREEN, GOLD]][n - 1]

REF_W = 1980
GAP_TITLE_SUB, GAP_SUB_PLOT, GAP_PLOT_CAP, GAP_CAP_MARK, BORDER = 25, 70, 60, 20, 70
TITLE_PX, SUB_PX, CAP_PX = 61, 40, 30          # at REF_W; title ~3.1% of width
TITLE_RGB, SUB_RGB, CAP_RGB = (45, 45, 45), (100, 100, 100), (102, 102, 102)
WATERMARK = "movingfrontiers.substack.com"

_fp = font_manager.findfont("DejaVu Sans")
_fpb = font_manager.findfont(font_manager.FontProperties(family="DejaVu Sans", weight="bold"))
def _font(px, bold=False):
    return ImageFont.truetype(_fpb if bold else _fp, px)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 15,
    "xtick.labelsize": 14, "ytick.labelsize": 14, "legend.fontsize": 14,
    "axes.labelsize": 15, "axes.edgecolor": "#888888", "axes.linewidth": 1.0,
    "axes.facecolor": PAPER, "figure.facecolor": "none", "savefig.facecolor": "none",
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": "#444444", "ytick.color": "#444444", "text.color": INK,
})

def new_figure(w_in=9.2, h_in=7.34, dpi=200):
    fig = plt.figure(figsize=(w_in, h_in), dpi=dpi)
    return fig

def render_plot(fig):
    """Rasterise the figure on a transparent background and crop to its ink."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=fig.dpi, transparent=True, bbox_inches="tight", pad_inches=0.05)
    buf.seek(0)
    im = Image.open(buf).convert("RGBA")
    bbox = im.getchannel("A").getbbox()
    return im.crop(bbox)

def _text_layer(text, px, rgb, bold=False, width_px=None, align="left", linespacing=1.25):
    """Render wrapped text on a transparent layer cropped to its ink."""
    font = _font(px, bold)
    if width_px:
        # wrap by measured width
        lines = []
        for para in text.split("\n"):
            words, cur = para.split(), ""
            for w in words:
                t = (cur + " " + w).strip()
                if font.getlength(t) <= width_px or not cur:
                    cur = t
                else:
                    lines.append(cur); cur = w
            lines.append(cur)
    else:
        lines = text.split("\n")
    lh = int(round(px * linespacing))
    H = lh * len(lines) + px
    W = int(max(font.getlength(l) for l in lines)) + px
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, l in enumerate(lines):
        x = 0 if align == "left" else W - px - font.getlength(l)
        d.text((x, i * lh), l, font=font, fill=rgb + (255,))
    return layer.crop(layer.getchannel("A").getbbox())

def compose(plot_im, title, subtitle, source, note=None, out="chart.png", csv=None, csv_rows=None, W=REF_W):
    s = W / REF_W
    inner = W - 2 * BORDER
    # scale the plot to the inner width
    pw, ph = plot_im.size
    if pw != inner:
        plot_im = plot_im.resize((inner, int(ph * inner / pw)), Image.LANCZOS)
    t_layer = _text_layer(title, int(TITLE_PX * s), TITLE_RGB, bold=True, width_px=inner)
    s_layer = _text_layer(subtitle, int(SUB_PX * s), SUB_RGB, width_px=inner)
    cap = "Source: " + source + ("\nNote: " + note if note else "")
    c_layer = _text_layer(cap, int(CAP_PX * s), CAP_RGB, width_px=inner)
    m_layer = _text_layer(WATERMARK, int(CAP_PX * 1.2 * s), CAP_RGB)
    H = (BORDER + t_layer.height + GAP_TITLE_SUB + s_layer.height + GAP_SUB_PLOT + plot_im.height
         + GAP_PLOT_CAP + c_layer.height + GAP_CAP_MARK + m_layer.height + BORDER)
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    y = BORDER
    canvas.paste(t_layer, (BORDER, y), t_layer); y += t_layer.height + GAP_TITLE_SUB
    canvas.paste(s_layer, (BORDER, y), s_layer); y += s_layer.height + GAP_SUB_PLOT
    canvas.paste(plot_im, (BORDER, y), plot_im); y += plot_im.height + GAP_PLOT_CAP
    canvas.paste(c_layer, (BORDER, y), c_layer); y += c_layer.height + GAP_CAP_MARK
    canvas.paste(m_layer, (W - BORDER - m_layer.width, y), m_layer)
    canvas.save(out, dpi=(200, 200))
    if csv and csv_rows:
        import csv as _csv
        with open(csv, "w", newline="") as f:
            _csv.writer(f).writerows(csv_rows)
    verify(out, (t_layer.height, s_layer.height, plot_im.height, c_layer.height, m_layer.height))
    return out

def verify(path, heights):
    """Scan rows of the finished PNG for ink and assert the vertical gaps."""
    a = np.asarray(Image.open(path).convert("L"))
    ink_rows = np.where((a < 250).any(axis=1))[0]
    ink_cols = np.where((a < 250).any(axis=0))[0]
    assert ink_rows[0] == BORDER and ink_cols[0] == BORDER, ("border", ink_rows[0], ink_cols[0])
    assert a.shape[0] - 1 - ink_rows[-1] == BORDER, ("bottom border", a.shape[0] - 1 - ink_rows[-1])
    # blocks of ink separated by white gaps
    gaps, prev = [], ink_rows[0]
    for r in ink_rows[1:]:
        if r - prev > 1:
            gaps.append(r - prev - 1)
        prev = r
    expected = [GAP_TITLE_SUB, GAP_SUB_PLOT, GAP_PLOT_CAP, GAP_CAP_MARK]
    found = [g for g in gaps if g >= GAP_CAP_MARK - 1]
    # the four structural gaps must be present in order (text lines create smaller gaps)
    ok = [g for g in found if g in expected or g - 1 in expected or g + 1 in expected]
    assert len(ok) >= 4, ("structural gaps", found)
    print(f"verified {path}: size {a.shape[1]}x{a.shape[0]}, gaps {found}")
# ---------------------------------------------------------------------------

# World Bank PIP country estimates, $3.00 a day (2021 PPP): latest national survey per economy.
# (country, code, survey reporting year, headcount ratio, population in survey year)
DATA = [
    ('Congo, Dem. Rep.', 'COD', 2020, 0.853177, 95989998),
    ('Mozambique', 'MOZ', 2022, 0.813614, 32734559),
    ('South Sudan', 'SSD', 2016, 0.765026, 10544628),
    ('Malawi', 'MWI', 2019, 0.754382, 19183274),
    ('Burundi', 'BDI', 2020, 0.741992, 12669302),
    ('Zambia', 'ZMB', 2022, 0.716561, 20152938),
    ('Central African Republic', 'CAF', 2021, 0.716173, 5112100),
    ('Madagascar', 'MDG', 2021, 0.691726, 30250716),
    ('Niger', 'NER', 2021, 0.604899, 24907056),
    ('Uganda', 'UGA', 2023, 0.543621, 48887544),
    ('Papua New Guinea', 'PNG', 2009, 0.522103, 7558584),
    ('Tanzania', 'TZA', 2018, 0.513469, 57294404),
    ('Zimbabwe', 'ZWE', 2019, 0.492199, 15271368),
    ('Kenya', 'KEN', 2022, 0.454827, 54980444),
    ('Eswatini', 'SWZ', 2016, 0.445309, 1150983),
    ('Timor-Leste', 'TLS', 2014, 0.440327, 1189103),
    ('Burkina Faso', 'BFA', 2021, 0.420616, 22339485),
    ('Lesotho', 'LSO', 2017, 0.418585, 2160819),
    ('Nigeria', 'NGA', 2022, 0.418195, 226510650),
    ('Sierra Leone', 'SLE', 2018, 0.414852, 7554563),
    ('Haiti', 'HTI', 2012, 0.404150, 10069771),
    ('Solomon Islands', 'SLB', 2012, 0.403015, 590463),
    ('Guinea-Bissau', 'GNB', 2021, 0.398611, 2093857),
    ('Chad', 'TCD', 2022, 0.394754, 18455316),
    ('Angola', 'AGO', 2018, 0.392947, 31480496),
    ('Congo, Rep.', 'COG', 2011, 0.392169, 4697310),
    ('Ghana', 'GHA', 2016, 0.390258, 29845451),
    ('Ethiopia', 'ETH', 2021, 0.386361, 122138588),
    ('Rwanda', 'RWA', 2023, 0.385505, 14187084),
    ('Mali', 'MLI', 2021, 0.361031, 22778515),
    ('Turkmenistan', 'TKM', 1998, 0.350759, 4410507),
    ('Togo', 'TGO', 2021, 0.346611, 9011535),
    ('Liberia', 'LBR', 2016, 0.335589, 4755608),
    ('Yemen, Rep.', 'YEM', 2014, 0.333005, 30226309),
    ('Benin', 'BEN', 2021, 0.272234, 13672980),
    ('Cameroon', 'CMR', 2021, 0.266918, 27396156),
    ('Micronesia, Fed. Sts.', 'FSM', 2013, 0.261471, 108121),
    ('Djibouti', 'DJI', 2017, 0.253609, 1054841),
    ('Pakistan', 'PAK', 2024, 0.229563, 253639397),
    ('Namibia', 'NAM', 2015, 0.228631, 2391826),
    ('Gambia, The', 'GMB', 2020, 0.220019, 2520555),
    ('Botswana', 'BWA', 2015, 0.213653, 2230050),
    ("Côte d'Ivoire", 'CIV', 2021, 0.208261, 30206185),
    ('Vanuatu', 'VUT', 2019, 0.194956, 293428),
    ('Syrian Arab Republic', 'SYR', 2022, 0.179619, 22462173),
    ('Senegal', 'SEN', 2021, 0.178875, 17526334),
    ('South Africa', 'ZAF', 2022, 0.174359, 63087287),
    ('Honduras', 'HND', 2024, 0.157174, 10825703),
    ('Cabo Verde', 'CPV', 2015, 0.146041, 512394),
    ('Guyana', 'GUY', 1998, 0.130110, 763586),
    ('São Tomé and Príncipe', 'STP', 2017, 0.130061, 206970),
    ('Guinea', 'GIN', 2018, 0.116504, 12869560),
    ('Philippines', 'PHL', 2023, 0.115317, 114891199),
    ('Myanmar', 'MMR', 2017, 0.102662, 51894938),
    ('Mauritania', 'MRT', 2019, 0.102215, 4547161),
    ('Sudan', 'SDN', 2014, 0.101000, 38823318),
    ('Kosovo', 'XKX', 2022, 0.099788, 1768096),
    ('Nauru', 'NRU', 2012, 0.097186, 10439),
    ('Venezuela, RB', 'VEN', 2006, 0.097121, 27224686),
    ('Guatemala', 'GTM', 2023, 0.096609, 18124838),
    ('Tuvalu', 'TUV', 2010, 0.089908, 10614),
    ('Equatorial Guinea', 'GNQ', 2022, 0.087942, 1830387),
    ('Colombia', 'COL', 2024, 0.085007, 52886363),
    ('Lao PDR', 'LAO', 2024, 0.071269, 7769819),
    ('Nicaragua', 'NIC', 2014, 0.065704, 6066492),
    ('Tajikistan', 'TJK', 2024, 0.061335, 10590927),
    ('Bangladesh', 'BGD', 2022, 0.059091, 169384897),
    ('Lebanon', 'LBN', 2022, 0.057806, 5767692),
    ('Peru', 'PER', 2024, 0.051406, 34217848),
    ('Comoros', 'COM', 2024, 0.050668, 866628),
    ('Fiji', 'FJI', 2019, 0.046531, 914908),
    ('El Salvador', 'SLV', 2023, 0.046368, 6309624),
    ('Samoa', 'WSM', 2013, 0.044586, 198710),
    ('Georgia', 'GEO', 2024, 0.042293, 3699557),
    ('North Macedonia', 'MKD', 2019, 0.039404, 1876262),
    ('Gabon', 'GAB', 2017, 0.038105, 2156900),
    ('Indonesia', 'IDN', 2025, 0.036916, 285721236),
    ('Morocco', 'MAR', 2013, 0.036759, 33996175),
    ('Ecuador', 'ECU', 2025, 0.034185, 18289896),
    ('Trinidad and Tobago', 'TTO', 1992, 0.032380, 1271674),
    ('Panama', 'PAN', 2024, 0.031258, 4515577),
    ('Brazil', 'BRA', 2024, 0.030075, 211998573),
    ('Sri Lanka', 'LKA', 2019, 0.027055, 21803000),
    ('India', 'IND', 2023, 0.025724, 1445531989),
    ('Montenegro', 'MNE', 2021, 0.024938, 625053),
    ('Iran, Islamic Rep.', 'IRN', 2023, 0.024873, 90829284),
    ('Nepal', 'NPL', 2022, 0.024363, 29705025),
    ('Uzbekistan', 'UZB', 2025, 0.023007, 37053428),
    ('Kyrgyz Republic', 'KGZ', 2024, 0.021876, 7221868),
    ('Suriname', 'SUR', 2022, 0.021780, 623164),
    ('Paraguay', 'PRY', 2024, 0.021053, 6929153),
    ('Marshall Islands', 'MHL', 2019, 0.021010, 43356),
    ('West Bank and Gaza', 'PSE', 2023, 0.020733, 5165775),
    ('Bolivia', 'BOL', 2024, 0.020502, 12413315),
    ('Barbados', 'BRB', 2016, 0.016774, 279598),
    ('Mexico', 'MEX', 2024, 0.016459, 130861007),
    ('Viet Nam', 'VNM', 2022, 0.016034, 99680655),
    ('Jamaica', 'JAM', 2021, 0.013869, 2837682),
    ('Egypt, Arab Rep.', 'EGY', 2021, 0.013738, 112236164),
    ('Japan', 'JPN', 2020, 0.012000, 126261000),
    ('United States', 'USA', 2024, 0.011000, 340110988),
    ('Lithuania', 'LTU', 2023, 0.010979, 2871585),
    ('Serbia', 'SRB', 2023, 0.010942, 6623183),
    ('Belize', 'BLZ', 2018, 0.010365, 381346),
    ('Bulgaria', 'BGR', 2023, 0.010110, 6446596),
    ('Kiribati', 'KIR', 2023, 0.009291, 133364),
    ('Italy', 'ITA', 2023, 0.009272, 58984216),
    ('Hungary', 'HUN', 2017, 0.009180, 9726756),
    ('Australia', 'AUS', 2020, 0.009000, 25649248),
    ('Sweden', 'SWE', 2023, 0.008379, 10536632),
    ('Spain', 'ESP', 2023, 0.008134, 48352528),
    ('Armenia', 'ARM', 2024, 0.007843, 3033500),
    ('Dominican Republic', 'DOM', 2024, 0.007753, 11427557),
    ('Grenada', 'GRD', 2018, 0.007674, 115795),
    ('Costa Rica', 'CRI', 2025, 0.007547, 5152950),
    ('Romania', 'ROU', 2023, 0.007002, 19061062),
    ('Germany', 'DEU', 2022, 0.007000, 83177813),
    ('Seychelles', 'SYC', 2018, 0.006736, 96831),
    ('Tunisia', 'TUN', 2021, 0.006540, 12064885),
    ('Greece', 'GRC', 2023, 0.005943, 10407351),
    ('Iraq', 'IRQ', 2023, 0.005494, 45074049),
    ('Mauritius', 'MUS', 2017, 0.005402, 1264887),
    ('Austria', 'AUT', 2023, 0.005282, 9131761),
    ('Slovak Republic', 'SVK', 2023, 0.004521, 5426740),
    ('Latvia', 'LVA', 2023, 0.004441, 1883710),
    ('Mongolia', 'MNG', 2022, 0.004398, 3433748),
    ('Portugal', 'PRT', 2023, 0.004133, 10578174),
    ('Tonga', 'TON', 2021, 0.004088, 105490),
    ('Israel', 'ISR', 2022, 0.004000, 9557500),
    ('United Kingdom', 'GBR', 2021, 0.004000, 66984000),
    ('Chile', 'CHL', 2024, 0.003997, 19764771),
    ('Malta', 'MLT', 2023, 0.003939, 552747),
    ('Denmark', 'DNK', 2023, 0.003592, 5946952),
    ('Albania', 'ALB', 2020, 0.003409, 2528480),
    ('Estonia', 'EST', 2023, 0.003169, 1370286),
    ('Canada', 'CAN', 2022, 0.003000, 38935934),
    ('Bosnia and Herzegovina', 'BIH', 2021, 0.002675, 3244907),
    ('Croatia', 'HRV', 2023, 0.002628, 3859686),
    ('Poland', 'POL', 2023, 0.002441, 36687353),
    ('Norway', 'NOR', 2023, 0.001971, 5519601),
    ('Finland', 'FIN', 2023, 0.001951, 5583911),
    ('Türkiye', 'TUR', 2023, 0.001751, 85325965),
    ('Uruguay', 'URY', 2024, 0.001672, 3386588),
    ('Jordan', 'JOR', 2010, 0.001041, 7341054),
    ('Taiwan, China', 'TWN', 2021, 0.001000, 23487509),
    ('Korea, Rep.', 'KOR', 2021, 0.001000, 51769539),
    ('Netherlands', 'NLD', 2021, 0.000973, 17533044),
    ('Russian Federation', 'RUS', 2023, 0.000912, 143826130),
    ('Belgium', 'BEL', 2023, 0.000869, 11779946),
    ('Luxembourg', 'LUX', 2023, 0.000851, 666430),
    ('St. Lucia', 'LCA', 2015, 0.000829, 175482),
    ('Ireland', 'IRL', 2023, 0.000823, 5311538),
    ('Iceland', 'ISL', 2019, 0.000799, 360563),
    ('France', 'FRA', 2023, 0.000697, 68372286),
    ('Switzerland', 'CHE', 2023, 0.000696, 8888822),
    ('Kazakhstan', 'KAZ', 2021, 0.000402, 19743603),
    ('Ukraine', 'UKR', 2020, 0.000338, 44680014),
    ('Thailand', 'THA', 2024, 0.000147, 71668011),
    ('Cyprus', 'CYP', 2023, 0.000132, 1344976),
    ('Malaysia', 'MYS', 2021, 0.000131, 34472422),
    ('Bhutan', 'BTN', 2022, 0.000070, 780914),
    ('Azerbaijan', 'AZE', 2005, 0.000000, 8391850),
    ('Algeria', 'DZA', 2011, 0.000000, 37029650),
    ('United Arab Emirates', 'ARE', 2018, 0.000000, 9346701),
    ('Qatar', 'QAT', 2017, 0.000000, 2563277),
    ('Maldives', 'MDV', 2019, 0.000000, 496363),
    ('Belarus', 'BLR', 2020, 0.000000, 9379952),
    ('China', 'CHN', 2022, 0.000000, 1412175000),
    ('Slovenia', 'SVN', 2023, 0.000000, 2120461),
    ('Czechia', 'CZE', 2023, 0.000000, 10864042),
    ('Moldova', 'MDA', 2024, 0.000000, 2402306)
]
from matplotlib.patches import Patch
rows = sorted(DATA, key=lambda r: -r[3])
x0, acc = [], 0.0
for r in rows:
    x0.append(acc); acc += r[4] / 1e9
widths = [r[4] / 1e9 for r in rows]
h = [r[3] * 100 for r in rows]
total_pop = acc

def col(v):
    return RED if v >= 50 else (GOLD if v >= 25 else (BLUE if v >= 10 else GREY))

fig = new_figure(9.2, 6.4)
ax = fig.add_subplot(111)
ax.bar(x0, h, width=widths, align="edge", color=[col(v) for v in h], linewidth=0.3, edgecolor="white")
ax.set_xlim(0, total_pop)
ax.set_ylim(0, 100)
ax.set_xlabel("Population, billions (economies sorted from highest to lowest poverty rate)")
ax.set_ylabel("Share of population below $3.00 a day, %")
ax.set_yticks(range(0, 101, 25))
ax.set_yticklabels([f"{v}%" for v in range(0, 101, 25)])

idx = {r[0]: i for i, r in enumerate(rows)}
def lab(name, text, dy, dx):
    i = idx[name]; xm = x0[i] + widths[i] / 2
    ax.annotate(text, xy=(xm, h[i]), xytext=(xm + dx, h[i] + dy), fontsize=12, ha="left", va="bottom", color=INK,
                arrowprops=dict(arrowstyle="-", color="#666", lw=0.8))
lab("Congo, Dem. Rep.", f"DR Congo {h[idx['Congo, Dem. Rep.']]:.0f}%", 5, 0.05)
lab("Nigeria", f"Nigeria {h[idx['Nigeria']]:.0f}%", 10, 0.1)
lab("Ethiopia", f"Ethiopia {h[idx['Ethiopia']]:.0f}%", 5, 0.28)
lab("Pakistan", f"Pakistan {h[idx['Pakistan']]:.0f}%", 8, 0.3)
lab("India", f"India {h[idx['India']]:.0f}%", 20, 0.1)
lab("China", f"China {h[idx['China']]:.0f}%", 14, 0.1)

n50 = sum(v >= 50 for v in h); n25 = sum(25 <= v < 50 for v in h); n10 = sum(10 <= v < 25 for v in h); n0 = sum(v < 10 for v in h)
ax.legend(handles=[Patch(color=RED, label=f"50% or more ({n50} economies)"), Patch(color=GOLD, label=f"25 to 50% ({n25})"),
                   Patch(color=BLUE, label=f"10 to 25% ({n10})"), Patch(color=GREY, label=f"Under 10% ({n0})")],
          loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, frameon=False)

poor_m = sum(r[3] * r[4] for r in rows) / 1e6
compose(render_plot(fig),
        title=f"In {n50} economies most people live on less than $3.00 a day; in {n50 + n25 + n10}, at least one in ten does",
        subtitle="Extreme poverty rate by economy, each bar as wide as its population, latest household survey",
        source="World Bank Poverty and Inequality Platform, country estimates at the $3.00 line (2021 PPP), latest national survey per economy.",
        note=f"{len(rows)} economies with a survey, covering {total_pop:.1f} billion people. Survey years range from {min(r[2] for r in rows)} to {max(r[2] for r in rows)} with a median of 2021, so the picture is a patchwork of vintages rather than a single year, and the area under the bars (about {round(poor_m, -1):.0f} million) understates the current World Bank count. Consumption surveys for most low and middle income economies, income surveys for most high income ones.",
        out="chart-2-poverty-by-economy.png", csv="chart-2-poverty-by-economy.csv",
        csv_rows=[["country", "code", "survey_year", "headcount_pct", "population"]] + [[r[0], r[1], r[2], round(r[3] * 100, 2), r[4]] for r in rows])
