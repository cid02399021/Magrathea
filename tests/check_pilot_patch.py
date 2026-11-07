"""Fixed coordinator test driver. Applies DeepSeek proposals to a new D: copy only."""
import argparse, hashlib, json, os, pathlib, shutil, subprocess, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
ALLOW={'src/'+x for x in ('EOS.h','EOS.cpp','phase.h','phase.cpp','main.cpp','tp_settings.cpp','tp_diagnostics.h','tp_diagnostics.cpp','hydro.h','hydro.cpp')}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def linux(p):return '/mnt/'+str(p)[0].lower()+str(p)[2:].replace('\\','/')
def main():
 p=argparse.ArgumentParser();p.add_argument('--proposal');a=p.parse_args()
 dest=ROOT.parent/'validated-pilot-source' if a.proposal else pathlib.Path(tempfile.mkdtemp(prefix='pilot-red-',dir='D:/Codex/tmp'))
 if a.proposal:dest.mkdir()
 for pattern in ('src/*.h','src/*.cpp','tabulated/*','Makefile','tests/test_pilot_eos.cpp','tests/test_interface_temperature.cpp'):
  for f in ROOT.glob(pattern):
   if f.is_file():
    out=dest/f.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,out)
 changed=set()
 if a.proposal:
  patch=(ROOT/a.proposal).read_text(encoding='utf-8')
  if patch.startswith('diff --git ') or patch.startswith('--- '):
   import re
   targets=re.findall(r'^\+\+\+ b/(.+)$',patch,re.M)
   assert targets and set(targets)<=ALLOW
   assert not re.search(r'^(?:---|\+\+\+) (?![ab]/src/)',patch,re.M)
   # Exact unique textual hunks; never fuzzy matching or trusting line numbers.
   current=None;old=[];new=[];in_hunk=False
   def apply_hunk():
    if not old and not new:return
    f=dest/current;raw=f.read_bytes();nl=b'\r\n' if b'\r\n' in raw else b'\n'
    text=raw.decode().replace('\r\n','\n');a=''.join(old);b=''.join(new)
    assert a and text.count(a)==1,(current,'unique exact hunk',text.count(a))
    f.write_bytes(text.replace(a,b,1).replace('\n',nl.decode()).encode())
   for line in patch.splitlines(keepends=True):
    if line.startswith('diff --git '):
     apply_hunk();old=[];new=[];in_hunk=False;current=None
    elif line.startswith('--- a/'):
     apply_hunk();old=[];new=[];in_hunk=False;current=None
    elif line.startswith('+++ b/'):
     current=line[6:].strip();assert current in ALLOW;changed.add(current)
    elif line.startswith('@@ '):
     apply_hunk();old=[];new=[];in_hunk=True
    elif line in ('\n','\r\n'):
     apply_hunk();old=[];new=[];in_hunk=False
    elif in_hunk:
     assert line[0] in ' +-',(current,repr(line))
     if line[0] in ' -':old.append(line[1:])
     if line[0] in ' +':new.append(line[1:])
   apply_hunk()
   assert all((dest/rel).read_bytes()!=(ROOT/rel).read_bytes() for rel in targets),'patch skipped files'

  else:
   data=json.loads(patch)
   assert set(data)=={'operations'}
   for op in data['operations']:
    assert set(op)=={'file','old','new'} and op['file'] in ALLOW and op['old']!=op['new']
    f=dest/op['file'];raw=f.read_bytes();nl='\r\n' if b'\r\n' in raw else '\n'
    text=raw.decode('utf-8').replace('\r\n','\n');old=op['old'].replace('\r\n','\n');new=op['new'].replace('\r\n','\n')
    assert old and text.count(old)==1,(op['file'],'anchor count',text.count(old))
    f.write_bytes(text.replace(old,new,1).replace('\n',nl).encode());changed.add(op['file'])
 d=linux(dest)
 sources=sorted(str(x.relative_to(dest)).replace('\\','/') for x in (dest/'src').glob('*.cpp') if x.name!='main.cpp')
 cmds=[['g++','-std=c++11','-O2','-Isrc','tests/test_pilot_eos.cpp',*sources,'-lgsl','-lgslcblas','-lm','-o','pilot-unit'],['./pilot-unit'],['g++','-std=c++11','-O2','-Isrc','tests/test_interface_temperature.cpp',*sources,'-lgsl','-lgslcblas','-lm','-o','interface-unit'],['./interface-unit'],['make','-B','-j2']]
 for i,argv in enumerate(cmds):
  import shlex
  shell='cd '+shlex.quote(d)+' && TMPDIR=/mnt/d/Codex/tmp '+shlex.join(argv)
  r=subprocess.run(['wsl','--','bash','-lc',shell],capture_output=True,timeout=240)
  (dest/('check-%d.log'%i)).write_bytes(r.stdout+r.stderr)
  if r.returncode:print((r.stdout+r.stderr).decode(errors='replace')[-6000:]);raise SystemExit(r.returncode)
  print(r.stdout.decode(errors='replace')[-1000:])
 manifest={str(x.relative_to(dest)).replace('\\','/'):sha(x) for pattern in ('src/*.h','src/*.cpp','tabulated/*','Makefile','planet') for x in dest.glob(pattern) if x.is_file()}
 (dest/'validated-source.json').write_text(json.dumps({'changed':sorted(changed),'sha256':manifest},indent=2),encoding='utf-8')
 print('applied_source_root='+str(dest))
if __name__=='__main__':main()
