#!/usr/bin/env python3
"""
Two Centuries of the Top Five

Self-contained: data embedded below, style constants included, no input files
and no network. Needs only matplotlib, numpy and pandas. Running it writes chart-4-top-five.png.

A rank grid: one row per economy, one cell per decade, the number is the rank
among the five largest and colour opacity tracks it.

Source: Maddison Project Database 2023 (Bolt and van Zanden), real GDP computed as
GDP per capita times population, in constant 2011 international dollars. NOT
comparable with the current-price IMF WEO series.
"""
import textwrap
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family']='DejaVu Sans'
VCOL={'H':'#283593','UM':'#00897B','LM':'#F9A825','L':'#C62828'}
LM_LABEL='#B8860B'; INK='#141414'; PAPER='#FFFFFF'; GREY='#BDBDBD'
CAPTION=('Source: IMF WEO database April 2026; World Bank income classification for 2025.')
CAPTION_IMF='Source: IMF WEO database April 2026.'
WATERMARK='movingfrontiers.substack.com'
FIGSIZE=(8,6.6); DPI=200
GAP_SUB=60; GAP_SRC=60; GAP_MARK=20; GAP_EDGE=10

def frame(title, subtitle, bottom=0.20, left=0.115, right=0.885, box_aspect=0.798):
    fig=plt.figure(figsize=FIGSIZE,dpi=DPI,facecolor=PAPER)
    W,H=np.array(FIGSIZE)*DPI
    ttl=fig.text(0.03,0.975,title,fontsize=19,fontweight='bold',color='#222',
                 ha='left',va='top',linespacing=1.25)
    fig.canvas.draw(); r=fig.canvas.get_renderer()
    for fs in np.arange(19,13.9,-0.5):
        ttl.set_fontsize(fs); fig.canvas.draw()
        if ttl.get_window_extent(r).width<=0.94*W: break
    sub=fig.text(0.03,0.912,subtitle,fontsize=11.5,color='#555',ha='left',va='top')
    fig.canvas.draw()
    top=(sub.get_window_extent(r).y0-GAP_SUB)/H
    ax=fig.add_axes([left,bottom,right-left,top-bottom]); ax.set_facecolor(PAPER)
    for sp in ('top','right'): ax.spines[sp].set_visible(False)
    for sp in ('left','bottom'):
        ax.spines[sp].set_color('#888'); ax.spines[sp].set_linewidth(1.0)
    ax.tick_params(labelsize=14,colors='#333',length=4,color='#888')
    if box_aspect: ax.set_box_aspect(box_aspect)
    return fig,ax,r,W,H

def fit_legend(fig,ax,r,handles=None,labels=None,ncol=2,anchor_y=-0.09,**kw):
    for fs in (14,13,12,11,10.5,10):
        leg=ax.legend(loc='upper center',bbox_to_anchor=(0.5,anchor_y),ncol=ncol,
                      frameon=False,fontsize=fs,**kw) if handles is None else \
            ax.legend(handles,labels,loc='upper center',bbox_to_anchor=(0.5,anchor_y),
                      ncol=ncol,frameon=False,fontsize=fs,**kw)
        for t in leg.get_texts(): t.set_color('#333')
        fig.canvas.draw()
        if leg.get_window_extent(r).width<=ax.get_window_extent(r).width: return leg
    return leg

def finish(fig,ax,r,W,H,caption=CAPTION,extra_artists=()):
    fig.canvas.draw()
    lows=[ax.get_tightbbox(r).y0]
    if ax.get_legend() is not None: lows.append(ax.get_legend().get_window_extent(r).y0)
    for a in extra_artists: lows.append(a.get_window_extent(r).y0)
    lowest=min(lows)
    lines=textwrap.wrap(caption,126); fs=8.2; lh=fs*1.42/72*200
    top=lowest-GAP_SRC
    for k,ln in enumerate(lines):
        cap=fig.text(0.02,(top-k*lh)/H,ln,fontsize=fs,color='#666',ha='left',va='top')
    fig.canvas.draw()
    ink=(top-(len(lines)-1)*lh)-fs/72*200
    wm=fig.text(0.98,(ink-GAP_MARK)/H,WATERMARK,fontsize=fs*1.2,color='#666',ha='right',va='top')
    fig.canvas.draw()
    return wm.get_window_extent(r).y0, cap, wm

