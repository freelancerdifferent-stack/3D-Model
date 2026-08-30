from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

if 'PART_TRANSFORM_STABILITY_V1' in s:
    print('Part Transform stability patch already applied')
    raise SystemExit(0)

# Keep Part Drag / Rotate / Scale strictly mutually-exclusive and transform only
# the mesh selected from Mesh Layers when there is one. This avoids accidental
# retargeting to a large overlapping torso mesh on touch screens.
marker='function partDragVisibleMeshes(){'
if marker not in s:
    raise SystemExit('Android Part Drag helper marker missing')
helpers=r'''// PART_TRANSFORM_STABILITY_V1
function activePartMesh(){
  const m=(activeMeshLayerIndex>=0)?meshList[activeMeshLayerIndex]:null;
  return (m && m.isMesh && m.visible)?m:null;
}
function hitForSpecificMesh(ev,mesh){
  if(!mesh || !setPartDragPointer(ev)) return null;
  if(root) root.updateMatrixWorld(true);
  camera.updateMatrixWorld(true);
  const hits=partDragRaycaster.intersectObject(mesh,false);
  return hits.length?hits[0]:null;
}
function setExclusivePartMode(mode,on){
  partDragEnabled=mode==='move' && !!on;
  partRotateEnabled=mode==='rotate' && !!on;
  partScaleEnabled=mode==='scale' && !!on;
  if(!on){
    partDragEnabled=false;
    partRotateEnabled=false;
    partScaleEnabled=false;
  }
  finishPartDrag();
  finishPartTransform();
  updatePartDragUI();
}
'''
s=s.replace(marker,helpers+'\n'+marker,1)

# Replace mode setters with one state machine. Old implementation could leave a
# stale gesture/pointer around while switching modes.
start=s.find('function setPartDragEnabled(on){')
end=s.find('\nfunction showPartDragSelection(mesh){',start)
if start<0 or end<0: raise SystemExit('setPartDragEnabled block missing')
move_set=r'''function setPartDragEnabled(on){
  setExclusivePartMode('move',on);
  if(on){go('editorScreen');msg('Part Drag ON — pilih Mesh lalu drag part tersebut')}
  else msg('Part Drag OFF');
}'''
s=s[:start]+move_set+s[end:]

start=s.find('function setPartRotateEnabled(on){')
end=s.find('\nfunction setPartScaleEnabled(on){',start)
if start<0 or end<0: raise SystemExit('setPartRotateEnabled block missing')
rot_set=r'''function setPartRotateEnabled(on){
  setExclusivePartMode('rotate',on);
  if(on){go('editorScreen');msg('Part Rotate ON — pilih Mesh lalu drag')}
  else msg('Part Rotate OFF');
}'''
s=s[:start]+rot_set+s[end:]

start=s.find('function setPartScaleEnabled(on){')
end=s.find('\nfunction beginPartTransform(ev){',start)
if start<0 or end<0: raise SystemExit('setPartScaleEnabled block missing')
scale_set=r'''function setPartScaleEnabled(on){
  setExclusivePartMode('scale',on);
  if(on){go('editorScreen');msg('Part Scale ON — pilih Mesh lalu drag')}
  else msg('Part Scale OFF');
}'''
s=s[:start]+scale_set+s[end:]

