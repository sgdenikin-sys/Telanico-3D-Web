"""Failure-safety tests use an isolated fake API; never contact private services."""
import datetime as dt,io,json,os,pathlib,subprocess,sys,tempfile,unittest,zipfile
SCRIPT=pathlib.Path(__file__).with_name('import_preview.py').resolve()
class ImportSafety(unittest.TestCase):
 def exercise(self,*,conclusion='success',bad_sha=False,extra=False,already=False,foreign=False):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp);(root/'site').mkdir();old='abc123' if already else 'previous-good'
   (root/'site/build.json').write_text(json.dumps({'commit':old}));(root/'site/keep.txt').write_text('previous-good')
   run={'id':123,'run_number':7,'name':'Godot Web playable','head_branch':'codex/telanico-overworld-v2','head_sha':'abc123','head_repository':{'full_name':'outside/fork' if foreign else 'sgdenikin-sys/Telanico-3D-Lab'},'status':'completed','conclusion':conclusion,'updated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'html_url':'https://github.com/example/actions/runs/123'}
   (root/'runs.json').write_text(json.dumps({'workflow_runs':[run]}));(root/'artifacts.json').write_text(json.dumps({'artifacts':[{'id':456,'name':'telanico-3d-web','expired':False}]}))
   with zipfile.ZipFile(root/'candidate.zip','w') as z:
    files={'index.html':b'const GODOT_THREADS_ENABLED = false; abc123','index.js':b'// test fixture','index.wasm':b'\0asm\x01\0\0\0','index.pck':b'GDPC','index.audio.worklet.js':b'// worklet','index.audio.position.worklet.js':b'// worklet','LICENSES.html':b'CC0','build.json':json.dumps({'commit':'wrong' if bad_sha else 'abc123','branch':run['head_branch'],'source_run_id':'123'}).encode()}
    if extra:files['private.blend']=b'not-public'
    for name,data in files.items():z.writestr(name,data)
   (root/'gh').write_text('#!/usr/bin/env python3\nimport sys,pathlib\np=sys.argv[-1]\nf="candidate.zip" if p.endswith("/zip") else "artifacts.json" if p.endswith("/artifacts") else "runs.json"\nsys.stdout.buffer.write(pathlib.Path(f).read_bytes())\n');(root/'gh').chmod(0o755)
   env=dict(os.environ,PATH=str(root)+os.pathsep+os.environ['PATH'],GITHUB_OUTPUT=str(root/'output'))
   result=subprocess.run([sys.executable,str(SCRIPT)],cwd=root,env=env,capture_output=True,text=True)
   should_fail=conclusion!='success' or bad_sha or extra or foreign
   if should_fail:
    self.assertNotEqual(result.returncode,0,result.stdout)
    self.assertEqual((root/'site/keep.txt').read_text(),'previous-good')
   else:
    self.assertEqual(result.returncode,0,result.stderr)
    self.assertIn('changed=false' if already else 'changed=true',(root/'output').read_text())
    if not already:self.assertFalse((root/'site/keep.txt').exists())
 def test_valid_candidate(self):self.exercise()
 def test_identical_commit_is_noop(self):self.exercise(already=True)
 def test_failed_newest_retains_previous(self):self.exercise(conclusion='failure')
 def test_wrong_commit_retains_previous(self):self.exercise(bad_sha=True)
 def test_private_file_retains_previous(self):self.exercise(extra=True)
 def test_same_named_fork_branch_is_rejected(self):self.exercise(foreign=True)
if __name__=='__main__':unittest.main()
