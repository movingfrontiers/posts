"""Chart 2: mean-to-median ratio.

Self-sufficient: the data this chart consumes are embedded below, frozen at the
July 2026 vintage. No external files, downloads or network access. Writes the png
of the same name. Run from any directory:  python3 chart-2-mean-to-median-ratio-build.py
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
DATA=(  # (year, mean_to_median_ratio), csv row order
(1987,10.083),
(1988,10.7058),
(1989,11.16),
(1990,11.5014),
(1991,12.6566),
(1992,11.9764),
(1993,11.5489),
(1994,10.753),
(1995,9.9374),
(1996,8.5268),
(1997,7.4726),
(1998,6.7814),
(1999,6.3057),
(2000,5.9045),
(2001,5.4743),
(2002,4.8877),
(2003,4.5583),
(2004,4.4152),
(2005,4.1839),
(2006,3.8185),
(2007,3.3354),
(2008,2.8481),
(2009,2.4015),
(2010,2.1357),
(2011,2.0437),
(2012,1.9407),
(2013,1.9439),
(2014,1.9487),
(2015,2.0071),
(2016,2.4765),
(2017,2.5359),
(2018,2.6556),
(2019,2.7498),
(2020,2.897),
(2021,2.97),
(2022,2.8901),
(2023,2.7934),
(2024,2.751),
(2025,2.802),
(2026,2.7588),
(2027,2.7175),
(2028,2.6774),
(2029,2.6386),
(2030,2.6592),
(2031,2.7447),
(2032,2.7131),
(2033,2.7108),
(2034,2.8506),
(2035,2.9026),
(2036,2.9782),
(2037,3.0756),
(2038,3.0397),
(2039,2.9289),
(2040,2.9189),
(2041,2.9056),
(2042,3.1795),
(2043,3.0966),
(2044,3.0167),
(2045,2.9395),
(2046,2.8651),
(2047,2.7932),
(2048,2.7239),
(2049,2.6569),
(2050,2.5922),
)
YY=[t[0] for t in DATA]
S=[t[1] for t in DATA]
NH=YY.index(2025)+1
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'axes.edgecolor':'#888',
 'axes.linewidth':1.0,'figure.facecolor':'white','xtick.labelsize':9.8,'ytick.labelsize':9.8})
fig,ax=plt.subplots(figsize=(7.6,6.6),dpi=200)
ax.axvspan(2025.5,2050,color='#F4F4F4',zorder=0)
ax.axvline(2025.5,ls=':',lw=1.4,color='#777',zorder=1)
ax.grid(axis='y',color='#E6E6E6',lw=0.8,zorder=0); ax.set_axisbelow(True)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.axhline(1.0,ls='--',lw=1.6,color='#555',zorder=2)
ax.plot(YY[:NH],S[:NH],color=AMBER,lw=3.0,zorder=5,solid_capstyle='round')
ax.plot(YY[NH-1:],S[NH-1:],color=AMBER,lw=2.6,ls=(0,(4.5,2.2)),zorder=5)
ax.set_xlim(1987,2050); ax.set_xticks([1987,2000,2010,2020,2030,2040,2050])
ax.set_ylim(0,15.8); ax.set_yticks([0,2,4,6,8,10,12])
ax.set_yticklabels(['0','2x','4x','6x','8x','10x','12x'])
pk=YY[int(np.argmax(S[:NH]))]; tr=YY[int(np.argmin(S[:NH]))]
assert round(S[YY.index(1987)],1)==10.1, 'in-chart label "10.1x in 1987" is orphaned'
assert pk==1991 and round(S[YY.index(pk)],1)==12.7, 'in-chart label "peak 1991 / 12.7x" is orphaned'
assert tr==2012 and round(S[YY.index(tr)],2)==1.94, 'in-chart label "trough 2012 / 1.94x" is orphaned'
assert round(S[YY.index(2025)],1)==2.8, 'in-chart label "2.8x in 2025" is orphaned'
assert YY[-1]==2050 and round(S[-1],1)==2.6, 'in-chart label "2.6x in 2050" is orphaned'
assert round(S[YY.index(2025)])==3, 'title: "the mean still exceeds the median by a factor of three"'
for yr,ms in ((pk,13),(tr,13)):
    ax.plot([yr],[S[YY.index(yr)]],'o',mfc='white',mec=AMBERTXT,mew=2.6,ms=ms,zorder=30,clip_on=False)
LBL=[(1987,'10.1x'+chr(10)+'in 1987',1987.9,9.55,'left','top'),
     (pk,'peak 1991'+chr(10)+'12.7x',pk+0.8,S[YY.index(pk)]+0.30,'left','bottom'),
     (tr,'trough 2012'+chr(10)+'1.94x',tr+1.35,2.90,'center','bottom'),
     (2025,'2.8x'+chr(10)+'in 2025',2026.05,S[YY.index(2025)]+0.45,'left','bottom'),
     (2050,'2.6x'+chr(10)+'in 2050',2049.4,S[-1]+0.55,'right','bottom')]
for yr,txt,lx,ly,ha,va in LBL:
    ax.plot([yr],[S[YY.index(yr)]],'o',mfc=AMBERTXT,mec='white',mew=1.1,ms=8.5,zorder=30,clip_on=False)
    ax.text(lx,ly,txt,fontsize=10.5,fontweight='bold',color=AMBERTXT,ha=ha,va=va,linespacing=1.25,zorder=31)
ax.text(2026.4,15.8*0.955,'projected',fontsize=10.5,color='#777',style='italic',ha='left',va='top')
ax.text(1988.2,1.06+0.5*0.435,'1x = median person'+chr(10)+'lives in an economy'+chr(10)+'at the world average',
        fontsize=8.6,color='#666',ha='left',va='bottom',linespacing=1.25)
fig.tight_layout(rect=[0,0.300,1,0.985])
CAP=("Source: World Bank WDI, GNI per capita, Atlas method (NY.GNP.PCAP.CD) and population (SP.POP.TOTL); World Bank OGHIST "
"(1 July 2026) for the operational thresholds. Author's calculations and projections. Schellekens 2026, The Great Income Inversion, "
"Moving Frontiers."+chr(10)+
"Note: The ratio of world GNI per capita, which is world GNI divided by world population, to GNI per capita in the median person's "
"country, the economy at which cumulative population ranked by income first reaches half the world. This is inequality between countries "
"only: every person carries their own country's average. The rebound after 2015 follows the dollar-terms collapse across commodity "
"exporters and the handover of the median slot from Thailand through Venezuela to Indonesia. Values are for 2026, which reflects a "
"nowcast based on a conservative constant-pace scenario that replicates country-level median per capita income growth over the last "
"decade. See Schellekens 2026 for methodology.")
caption(fig,ax,CAP,7.6,url_on_last_line=False,gap_lines=2.0)
fig.savefig('chart-2-mean-to-median-ratio.png',dpi=200); plt.close(fig)
title_band('chart-2-mean-to-median-ratio.png',
  "Between-country inequality has fallen dramatically, but the mean still exceeds the median by a factor of three",
  "Ratio of world GNI per capita to GNI per capita in the median person's country, 1987 to 2050",0.0285,0.0168)
