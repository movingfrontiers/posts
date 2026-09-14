"""Chart 5: every economy as a multiple of the world average.

Self-sufficient: the data this chart consumes are embedded below, frozen at the
July 2026 vintage. No external files, downloads or network access. Writes the png
of the same name. Run from any directory:
  python3 chart-5-economies-by-multiple-of-world-average-build.py
Requires Python 3 with numpy, matplotlib and Pillow.
"""
# ------------------------------------------------------------------ provenance
# Embedded data, frozen 29 August 2026 from the chart csv of the replication
# bundle for "If the World Were a Country, It Would Be a Very Strange One"
# (https://movingfrontiers.substack.com/p/the-world-turns-rich-this-year).
# Upstream sources: World Bank OGHIST classification and income thresholds,
# release of 1 July 2026; World Bank WDI, GNI per capita, Atlas method
# (NY.GNP.PCAP.CD) and population (SP.POP.TOTL), July 2026 release; UN World
# Population Prospects 2024, medium variant.
# Values for 2026 onward are not raw source data: they are the author's
# nowcast and projection (conservative constant-pace scenario), carried from
# the projection workbook into the bundle csv and frozen here.
# Do not replace the embedded table with a live download or API call: the
# output is pinned to this vintage and must keep running offline.
# The shared helper functions and the caption texts are duplicated verbatim
# across the five chart scripts of this folder; the duplication is deliberate
# so each file stays single-file self-sufficient.
# The caption's world GNI per capita of $14,801 is derived upstream and cannot
# be recomputed from the ratios embedded here; the 8.14 billion population
# total can be, and is asserted below.
import os
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

RED='#C62828'; AMBER='#F9A825'; AMBERTXT='#B8860B'; INDIGO='#283593'; INK='#141414'

SRC=("Source: World Bank OGHIST classification and income thresholds, 1 July 2026; GNI per capita, Atlas method, and population from "
"World Bank WDI, July 2026 release; UN World Population Prospects 2024, medium variant; author's calculations and projections. "
"Schellekens 2026, The Great Income Inversion, Moving Frontiers." + chr(10))
PROJ=("Note: Values are for 2026, which reflects a nowcast based on a conservative constant-pace scenario that replicates country-level "
"median per capita income growth over the last decade. See Schellekens 2026 for methodology. ")
CAVEAT=("World GNI per capita is world GNI divided by world population, $14,801 in 2026, covering 8.14 billion people. Every person "
"carries their own country's average, so this is inequality between countries, not within them. ")

def frame(figsize):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':13,'axes.edgecolor':'#888',
     'axes.linewidth':1.0,'figure.facecolor':'white','xtick.labelsize':10,'ytick.labelsize':10})
    fig,ax=plt.subplots(figsize=figsize,dpi=200)
    ax.grid(axis='y',color='#E8E8E8',lw=0.8,zorder=0); ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    return fig,ax

