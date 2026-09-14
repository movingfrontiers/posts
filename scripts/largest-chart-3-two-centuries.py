#!/usr/bin/env python3
"""
Two Centuries of China and the United States

Self-contained: data embedded below, style constants included, no input files
and no network. Needs only matplotlib, numpy and pandas. Running it writes chart-3-two-centuries.png.

Log scale from 1820. Bracket measures give the ratio between the two economies
at three moments: 1820, the widest US lead in 1940-1990, and 2022. Bare year
labels mark the two changes of lead.

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

import pandas as _pd
COLS = ['year', 'CHN', 'USA']
ROWS = [
    (1820, 336.042, 26.69),
    (1821, None, 27.964),
    (1822, None, 29.658),
    (1823, None, 30.227),
    (1824, None, 31.982),
    (1825, None, 33.62),
    (1826, None, 34.81),
    (1827, None, 35.894),
    (1828, None, 36.861),
    (1829, None, 36.569),
    (1830, 346.014, 40.238),
    (1831, None, 44.058),
    (1832, None, 47.057),
    (1833, None, 50.15),
    (1834, None, 49.145),
    (1835, None, 52.438),
    (1836, None, 54.66),
    (1837, None, 54.344),
    (1838, None, 55.243),
    (1839, None, 59.39),
    (1840, 349.788, 57.904),
    (1841, None, 58.728),
    (1842, None, 60.164),
    (1843, None, 63.128),
    (1844, None, 68.683),
    (1845, None, 71.88),
    (1846, None, 74.456),
    (1847, None, 78.626),
    (1848, None, 82.933),
    (1849, None, 82.996),
    (1850, 353.496, 85.638),
    (1851, None, 92.211),
    (1852, None, 100.198),
    (1853, None, 110.971),
    (1854, None, 114.357),
    (1855, None, 115.306),
    (1856, None, 121.206),
    (1857, None, 122.03),
    (1858, None, 126.084),
    (1859, None, 133.003),
    (1860, None, 140.152),
    (1861, None, 140.904),
    (1862, None, 149.042),
    (1863, None, 162.622),
    (1864, None, 172.059),
    (1865, None, 167.081),
    (1866, None, 169.593),
    (1867, None, 179.172),
    (1868, None, 185.632),
    (1869, None, 194.685),
    (1870, 338.31, 193.278),
    (1871, None, 202.149),
    (1872, None, 210.342),
    (1873, None, 220.908),
    (1874, None, 219.512),
    (1875, None, 230.981),
    (1876, None, 233.742),
    (1877, None, 241.295),
    (1878, None, 251.432),
    (1879, None, 282.359),
    (1880, None, 315.652),
    (1881, None, 326.883),
    (1882, None, 347.743),
    (1883, None, 356.233),
    (1884, None, 362.654),
    (1885, None, 365.399),
    (1886, None, 376.421),
    (1887, 343.239, 393.366),
    (1888, None, 391.556),
    (1889, None, 415.86),
    (1890, 366.32, 421.879),
    (1891, None, 440.079),
    (1892, None, 482.817),
    (1893, None, 459.473),
    (1894, None, 446.221),
    (1895, None, 500.099),
    (1896, None, 489.991),
    (1897, None, 536.745),
    (1898, None, 547.965),
    (1899, None, 597.661),
    (1900, 388.8, 613.998),
    (1901, None, 683.106),
    (1902, None, 690.127),
    (1903, None, 723.766),
    (1904, None, 714.622),
    (1905, None, 767.533),
    (1906, None, 855.994),
    (1907, None, 869.071),
    (1908, None, 799.356),
    (1909, None, 890.11),
    (1910, None, 893.975),
    (1911, 387.034, 917.452),
    (1912, None, 954.787),
    (1913, 430.583, 986.598),
    (1914, None, 905.134),
    (1915, None, 925.041),
    (1916, None, 1046.398),
    (1917, None, 1014.196),
    (1918, None, 1099.047),
    (1919, None, 1102.17),
    (1920, None, 1085.155),
    (1921, None, 1054.214),
    (1922, None, 1105.913),
    (1923, None, 1244.264),
    (1924, None, 1274.654),
    (1925, None, 1296.54),
    (1926, None, 1372.771),
    (1927, None, 1378.145),
    (1928, None, 1385.247),
    (1929, 488.735, 1461.345),
    (1930, 494.868, 1322.627),
    (1931, 500.03, 1237.726),
    (1932, 515.663, 1051.217),
    (1933, 461.5, 1015.525),
    (1934, 470.973, 1100.53),
    (1935, 508.829, 1237.782),
    (1936, 540.976, 1359.902),
    (1937, 528.002, 1462.309),
    (1938, 514.876, 1373.408),
    (1939, None, 1469.481),
    (1940, None, 1592.32),
    (1941, None, 1815.099),
    (1942, None, 2013.171),
    (1943, None, 2203.245),
    (1944, None, 2361.836),
    (1945, None, 2314.668),
    (1946, None, 2103.901),
    (1947, None, 2070.709),
    (1948, None, 2168.923),
    (1949, None, 2126.236),
    (1950, 436.905, 2320.61),
    (1951, 529.606, 2497.408),
    (1952, 595.649, 2590.802),
    (1953, 672.668, 2709.833),
    (1954, 624.48, 2691.885),
    (1955, 681.085, 2882.221),
    (1956, 738.922, 2938.405),
    (1957, 761.703, 2993.554),
    (1958, 766.245, 2963.55),
    (1959, 743.928, 3183.157),
    (1960, 705.093, 3262.376),
    (1961, 577.128, 3338.584),
    (1962, 616.503, 3539.745),
    (1963, 705.534, 3692.868),
    (1964, 804.505, 3906.86),
    (1965, 896.127, 4156.141),
    (1966, 927.339, 4428.3),
    (1967, 933.378, 4538.98),
    (1968, 912.373, 4754.926),
    (1969, 1006.176, 4903.77),
    (1970, 1144.004, 4912.636),
    (1971, 1216.238, 5065.682),
    (1972, 1233.565, 5334.297),
    (1973, 1334.375, 5637.203),
    (1974, 1367.632, 5621.366),
    (1975, 1460.734, 5605.795),
    (1976, 1413.711, 5899.591),
    (1977, 1493.489, 6166.912),
    (1978, 1667.552, 6518.624),
    (1979, 1801.38, 6740.172),
    (1980, 1893.784, 6743.208),
    (1981, 1949.955, 6911.865),
    (1982, 2128.598, 6782.207),
    (1983, 2278.862, 7066.237),
    (1984, 2534.0, 7581.108),
    (1985, 2752.674, 7874.872),
    (1986, 2931.539, 8146.028),
    (1987, 3177.307, 8432.567),
    (1988, 3354.463, 8787.203),
    (1989, 3380.56, 9091.291),
    (1990, 3385.122, 9250.378),
    (1991, 3508.948, 9224.688),
    (1992, 3755.038, 9552.658),
    (1993, 4126.17, 9814.94),
    (1994, 4438.753, 10211.204),
    (1995, 4810.0, 10488.857),
    (1996, 5127.59, 10886.953),
    (1997, 5291.339, 11375.561),
    (1998, 5338.703, 11881.793),
    (1999, 5578.503, 12438.445),
    (2000, 5952.682, 12947.418),
    (2001, 6329.737, 13073.81),
    (2002, 6814.494, 13307.343),
    (2003, 7248.623, 13680.912),
    (2004, 7830.953, 14198.91),
    (2005, 8602.94, 14673.826),
    (2006, 9489.543, 15065.164),
    (2007, 10358.206, 15333.183),
    (2008, 10799.148, 15288.553),
    (2009, 11572.544, 14864.003),
    (2010, 12858.808, 15239.587),
    (2011, 13691.527, 15477.886),
    (2012, 14773.158, 15830.888),
    (2013, 15925.464, 16122.473),
    (2014, 17103.948, 16491.318),
    (2015, 18301.225, 16937.635),
    (2016, 19545.708, 17220.066),
    (2017, 20894.362, 17606.125),
    (2018, 22294.284, 18124.693),
    (2019, 23631.941, 18540.553),
    (2020, 24151.844, 18027.36),
    (2021, 26180.599, 19099.379),
    (2022, 26966.017, 19493.171),
]
p = _pd.DataFrame(ROWS, columns=COLS).set_index('year')

# ----- HELPER -----


def logchart(series, title, sub, outfile, ylim, yticks, annot=None, bottom=0.20,
             right=0.775, end_labels=True):
    global p
    fig,ax,r,W,H=frame(title,sub,bottom=bottom,left=0.145,right=right,box_aspect=None)
    ax.set_yscale('log'); ax.set_ylim(*ylim)
    ax.set_xlim(1820,2022); ax.set_xticks([1820,1860,1900,1940,1980,2020])
    ax.set_yticks(yticks); ax.set_yticklabels([f'{v:,}' for v in yticks])
    ax.set_ylabel('Billions of 2011 international dollars',fontsize=15,color='#333',labelpad=8)
    ax.grid(axis='y',color='#F2F2F2',lw=0.8,zorder=0); ax.set_axisbelow(True)
    ends=[]
    for iso,col,lab,lcol in series:
        s=p[iso].dropna()
        ax.plot(s.index,s.values,color=col,lw=2.2,zorder=3)
        e=s[s.index<1900]
        ax.scatter(e.index,e.values,s=15,color=col,zorder=4)
        ends.append((s.iloc[-1],lab,lcol or col))
    if not end_labels:
        if annot: annot(ax,p)
        return fig,ax,r,W,H,outfile
    # de-collide the end labels in log space
    fig.canvas.draw()
    ends.sort(key=lambda t:-t[0])
    ys=[np.log10(v) for v,_,_ in ends]
    span=np.log10(ylim[1])-np.log10(ylim[0])
    mingap=span*(30.0/ax.get_window_extent(r).height)
    for k in range(1,len(ys)):
        if ys[k-1]-ys[k]<mingap: ys[k]=ys[k-1]-mingap
    for (v,lab,col),yy in zip(ends,ys):
        ax.text(2032,10**yy,lab,color=col,fontsize=12.5,fontweight='bold',
                va='center',ha='left',clip_on=False)
    if annot: annot(ax,p)
    return fig,ax,r,W,H,outfile

def render(fn,*a,**kw):
    b=0.20
    for _ in range(8):
        fig,ax,r,W,H,out=fn(bottom=b,**kw)
        y0,cap,wm=finish(fig,ax,r,W,H,caption='Source: Maddison Project Database 2023.')
        d=GAP_EDGE-y0
        if abs(d)<=1.0: break
        plt.close(fig); b+=d/H
    fig.savefig(out,dpi=DPI,facecolor=PAPER)
    print(out,'wm %.1f'%y0)

# ----- FIGURE -----

CN='#C62828'; US='#283593'

def ann(ax,p):
    peak=int((p.USA/p.CHN).loc[1940:1990].idxmax())
    fig=ax.figure
    def bracket(yr,x,dx,ha,txt,sub=None,above=False):
        a,b=p.loc[yr,'USA'],p.loc[yr,'CHN']
        lo,hi=min(a,b),max(a,b)
        ax.plot([x,x],[lo,hi],color='#777',lw=1.1,zorder=6)
        for yy in (lo,hi):
            ax.plot([x-2.2,x+2.2],[yy,yy],color='#777',lw=1.1,zorder=6)
        anchor=(x,hi) if above else (x,np.sqrt(lo*hi))
        oy=12 if above else (7 if sub else 0)
        va='bottom' if above else 'center'
        ax.annotate(txt,anchor,xytext=(dx,oy),textcoords='offset points',ha=ha,va=va,
                    fontsize=12.5,color='#333',fontweight='bold',zorder=7)
        if sub:
            ax.annotate(sub,anchor,xytext=(dx,-10),textcoords='offset points',ha=ha,
                        va='center',fontsize=10.5,color='#777',zorder=7)
    bracket(1820,1827,0,'left','')
    bracket(peak,peak,0,'left','')
    bracket(2022,2022,10,'left','China 1.4x the US')
    a0,b0=p.loc[1820,'USA'],p.loc[1820,'CHN']
    fig.canvas.draw()
    px,py=ax.transData.transform((1846,860))
    tx,ty=ax.transData.inverted().transform((px-40,py-20))
    ax.annotate('China 12.6x\nthe US',(1829,np.sqrt(a0*b0)),xytext=(tx,ty),
                fontsize=12.5,color='#333',fontweight='bold',ha='left',va='center',
                linespacing=1.3,zorder=7,
                arrowprops=dict(arrowstyle='-',color='#777',lw=0.9,shrinkA=4,shrinkB=2))
    a,b=p.loc[peak,'USA'],p.loc[peak,'CHN']; mid=np.sqrt(a*b)
    ax.annotate('US 5.8x China',(peak+1.5,mid),xytext=(1983,1120),fontsize=12.5,
                color='#333',fontweight='bold',ha='left',va='center',zorder=7,
                arrowprops=dict(arrowstyle='-',color='#777',lw=0.9,shrinkA=3,shrinkB=2))
    ax.text(1983,865,f'widest US lead, {peak}',fontsize=10.5,color='#777',ha='left',
            va='center',zorder=7)
    for yr,iso,col,dx,dy,ha,va in ((1887,'USA',US,7,-15,'center','top'),
                                   (2014,'CHN',CN,-3,-1,'right','bottom')):
        ax.scatter([yr],[p.loc[yr,iso]],s=46,color=col,zorder=7,edgecolor=PAPER,lw=1.3)
        ax.annotate(str(yr),(yr,p.loc[yr,iso]),xytext=(dx,dy),textcoords='offset points',
                    ha=ha,va=va,fontsize=12.5,color=col,fontweight='bold',zorder=7)
    # sit the label 15 px to the left of the US line, 40 px above the 1922 level
    fig.canvas.draw()
    x0,y0=ax.transData.transform((1922,p.loc[1922,'USA']))
    ytar=ax.transData.inverted().transform((x0,y0+60))[1]
    us=p['USA'].dropna()
    xtar=float(np.interp(np.log(ytar),np.log(us.values),us.index.values))
    ax.annotate('United States',(xtar,ytar),xytext=(-10,0),textcoords='offset points',
                ha='right',va='center',fontsize=13,color=US,fontweight='bold',zorder=7)
    ax.annotate('China',(1930,p.loc[1930,'CHN']),xytext=(0,-12),textcoords='offset points',
                ha='center',va='top',fontsize=13,color=CN,fontweight='bold',zorder=7)

def build(bottom=0.20):
    return logchart([('CHN',CN,'China',None),('USA',US,'United States',None)],
        'Two centuries of China and the United States',
        'GDP, 1820 to 2022, billions of 2011 international dollars, log scale',
        'chart-3-two-centuries.png',(20,60000),[100,1000,10000],
        annot=ann,bottom=bottom,right=0.70,end_labels=False)
render(build)
