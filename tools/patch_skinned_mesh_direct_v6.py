from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_SKINNED_DIRECT_V6' in s:
    print('Skinned direct v6 already applied'); raise SystemExit(0)

# This patch must run after Live Edit v5 and Project Manager are present.
for marker in ['LIVE_EDIT_TOUCH_TRANSFORM_V5','function loadProjectGlb(data){','function exportProjectObject(obj){']:
    if marker not in s: raise SystemExit('Missing required marker: '+marker)

insert_at=s.rfind('</script>')
if insert_at<0: raise SystemExit('script end marker missing')

js=r'''
// LIVE_EDIT_SKINNED_DIRECT_V6
// A SkinnedMesh in Three.js normally uses bindMode="attached". In that mode,
// moving mesh.position can be cancelled by the skin bind inverse, making the
// selection helper move while the rendered skin/material appears to disappear.
// Keep the original bind matrix fixed (detached) and transform the mesh itself.
function liveV6PrepareSkinnedMesh(mesh){
  if(!mesh || !mesh.isSkinnedMesh)return mesh;
  if(!mesh.userData.__liveEditDetachedPrepared){
    mesh.userData.__liveEditDetachedPrepared=true;
    mesh.userData.__liveEditOldBindMode=mesh.bindMode||'attached';
  }
  mesh.bindMode='detached';
  // Detached mode intentionally keeps bindMatrix fixed at the imported bind pose.
  if(mesh.bindMatrix && mesh.bindMatrixInverse){
    mesh.bindMatrixInverse.copy(mesh.bindMatrix).invert();
  }
  mesh.updateMatrixWorld(true);
  return mesh;
}

// V5 is the Android touch owner. Prepare the selected SkinnedMesh before V5
// snapshots position/rotation/scale, so the actual visible mesh is transformed.
if(typeof liveV5Start==='function'){
  const _liveV5StartDirectV6=liveV5Start;
  liveV5Start=function(ev){
    const selected=(typeof liveV5SelectedMesh==='function')?liveV5SelectedMesh():null;
    if(selected)liveV6PrepareSkinnedMesh(selected);
    return _liveV5StartDirectV6(ev);
  };
}

// Keep desktop/pointer route consistent too.
if(typeof liveV4Begin==='function'){
  const _liveV4BeginDirectV6=liveV4Begin;
  liveV4Begin=function(ev){
    const selected=(typeof liveV4SelectedMesh==='function')?liveV4SelectedMesh():null;
    if(selected)liveV6PrepareSkinnedMesh(selected);
    return _liveV4BeginDirectV6(ev);
  };
}

// Recovery for projects created by the previous carrier experiment.
// Flatten __LiveEditCarrier_* groups back into their child transform before
// rendering/exporting. This also prevents synthetic editor groups from being
// serialized into future project GLBs.
function liveV6RepairCarrierTree(rootObj){
  if(!rootObj)return rootObj;
  rootObj.updateMatrixWorld(true);
  const carriers=[];
  rootObj.traverse(o=>{
    if(o && o.isGroup && typeof o.name==='string' && o.name.startsWith('__LiveEditCarrier_'))carriers.push(o);
  });
  // Deepest first in case an old project somehow contains nested carriers.
  carriers.reverse().forEach(carrier=>{
    const parent=carrier.parent;
    if(!parent)return;
    carrier.updateMatrix();
    const children=[...carrier.children];
    children.forEach(child=>{
      child.updateMatrix();
      // childLocal(new parent) = carrierLocal * childLocal(old carrier)
      const combined=carrier.matrix.clone().multiply(child.matrix);
      parent.add(child);
      combined.decompose(child.position,child.quaternion,child.scale);
      child.updateMatrix();
      if(child.isSkinnedMesh)liveV6PrepareSkinnedMesh(child);
    });
    parent.remove(carrier);
  });
  rootObj.traverse(o=>{if(o.isSkinnedMesh && o.userData?.__liveEditDetachedPrepared)liveV6PrepareSkinnedMesh(o)});
  rootObj.updateMatrixWorld(true);
  return rootObj;
}

// Clean scene hierarchy immediately before Save Project exports a model.
const _exportProjectObjectDirectV6=exportProjectObject;
exportProjectObject=function(obj){
  liveV6RepairCarrierTree(obj);
  return _exportProjectObjectDirectV6(obj);
};

// Repair older saved project GLBs as soon as they are parsed.
const _loadProjectGlbDirectV6=loadProjectGlb;
loadProjectGlb=function(data){
  return _loadProjectGlbDirectV6(data).then(obj=>liveV6RepairCarrierTree(obj));
};
'''

s=s[:insert_at]+js+'\n'+s[insert_at:]
p.write_text(s,encoding='utf-8')
print('SkinnedMesh direct transform v6 applied; carrier hack removed/repaired for projects')
