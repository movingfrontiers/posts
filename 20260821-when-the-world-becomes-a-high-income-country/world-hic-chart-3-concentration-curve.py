"""Chart 3: concentration curve of world GNI across people.

Self-sufficient: the data this chart consumes are embedded below, frozen at the
July 2026 vintage. No external files, downloads or network access. Writes the png
of the same name. Run from any directory:  python3 chart-3-concentration-curve-build.py
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
# The caption's world GNI per capita of $14,801 is derived upstream (world GNI
# over world population) and cannot be recomputed from the shares embedded
# here; the 8.14 billion population total can be, and is asserted below.
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
DATA=(  # (cum_pop_share_pct, cum_gni_share_pct, population_millions, at_or_below_world_average), csv row order = rank poorest to richest
(0.181,0.003,14.729,True),
(0.7346,0.0177,45.047,True),
(1.1466,0.0338,33.522,True),
(1.2166,0.0365,5.699,True),
(1.6669,0.0542,36.64,True),
(1.9469,0.0658,22.786,True),
(2.1965,0.0769,20.306,True),
(3.6276,0.1496,116.452,True),
(3.9818,0.1681,28.815,True),
(4.0923,0.1743,8.997,True),
(4.1643,0.1785,5.854,True),
(4.8191,0.2188,53.283,True),
(4.8545,0.2212,2.884,True),
(5.1195,0.2387,21.56,True),
(5.4218,0.2593,24.602,True),
(5.7405,0.284,25.932,True),
(5.7688,0.2862,2.298,True),
(6.4172,0.3373,52.761,True),
(8.1242,0.4725,138.902,True),
(8.3072,0.4875,14.89,True),
(8.584,0.5103,22.522,True),
(8.6134,0.5128,2.389,True),
(9.5051,0.5912,72.564,True),
(10.1833,0.6525,55.185,True),
(13.1627,0.9296,242.432,True),
(13.2706,0.9399,8.777,True),
(13.2882,0.9417,1.437,True),
(16.4749,1.2785,259.3,True),
(16.839,1.3192,29.629,True),
(17.0255,1.3401,15.17,True),
(17.2635,1.3694,19.367,True),
(17.4533,1.3933,15.442,True),
(17.8298,1.4415,30.641,True),
(17.8409,1.443,0.899,True),
(17.8514,1.4444,0.858,True),
(17.9994,1.4649,12.038,True),
(18.1343,1.4846,10.979,True),
(18.2323,1.4991,7.974,True),
(18.2994,1.5095,5.461,True),
(18.381,1.5222,6.638,True),
(19.1016,1.6353,58.636,True),
(19.5403,1.7155,35.698,True),
(19.7526,1.7565,17.274,True),
(20.2468,1.8532,40.215,True),
(20.6584,1.9337,33.494,True),
(20.793,1.9603,10.948,True),
(38.94,5.5622,1476.626,True),
(39.1619,5.6065,18.051,True),
(39.2491,5.6239,7.097,True),
(39.3406,5.6425,7.449,True),
(41.5259,6.0932,177.818,True),
(43.0019,6.4223,120.101,True),
(43.0697,6.4377,5.514,True),
(43.2071,6.4697,11.185,True),
(43.2796,6.4874,5.897,True),
(43.2952,6.4914,1.27,True),
(43.7588,6.6131,37.724,True),
(44.1107,6.706,28.634,True),
(44.1137,6.7069,0.245,True),
(44.1154,6.7073,0.138,True),
(44.1302,6.7115,1.199,True),
(44.2828,6.7564,12.415,True),
(44.3215,6.7679,3.153,True),
(44.7979,6.9111,38.762,True),
(44.8077,6.9141,0.802,True),
(44.8119,6.9155,0.343,True),
(44.9686,6.9649,12.749,True),
(46.1136,7.3291,93.168,True),
(46.3824,7.4163,21.867,True),
(46.3838,7.4167,0.114,True),
(47.8305,7.9124,117.724,True),
(49.0863,8.3617,102.177,True),
(52.6243,9.6442,287.887,True),
(52.7667,9.696,11.59,True),
(52.8452,9.726,6.391,True),
(53.4352,9.9557,48.007,True),
(53.4379,9.9567,0.221,True),
(53.9238,10.1496,39.536,True),
(54.5141,10.3866,48.028,True),
(54.5384,10.3964,1.984,True),
(54.545,10.3991,0.53,True),
(54.5529,10.4024,0.645,True),
(55.3573,10.7474,65.453,True),
(55.4523,10.7886,7.737,True),
(55.4639,10.7936,0.937,True),
(55.5082,10.8136,3.609,True),
(55.7413,10.9196,18.968,True),
(55.8285,10.9602,7.095,True),
(56.0552,11.0675,18.445,True),
(56.0565,11.0682,0.103,True),
(56.1491,11.1141,7.54,True),
(56.1811,11.1306,2.603,True),
(56.3078,11.1966,10.303,True),
(56.313,11.1994,0.429,True),
(57.1925,11.6664,71.56,True),
(57.8553,12.035,53.936,True),
(57.8901,12.0545,2.833,True),
(57.9227,12.0727,2.647,True),
(57.942,12.0838,1.57,True),
(57.9706,12.1008,2.333,True),
(58.3998,12.3589,34.922,True),
(58.4482,12.3909,3.934,True),
(58.5591,12.4645,9.025,True),
(58.5967,12.4895,3.064,True),
(58.619,12.5047,1.811,True),
(58.6191,12.5048,0.009,True),
(58.6195,12.5051,0.035,True),
(58.6578,12.5327,3.114,True),
(61.2824,14.4566,213.563,True),
(61.4251,14.5644,11.61,True),
(61.4259,14.565,0.066,True),
(61.4273,14.5662,0.117,True),
(61.8745,14.9491,36.385,True),
(61.8757,14.9501,0.099,True),
(61.9043,14.9756,2.332,True),
(61.9109,14.9817,0.532,True),
(61.9131,14.9838,0.18,True),
(63.5476,16.5725,132.998,True),
(63.8067,16.8261,21.084,True),
(63.8219,16.8412,1.241,True),
(63.9018,16.9205,6.503,True),
(81.1493,34.3336,1403.424,False),
(81.1569,34.3415,0.617,False),
(81.7222,34.936,46.004,False),
(82.7805,36.1272,86.114,False),
(84.5369,38.1568,142.912,False),
(84.782,38.4449,19.946,False),
(84.7988,38.4663,1.37,False),
(84.8624,38.5473,5.175,False),
(84.9409,38.6483,6.388,False),
(84.9978,38.7254,4.626,False),
(85.0675,38.8206,5.671,False),
(85.069,38.8227,0.125,False),
(85.0692,38.823,0.018,False),
(85.3016,39.1628,18.912,False),
(85.3018,39.163,0.012,False),
(85.3037,39.166,0.156,False),
(85.3072,39.1717,0.283,False),
(85.4235,39.3697,9.468,False),
(85.4651,39.4405,3.383,False),
(85.4663,39.4425,0.095,False),
(85.4669,39.4435,0.047,False),
(85.4894,39.4831,1.83,False),
(85.6168,39.7076,10.37,False),
(85.6641,39.7945,3.85,False),
(86.1084,40.6155,36.151,False),
(86.1746,40.7383,5.391,False),
(86.1781,40.7449,0.283,False),
(86.2171,40.8194,3.172,False),
(86.2372,40.8589,1.632,False),
(86.2475,40.88,0.841,False),
(86.3801,41.1585,10.788,False),
(86.4152,41.236,2.855,False),
(86.4318,41.2739,1.353,False),
(86.5646,41.5867,10.803,False),
(86.5703,41.6004,0.47,False),
(87.0326,42.7478,37.615,False),
(87.0339,42.7511,0.109,False),
(87.0601,42.8168,2.128,False),
(87.0771,42.8595,1.382,False),
(87.6831,44.4191,49.315,False),
(87.6881,44.4321,0.405,False),
(89.1959,48.3863,122.69,False),
(89.8303,50.0595,51.618,False),
(89.8308,50.061,0.047,False),
(89.8314,50.0625,0.044,False),
(90.5527,52.1388,58.696,False),
(90.6135,52.3168,4.94,False),
(90.6206,52.3379,0.584,False),
(90.6865,52.548,5.361,False),
(91.5323,55.3731,68.819,False),
(91.6766,55.8992,11.745,False),
(92.5352,59.1031,69.867,False),
(92.6046,59.3654,5.645,False),
(93.1208,61.3894,42.006,False),
(93.2469,61.8891,10.262,False),
(94.2678,66.1165,83.063,False),
(94.3808,66.5864,9.202,False),
(94.5278,67.197,11.958,False),
(94.6586,67.7606,10.641,False),
(94.7505,68.1663,7.481,False),
(95.0931,69.69,27.873,False),
(95.3166,70.7452,18.188,False),
(95.325,70.7873,0.687,False),
(95.3257,70.7907,0.055,False),
(95.3629,70.9799,3.027,False),
(95.437,71.3737,6.03,False),
(95.5126,71.8055,6.148,False),
(95.5135,71.8112,0.077,False),
(95.5146,71.8173,0.084,False),
(95.5826,72.2338,5.535,False),
(99.8042,98.5961,343.517,False),
(99.8091,98.6276,0.396,False),
(99.8176,98.6838,0.694,False),
(99.887,99.1452,5.641,False),
(99.9992,99.9923,9.133,False),
(100.0,100.0,0.064,False),
)
cw=np.array([0.0]+[t[0] for t in DATA])
cg=np.array([0.0]+[t[1] for t in DATA])
pop=np.array([t[2] for t in DATA])
below=np.array([t[3] for t in DATA])
P=100*pop[below].sum()/pop.sum()
assert round(float(P))==64, 'caption: "64 percent of people live in an economy poorer than the world average"'
assert round(float(np.interp(P,cw,cg)))==17, 'caption: "those economies together hold 17 percent of world GNI"'
assert round(float(np.interp(50,cw,cg)))==9, 'title: "half of humanity lives on nine percent of world income"'
assert round(float(pop.sum())/1000,2)==8.14, 'caption: "covering 8.14 billion people"'
fig,ax=frame((7.6,6.4))
fig.tight_layout(rect=[0.02,0.300,0.99,0.985])
ax.plot([0,100],[0,100],ls='--',lw=1.4,color='#999',zorder=2)
ax.fill_between(cw,cg,cw,color=INDIGO,alpha=0.13,zorder=1)
ax.plot(cw,cg,color=INDIGO,lw=3.2,zorder=5,solid_capstyle='round')
ax.plot([P,P],[0,np.interp(P,cw,cg)],ls=':',lw=1.6,color=RED,zorder=4)
ax.plot([P],[np.interp(P,cw,cg)],'o',mfc='white',mec=RED,mew=2.6,ms=11,zorder=9,clip_on=False)
def note(mx,my,lx,ly,txt,col,ha):
    ax.plot([mx],[my],'o',mfc='white',mec=col,mew=2.4,ms=9,zorder=9)
    t=ax.text(lx,ly,txt,fontsize=9.5,fontweight='bold',color=col,ha=ha,va='center',linespacing=1.3,zorder=10)
    fig.canvas.draw()
    bb=t.get_window_extent(fig.canvas.get_renderer()); inv=ax.transData.inverted()
    (x0,y0)=inv.transform((bb.x0,bb.y0)); (x1,y1)=inv.transform((bb.x1,bb.y1))
    ax.plot([mx,(x0+x1)/2],[my,(y0 if my<(y0+y1)/2 else y1)],color=col,lw=1.1,zorder=8)
note(50,np.interp(50,cw,cg),34,26,'Poorest half:'+chr(10)+'%.0f%% of world GNI'%np.interp(50,cw,cg),INDIGO,'left')
note(P,np.interp(P,cw,cg),56,39,'World average sits at'+chr(10)+'the %.0fth percentile'%P,RED,'left')
note(90,np.interp(90,cw,cg),87.5,66,'Richest tenth:'+chr(10)+'%.0f%% of GNI'%(100-np.interp(90,cw,cg)),INDIGO,'right')
ax.set_xlim(0,100); ax.set_ylim(0,100)
ax.set_xticks(range(0,101,20)); ax.set_yticks(range(0,101,20))
ax.set_xlabel('Cumulative share of world population, percent',fontsize=10.5)
ax.set_ylabel('Cumulative share of world GNI, percent',fontsize=10.5)
ax.grid(axis='x',color='#E8E8E8',lw=0.8,zorder=0)
caption(fig,ax,SRC+PROJ+CAVEAT+("Economies are ranked from poorest to richest; the curve accumulates their population and "
 "their GNI. The dashed diagonal is the line of equal income per person everywhere. The marked point is where world GNI per capita "
 "falls in the ranked distribution: 64 percent of people live in an economy poorer than the world average, and those economies "
 "together hold 17 percent of world GNI."),7.6,url_on_last_line=False,gap_lines=0.85,use_xlabel=True)
fig.savefig('chart-3-concentration-curve.png',dpi=200); plt.close(fig)
title_band('chart-3-concentration-curve.png','Between countries, half of humanity lives on nine percent of world income',
 'Cumulative share of world GNI against cumulative share of world population, economies ranked by GNI per '
 'capita, 2026; every person carries their country average, so inequality within countries is not shown',0.0285,0.0168)
