import hashlib,json,math,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'workflow'))
from tp_import import convert_profile

def linux(p):
 s=str(Path(p).resolve()).replace('\\','/')
 return '/mnt/'+s[0].lower()+s[2:] if len(s)>2 and s[1]==':' else s

class ImportTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir='D:/Codex/tmp'); self.addCleanup(self.tmp.cleanup); self.base=Path(self.tmp.name)
 def convert(self,text):
  src=self.base/'input.pt'; src.write_bytes(text.encode()); return convert_profile(src,self.base/'out')
 def test_units_points_and_provenance(self):
  raw='# P (Pa)  T (K)  \n1 350\n100000 350.0001\n1000000000 1258.3\n'; report=self.convert(raw)
  self.assertEqual(report['status'],'READY_FOR_EXTERNAL_TP'); self.assertEqual(report['point_count'],3); self.assertIs(report['physical_acceptance'],False)
  self.assertEqual((self.base/'out/source.pt').read_bytes(),raw.encode())
  lines=(self.base/'out/profile.csv').read_text().splitlines(); self.assertEqual(lines[0],'P_bar,T_K'); points=[tuple(map(float,l.split(','))) for l in lines[1:]]
  for actual,expected in zip(points,[(1e-5,350),(1,350.0001),(1e4,1258.3)]): self.assertEqual(actual,expected)
  for name,key in [('source.pt','source'),('profile.csv','converted')]: self.assertEqual(report['identities'][key]['sha256'],hashlib.sha256((self.base/'out'/name).read_bytes()).hexdigest())
  self.assertEqual(report['identities']['converter']['sha256'],hashlib.sha256((self.base/'out/source/tp_import.py').read_bytes()).hexdigest())
  self.assertEqual(json.loads((self.base/'out/manifest.json').read_text()),report)
 def test_wrong_units_and_bad_values(self):
  bad=['# P (bar) T (K)\n1 300\n2 400\n','# P (Pa) T (K)\n1 300\n1 400\n','# P (Pa) T (K)\n1 300 4\n2 400\n','# P (Pa) T (K)\n1 nan\n2 400\n','# P (Pa) T (K)\n0 300\n2 400\n','# P (Pa) T (K)\n1 300\n','# P (Pa) T (K)\n1 300\n1e308 400\n']
  for i,text in enumerate(bad):
   src=self.base/f'bad{i}.pt'; src.write_text(text); out=self.base/f'badout{i}'; r=convert_profile(src,out); self.assertEqual(r['status'],'FAILED'); self.assertTrue(r['reason']); self.assertFalse((out/'profile.csv').exists()); self.assertEqual((out/'source.pt').read_bytes(),src.read_bytes())
 def test_missing_input_and_source_identity(self):
  r=convert_profile(self.base/'missing.pt',self.base/'out'); self.assertEqual(r['status'],'FAILED'); self.assertTrue(r['reason']); self.assertIn('converter',r['identities']); self.assertIs(r['physical_acceptance'],False)
 def test_no_overwrite(self):
  self.convert('# P (Pa) T (K)\n1 300\n2 400\n'); before={str(p.relative_to(self.base/'out')):p.read_bytes() for p in (self.base/'out').rglob('*') if p.is_file()}
  with self.assertRaises((FileExistsError,ValueError)): convert_profile(self.base/'input.pt',self.base/'out')
  self.assertEqual(before,{str(p.relative_to(self.base/'out')):p.read_bytes() for p in (self.base/'out').rglob('*') if p.is_file()})
 def test_failed_manifest_write_propagates(self):
  import builtins,io
  from unittest.mock import patch
  def block(original):
   def opened(file,mode='r',*args,**kwargs):
    if 'manifest.json' in str(file) and any(c in mode for c in 'wax'): raise OSError('INJECTED_MANIFEST_WRITE_FAILURE')
    return original(file,mode,*args,**kwargs)
   return opened
  with patch.object(builtins,'open',block(builtins.open)),patch.object(io,'open',block(io.open)):
   with self.assertRaises(OSError): convert_profile(self.base/'absent.pt',self.base/'out')
 def test_completed_header_check_retained(self):
  r=self.convert('# P (Pa) T (K)\n1 300\n1 400\n'); self.assertEqual(r['status'],'FAILED'); self.assertTrue(r['checks'])
 def test_failed_manifest_declares_expected_units(self):
  r=convert_profile(self.base/'absent.pt',self.base/'out'); self.assertEqual(r['input_unit'],'Pa'); self.assertEqual(r['output_unit'],'bar')
 def test_converter_snapshot_uses_captured_bytes(self):
  import tp_import
  from unittest.mock import patch
  original=Path.read_bytes; code=Path(tp_import.__file__).resolve(); captured=b'# simulated captured source before a concurrent file update\n'
  def read(path): return captured if path.resolve()==code else original(path)
  src=self.base/'input.pt'; src.write_bytes(b'# P (Pa) T (K)\n1 300\n2 400\n')
  with patch.object(Path,'read_bytes',read): report=convert_profile(src,self.base/'out')
  saved=(self.base/'out/source/tp_import.py').read_bytes(); self.assertEqual(saved,captured); self.assertEqual(report['identities']['converter']['sha256'],hashlib.sha256(saved).hexdigest())
 def test_cli(self):
  src=self.base/'input.pt'; src.write_text('# P (Pa) T (K)\n1 300\n2 400\n'); p=subprocess.run([sys.executable,'-B',str(ROOT/'workflow/tp_import.py'),'--source',str(src),'--output',str(self.base/'cli')],capture_output=True,text=True); self.assertEqual(p.returncode,0,p.stderr)

class NativeQueryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(dir='D:/Codex/tmp'); cls.base=Path(cls.tmp.name); cls.binary=cls.base/'tp-query'
  p=subprocess.run(['wsl','--exec','env','TMPDIR=/mnt/d/Codex/tmp','g++','-std=c++11','-O2','-I'+linux(ROOT/'src'),linux(ROOT/'workflow/tp_query.cpp'),linux(ROOT/'src/tp_profile.cpp'),'-o',linux(cls.binary)],capture_output=True,text=True,timeout=120)
  if p.returncode: raise RuntimeError(p.stderr)
  cls.profile=cls.base/'query.csv'; cls.profile.write_bytes(b'P_bar,T_K\n1,300\n100,500\n10000,400\n')
 @classmethod
 def tearDownClass(cls): cls.tmp.cleanup()
 def query(self,*args): return subprocess.run(['wsl','--exec',linux(self.binary),linux(self.profile),*map(str,args)],capture_output=True,text=True,timeout=20)
 def test_existing_native_evaluator(self):
  p=self.query(1,10,100,1000,10000); self.assertEqual(p.returncode,0,p.stderr); rows=json.loads(p.stdout); self.assertEqual(len(rows),5)
  for row,T in zip(rows,[300,400,500,450,400]): self.assertAlmostEqual(row['temperature_K'],T,places=11); self.assertTrue(math.isfinite(row['dT_dP_cgs']))
  self.assertAlmostEqual(rows[1]['dT_dP_cgs'],200/math.log(100)/1e7,places=16)
 def test_outside_and_bad_queries_rejected(self):
  for args in [(1,1e6),('nan',),('10garbage',),(0,),('1e308',)]:
   p=self.query(*args); self.assertNotEqual(p.returncode,0); self.assertEqual(p.stdout.strip(),''); self.assertTrue(p.stderr.strip())

if __name__=='__main__': unittest.main()