# ---------------------------------------------------------------- shared helpers
def caption(fig, ax, cap, fs, url_on_last_line, gap_lines=2.0, use_xlabel=False):
    """Moving Frontiers caption block. The watermark either sits on the baseline of
    the last note line, or on its own line below it."""
    fig.canvas.draw(); r=fig.canvas.get_renderer()
    Wpx=fig.get_figwidth()*fig.dpi
    bots=[t.get_window_extent(r).y0 for t in ax.get_xticklabels() if t.get_text()]
    if use_xlabel and ax.xaxis.label.get_text():
        bots.append(ax.xaxis.label.get_window_extent(r).y0)
    xb=fig.transFigure.inverted().transform((0,min(bots)))[1]
    for lg in fig.legends:
        lb=lg.get_window_extent(r).transformed(fig.transFigure.inverted())
        if lb.y1<xb: xb=min(xb,lb.y0)
    LH=fs*1.2/(72*fig.get_figheight())
    pr=fig.text(0,0,'0',fontsize=fs); fig.canvas.draw()
    CW=pr.get_window_extent(fig.canvas.get_renderer()).width/Wpx; pr.remove()
    def w(t,size=fs):
        tt=fig.text(0,0,t,fontsize=size); fig.canvas.draw()
        v=tt.get_window_extent(fig.canvas.get_renderer()).width/Wpx; tt.remove(); return v
    URL='movingfrontiers.substack.com'; UFS=fs*1.2
    x0=0.012; right=1.0-70.0/Wpx
    full=right-x0
    lastmax=right-w(URL,UFS)-2.0*CW-x0 if url_on_last_line else full
    lines=[]
    for para in cap.split(chr(10)):
        cur=''
        for word in para.split():
            z=(cur+' '+word).strip()
            if w(z)<=full or not cur: cur=z
            else: lines.append(cur); cur=word
        lines.append(cur)
    if url_on_last_line:
        for _ in range(400):
            if w(lines[-1])>lastmax and ' ' in lines[-1]:
                h,_,t=lines[-1].rpartition(' '); lines[-1]=h; lines.append(t); continue
            if len(lines)>=2 and w(lines[-2])>lastmax and ' ' in lines[-2]:
                h,_,t=lines[-2].rpartition(' ')
                lines[-2]=h; lines[-1]=(t+' '+lines[-1]).strip(); continue
            break
        if len(lines)>=2:
            while ' ' in lines[-2]:
                h,_,t=lines[-2].rpartition(' ')
                cand=(t+' '+lines[-1]).strip()
                if w(cand)>lastmax: break
                if abs(w(cand)-w(h))>=abs(w(lines[-1])-w(lines[-2])): break
                lines[-2]=h; lines[-1]=cand
    top=xb-gap_lines*LH
    objs=[fig.text(x0,top-i*LH,ln,fontsize=fs,color='#666',va='top') for i,ln in enumerate(lines)]
    fig.canvas.draw(); r2=fig.canvas.get_renderer()
    lb=objs[-1].get_window_extent(r2).transformed(fig.transFigure.inverted())
    if url_on_last_line:
        fig.text(right,lb.y0,URL,ha='right',va='bottom',fontsize=UFS,color='#999')
        assert lb.y0>0.004,'caption runs off the canvas'
    else:
        fig.text(right,lb.y0-0.45*LH,URL,ha='right',va='top',fontsize=UFS,color='#999')
        assert lb.y0-0.45*LH>0.004,'caption runs off the canvas'
    print('  caption %d lines'%len(lines))

def title_band(path, title, sub, title_frac, sub_frac):
    """Composite the title and subtitle above the rendered figure with PIL, after
    cropping the figure to its ink, so a two-line title never squeezes the plot."""
    _ttf=os.path.join(matplotlib.get_data_path(),'fonts','ttf')
    FB=os.path.join(_ttf,'DejaVuSans-Bold.ttf')
    FR=os.path.join(_ttf,'DejaVuSans.ttf')
    if not os.path.isfile(FB): FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    if not os.path.isfile(FR): FR='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    assert os.path.isfile(FB) and os.path.isfile(FR), 'DejaVu Sans fonts not found in the matplotlib bundle or the system path'
    im=Image.open(path).convert('RGB')
    a=np.array(im.convert('L')); rr=np.where((a<250).sum(axis=1)>0)[0]
    im=im.crop((0,0,im.size[0],min(im.size[1],int(rr.max())+10)))
    W,H=im.size
    fs=int(W*title_frac); f1=ImageFont.truetype(FB,fs)
    fss=int(W*sub_frac);  f2=ImageFont.truetype(FR,fss)
    dd=ImageDraw.Draw(im); M=int(W*0.03); LIM=W-2*M
    def wrap(t,f):
        o=[];cur=''
        for x in t.split():
            z=(cur+' '+x).strip()
            if dd.textlength(z,font=f)<=LIM: cur=z
            else: o.append(cur); cur=x
        o.append(cur); return o
    tl=wrap(title,f1); sl=wrap(sub,f2)
    lh=int(fs*1.25); lhs=int(fss*1.35)
    bh=int(fs*0.85)+lh*len(tl)+int(fss*0.55)+lhs*len(sl)+int(fs*0.22)
    cv=Image.new('RGB',(W,H+bh),'white'); cv.paste(im,(0,bh))
    dr=ImageDraw.Draw(cv); y=int(fs*0.85)
    for ln in tl: dr.text((M,y),ln,font=f1,fill=(45,45,45)); y+=lh
    y+=int(fss*0.4)
    for ln in sl: dr.text((M,y),ln,font=f2,fill=(100,100,100)); y+=lhs
    cv.save(path,optimize=True)
    print('  wrote %s  %dx%d'%(path,cv.size[0],cv.size[1]))

