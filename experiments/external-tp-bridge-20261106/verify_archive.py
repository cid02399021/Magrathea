"""Read-only archive and saved-model verification. Never launch any solver."""
import hashlib,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
sys.path.insert(0,str(BASE/'build'))
from check_tp_model import verify

def validate_saved_data():
 contract=json.loads((BASE/'runtime-contract.json').read_text()); ledger=json.loads((BASE/'runtime-ledger.json').read_text())
 assert ledger['closed'] is True and ledger['planet_attempts']==2 and ledger['status']=='ENGINEERING_FORWARD_PASS'
 assert ledger['physical_acceptance'] is False and contract['physical_acceptance'] is False
 assert (BASE/'build/planet.elf').read_bytes().startswith(b'\x7fELF')
 raw=[tuple(map(float,line.split())) for line in (BASE/'converted/source.pt').read_text().splitlines()[1:] if line.strip()]
 points=[tuple(map(float,line.split(','))) for line in (BASE/'converted/profile.csv').read_text().splitlines()[1:]]
 assert len(raw)==len(points)==400
 for (pa,t),(bar,t2) in zip(raw,points): assert pa/1e5==bar and t==t2
 source=json.loads((BASE/'converted/manifest.json').read_text()); assert source['status']=='READY_FOR_EXTERNAL_TP' and source['point_count']==400
 for file,key in [('source.pt','source'),('profile.csv','converted'),('source/tp_import.py','converter')]:
  assert hashlib.sha256((BASE/'converted'/file).read_bytes()).hexdigest()==source['identities'][key]['sha256']
 radii=[]; checks=[]
 for name in ['real-01-baseline','real-02-confirmation']:
  case=BASE/name; before=json.loads((case/'before-run.json').read_text()); assert before['runtime_contract_sha256']==hashlib.sha256((BASE/'runtime-contract.json').read_bytes()).hexdigest()
  acceptance=verify(case/'model.dat.tp.json',case/'portable-recheck-contract.json'); result=json.loads((case/'result.json').read_text())
  assert result['exit_code']==0 and result['status']=='ENGINEERING_FORWARD_PASS' and result['physical_acceptance'] is False
  assert acceptance['gas_rows']==12163
  radii.append(acceptance['radius_cm']/contract['earth_radius_cm']); checks.append({'case':name,'gas_rows':acceptance['gas_rows'],'density_relative_max':acceptance['max_density_relative']})
 relative=abs(radii[1]-radii[0])/radii[0]; assert relative<=contract['confirmation_radius_relative_max']; assert relative==ledger['radius_confirmation_relative_difference']
 mock=json.loads((BASE/'mock-integration/report.json').read_text()); assert mock['status']=='ENGINEERING_SMOKE_PASS' and mock['physical_acceptance'] is False
 return {'numerical_engineering':'PASS','physical_acceptance':False,'real_solver_launches_recorded':2,'solver_launches_by_this_verifier':0,'radius_earth':radii,'radius_confirmation_relative_difference':relative,'checks':checks}

def main():
 manifest=json.loads((BASE/'manifest.json').read_text())
 for rel,digest in manifest['files'].items():
  path=(BASE/rel).resolve(); assert path.is_relative_to(BASE.resolve()); assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,rel
 audit=json.loads((BASE/'evidence/real-solver-audit.json').read_text()); assert audit['approved'] is True
 result=validate_saved_data(); result['archive_files_verified']=len(manifest['files']); print(json.dumps(result))
if __name__=='__main__': main()
