# =============================================================================
# Chart 7: where people live by country income group
#
# Provenance, frozen vintage. Nothing is read from disk or the network.
#   Classifications       : World Bank OGHIST, 1 July 2026, Country Analytical History.
#   GNI per capita        : World Bank WDI, July 2026 vintage, Atlas method, current US$.
#   Population            : WDI SP.POP.TOTL to 2025; UN World Population Prospects 2024
#                           revision, medium variant, rebased to each economy's 2025 level.
#   Vintage freeze date   : 1 July 2026. The chart is pinned to this vintage; do not swap
#                           the embedded data for a live API call.
#
# Reduction: The script reads six columns of its companion csv at the seven-decade span
# 1987-2050. Those columns are embedded here as COLS and ROWS; the csv still ships
# alongside as the published data file.
#
# Values from 2026 are a nowcast inherited from the shared upstream projection
# pipeline (decade-median growth, floored at the threshold drift, capped at the
# group's 90th percentile) and are embedded here already resolved.
# =============================================================================
"""Chart 7: where people live, by broad income group.

Reads chart-7-where-people-live-by-country-income-group.csv and writes the png of the same name.
Run from inside this folder:  python3 chart-7-where-people-live-by-country-income-group-build.py
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from PIL import Image, ImageDraw, ImageFont

SRC=("Source: World Bank OGHIST (1 July 2026), Country Analytical History, with WDI GNI per capita, Atlas method, and population "
"(SP.POP.TOTL) to 2025; UN World Population Prospects 2024, medium variant, for population from 2026; author's calculations."+chr(10))

# ---------------------------------------------------------------- shared helpers

def place_marks(fig, ax, YY, series, marks, fontsize=10.5, pad_frac=0.014, align_x=None, override=None, dots=True, dotsize=8.5):
    """Put a value label near its point, clear of every series and every other label."""
    inv=ax.transData.inverted()
    span=ax.get_ylim()[1]-ax.get_ylim()[0]
    pad=span*pad_frac
    out=[]; fixed=[]
    def box(t):
        bb=t.get_window_extent(fig.canvas.get_renderer())
        (a0,b0)=inv.transform((bb.x0,bb.y0)); (a1,b1)=inv.transform((bb.x1,bb.y1))
        return a0,a1,min(b0,b1),max(b0,b1)
    def bad(b,skip=None):
        a0,a1,lo,hi=b
        if a1>ax.get_xlim()[1] or a0<ax.get_xlim()[0]: return True
        if hi>ax.get_ylim()[1] or lo<ax.get_ylim()[0]: return True
        xs=[q for q in YY if a0-0.7<=q<=a1+0.7]
        for s in series:
            if any(lo-pad<=s[YY.index(q)]<=hi+pad for q in xs): return True
        gx,gy=0.8,span*0.018
        for j,ot in enumerate(out):
            if j==skip: continue
            ob=box(ot)
            if a0-gx<ob[1] and ob[0]<a1+gx and lo-gy<ob[3] and ob[2]<hi+gy: return True
        return False
    for item in marks:
        yr,txt,prefer,own,col=item
        yv=own[YY.index(yr)]
        if dots:
            ax.plot([yr],[yv],'o',color=col,ms=dotsize,zorder=30,
                    markeredgecolor='white',markeredgewidth=1.1,clip_on=False)
        cands=[]
        if override and (col,yr) in override:
            ox,oy,oha,ova=override[(col,yr)]; cands=[(ox,oy,oha,ova)]
        elif align_x is not None and yr in align_x:
            lx,ha=align_x[yr]
            for st in (0.045,0.065,0.088,0.113,0.140,0.170,0.203,0.240,0.280):
                for side in ([1,-1] if prefer=='above' else [-1,1]):
                    cands.append((lx,yv+side*span*st,ha,'bottom' if side>0 else 'top'))
            cands.append((lx,yv,ha,'center'))
        else:
            for st in (0.050,0.070,0.095,0.125,0.160,0.200,0.245):
                for side in ([1,-1] if prefer=='above' else [-1,1]):
                    for dx,ha in ((-0.6,'right'),(0.6,'left'),(0.0,'center'),
                                  (2.5,'left'),(-2.5,'right'),(5.0,'left'),(-5.0,'right'),
                                  (8.0,'left'),(-8.0,'right')):
                        xr=min(max(yr+dx,YY[0]),YY[-1])
                        cands.append((xr,own[YY.index(int(round(xr)))]+side*span*st,ha,
                                      'bottom' if side>0 else 'top'))
        t=ax.text(0,0,txt,fontsize=fontsize,fontweight='bold',color=col,linespacing=1.25,zorder=9)
        out.append(t)
        if override and (col,yr) in override:
            lx,ly,ha,va=cands[0]
            t.set_position((lx,ly)); t.set_ha(ha); t.set_va(va); fig.canvas.draw()
            fixed.append(len(out)-1); continue
        ok=False
        for lx,ly,ha,va in cands:
            t.set_position((lx,ly)); t.set_ha(ha); t.set_va(va); fig.canvas.draw()
            if not bad(box(t),skip=len(out)-1): ok=True; break
        if not ok:
            lx,ly,ha,va=cands[0]
            t.set_position((lx,ly)); t.set_ha(ha); t.set_va(va); fig.canvas.draw()
    for _ in range(60):
        fig.canvas.draw(); moved=False
        for i,t in enumerate(out):
            if i in fixed: continue
            if bad(box(t),skip=i):
                x,y=t.get_position(); up=t.get_va()!='top'
                ny=y+(span*0.030 if up else -span*0.030)
                if ax.get_ylim()[0]<ny<ax.get_ylim()[1]: t.set_y(ny); moved=True
        if not moved: break
    return out

def caption(fig, ax, cap, fs=7.8, gap_lines=2.0):
    """Moving Frontiers caption block: every line runs full width except the last two,
    which stop short so the watermark can sit on the baseline of the last line."""
    fig.canvas.draw(); r=fig.canvas.get_renderer()
    Wpx=fig.get_figwidth()*fig.dpi
    bots=[t.get_window_extent(r).y0 for t in ax.get_xticklabels() if t.get_text()]
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
    lastmax=right-w(URL,UFS)-2.0*CW-x0
    lines=[]
    for para in cap.split(chr(10)):
        cur=''
        for word in para.split():
            z=(cur+' '+word).strip()
            if w(z)<=full or not cur: cur=z
            else: lines.append(cur); cur=word
        lines.append(cur)
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
    fig.canvas.draw()
    lb=objs[-1].get_window_extent(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
    fig.text(right,lb.y0,URL,ha='right',va='bottom',fontsize=UFS,color='#999')
    assert lb.y0>0.004,'caption runs off the canvas'
    print('  caption %d lines'%len(lines))

def title_band(path, title, sub, tf=0.0285, sf=0.0168):
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
    im=Image.open(path).convert('RGB')
    a=np.array(im.convert('L')); rr=np.where((a<250).sum(axis=1)>0)[0]
    im=im.crop((0,0,im.size[0],min(im.size[1],int(rr.max())+13)))
    W,H=im.size
    fs=int(W*tf); f1=ImageFont.truetype(FB,fs)
    fss=int(W*sf); f2=ImageFont.truetype(FR,fss)
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
    dr=ImageDraw.Draw(cv); y=int(fs*0.85)+3
    for ln in tl: dr.text((M,y),ln,font=f1,fill=(45,45,45)); y+=lh
    y+=int(fss*0.4)
    for ln in sl: dr.text((M,y),ln,font=f2,fill=(100,100,100)); y+=lhs
    cv.save(path,optimize=True)
    print('  wrote %s  %dx%d'%(path,cv.size[0],cv.size[1]))

AMBER='#F9A825'; AMBERTXT='#B8860B'; RED='#C62828'; INDIGO='#283593'
def panel(ax,ymax,ticks,lab,tickfmt):
    ax.axvspan(2025.5,2050,color='#F4F4F4',zorder=0)
    ax.axvline(2025.5,ls=':',lw=1.4,color='#777',zorder=1)
    ax.grid(axis='y',color='#E6E6E6',lw=0.8,zorder=0); ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.set_xlim(1987,2050); ax.set_xticks([1987,2000,2010,2020,2030,2040,2050])
    ax.set_ylim(0,ymax); ax.set_yticks(list(ticks))
    if tickfmt: ax.set_yticklabels([tickfmt(v) for v in ticks])
    ax.set_title(lab,fontsize=13,fontweight='bold',color='#333',pad=8)
def draw(ax,YY,S,col,NH):
    ax.plot(YY[:NH],S[:NH],color=col,lw=2.9,zorder=5,solid_capstyle='round')
    ax.plot(YY[NH-1:],S[NH-1:],color=col,lw=2.5,ls=(0,(4.5,2.2)),zorder=5)

PNG='chart-7-where-people-live-by-country-income-group.png'
LEVCOLS={'LIC':'low_income_population_millions','MIC':'middle_income_population_millions','HIC':'high_income_population_millions'}
SHCOLS={'LIC':'low_income_share_of_world_percent','MIC':'middle_income_share_of_world_percent','HIC':'high_income_share_of_world_percent'}
LEVTTL='Billions of people'
SHTTL='Percent of world population'
YMAXL=8300
TICKSL=range(0,7001,1000)
FMTL=lambda v:'%.0f'%(v/1000) if v else '0'
YMAXS=122
TICKSS=range(0,101,20)
VALL=lambda v:'%.2f'%(v/1000)
VALS=lambda v:'%.0f%%'%v
FORCE_BELOW=(('MIC',1987),)
OVR=None
NOTE=("Note: Middle income combines the lower-middle and upper-middle groups. Classifications are actual through 2025 and projected "
"from 2026. Shares are of total world population, so they include the small share living in economies the World Bank does not classify. "
"A group's population changes both because its members grow and because economies cross a threshold, which is why the lines step in the "
"years when large economies are reclassified. Projection: GNI per capita grows at each economy's median annual rate over the decade to "
"2025, floored at the 1.244 percent threshold drift so that no economy is downgraded, and capped at the 90th percentile of decade "
"medians within its own 2025 income group. All three thresholds drift up at 1.244 percent a year, the median annual increase in the "
"published thresholds over the same decade to 2025.")
TITLE="Where people live by country income group"
SUB="Population of each broad income group, billions and as a percent of world population"

# ---- embedded data, see the provenance header ----
COLS=['year', 'low_income_population_millions', 'middle_income_population_millions', 'high_income_population_millions', 'low_income_share_of_world_percent', 'middle_income_share_of_world_percent', 'high_income_share_of_world_percent']
ROWS=[(1987.0,2819.4159,1035.2595,790.3853,56.088,20.5949,15.7235),(1988.0,2878.3002,1067.7698,796.3097,56.2509,20.8675,15.5624),(1989.0,2937.9627,1097.5137,806.4874,56.4192,21.0761,15.4874),(1990.0,3060.5979,1410.6649,818.2718,57.7584,26.6215,15.4421),(1991.0,3150.1672,1403.8427,824.806,58.4641,26.054,15.3076),(1992.0,3218.3618,1418.7917,832.0809,58.7633,25.9054,15.1928),(1993.0,3117.8674,1600.1563,838.721,56.0318,28.7567,15.0728),(1994.0,3212.3239,1577.1306,855.4875,56.8499,27.9112,15.1399),(1995.0,3217.6488,1605.9527,906.837,56.0937,27.9968,15.809),(1996.0,3273.8263,1618.6478,923.967,56.2288,27.8007,15.8694),(1997.0,2090.6813,2879.0806,932.3635,35.3862,48.7304,15.7809),(1998.0,3605.6373,1489.2354,892.6044,60.1568,24.8466,14.8923),(1999.0,2486.1913,2687.5661,898.001,40.9043,44.2174,14.7744),(2000.0,2531.6182,2718.7111,904.713,41.0875,44.124,14.6833),(2001.0,2589.3058,2691.1377,958.2301,41.4638,43.0945,15.3446),(2002.0,2588.7434,2762.6603,969.4191,40.9147,43.6634,15.3215),(2003.0,2403.3472,3023.8421,975.5104,37.4975,47.1786,15.2201),(2004.0,2432.9227,3050.6476,1001.7991,37.4737,46.9883,15.4304),(2005.0,2450.2981,3108.3866,1009.384,37.2646,47.2729,15.3509),(2006.0,2497.8011,3121.4949,1030.7008,37.5071,46.8726,15.4771),(2007.0,1319.4251,4355.8393,1058.848,19.5643,64.5879,15.7005),(2008.0,973.8079,4775.2051,1072.4992,14.2576,69.9143,15.7026),(2009.0,842.8781,4943.5477,1120.8237,12.1871,71.4781,16.2058),(2010.0,811.8037,5055.0871,1124.4787,11.5958,72.2067,16.062),(2011.0,833.2917,5123.1897,1130.2449,11.7585,72.293,15.9488),(2012.0,859.0928,5020.2818,1297.1191,11.9709,69.9546,18.0746),(2013.0,861.5238,5098.8554,1305.0236,11.8579,70.1799,17.9622),(2014.0,628.944,5328.8822,1395.7103,8.553,72.467,18.9801),(2015.0,644.1899,5611.9303,1185.0322,8.6572,75.4182,15.9255),(2016.0,661.2457,5678.1342,1188.9194,8.7836,75.4246,15.7928),(2017.0,740.1474,5626.4645,1247.2573,9.7211,73.8984,16.3816),(2018.0,728.0297,5760.6948,1207.5202,9.4596,74.8515,15.6899),(2019.0,693.5447,5850.5119,1233.1889,8.9177,75.2268,15.8565),(2020.0,692.0503,5921.1455,1212.303,8.8116,75.3915,15.4358),(2021.0,730.5871,5926.1297,1234.6841,9.2251,74.829,15.5903),(2022.0,715.8447,6002.2663,1242.4601,8.9609,75.1359,15.553),(2023.0,735.3859,5896.2036,1402.9769,9.1206,73.1274,17.4004),(2024.0,623.4994,5939.0066,1417.7273,7.6589,72.9527,17.4149),(2025.0,767.4902,6024.1948,1423.506,9.3421,73.3279,17.3272),(2026.0,773.2554,4541.7748,2969.2487,9.3339,54.8235,35.8416),(2027.0,594.7385,4633.3205,3124.6485,7.1204,55.4714,37.4091),(2028.0,610.143,4683.1447,3126.9591,7.2463,55.6191,37.1372),(2029.0,597.4698,4763.018,3126.4412,7.0402,56.1242,36.8399),(2030.0,612.3741,4815.0276,3125.3825,7.1604,56.3011,36.5445),(2031.0,624.1723,4866.944,3126.6783,7.2434,56.4798,36.2844),(2032.0,639.1533,4911.4172,3131.3527,7.3626,56.5758,36.0708),(2033.0,654.1901,4939.2446,3151.728,7.4814,56.4858,36.0436),(2034.0,669.2723,4986.2088,3152.0405,7.5998,56.6201,35.7925),(2035.0,684.387,5035.9564,3148.6284,7.7177,56.7896,35.5066),(2036.0,699.5691,5085.0895,3144.8162,7.8356,56.956,35.2238),(2037.0,714.7955,5133.5156,3140.659,7.9533,57.1188,34.945),(2038.0,730.0111,5142.8893,3174.5213,8.0702,56.8542,35.0941),(2039.0,713.6106,5177.4265,3213.7734,7.8393,56.8761,35.3046),(2040.0,728.4328,5219.4838,3213.1912,7.9531,56.9866,35.0818),(2041.0,566.3453,5441.7872,3208.1042,6.1465,59.0592,34.8172),(2042.0,576.7684,5490.6915,3202.6452,6.2233,59.2445,34.5565),(2043.0,587.1574,5538.1994,3197.341,6.2998,59.4209,34.3051),(2044.0,589.3596,5525.0659,3259.5295,6.2889,58.9566,34.7816),(2045.0,599.6398,5352.5591,3471.5699,6.3649,56.8147,36.849),(2046.0,609.9399,5229.2768,3632.8537,6.4413,55.2239,38.3648),(2047.0,620.2163,5274.0687,3624.4966,6.5178,55.4244,38.0893),(2048.0,630.4639,5317.6763,3615.6913,6.5943,55.6202,37.8183),(2049.0,640.7719,5360.6516,3605.7603,6.672,55.8174,37.5448),(2050.0,651.0394,5402.8864,3594.8811,6.7498,56.0153,37.2705)]
rows=[dict(zip(COLS,r)) for r in ROWS]
YY=[int(r['year']) for r in rows]
LEV={k:[float(r[c]) for r in rows] for k,c in LEVCOLS.items()}
SH ={k:[float(r[c]) for r in rows] for k,c in SHCOLS.items()}
NH=YY.index(2025)+1
KEYS=('LIC','MIC','HIC')
# ---- the chart's stated numbers must follow from the embedded data ----
assert YY[0]==1987 and YY[-1]==2050 and len(YY)==64, 'the series runs 1987 to 2050'
# the nine labelled values, so a data refresh cannot silently orphan them
for _y,_lev,_sh in ((1987,(2.82,1.04,0.79),(56,21,16)),
                    (2025,(0.77,6.02,1.42),(9,73,17)),
                    (2050,(0.65,5.40,3.59),(7,56,37))):
    _i=YY.index(_y)
    assert tuple(round(LEV[k][_i]/1000,2) for k in KEYS)==_lev, 'levels labels at %d'%_y
    assert tuple(round(SH[k][_i]) for k in KEYS)==_sh, 'shares labels at %d'%_y
# the three groups do not sum to world population: economies the World Bank does not
# classify sit outside them, 7.6 percent of people in 1987 and almost none by 2025
assert round(100-sum(SH[k][0] for k in KEYS),1)==7.6, 'unclassified residual in 1987'
COL={'LIC':RED,'MIC':AMBER,'HIC':INDIGO}
TXT={'LIC':RED,'MIC':AMBERTXT,'HIC':INDIGO}
NAME={'LIC':'Low income','MIC':'Middle income','HIC':'High income'}
ALIGN={1987:(1988.6,'left'),2025:(2024.4,'right'),2050:(2049.4,'right')}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'axes.edgecolor':'#888',
 'axes.linewidth':1.0,'figure.facecolor':'white','xtick.labelsize':12,'ytick.labelsize':12})
fig,axs=plt.subplots(1,2,figsize=(9.6,6.3),dpi=200)
for ax,(D,ttl,ymax,ticks,fmt,vf,which) in zip(axs,[(LEV,LEVTTL,YMAXL,TICKSL,FMTL,VALL,'lev'),
                                                   (SH,SHTTL,YMAXS,TICKSS,None,VALS,'sh')]):
    panel(ax,ymax,ticks,ttl,fmt)
    for k in KEYS: draw(ax,YY,D[k],COL[k],NH)
    MK=[]
    for k in KEYS:
        for yr in (1987,2025,2050):
            pref='below' if (k,yr) in FORCE_BELOW else 'above'
            MK.append((yr,vf(D[k][YY.index(yr)]),pref,D[k],TXT[k]))
    place_marks(fig,ax,YY,[D[k] for k in KEYS],MK,fontsize=10.0,align_x=ALIGN,
                override=(OVR.get(which) if OVR else None))
    ax.text(2026.4,ymax*0.955,'projected',fontsize=10.5,color='#777',style='italic',ha='left',va='top')
fig.legend(handles=[Line2D([],[],color=COL[k],lw=3.0,label=NAME[k]) for k in KEYS],
           loc='lower center',bbox_to_anchor=(0.5,0.268),ncol=3,frameon=False,fontsize=12,
           columnspacing=3.0,handlelength=2.2)
fig.tight_layout(rect=[0,0.340,1,0.985]); fig.subplots_adjust(wspace=0.16)
caption(fig,axs[0],SRC+NOTE)
fig.savefig(PNG,dpi=200); plt.close(fig)
title_band(PNG,TITLE,SUB)
