"""Coordinator orchestration checks, no native solver calls."""
import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
ENTRY=ROOT/'experiments/pure-fe-pilot-20261106/run_pilot.py'
spec=importlib.util.spec_from_file_location('controller',ENTRY);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class ControllerChecks(unittest.TestCase):
 def test_campaign_limit(self):
  with tempfile.TemporaryDirectory(dir='D:/Codex/tmp') as d:
   out=Path(d);ledger=out/'ledger.json'
   for i in range(36):
    self.assertEqual(p.reserve(ledger,out,str(i),[.3,0,.699,.001],False),i)
    self.assertEqual(len(json.loads(ledger.read_text())['attempts']),i+1)
   before=ledger.read_bytes()
   with self.assertRaises(ValueError):p.reserve(ledger,out,'extra',[],False)
   self.assertEqual(before,ledger.read_bytes())
 def test_freeze_tamper(self):
  with tempfile.TemporaryDirectory(dir='D:/Codex/tmp') as d:
   out=Path(d);f=out/'frozen-source';f.mkdir();(f/'sample').write_bytes(b'abc')
   self.fixture(out)
   p.identities(out);(f/'sample').write_bytes(b'abcd')
   with self.assertRaises(ValueError):p.identities(out)
 def fixture(self,out):
  f=out/'frozen-source';(f/'inputs').mkdir(exist_ok=True)
  data=json.dumps({'campaign_id':p.CAMPAIGN_ID}).encode();(f/'inputs/config.json').write_bytes(data);(out/'config-used.json').write_bytes(data)
  m={'campaign_id':p.CAMPAIGN_ID,'campaign_ledger':str(p.campaign_path(p.CAMPAIGN_ID)),'controller_sha256':p.sha(ENTRY.read_bytes()),'files':{'sample':p.sha(b'abc'),'inputs/config.json':p.sha(data)}}
  p.write(out/'identity.json',m)
 def test_campaign_binding_across_outputs(self):
  with tempfile.TemporaryDirectory(dir='D:/Codex/tmp') as d:
   paths=[]
   for name in ('first','retry'):
    out=Path(d)/name;f=out/'frozen-source';f.mkdir(parents=True);(f/'sample').write_bytes(b'abc');self.fixture(out);paths.append(p.identities(out)['campaign_ledger'])
   self.assertEqual(paths[0],paths[1])
   m=json.loads((out/'identity.json').read_text());m['campaign_ledger']=str(Path(d)/'fresh-ledger.json');p.write(out/'identity.json',m)
   with self.assertRaisesRegex(ValueError,'ledger substitution'):p.identities(out)
 def test_config_mutation(self):
  with tempfile.TemporaryDirectory(dir='D:/Codex/tmp') as d:
   out=Path(d);f=out/'frozen-source';f.mkdir();(f/'sample').write_bytes(b'abc');self.fixture(out)
   (out/'config-used.json').write_bytes(b'{}')
   with self.assertRaisesRegex(ValueError,'configuration changed'):p.identities(out)
 def test_cli_rejects_ledger_override(self):
  r=subprocess.run([sys.executable,'-B',str(ENTRY),'--stage','grid','--output','D:/Codex/tmp/no-launch','--campaign-ledger','D:/Codex/tmp/other.json'],capture_output=True)
  self.assertNotEqual(r.returncode,0);self.assertIn(b'unrecognized arguments',r.stderr)
 def test_run_case_reservation_and_artifacts(self):
  with tempfile.TemporaryDirectory(dir='D:/Codex/tmp') as d:
   out=Path(d);f=out/'frozen-source';f.mkdir();self.fixture(out);ledger=out/'ledger.json'
   helper=SimpleNamespace(config_text=lambda *a,**kw:'fixture cfg')
   checker=SimpleNamespace(verify=lambda *a:{'status':'PASS_CONDITIONAL_NUMERICAL','radius_earth':2.4})
   def fake_execute(cwd,argv,seconds):
    self.assertEqual(len(json.loads(ledger.read_text())['attempts']),1)
    self.assertEqual(seconds,180)
    (out/'case/model.dat').write_bytes(b'fixture');(out/'case/model.dat.tp.json').write_bytes(b'{}')
    return SimpleNamespace(returncode=0,stdout=b'ok',stderr=b'')
   with patch.object(p,'identities',return_value={}),patch.object(p,'execute',side_effect=fake_execute):
    result=p.run_case(out,'case',[.3,0,.699,.001],False,ledger,helper,checker)
   self.assertEqual(result['status'],'PASS_CONDITIONAL_NUMERICAL')
   state=json.loads(ledger.read_text());self.assertEqual(state['attempts'][0]['status'],result['status'])
   self.assertIn('model.dat',state['attempts'][0]['artifact_sha256'])
 def test_grid_execution_path_without_models(self):
  with tempfile.TemporaryDirectory(dir='D:/Codex/tmp') as d:
   out=Path(d);f=out/'frozen-source/inputs';f.mkdir(parents=True)
   p.write(f/'config.json',{'campaign_id':p.CAMPAIGN_ID,'u_values':[.5],'gas_fractions':[.001]})
   p.write(out/'single-gate.json',{'status':'PASS'})
   helper=SimpleNamespace(make_grid=lambda *a:[{'u':.5,'gas_fraction':.001,'fractions':[.4995,0,.4995,.001]}],crossings=lambda *a:[])
   with patch.object(p,'check_case',return_value={}) as gate,patch.object(p,'run_case',return_value={'status':'PASS_CONDITIONAL_NUMERICAL','radius_earth':2.4}):
    p.grid(out,out/'ledger.json',helper,None)
   self.assertEqual(gate.call_count,5)
   saved=json.loads((out/'summary.json').read_text());self.assertEqual(saved['stop_reason'],'STOP_AFTER_SPARSE_PILOT');self.assertEqual(len(saved['samples']),1)
 def test_single_gate_control_without_models(self):
  with tempfile.TemporaryDirectory(dir='D:/Codex/tmp') as d:
   out=Path(d)
   with patch.object(p,'run_case',return_value={'status':'PASS_CONDITIONAL_NUMERICAL','radius_earth':2.4}) as run:
    self.assertTrue(p.single(out,out/'ledger.json',None,None))
   self.assertEqual(run.call_count,5)
   self.assertEqual(run.call_args_list[0].args[2],run.call_args_list[4].args[2])
   self.assertFalse(run.call_args_list[0].args[3]);self.assertTrue(run.call_args_list[4].args[3])
 def test_readonly_identity_allows_new_verifier(self):
  with tempfile.TemporaryDirectory(dir='D:/Codex/tmp') as d:
   out=Path(d);f=out/'frozen-source';f.mkdir();(f/'sample').write_bytes(b'abc');self.fixture(out)
   replacement=out/'new-verifier.py';replacement.write_bytes(b'new readonly verifier')
   with patch.object(p,'__file__',str(replacement)):
    p.identities(out,require_execution_identity=False)
    with self.assertRaisesRegex(ValueError,'Controller changed'):p.identities(out)
 def test_verify_filters_gate_file_and_never_executes(self):
  with tempfile.TemporaryDirectory(dir='D:/Codex/tmp') as d:
   out=Path(d);p.write(out/'single-gate.json',{'status':'PASS'})
   for label,status in [('single-01','PASS_CONDITIONAL_NUMERICAL'),('grid-01','FAILED')]:
    case=out/label;case.mkdir();p.write(case/'acceptance.json',{'status':status})
   original={str(x.relative_to(out)):x.read_bytes() for x in out.rglob('*') if x.is_file()}
   argv=[str(ENTRY),'--stage','verify','--output',str(out)]
   with patch.object(sys,'argv',argv),patch.object(p,'identities',return_value={'campaign_ledger':str(out/'unused-ledger.json')}) as identities,patch.object(p,'modules',return_value=(None,None)),patch.object(p,'check_case',return_value={}) as checks,patch.object(p,'verify_case_artifacts') as failed,patch.object(p,'execute') as execution:
    self.assertEqual(p.main(),0);execution.assert_not_called()
   self.assertFalse(identities.call_args.kwargs['require_execution_identity'])
   self.assertEqual(checks.call_count,1);self.assertEqual(failed.call_count,1)
   self.assertEqual(original,{str(x.relative_to(out)):x.read_bytes() for x in out.rglob('*') if x.is_file()})
 def test_existing_output(self):
  with tempfile.TemporaryDirectory(dir='D:/Codex/tmp') as d:
   out=Path(d);marker=out/'marker';marker.write_bytes(b'keep')
   r=subprocess.run([sys.executable,'-B',str(ENTRY),'--stage','single','--output',str(out)],capture_output=True)
   self.assertNotEqual(r.returncode,0);self.assertEqual(marker.read_bytes(),b'keep')
   self.assertEqual(set(x.name for x in out.iterdir()),{'marker'})
 def test_native_path(self):
  self.assertTrue(p.native_path(Path('D:/Codex/tmp')).startswith('/mnt/d/'))
  with self.assertRaises(ValueError):p.native_path(Path('C:/Windows'))
if __name__=='__main__':unittest.main()
