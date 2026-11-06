"""Coordinator's bounded deterministic real-solver verification, not a grid driver."""
import copy,hashlib,json,os,re,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path('D:/Codex/downloads/subneptune-research-workflow')
ARCHIVE=ROOT/'experiments/external-tp-bridge-20261106'
BUILD=Path('D:/Codex/tmp/toi732c-profile-real-20261106-build01')
sys.path.insert(0,str(ROOT/'tests'))
from check_tp_model import verify

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,data):
 path=Path(path); temp=path.with_name(path.name+'.tmp'); temp.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n'); os.replace(temp,path)
def linux(path):
 s=str(Path(path).resolve()).replace('\\','/'); return '/mnt/'+s[0].lower()+s[2:]

def main():
 contract_path=ARCHIVE/'runtime-contract.json'; c=json.loads(contract_path.read_text()); ledger_path=ARCHIVE/'runtime-ledger.json'; ledger=json.loads(ledger_path.read_text())
 assert ledger['status']=='FROZEN_NOT_STARTED' and ledger['planet_attempts']==0,'Refuse replay/resume of closed or started experiment'
 assert c['max_planet_attempts']==2 and c['max_seconds_per_case']==180
 for key,entry in c['artifacts'].items(): assert sha(ARCHIVE/entry['path'])==entry['sha256'],key
 source_manifest=json.loads((ARCHIVE/'build/compiled-source-manifest.json').read_text())
 template=(ROOT/'run/mode0.cfg').read_text()
 def case(name,controls):
  assert ledger['planet_attempts']<c['max_planet_attempts']; directory=ARCHIVE/name; directory.mkdir(exist_ok=False)
  # Every source/table byte verified before executing the archived exact ELF.
  for item in source_manifest['files']: assert sha(directory/item['path'])==item['sha256'],item['path']
  for key in ['build','profile','raw_profile','source_manifest','checker']:
   entry=c['artifacts'][key]; assert sha(ARCHIVE/entry['path'])==entry['sha256'],key
  output=directory/'model.dat'; cfg=directory/'run.cfg'
  updates={'input_mode':0,'mass_of_core':c['mass_earth']*c['fractions']['iron'],'mass_of_mantle':c['mass_earth']*c['fractions']['silicate'],'mass_of_hydro':c['mass_earth']*c['fractions']['water'],'mass_of_atm':c['mass_earth']*c['fractions']['hhe'],'surface_temp':c['outer_temperature_K'],'temp_jump_1':0,'temp_jump_2':0,'temp_jump_3':0,'P_surface':c['outer_pressure_bar']*1e6,'core_phasedgm':'"'+c['eos_selectors']['core']+'"','mantle_phasedgm':'"'+c['eos_selectors']['mantle']+'"','hydro_phasedgm':'"'+c['eos_selectors']['water']+'"','atm_phasedgm':'"'+c['eos_selectors']['gas']+'"','output_file':'"'+linux(output)+'"','verbose':'false',**controls}
  text=template
  for key,value in updates.items():
   val=format(value,'.17g') if isinstance(value,float) else str(value)
   text,count=re.subn(r'(?m)^'+re.escape(key)+r'\s*=.*$',key+'='+val,text); assert count==1,key
  text+='\ntp_profile_file="'+linux(ARCHIVE/'converted/profile.csv')+'"\n'; cfg.write_text(text)
  dump(directory/'source-manifest.json',source_manifest)
  command=['wsl','--cd',linux(BUILD),'--exec','env','TMPDIR=/mnt/d/Codex/tmp','timeout','--signal=TERM','--kill-after=5','180s',linux(ARCHIVE/'build/planet.elf'),linux(cfg)]
  before={'ordinal':ledger['planet_attempts']+1,'case':name,'runtime_contract_sha256':sha(contract_path),'binary_sha256':sha(ARCHIVE/'build/planet.elf'),'config_sha256':sha(cfg),'profile_sha256':sha(ARCHIVE/'converted/profile.csv'),'current_git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'command_argv':command,'input_origin':'USER_EXAMPLE_TP_WITH_TEST_COMPOSITION','physical_acceptance':False}
  dump(directory/'before-run.json',before)
  result={'case':name,'ordinal':ledger['planet_attempts']+1,'status':'STARTED','physical_acceptance':False}; ledger['cases'].append(result); ledger['planet_attempts']+=1; ledger['status']='RUNNING'; dump(ledger_path,ledger)
  bp=ROOT/'workflow/project-budget.json'; budget=json.loads(bp.read_text()); budget['external_tp_bridge_real_attempts']=budget.get('external_tp_bridge_real_attempts',0)+1; budget['external_tp_bridge_real_attempt_limit']=2; budget['external_tp_bridge_real_attempt_scope']='New user-authorized engineering forward probe; old14-fit study closed and unchanged'; dump(bp,budget)
  print('REAL_SOLVER_START',name,'ordinal',result['ordinal'],flush=True); start=time.monotonic()
  with (directory/'stdout.log').open('wb') as stdout,(directory/'stderr.log').open('wb') as stderr:
   try: proc=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=210); code=proc.returncode
   except subprocess.TimeoutExpired: code=124
  result.update(exit_code=code,seconds=time.monotonic()-start,status='FAILED')
  try:
   assert code==0,'Real solver exited '+str(code)
   diag=Path(str(output)+'.tp.json'); assert output.is_file() and diag.is_file(),'Missing genuine model or diagnostic sidecar'
   acceptance={'total_mass_earth':c['mass_earth'],'earth_mass_g':c['earth_mass_g'],'requested_gas_fraction':c['fractions']['hhe'],'outer_pressure_bar':c['outer_pressure_bar'],'outer_temperature_K':c['outer_temperature_K'],'density_formula':c['density_formula'],'thresholds':copy.deepcopy(c['thresholds']),'physical_acceptance':False}
   acceptance['thresholds']['normalized_fit_residual_max']=min(c['thresholds']['normalized_fit_residual_max'],controls['fit_eps_rel'])
   acceptance['artifacts']={key:{'path':rel,'sha256':sha(directory/rel)} for key,rel in [('build','../build/planet.elf'),('config','run.cfg'),('profile','../converted/profile.csv'),('source_manifest','source-manifest.json'),('diagnostics','model.dat.tp.json')]}
   ap=directory/'acceptance-contract.json'; dump(ap,acceptance); check=verify(diag,ap); dump(directory/'acceptance.json',check)
   d=json.loads(diag.read_text()); result.update(status='ENGINEERING_FORWARD_PASS',radius_earth=d['total_radius_cm']/c['earth_radius_cm'],gas_base_pressure_bar=d['gas_base_pressure']/1e6,gas_base_temperature_K=d['gas_base_temperature'],actual_gas_pressure_bar=[d['gas_pressure_min']/1e6,d['gas_pressure_max']/1e6],gas_rows=check['gas_rows'],normalized_fit_residual=d['fit_residual'])
  except Exception as error:
   result['reason']=str(error)
   tail=(directory/'stdout.log').read_text(errors='replace')[-3000:]+'\n'+(directory/'stderr.log').read_text(errors='replace')[-3000:]; result['failure_log_tail']=tail
  # Preserve original profiles/code identity even on rejection.
  for key in ['build','profile','raw_profile','source_manifest','checker']:
   entry=c['artifacts'][key]; assert sha(ARCHIVE/entry['path'])==entry['sha256'],'Artifact mutated: '+key
  dump(directory/'result.json',result); dump(ledger_path,ledger); print('REAL_SOLVER_END',json.dumps(result),flush=True); return result
 baseline=case('real-01-baseline',c['baseline_controls'])
 if baseline['status']=='ENGINEERING_FORWARD_PASS':
  confirmation=case('real-02-confirmation',c['confirmation_controls'])
  if confirmation['status']=='ENGINEERING_FORWARD_PASS':
   delta=abs(confirmation['radius_earth']-baseline['radius_earth'])/baseline['radius_earth']; ledger['radius_confirmation_relative_difference']=delta
   ledger['status']='ENGINEERING_FORWARD_PASS' if delta<=c['confirmation_radius_relative_max'] else 'NUMERICAL_CONFIRMATION_INSUFFICIENT'
  else: ledger['status']='CONFIRMATION_FAILED'
 else: ledger['status']='BASELINE_FAILED_OR_REJECTED'
 ledger['physical_acceptance']=False; ledger['closed']=True; dump(ledger_path,ledger); print('FINAL',json.dumps(ledger),flush=True)
 return 0 if ledger['status']=='ENGINEERING_FORWARD_PASS' else 1
if __name__=='__main__': raise SystemExit(main())
