"""Verify archived bytes and mock-only acceptance; never launch a solver."""
import hashlib,json
from pathlib import Path

def verify():
 base=Path(__file__).resolve().parent
 manifest=json.loads((base/'manifest.json').read_text())
 for relative,digest in manifest['files'].items():
  path=(base/relative).resolve()
  if not path.is_relative_to(base.resolve()): raise ValueError('unsafe archive path')
  if hashlib.sha256(path.read_bytes()).hexdigest()!=digest: raise ValueError('hash mismatch: '+relative)
 report=json.loads((base/'success/report.json').read_text())
 result=json.loads((base/'success/result.json').read_text())
 config=json.loads((base/'success/config.json').read_text(encoding='utf-8-sig'))
 assert report['status']=='ENGINEERING_SMOKE_PASS' and report['physical_acceptance'] is False
 assert config['origin']=='SYNTHETIC_FIXTURE' and result['origin']=='MOCK_SOLVER' and result['physical_acceptance'] is False
 for name,key in [('config.json','config'),('tp.csv','tp')]:
  assert hashlib.sha256((base/'success'/name).read_bytes()).hexdigest()==report['identities'][key]['sha256']
 for name in ['single_case.py','check_tp_model.py']:
  assert hashlib.sha256((base/'success/source'/name).read_bytes()).hexdigest()==report['identities']['source/'+name]
 for name in ['rejected-input','failed-adapter']:
  failed=json.loads((base/name/'report.json').read_text()); assert failed['status']=='FAILED' and failed['physical_acceptance'] is False and failed['reason']
  assert 'sha256' in failed['identities']['tp']
 review=json.loads((base/'evidence/whole-code-review.json').read_text()); assert review['approved'] is True
 summary=json.loads((base/'evidence/demo-summary.json').read_text()); assert summary['overwrite_bytes_unchanged'] is True and summary['overwrite_cli_exit']==1
 state=json.loads((base/'evidence/controller-state.json').read_text()); evidence=state['evidence']['single_case_mock_smoke:tests']; assert evidence['exit_codes']==[0] and evidence['before_hash']==evidence['after_hash']
 assert 'Ran 24 tests' in (base/'evidence/tests-24.log').read_text()
 return {'archive':'PASS','files_verified':len(manifest['files']),'engineering_smoke_only':True,'physical_acceptance':False,'solver_launches':0}
if __name__=='__main__': print(json.dumps(verify()))