# --------------------------------------------- embedded data (see provenance)
DATA=(  # (economy, ratio_to_world_average, population_millions), csv row order = rank poorest to richest,
       # on which np.argsort ties and the name-index lookups depend
('Burundi',0.0164,14.729),
('Afghanistan',0.0267,45.047),
('Madagascar',0.039,33.522),
('Central African Republic',0.0391,5.699),
('Mozambique',0.0393,36.64),
('Malawi',0.0413,22.786),
('Somalia, Fed. Rep.',0.0447,20.306),
('Congo, Dem. Rep.',0.0508,116.452),
('Niger',0.052,28.815),
('Sierra Leone',0.0568,8.997),
('Liberia',0.0579,5.854),
('Sudan',0.0616,53.283),
('Gambia, The',0.0662,2.884),
('Chad',0.0664,21.56),
('Burkina Faso',0.0679,24.602),
('Mali',0.0776,25.932),
('Guinea-Bissau',0.0777,2.298),
('Uganda',0.0789,52.761),
('Ethiopia',0.0792,138.902),
('Rwanda',0.082,14.89),
('Zambia',0.0821,22.522),
('Lesotho',0.0876,2.389),
('Tanzania',0.0879,72.564),
('Myanmar',0.0903,55.185),
('Nigeria',0.093,242.432),
('Togo',0.0951,8.777),
('Timor-Leste',0.1033,1.437),
('Pakistan',0.1057,259.3),
('Nepal',0.112,29.629),
('Benin',0.1121,15.17),
('Senegal',0.1231,19.367),
('Guinea',0.1256,15.442),
('Cameroon',0.1281,30.641),
('Comoros',0.1352,0.899),
('Solomon Islands',0.1382,0.858),
('Haiti',0.1384,12.038),
('Tajikistan',0.1461,10.979),
('Lao PDR',0.1479,7.974),
('Mauritania',0.1546,5.461),
('Congo, Rep.',0.1561,6.638),
('Kenya',0.1569,58.636),
('Ghana',0.1828,35.698),
('Zimbabwe',0.1931,17.274),
('Angola',0.1956,40.215),
("Côte d'Ivoire",0.1957,33.494),
('Papua New Guinea',0.1977,10.948),
('India',0.1985,1476.626),
('Cambodia',0.1997,18.051),
('Nicaragua',0.2003,7.097),
('Kyrgyz Republic',0.2033,7.449),
('Bangladesh',0.2062,177.818),
('Egypt, Arab Rep.',0.223,120.101),
('West Bank and Gaza',0.2273,5.514),
('Honduras',0.233,11.185),
('Lebanon',0.2435,5.897),
('Eswatini',0.2565,1.27),
('Uzbekistan',0.2626,37.724),
('Venezuela, RB',0.264,28.634),
('São Tomé and Príncipe',0.2759,0.245),
('Kiribati',0.2772,0.138),
('Djibouti',0.2834,1.199),
('Tunisia',0.2941,12.415),
('Namibia',0.2969,3.153),
('Morocco',0.3006,38.762),
('Bhutan',0.308,0.802),
('Vanuatu',0.313,0.343),
('Bolivia',0.3154,12.749),
('Iran, Islamic Rep.',0.3181,93.168),
('Sri Lanka',0.3244,21.867),
('Micronesia, Fed. Sts.',0.3313,0.114),
('Philippines',0.3426,117.724),
('Viet Nam',0.3578,102.177),
('Indonesia',0.3625,287.887),
('Jordan',0.3636,11.59),
('El Salvador',0.3829,6.391),
('Iraq',0.3892,48.007),
('Samoa',0.3949,0.221),
('Ukraine',0.397,39.536),
('Algeria',0.4015,48.028),
('Equatorial Guinea',0.4029,1.984),
('Cabo Verde',0.4034,0.53),
('Suriname',0.4229,0.645),
('South Africa',0.4289,65.453),
('Turkmenistan',0.4337,7.737),
('Fiji',0.4348,0.937),
('Mongolia',0.4502,3.609),
('Guatemala',0.4544,18.968),
('Paraguay',0.4663,7.095),
('Ecuador',0.4735,18.445),
('Tonga',0.4832,0.103),
('Libya',0.4959,7.54),
('Botswana',0.5139,2.603),
('Azerbaijan',0.5218,10.303),
('Belize',0.5252,0.429),
('Thailand',0.5311,71.56),
('Colombia',0.5561,53.936),
('Jamaica',0.5579,2.833),
('Gabon',0.5613,2.647),
('Kosovo',0.5715,1.57),
('Moldova',0.5932,2.333),
('Peru',0.6014,34.922),
('Georgia',0.6625,3.934),
('Belarus',0.6636,9.025),
('Armenia',0.6647,3.064),
('North Macedonia',0.6805,1.811),
('Tuvalu',0.6834,0.009),
('Marshall Islands',0.6951,0.035),
('Bosnia and Herzegovina',0.7234,3.114),
('Brazil',0.733,213.563),
('Dominican Republic',0.7551,11.61),
('Dominica',0.7602,0.066),
('Grenada',0.8382,0.117),
('Malaysia',0.8563,36.385),
('St. Vincent and the Grenadines',0.8604,0.099),
('Albania',0.8887,2.332),
('Maldives',0.9362,0.532),
('St. Lucia',0.9611,0.18),
('Mexico',0.972,132.998),
('Kazakhstan',0.9788,21.084),
('Mauritius',0.9853,1.241),
('Serbia',0.9934,6.503),
('China',1.0096,1403.424),
('Montenegro',1.0427,0.617),
('Argentina',1.0515,46.004),
('Türkiye',1.1255,86.114),
('Russian Federation',1.1556,142.912),
('Chile',1.1754,19.946),
('Trinidad and Tobago',1.2689,1.37),
('Costa Rica',1.2737,5.175),
('Bulgaria',1.2874,6.388),
('Panama',1.3562,4.626),
('Oman',1.3654,5.671),
('Seychelles',1.3756,0.125),
('Palau',1.391,0.018),
('Romania',1.4619,18.912),
('Nauru',1.4926,0.012),
('Curaçao',1.5742,0.156),
('French Polynesia',1.6485,0.283),
('Hungary',1.7016,9.468),
('Uruguay',1.702,3.383),
('Antigua and Barbuda',1.7128,0.095),
('St. Kitts and Nevis',1.7333,0.047),
('Latvia',1.7613,1.83),
('Greece',1.7618,10.37),
('Croatia',1.8362,3.85),
('Poland',1.8478,36.151),
('Slovak Republic',1.855,5.391),
('Barbados',1.879,0.283),
('Puerto Rico (U.S.)',1.9106,3.172),
('Bahrain',1.972,1.632),
('Guyana',2.0435,0.841),
('Portugal',2.1007,10.788),
('Lithuania',2.2084,2.855),
('Estonia',2.2764,1.353),
('Czechia',2.3559,10.803),
('Brunei Darussalam',2.3797,0.47),
('Saudi Arabia',2.482,37.615),
('Aruba',2.4988,0.109),
('Slovenia',2.5116,2.128),
('Cyprus',2.5148,1.382),
('Spain',2.5733,49.315),
('Bahamas, The',2.604,0.405),
('Japan',2.6226,122.69),
('Korea, Rep.',2.6376,51.618),
('Turks and Caicos Islands',2.656,0.047),
('Sint Maarten (Dutch part)',2.7241,0.044),
('Italy',2.8784,58.696),
('Kuwait',2.9306,4.94),
('Malta',2.9419,0.584),
('New Zealand',3.1896,5.361),
('France',3.3404,68.819),
('United Arab Emirates',3.6447,11.745),
('United Kingdom',3.7314,69.867),
('Finland',3.7806,5.645),
('Canada',3.9209,42.006),
('Israel',3.9622,10.262),
('Germany',4.1412,83.063),
('Austria',4.1545,9.202),
('Belgium',4.1553,11.958),
('Sweden',4.3101,10.641),
('Hong Kong SAR, China',4.4121,7.481),
('Australia',4.448,27.873),
('Netherlands',4.7209,18.188),
('Macao SAR, China',4.9838,0.687),
('Faeroe Islands',5.0016,0.055),
('Qatar',5.0844,3.027),
('Denmark',5.3141,6.03),
('Singapore',5.7159,6.148),
('Cayman Islands',5.9315,0.077),
('Isle of Man',5.9531,0.084),
('Ireland',6.1234,5.535),
('United States',6.2445,343.517),
('Iceland',6.46,0.396),
('Luxembourg',6.5909,0.694),
('Norway',6.6563,5.641),
('Switzerland',7.5469,9.133),
('Bermuda',9.7232,0.064),
)
nm=[t[0] for t in DATA]
r_=np.array([t[1] for t in DATA])
pop=np.array([t[2] for t in DATA])
o=np.argsort(r_)
assert len(DATA)==197, 'y-axis label: "197 economies, ranked poorest to richest"'
_bur=r_[nm.index('Burundi')]; _ber=r_[nm.index('Bermuda')]
assert round(float(_bur),3)==0.016, 'caption: "Burundi at 0.016 times the world average"'
assert round(float(_ber),1)==9.7, 'caption: "Bermuda at 9.7 times"'
assert round(float(_ber/_bur),-2)==600, 'title and caption: "A 600-fold range, from Burundi to Bermuda"'
assert round(float(pop.sum())/1000,2)==8.14, 'caption: "covering 8.14 billion people"'
XM=np.log10(1450)-1.0
def area(pm):
    if pm<10: return 10.0
    return 10+((np.log10(pm)-1.0)/XM)**3.4*2200
