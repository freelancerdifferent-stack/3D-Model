from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_STATE_V3' in s:
    print('Live Edit state v3 already applied'); raise SystemExit(0)

marker='// LIVE_EDIT_TRANSFORM_V2'
if marker not in s: raise SystemExit('Live Edit v2 marker missing')

js=r'''// LIVE_EDIT_STATE_V3
// Make Select a true one-tap portal: ON enters Live Edit, OFF always restores OrbitControls.
function forceLiveEditOrbitState(){
  controls.enabled=!liveEditSelectMode;
}

function exitLiveEditV3(){
  liveEditTransformMode=null;
  liveV2Stop();
  try{setExclusivePartMode('move',false)}catch(_){ }
  liveEditSelectMode=false;
  $('liveEditBadge')?.classList.remove('on');
  $('livePanPad')?.classList.remove('on');
  $('liveEditSelectBtn')?.classList.remove('active');
  $('liveMoveBtn')?.classList.remove('active');
  $('liveRotateBtn')?.classList.remove('active');
  $('liveScaleBtn')?.classList.remove('active');
  controls.enabled=true;
  msg('Live Edit nonaktif — OrbitControls aktif');
}

function enterLiveEditV3(){
  liveEditSelectMode=true;
  liveEditTransformMode=null;
  try{setExclusivePartMode('move',false)}catch(_){ }
  $('liveEditBadge')?.classList.add('on');
  $('livePanPad')?.classList.add('on');
  controls.enabled=false;
  updateLiveEditToolUI();
  msg('Live Edit aktif — sentuh part untuk memilih');
}

// Replace any previous Select behavior. One tap while ON exits immediately,
// even when Move/Rotate/Scale is currently selected.
$('liveEditSelectBtn').onclick=()=>{
  if(liveEditSelectMode) exitLiveEditV3();
  else enterLiveEditV3();
};

// Wrap transform-mode selection so OrbitControls can never remain accidentally
// disabled outside Live Edit and can never wake up while Live Edit is active.
const setLiveEditTransformModeV2=setLiveEditTransformMode;
setLiveEditTransformMode=function(mode){
  if(!liveEditSelectMode){
    controls.enabled=true;
    msg('Tekan Select untuk masuk Live Edit');
    return;
  }
  setLiveEditTransformModeV2(mode);
  controls.enabled=false;
};

// Some older transform/lock paths directly assign controls.enabled. Re-assert
// ownership after every pointer gesture based only on the Live Edit portal state.
['pointerup','pointercancel'].forEach(type=>{
  canvas.addEventListener(type,()=>setTimeout(forceLiveEditOrbitState,0),{capture:false});
});

'''
s=s.replace(marker,js+'\n'+marker,1)
p.write_text(s,encoding='utf-8')
print('Live Edit state v3 applied: Select toggles directly and OrbitControls restore reliably')
