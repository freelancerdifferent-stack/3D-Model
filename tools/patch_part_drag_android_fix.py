from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

if 'PART_DRAG_ANDROID_FIX_V2' in s:
    print('Android Part Drag fix already applied')
    raise SystemExit(0)

# Make the viewport own touch gestures only while a part transform tool is active.
css_marker='.part-drag-badge.on{display:flex}'
if css_marker not in s:
    raise SystemExit('Part Drag CSS marker missing')
s=s.replace(css_marker, css_marker+'\ncanvas.part-transform-touch{touch-action:none}', 1)

# Replace the original move begin handler with a more robust Android/WebView version.
start=s.find('function beginPartDrag(ev){')
end=s.find('\nfunction movePartDrag(ev){', start)
if start<0 or end<0:
    raise SystemExit('beginPartDrag block missing')
new_begin=r'''// PART_DRAG_ANDROID_FIX_V2
function partDragVisibleMeshes(){
  return meshList.filter(m=>m && m.isMesh && m.visible && (!m.parent || m.parent.visible!==false));
}
function beginPartDrag(ev){
  if(!partDragEnabled || !meshList.length) return;
  if(ev.pointerType==='mouse' && ev.button!==0) return;
  if(!setPartDragPointer(ev)) return;

  // Update matrices first; Assimp/FBX models can otherwise raycast against stale transforms.
  if(root) root.updateMatrixWorld(true);
  camera.updateMatrixWorld(true);

  let hits=partDragRaycaster.intersectObjects(partDragVisibleMeshes(),false);
  let mesh=hits.length ? hits[0].object : null;

  // On small phone screens the exact touch can miss thin geometry. If a Mesh Layer
  // was explicitly selected, allow that selected part as a fallback target.
  if(!mesh && activeMeshLayerIndex>=0) mesh=meshList[activeMeshLayerIndex]||null;
  if(!mesh) return;

  const index=meshList.indexOf(mesh);
  if(index<0) return;
  selectMeshLayer(index);
  rememberPartDragOriginal(mesh);
  showPartDragSelection(mesh);
  partDragMesh=mesh;
  partDragPointerId=ev.pointerId;
  partAxisStartPosition=mesh.position.clone();
  mesh.getWorldPosition(partDragStartWorld);

  const hitPoint=hits.length ? hits[0].point : partDragStartWorld;
  const normal=camera.getWorldDirection(new THREE.Vector3()).normalize();
  partDragPlane.setFromNormalAndCoplanarPoint(normal,hitPoint);
  if(!partDragRaycaster.ray.intersectPlane(partDragPlane,partDragStartPoint)){
    partDragMesh=null; partDragPointerId=null; return;
  }

  controls.enabled=false;
  canvas.classList.add('part-transform-touch');
  try{canvas.setPointerCapture(ev.pointerId)}catch(_){ }
  ev.preventDefault();
  ev.stopPropagation();
  if(ev.stopImmediatePropagation) ev.stopImmediatePropagation();
}'''
s=s[:start]+new_begin+s[end:]

# Harden move handler against Android pointer cancellation / stale matrices.
old='''  partDragMesh.updateMatrixWorld(true);\n  if(partDragHelper) partDragHelper.update();\n  ev.preventDefault();\n  ev.stopPropagation();'''
new='''  partDragMesh.updateMatrixWorld(true);\n  if(root) root.updateMatrixWorld(true);\n  if(partDragHelper) partDragHelper.update();\n  ev.preventDefault();\n  ev.stopPropagation();\n  if(ev.stopImmediatePropagation) ev.stopImmediatePropagation();'''
if old not in s:
    raise SystemExit('movePartDrag tail missing')
s=s.replace(old,new,1)

# Always restore OrbitControls and touch-action when the gesture ends.
old_finish='''  partDragPointerId=null;\n  partDragMesh=null;\n  partAxisStartPosition=null;\n  controls.enabled=true;'''
new_finish='''  partDragPointerId=null;\n  partDragMesh=null;\n  partAxisStartPosition=null;\n  controls.enabled=true;\n  canvas.classList.remove('part-transform-touch');'''
if old_finish not in s:
    raise SystemExit('finishPartDrag tail missing')
s=s.replace(old_finish,new_finish,1)

# Synchronize touch-action immediately when toggling tools.
ui_tail='''  updatePartAxisOverlay();\n}'''
ui_repl='''  updatePartAxisOverlay();\n  canvas.classList.toggle('part-transform-touch',partDragEnabled||partRotateEnabled||partScaleEnabled);\n}'''
if ui_tail not in s:
    raise SystemExit('Part transform UI tail missing')
s=s.replace(ui_tail,ui_repl,1)

p.write_text(s,encoding='utf-8')
print('Android Part Drag fix applied')
