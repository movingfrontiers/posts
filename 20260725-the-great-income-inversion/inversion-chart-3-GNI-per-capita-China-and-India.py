# =============================================================================
# Chart 3: China and India's climb through the income classification, 1990 to 2050
#
# Provenance, frozen vintage. Nothing is read from disk or the network.
#   Thresholds 1990-2025 : World Bank OGHIST, 1 July 2026 release, Thresholds
#                          worksheet, official values as published, no smoothing.
#   Classifications      : World Bank OGHIST, 1 July 2026, Country Analytical History.
#   GNI per capita       : World Bank WDI, July 2026 vintage, Atlas method, current US$.
#   Vintage freeze date  : 1 July 2026. The chart is pinned to this vintage;
#                          do not swap the embedded series for a live API call.
#
# G_CN and G_IN are the decade-median annual growth rates inherited from the shared
# upstream projection pipeline that also drives the shares and levels charts, and
# are embedded here already resolved, at full precision.
# =============================================================================
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

OUT=''; FN='chart-3-GNI-per-capita-China-and-India.png'
LINE_CN='#FFFFFF'; LINE_IN='#141414'   # line colours, chosen to read on every solid band
BAND={'L':'#C62828','LM':'#F9A825','UM':'#00897B','H':'#283593'}   # solid, as on the shares and levels charts
INK='#141414'; PAPER='#FFFFFF'
import matplotlib.patheffects as pe
PE_W=[pe.Stroke(linewidth=6.4,foreground=INK),pe.Normal()]     # white line, dark outline
PE_K=[pe.Stroke(linewidth=6.0,foreground=PAPER),pe.Normal()]   # dark line, white outline
# ---- embedded series, see the provenance header ----
# GNI per capita, Atlas method, current US$, 1990-2025, WDI July 2026 vintage
GNI_CN={1990:330.0,1991:360.0,1992:400.0,1993:420.0,1994:470.0,1995:540.0,1996:660.0,1997:760.0,1998:800.0,1999:860.0,2000:950.0,2001:1020.0,2002:1130.0,2003:1300.0,2004:1530.0,2005:1790.0,2006:2090.0,2007:2550.0,2008:3140.0,2009:3740.0,2010:4410.0,2011:5130.0,2012:6010.0,2013:6860.0,2014:7600.0,2015:8040.0,2016:8360.0,2017:8830.0,2018:9720.0,2019:10510.0,2020:10740.0,2021:12220.0,2022:13170.0,2023:13750.0,2024:13660.0,2025:14230.0}
GNI_IN={1990:390.0,1991:350.0,1992:350.0,1993:330.0,1994:340.0,1995:370.0,1996:400.0,1997:410.0,1998:410.0,1999:440.0,2000:440.0,2001:450.0,2002:460.0,2003:510.0,2004:610.0,2005:700.0,2006:780.0,2007:910.0,2008:990.0,2009:1110.0,2010:1210.0,2011:1350.0,2012:1460.0,2013:1500.0,2014:1540.0,2015:1580.0,2016:1670.0,2017:1790.0,2018:1970.0,2019:2070.0,2020:1900.0,2021:2170.0,2022:2360.0,2023:2490.0,2024:2550.0,2025:2760.0}
# official operational thresholds [low, lower-middle, upper-middle], OGHIST 1 July 2026
TH={1990:[610.0, 2465.0, 7620.0],1991:[635.0, 2555.0, 7910.0],1992:[675.0, 2695.0, 8355.0],1993:[695.0, 2785.0, 8625.0],1994:[725.0, 2895.0, 8955.0],1995:[765.0, 3035.0, 9385.0],1996:[785.0, 3115.0, 9645.0],1997:[785.0, 3125.0, 9655.0],1998:[760.0, 3030.0, 9360.0],1999:[755.0, 2995.0, 9265.0],2000:[755.0, 2995.0, 9265.0],2001:[745.0, 2975.0, 9205.0],2002:[735.0, 2935.0, 9075.0],2003:[765.0, 3035.0, 9385.0],2004:[825.0, 3255.0, 10065.0],2005:[875.0, 3465.0, 10725.0],2006:[905.0, 3595.0, 11115.0],2007:[935.0, 3705.0, 11455.0],2008:[975.0, 3855.0, 11905.0],2009:[995.0, 3945.0, 12195.0],2010:[1005.0, 3975.0, 12275.0],2011:[1025.0, 4035.0, 12475.0],2012:[1035.0, 4085.0, 12615.0],2013:[1045.0, 4125.0, 12745.0],2014:[1045.0, 4125.0, 12735.0],2015:[1025.0, 4035.0, 12475.0],2016:[1005.0, 3955.0, 12235.0],2017:[995.0, 3895.0, 12055.0],2018:[1025.0, 3995.0, 12375.0],2019:[1035.0, 4045.0, 12535.0],2020:[1045.0, 4095.0, 12695.0],2021:[1085.0, 4255.0, 13205.0],2022:[1135.0, 4465.0, 13845.0],2023:[1145.0, 4515.0, 14005.0],2024:[1135.0, 4495.0, 13935.0],2025:[1175.0, 4635.0, 14375.0]}
DRIFT=0.012440
# decade-median annual growth from the shared upstream pipeline behind charts 1 and 2
G_CN=0.0501297896843995
# decade-median annual growth from the shared upstream pipeline behind charts 1 and 2
G_IN=0.0644091563708026
assert round(DRIFT*100,3)==1.244, 'caption states a 1.244 percent threshold drift'
assert round(G_CN*100,1)==5.0,   'caption states 5.0 percent for China'
assert round(G_IN*100,1)==6.4,   'caption states 6.4 percent for India'
gCN,gIN=G_CN,G_IN
HY=list(range(1990,2026)); PY=list(range(2025,2051))
cn=dict(GNI_CN); ind=dict(GNI_IN)
for y in PY[1:]:
    cn[y]=cn[y-1]*(1+gCN); ind[y]=ind[y-1]*(1+gIN)
