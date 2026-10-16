"""The ten biggest gainers improved broadly; four also gained on rights and voice

Self-contained: embeds its data (also saved as chart-06-ten-biggest-gains-drivers.csv) and the Moving Frontiers house style.
Needs only numpy, pandas, matplotlib and Pillow. Run `python chart-06-ten-biggest-gains-drivers.py` to write chart-06-ten-biggest-gains-drivers.png in the current folder.
Data: Social Progress Imperative, 2026 Global Social Progress Index (ranked countries), frozen October 2026."""
DATA = """\
country,spicountrycode,spiyear,status,score_spi,score_nbmc,score_ws,score_sh,score_ps,score_abk,score_aic,score_hw,score_eq,score_pr,score_pfc,score_incl,score_aae,GDPpc,population
Armenia,ARM,2011,Ranked,62.78,88.79,77.95,83.06,84.01,84.35000000000001,50.0,50.92,45.72,57.59,50.9,40.85,39.18,10438.5642,3044800
Armenia,ARM,2025,Ranked,72.74,92.19,82.81,90.55,87.01,87.61,83.79,55.92,56.99,68.9,67.51,50.870000000000005,48.76,20078.784900000002,3033500
Fiji,FJI,2011,Ranked,57.38,78.89,75.59,60.72,75.55,77.2,42.77,31.25,67.0,46.480000000000004,64.85,44.160000000000004,24.07,10167.349600000001,910419
Fiji,FJI,2025,Ranked,69.21000000000001,79.39,82.92,74.36,76.09,82.65,75.42,34.08,67.74,70.4,73.98,61.28,52.15,14104.4436,928784
Georgia,GEO,2011,Ranked,61.910000000000004,84.55,73.35000000000001,69.63,85.36,85.86,51.56,44.02,50.99,66.46000000000001,59.13,34.230000000000004,37.730000000000004,11294.3686,3786695
Georgia,GEO,2025,Ranked,71.54,88.44,80.07000000000001,91.65,84.5,86.01,74.01,54.620000000000005,60.01,63.6,68.87,48.83,57.89,25000.6326,3673850
"Gambia, The",GMB,2011,Ranked,41.44,51.08,42.2,35.59,61.5,40.27,34.12,46.86,58.47,41.34,37.87,38.32,9.63,2824.2126000000003,1926630
"Gambia, The",GMB,2025,Ranked,51.43,57.67,50.21,43.77,57.01,62.71,49.14,46.74,55.82,69.22,57.13,45.86,21.91,3030.9741000000004,2759988
Moldova,MDA,2011,Ranked,61.980000000000004,82.73,64.75,77.94,69.49,79.16,48.09,45.56,52.04,67.81,61.77,52.18,42.24,9649.951000000001,2862354
Moldova,MDA,2025,Ranked,72.02,89.21000000000001,74.36,88.88,80.99,91.36,80.5,53.28,62.42,69.60000000000001,67.85,61.42,44.44,16465.9287,2389275
Nepal,NPL,2011,Ranked,48.63,64.33,53.300000000000004,45.6,75.92,45.87,31.26,47.08,48.33,61.64,42.7,51.160000000000004,16.39,3085.3141,27341952
Nepal,NPL,2025,Ranked,58.21,77.66,65.82000000000001,67.27,77.16,56.44,60.02,48.14,46.2,61.64,55.34,55.84,26.97,5046.8159000000005,29651054
Saudi Arabia,SAU,2011,Ranked,59.0,86.83,77.85000000000001,90.15,68.24,78.31,54.14,54.77,33.85,26.35,63.83,37.7,35.92,54911.5475,23978487
Saudi Arabia,SAU,2025,Ranked,69.8,88.35000000000001,92.37,94.29,78.5,88.61,85.96000000000001,66.26,41.21,27.16,76.24,38.36,60.29,62676.698000000004,35300280
Eswatini,SWZ,2011,Ranked,39.95,41.84,42.74,44.29,23.3,59.09,33.82,30.79,62.33,22.61,63.1,43.62,11.84,8210.697,1111650
Eswatini,SWZ,2025,Ranked,49.59,60.14,52.0,65.43,31.76,68.4,62.22,44.12,66.18,19.23,64.6,46.13,14.9,10367.2683,1242822
Uzbekistan,UZB,2011,Ranked,56.7,84.54,73.83,82.94,82.22,90.14,43.2,38.300000000000004,33.38,14.1,69.99,44.08,23.650000000000002,5760.8051000000005,28385506
Uzbekistan,UZB,2025,Ranked,66.44,91.01,76.14,88.93,86.96000000000001,89.3,73.47,48.36,36.25,32.1,75.52,53.07,46.21,10450.205100000001,36361859
Vietnam,VNM,2011,Ranked,61.06,78.46000000000001,66.28,71.31,74.56,80.67,43.0,59.980000000000004,70.59,39.97,66.33,59.46,22.09,7274.7331,87455152
Vietnam,VNM,2025,Ranked,70.76,83.76,80.2,94.31,82.05,86.94,72.31,65.32000000000001,70.56,38.24,68.60000000000001,68.06,38.76,14415.216,100987686
"""