# Part Drag: if a Mesh Layer is selected, lock targeting to it. Only use generic
# touch-raycast when no Mesh Layer has been selected yet.
start=s.find('function beginPartDrag(ev){')
end=s.find('\nfunction movePartDrag(ev){',start)
if start<0 or end<0: raise SystemExit('beginPartDrag block missing')
new_begin=r'''function beginPartDrag(ev){
  if(!partDragEnabled || !meshList.length) return;
  if(ev.pointerType==='mouse' && ev.button!==0) return;
  if(!setPartDragPointer(ev)) return;
  if(root) root.updateMatrixWorld(true);
  camera.updateMatrixWorld(true);

  const selected=activePartMesh();
  let hits=[];
  let mesh=null;
  if(selected){
    hits=partDragRaycaster.intersectObject(selected,false);
    // Selected-mesh editing should still start when the finger is slightly
    // outside thin geometry; the selected mesh remains the target.
    mesh=selected;
  }else{
    hits=partDragRaycaster.intersectObjects(partDragVisibleMeshes(),false);
    mesh=hits.length?hits[0].object:null;
  }
  if(!mesh)return;

  const index=meshList.indexOf(mesh);
  if(index<0)return;
  if(activeMeshLayerIndex!==index) selectMeshLayer(index);
  rememberPartDragOriginal(mesh);
  showPartDragSelection(mesh);
  partDragMesh=mesh;
  partDragPointerId=ev.pointerId;
  partAxisStartPosition=mesh.position.clone();
  mesh.getWorldPosition(partDragStartWorld);

  const hitPoint=hits.length?hits[0].point:partDragStartWorld.clone();
  const normal=camera.getWorldDirection(new THREE.Vector3()).normalize();
  partDragPlane.setFromNormalAndCoplanarPoint(normal,hitPoint);
  if(!partDragRaycaster.ray.intersectPlane(partDragPlane,partDragStartPoint)){
    partDragMesh=null;partDragPointerId=null;return;
  }
  controls.enabled=false;
  canvas.classList.add('part-transform-touch');
  try{canvas.setPointerCapture(ev.pointerId)}catch(_){ }
  ev.preventDefault();
  ev.stopPropagation();
  if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
}'''
s=s[:start]+new_begin+s[end:]

# Rotate / Scale use the same selected-mesh targeting rule.
start=s.find('function beginPartTransform(ev){')
end=s.find('\nfunction movePartTransform(ev){',start)
if start<0 or end<0: raise SystemExit('beginPartTransform block missing')
new_transform_begin=r'''function beginPartTransform(ev){
  if((!partRotateEnabled && !partScaleEnabled) || !meshList.length) return;
  if(ev.pointerType==='mouse' && ev.button!==0)return;
  if(!setPartDragPointer(ev))return;
  if(root)root.updateMatrixWorld(true);
  camera.updateMatrixWorld(true);

  const selected=activePartMesh();
  let hits=[];
  let mesh=null;
  if(selected){
    hits=partDragRaycaster.intersectObject(selected,false);
    mesh=selected;
  }else{
    hits=partDragRaycaster.intersectObjects(partDragVisibleMeshes(),false);
    mesh=hits.length?hits[0].object:null;
  }
  if(!mesh)return;

  const index=meshList.indexOf(mesh);
  if(index<0)return;
  if(activeMeshLayerIndex!==index)selectMeshLayer(index);
  showPartDragSelection(mesh);
  partDragMesh=mesh;
  partDragPointerId=ev.pointerId;
  partTransformStartX=ev.clientX;
  partTransformStartY=ev.clientY;
  if(partRotateEnabled){rememberPartRotateOriginal(mesh);partRotateStart=mesh.rotation.clone()}
  if(partScaleEnabled){rememberPartScaleOriginal(mesh);partScaleStart=mesh.scale.clone()}
  controls.enabled=false;
  canvas.classList.add('part-transform-touch');
  try{canvas.setPointerCapture(ev.pointerId)}catch(_){ }
  ev.preventDefault();
  ev.stopPropagation();
  if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
}'''
s=s[:start]+new_transform_begin+s[end:]

# Prevent stale state after transform finish as well.
needle='''    partScaleStart=null;\n    controls.enabled=true;\n  }\n}'''
repl='''    partScaleStart=null;\n    controls.enabled=true;\n    canvas.classList.remove('part-transform-touch');\n  }\n}'''
if needle not in s: raise SystemExit('finishPartTransform tail missing')
s=s.replace(needle,repl,1)

p.write_text(s,encoding='utf-8')
print('Part Transform stability patch applied')
