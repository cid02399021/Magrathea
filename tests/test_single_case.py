import copy, hashlib, json, math, os, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'workflow'))
from single_case import run_case, check_result, MockSolver
ROOT=Path(__file__).resolve().parent
class SmokeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir='D:/Codex/tmp'); self.addCleanup(self.tmp.cleanup); self.base=Path(self.tmp.name)
  self.c=json.loads((ROOT/'fixtures/main-smoke.json').read_text(encoding='utf-8-sig'))
  (self.base/'main-smoke-tp.csv').write_bytes((ROOT/'fixtures/main-smoke-tp.csv').read_bytes())
 def run_fixture(self,c=None,solver=None,name='out'):
  p=self.base/'input.json'; p.write_text(json.dumps(self.c if c is None else c),encoding='utf-8')
  return run_case(p,self.base/name,solver=solver)
 def test_success_and_identity(self):
  r=self.run_fixture(); self.assertEqual(r['status'],'ENGINEERING_SMOKE_PASS'); self.assertIs(r['physical_acceptance'],False)
  for name in ['config.json','tp.csv','result.json','report.json']: self.assertTrue((self.base/'out'/name).is_file(),name)
  hashes=json.dumps(r['identities']); self.assertIn(hashlib.sha256((self.base/'input.json').read_bytes()).hexdigest(),hashes); self.assertIn(hashlib.sha256((self.base/'main-smoke-tp.csv').read_bytes()).hexdigest(),hashes)
  self.assertIn('source',hashes.lower()); self.assertTrue(r['checks'])
  self.assertEqual(json.loads((self.base/'out/result.json').read_text())['origin'],'MOCK_SOLVER')
 def test_invalid_configs_do_not_solve(self):
  class Bomb:
   def solve(self,c): raise AssertionError('MUST_NOT_CALL')
  changes=[{'fractions':{'iron':.2,'silicate':.2,'water':.2,'hhe':.2}}, {'units':{'mass':'kg','pressure':'bar','temperature':'K'}},{'tp_profile_file':'missing.csv'},{'mass_earth':True},{'mass_earth':float('nan')},{'origin':'OBSERVED'},{'outer_pressure_bar':1000},{'outer_temperature_K':301},{'fractions':{'iron':.3,'silicate':.5,'water':.2,'hhe':0}}]
  for i,change in enumerate(changes):
   with self.subTest(change=change):
    c=copy.deepcopy(self.c); c.update(change); r=self.run_fixture(c,Bomb(),f'bad{i}'); self.assertEqual(r['status'],'FAILED'); self.assertNotIn('MUST_NOT_CALL',r['reason']); self.assertTrue(r['reason'])
 def test_bad_tp(self):
  for i,data in enumerate(['P_bar,T_K\n1,300\n1,400\n','P_bar,T_K\n1,300,5\n10,400\n','P_bar,T_K\n1,NaN\n10,400\n','P_Pa,T_K\n1,300\n10,400\n','P_bar,T_K\n1,300\n']):
   (self.base/'main-smoke-tp.csv').write_text(data); r=self.run_fixture(name=f'tp{i}'); self.assertEqual(r['status'],'FAILED')
 def test_adapter_failure(self):
  class Broken:
   def solve(self,c): raise RuntimeError('fixture adapter intentional failure')
  r=self.run_fixture(solver=Broken()); self.assertEqual(r['status'],'FAILED'); self.assertIn('intentional failure',r['reason']); self.assertIs(r['physical_acceptance'],False)
 def test_bad_results(self):
  good={'origin':'MOCK_SOLVER','mass_earth':8.0,'radius_earth':2.0,'physical_acceptance':False}
  for i,change in enumerate([{'radius_earth':float('nan')},{'radius_earth':-1},{'physical_acceptance':True},{'origin':'REAL_SOLVER'},{'mass_earth':True},{'mass_earth':7.0}]):
   class Bad:
    def solve(self,c): return dict(good,**change)
   r=self.run_fixture(solver=Bad(),name=f'result{i}'); self.assertEqual(r['status'],'FAILED')
 def test_no_overwrite(self):
  self.run_fixture(); before={str(p.relative_to(self.base/'out')):p.read_bytes() for p in (self.base/'out').rglob('*') if p.is_file()}
  with self.assertRaises((FileExistsError,ValueError)): self.run_fixture()
  self.assertEqual(before,{str(p.relative_to(self.base/'out')):p.read_bytes() for p in (self.base/'out').rglob('*') if p.is_file()})
  (self.base/'empty').mkdir()
  with self.assertRaises((FileExistsError,ValueError)): self.run_fixture(name='empty')
 def test_replace_adapter_and_fixture(self):
  class Other:
   def solve(self,c): return {'origin':'MOCK_SOLVER','mass_earth':c['mass_earth'],'radius_earth':9.0,'physical_acceptance':False}
  self.c['mass_earth']=9.; r=self.run_fixture(solver=Other()); self.assertEqual(r['status'],'ENGINEERING_SMOKE_PASS'); self.assertEqual(json.loads((self.base/'out/result.json').read_text())['radius_earth'],9.)
 def test_legacy_physics_checker_rejects_mock(self):
  from check_tp_model import verify
  self.run_fixture()
  with self.assertRaises((ValueError,KeyError,TypeError)): verify(self.base/'out/result.json',self.base/'out/report.json')
 def test_input_mutation(self):
  base=self.base
  class Mutating:
   def solve(self,c):
    (base/'main-smoke-tp.csv').write_text('P_bar,T_K\n1,300\n10,999\n')
    return {'origin':'MOCK_SOLVER','mass_earth':c['mass_earth'],'radius_earth':2.,'physical_acceptance':False}
  r=self.run_fixture(solver=Mutating()); self.assertEqual(r['status'],'FAILED')
 def test_missing_and_malformed_config(self):
  for i,data in enumerate([None,'[]','{invalid']):
   p=self.base/f'bad-config{i}.json'
   if data is not None: p.write_text(data)
   r=run_case(p,self.base/f'bad-config-out{i}'); self.assertEqual(r['status'],'FAILED'); self.assertTrue(r['reason']); self.assertIs(r['physical_acceptance'],False)
   self.assertTrue((self.base/f'bad-config-out{i}'/'report.json').is_file())
 def test_strict_schema_and_anchor(self):
  for i,change in enumerate([{'schema_version':True},{'schema_version':1.0},{'outer_temperature_K':300.0000001},{'unknown_option':1}]):
   c=copy.deepcopy(self.c); c.update(change); r=self.run_fixture(c,name=f'strict{i}'); self.assertEqual(r['status'],'FAILED')
 def test_source_snapshot_identities(self):
  import single_case,check_tp_model
  self.run_fixture()
  for m in [single_case,check_tp_model]: self.assertEqual((self.base/'out/source'/Path(m.__file__).name).read_bytes(),Path(m.__file__).read_bytes())
 def test_failure_preserves_original_tp_bytes(self):
  original=(self.base/'main-smoke-tp.csv').read_bytes(); base=self.base
  class Mutating:
   def solve(self,c):
    (base/'main-smoke-tp.csv').write_text('P_bar,T_K\n1,300\n10,999\n')
    return {'origin':'MOCK_SOLVER','mass_earth':c['mass_earth'],'radius_earth':2.,'physical_acceptance':False}
  r=self.run_fixture(solver=Mutating()); self.assertEqual(r['status'],'FAILED'); self.assertEqual((self.base/'out/tp.csv').read_bytes(),original)
 def test_adapter_deletes_input(self):
  base=self.base
  class Deleting:
   def solve(self,c):
    (base/'main-smoke-tp.csv').unlink()
    return {'origin':'MOCK_SOLVER','mass_earth':c['mass_earth'],'radius_earth':2.,'physical_acceptance':False}
  r=self.run_fixture(solver=Deleting()); self.assertEqual(r['status'],'FAILED'); self.assertTrue((self.base/'out/report.json').is_file())
 def test_partial_checks_retained(self):
  (self.base/'main-smoke-tp.csv').write_text('P_bar,T_K\n1,300\n1,400\n')
  r=self.run_fixture(); self.assertEqual(r['status'],'FAILED'); self.assertIn('units valid',r['checks']); self.assertIn('fractions valid',r['checks'])
 def test_returned_rejected_result_saved(self):
  class WrongMass:
   def solve(self,c): return {'origin':'MOCK_SOLVER','mass_earth':7.,'radius_earth':2.,'physical_acceptance':False}
  r=self.run_fixture(solver=WrongMass()); self.assertEqual(r['status'],'FAILED'); self.assertEqual(json.loads((self.base/'out/result.json').read_text())['mass_earth'],7.)
 def test_output_failure_never_returns_pass(self):
  import single_case
  from unittest.mock import patch
  original=Path.write_text
  def fail_result(path,*args,**kwargs):
   if path.name=='result.json': raise OSError('INJECTED_OUTPUT_WRITE_FAILURE')
   return original(path,*args,**kwargs)
  with patch.object(Path,'write_text',fail_result):
   try: r=self.run_fixture()
   except OSError: return
   self.assertEqual(r['status'],'FAILED'); self.assertIs(r['physical_acceptance'],False)
   self.assertEqual(json.loads((self.base/'out/report.json').read_text())['status'],'FAILED')
 def test_snapshot_and_report_write_failures(self):
  from unittest.mock import patch
  original_bytes=Path.write_bytes; original_text=Path.write_text
  for i,target in enumerate(['config.json','tp.csv','report.json']):
   hit=[False]
   def fail_bytes(path,*args,**kwargs):
    if path.name==target and not hit[0]: hit[0]=True; raise OSError('INJECTED_SNAPSHOT_WRITE_FAILURE')
    return original_bytes(path,*args,**kwargs)
   def fail_text(path,*args,**kwargs):
    if path.name==target and not hit[0]: hit[0]=True; raise OSError('INJECTED_REPORT_WRITE_FAILURE')
    return original_text(path,*args,**kwargs)
   with self.subTest(target=target),patch.object(Path,'write_bytes',fail_bytes),patch.object(Path,'write_text',fail_text):
    try: r=self.run_fixture(name=f'writefail{i}')
    except OSError: continue
    self.assertTrue(hit[0]); self.assertEqual(r['status'],'FAILED'); self.assertIs(r['physical_acceptance'],False)
    saved=json.loads((self.base/f'writefail{i}'/'report.json').read_text()); self.assertEqual(saved,r)
 def test_primary_and_fallback_report_failures_propagate(self):
  from unittest.mock import patch
  original=Path.write_text; hits=[0]
  def fail_twice(path,*args,**kwargs):
   if path.name=='report.json':
    hits[0]+=1
    if hits[0]<=2: raise OSError('INJECTED_PRIMARY_AND_FALLBACK_FAILURE')
   return original(path,*args,**kwargs)
  with patch.object(Path,'write_text',fail_twice):
   with self.assertRaises(OSError): self.run_fixture()
  self.assertEqual(hits[0],2)
 def test_returned_null_is_preserved(self):
  class Null:
   def solve(self,c): return None
  r=self.run_fixture(solver=Null()); self.assertEqual(r['status'],'FAILED'); self.assertIsNone(json.loads((self.base/'out/result.json').read_text()))
 def test_partial_result_checks_retained(self):
  class NegativeRadius:
   def solve(self,c): return {'origin':'MOCK_SOLVER','mass_earth':8.,'radius_earth':-1.,'physical_acceptance':False}
  r=self.run_fixture(solver=NegativeRadius()); self.assertEqual(r['status'],'FAILED'); self.assertIn('origin MOCK_SOLVER',r['checks']); self.assertIn('physical_acceptance false',r['checks']); self.assertNotIn('adapter invocation failed',r['checks']); self.assertIn('result',r['reason'].lower())
 def test_invalid_config_preserves_readable_tp(self):
  original=(self.base/'main-smoke-tp.csv').read_bytes()
  for i,change in enumerate([{'mass_earth':True},{'units':{'mass':'kg','pressure':'bar','temperature':'K'}},{'fractions':{'iron':.2,'silicate':.2,'water':.2,'hhe':.2}}]):
   c=copy.deepcopy(self.c); c.update(change); r=self.run_fixture(c,name=f'provenance{i}'); self.assertEqual(r['status'],'FAILED')
   self.assertEqual((self.base/f'provenance{i}'/'tp.csv').read_bytes(),original); self.assertEqual(r['identities']['tp']['sha256'],hashlib.sha256(original).hexdigest())
 def test_missing_config_preserves_source_identities(self):
  r=run_case(self.base/'absent.json',self.base/'missing-source-identities'); self.assertEqual(r['status'],'FAILED')
  for name in ['single_case.py','check_tp_model.py']:
   saved=self.base/'missing-source-identities/source'/name
   self.assertTrue(saved.is_file()); self.assertEqual(r['identities']['source/'+name],hashlib.sha256(saved.read_bytes()).hexdigest())
 def test_cli(self):
  self.run_fixture(name='prepared')
  p=subprocess.run([sys.executable,'-B',str(ROOT.parent/'workflow/single_case.py'),'--config',str(self.base/'input.json'),'--output',str(self.base/'cli')],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr); self.assertIn('ENGINEERING_SMOKE_PASS',p.stdout)
if __name__=='__main__': unittest.main()