r=r_
fig,ax=frame((6.8,8.6))
fig.tight_layout(rect=[0.02,0.335,0.99,0.985])
ax.axvspan(1e-3,1,color=RED,alpha=0.07,zorder=0)
ax.axvline(1,ls='--',lw=1.8,color=INK,zorder=4)
yv=np.arange(len(o))
sz=np.array([area(p) for p in pop[o]])
col=[RED if x<1 else INDIGO for x in r[o]]
ax.scatter(r[o],yv,s=sz,c=col,alpha=0.55,edgecolors='white',linewidths=0.6,zorder=5)
ax.set_xscale('log'); ax.set_xlim(0.011,26); ax.set_ylim(-10,len(o)+22)
ax.set_yticks([])
ticks=[0.02,0.05,0.1,0.25,0.5,1,2,4,10]
ax.set_xticks(ticks); ax.set_xticklabels(['0.02x','0.05x','0.1x','0.25x','0.5x','1x'+chr(10)+'world'+chr(10)+'average','2x','4x','10x'])
ax.minorticks_off()
ax.grid(axis='x',color='#E8E8E8',lw=0.8,zorder=0); ax.grid(axis='y',visible=False)
ax.spines['left'].set_visible(False)
fig.canvas.draw(); REN=fig.canvas.get_renderer()
CX,CY=ax.transData.transform(np.column_stack([r[o],yv])).T
RAD=np.sqrt(sz/np.pi)*fig.dpi/72.0
placed=[]
def clear(bb,skip_row):
    for i,(cx,cy,rad) in enumerate(zip(CX,CY,RAD)):
        if i==skip_row: continue
        nx=min(max(cx,bb.x0),bb.x1); ny=min(max(cy,bb.y0),bb.y1)
        if (nx-cx)**2+(ny-cy)**2 < (rad+2.0)**2: return False
    for pb in placed:
        if bb.x0<pb.x1+3 and pb.x0<bb.x1+3 and bb.y0<pb.y1+3 and pb.y0<bb.y1+3: return False
    ab=ax.get_window_extent(REN)
    if bb.x0<ab.x0+2 or bb.x1>ab.x1-2 or bb.y0<ab.y0+2 or bb.y1>ab.y1-2: return False
    return True
