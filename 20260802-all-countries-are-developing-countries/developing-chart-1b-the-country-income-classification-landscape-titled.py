"""Landscape version: linear and log panels stacked as rows, income on x.
Malaysia highlighted in both. No title band, no subtitle, no legend."""
import pandas as pd, numpy as np

# ---------------------------------------------------------------------------
# PROVENANCE (data frozen; do not replace with live calls or downloads)
#
# Source: World Bank OGHIST classification and income thresholds, 1 July 2026 (FY27);
# Source:         GNI per capita (Atlas) and population, World Bank WDI, July 2026 release.
# Frozen: 28 August 2026, from the csv published in this repository.
# The output is pinned to this vintage; a script that re-fetches upstream
# data is not reproducible, merely convenient.
# Derived: gni values are the author pipeline outputs rounded to whole dollars and
# Derived:         population to 3 decimals, exactly as in the published csv.
# Duplication: the same 207-economy table is embedded in the chart-1 build; the duplication is deliberate so each file stays single-file self-sufficient.
# ---------------------------------------------------------------------------

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family':'DejaVu Sans',
    'axes.edgecolor':'#888','axes.linewidth':1.0,
    'figure.facecolor':'white','axes.facecolor':'white'})

COL = {'L':'#C62828','LM':'#F9A825','UM':'#00897B','H':'#283593'}
TH = (1175,4635,14375)                     # FY27 thresholds, 2025 GNI per capita
GRP = {'Low income':'L','Lower middle income':'LM',
       'Upper middle income':'UM','High income':'H'}