th={y:list(TH[y]) for y in HY}
for y in PY[1:]: th[y]=[v*(1+DRIFT) for v in th[y-1]]
YR=list(range(1990,2051))
tL=np.array([th[y][0] for y in YR]); tM=np.array([th[y][1] for y in YR]); tU=np.array([th[y][2] for y in YR])

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':15,'axes.edgecolor':'#888',
 'axes.linewidth':1.0,'figure.facecolor':'white','xtick.labelsize':14,'ytick.labelsize':14,
 'axes.labelsize':15})
fig,ax=plt.subplots(figsize=(8,6.6),dpi=200)
YLO,YHI=190,62000
ax.fill_between(YR,YLO,tL,color=BAND['L'],zorder=0)
ax.fill_between(YR,tL,tM,color=BAND['LM'],zorder=0)
ax.fill_between(YR,tM,tU,color=BAND['UM'],zorder=0)
ax.fill_between(YR,tU,YHI,color=BAND['H'],zorder=0)
for t in (tL,tM,tU):
    ax.plot(YR,t,ls='--',lw=1.5,color='white',alpha=0.85,zorder=2)
ax.axvline(2025.5,ls=':',lw=1.8,color='white',zorder=3)

ax.plot(HY,[cn[y] for y in HY],color=LINE_CN,lw=3.4,zorder=5,solid_capstyle='round',path_effects=PE_W)
ax.plot(PY,[cn[y] for y in PY],color=LINE_CN,lw=3.0,ls=(0,(5,2.6)),zorder=5,path_effects=PE_W)
ax.plot(HY,[ind[y] for y in HY],color=LINE_IN,lw=3.4,zorder=5,solid_capstyle='round',path_effects=PE_K)
ax.plot(PY,[ind[y] for y in PY],color=LINE_IN,lw=3.0,ls=(0,(5,2.6)),zorder=5,path_effects=PE_K)