# ---- data (embedded) and the few shared definitions the chart code expects ----
import io, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
a=pd.read_csv(io.StringIO(DATA))
COMP=['score_nbmc','score_ws','score_sh','score_ps','score_abk','score_aic','score_hw','score_eq','score_pr','score_pfc','score_incl','score_aae']
CN=['Nutrition and medical care','Water and sanitation','Housing','Safety','Basic education','Information and communications','Health','Environmental quality','Rights and voice','Freedom and choice','Inclusive society','Advanced education']
cn=dict(zip(COMP,CN))

import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, warnings; warnings.filterwarnings('ignore')
from matplotlib.patches import Patch
plt.rcParams.update({'font.family':'DejaVu Sans','axes.edgecolor':'#888','axes.linewidth':1.0})
C=['FJI', 'SAU', 'MDA', 'GMB', 'ARM', 'UZB', 'VNM', 'SWZ', 'GEO', 'NPL']
NM={'FJI': 'Fiji', 'SAU': 'Saudi Arabia', 'MDA': 'Moldova', 'GMB': 'The Gambia', 'ARM': 'Armenia', 'UZB': 'Uzbekistan', 'VNM': 'Viet Nam', 'SWZ': 'Eswatini', 'GEO': 'Georgia', 'NPL': 'Nepal'}
S=a[a.spicountrycode.isin(C)].pivot(index='spiyear',columns='spicountrycode')
D=pd.DataFrame({k:(S[k].loc[2025,C]-S[k].loc[2011,C])/12 for k in COMP}).T     # contribution to the index change
G={'Rights and voice':['score_pr'],'Other opportunity':['score_pfc','score_incl','score_aae'],
   'Foundations of wellbeing':['score_abk','score_aic','score_hw','score_eq'],'Basic needs':['score_nbmc','score_ws','score_sh','score_ps']}
GC={'Rights and voice':'#C62828','Other opportunity':'#F9A825','Foundations of wellbeing':'#00897B','Basic needs':'#283593'}
GD=pd.DataFrame({g:D.loc[ks].sum() for g,ks in G.items()}); tot=GD.sum(axis=1)
assert np.allclose(tot,(S.score_spi.loc[2025,C]-S.score_spi.loc[2011,C]),atol=0.02); tot=(S.score_spi.loc[2025,C]-S.score_spi.loc[2011,C])   # label the published change
order=tot.sort_values(ascending=True).index; OFFX=0.04*((-1.2,15.2)[1]-(-1.2,15.2)[0])          # smallest fall at the bottom
W=H=1200; DPI=200
fig=plt.figure(figsize=(W/DPI,H/DPI),dpi=DPI); fig.patch.set_facecolor('white'); r=fig.canvas.get_renderer(); bb=lambda o:o.get_window_extent(r)
tt=fig.text(0.04,1-22/H,'The ten biggest gainers improved broadly;\nfour also gained on rights and voice',fontsize=14.5,fontweight='bold',color='#222',ha='left',va='top',linespacing=1.25); fig.canvas.draw()
st=fig.text(0.04,(bb(tt).y0-14)/H,'Contribution to the change in the Social Progress Index, 2011-2025 (points)',fontsize=9.6,color='#646464',ha='left',va='top'); fig.canvas.draw()
wm=fig.text(0.96,0,'movingfrontiers.substack.com',fontsize=7.7,color='#666',ha='right',va='bottom'); fig.canvas.draw(); wm.set_y((10-bb(wm).y0)/H); fig.canvas.draw()
ct=fig.text(0.04,0,'Source: Social Progress Imperative, 2026 Global Social Progress Index.\nNote: The index is the simple average of its 12 components, so each contributes its change divided by 12. Basic needs\nand foundations of wellbeing each group four components; other opportunity covers freedom and choice, inclusive\nsociety and advanced education.',
 fontsize=6.4,color='#666',ha='left',va='bottom',linespacing=1.35); fig.canvas.draw(); ct.set_y((bb(wm).y1+20-bb(ct).y0)/H); fig.canvas.draw()
