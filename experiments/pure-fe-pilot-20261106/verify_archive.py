"""Read-only archived-byte verification. Never builds or runs a solver."""
import gzip,hashlib,json
from pathlib import Path
def verify(root):
 root=Path(root).resolve();index=json.loads((root/'archive-index.json').read_text())
 for entry in index['files']:
  path=(root/entry['stored_path']).resolve();path.relative_to(root)
  data=path.read_bytes()
  assert hashlib.sha256(data).hexdigest()==entry['stored_sha256'],entry['stored_path']
  raw=gzip.decompress(data) if entry['encoding']=='gzip' else data
  assert hashlib.sha256(raw).hexdigest()==entry['original_sha256'],entry['stored_path']
  assert len(raw)==entry['original_bytes'],entry['stored_path']
 print('ARCHIVE_BYTES_PASS',len(index['files']),'files; no solver launched')
 return len(index['files'])
if __name__=='__main__':verify(Path(__file__).resolve().parent)