# EMBEDDED DATA, exact copy of the csv (row order preserved: the jitter RNG maps by row)
ROWS = [
    ('Bermuda', 139370, 0.065, 'High income'),
    ('Liechtenstein', 116380, 0.041, 'High income'),
    ('Switzerland', 110330, 9.092, 'High income'),
    ('Norway', 97310, 5.611, 'High income'),
    ('Luxembourg', 95720, 0.687, 'High income'),
    ('Iceland', 89220, 0.392, 'High income'),
    ('United States', 88810, 341.785, 'High income'),
    ('Ireland', 87360, 5.484, 'High income'),
    ('Isle of Man', 87030, 0.084, 'High income'),
    ('Cayman Islands', 81920, 0.076, 'High income'),
    ('Singapore', 81760, 6.111, 'High income'),
    ('Denmark', 77190, 6.009, 'High income'),
    ('Qatar', 74330, 2.972, 'High income'),
    ('Faeroe Islands', 73120, 0.055, 'High income'),
    ('Macao SAR, China', 69920, 0.686, 'High income'),
    ('Netherlands', 68530, 18.088, 'High income'),
    ('Australia', 64120, 27.614, 'High income'),
    ('Sweden', 63010, 10.597, 'High income'),
    ('Hong Kong SAR, China', 62500, 7.499, 'High income'),
    ('Austria', 60360, 9.208, 'High income'),
    ('Germany', 60200, 83.491, 'High income'),
    ('Belgium', 59500, 11.942, 'High income'),
    ('Canada', 56420, 41.652, 'High income'),
    ('Israel', 56180, 10.123, 'High income'),
    ('Finland', 55250, 5.646, 'High income'),
    ('United Kingdom', 54550, 69.487, 'High income'),
    ('San Marino', 53910, 0.034, 'High income'),
    ('Andorra', 53230, 0.083, 'High income'),
    ('United Arab Emirates', 51550, 11.513, 'High income'),
    ('France', 48630, 68.72, 'High income'),
    ('New Zealand', 46630, 5.325, 'High income'),
    ('Italy', 42080, 58.916, 'High income'),
    ('Malta', 41440, 0.58, 'High income'),
    ('Kuwait', 41110, 4.865, 'High income'),
    ('Sint Maarten (Dutch part)', 38950, 0.044, 'High income'),
    ('Japan', 38340, 123.367, 'High income'),
    ('Korea, Rep.', 37880, 51.685, 'High income'),
    ('Spain', 37120, 49.355, 'High income'),
    ('Bahamas, The', 37020, 0.403, 'High income'),
    ('Turks and Caicos Islands', 36760, 0.047, 'High income'),
    ('Cyprus', 36110, 1.371, 'High income'),
    ('Saudi Arabia', 36070, 36.974, 'High income'),
    ('Slovenia', 35520, 2.131, 'High income'),
    ('Aruba', 35200, 0.109, 'High income'),
    ('Greenland', 34800, 0.057, 'High income'),
    ('Brunei Darussalam', 34790, 0.466, 'High income'),
    ('Czechia', 32960, 10.887, 'High income'),
    ('Estonia', 32310, 1.366, 'High income'),
    ('Lithuania', 30500, 2.889, 'High income'),
    ('New Caledonia', 30070, 0.295, 'High income'),
    ('Portugal', 29930, 10.805, 'High income'),
    ('Bahrain', 28790, 1.6, 'High income'),
    ('Guyana', 28470, 0.836, 'High income'),
    ('Puerto Rico (U.S.)', 27320, 3.185, 'High income'),
    ('Barbados', 27080, 0.283, 'High income'),
    ('Slovak Republic', 26410, 5.414, 'High income'),
    ('Poland', 25520, 36.436, 'High income'),
    ('Greece', 25360, 10.414, 'High income'),
    ('Croatia', 25360, 3.876, 'High income'),
    ('Latvia', 24980, 1.848, 'High income'),
    ('St. Kitts and Nevis', 24530, 0.047, 'High income'),
    ('French Polynesia', 24100, 0.282, 'High income'),
    ('Uruguay', 24020, 3.385, 'High income'),
    ('Hungary', 23850, 9.514, 'High income'),
    ('Antigua and Barbuda', 23790, 0.094, 'High income'),
    ('Curaçao', 22570, 0.156, 'High income'),
    ('Nauru', 20690, 0.012, 'High income'),
    ('Romania', 20190, 19.02, 'High income'),
    ('Palau', 19890, 0.018, 'High income'),
    ('Oman', 19520, 5.495, 'High income'),
    ('Seychelles', 19200, 0.123, 'High income'),
    ('Panama', 19140, 4.571, 'High income'),
    ('Trinidad and Tobago', 18550, 1.368, 'High income'),
    ('Costa Rica', 17930, 5.153, 'High income'),
    ('Bulgaria', 17780, 6.433, 'High income'),
    ('Chile', 16960, 19.86, 'High income'),
    ('Türkiye', 16300, 85.879, 'Upper middle income'),
    ('Russian Federation', 15960, 143.513, 'High income'),
    ('Argentina', 14650, 45.851, 'Upper middle income'),
    ('China', 14230, 1406.585, 'Upper middle income'),
    ('Montenegro', 14150, 0.623, 'Upper middle income'),
    ('Mauritius', 14040, 1.244, 'Upper middle income'),
    ('Kazakhstan', 13740, 20.844, 'Upper middle income'),
    ('Mexico', 13730, 131.947, 'Upper middle income'),
    ('Serbia', 13480, 6.549, 'Upper middle income'),
    ('St. Lucia', 13410, 0.18, 'Upper middle income'),
    ('Maldives', 12950, 0.53, 'Upper middle income'),
    ('Malaysia', 12380, 35.978, 'Upper middle income'),
    ('Albania', 12060, 2.35, 'Upper middle income'),
    ('St. Vincent and the Grenadines', 12000, 0.1, 'Upper middle income'),
    ('Grenada', 11660, 0.117, 'Upper middle income'),
    ('Dominica', 10690, 0.066, 'Upper middle income'),
    ('Dominican Republic', 10620, 11.52, 'Upper middle income'),
    ('Brazil', 10550, 212.812, 'Upper middle income'),
    ('Bosnia and Herzegovina', 9940, 3.14, 'Upper middle income'),
    ('Tuvalu', 9780, 0.009, 'Upper middle income'),
    ('Marshall Islands', 9710, 0.036, 'Upper middle income'),
    ('North Macedonia', 9490, 1.821, 'Upper middle income'),
    ('Belarus', 9160, 9.086, 'Upper middle income'),
    ('Armenia', 9020, 3.087, 'Upper middle income'),
    ('Cuba', 9010, 10.937, 'Upper middle income'),
    ('Georgia', 8990, 3.936, 'Upper middle income'),
    ('Peru', 8430, 34.577, 'Upper middle income'),
    ('Gabon', 8090, 2.593, 'Upper middle income'),
    ('Moldova', 8050, 2.361, 'Upper middle income'),
    ('Colombia', 7900, 53.426, 'Upper middle income'),
    ('Jamaica', 7790, 2.837, 'Upper middle income'),
    ('Kosovo', 7760, 1.577, 'Upper middle income'),
    ('Thailand', 7690, 71.62, 'Upper middle income'),
    ('Belize', 7530, 0.423, 'Upper middle income'),
    ('Botswana', 7390, 2.562, 'Upper middle income'),
    ('Azerbaijan', 7360, 10.247, 'Upper middle income'),
    ('Libya', 7250, 7.459, 'Upper middle income'),
    ('Ecuador', 6890, 18.29, 'Upper middle income'),
    ('Tonga', 6840, 0.104, 'Upper middle income'),
    ('Paraguay', 6750, 7.013, 'Upper middle income'),
    ('Guatemala', 6360, 18.688, 'Upper middle income'),
    ('Turkmenistan', 6340, 7.619, 'Upper middle income'),
    ('South Africa', 6270, 64.747, 'Upper middle income'),
    ('Fiji', 6230, 0.933, 'Upper middle income'),
    ('Mongolia', 6210, 3.569, 'Upper middle income'),
    ('Suriname', 6140, 0.64, 'Upper middle income'),
    ('Equatorial Guinea', 5890, 1.938, 'Upper middle income'),
    ('Algeria', 5850, 47.435, 'Upper middle income'),
    ('Iraq', 5690, 47.021, 'Upper middle income'),
    ('Samoa', 5640, 0.219, 'Upper middle income'),
    ('Cabo Verde', 5590, 0.527, 'Upper middle income'),
    ('Ukraine', 5510, 38.98, 'Upper middle income'),
    ('El Salvador', 5410, 6.366, 'Upper middle income'),
    ('Jordan', 5260, 11.521, 'Upper middle income'),
    ('Indonesia', 5120, 285.721, 'Upper middle income'),
    ('Viet Nam', 4970, 101.599, 'Upper middle income'),
    ('Philippines', 4850, 116.787, 'Upper middle income'),
    ('Micronesia, Fed. Sts.', 4760, 0.114, 'Upper middle income'),
    ('Sri Lanka', 4670, 21.756, 'Upper middle income'),
    ('Iran, Islamic Rep.', 4650, 92.418, 'Upper middle income'),
    ('Bolivia', 4420, 12.582, 'Lower middle income'),
    ('Vanuatu', 4410, 0.335, 'Lower middle income'),
    ('Morocco', 4360, 38.431, 'Lower middle income'),
    ('Namibia', 4340, 3.093, 'Lower middle income'),
    ('Bhutan', 4310, 0.797, 'Lower middle income'),
    ('Tunisia', 4300, 12.349, 'Lower middle income'),
    ('Djibouti', 3960, 1.184, 'Lower middle income'),
    ('Kiribati', 3930, 0.136, 'Lower middle income'),
    ('Venezuela, RB', 3860, 28.517, 'Lower middle income'),
    ('São Tomé and Príncipe', 3800, 0.24, 'Lower middle income'),
    ('Eswatini', 3730, 1.256, 'Lower middle income'),
    ('Uzbekistan', 3670, 37.053, 'Lower middle income'),
    ('Lebanon', 3560, 5.849, 'Lower middle income'),
    ('Honduras', 3270, 11.006, 'Lower middle income'),
    ('Egypt, Arab Rep.', 3260, 118.366, 'Lower middle income'),
    ('West Bank and Gaza', 3250, 5.414, 'Lower middle income'),
    ('Papua New Guinea', 2890, 10.763, 'Lower middle income'),
    ('Angola', 2860, 39.04, 'Lower middle income'),
    ('Nicaragua', 2850, 7.008, 'Lower middle income'),
    ('Bangladesh', 2840, 175.687, 'Lower middle income'),
    ('Kyrgyz Republic', 2800, 7.343, 'Lower middle income'),
    ("Côte d'Ivoire", 2780, 32.712, 'Lower middle income'),
    ('India', 2760, 1463.866, 'Lower middle income'),
    ('Cambodia', 2750, 17.848, 'Lower middle income'),
    ('Zimbabwe', 2660, 16.951, 'Lower middle income'),
    ('Ghana', 2630, 35.064, 'Lower middle income'),
    ('Congo, Rep.', 2280, 6.484, 'Lower middle income'),
    ('Mauritania', 2210, 5.315, 'Lower middle income'),
    ('Kenya', 2200, 57.532, 'Lower middle income'),
    ('Lao PDR', 2150, 7.873, 'Lower middle income'),
    ('Tajikistan', 2080, 10.787, 'Lower middle income'),
    ('Solomon Islands', 2020, 0.839, 'Lower middle income'),
    ('Haiti', 2010, 11.906, 'Lower middle income'),
    ('Comoros', 1950, 0.883, 'Lower middle income'),
    ('Cameroon', 1860, 29.879, 'Lower middle income'),
    ('Senegal', 1780, 18.932, 'Lower middle income'),
    ('Guinea', 1730, 15.1, 'Lower middle income'),
    ('Benin', 1600, 14.814, 'Lower middle income'),
    ('Nepal', 1570, 29.618, 'Lower middle income'),
    ('Timor-Leste', 1510, 1.419, 'Lower middle income'),
    ('Pakistan', 1500, 255.22, 'Lower middle income'),
    ('Nigeria', 1360, 237.528, 'Lower middle income'),
    ('Togo', 1350, 8.592, 'Lower middle income'),
    ('Myanmar', 1320, 54.851, 'Lower middle income'),
    ('Lesotho', 1280, 2.363, 'Lower middle income'),
    ('Tanzania', 1270, 70.546, 'Lower middle income'),
    ('Zambia', 1200, 21.914, 'Lower middle income'),
    ('Rwanda', 1150, 14.569, 'Low income'),
    ('Uganda', 1120, 51.385, 'Low income'),
    ('Mali', 1120, 25.199, 'Low income'),
    ('Ethiopia', 1110, 135.472, 'Low income'),
    ('Guinea-Bissau', 1090, 2.25, 'Low income'),
    ('South Sudan', 1050, 12.189, 'Low income'),
    ('Burkina Faso', 980, 24.075, 'Low income'),
    ('Chad', 970, 21.004, 'Low income'),
    ('Gambia, The', 930, 2.822, 'Low income'),
    ('Sudan', 900, 51.662, 'Low income'),
    ('Sierra Leone', 830, 8.82, 'Low income'),
    ('Liberia', 830, 5.731, 'Low income'),
    ('Niger', 750, 27.918, 'Low income'),
    ('Yemen, Rep.', 740, 41.774, 'Low income'),
    ('Congo, Dem. Rep.', 720, 112.832, 'Low income'),
    ('Syrian Arab Republic', 720, 25.62, 'Low income'),
    ('Eritrea', 650, 3.607, 'Low income'),
    ('Somalia, Fed. Rep.', 640, 19.655, 'Low income'),
    ('Malawi', 600, 22.216, 'Low income'),
    ('Mozambique', 570, 35.632, 'Low income'),
    ('Central African Republic', 560, 5.513, 'Low income'),
    ('Madagascar', 560, 32.741, 'Low income'),
    ('Afghanistan', 390, 43.844, 'Low income'),
    ('Burundi', 240, 14.39, 'Low income'),
]
COLS = ['economy', 'gni_per_capita_usd_atlas_2025', 'population_millions_2025', 'income_group_fy27']
d = pd.DataFrame(ROWS, columns=COLS)
g = pd.DataFrame({'name':d['economy'],
                  'base':d['gni_per_capita_usd_atlas_2025'].astype(float),
                  'pop':d['population_millions_2025'],
                  'cls':d['income_group_fy27'].map(GRP)})

