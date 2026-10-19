"""Public importer: only an allowlisted, tested feature-branch browser artifact."""
import datetime as dt, json, os, pathlib, shutil, subprocess, zipfile
REPO='sgdenikin-sys/Telanico-3D-Lab';BRANCH='codex/telanico-overworld-v2'
def api(path):return json.loads(subprocess.check_output(['gh','api',f'repos/{REPO}/{path}']))
runs=api('actions/runs?branch='+BRANCH+'&per_page=30')['workflow_runs']
runs=[r for r in runs if r['head_branch']==BRANCH and r['name']=='Godot Web playable' and r.get('path')=='.github/workflows/web-smoke.yml' and r.get('head_repository',{}).get('full_name')==REPO]
assert runs,'No allowlisted V2 build available'
r=max(runs,key=lambda r:r['created_at'])
assert r['status']=='completed' and r['conclusion']=='success','Newest candidate is not successful; retaining last working preview'
assert dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(r['updated_at'].replace('Z','+00:00'))<dt.timedelta(days=14),'Candidate artifact too old'
old=pathlib.Path('site/build.json')
if old.exists() and json.loads(old.read_text()).get('commit')==r['head_sha']:
 print('Already published',r['head_sha']);open(os.environ['GITHUB_OUTPUT'],'a').write('changed=false\n');raise SystemExit()
arts=api(f"actions/runs/{r['id']}/artifacts")['artifacts'];a=next(a for a in arts if a['name']=='telanico-3d-web' and not a['expired'])
raw=subprocess.check_output(['gh','api',f"repos/{REPO}/actions/artifacts/{a['id']}/zip"]);pathlib.Path('preview.zip').write_bytes(raw)
allowed={'index.html','index.js','index.wasm','index.pck','index.audio.worklet.js','index.audio.position.worklet.js','index.icon.png','index.apple-touch-icon.png','index.png','build.json','LICENSES.html'}
with zipfile.ZipFile('preview.zip') as z:
 assert set(z.namelist())<=allowed,('Unexpected public file',z.namelist())
 z.extractall('incoming')
p=pathlib.Path('incoming');meta=json.loads((p/'build.json').read_text())
assert meta['branch']==BRANCH and meta['commit']==r['head_sha'] and str(meta['source_run_id'])==str(r['id'])
for f in ['index.html','index.js','index.wasm','index.pck','index.audio.worklet.js','index.audio.position.worklet.js','build.json','LICENSES.html']:assert (p/f).stat().st_size>0
assert (p/'index.wasm').read_bytes()[:8]==b'\0asm\x01\0\0\0'
assert (p/'index.pck').read_bytes()[:4]==b'GDPC'
assert 'const GODOT_THREADS_ENABLED = false;' in (p/'index.html').read_text()
assert r['head_sha'] in (p/'index.html').read_text()
# Only now replace the previous good snapshot.
shutil.rmtree('site');shutil.move('incoming','site');pathlib.Path('site/.nojekyll').touch()
with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write(f"changed=true\ncommit={r['head_sha']}\nsource_run={r['id']}\n")
print('Verified candidate',r['head_sha'],r['html_url'])
