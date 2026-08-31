from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_ORBIT_TRACKPAD_VISIBILITY_V9' in s:
    print('Orbit trackpad visibility v9 already applied'); raise SystemExit(0)

if 'LIVE_EDIT_ORBIT_TRACKPAD_V8' not in s:
    raise SystemExit('Orbit trackpad v8 must be patched first')
if 'LIVE_EDIT_STATE_V3' not in s:
    raise SystemExit('Live Edit state v3 must be patched first')

marker='// LIVE_EDIT_TOUCH_TRANSFORM_V3'
if marker not in s:
    raise SystemExit('Live Edit touch v3 marker missing')

js=r'''// LIVE_EDIT_ORBIT_TRACKPAD_VISIBILITY_V9
// State V3 replaces the original Live Edit enter/exit handler. Keep the dedicated
// orbit trackpad synchronized with the final V3 portal state as well.
const _enterLiveEditV3OrbitPad=enterLiveEditV3;
enterLiveEditV3=function(){
  _enterLiveEditV3OrbitPad();
  $('liveOrbitTrackpad')?.classList.add('on');
};

const _exitLiveEditV3OrbitPad=exitLiveEditV3;
exitLiveEditV3=function(){
  $('liveOrbitTrackpad')?.classList.remove('on');
  try{liveOrbitTouches?.clear()}catch(_){ }
  try{liveOrbitResetGesture()}catch(_){ }
  _exitLiveEditV3OrbitPad();
};

// Defensive sync for any older path that changes Live Edit state directly.
function syncLiveOrbitTrackpadV9(){
  $('liveOrbitTrackpad')?.classList.toggle('on',!!liveEditSelectMode);
}
$('liveEditSelectBtn')?.addEventListener('click',()=>setTimeout(syncLiveOrbitTrackpadV9,0));

'''
s=s.replace(marker,js+'\n'+marker,1)
p.write_text(s,encoding='utf-8')
print('Orbit trackpad visibility v9 applied: synchronized with Live Edit V3')