XM = np.log10(1450) - 1.0
def area(pop_m):
    if pop_m < 10: return 10
    x = (np.log10(pop_m) - 1.0) / XM
    return 10 + x**3.4 * 2200

rng = np.random.default_rng(7)
g['yj'] = rng.uniform(0.17,0.92,len(g))
SIDE = {'China':'right','India':'right','United States':'right','Indonesia':'eleven',
        'Nigeria':'right','Pakistan':'left','Brazil':'left','Japan':'right',
        'Congo, Dem. Rep.':'right','Malaysia':'right','Bermuda':'left'}
PINY = {'China':0.68,'India':0.42,'United States':0.52,'Indonesia':0.72,
        'Nigeria':0.56,'Pakistan':0.32,'Brazil':0.62,'Japan':0.30,
        'Congo, Dem. Rep.':0.42,'Malaysia':0.20,'Bermuda':0.80}
g.loc[g['name'].isin(PINY),'yj'] = g.loc[g['name'].isin(PINY),'name'].map(PINY)
SHOW={'United States':'US','Congo, Dem. Rep.':'DR Congo'}

FIGW, FIGH = 8, 6.6
L_TOP, R_TOP = 140000, 140000
assert g['base'].max() <= L_TOP, 'linear scale no longer covers the maximum'

