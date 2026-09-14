#!/usr/bin/env python3
"""
The global GDP share at PPP and market prices

Self-contained: data embedded below, style constants included, no input files
and no network. Needs only matplotlib, numpy and pandas. Running it writes chart-2-global-shares.png.

Share of world GDP in 2025 under each concept, ten largest economies,
China and the United States highlighted.

Source: IMF World Economic Outlook, April 2026 vintage (dataset IMF.RES:WEO(9.0.0),
published 14 April 2026); World Bank income
classification for 2025.
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

COLS = ['ISO', 'nm', 'CLASS', 'ppp_sh', 'mer_sh', 'pli', 'uplift', 'PPPGDP', 'NGDPD']
ROWS = [
    ('CHN', 'China', 'UM', 19.6105, 16.609, 47.5881, 2.1014, 41241.951, 19626.247),
    ('USA', 'US', 'H', 14.6297, 26.0371, 100.0, 1.0, 30767.075, 30767.075),
    ('IND', 'India', 'LM', 8.2061, 3.3142, 22.6929, 4.4067, 17257.883, 3916.312),
    ('RUS', 'Russia', 'H', 3.441, 2.1901, 35.7618, 2.7963, 7236.601, 2587.938),
    ('JPN', 'Japan', 'H', 3.333, 3.7533, 63.2734, 1.5804, 7009.525, 4435.163),
    ('DEU', 'Germany', 'H', 2.9391, 4.272, 81.6696, 1.2244, 6181.073, 5048.059),
    ('IDN', 'Indonesia', 'UM', 2.4001, 1.2234, 28.6407, 3.4915, 5047.517, 1445.642),
    ('BRA', 'Brazil', 'UM', 2.3721, 1.9294, 45.7025, 2.1881, 4988.607, 2279.918),
    ('FRA', 'France', 'H', 2.1698, 2.851, 73.8276, 1.3545, 4563.23, 3368.925),
    ('GBR', 'UK', 'H', 2.165, 3.3876, 87.9185, 1.1374, 4553.105, 4003.022),
]
import pandas as _pd
t = _pd.DataFrame(ROWS, columns=COLS).head(10).copy()

# ----- FIGURE -----

from matplotlib.lines import Line2D
HL={'CHN':'#00897B','USA':'#283593'}

def spread(vals, mingap, lo, hi):
    idx=np.argsort(-np.asarray(vals)); out=np.array(vals,dtype=float)
    order=idx.tolist()
    for k in range(1,len(order)):
        a,b=order[k-1],order[k]
        if out[a]-out[b]<mingap: out[b]=out[a]-mingap
    lowest=out[order[-1]]
    if lowest<lo: out[order]+=lo-lowest
    top=out[order[0]]
    if top>hi: out[order]-=top-hi
    return out

def draw(bottom=0.20):
    fig,ax,r,W,H=frame('The global GDP share at PPP and market prices',
                       'Share of world GDP, 2025, market exchange rates versus purchasing power parity',
                       bottom=bottom)
    ax.set_xlim(-0.46,1.46); ax.set_ylim(0,28)
    fig.canvas.draw()
    axbb=ax.get_window_extent(r); ppu=axbb.height/28.0
    gap=30.0/ppu
    hl_mask=t.ISO.isin(HL).values
    def place(vals):
        out=np.array(vals,dtype=float)
        g=~hl_mask
        out[g]=spread(vals[g],gap,0.5,13.0)
        return out
    ly_m=place(t.mer_sh.values); ly_p=place(t.ppp_sh.values)
    for k,(_,row) in enumerate(t.iterrows()):
        hl=row.ISO in HL
        col=HL.get(row.ISO,GREY); lw=3.0 if hl else 1.4; z=4 if hl else 2
        ax.plot([0,1],[row.mer_sh,row.ppp_sh],color=col,lw=lw,zorder=z,solid_capstyle='round')
        ax.scatter([0,1],[row.mer_sh,row.ppp_sh],s=34 if hl else 16,color=col,zorder=z+1)
        fs=13 if hl else 10.5
        tc=col if hl else '#666'; fw='bold' if hl else 'normal'
        ax.text(-0.045,ly_m[k],f'{row.nm}  {row.mer_sh:.1f}',ha='right',va='center',
                fontsize=fs,color=tc,fontweight=fw,zorder=5)
        ax.text(1.045,ly_p[k],f'{row.ppp_sh:.1f}  {row.nm}',ha='left',va='center',
                fontsize=fs,color=tc,fontweight=fw,zorder=5)
        if abs(ly_m[k]-row.mer_sh)>0.10:
            ax.add_line(Line2D([-0.04,-0.005],[ly_m[k],row.mer_sh],color=col,lw=0.7,zorder=1))
        if abs(ly_p[k]-row.ppp_sh)>0.10:
            ax.add_line(Line2D([1.005,1.04],[row.ppp_sh,ly_p[k]],color=col,lw=0.7,zorder=1))
    ax.set_xticks([0,1]); ax.set_xticklabels(['Market exchange rates','Purchasing power parity'],fontsize=14)
    ax.set_yticks([]); ax.spines['left'].set_visible(False)
    ax.set_ylabel('Share of world GDP, %',fontsize=15,color='#333',labelpad=8)
    ax.tick_params(axis='x',length=0)
    return fig,ax,r,W,H

b=0.20
for _ in range(8):
    fig,ax,r,W,H=draw(b)
    y0,cap,wm=finish(fig,ax,r,W,H,caption=CAPTION_IMF)
    d=GAP_EDGE-y0
    if abs(d)<=1.0: break
    plt.close(fig); b+=d/H
fig.savefig('chart-2-global-shares.png',dpi=DPI,facecolor=PAPER)
print('wm %.1f'%y0)
