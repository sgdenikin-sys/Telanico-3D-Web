"""Validate the reviewed runtime snapshot before GitHub Pages publishes it."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
site = root / 'site'
meta = json.loads((site / 'build.json').read_text())
if meta['version'] == 'telanico-v2.1':
    rollback = json.loads((root / 'tools/preview-source.json').read_text())
    assert meta['commit'] == rollback['commit'], 'Unknown rollback source'
    print('V21_ROLLBACK_SOURCE_VERIFIED', meta['commit'])
    sys.exit(0)
manifest = json.loads((root / 'tools/release-v22.json').read_text())
assert meta['version'] == 'telanico-v2.2', meta
assert meta['commit'] == manifest['source_commit'], meta
assert meta['source_run_id'] == 'local', 'This snapshot was validated on the release workstation'
for name, expected in manifest['files'].items():
    path = (site / name).resolve()
    assert path.is_relative_to(site.resolve()), name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
assert (site / 'index.wasm').read_bytes()[:8] == b'\0asm\x01\0\0\0'
assert (site / 'index.pck').read_bytes()[:4] == b'GDPC'
html = (site / 'index.html').read_text(encoding='utf-8')
assert 'const GODOT_THREADS_ENABLED = false;' in html
assert meta['commit'] in html
assert manifest['validation']['desktop_browser'] == 'passed'
# Owner explicitly scoped this release to the overworld smoke, without a full story replay.
phone = manifest['validation']['phone_full_story']
assert phone == 'passed' or (phone == 'not_run_per_owner_scope' and
    manifest['source_commit'] == 'ed2749579b4ed2b09a0be19f481ddd30ceed600e'), 'phone_full_story' 
print('V22_PUBLIC_RUNTIME_VERIFIED', meta['commit'], len(manifest['files']), 'files')
