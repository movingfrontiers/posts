#!/usr/bin/env python3
"""
Four perspectives on China and the United States

Self-contained: data embedded below, style constants included, no input files
and no network. Needs only matplotlib, numpy and pandas. Running it writes chart-1-four-perspectives.png.

China as a ratio of the United States on four perspectives: GDP and GDP per
capita, each under market exchange rates and purchasing power parity.

Source: IMF World Economic Outlook, April 2026 vintage (dataset IMF.RES:WEO(9.0.0),
published 14 April 2026). Values from 2026 are WEO projections.
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

YEARS = [1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031]
CHN_PPPGDP = [271.921, 312.828, 362.053, 416.864, 497.56, 582.594, 647.219, 740.858, 852.888, 923.559, 995.375, 1134.039, 1325.481, 1545.987, 1785.885, 2024.185, 2266.714, 2520.675, 2751.244, 3006.613, 3338.298, 3697.446, 4100.895, 4605.114, 5207.28, 5984.795, 6950.678, 8149.415, 9106.992, 10028.619, 11225.111, 12539.482, 13775.337, 15098.444, 16512.19, 17835.078, 19224.458, 20917.221, 22803.146, 24798.514, 25960.998, 29420.351, 32493.554, 35507.59, 38209.549, 41241.951, 44295.453, 47093.755, 49781.417, 52523.765, 55279.714, 58129.519]
USA_PPPGDP = [2857.325, 3207.025, 3343.8, 3634.025, 4037.65, 4339.0, 4579.625, 4855.25, 5236.425, 5641.6, 5963.125, 6158.125, 6520.325, 6858.55, 7287.25, 7639.75, 8073.125, 8577.55, 9062.825, 9631.175, 10250.95, 10581.925, 10929.1, 11456.45, 12217.175, 13039.2, 13815.6, 14474.25, 14769.85, 14478.05, 15048.975, 15599.725, 16253.95, 16880.675, 17608.125, 18295.0, 18804.9, 19612.1, 20656.525, 21539.975, 21375.275, 23725.65, 26054.6, 27811.5, 29298.025, 30767.075, 32383.92, 33790.035, 35065.9, 36360.58, 37677.878, 39031.262]
CHN_NGDPD = [303.55, 289.215, 285.139, 306.013, 314.832, 310.709, 301.471, 328.305, 409.363, 458.985, 397.359, 415.946, 495.515, 621.918, 566.382, 737.894, 868.768, 967.89, 1035.515, 1101.119, 1220.346, 1351.395, 1486.628, 1680.932, 1978.988, 2326.577, 2798.78, 3613.61, 4655.583, 5176.499, 6138.878, 7628.383, 8682.534, 9787.51, 10702.458, 11305.64, 11452.0, 12516.152, 14107.927, 14593.45, 15110.191, 18183.505, 18337.777, 18366.936, 18945.112, 19626.247, 20851.593, 21928.979, 23259.956, 24662.788, 26046.793, 27496.67]
USA_NGDPD = [2857.325, 3207.025, 3343.8, 3634.025, 4037.65, 4339.0, 4579.625, 4855.25, 5236.425, 5641.6, 5963.125, 6158.125, 6520.325, 6858.55, 7287.25, 7639.75, 8073.125, 8577.55, 9062.825, 9631.175, 10250.95, 10581.925, 10929.1, 11456.45, 12217.175, 13039.2, 13815.6, 14474.25, 14769.85, 14478.05, 15048.975, 15599.725, 16253.95, 16880.675, 17608.125, 18295.0, 18804.9, 19612.1, 20656.525, 21539.975, 21375.275, 23725.65, 26054.6, 27811.5, 29298.025, 30767.075, 32383.92, 33790.035, 35065.9, 36360.58, 37677.878, 39031.262]
CHN_PPPPC = [275.489, 312.603, 356.162, 404.691, 476.786, 550.391, 602.025, 677.821, 768.187, 819.455, 870.593, 979.114, 1131.236, 1304.443, 1490.1, 1671.209, 1852.057, 2038.952, 2205.211, 2390.26, 2633.912, 2897.072, 3192.526, 3563.585, 4005.97, 4577.071, 5287.778, 6167.771, 6857.571, 7514.889, 8371.264, 9294.288, 10134.737, 11042.848, 11996.128, 12893.511, 13807.5, 14939.698, 16225.262, 17586.601, 18384.413, 20827.093, 23016.507, 25188.583, 27132.068, 29352.032, 31596.218, 33669.345, 35680.538, 37749.565, 39847.633, 42034.314]
USA_PPPPC = [12552.943, 13948.701, 14404.994, 15513.679, 17086.441, 18199.32, 19034.766, 20000.968, 21375.999, 22814.077, 23847.977, 24302.776, 25392.931, 26364.192, 27674.021, 28671.48, 29946.973, 31440.087, 32833.666, 34496.241, 36312.782, 37101.453, 37945.761, 39405.354, 41641.617, 44034.256, 46216.853, 47943.353, 48470.553, 47102.428, 48586.288, 50008.108, 51736.738, 53363.904, 55263.817, 57006.926, 58179.697, 60292.978, 63165.278, 65561.32, 64517.998, 71365.73, 77948.992, 82536.095, 86173.365, 89991.152, 94429.753, 98277.579, 101714.787, 105171.151, 108659.462, 112241.909]
CHN_NGDPDPC = [307.533, 289.007, 280.5, 297.077, 301.687, 293.534, 280.42, 300.37, 368.709, 407.249, 347.545, 359.122, 422.899, 524.75, 472.576, 609.22, 709.842, 782.918, 829.999, 875.39, 962.851, 1058.863, 1157.332, 1300.759, 1522.439, 1779.327, 2129.192, 2734.911, 3505.657, 3878.98, 4578.143, 5654.172, 6387.88, 7158.485, 7775.35, 8173.185, 8225.121, 8939.406, 10038.3, 10349.377, 10700.359, 12872.366, 12989.394, 13029.245, 13452.66, 13968.065, 14873.569, 15677.967, 16671.437, 17725.491, 18775.478, 19883.249]
USA_NGDPDPC = [12552.943, 13948.701, 14404.994, 15513.679, 17086.441, 18199.32, 19034.766, 20000.968, 21375.999, 22814.077, 23847.977, 24302.776, 25392.931, 26364.192, 27674.021, 28671.48, 29946.973, 31440.087, 32833.666, 34496.241, 36312.782, 37101.453, 37945.761, 39405.354, 41641.617, 44034.256, 46216.853, 47943.353, 48470.553, 47102.428, 48586.288, 50008.108, 51736.738, 53363.904, 55263.817, 57006.926, 58179.697, 60292.978, 63165.278, 65561.32, 64517.998, 71365.73, 77948.992, 82536.095, 86173.365, 89991.152, 94429.753, 98277.579, 101714.787, 105171.151, 108659.462, 112241.909]

import numpy as _np
ts = {'years': YEARS, 'CHN_PPPGDP': CHN_PPPGDP, 'USA_PPPGDP': USA_PPPGDP, 'CHN_NGDPD': CHN_NGDPD, 'USA_NGDPD': USA_NGDPD, 'CHN_PPPPC': CHN_PPPPC, 'USA_PPPPC': USA_PPPPC, 'CHN_NGDPDPC': CHN_NGDPDPC, 'USA_NGDPDPC': USA_NGDPDPC}
yrs=_np.array(ts['years'])
CUT=2025
i=list(yrs).index(CUT)

# ----- FIGURE -----

LAB2={'GDP per capita, PPP':'GDP per capita,\nPPP',
      'GDP per capita, market rates':'GDP per capita,\nmarket rates'}
S=[('GDP, PPP','#00897B',np.array(ts['CHN_PPPGDP'])/np.array(ts['USA_PPPGDP'])),
   ('GDP, market rates','#283593',np.array(ts['CHN_NGDPD'])/np.array(ts['USA_NGDPD'])),
   ('GDP per capita, PPP','#F9A825',np.array(ts['CHN_PPPPC'])/np.array(ts['USA_PPPPC'])),
   ('GDP per capita, market rates','#C62828',np.array(ts['CHN_NGDPDPC'])/np.array(ts['USA_NGDPDPC']))]
LC={'GDP per capita, PPP':'#B8860B'}

def draw(bottom=0.20):
    fig,ax,r,W,H=frame('Four perspectives on China and the United States',
                       'China as a ratio of the United States, 1980 to 2031, four perspectives',
                       bottom=bottom,left=0.10,right=0.685,box_aspect=None)
    ax.axhline(1.0,color='#C62828',lw=1.2,ls=(0,(2,2.5)),zorder=2)
    ax.text(1981,1.02,'Parity with the United States',fontsize=10.5,color='#C62828',va='bottom')
    for lab,col,v in S:
        ax.plot(yrs[:i+1],v[:i+1],color=col,lw=2.4,zorder=3)
        ax.plot(yrs[i:],v[i:],color=col,lw=2.4,ls=(0,(3,2.5)),zorder=3)
        ax.text(2032.4,v[-1],LAB2.get(lab,lab),color=LC.get(lab,col),fontsize=12,va='center',ha='left',
                fontweight='bold',linespacing=1.3)
    ppp=S[0][2]; k=list(yrs).index(2016)
    x0,y0=yrs[k-1],ppp[k-1]; x1,y1=yrs[k],ppp[k]
    xpar=x0+(1.0-y0)*(x1-x0)/(y1-y0)          # exact crossing of the 1.0 line
    ax.scatter([xpar],[1.0],s=80,color='#00897B',zorder=5,edgecolor=PAPER,lw=1.6)
    ax.annotate('parity, 2016',(xpar,1.0),xytext=(1998,1.30),fontsize=11.5,
                color='#00614F',fontweight='bold',ha='right',
                arrowprops=dict(arrowstyle='-',color='#00897B',lw=0.9,shrinkA=0,shrinkB=7))
    ax.axvspan(2025,2031,color='#F5F5F5',zorder=0)
    ax.set_xlim(1980,2031); ax.set_ylim(0,1.6)
    ax.set_yticks(np.arange(0,1.61,0.2))
    ax.set_xticks([1980,1990,2000,2010,2020,2030])
    ax.set_ylabel('Ratio, China / United States',fontsize=15,color='#333',labelpad=8)
    ax.grid(axis='y',color='#F2F2F2',lw=0.8,zorder=0); ax.set_axisbelow(True)
    return fig,ax,r,W,H

b=0.20
for _ in range(8):
    fig,ax,r,W,H=draw(b)
    y0,cap,wm=finish(fig,ax,r,W,H,caption=(
        'Source: IMF WEO database April 2026. Note: On this series China reaches parity with the '
        'United States on GDP at purchasing power parity in 2016. The Maddison Project Database '
        'dates the same crossing to 2014 because it measures real GDP in constant 2011 '
        'international dollars on the ICP 2011 benchmark, while the IMF series is current-price '
        'and anchored on the ICP 2017 and 2021 benchmarks.'))
    d=GAP_EDGE-y0
    if abs(d)<=1.0: break
    plt.close(fig); b+=d/H
fig.savefig('chart-1-four-perspectives.png',dpi=DPI,facecolor=PAPER)
print('wm %.1f'%y0, {l:round(v[i],3) for l,c,v in S})