def lbl(name,prefer='left',fixed=None,vert=False,two=False):
    i=[k for k,x in enumerate(nm) if x==name]
    if not i: return
    i=i[0]; row=list(o).index(i)
    txt='%s  %.2fx'%(name,r[i])
    if two: txt='%s  %.2fx'%(name,r[i])+chr(10)+('poorest' if r[i]<1 else 'richest')
    c=RED if r[i]<1 else INDIGO
    inv=ax.transData.inverted()
    if fixed is not None:
        ha,dx,dy=fixed
        t=ax.text(r[i]*dx,row+dy,txt,fontsize=8.6,fontweight='bold',color=c,ha=ha,va='center',zorder=10)
        fig.canvas.draw(); bb=t.get_window_extent(REN); placed.append(bb)
        cx,cy,rad=CX[row],CY[row],RAD[row]
        if vert:
            lx=(bb.x0+bb.x1)/2; ye=bb.y1 if dy<0 else bb.y0
            (a0,b0)=inv.transform((lx,cy-rad-1.5 if dy<0 else cy+rad+1.5)); (a1,b1)=inv.transform((lx,ye))
            ax.plot([a0,a1],[b0,b1],color=c,lw=0.55,alpha=0.9,zorder=8)
        else:
            px=min(max(cx,bb.x0),bb.x1); py=min(max(cy,bb.y0),bb.y1)
            d=np.hypot(px-cx,py-cy)
            if d>rad+3:
                ux,uy=(px-cx)/d,(py-cy)/d
                (a0,b0)=inv.transform((cx+ux*(rad+1.5),cy+uy*(rad+1.5)))
                (a1,b1)=inv.transform((px-ux*1.5,py-uy*1.5))
                ax.plot([a0,a1],[b0,b1],color=c,lw=0.55,alpha=0.9,zorder=8)
        return
    sides=[('right',0.62),('left',1.6),('right',0.42),('left',2.3),('right',0.30),('left',3.2)]
    if prefer=='right': sides=[s for s in sides if s[0]=='left']+[s for s in sides if s[0]=='right']
    best=None
    for dy in (0,10,-10,20,-20,30,-30,42,-42,56,-56,72):
        for ha,dx in sides:
            t=ax.text(r[i]*dx,row+dy,txt,fontsize=8.6,fontweight='bold',color=c,ha=ha,va='center',zorder=10)
            fig.canvas.draw(); bb=t.get_window_extent(REN)
            if clear(bb,row): best=(t,bb,ha,dx,dy); break
            t.remove()
        if best: break
    if best is None:
        t=ax.text(r[i]*0.62,row,txt,fontsize=8.6,fontweight='bold',color=c,ha='right',va='center',zorder=10)
        fig.canvas.draw(); best=(t,t.get_window_extent(REN),'right',0.62,0)
        print('   !! no clear slot for',name)
    t,bb,ha,dx,dy=best; placed.append(bb)
    cx,cy,rad=CX[row],CY[row],RAD[row]
    px=min(max(cx,bb.x0),bb.x1); py=min(max(cy,bb.y0),bb.y1)
    d=np.hypot(px-cx,py-cy)
    if d>rad+3:
        ux,uy=(px-cx)/d,(py-cy)/d
        (dx0,dy0)=inv.transform((cx+ux*(rad+1.5),cy+uy*(rad+1.5)))
        (dx1,dy1)=inv.transform((px-ux*1.5,py-uy*1.5))
        ax.plot([dx0,dx1],[dy0,dy1],color=c,lw=0.55,alpha=0.9,zorder=8)