fig, axes = plt.subplots(2,1,figsize=(FIGW,FIGH))
BLW = 2.4*4
seg_specs=[]; panel_titles=[]
for ax, scale in zip(axes,['linear','log']):
    if scale=='linear':
        lo,hi = 0,L_TOP
    else:
        lo,hi = 200,R_TOP; ax.set_xscale('log')
    ax.set_xlim(lo,hi); ax.set_ylim(0,1)
    seg_specs.append((ax,[lo,TH[0],TH[1],TH[2],hi]))
    sub = g if scale=='log' else g[g['base']<=L_TOP]
    sub = sub.assign(_a=sub['pop'].apply(area)).sort_values('_a',ascending=False)
    for _,r in sub.iterrows():
        ax.scatter(r['base'],r['yj'],s=area(r['pop']),
                   facecolor=COL[r['cls']],alpha=0.45,
                   edgecolor='white',lw=0.5,zorder=3,clip_on=False)
    # labels
    lab = SIDE if scale=='log' else {}
    for _,r in g[g['name'].isin(lab)].iterrows():
        if scale=='linear' and r['base']>L_TOP: continue
        nm = SHOW.get(r['name'],r['name'])
        side = lab[r['name']]
        rad = np.sqrt(area(r['pop']))/2
        if side=='eleven':
            dx,dy,ha,va = -0.72*rad-2, 0.72*rad+2, 'right','bottom'
        else:
            off = 3 + rad
            dx = off if side=='right' else -off
            dy = 0
            ha = 'left' if side=='right' else 'right'; va='center'
        ax.annotate(nm,(r['base'],r['yj']),xytext=(dx,dy),
            textcoords='offset points',ha=ha,va=va,
            fontsize=8.6,fontweight='bold',color='#555',zorder=7)
    if scale=='log':
        ax.set_xticks([1175,4635,14375,R_TOP])
        ax.set_xticklabels(['$1,175','$4,635','$14,375','$140,000'],fontsize=10)
        ax.minorticks_off()
        panel_lbl='Log scale: equal widths are equal ratios'
    else:
        ax.set_xticks([4635,14375,L_TOP])
        ax.set_xticklabels(['\n$4,635','$14,375','$140,000'],fontsize=10)
        panel_lbl='Linear scale: equal widths are equal dollars'
    ax.set_yticks([])
    for s in ['top','right','left','bottom']: ax.spines[s].set_visible(False)
    ax.tick_params(axis='x',length=0,pad=5)
    panel_titles.append(ax.text(0.0,1.03,panel_lbl,transform=ax.transAxes,
        fontsize=11.5,fontweight='bold',color='#444',va='bottom'))