def dot(x,y,col):
    edge = INK if col==PAPER else PAPER
    ax.plot([x],[y],'o',mfc=col,mec=edge,mew=2.8,ms=12,zorder=7)
# ---- label placement solver: pick anchors that clear every curve and every other label ----
ax.set_yscale('log'); ax.set_ylim(YLO,YHI); ax.set_xlim(1989.6,2050.5)
ticks=[200,500,1000,2000,5000,10000,20000,40000]
ax.set_yticks(ticks); ax.set_yticklabels(['$%s'%format(t,',') for t in ticks]); ax.minorticks_off()
ax.set_xticks([1990,2000,2010,2020,2030,2040,2050])

ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout(rect=[0,0.218,0.902,0.995])
fig.canvas.draw()
REN=fig.canvas.get_renderer()
CURVES=[lambda x:cn[x],lambda x:ind[x],lambda x:th[x][0],lambda x:th[x][1],lambda x:th[x][2]]
placed=[]
def databox(t):
    bb=t.get_window_extent(REN); inv=ax.transData.inverted()
    (x0,y0)=inv.transform((bb.x0,bb.y0)); (x1,y1)=inv.transform((bb.x1,bb.y1))
    return x0,x1,min(y0,y1),max(y0,y1)
def ok(box,pad=0.030):
    x0,x1,ylo,yhi=box
    if x0<1989.8 or x1>2050.3: return False
    lo,hi=ylo/10**pad,yhi*10**pad
    xs=[x for x in YR if x0-0.7<=x<=x1+0.7]
    for f in CURVES:
        for x in xs:
            if lo<=f(x)<=hi: return False
    for p in placed:
        if x0<p[1]+0.4 and p[0]<x1+0.4 and ylo/10**0.012<p[3] and p[2]<yhi*10**0.012: return False
    return True
def place(lab,cands,fs,col,weight='bold'):
    for (lx,ly,ha,va) in cands:
        fc,tc=(INK,PAPER) if col==PAPER else (PAPER,INK)
        t=ax.text(lx,ly,lab,fontsize=fs,fontweight=weight,color=tc,ha=ha,va=va,
                  zorder=8,linespacing=1.3,
                  bbox=dict(boxstyle='round,pad=0.26',facecolor=fc,edgecolor='none'))
        b=databox(t)
        if ok(b):
            placed.append(b); return t,b
        t.remove()
    fc,tc=(INK,PAPER) if col==PAPER else (PAPER,INK)
    t=ax.text(cands[0][0],cands[0][1],lab,fontsize=fs,fontweight=weight,color=tc,
              ha=cands[0][2],va=cands[0][3],zorder=8,linespacing=1.3,
              bbox=dict(boxstyle='round,pad=0.26',facecolor=fc,edgecolor='none'))
    b=databox(t); placed.append(b); print('  !! no clear slot for',lab.replace(chr(10),' ')[:28])
    return t,b

JOBS=[
 ('2026',2026,cn[2026],LINE_CN,
   [(2024.6,y,'right','center') for y in (21500,24000,19500)]+
   [(2027.8,y,'left','center') for y in (11800,11000)]),
 ('2010',2010,cn[2010],LINE_CN,
   [(2008.8,y,'right','center') for y in (6100,6700,5600)]+
   [(2011.8,y,'left','center') for y in (3250,3000)]),
 ('1999',1999,cn[1999],LINE_CN,
   [(1997.6,y,'right','center') for y in (1200,1330,1090)]+
   [(2000.9,y,'left','center') for y in (610,560)]),
 ('2036',2036,ind[2036],LINE_IN,
   [(2037.8,y,'left','center') for y in (4100,3800,4450)]+
   [(2034.2,y,'right','center') for y in (7400,8100)]),
 ('2007',2007,ind[2007],LINE_IN,
   [(2008.8,y,'left','center') for y in (630,580,690)]+
   [(2005.2,y,'right','center') for y in (630,580)]),
]
for lab,dx,dy,col,cands in JOBS:
    dot(dx,dy,col)
    place(lab,cands,13,col)

