from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_TRANSFORM_V1' in s:
    print('Live Edit transform already applied'); raise SystemExit(0)

# Reuse the existing left toolbar buttons.
repls={
'<button class="tool"><b>✣</b>Move</button>':'<button class="tool" id="liveMoveBtn"><b>✣</b>Move</button>',
'<button class="tool"><b>⟳</b>Rotate</button>':'<button class="tool" id="liveRotateBtn"><b>⟳</b>Rotate</button>',
'<button class="tool"><b>⌗</b>Scale</button>':'<button class="tool" id="liveScaleBtn"><b>⌗</b>Scale</button>',
}
for old,new in repls.items():
    if old not in s: raise SystemExit('Toolbar marker missing: '+old)
    s=s.replace(old,new,1)

# Long press is no longer part of the Live Edit workflow. Do not let its parent
# capture listener compete with direct select/transform gestures while Select is ON.
needle='function beginPartLongPress(ev){\n'
if needle not in s: raise SystemExit('beginPartLongPress marker missing')
s=s.replace(needle,"function beginPartLongPress(ev){\n  if(typeof liveEditSelectMode!=='undefined' && liveEditSelectMode)return;\n",1)

# Add transform-mode state beside the Live Edit state.
needle='let liveEditSelectMode=false;\nlet liveEditPointerId=null;'
if needle not in s: raise SystemExit('Live Edit state marker missing')
s=s.replace(needle,"let liveEditSelectMode=false;\nlet liveEditTransformMode=null; // LIVE_EDIT_TRANSFORM_V1\nlet liveEditPointerId=null;",1)

# Selection capture must stand aside when Move/Rotate/Scale is active so the
# established part-transform handlers receive the canvas drag gesture.
needle="  if(!liveEditSelectMode)return;\n  if(ev.pointerType==='mouse'&&ev.button!==0)return;\n  liveEditPointerId=ev.pointerId;"
if needle not in s: raise SystemExit('Live Edit pointerdown marker missing')
s=s.replace(needle,"  if(!liveEditSelectMode || liveEditTransformMode)return;\n  if(ev.pointerType==='mouse'&&ev.button!==0)return;\n  liveEditPointerId=ev.pointerId;",1)
needle="  if(!liveEditSelectMode||ev.pointerId!==liveEditPointerId)return;"
if needle not in s: raise SystemExit('Live Edit pointerup marker missing')
s=s.replace(needle,"  if(!liveEditSelectMode || liveEditTransformMode || ev.pointerId!==liveEditPointerId)return;",1)

# Replace Select click behavior: while a transform tool is active, Select first
# returns to pick mode; pressing Select again exits Live Edit and restores orbit.
needle="$('liveEditSelectBtn').onclick=()=>setLiveEditSelectMode(!liveEditSelectMode);"
if needle not in s: raise SystemExit('Select click marker missing')
replacement=r'''function updateLiveEditToolUI(){
  $('liveEditSelectBtn')?.classList.toggle('active',liveEditSelectMode && !liveEditTransformMode);
  $('liveMoveBtn')?.classList.toggle('active',liveEditSelectMode && liveEditTransformMode==='move');
  $('liveRotateBtn')?.classList.toggle('active',liveEditSelectMode && liveEditTransformMode==='rotate');
  $('liveScaleBtn')?.classList.toggle('active',liveEditSelectMode && liveEditTransformMode==='scale');
}
function setLiveEditTransformMode(mode){
  if(!liveEditSelectMode){msg('Tekan Select dulu untuk masuk Live Edit');return}
  const mesh=(typeof activePartMesh==='function')?activePartMesh():null;
  if(!mesh){msg('Pilih part dulu dengan Select');return}
  if(typeof isMeshPartLocked==='function' && isMeshPartLocked(mesh)){msg('Part ini dikunci');return}
  liveEditTransformMode=mode;
  if(typeof setPartTransformAxis==='function')setPartTransformAxis('free');
  if(typeof setExclusivePartMode==='function')setExclusivePartMode(mode,true);
  controls.enabled=false;
  updateLiveEditToolUI();
  if(typeof showStrongPartSelection==='function')showStrongPartSelection(mesh);
  msg((mode==='move'?'Move':mode==='rotate'?'Rotate':'Scale')+' aktif — drag langsung part yang terseleksi');
}
$('liveEditSelectBtn').onclick=()=>{
  if(liveEditSelectMode && liveEditTransformMode){
    liveEditTransformMode=null;
    if(typeof setExclusivePartMode==='function')setExclusivePartMode('move',false);
    controls.enabled=false;
    updateLiveEditToolUI();
    msg('Select aktif — sentuh part lain');
    return;
  }
  setLiveEditSelectMode(!liveEditSelectMode);
  if(!liveEditSelectMode){
    liveEditTransformMode=null;
    if(typeof setExclusivePartMode==='function')setExclusivePartMode('move',false);
  }
  updateLiveEditToolUI();
};
$('liveMoveBtn').onclick=()=>setLiveEditTransformMode('move');
$('liveRotateBtn').onclick=()=>setLiveEditTransformMode('rotate');
$('liveScaleBtn').onclick=()=>setLiveEditTransformMode('scale');'''
s=s.replace(needle,replacement,1)

# When exiting Live Edit, clear any active part mode. When entering, default to Select.
needle='function setLiveEditSelectMode(on){\n  liveEditSelectMode=!!on;'
if needle not in s: raise SystemExit('setLiveEditSelectMode marker missing')
s=s.replace(needle,"function setLiveEditSelectMode(on){\n  liveEditSelectMode=!!on;\n  liveEditTransformMode=null;\n  if(typeof setExclusivePartMode==='function')setExclusivePartMode('move',false);",1)

# Existing transform finish functions restore OrbitControls. Wrap them so Live Edit
# owns camera state and keeps OrbitControls disabled after every drag.
marker='// Manual horizontal/vertical camera pan. Move camera and OrbitControls target together,'
if marker not in s: raise SystemExit('Live pan marker missing')
wrap=r'''// LIVE_EDIT_TRANSFORM_V1: Live Edit owns OrbitControls state.
const liveEditFinishPartDragBase=finishPartDrag;
finishPartDrag=function(){
  const out=liveEditFinishPartDragBase.apply(this,arguments);
  if(liveEditSelectMode)controls.enabled=false;
  return out;
};
const liveEditFinishPartTransformBase=finishPartTransform;
finishPartTransform=function(){
  const out=liveEditFinishPartTransformBase.apply(this,arguments);
  if(liveEditSelectMode)controls.enabled=false;
  return out;
};

'''
s=s.replace(marker,wrap+marker,1)

# Keep selection highlight and UI coherent after a part is chosen.
needle="  msg('Part dipilih: '+(typeof meshLayerDisplayName==='function'?meshLayerDisplayName(mesh,index):(mesh.name||('Mesh '+(index+1)))));"
if needle not in s: raise SystemExit('Live pick message marker missing')
s=s.replace(needle,"  liveEditTransformMode=null;\n  if(typeof setExclusivePartMode==='function')setExclusivePartMode('move',false);\n  controls.enabled=false;\n  updateLiveEditToolUI();\n"+needle,1)

p.write_text(s,encoding='utf-8')
print('Live Edit toolbar Move/Rotate/Scale wired to selected Mesh Part')
