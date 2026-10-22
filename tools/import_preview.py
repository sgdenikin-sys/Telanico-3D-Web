"""Public importer: only an allowlisted, tested feature-branch browser artifact."""
import datetime as dt, json, os, pathlib, shutil, subprocess, zipfile
REPO='sgdenikin-sys/Telanico-3D-Lab';BRANCH='codex/telanico-overworld-v2-1'
V22_BRANCH='codex/telanico-v2-2-story-integration'
TRUSTED_BRANCHES={BRANCH,V22_BRANCH}
def api(path):return json.loads(subprocess.check_output(['gh','api',f'repos/{REPO}/{path}']))
# Dispatch input overrides the optional release pin. Scheduled/push imports use
# the same verified run when a release pin is present; otherwise track newest.
pin_path=pathlib.Path('tools/preview-source.json')
pin=json.loads(pin_path.read_text()) if pin_path.exists() else {}
run_id=os.environ.get('TELANICO_SOURCE_RUN_ID') or pin.get('run_id')
if run_id:
 assert str(run_id).isdigit(),'Invalid private Actions run ID'
 r=api(f'actions/runs/{run_id}')
else:
 runs=api('actions/runs?branch='+V22_BRANCH+'&per_page=30')['workflow_runs']
 runs=[r for r in runs if r['head_branch']==V22_BRANCH and r['name']=='Godot Web playable' and r.get('path')=='.github/workflows/web-smoke.yml' and r.get('head_repository',{}).get('full_name')==REPO and r['status']=='completed' and r['conclusion']=='success']
 if not runs:
  runs=api('actions/runs?branch='+BRANCH+'&per_page=30')['workflow_runs']
  runs=[r for r in runs if r['head_branch']==BRANCH and r['name']=='Godot Web playable' and r.get('path')=='.github/workflows/web-smoke.yml' and r.get('head_repository',{}).get('full_name')==REPO]
 assert runs,'No eligible Web artifact available'
 r=max(runs,key=lambda r:r['created_at'])
assert r['head_branch'] in TRUSTED_BRANCHES and r['name']=='Godot Web playable' and r.get('path')=='.github/workflows/web-smoke.yml' and r.get('head_repository',{}).get('full_name')==REPO,'Untrusted source workflow/repository/branch'
if run_id:
 assert str(r['id'])==str(run_id),'Actions run ID mismatch'
 if not os.environ.get('TELANICO_SOURCE_RUN_ID') and pin.get('commit'):assert r['head_sha']==pin['commit'],'Pinned commit mismatch'
assert r['status']=='completed' and r['conclusion']=='success','Newest candidate is not successful; retaining last working preview'
assert dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(r['updated_at'].replace('Z','+00:00'))<dt.timedelta(days=14),'Candidate artifact too old'
old=pathlib.Path('site/build.json')
if old.exists() and json.loads(old.read_text()).get('commit')==r['head_sha']:
 print('Already published',r['head_sha']);open(os.environ['GITHUB_OUTPUT'],'a').write('changed=false\n');raise SystemExit()
arts=api(f"actions/runs/{r['id']}/artifacts")['artifacts'];a=next(a for a in arts if a['name']=='telanico-3d-web' and not a['expired'])
raw=subprocess.check_output(['gh','api',f"repos/{REPO}/actions/artifacts/{a['id']}/zip"]);pathlib.Path('preview.zip').write_bytes(raw)
media={'media/'+name for name in ['music.mp3','cooper_chponk.wav','door_open_office.wav','tube_water_flush.wav','bird_takeoff_soft_purr.wav','door_close_soft.wav','select_woosh.wav','menu_flip.wav','door_open_playful.wav','swallow_takeoff.wav']}
allowed=media | {'audio_bridge.js','media/'} | {'index.html' ,'index.js','index.wasm','index.pck','index.audio.worklet.js','index.audio.position.worklet.js','index.icon.png','index.apple-touch-icon.png','index.png','build.json','LICENSES.html'}
with zipfile.ZipFile('preview.zip') as z:
 assert set(z.namelist())<=allowed,('Unexpected public file',z.namelist())
 z.extractall('incoming')
p=pathlib.Path('incoming');meta=json.loads((p/'build.json').read_text())
assert meta['branch']==r['head_branch'] and meta['commit']==r['head_sha'] and str(meta['source_run_id'])==str(r['id'])
for f in ['index.html','index.js','index.wasm','index.pck','index.audio.worklet.js','index.audio.position.worklet.js','build.json','LICENSES.html']:assert (p/f).stat().st_size>0
assert (p/'index.wasm').read_bytes()[:8]==b'\0asm\x01\0\0\0'
assert (p/'index.pck').read_bytes()[:4]==b'GDPC'
assert 'const GODOT_THREADS_ENABLED = false;' in (p/'index.html').read_text()
assert r['head_sha'] in (p/'index.html').read_text()
if r['head_branch']==V22_BRANCH:
 assert meta.get('version')=='telanico-v2.2','Not the complete V2.2 story artifact'
 for filename in media | {'audio_bridge.js'}:assert (p/filename).is_file() and (p/filename).stat().st_size>0,('Missing V2.2 runtime audio',filename)
 assert 'audio_bridge.js' in (p/'index.html').read_text()
# Only now replace the previous good snapshot.
shutil.rmtree('site');shutil.move('incoming','site');pathlib.Path('site/.nojekyll').touch()
with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write(f"changed=true\ncommit={r['head_sha']}\nsource_run={r['id']}\n")
print('Verified candidate',r['head_sha'],r['html_url'])
