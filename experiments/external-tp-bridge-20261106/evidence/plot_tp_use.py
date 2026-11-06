"""Plot supplied TP and saved true-solver gas rows; never run any solver."""
import json,math,os
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']='D:/Codex/tmp/mpl-external-tp-bridge-20261106'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 points=[tuple(map(float,l.split(','))) for l in (BASE/'converted/profile.csv').read_text().splitlines()[1:]]
 d=json.loads((BASE/'real-02-confirmation/model.dat.tp.json').read_text()); rows=d['gas_rows']; stride=max(1,math.ceil(len(rows)/550)); shown=rows[::stride]
 if shown[-1] is not rows[-1]: shown.append(rows[-1])
 out=BASE/'figures'; out.mkdir(exist_ok=False)
 fig,ax=plt.subplots(figsize=(7.5,6.3)); ax.plot([t for p,t in points],[p for p,t in points],color='#2563eb',lw=2.3,label='Your TP table (all 400 points, Pa converted to bar)')
 ax.scatter([r['temperature_K'] for r in shown],[r['pressure_cgs']/1e6 for r in shown],s=10,color='#f97316',alpha=.65,label=f'Real C++ gas solution ({len(shown)} shown / {len(rows)} verified)')
 ax.scatter([d['gas_base_temperature']],[d['gas_base_pressure']/1e6],s=65,color='#b91c1c',zorder=5)
 ax.annotate('Gas base: 4575 bar, 1052 K',xy=(d['gas_base_temperature'],d['gas_base_pressure']/1e6),xytext=(600,40),arrowprops={'arrowstyle':'->','color':'#555'},fontsize=10)
 ax.set_yscale('log');ax.invert_yaxis();ax.set_xlabel('Temperature (K)');ax.set_ylabel('Pressure (bar)');ax.set_title('External TP used by the real solver: gas layer only');ax.grid(True,which='both',alpha=.18);ax.legend(loc='upper right',fontsize=8)
 fig.text(.5,.015,'Engineering test composition + ideal-mu2 gas EOS. No observational fit or physical-validity claim.',ha='center',fontsize=8,color='#555');fig.tight_layout(rect=(0,.04,1,1));fig.savefig(out/'external-tp-use.png',dpi=180);fig.savefig(out/'external-tp-use.svg');plt.close(fig)
 print('Saved TP-use figure; no solver launched')
if __name__=='__main__': main()