# ---------------- caption / watermark, project-standard format ----------------
FS = 7.0                     # caption font size
WMFS = FS*1.2                # watermark = caption size x 1.2
H_OUT = FIGH*200; W_OUT = FIGW*200
lh_fig = 22.0/H_OUT          # caption line pitch, published standard

CAP_TEXT = ("Source: World Bank OGHIST classification and income thresholds, 1 July 2026 "
 "(FY27, 2025 GNI per capita, Atlas method, current US\$); GNI per capita and population "
 "from World Bank WDI, July 2026 release. Note: Each bubble is one of the 207 classified "
 "economies with a reported income level, positioned by its latest GNI per capita. "
 "Colored segments mark the four income groups at the FY27 thresholds "
 "of \$1,175, \$4,635 and \$14,375; the high-income group has no upper bound and both scales "
 "end at Bermuda (\$139,370), the highest observed income. Argentina and Turkiye, "
 "upper-middle income in the FY27 classification, already report 2025 income above the "
 "threshold and sit above the high-income line.")
CLOSERS = ["All values refer to the 2025 data year.",
           "Bubble areas are comparable across the two panels.",
           "The vertical position within each panel carries no information."]

assert '%d classified '%len(g) in CAP_TEXT, \
    'caption economy count no longer matches the embedded data'