# ----- DATA -----

YEARS = [1820, 1830, 1840, 1850, 1860, 1870, 1880, 1890, 1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020, 2022]
WORLD = {1820: 1015.401, 1830: 1102.769, 1840: 1212.386, 1850: 1318.957, 1860: 1488.807, 1870: 1831.295, 1880: 2157.280, 1890: 2584.841, 1900: 3241.755, 1910: 4058.934, 1920: 4214.387, 1930: 5666.381, 1940: 6997.133, 1950: 8446.321, 1960: 13382.461, 1970: 22097.285, 1980: 32307.354, 1990: 43546.191, 2000: 60430.344, 2010: 90739.789, 2020: 119753.659, 2022: 131402.721}
TOP = {
    1820: [('CHN', 336.042), ('IND', 196.581), ('GBR', 70.216), ('FRA', 56.535), ('ITA', 50.895)],
    1830: [('CHN', 346.014), ('IND', 205.435), ('GBR', 85.693), ('FRA', 63.208), ('DEU', 57.34)],
    1840: [('CHN', 349.788), ('IND', 213.844), ('GBR', 107.461), ('FRA', 79.424), ('DEU', 67.352)],
    1850: [('CHN', 353.496), ('IND', 223.303), ('GBR', 117.748), ('FRA', 92.512), ('USA', 85.638)],
    1860: [('CHN', 345.82), ('IND', 220.062), ('GBR', 146.924), ('USA', 140.152), ('FRA', 112.497)],
    1870: [('CHN', 338.31), ('IND', 215.05), ('USA', 193.278), ('GBR', 183.031), ('SUN', 141.515)],
    1880: [('CHN', 341.201), ('USA', 315.652), ('IND', 228.073), ('GBR', 207.634), ('SUN', 147.009)],
    1890: [('USA', 421.879), ('CHN', 366.32), ('IND', 260.332), ('GBR', 256.585), ('DEU', 184.239)],
    1900: [('USA', 613.998), ('CHN', 388.8), ('GBR', 312.531), ('IND', 271.698), ('DEU', 258.778)],
    1910: [('USA', 893.975), ('CHN', 387.194), ('GBR', 346.662), ('IND', 335.633), ('DEU', 335.612)],
    1920: [('USA', 1085.155), ('CHN', 455.121), ('GBR', 328.543), ('IND', 309.267), ('DEU', 271.405)],
    1930: [('USA', 1322.627), ('CHN', 494.868), ('DEU', 412.177), ('SUN', 402.081), ('GBR', 397.796)],
    1940: [('USA', 1592.32), ('SUN', 669.629), ('DEU', 601.419), ('GBR', 527.014), ('CHN', 500.976)],
    1950: [('USA', 2320.61), ('SUN', 813.277), ('GBR', 554.455), ('CHN', 436.905), ('DEU', 422.965)],
    1960: [('USA', 3262.376), ('SUN', 1344.249), ('DEU', 890.21), ('GBR', 721.686), ('CHN', 705.093)],
    1970: [('USA', 4912.636), ('SUN', 2154.66), ('JPN', 1615.678), ('DEU', 1343.86), ('CHN', 1144.004)],
    1980: [('USA', 6743.208), ('SUN', 2724.412), ('JPN', 2500.144), ('CHN', 1893.784), ('DEU', 1761.468)],
    1990: [('USA', 9250.378), ('JPN', 3699.822), ('CHN', 3385.122), ('SUN', 3168.799), ('DEU', 2015.548)],
    2000: [('USA', 12947.418), ('CHN', 5952.682), ('JPN', 4209.652), ('IND', 2804.478), ('DEU', 2718.56)],
    2010: [('USA', 15239.587), ('CHN', 12858.808), ('IND', 5361.371), ('JPN', 4480.296), ('DEU', 3301.123)],
    2020: [('CHN', 24151.844), ('USA', 18027.36), ('IND', 8945.313), ('JPN', 4626.661), ('DEU', 3742.721)],
    2022: [('CHN', 26966.017), ('USA', 19493.171), ('IND', 10476.249), ('JPN', 4774.495), ('DEU', 3909.613)],
}
import pandas as _pd
world=_pd.Series(WORLD)
top={y:_pd.Series(dict(v)) for y,v in TOP.items()}
share={y:top[y]/world[y]*100 for y in YEARS}

