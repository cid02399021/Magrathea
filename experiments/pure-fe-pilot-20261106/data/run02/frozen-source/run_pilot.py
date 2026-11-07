"""Predeclared scientific verification controller; no solver/EOS implementation.
Codex orchestration; composition/CFG/interpolation are DeepSeek-authored.
All new runs are conditional example-TP tests, never production inference.
"""
import argparse,csv,hashlib,importlib.util,json,os,re,shlex,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
CAMPAIGN_ID='pure-fe-pilot-20261106'
def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def native_path(p):
 s=str(p.resolve()).replace('\\','/')
 if len(s)>2 and s[1]==':' and s[0].lower()=='d':return '/mnt/d'+s[2:]
 if s.startswith('/mnt/d/'):return s
 raise ValueError('All run files must be on D: / /mnt/d/')
def campaign_path(identifier):
 if not isinstance(identifier,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',identifier):raise ValueError('Invalid campaign ID')
 return (ROOT/'.runs'/('campaign-'+identifier+'.json')).resolve()
def identities(out):
 m=json.loads((out/'identity.json').read_text())
 for rel,digest in m['files'].items():
  if sha((out/'frozen-source'/rel).read_bytes())!=digest:raise ValueError('Frozen identity changed: '+rel)
 if sha(Path(__file__).read_bytes())!=m['controller_sha256']:raise ValueError('Controller changed after snapshot')
 if sha((out/'config-used.json').read_bytes())!=m['files']['inputs/config.json']:raise ValueError('Working configuration changed')
 config=json.loads((out/'frozen-source/inputs/config.json').read_text())
 if config['campaign_id']!=CAMPAIGN_ID:raise ValueError('Wrong predeclared campaign')
 if m['campaign_ledger']!=str(campaign_path(config['campaign_id'])):raise ValueError('Campaign ledger substitution')
 if m['campaign_id']!=config['campaign_id']:raise ValueError('Campaign ID substitution')
 return m
def execute(cwd,argv,seconds):
 shell='cd '+shlex.quote(native_path(cwd))+' && exec env TMPDIR=/mnt/d/Codex/tmp '+shlex.join(['timeout','--kill-after=5s',str(seconds)+'s',*argv])
 env=dict(os.environ,TEMP='D:/Codex/tmp',TMP='D:/Codex/tmp',PYTHONDONTWRITEBYTECODE='1')
 command=['wsl','--','bash','-lc',shell] if os.name=='nt' else ['bash','-lc',shell]
 return subprocess.run(command,capture_output=True,timeout=seconds+10,env=env)
def reserve(ledger,out,label,fractions,tight):
 state=json.loads(ledger.read_text()) if ledger.exists() else {'limit':36,'attempts':[]}
 if state['limit']!=36 or len(state['attempts'])>=36:raise ValueError('Campaign launch limit reached')
 entry={'output':str(out),'case':label,'fractions':fractions,'tight':tight,'status':'RESERVED'}
 state['attempts'].append(entry);write(ledger,state)
 return len(state['attempts'])-1
def finish(ledger,index,result):
 state=json.loads(ledger.read_text());state['attempts'][index].update(result);write(ledger,state)
def modules(out):
 frozen=out/'frozen-source'
 spec=importlib.util.spec_from_file_location('pilot_helpers',frozen/'workflow/pilot_grid.py')
 helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 sys.path.insert(0,str(frozen/'tests'))
 import check_pilot_model
 return helper,check_pilot_model
def snapshot(out,config_path):
 config_bytes=config_path.read_bytes();config=json.loads(config_bytes)
 if config['campaign_id']!=CAMPAIGN_ID:raise ValueError('Wrong predeclared campaign')
 ledger=campaign_path(config['campaign_id']);ledger.parent.mkdir(parents=True,exist_ok=True)
 if config['scenario']!='EXAMPLE_TP_CONDITIONAL_PILOT' or config['physical_acceptance'] is not False:raise ValueError('Conditional test configuration required')
 if config['mass_earth']!=8.04 or config['surface_pressure_cgs']!=1e5:raise ValueError('This frozen pilot uses M8.04 and P0=0.1bar')
 if config['max_launches']!=36 or config['timeout_seconds']!=180:raise ValueError('Frozen run budget must be36x180s')
 if config['u_values']!=[.1,.3,.5,.7,.9,1.] or config['gas_fractions']!=[1e-5,1e-4,1e-3,.003]:raise ValueError('Frozen sparse24-point catalogue required')
 if config['target_radius_earth']!=2.39 or config['radius_interval_earth']!=[2.28,2.49]:raise ValueError('Frozen radius-only comparison')
 frozen=out/'frozen-source';frozen.mkdir()
 captured={}
 for pattern in ('src/*.h','src/*.cpp','tabulated/*','Makefile'):
  for source in ROOT.glob(pattern):
   if source.is_file():
    if source.is_symlink():raise ValueError('Symlink source')
    captured[source.relative_to(ROOT).as_posix()]=source.read_bytes()
 for rel in ('workflow/pilot_grid.py','tests/check_pilot_model.py','tests/check_tp_model.py'):
  captured[rel]=(ROOT/rel).read_bytes()
 captured['inputs/profile.csv']=(ROOT/config['profile_file']).read_bytes()
 captured['inputs/config.json']=config_bytes
 captured['run_pilot.py']=Path(__file__).read_bytes()
 for rel,data in captured.items():
  target=frozen/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 manifest={'campaign_id':config['campaign_id'],'campaign_ledger':str(ledger),'base':'26b7b72','physical_acceptance':False,'controller_sha256':sha(captured['run_pilot.py']),'files':{k:sha(v) for k,v in captured.items()}}
 write(out/'identity.json',manifest);(out/'config-used.json').write_bytes(config_bytes)
 result=execute(frozen,['make','-B','-j2'],240)
 (out/'build.stdout.log').write_bytes(result.stdout);(out/'build.stderr.log').write_bytes(result.stderr)
 if result.returncode:raise ValueError('Fresh native build failed')
 manifest['files']['planet']=sha((frozen/'planet').read_bytes());write(out/'identity.json',manifest)
 identities(out)
 return config
def run_case(out,label,fractions,tight,ledger,helper,checker):
 identities(out);case=out/label;case.mkdir()
 config=json.loads((out/'frozen-source/inputs/config.json').read_text())
 if config['campaign_id']!=CAMPAIGN_ID:raise ValueError('Wrong predeclared campaign')
 frozen=out/'frozen-source'
 write(case/'case.json',{'mass_earth':8.04,'fractions':fractions,'surface_pressure_cgs':1e5})
 text=helper.config_text(fractions,8.04,native_path(frozen/'inputs/profile.csv'),native_path(case/'model.dat'),tight=tight)
 (case/'run.cfg').write_text(text,encoding='utf-8')
 index=reserve(ledger,out,label,fractions,tight)
 verdict={'status':'FAILED','radius_earth':None}
 try:
  result=execute(frozen,['./planet',native_path(case/'run.cfg')],180)
  (case/'stdout.log').write_bytes(result.stdout);(case/'stderr.log').write_bytes(result.stderr)
  if result.returncode:raise ValueError('Native exit '+str(result.returncode))
  if not(case/'model.dat').is_file():raise ValueError('Missing native model output')
  verdict=checker.verify(case/'model.dat.tp.json',case/'case.json',frozen/'inputs/profile.csv',frozen/'tabulated/ChabrierHHe0275.txt')
 except subprocess.TimeoutExpired as error:
  (case/'stdout.log').write_bytes(error.stdout or b'');(case/'stderr.log').write_bytes(error.stderr or b'')
  verdict.update(reason='Native/WSL timeout')
 except Exception as error:
  verdict.update(reason=str(error))
 finally:
  write(case/'acceptance.json',verdict)
  artifacts={name:sha((case/name).read_bytes()) for name in ['case.json','run.cfg','stdout.log','stderr.log','model.dat','model.dat.tp.json','acceptance.json'] if (case/name).is_file()}
  write(case/'artifacts.json',artifacts)
  finish(ledger,index,{'status':verdict['status'],'reason':verdict.get('reason'),'artifact_sha256':artifacts})
 identities(out)
 print(label,verdict['status'],verdict.get('radius_earth'),verdict.get('reason',''),flush=True)
 return verdict
def check_case(out,label,checker):
 case=out/label;frozen=out/'frozen-source'
 for name,digest in json.loads((case/'artifacts.json').read_text()).items():
  if sha((case/name).read_bytes())!=digest:raise ValueError('Case artifact changed: '+label+'/'+name)
 fresh=checker.verify(case/'model.dat.tp.json',case/'case.json',frozen/'inputs/profile.csv',frozen/'tabulated/ChabrierHHe0275.txt')
 saved=json.loads((case/'acceptance.json').read_text())
 if fresh!=saved:raise ValueError('Acceptance changed: '+label)
 return fresh
def single(out,ledger,helper,checker):
 compositions=[[.30,0,.699,.001],[.10,0,.8999,.0001],[.9999,0,0,.0001],[.50,0,.49999,.00001]]
 results=[]
 for i,f in enumerate(compositions+[compositions[0]]):
  result=run_case(out,'single-%02d'%(i+1),f,i==4,ledger,helper,checker);results.append(result)
  if result['status']!='PASS_CONDITIONAL_NUMERICAL':
   write(out/'single-gate.json',{'status':'FAILED','stop_reason':'single_case_gate_failed','results':results});return False
 difference=abs(results[0]['radius_earth']-results[4]['radius_earth'])/results[0]['radius_earth']
 passed=difference<=1e-5
 write(out/'single-gate.json',{'status':'PASS' if passed else 'FAILED','relative_radius_difference':difference,'results':results,'stop_reason':'READY_FOR_GRID' if passed else 'tight_confirmation_failed'})
 return passed
def grid(out,ledger,helper,checker):
 gate=json.loads((out/'single-gate.json').read_text())
 if gate['status']!='PASS':raise ValueError('Single-case gate has not passed')
 if (out/'summary.json').exists():raise ValueError('Grid summary exists; refuse replay')
 for i in range(1,6):check_case(out,'single-%02d'%i,checker)
 config=json.loads((out/'frozen-source/inputs/config.json').read_text())
 if config['campaign_id']!=CAMPAIGN_ID:raise ValueError('Wrong predeclared campaign')
 samples=[]
 for i,point in enumerate(helper.make_grid(config['u_values'],config['gas_fractions'])):
  verdict=run_case(out,'grid-%02d'%(i+1),point['fractions'],False,ledger,helper,checker)
  row=dict(point,case='grid-%02d'%(i+1),status=verdict['status'],radius_earth=verdict.get('radius_earth'),reason=verdict.get('reason'))
  radius=row['radius_earth'];row['radius_residual']=None if radius is None else radius-2.39
  row['inside_radius_interval']=None if radius is None else 2.28<=radius<=2.49
  samples.append(row)
  summary={'physical_acceptance':False,'scenario':'EXAMPLE_TP_CONDITIONAL_PILOT','mass_earth':8.04,'radius_interval_only':[2.28,2.49],'samples':samples,'stop_reason':'RUNNING_SPARSE_PILOT'}
  write(out/'summary.json',summary)
 good=[r for r in samples if r['status']=='PASS_CONDITIONAL_NUMERICAL']
 summary.update(stop_reason='STOP_AFTER_SPARSE_PILOT',best_direct_sample=min(good,key=lambda r:abs(r['radius_residual'])) if good else None,coarse_crossings={str(target):helper.crossings(samples,target) for target in [2.28,2.39,2.49]})
 write(out/'summary.json',summary)
 with (out/'points.csv').open('w',newline='') as stream:
  keys=['case','u','gas_fraction','fractions','radius_earth','radius_residual','inside_radius_interval','status','reason']
  writer=csv.DictWriter(stream,fieldnames=keys);writer.writeheader();writer.writerows(samples)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['single','grid','verify'],required=True)
 parser.add_argument('--output',required=True)
 parser.add_argument('--config');args=parser.parse_args()
 out=Path(args.output).resolve();native_path(out)
 if args.stage!='single' and args.config:raise ValueError('Configuration is frozen; --config is only valid for single stage')
 if args.stage=='single':out.mkdir(parents=True,exist_ok=False)
 elif not out.is_dir():raise ValueError('Existing single-case output required')
 try:
  if args.stage=='single':snapshot(out,Path(args.config or ROOT/'workflow/examples/toi732c-pilot.json').resolve())
  manifest=identities(out);ledger=Path(manifest['campaign_ledger']);native_path(ledger)
  helper,checker=modules(out)
  if args.stage=='single':
   if not single(out,ledger,helper,checker):return 1
  elif args.stage=='grid':grid(out,ledger,helper,checker)
  else:
   for case in sorted(out.glob('single-*'))+sorted(out.glob('grid-*')):
    verdict=json.loads((case/'acceptance.json').read_text())
    if verdict['status']=='PASS_CONDITIONAL_NUMERICAL':check_case(out,case.name,checker)
   print('READ_ONLY_VERIFICATION_PASS',flush=True)
  return 0
 except Exception as error:
  # A separate failure record preserves any earlier completed checks/partial grid.
  if args.stage!='verify':write(out/('failure-'+args.stage+'.json'),{'status':'FAILED','reason':str(error)})
  raise
if __name__=='__main__':sys.exit(main())