assert '\\$1,175, \\$4,635 and \\$14,375' in CAP_TEXT and TH==(1175,4635,14375), \
    'caption threshold values no longer match TH'
_mx=g.loc[g['base'].idxmax()]
assert _mx['name']=='Bermuda' and 'Bermuda (\\$139,370)' in CAP_TEXT and int(_mx['base'])==139370, \
    'caption maximum (Bermuda, \$139,370) no longer matches the data'
for _nm in ['Argentina','Türkiye']:
    _r=g[g['name']==_nm].iloc[0]
    assert _r['cls']=='UM' and _r['base']>TH[2], \
        'caption sentence on Argentina and Turkiye no longer matches the data'

fig.canvas.draw(); ren=fig.canvas.get_renderer()
CW,CH = fig.canvas.get_width_height()
_probe=fig.text(0.3,0.5,'',fontsize=FS)
_wcache={}
def wpx(t,fs):
    key=(t,fs)
    if key not in _wcache:
        _probe.set_text(t); _probe.set_fontsize(fs)
        _wcache[key]=_probe.get_window_extent(ren).width/CW
    return _wcache[key]
SPACE = wpx('n n',FS)-wpx('nn',FS)
X0 = 0.012
FULL = 1-70/1600                                # right margin 70 px
WM_X1 = 1-70/1600
wm_w = wpx('movingfrontiers.substack.com',WMFS)
MOVI = wpx('movi',WMFS)
SHORT = WM_X1 - wm_w - MOVI                     # last two lines stop one movi short

def greedy(words,limit):
    lines=[]; cur=[]; w=0.0
    for word in words:
        ww=wpx(word,FS)
        add=ww if not cur else ww+SPACE
        if X0+w+add<=limit or not cur:
            cur.append(word); w+=add
        else:
            lines.append(' '.join(cur)); cur=[word]; w=ww
    if cur: lines.append(' '.join(cur))
    return lines

text=CAP_TEXT; ci=0
while True:
    words=text.split()
    full_lines=greedy(words,FULL)
    lead, tail = full_lines[:-1], full_lines[-1]
    tail_lines=greedy(tail.split(),SHORT)
    if len(tail_lines)==2:
        pen_fill=(X0+ (wpx(tail_lines[0],FS))) >= X0+0.70*(SHORT-X0)
        if pen_fill: break
    if ci>=len(CLOSERS):
        break
    text=text+' '+CLOSERS[ci]; ci+=1
cap_lines=lead+tail_lines
n=len(cap_lines)

# vertical placement: caption top exactly 2.00 line-heights below the lowest axis element
cap_h = n*lh_fig
rect_bottom = 2*lh_fig + cap_h + 0.006
for attempt in range(4):
    fig.tight_layout(rect=[0.015,rect_bottom,0.985,0.975])
    fig.subplots_adjust(hspace=0.42)
    fig.canvas.draw()
    lows=[]
    for ax in axes:
        for a in list(ax.get_xticklabels())+list(ax.texts):
            bb=a.get_window_extent(ren)
            lows.append(bb.y0/CH)
        lows.append(ax.get_window_extent(ren).y0/CH)
    lowest=min(lows)
    cap_top = lowest - 2.0*lh_fig
    cap_bottom = cap_top - cap_h
    if cap_bottom > 0.004: break
    rect_bottom += (0.006 - cap_bottom)
assert cap_bottom > 0.004, 'caption does not fit'

_probe.remove()
arts=[]
for i,ln in enumerate(cap_lines):
    yb = cap_top - (i+1)*lh_fig + lh_fig*0.22        # baseline within the line box
    arts.append(fig.text(X0,yb,ln,fontsize=FS,color='#666',ha='left',va='baseline'))
wm = fig.text(WM_X1, cap_top - n*lh_fig + lh_fig*0.22,
              'movingfrontiers.substack.com',fontsize=WMFS,color='#999999',
              ha='right',va='baseline')
fig.canvas.draw()

# colored bottom-edge segments with half-character gaps, in display space
half_gap = 0.5*FS*fig.dpi/72
for ax,edges in seg_specs:
    tr=ax.transData; inv=tr.inverted()
    for k,(a0,a1,grp) in enumerate(zip(edges[:-1],edges[1:],['L','LM','UM','H'])):
        p0=tr.transform((a0,0))[0]+(half_gap/2 if k>0 else 0)
        p1=tr.transform((a1,0))[0]-(half_gap/2 if k<3 else 0)
        d0=inv.transform((p0,0))[0]; d1=inv.transform((p1,0))[0]
        ax.plot([d0,d1],[0.015,0.015],color=COL[grp],lw=BLW,
                solid_capstyle='butt',zorder=2,clip_on=False)
