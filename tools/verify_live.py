"""Verify the delivered release and actual desktop/touch opening after Pages deployment."""
import hashlib
import json
import sys
import shutil
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

url = sys.argv[1].rstrip('/') + '/'
manifest = json.loads(Path('tools/release-v22.json').read_text())
commit = manifest['source_commit']
out = Path('live-evidence')
out.mkdir(exist_ok=True)
for attempt in range(24):
    try:
        meta = json.load(urllib.request.urlopen(url+'build.json?verify='+commit, timeout=30))
        assert meta['commit'] == commit, meta
        break
    except Exception:
        if attempt == 23:
            raise
        time.sleep(5)
# Check every deployed runtime byte, including the actual PCK and GIF.
for name, expected in manifest['files'].items():
    with urllib.request.urlopen(url+name+'?verify='+commit, timeout=120) as response:
        assert hashlib.sha256(response.read()).hexdigest() == expected, name
print('LIVE_RUNTIME_HASHES_PASS', commit, flush=True)
results = []
with sync_playwright() as p:
    browser_bin = shutil.which('google-chrome') or shutil.which('chromium')
    assert browser_bin, 'Expected preinstalled Chrome on ubuntu-24.04 runner'
    print('LIVE_BROWSER', browser_bin, flush=True)
    browser = p.chromium.launch(executable_path=browser_bin,args=['--no-sandbox','--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader'])
    for width, height, touch in [(1280,720,False),(844,306,True)]:
        context = browser.new_context(viewport={'width':width,'height':height},has_touch=touch,device_scale_factor=3 if touch else 1)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('response', lambda r: errors.append(f'HTTP {r.status}: {r.url}') if r.status>=400 else None)
        page.on('console', lambda m: errors.append(m.text) if any(x in m.text for x in ['SCRIPT ERROR','Parse Error','ERROR:']) else None)
        def wait(expr):
            page.wait_for_function(expr,timeout=240000,polling=250)
        def click(key):
            wait('(window.__TELANICO_STORY?.controls||[]).some(c=>!c.disabled&&(c.text==='+json.dumps(key)+'||c.art==='+json.dumps(key)+'))')
            # Allow the real Godot layout to settle before trusted input.
            page.wait_for_timeout(1500)
            xy=page.evaluate('''key=>{const s=window.__TELANICO_STORY;const c=s.controls.find(c=>!c.disabled&&(c.text===key||c.art===key));const r=document.querySelector('#canvas').getBoundingClientRect();return [r.x+(c.rect[0]+c.rect[2]/2)*r.width/s.viewport[0],r.y+(c.rect[1]+c.rect[3]/2)*r.height/s.viewport[1]]}''',key)
            if touch:
                page.touchscreen.tap(*xy)
            else:
                page.mouse.click(*xy)
        try:
            page.goto(url+'?test=1&story_test=1&release='+commit,wait_until='domcontentloaded',timeout=120000)
            wait('window.__TELANICO_STORY?.screen==="intro"')
            if touch:
                page.evaluate("document.documentElement.style.setProperty('--safe-left','47px');document.documentElement.style.setProperty('--safe-right','47px');document.documentElement.style.setProperty('--safe-bottom','21px')")
            click('CHOOSE YOUR ROLE')
            wait('window.__TELANICO_STORY.screen==="characters"')
            click('SELECT COOPER')
            wait('window.__TELANICO_STORY.modal==="invoice"')
            state=page.evaluate('window.__TELANICO_STORY')
            assert state['walk_speed']==9.375 and state['courier_scale']==3
            assert 'Diorama' not in state['hud']
            assert state['clock_art'].endswith('clock_analog_blue.png')
            assert state['world_visible'] and state['courier_visible']
            assert state['modal_rect'][2]<state['viewport'][0]*.9
            click('button_close_invoice.png')
            wait('window.__TELANICO_STORY.modal==="assistant"')
            state=page.evaluate('window.__TELANICO_STORY')
            assert state['assistant_framed']
            anchor=state['hud']['Assistant'];card=state['modal_rect']
            units=state['viewport'][0]/width
            assert abs(card[0]-anchor[0]*units)<1 and abs(card[1]-(anchor[1]+anchor[3]+8)*units)<1
            assert all(r[2]>=184 and r[3]>=44 for r in state['hud'].values())
            media=state['assistant_media'];rim=state['assistant_frame']
            assert all(abs(x-y)<1 for x,y in zip(media,rim))
            assert rim[2]/units>=70 and abs(rim[2]-rim[3])<1
            assert rim[1]+rim[3]<=card[1]+card[3]+1
            continuation=next(c for c in state['controls'] if c['text']=='CONTINUE')
            assert rim[0]+rim[2]<=continuation['rect'][0]
            plate=state['clock_plate'];assert plate[2]/units>=280
            for c in state['controls']:
                if c['art_rect']:assert all(abs(x-y)<1 for x,y in zip(c['rect'],c['art_rect']))
            print('LIVE_MOBILE_UI_PASS',width,height,'Retina' if touch else 'desktop','framed portrait, clock backing and aligned artwork',flush=True)
            page.screenshot(path=str(out/f'assistant-{width}.png'))
            click('CONTINUE')
            wait('!window.__TELANICO_STORY.locked')
            if touch:
                page.set_viewport_size({'width':844,'height':390})
                page.wait_for_timeout(2000)
            scenery=page.evaluate('window.__TELANICO_STATE')
            assert scenery['commit']==commit, ('Stale in-game PCK',scenery['commit'],commit)
            print('LIVE_RUNTIME_SOURCE_PASS',width,commit,flush=True)
            factor=0.8 if touch else 1.0
            assert scenery['bushes']==36 and not scenery['world_control_glow']
            assert scenery['controls_factor']==factor
            units=scenery['viewport'][0]/width
            assert abs(scenery['camera_control_size'][0]/units-104*factor)<1
            assert abs(scenery['camera_control_size'][1]/units-52*factor)<1
            print('LIVE_ATMOSPHERE_PASS',width,'bushes',scenery['bushes'],'controls',factor,flush=True)
            page.screenshot(path=str(out/f'world-{width}.png'))
            assert not errors, errors
            results.append({'width':width,'height':height,'touch':touch,'opening':'passed','errors':errors})
            print('LIVE_OPENING_PASS',width,flush=True)
        finally:
            (out/f'errors-{width}.json').write_text(json.dumps(errors,indent=2))
            page.screenshot(path=str(out/f'final-{width}.png'))
            context.close()
    browser.close()
(out/'result.json').write_text(json.dumps({'source_commit':commit,'url':url,'runtime_hashes':'passed','browser':results,'physical_iphone_safari':'not tested'},indent=2))
