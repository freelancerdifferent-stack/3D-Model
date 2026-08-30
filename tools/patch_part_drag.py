from pathlib import Path

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

if 'id="partDragBtn"' in s:
    print('Part Drag patch already applied')
    raise SystemExit(0)

# Small visual state for the dedicated preview drag tool.
css_marker = '.hidden{display:none!important}'
css = '''\n.part-drag-badge{position:absolute;left:72px;top:10px;z-index:5;display:none;align-items:center;gap:7px;padding:7px 10px;border:1px solid #4c9cff;border-radius:9px;background:rgba(13,25,39,.92);font-size:11px;color:#8fc0ff;pointer-events:none}\n.part-drag-badge.on{display:flex}\n.part-drag-dot{width:7px;height:7px;border-radius:50%;background:#61a6ff}\n.mesh-layer-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}\n.mesh-layer-actions button{margin-top:0}\n'''
if css_marker not in s:
    raise SystemExit('CSS marker missing')
s = s.replace(css_marker, css_marker + css, 1)

# Add a separate tool; do not replace or alter the existing Move tool.
tool_marker = '          <button class="tool"><b>✣</b>Move</button>'
tool_repl = tool_marker + '\n          <button class="tool" id="partDragBtn"><b>☝</b>Part Drag</button>'
if tool_marker not in s:
    raise SystemExit('Move tool marker missing')
s = s.replace(tool_marker, tool_repl, 1)

# Show an explicit mode indicator inside the 3D preview.
viewport_marker = '          <div class="overright"><span class="pill" id="meshLabel">0 Mesh</span></div>'
viewport_repl = viewport_marker + '\n          <div class="part-drag-badge" id="partDragBadge"><span class="part-drag-dot"></span>PART DRAG • touch a part and drag</div>'
if viewport_marker not in s:
    raise SystemExit('Viewport marker missing')
s = s.replace(viewport_marker, viewport_repl, 1)

# Add controls to the separate Mesh Layers feature only. Existing Layers remains untouched.
mesh_button_marker = '      <button class="primary" id="meshLayersEditBtn">Edit Selected Material / Texture</button>'
mesh_button_repl = '''      <button class="primary" id="meshLayersEditBtn">Edit Selected Material / Texture</button>\n      <div class="mesh-layer-actions">\n        <button class="outline" id="meshLayersDragBtn">☝ Part Drag in Preview</button>\n        <button class="outline" id="meshLayersResetPosBtn">↶ Reset Part Position</button>\n      </div>'''
if mesh_button_marker not in s:
    raise SystemExit('Mesh Layers controls marker missing')
s = s.replace(mesh_button_marker, mesh_button_repl, 1)

