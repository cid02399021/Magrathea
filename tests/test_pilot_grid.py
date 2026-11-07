"""Immutable pure-function checks; never launches a planet."""
import sys,unittest,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'workflow'))
import pilot_grid as p
class PilotGridTests(unittest.TestCase):
 def test_compositions(self):
  g=p.make_grid([.1,.3,.5,.7,.9,1.],[1e-5,1e-4,1e-3,.003]);self.assertEqual(len(g),24)
  for x in g:
   f=x['fractions'];self.assertEqual(len(f),4);self.assertEqual(f[1],0);self.assertAlmostEqual(sum(f),1,14)
   self.assertAlmostEqual(f[0],(1-x['gas_fraction'])*x['u']);self.assertEqual(f[3],x['gas_fraction'])
  self.assertTrue(any(x['fractions'][2]==0 for x in g))
 def test_bad_grid(self):
  for u,g in [([0],[.001]),([1.1],[.001]),([.5],[0]),([.5],[1]),([float('nan')],[.001]),([.5],[float('inf')]),([.5,.5],[.001]),([.5],[.001,.001])]:
   with self.assertRaises(ValueError):p.make_grid(u,g)
 def row(self,u,g,r,status='PASS_CONDITIONAL_NUMERICAL'):
  return dict(u=u,gas_fraction=g,radius_earth=r,status=status)
 def test_log_interpolation(self):
  roots=p.crossings([self.row(.5,1e-5,2),self.row(.5,1e-3,3)],2.5)
  self.assertEqual(len(roots),1);self.assertAlmostEqual(roots[0]['gas_fraction'],1e-4,15)
  self.assertEqual(roots[0]['kind'],'INTERPOLATED_UNCONFIRMED')
 def test_holes(self):
  rows=[self.row(.5,1e-5,2),self.row(.5,1e-4,None,'FAILED'),self.row(.5,1e-3,3)]
  self.assertEqual(p.crossings(rows,2.5),[])
 def test_multiple(self):
  rows=[self.row(.5,1e-5,2),self.row(.5,1e-4,3),self.row(.5,1e-3,2),self.row(.5,.003,3)]
  self.assertEqual(len(p.crossings(rows,2.5)),3)
 def test_no_extrapolation(self):
  self.assertEqual(p.crossings([self.row(.5,1e-5,2),self.row(.5,1e-3,2.1)],2.5),[])
 def test_exact(self):
  roots=p.crossings([self.row(.5,1e-5,2),self.row(.5,1e-4,2.5),self.row(.5,1e-3,3)],2.5)
  self.assertEqual(len(roots),1);self.assertEqual(roots[0]['kind'],'DIRECT_SAMPLE')

 def test_mixed_u(self):
  rows=[self.row(.1,1e-5,2),self.row(.9,1e-3,3)]
  self.assertEqual(p.crossings(rows,2.5),[])
 def test_native_config(self):
  s=p.config_text([.3,0,.699,.001],8.04,'/mnt/d/profile.csv','/mnt/d/model.dat',tight=False)
  d=dict(line.strip().split('=',1) for line in s.splitlines() if line.strip() and not line.lstrip().startswith('#'))
  self.assertEqual(d['input_mode'],'0');self.assertEqual(float(d['mass_of_mantle']),0)
  self.assertAlmostEqual(float(d['mass_of_core']),.3*8.04)
  self.assertEqual(d['atm_phasedgm'],'"gas_hhe_prescribed"')
  self.assertEqual(d['tp_profile_file'],'"/mnt/d/profile.csv"')
  self.assertEqual(d['output_file'],'"/mnt/d/model.dat"')
  self.assertEqual(float(d['P_surface']),1e5)
  self.assertEqual(float(d['surface_temp']),350)
  self.assertNotEqual(s,p.config_text([.3,0,.699,.001],8.04,'/mnt/d/profile.csv','/mnt/d/model.dat',tight=True))
 def test_bad_path_config(self):
  with self.assertRaises(ValueError):p.config_text([.3,0,.699,.001],8.04,'/mnt/d/bad path.csv','/mnt/d/model.dat')

 def test_crossing_fractions(self):
  roots=p.crossings([self.row(.5,1e-5,2),self.row(.5,1e-3,3)],2.5)
  for root in roots:
   g=root['gas_fraction'];self.assertEqual(root['fractions'],[(1-g)*.5,0,(1-g)*.5,g])
 def test_exact_duplicate(self):
  row=self.row(.5,1e-4,2.5)
  roots=p.crossings([dict(row),dict(row)],2.5)
  self.assertEqual(len(roots),1);self.assertEqual(len(roots[0]['fractions']),4)

 def test_exact_ignores_supplied_fractions(self):
  for supplied in (None,[1,2,3,4]):
   row=dict(self.row(.5,1e-4,2.5),fractions=supplied)
   roots=p.crossings([dict(row),dict(row)],2.5)
   self.assertEqual(len(roots),1)
   self.assertEqual(roots[0]['fractions'],[(1-1e-4)*.5,0,(1-1e-4)*.5,1e-4])
if __name__=='__main__':unittest.main()