place('China',[(2043.5,y,'right','center') for y in (44000,48500,40000)]+
      [(2038,y,'right','center') for y in (37000,41000)],13,LINE_CN)
place('India',[(2046.5,y,'right','center') for y in (14600,13600,15600,16600)]+
      [(2043,y,'right','center') for y in (14600,13600,16000)]+
      [(2049.8,y,'right','center') for y in (17500,16000)],13,LINE_IN)

# band labels, outside the axes on the right, two lines each, centred in each band
BANDLAB=[('HIGH\nINCOME',  np.sqrt(th[2050][2]*YHI)),
         ('UPPER-\nMIDDLE',np.sqrt(th[2050][1]*th[2050][2])),
         ('LOWER-\nMIDDLE',np.sqrt(th[2050][0]*th[2050][1])),
         ('LOW\nINCOME',   np.sqrt(YLO*th[2050][0]))]
BANDCOL=['#283593','#00897B','#B8860B','#C62828']
for (lab,yv),cc in zip(BANDLAB,BANDCOL):
    ax.text(1.012,yv,lab,transform=ax.get_yaxis_transform(),fontsize=11.5,fontweight='bold',
            color=cc,ha='left',va='center',linespacing=1.25,clip_on=False,zorder=6)

ax.text(2026.4,YLO*1.12,'projected',fontsize=11.5,color='white',fontweight='bold',ha='left',va='bottom',zorder=6)
ax.text(2024.6,YLO*1.12,'actual',fontsize=11.5,color='white',fontweight='bold',ha='right',va='bottom',zorder=6)

CAPFS=7.4
CAPTXT=("Source: World Bank OGHIST (1 July 2026): Thresholds worksheet for the official thresholds and Country Analytical History for\n"
"the classifications, both 1990 to 2025; WDI GNI per capita, Atlas method (July 2026 vintage); author's calculations and projections.\n"
"Note: Shaded bands are the four income groups, named at right. Their boundaries are the official thresholds year by year as\n"
"published, with no smoothing, extended beyond 2025 at 1.244 percent a year, the median annual increase of the past decade. Solid\n"
"lines are actual GNI per capita through 2025, dashed lines projected at each economy's decade-median growth, 5.0 percent for\n"
"China and 6.4 percent for India. Circles mark each economy's crossings, dated by the classification year; each is announced the\n"
"following July.")
fig.canvas.draw()
_r=fig.canvas.get_renderer()
_bots=[t.get_window_extent(_r).y0 for t in ax.get_xticklabels() if t.get_text()]
xl=ax.xaxis.get_label().get_window_extent(_r)
xl_bot=fig.transFigure.inverted().transform((0,min(_bots+[xl.y0])))[1]
LH=CAPFS*1.2/(72*fig.get_figheight())
cap=fig.text(0.012,xl_bot-2*LH,CAPTXT,fontsize=CAPFS,color='#666',va='top')
fig.canvas.draw()
cb=cap.get_window_extent(fig.canvas.get_renderer())
top,bot=[fig.transFigure.inverted().transform((0,v))[1] for v in (cb.y1,cb.y0)]
print('axis bottom {:.4f} | caption top {:.4f} | gap {:.2f} caption lines'.format(xl_bot,top,(xl_bot-top)/LH))
print('caption bottom {:.4f}'.format(bot))
assert bot>0.004, 'caption runs off the canvas'

