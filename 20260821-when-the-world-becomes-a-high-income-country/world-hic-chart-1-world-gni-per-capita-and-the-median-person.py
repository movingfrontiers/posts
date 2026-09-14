"""Chart 1: World GNI per capita and the income of the median person's country.

Self-sufficient: the data this chart consumes are embedded below, frozen at the
July 2026 vintage. No external files, downloads or network access. Writes the png
of the same name. Run from any directory:
  python3 chart-1-world-gni-per-capita-and-the-median-person-build.py
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
# The caption's 'Russia down 34 percent and Brazil 26 percent' are historical
# WDI facts external to this chart's series and are not assertable here.
import os
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from PIL import Image, ImageDraw, ImageFont

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

PNG='chart-1-world-gni-per-capita-and-the-median-person.png'
# --------------------------------------------- embedded data (see provenance)
DATA=(  # (year, world_gni_pc, median_person_country_gni_pc, th_L_LM, th_LM_UM, th_UM_H), csv row order
(1987,3629.9,360.0,480.0,1940.0,6000.0),
(1988,4282.3,400.0,545.0,2200.0,6000.0),
(1989,4352.4,390.0,580.0,2335.0,6000.0),
(1990,4485.5,390.0,610.0,2465.0,7620.0),
(1991,4556.4,360.0,635.0,2555.0,7910.0),
(1992,4790.6,400.0,675.0,2695.0,8355.0),
(1993,4850.6,420.0,695.0,2785.0,8625.0),
(1994,5053.9,470.0,725.0,2895.0,8955.0),
(1995,5366.2,540.0,765.0,3035.0,9385.0),
(1996,5627.7,660.0,785.0,3115.0,9645.0),
(1997,5679.2,760.0,785.0,3125.0,9655.0),
(1998,5425.1,800.0,760.0,3030.0,9360.0),
(1999,5422.9,860.0,755.0,2995.0,9265.0),
(2000,5609.2,950.0,755.0,2995.0,9265.0),
(2001,5583.7,1020.0,745.0,2975.0,9205.0),
(2002,5523.1,1130.0,735.0,2935.0,9075.0),
(2003,5925.7,1300.0,765.0,3035.0,9385.0),
(2004,6755.2,1530.0,825.0,3255.0,10065.0),
(2005,7489.2,1790.0,875.0,3465.0,10725.0),
(2006,7980.7,2090.0,905.0,3595.0,11115.0),
(2007,8505.2,2550.0,935.0,3705.0,11455.0),
(2008,8943.0,3140.0,975.0,3855.0,11905.0),
(2009,8981.8,3740.0,995.0,3945.0,12195.0),
(2010,9418.5,4410.0,1005.0,3975.0,12275.0),
(2011,9891.6,4840.0,1025.0,4035.0,12475.0),
(2012,10479.6,5400.0,1035.0,4085.0,12615.0),
(2013,10846.9,5580.0,1045.0,4125.0,12745.0),
(2014,10951.9,5620.0,1045.0,4125.0,12735.0),
(2015,10597.4,5280.0,1025.0,4035.0,12475.0),
(2016,10351.9,4180.0,1005.0,3955.0,12235.0),
(2017,10422.5,4110.0,995.0,3895.0,12055.0),
(2018,11126.9,4190.0,1025.0,3995.0,12375.0),
(2019,11604.1,4220.0,1035.0,4045.0,12535.0),
(2020,11153.4,3850.0,1045.0,4095.0,12695.0),
(2021,12266.0,4130.0,1085.0,4255.0,13205.0),
(2022,13063.4,4520.0,1135.0,4465.0,13845.0),
(2023,13436.2,4810.0,1145.0,4515.0,14005.0),
(2024,13534.8,4920.0,1135.0,4495.0,13935.0),
(2025,14346.2,5120.0,1175.0,4635.0,14375.0),
(2026,14801.2,5365.2,1189.6,4692.7,14553.8),
(2027,15277.8,5622.1,1204.4,4751.0,14734.9),
(2028,15773.6,5891.3,1219.4,4810.1,14918.2),
(2029,16289.1,6173.4,1234.6,4870.0,15103.8),
(2030,16825.4,6327.3,1249.9,4930.6,15291.6),
(2031,17383.7,6333.6,1265.5,4991.9,15481.9),
(2032,17965.4,6621.6,1281.2,5054.0,15674.5),
(2033,18572.0,6851.1,1297.2,5116.9,15869.5),
(2034,19204.5,6736.9,1313.3,5180.5,16066.9),
(2035,19864.0,6843.4,1329.6,5245.0,16266.8),
(2036,20551.6,6900.7,1346.2,5310.2,16469.1),
(2037,21269.3,6915.6,1362.9,5376.3,16674.0),
(2038,22018.6,7243.6,1379.9,5443.2,16881.4),
(2039,22800.4,7784.5,1397.0,5510.9,17091.4),
(2040,23616.2,8090.8,1414.4,5579.4,17304.0),
(2041,24468.0,8420.8,1432.0,5648.8,17519.3),
(2042,25358.0,7975.5,1449.8,5719.1,17737.2),
(2043,26287.6,8489.1,1467.9,5790.2,17957.9),
(2044,27258.2,9035.9,1486.1,5862.3,18181.3),
(2045,28272.1,9617.9,1504.6,5935.2,18407.5),
(2046,29331.1,10237.4,1523.3,6009.0,18636.4),
(2047,30437.2,10896.8,1542.3,6083.8,18868.3),
(2048,31593.1,11598.6,1561.5,6159.5,19103.0),
(2049,32800.9,12345.7,1580.9,6236.1,19340.6),
(2050,34063.5,13140.9,1600.6,6313.7,19581.2),
)
YR=[t[0] for t in DATA]
V={'mean':{t[0]:t[1] for t in DATA},'med':{t[0]:t[2] for t in DATA}}
TH={t[0]:[t[3],t[4],t[5]] for t in DATA}
# the csv's median_person_country column was loaded here as ECON but never
# used downstream, so it is dropped from the embedding
S={k:np.array([V[k][y] for y in YR]) for k in ('mean','med')}
tL=np.array([TH[y][0] for y in YR]); tM=np.array([TH[y][1] for y in YR]); tU=np.array([TH[y][2] for y in YR])

# threshold crossings, each year against that year's own threshold
CR=[]
for k in ('mean','med'):
    for j,tn in enumerate(('LIC/LMIC','LMIC/UMIC','UMIC/HIC')):
        for i in range(1,len(YR)):
            a,b=YR[i-1],YR[i]
            if V[k][a]<=TH[a][j] and V[k][b]>TH[b][j]: CR.append((k,tn,b,'up'))
            if V[k][a]>TH[a][j] and V[k][b]<=TH[b][j]: CR.append((k,tn,b,'down'))
print('  crossings:',[(k,t,y,d) for k,t,y,d in CR])
_EXPECT=[('mean','UMIC/HIC',2026,'up'),('med','LIC/LMIC',1998,'up'),('med','LMIC/UMIC',2010,'up'),
         ('med','LMIC/UMIC',2020,'down'),('med','LMIC/UMIC',2022,'up')]
assert CR==_EXPECT, ('crossings changed: the title year 2026 and the marker labels '
 '"1998 China", "2010 China", "2020-22 Indonesia" and "2026 world average" are orphaned')

BAND={'L':'#C62828','LM':'#F9A825','UM':'#00897B','H':'#283593'}
INK='#141414'; PAPER='#FFFFFF'; AMBERTXT='#8A5A00'
LC={'mean':PAPER,'med':'#FFD166'}
PEF={'mean':[pe.Stroke(linewidth=6.6,foreground=INK),pe.Normal()],
     'med' :[pe.Stroke(linewidth=6.4,foreground=INK),pe.Normal()]}
LEGLAB={'mean':'World GNI per capita','med':"GNI per capita in the median person's country"}

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':15,'axes.edgecolor':'#888',
 'axes.linewidth':1.0,'figure.facecolor':'white','xtick.labelsize':9.8,'ytick.labelsize':9.8,
 'axes.labelsize':15})
fig,ax=plt.subplots(figsize=(8,7.6),dpi=200)
YLO,YHI=230,72000
ax.fill_between(YR,YLO,tL,color=BAND['L'],zorder=0)
ax.fill_between(YR,tL,tM,color=BAND['LM'],zorder=0)
ax.fill_between(YR,tM,tU,color=BAND['UM'],zorder=0)
ax.fill_between(YR,tU,YHI,color=BAND['H'],zorder=0)
for t in (tL,tM,tU): ax.plot(YR,t,ls='--',lw=1.5,color='white',alpha=0.85,zorder=2)
NH=YR.index(2025)+1
for k in ('med','mean'):
    ax.plot(YR[:NH],S[k][:NH],color=LC[k],lw=3.4,zorder=5,solid_capstyle='round',path_effects=PEF[k])
    ax.plot(YR[NH-1:],S[k][NH-1:],color=LC[k],lw=3.0,ls=(0,(5,2.4)),zorder=5,path_effects=PEF[k])
ax.axvline(2025.5,ls=':',lw=1.8,color='white',zorder=3)
def dot(x,y,col,ms=11):
    ax.plot([x],[y],'o',mfc=col,mec=INK if col!=INK else PAPER,mew=2.6,ms=ms,zorder=9,clip_on=False)
ax.set_yscale('log'); ax.set_ylim(YLO,YHI); ax.set_xlim(1986.6,2050.5)
ticks=[250,500,1000,2000,5000,10000,20000,50000]
ax.set_yticks(ticks); ax.set_yticklabels(['$%s'%format(t,',') for t in ticks]); ax.minorticks_off()
ax.set_xticks([1987,2000,2010,2020,2030,2040,2050])
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout(rect=[0.012,0.360,0.885,0.995])
fig.canvas.draw(); REN=fig.canvas.get_renderer()
CURVES=[lambda x:V['mean'][x],lambda x:V['med'][x],
        lambda x:TH[x][0],lambda x:TH[x][1],lambda x:TH[x][2]]
placed=[]
def databox(t):
    bb=t.get_window_extent(REN); inv=ax.transData.inverted()
    (x0,y0)=inv.transform((bb.x0,bb.y0)); (x1,y1)=inv.transform((bb.x1,bb.y1))
    return x0,x1,min(y0,y1),max(y0,y1)
def ok(box,pad=0.026):
    x0,x1,ylo,yhi=box
    if x0<1986.8 or x1>2050.3: return False
    if ylo<YLO*1.02 or yhi>YHI*0.98: return False
    lo,hi=ylo/10**pad,yhi*10**pad
    xs=[x for x in YR if x0-0.5<=x<=x1+0.5]
    for f in CURVES:
        for x in xs:
            if lo<=f(x)<=hi: return False
    for p in placed:
        if x0<p[1]+0.4 and p[0]<x1+0.4 and ylo/10**0.012<p[3] and p[2]<yhi*10**0.012: return False
    return True
def place(lab,cands,fs,col):
    for (lx,ly,ha,va) in cands:
        fc,tc=(PAPER,AMBERTXT) if col=='#FFD166' else (PAPER,INK)
        t=ax.text(lx,ly,lab,fontsize=fs,fontweight='bold',color=tc,ha=ha,va=va,zorder=8,
                  linespacing=1.25,bbox=dict(boxstyle='round,pad=0.24',facecolor=fc,edgecolor='none'))
        b=databox(t)
        if ok(b): placed.append(b); return
        t.remove()
    fc,tc=(PAPER,AMBERTXT) if col=='#FFD166' else (PAPER,INK)
    t=ax.text(cands[0][0],cands[0][1],lab,fontsize=fs,fontweight='bold',color=tc,
              ha=cands[0][2],va=cands[0][3],zorder=8,linespacing=1.25,
              bbox=dict(boxstyle='round,pad=0.24',facecolor=fc,edgecolor='none'))
    placed.append(databox(t)); print('   !! no clear slot for',lab.replace(chr(10),' ')[:30])

SKIP={(2022,'med')}
SHIFT={(2010,'med'):-2.0}
FIXED={(2020,'med'):(2020.9,V['med'][2010]/1.42,'left')}
PREF={(1998,'med'):'down-right',(2010,'med'):'down-right',
      (2020,'med'):'down-right',(2026,'mean'):'up-left'}
TXT={(1998,'med'):'1998  China',(2010,'med'):'2010  China',
     (2020,'med'):'2020-22  Indonesia',
     (2026,'mean'):'2026  world average'+chr(10)+'at high-income line'}
for k,tn,yr,dirn in CR:
    y0=V[k][yr]; dot(yr,y0,LC[k],ms=11)
    if (yr,k) in SKIP: continue
    if (yr,k) in FIXED:
        fx,fy,fha=FIXED[(yr,k)]; cands=[(fx,fy,fha,'center')]
    elif PREF[(yr,k)]=='down-right':
        sh=SHIFT.get((yr,k),0.0)
        cands=[(yr+1.2+sh,y0/f,'left','center') for f in (1.42,1.58,1.78,2.00)]+\
              [(yr-1.2+sh,y0/f,'right','center') for f in (1.45,1.62)]
    else:
        cands=[(yr-1.2,y0*f,'right','center') for f in (1.38,1.55,1.75)]+\
              [(yr+1.2,y0*f,'left','center') for f in (1.40,1.58)]
    place(TXT[(yr,k)],cands,8.05,LC[k])

handles=[Line2D([],[],color=LC[k],lw=3.4,label=LEGLAB[k],path_effects=PEF[k]) for k in ('mean','med')]
fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(0.5,0.272),ncol=1,frameon=False,
           fontsize=11.5,columnspacing=2.2,handlelength=2.6,labelspacing=0.5)
BANDLAB=[('HIGH'+chr(10)+'INCOME',np.sqrt(TH[2050][2]*YHI)),
         ('UPPER-'+chr(10)+'MIDDLE',np.sqrt(TH[2050][1]*TH[2050][2])),
         ('LOWER-'+chr(10)+'MIDDLE',np.sqrt(TH[2050][0]*TH[2050][1])),
         ('LOW'+chr(10)+'INCOME',np.sqrt(YLO*TH[2050][0]))]
for (lab,yv),cc in zip(BANDLAB,['#283593','#00897B','#B8860B','#C62828']):
    ax.text(1.012,yv,lab,transform=ax.get_yaxis_transform(),fontsize=11.5,fontweight='bold',
            color=cc,ha='left',va='center',linespacing=1.25,clip_on=False,zorder=6)

MEDNOTE=("The second line is the population-weighted median: rank economies by GNI per capita, accumulate population, and take the "
"value of the economy in which the total first reaches half. It is the average income of the country the median person lives in, not the "
"median income of people: every person is assigned their own country's average, so all within-country distribution is discarded. Markers "
"show every threshold crossing, labelled with the year and the economy concerned. The fall from 2014 to 2017 combines a real dollar-terms "
"collapse across commodity exporters, Russia down 34 percent and Brazil 26 percent from 2014 to 2016, with a reshuffling that moved the "
"median slot from Thailand through Venezuela and Georgia to Azerbaijan, while China and India rose past it. ")
CAP=("Source: World Bank WDI, GNI per capita, Atlas method (NY.GNP.PCAP.CD) and population (SP.POP.TOTL); World Bank OGHIST "
"(1 July 2026) for the operational thresholds. Author's calculations and projections. Schellekens 2026, The Great Income Inversion, "
"Moving Frontiers."+chr(10)+
"Note: Shaded bands are the four income groups, named at right; their boundaries are the official thresholds year by year. World GNI per "
"capita is world GNI divided by world population, the population-weighted mean across economies. "+MEDNOTE+
"Values are for 2026, which reflects a nowcast based on a conservative constant-pace scenario that replicates country-level median per "
"capita income growth over the last decade. See Schellekens 2026 for methodology.")
caption(fig,ax,CAP,7.4,url_on_last_line=True)
fig.savefig(PNG,dpi=200); plt.close(fig)
title_band(PNG,"World GNI per capita crosses the high-income line in 2026",
   "Atlas GNI per capita in current US dollars, log scale, against the World Bank's income-classification thresholds",
   0.0265,0.0163)
