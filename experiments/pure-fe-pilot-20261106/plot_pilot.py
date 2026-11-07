"""Read-only numerical-result analysis and standard scientific figures (no models)."""
import argparse,gzip,json,os
from pathlib import Path
def read(path):
 if path.exists():return json.loads(path.read_text())
 return json.loads(gzip.decompress(Path(str(path)+'.gz').read_bytes()))
def plot(out):
 os.environ['MPLCONFIGDIR']=str(out/'mpl-cache')
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 import numpy as np
 from matplotlib.colors import TwoSlopeNorm
 figdir=out/'figures';figdir.mkdir(exist_ok=True)
 # Actual accepted phases: show all native integration rows, only downsample display.
 d=read(out/'single-01/model.dat.tp.json');rows=d['layer_rows']
 colors=plt.get_cmap('tab10')
 fig,axes=plt.subplots(1,2,figsize=(11,4.6),constrained_layout=True)
 names=list(dict.fromkeys(row['actual_eos_id'] for row in rows))
 for i,name in enumerate(names):
  selected=[r for r in rows if r['actual_eos_id']==name];step=max(1,len(selected)//1500)
  selected=selected[::step]
  axes[0].plot([r['radius_cm']/6.3781e8 for r in selected],[r['pressure_cgs']/1e10 for r in selected],'.',ms=2,color=colors(i%10),label=name)
  axes[1].plot([r['pressure_cgs']/1e10 for r in selected],[r['temperature_K'] for r in selected],'.',ms=2,color=colors(i%10),label=name)
 axes[0].set(xlabel='Radius (Earth equatorial radii)',ylabel='Pressure (GPa)',yscale='log')
 axes[1].set(xlabel='Pressure (GPa)',ylabel='Temperature (K)',xscale='log')
 axes[0].legend(fontsize=8,markerscale=3)
 fig.suptitle('Conditional single-planet check: pure Fe + water + H/He\nExample external TP in gas; native thermal model below gas')
 for ext in ('png','svg'):fig.savefig(figdir/('single-planet-phases.'+ext),dpi=180)
 plt.close(fig)
 summary=out/'summary.json'
 if not summary.exists():return
 s=read(summary);samples=s['samples'];good=[x for x in samples if x['status']=='PASS_CONDITIONAL_NUMERICAL']
 if not good:return
 residual=np.array([x['radius_earth']-2.39 for x in good]);span=max(.01,float(np.max(np.abs(residual))))
 norm=TwoSlopeNorm(vmin=-span,vcenter=0,vmax=span)
 fig,axes=plt.subplots(1,2,figsize=(12,6.2),constrained_layout=True)
 height=np.sqrt(3)/2
 axes[0].plot([0,1,.5,0],[0,0,height,0],color='black',lw=1)
 for fraction in (.25,.5,.75):
  axes[0].plot([fraction,.5+.5*fraction],[0,(1-fraction)*height],color='.9',lw=.7)
  axes[0].plot([1-fraction,.5*(1-fraction)],[0,(1-fraction)*height],color='.9',lw=.7)
  axes[0].plot([fraction/2,1-fraction/2],[fraction*height,fraction*height],color='.9',lw=.7)
 for value in (.2,.4,.6,.8):axes[0].text(value,-.018,str(value),ha='center',va='top',fontsize=7)
 axes[0].text(.5,-.07,'H2O mass fraction along base',ha='center',fontsize=8)
 axes[0].text(0,-.04,'Pure Fe',ha='center');axes[0].text(1,-.04,'H2O',ha='center');axes[0].text(.5,height+.025,'H/He',ha='center')
 axes[0].scatter([x['fractions'][2]+.5*x['fractions'][3] for x in good],[height*x['fractions'][3] for x in good],c=residual,cmap='coolwarm',norm=norm,s=30)
 axes[0].text(.5,.3,'Gas fraction ≤0.3% in this pilot\nPoints lie near the base;\nright panel resolves the gas axis.',ha='center',fontsize=9,color='.35')
 axes[0].set_aspect('equal');axes[0].axis('off');axes[0].set_title('Direct composition samples (mass fractions)')
 scatter=axes[1].scatter([x['fractions'][0] for x in good],[x['gas_fraction'] for x in good],c=residual,cmap='coolwarm',norm=norm,s=43,label='Direct numerical samples')
 inside=[x for x in good if x['inside_radius_interval']]
 axes[1].scatter([x['fractions'][0] for x in inside],[x['gas_fraction'] for x in inside],facecolors='none',edgecolors='green',s=95,lw=1.4,label='Direct sample within radius interval')
 failed=[x for x in samples if x['status']!='PASS_CONDITIONAL_NUMERICAL']
 if failed:axes[1].scatter([x['fractions'][0] for x in failed],[x['gas_fraction'] for x in failed],c='.5',marker='x',s=48,label='TP-boundary trial failure')
 for target,marker,color in [('2.28','+', '.55'),('2.49','+', '.55'),('2.39','x','black')]:
  roots=s['coarse_crossings'][target]
  if roots:
   xs=[(1-x['gas_fraction'])*x['u'] for x in roots];ys=[x['gas_fraction'] for x in roots]
   axes[1].scatter(xs,ys,c=color,marker=marker,s=65,label=('Unconfirmed coarse R=2.39 crossing' if target=='2.39' else 'Coarse radius-interval crossing' if target=='2.28' else None))
 # Dashed segments are visualization of unconfirmed coarse crossings only.
 roots=s['coarse_crossings']['2.39'];unique={}
 for root in roots:unique.setdefault(root['u'],[]).append(root)
 for root in roots:
  g=root['gas_fraction'];fe=(1-g)*root['u'];water=(1-g)*(1-root['u'])
  axes[0].plot(water+.5*g,height*g,'x',color='black',ms=5)
 ordered=[.1,.3,.5,.7,.9,1.]
 for u0,u1 in zip(ordered,ordered[1:]):
  if len(unique.get(u0,[]))==len(unique.get(u1,[]))==1:
   pair=[unique[u0][0],unique[u1][0]];gs=[v['gas_fraction'] for v in pair];fes=[(1-v['gas_fraction'])*v['u'] for v in pair]
   axes[1].plot(fes,gs,'--',color='black',lw=.9)
   xs=[(1-v['gas_fraction'])*(1-v['u'])+.5*v['gas_fraction'] for v in pair]
   axes[0].plot(xs,[height*g for g in gs],'--',color='black',lw=.9)
 for water in (.25,.5,.75):
  gs=np.geomspace(1e-5,.003,50);axes[1].plot(1-water-gs,gs,':',lw=.7,color='.75')
 axes[1].set(xlabel='Iron core mass fraction',ylabel='H/He mass fraction',yscale='log',xlim=(0,1.02),ylim=(8e-6,.004))
 axes[1].legend(fontsize=7,loc='upper center',bbox_to_anchor=(.5,-.16),ncol=2)
 fig.colorbar(scatter,ax=axes[1],label='Model radius − 2.39 (Earth radii)',shrink=.8)
 fig.suptitle('TOI-732 c sparse pilot — TEST TP / fixed mass 8.04 Earth masses\nRadius-only comparison 2.28–2.49; adopted EOS prescriptions; no posterior band',fontsize=11)
 for ext in ('png','svg'):fig.savefig(figdir/('pilot-composition.'+ext),dpi=180)
 plt.close(fig)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('output');plot(Path(p.parse_args().output).resolve())