from matplotlib.patches import Rectangle
import matplotlib.patheffects as pe
NAME={'CHN':'China','USA':'United States','IND':'India','JPN':'Japan','DEU':'Germany',
      'GBR':'UK','FRA':'France','ITA':'Italy','SUN':'USSR','RUS':'Russia'}
COL={'CHN':'#C62828','USA':'#283593','IND':'#F9A825','JPN':'#00897B','DEU':'#6A1B9A',
     'GBR':'#00838F','FRA':'#EF6C00','ITA':'#558B2F','SUN':'#5D4037','RUS':'#5D4037'}
TCOL={'IND':'#B8860B','FRA':'#C25A00'}
NOTE=('Source: Maddison Project Database 2023. Note: Snapshots every ten years. Sparse benchmark '
      'years are interpolated in logs. World GDP is the sum of all economies in the database, which '
      'under-covers the nineteenth century. The USSR is one economy through 1990, Russia separately '
      'from 1991.')

# ----- FIGURE -----

# ---------- 13b: rank heatmap ----------
def b(bottom=0.20):
    fig,ax,r,W,H=frame('Two centuries of the Top Five',
                       'Rank of each economy among the five largest, 1820 to 2022',
                       bottom=bottom,left=0.165,right=0.945,box_aspect=None)
    isos=[i for i in ['CHN','USA','IND','JPN','DEU','GBR','FRA','ITA','SUN'] ]
    isos=[i for i in isos if any(i in top[y].index for y in YEARS)]
    order=sorted(isos,key=lambda i:min([k for y in YEARS for k,j in enumerate(top[y].index,1) if j==i]
                                       +[9])*100+min([YEARS.index(y) for y in YEARS if i in top[y].index]))
    for row,iso in enumerate(order):
        for col,y in enumerate(YEARS):
            if iso in top[y].index:
                rk=list(top[y].index).index(iso)+1
                al=[1.0,0.80,0.62,0.46,0.32][rk-1]
                ax.add_patch(Rectangle((col-0.44,row-0.42),0.88,0.84,facecolor=COL[iso],
                                       alpha=al,lw=0,zorder=3))
                ax.text(col,row,str(rk),ha='center',va='center',fontsize=10.5,
                        color='white' if rk<=2 else '#222',fontweight='bold',zorder=4)
    ax.set_xlim(-0.7,len(YEARS)-0.3); ax.set_ylim(len(order)-0.4,-0.6)
    ax.set_yticks(range(len(order))); ax.set_yticklabels([NAME[i] for i in order],fontsize=12.5)
    for lbl,iso in zip(ax.get_yticklabels(),order): lbl.set_color(TCOL.get(iso,COL[iso]))
    show=[1820,1850,1880,1910,1940,1970,2000,2022]
    ax.set_xticks([YEARS.index(y) for y in show]); ax.set_xticklabels([str(y) for y in show],fontsize=13)
    for sp in ('left','bottom'): ax.spines[sp].set_visible(False)
    ax.tick_params(length=0)
    return fig,ax,r,W,H,'chart-4-top-five.png'


NOTE_B=('Source: Maddison Project Database 2023. Note: Snapshots every ten years. Sparse benchmark '
        'years are interpolated in logs.')
bt=0.20
for _ in range(8):
    fig,ax,r,W,H,out=b(bt)
    y0,cap,wm=finish(fig,ax,r,W,H,caption=NOTE_B)
    d=GAP_EDGE-y0
    if abs(d)<=1.0: break
    plt.close(fig); bt+=d/H
fig.savefig(out,dpi=DPI,facecolor=PAPER)
print(out,'wm %.1f'%y0)