ax=fig.add_axes([0.27,0.2,0.68,0.55]); ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False); ax.spines['left'].set_visible(False)
for i,c in enumerate(order):
    pos=neg=0
    for g in G:
        v=GD.loc[c,g]
        if v>=0: ax.barh(i,v,left=pos,color=GC[g],height=.62,edgecolor='white',lw=.6); pos+=v
        else: ax.barh(i,v,left=neg,color=GC[g],height=.62,edgecolor='white',lw=.6); neg+=v
    ax.scatter(tot[c],i,marker='D',s=34,c='#141414',zorder=5,edgecolor='white',lw=.6)
    ax.text((min(neg,tot[c])-OFFX) if tot[c]<0 else (max(pos,tot[c])+OFFX),i,(f'{tot[c]:+.1f}' if tot[c]>0 else f'{tot[c]:.1f}').replace('-','−') if abs(tot[c])>=0.05 else f'{tot[c]:.2f}'.replace('-','−'),ha='right' if tot[c]<0 else 'left',va='center',fontsize=8.6,fontweight='bold',color='#141414')
ax.axvline(0,c='#444',lw=.9); ax.set_yticks(range(len(order))); ax.set_yticklabels([NM[c] for c in order],fontsize=9.5,color='#222'); ax.tick_params(axis='y',length=0)
ax.tick_params(axis='x',labelsize=9,colors='#444',length=3); ax.grid(axis='x',c='#eeeeee',lw=.8); ax.set_axisbelow(True)
ax.set_xlim(-1.2,15.2); ax.set_xticks([0, 2, 4, 6, 8, 10, 12, 14]); ax.set_xticklabels([str(v).replace('-','−') for v in [0, 2, 4, 6, 8, 10, 12, 14]])
ax.set_xlabel('Contribution to the change (points)',fontsize=9,color='#444')
h=[Patch(facecolor=GC[g],label=g) for g in G]+[plt.Line2D([],[],marker='D',ls='',c='#141414',ms=5.5,label='Net change')]
lg=fig.legend(handles=h,loc='upper left',ncol=3,frameon=False,fontsize=8.6,handlelength=1.2,columnspacing=1.2,bbox_to_anchor=(0.04,0.5))
# lay out: legend just above caption, axes between subtitle and legend
for _ in range(5):
    fig.canvas.draw(); lb=bb(lg); err=(bb(ct).y1+20)-lb.y0; ay=lg.get_bbox_to_anchor().transformed(fig.transFigure.inverted()).y0; lg.set_bbox_to_anchor((0.04,ay+err/H)); fig.canvas.draw(); lb=bb(lg)
    tb=ax.get_tightbbox(r); p=ax.get_position()
    y0=p.y0+(lb.y1+24-tb.y0)/H; y1=p.y1+(bb(st).y0-30-tb.y1)/H; ax.set_position([p.x0,y0,p.width,y1-y0])
fig.canvas.draw(); tb=ax.get_tightbbox(r); lb=bb(lg)
print('cap-wm',round(bb(ct).y0-bb(wm).y1,1),'wm-edge',round(bb(wm).y0,1)); print('gaps sub-plot',round(bb(st).y0-tb.y1,1),'plot-legend',round(tb.y0-lb.y1,1),'legend-cap',round(lb.y0-bb(ct).y1,1),'right',round(W-max(tb.x1,lb.x1,bb(st).x1)))
print({c:(GD.loc[c].idxmin(),round(GD.loc[c].min(),2)) for c in order}); print('rv share of gross losses',{c:round(-GD.loc[c,'Rights and voice']/-GD.loc[c][GD.loc[c]<0].sum(),2) for c in order})
fig.savefig('chart-06-ten-biggest-gains-drivers.png',dpi=DPI,facecolor='white')

