from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_VISUAL_PREVIEW_V7' in s:
    print('Live Edit visual preview v7 already applied'); raise SystemExit(0)

for marker in ['LIVE_EDIT_SKINNED_DIRECT_V6','LIVE_EDIT_TOUCH_TRANSFORM_V5']:
    if marker not in s: raise SystemExit('Missing required marker: '+marker)

insert_at=s.rfind('</script>')
if insert_at<0: raise SystemExit('script end marker missing')

js=r'''
// LIVE_EDIT_VISUAL_PREVIEW_V7
// Android generates PointerEvents for the same finger that also generates TouchEvents.
// Keep ONE transform owner on touch devices: native V5 Touch Events.
function liveV7IsTouchPointer(ev){
  return !!ev && (ev.pointerType==='touch' || ev.pointerType==='pen');
}

// If an old carrier helper happens to exist in a previously patched runtime,
// neutralize it. In the current pipeline this function is normally absent.
if(typeof liveEditActualTransformTarget==='function'){
  liveEditActualTransformTarget=function(mesh){
    if(mesh?.isSkinnedMesh && typeof liveV6PrepareSkinnedMesh==='function')liveV6PrepareSkinnedMesh(mesh);
    return mesh;
  };
}

function liveV7FlattenCurrentCarriers(){
  const roots=(typeof sceneLayers!=='undefined')?sceneLayers.filter(l=>l.kind==='model').map(l=>l.object):[];
  roots.forEach(r=>{if(typeof liveV6RepairCarrierTree==='function')liveV6RepairCarrierTree(r)});
}

// Do not let V4 PointerEvents also transform the same finger drag.
if(typeof liveV4Begin==='function'){
  const _liveV4BeginVisualV7=liveV4Begin;
  liveV4Begin=function(ev){
    if(liveV7IsTouchPointer(ev))return false;
    return _liveV4BeginVisualV7(ev);
  };
}

// Prepare the exact selected source BEFORE V5 snapshots its transform.
if(typeof liveV5Start==='function'){
  const _liveV5StartVisualV7=liveV5Start;
  liveV5Start=function(ev){
    liveV7FlattenCurrentCarriers();
    const mesh=(typeof liveV5SelectedMesh==='function')?liveV5SelectedMesh():null;
    if(mesh?.isSkinnedMesh && typeof liveV6PrepareSkinnedMesh==='function'){
      liveV6PrepareSkinnedMesh(mesh);
      mesh.updateMatrix();
      mesh.updateMatrixWorld(true);
      if(mesh.skeleton)mesh.skeleton.update();
    }
    return _liveV5StartVisualV7(ev);
  };
}

// Re-assert detached skinning and matrices on EVERY drag frame. The edited
// SkinnedMesh must visually follow the finger immediately, not only appear at the
// new transform after Save -> Open.
if(typeof liveV5Move==='function'){
  const _liveV5MoveVisualV7=liveV5Move;
  liveV5Move=function(ev){
    const result=_liveV5MoveVisualV7(ev);
    const mesh=(typeof liveV5Mesh!=='undefined')?liveV5Mesh:null;
    if(mesh){
      if(mesh.isSkinnedMesh && typeof liveV6PrepareSkinnedMesh==='function')liveV6PrepareSkinnedMesh(mesh);
      mesh.updateMatrix();
      mesh.updateMatrixWorld(true);
      if(mesh.isSkinnedMesh && mesh.skeleton)mesh.skeleton.update();
      if(typeof partDragHelper!=='undefined' && partDragHelper){try{partDragHelper.update()}catch(_){ }}
    }
    return result;
  };
}

if(typeof liveV5SetMode==='function'){
  const _liveV5SetModeVisualV7=liveV5SetMode;
  liveV5SetMode=function(mode){
    liveV7FlattenCurrentCarriers();
    const mesh=(typeof liveV5SelectedMesh==='function')?liveV5SelectedMesh():null;
    if(mesh?.isSkinnedMesh && typeof liveV6PrepareSkinnedMesh==='function'){
      liveV6PrepareSkinnedMesh(mesh);
      mesh.updateMatrix();
      mesh.updateMatrixWorld(true);
      if(mesh.skeleton)mesh.skeleton.update();
    }
    return _liveV5SetModeVisualV7(mode);
  };
  $('liveMoveBtn').onclick=()=>liveV5SetMode('move');
  $('liveRotateBtn').onclick=()=>liveV5SetMode('rotate');
  $('liveScaleBtn').onclick=()=>liveV5SetMode('scale');
}
'''

s=s[:insert_at]+js+'\n'+s[insert_at:]
p.write_text(s,encoding='utf-8')
print('Live Edit visual preview v7 applied: one Android touch owner and live SkinnedMesh matrix refresh')