US_ROW=list(o).index([k for k,x in enumerate(nm) if x=='United States'][0])
BM_ROW=list(o).index([k for k,x in enumerate(nm) if x=='Bermuda'][0])
lbl('Bermuda',fixed=('center',1.0,-(BM_ROW-US_ROW)-22),vert=True,two=True)
lbl('United States')
lbl('China',fixed=('right',0.50,0))
lbl('India',fixed=('left',1.95,0))
lbl('Nigeria',fixed=('left',1.52,0))
lbl('Burundi',fixed=('center',1.0,17),vert=True,two=True)
LEG=[(1400,'1.4 bn'),(250,'250 m'),(50,'50 m')]
lx=10.0; legrows=[70,34,16]
ax.text(lx*0.60,legrows[0]+26,'Population',fontsize=8.8,fontweight='bold',color='#555',ha='left',va='center')
for (pv,plab),ry in zip(LEG,legrows):
    a=area(pv)
    ax.scatter([lx],[ry],s=a,c='#BBBBBB',alpha=0.75,edgecolors='white',linewidths=0.6,zorder=5)
    x_pt=ax.transData.transform((lx,ry))[0]+np.sqrt(a/np.pi)*fig.dpi/72.0+6
    ax.text(ax.transData.inverted().transform((x_pt,0))[0],ry,plab,fontsize=8.2,color='#555',ha='left',va='center')
ax.set_xlabel('GNI per capita as a multiple of world GNI per capita, log scale',fontsize=10.5)
ax.set_ylabel('197 economies, ranked poorest to richest',fontsize=10.5)
caption(fig,ax,SRC+PROJ+CAVEAT+("Each bubble is one economy, positioned by its GNI per capita relative to the world average and "
 "ranked from poorest at the bottom to richest at the top. Bubble area follows a logarithmic population scale; economies under ten "
 "million people are drawn at a fixed minimum size. Burundi at 0.016 times the world average and Bermuda at 9.7 times span a 600-fold "
 "range."),7.6,url_on_last_line=False,gap_lines=0.85,use_xlabel=True)
fig.savefig('chart-5-economies-by-multiple-of-world-average.png',dpi=200); plt.close(fig)
title_band('chart-5-economies-by-multiple-of-world-average.png','A 600-fold range, from Burundi to Bermuda',
 'Every economy as a multiple of world GNI per capita, bubble area on a log population scale, 2026',0.0285,0.0168)
