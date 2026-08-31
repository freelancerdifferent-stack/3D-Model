from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_VISUAL_PREVIEW_V7' in s:
    print('Live Edit visual preview v7 already applied'); raise SystemExit(0)

for marker in ['LIVE_EDIT_SKINNED_DIRECT_V6','LIVE_EDIT_TOUCH_TRANSFORM_V5','LIVE_EDIT_MESH_CARRIER_V5']:
    if marker not in s: raise SystemExit('Missing required marker: '+marker)

insert_at=s.rfind('</script>')
if insert_at<0: raise SystemExit('script end marker missing')

js=r'''
// LIVE_EDIT_VISUAL_PREVIEW_V7
// Android generates PointerEvents for the same finger that also generates TouchEvents.
// Older V4 + carrier handlers were therefore moving a helper/carrier while V5 was
// moving the real SkinnedMesh. Keep ONE owner on touch devices: native V5.
function liveV7IsTouchPointer(ev){
  return !!ev && (ev.pointerType==='touch' || ev.pointerType==='pen');
}

// Completely neutralize the old carrier target. The source mesh itself is now the
// only editable object; v6 puts SkinnedMesh into detached bind mode so modelMatrix
// is visible immediately instead of being cancelled by skin bind inverse.
liveEditActualTransformTarget=function(mesh){
  if(mesh?.isSkinnedMesh && typeof liveV6PrepareSkinnedMesh==='function')liveV6PrepareSkinnedMesh(mesh);
  return mesh;
};

// Remove synthetic carriers left in the currently loaded scene without changing
// the intended child local transform.
function liveV7FlattenCurrentCarriers(){
  const roots=(typeof sceneLayers!=='undefined')?sceneLayers.filter(l=>l.kind==='model').map(l=>l.object):[];
  roots.forEach(r=>{if(typeof liveV6RepairCarrierTree==='function')liveV6RepairCarrierTree(r)});
  if(typeof refreshMeshList==='function')try{refreshMeshList()}catch(_){ }
}

// Disable V4 pointer transform for finger/stylus. Mouse still uses V4 on desktop.
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
      // Force matrices now so the current frame renders at the edited location.
      mesh.updateMatrix();
      mesh.updateMatrixWorld(true);
      if(mesh.skeleton)mesh.skeleton.update();
    }
    return _liveV5StartVisualV7(ev);
  };
}

// Re-assert detached skinning and matrices on every drag frame. This is the key
// visual-preview fix: the visible vertices follow position/rotation/scale BEFORE
// Save/Open, not only after GLB serialization.
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

// Also prepare immediately when a transform mode is chosen, so there is no one-
// frame flash/disappearance between tapping Move/Rotate/Scale and starting drag.
if(typeof liveV5SetMode==='function'){
  const _liveV5SetModeVisualV7=liveV5SetMode;
  liveV5SetMode=function(mode){
    liveV7FlattenCurrentCarriers();
    const mesh=(typeof liveV5SelectedMesh==='function')?liveV5SelectedMesh():null;
    if(mesh?.isSkinnedMesh && typeof liveV6PrepareSkinnedMesh==='function'){
      liveV6PrepareSkinnedMesh(mesh);
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
print('Live Edit visual preview v7 applied: one Android touch owner, no carrier, live SkinnedMesh matrices refreshed')