# watermark: same format and placement as the shares and levels charts,
# right-aligned to the last plotted year, sitting on the caption's bottom line
# right edge set to match the shares and levels charts exactly (95 px from the canvas edge)
xw=1.0-95.0/(fig.get_figwidth()*fig.dpi)
wm=fig.text(xw,bot-1.30*LH,'movingfrontiers.substack.com',ha='right',va='bottom',
            fontsize=7.9,color='#999')
fig.canvas.draw()
wb=wm.get_window_extent(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
cbx=cap.get_window_extent(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
print('watermark x {:.4f}-{:.4f} y {:.4f}-{:.4f} | caption right edge {:.4f}'.format(
      wb.x0,wb.x1,wb.y0,wb.y1,cbx.x1))
assert wb.x0>0 and wb.x1<1.0, 'watermark off canvas'
fig.savefig(OUT+FN,dpi=200); plt.close(fig)

# ---- standard title band ----
# ---- fonts: DejaVu from matplotlib's bundled ttf, system path only as a fallback ----
import os as _os
from matplotlib import font_manager as _fm
def _dejavu(stem):
    p=_os.path.join(matplotlib.get_data_path(),'fonts','ttf',stem)
    if _os.path.exists(p): return p
    try:
        q=_fm.findfont(_fm.FontProperties(family='DejaVu Sans',
            weight=('bold' if 'Bold' in stem else 'normal')),fallback_to_default=False)
        if _os.path.basename(q)==stem and _os.path.exists(q): return q
    except Exception: pass
    p=_os.path.join('/usr/share/fonts/truetype/dejavu',stem)
    if _os.path.exists(p): return p
    raise FileNotFoundError('DejaVu font not found: '+stem)
FB=_dejavu('DejaVuSans-Bold.ttf'); FR=_dejavu('DejaVuSans.ttf')
assert _os.path.exists(FB) and _os.path.exists(FR), 'resolved DejaVu font files must exist'
title="China and India's climb through the income classification, 1990 to 2050"
sub="GNI per capita (Atlas method, logs) against World Bank's moving income thresholds"
im=Image.open(OUT+FN).convert('RGB')
_a=np.array(im.convert('L')); _rows=np.where((_a<250).sum(axis=1)>0)[0]
im=im.crop((0,0,im.size[0],min(im.size[1],int(_rows.max())+6)))
W,H=im.size
print('trimmed trailing whitespace: height {} -> {}'.format(_a.shape[0],H))
fs=int(W*0.031); f1=ImageFont.truetype(FB,fs)
fss=int(W*0.0225); f2=ImageFont.truetype(FR,fss)
dd=ImageDraw.Draw(im); lines=[]; cur=''
for w in title.split():
    t=(cur+' '+w).strip()
    if dd.textlength(t,font=f1)<=W-2*int(W*0.03): cur=t
    else: lines.append(cur); cur=w
lines.append(cur)
lh=int(fs*1.25); lhs=int(fss*1.3)
band=int(fs*0.85)+lh*len(lines)+int(fss*0.5)+lhs+int(fs*0.2)
cv=Image.new('RGB',(W,H+band),'white'); cv.paste(im,(0,band))
dr=ImageDraw.Draw(cv); y=int(fs*0.85)
for ln in lines: dr.text((int(W*0.03),y),ln,font=f1,fill=(45,45,45)); y+=lh
y+=int(fss*0.35); dr.text((int(W*0.03),y),sub,font=f2,fill=(100,100,100))
cv.save(OUT+FN,optimize=True)
print('saved',FN,cv.size)
print('China 2025 %.0f  2026 %.0f  2045 %.0f | growth %.4f%%'%(cn[2025],cn[2026],cn[2045],gCN*100))
print('India 2025 %.0f  2036 %.0f  2045 %.0f | growth %.4f%%'%(ind[2025],ind[2036],ind[2045],gIN*100))
print('thresholds 2026 %s | 2036 %s | 2045 %s'%([round(v) for v in th[2026]],[round(v) for v in th[2036]],[round(v) for v in th[2045]]))