# Insert state and behavior after Mesh Layers state so it can reuse activeMeshLayerIndex.
state_marker = 'let activeMeshLayerIndex=-1;'
part_drag_code = r'''let partDragEnabled=false;
let partDragPointerId=null;
let partDragMesh=null;
let partDragPlane=new THREE.Plane();
let partDragStartPoint=new THREE.Vector3();
let partDragStartWorld=new THREE.Vector3();
const partDragRaycaster=new THREE.Raycaster();
const partDragPointer=new THREE.Vector2();
let partDragHelper=null;

function setPartDragPointer(ev){
  const r=canvas.getBoundingClientRect();
  if(!r.width || !r.height) return false;
  partDragPointer.x=((ev.clientX-r.left)/r.width)*2-1;
  partDragPointer.y=-((ev.clientY-r.top)/r.height)*2+1;
  partDragRaycaster.setFromCamera(partDragPointer,camera);
  return true;
}
function updatePartDragUI(){
  const btn=$('partDragBtn');
  if(btn) btn.classList.toggle('active',partDragEnabled);
  const badge=$('partDragBadge');
  if(badge) badge.classList.toggle('on',partDragEnabled);
  const meshBtn=$('meshLayersDragBtn');
  if(meshBtn) meshBtn.textContent=partDragEnabled?'✓ Part Drag Active':'☝ Part Drag in Preview';
}
function setPartDragEnabled(on){
  partDragEnabled=!!on;
  if(!partDragEnabled) finishPartDrag();
  updatePartDragUI();
  if(partDragEnabled){
    go('editorScreen');
    msg('Part Drag ON — sentuh part lalu drag');
  }else{
    msg('Part Drag OFF');
  }
}
function showPartDragSelection(mesh){
  if(partDragHelper){ scene.remove(partDragHelper); partDragHelper.geometry?.dispose?.(); partDragHelper.material?.dispose?.(); partDragHelper=null; }
  if(!mesh)return;
  partDragHelper=new THREE.BoxHelper(mesh,0x61a6ff);
  partDragHelper.raycast=()=>{};
  scene.add(partDragHelper);
}
function rememberPartDragOriginal(mesh){
  if(!mesh.userData.__partDragOriginalPosition){
    mesh.userData.__partDragOriginalPosition={x:mesh.position.x,y:mesh.position.y,z:mesh.position.z};
  }
}
function beginPartDrag(ev){
  if(!partDragEnabled || !meshList.length || ev.button>0) return;
  if(!setPartDragPointer(ev)) return;
  const hits=partDragRaycaster.intersectObjects(meshList.filter(m=>m.visible),false);
  if(!hits.length) return;
  const mesh=hits[0].object;
  const index=meshList.indexOf(mesh);
  if(index<0)return;
  selectMeshLayer(index);
  rememberPartDragOriginal(mesh);
  showPartDragSelection(mesh);
  partDragMesh=mesh;
  partDragPointerId=ev.pointerId;
  mesh.getWorldPosition(partDragStartWorld);
  const normal=camera.getWorldDirection(new THREE.Vector3());
  partDragPlane.setFromNormalAndCoplanarPoint(normal,hits[0].point);
  if(!partDragRaycaster.ray.intersectPlane(partDragPlane,partDragStartPoint)){
    partDragMesh=null; partDragPointerId=null; return;
  }
  controls.enabled=false;
  try{canvas.setPointerCapture(ev.pointerId)}catch(_){ }
  ev.preventDefault();
  ev.stopPropagation();
}
function movePartDrag(ev){
  if(!partDragEnabled || !partDragMesh || ev.pointerId!==partDragPointerId) return;
  if(!setPartDragPointer(ev)) return;
  const p=new THREE.Vector3();
  if(!partDragRaycaster.ray.intersectPlane(partDragPlane,p)) return;
  const desiredWorld=partDragStartWorld.clone().add(p.sub(partDragStartPoint));
  if(partDragMesh.parent){
    partDragMesh.parent.updateMatrixWorld(true);
    partDragMesh.position.copy(partDragMesh.parent.worldToLocal(desiredWorld.clone()));
  }else{
    partDragMesh.position.copy(desiredWorld);
  }
  partDragMesh.updateMatrixWorld(true);
  if(partDragHelper) partDragHelper.update();
  ev.preventDefault();
  ev.stopPropagation();
}
function finishPartDrag(ev){
  if(ev && partDragPointerId!==null && ev.pointerId!==partDragPointerId)return;
  if(partDragPointerId!==null){ try{canvas.releasePointerCapture(partDragPointerId)}catch(_){ } }
  partDragPointerId=null;
  partDragMesh=null;
  controls.enabled=true;
}
function resetSelectedPartPosition(){
  const mesh=meshList[activeMeshLayerIndex];
  if(!mesh){msg('Pilih satu mesh dulu');return}
  const p=mesh.userData.__partDragOriginalPosition;
  if(!p){msg('Mesh ini belum pernah digeser');return}
  mesh.position.set(p.x,p.y,p.z);
  mesh.updateMatrixWorld(true);
  if(partDragHelper) partDragHelper.update();
  msg('Posisi part dikembalikan');
}

'''
if state_marker not in s:
    raise SystemExit('Mesh Layers state marker missing')
s = s.replace(state_marker, state_marker + '\n' + part_drag_code, 1)

# Highlight Mesh Layers selections in the preview as well.
select_marker = "  const mesh=meshList[index];\n  $('meshLayersStatus').textContent=`Target aktif: ${meshLayerDisplayName(mesh,index)} • Material/Texture hanya diterapkan ke mesh ini.`;"
select_repl = "  const mesh=meshList[index];\n  showPartDragSelection(mesh);\n  $('meshLayersStatus').textContent=`Target aktif: ${meshLayerDisplayName(mesh,index)} • Material/Texture hanya diterapkan ke mesh ini.`;"
if select_marker not in s:
    raise SystemExit('selectMeshLayer marker missing')
s = s.replace(select_marker, select_repl, 1)

# Wire up touch/pointer drag. Capture phase lets us suppress OrbitControls only when a part is actually grabbed.
handler_marker = "$('meshLayersNav').addEventListener('click',()=>renderMeshLayers());"
handler_repl = r'''$('partDragBtn').addEventListener('click',()=>setPartDragEnabled(!partDragEnabled));
$('meshLayersDragBtn').addEventListener('click',()=>setPartDragEnabled(!partDragEnabled));
$('meshLayersResetPosBtn').addEventListener('click',resetSelectedPartPosition);
canvas.addEventListener('pointerdown',beginPartDrag,{capture:true});
canvas.addEventListener('pointermove',movePartDrag,{capture:true});
canvas.addEventListener('pointerup',finishPartDrag,{capture:true});
canvas.addEventListener('pointercancel',finishPartDrag,{capture:true});
$('meshLayersNav').addEventListener('click',()=>renderMeshLayers());'''
if handler_marker not in s:
    raise SystemExit('Mesh Layers handler marker missing')
s = s.replace(handler_marker, handler_repl, 1)

# Keep the selection helper aligned while animations or parent transforms update.
animate_marker = '  controls.update();\n  renderer.render(scene,camera);'
animate_repl = '  controls.update();\n  if(partDragHelper) partDragHelper.update();\n  renderer.render(scene,camera);'
if animate_marker not in s:
    raise SystemExit('Animation render marker missing')
s = s.replace(animate_marker, animate_repl, 1)

p.write_text(s, encoding='utf-8')
print('Part Drag patch applied')