fig.canvas.draw()

# ---- project-standard watermark asserts ----
wmb=wm.get_window_extent(ren)
for ln_art in arts[-2:]:
    gap=(wmb.x0 - ln_art.get_window_extent(ren).x1)/CW
    assert gap >= MOVI*0.98, 'last-two-line gap below one movi width: %.4f'%gap
pen_w=(arts[-2].get_window_extent(ren).x1)/CW
assert pen_w >= X0+0.70*(SHORT-X0)*0.98, 'second-to-last line underfilled'
# same baseline: both drawn va=baseline at identical y
assert abs(wm.get_position()[1]-arts[-1].get_position()[1])<1e-9
print('caption lines: %d (closers appended: %d), gap(last)=%.4f movi=%.4f'%(
      n,ci,(wmb.x0-arts[-1].get_window_extent(ren).x1)/CW,MOVI))
print('caption bottom %.4f, top gap below axes = 2.00 lines by construction'%cap_bottom)

ax1=axes[1]
texts=[t for t in ax1.texts if t.get_fontweight()=='bold' and t.get_fontsize()==8.6]
texts+=[t for t in axes[0].texts if t.get_fontweight()=='bold' and t.get_fontsize()==8.6]
import itertools
for a,b in itertools.combinations(texts,2):
    if a.axes is not b.axes: continue
    ba,bb=a.get_window_extent(ren),b.get_window_extent(ren)
    ox=max(0,min(ba.x1,bb.x1)-max(ba.x0,bb.x0)); oy=max(0,min(ba.y1,bb.y1)-max(ba.y0,bb.y0))
    assert ox*oy==0, 'label overlap %s/%s'%(a.get_text(),b.get_text())
print('labels clean:',len(texts))

OUT='chart-1b-the-country-income-classification-landscape-titled.png'
fig.savefig(OUT,dpi=200)
plt.close(fig)
from PIL import Image, ImageDraw, ImageFont


def _resolve_font(name):
    """System DejaVu first (matches the published render on the original build
    machine), then matplotlib's bundled copy. On systems where the fallback
    engages, the PIL title band may differ at pixel level; nothing else does."""
    import matplotlib, os
    cands = ['/usr/share/fonts/truetype/dejavu/'+name,
             os.path.join(matplotlib.get_data_path(),'fonts','ttf',name)]
    for p in cands:
        if os.path.exists(p): return p
    raise FileNotFoundError(name+' not found in any known location')
FB=_resolve_font('DejaVuSans-Bold.ttf')
FR=_resolve_font('DejaVuSans.ttf')
title="The high-income line is not a finish line"
subtitle='Classified economies by GNI per capita against FY27 income thresholds, sized by population and on a linear and a logarithmic scale'
im=Image.open(OUT).convert('RGB'); W,H=im.size
fs=int(W*0.031); font=ImageFont.truetype(FB,fs)
fss=int(W*0.0225); fonts=ImageFont.truetype(FR,fss)
tmp=ImageDraw.Draw(im)
def wrap(text,f):
    words=text.split(); lines=[]; cur=''
    for w in words:
        t=(cur+' '+w).strip()
        if tmp.textlength(t,font=f)<=W-2*int(W*0.03): cur=t
        else: lines.append(cur); cur=w
    lines.append(cur); return lines
lines=wrap(title,font); slines=wrap(subtitle,fonts)
lh=int(fs*1.25); lhs=int(fss*1.3)
band=int(fs*0.85)+lh*len(lines)+int(fss*0.5)+lhs*len(slines)+int(fs*0.03)
canvas=Image.new('RGB',(W,H+band),'white'); canvas.paste(im,(0,band))
dr=ImageDraw.Draw(canvas); y=int(fs*0.85)
for ln in lines: dr.text((int(W*0.03),y),ln,font=font,fill=(45,45,45)); y+=lh
y+=int(fss*0.35)
for ln in slines: dr.text((int(W*0.03),y),ln,font=fonts,fill=(100,100,100)); y+=lhs
canvas.save(OUT,optimize=True)
print('done titled',canvas.size)
