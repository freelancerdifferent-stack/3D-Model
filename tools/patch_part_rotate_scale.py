from pathlib import Path

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

if 'id="partRotateBtn"' in s:
    print('Part Rotate/Scale patch already applied')
    raise SystemExit(0)

# Dedicated Rotate / Scale tools beside the existing Part Drag tool.
tool_marker = '          <button class="tool" id="partDragBtn"><b>☝</b>Part Drag</button>'
tool_repl = tool_marker + '''\n          <button class="tool" id="partRotateBtn"><b>⟳</b>Part Rotate</button>\n          <button class="tool" id="partScaleBtn"><b>⤢</b>Part Scale</button>'''
if tool_marker not in s:
    raise SystemExit('Part Drag tool marker missing')
s = s.replace(tool_marker, tool_repl, 1)

# Reuse the existing preview badge, but allow its text to change with the active mode.
badge_marker = '<div class="part-drag-badge" id="partDragBadge"><span class="part-drag-dot"></span>PART DRAG • touch a part and drag</div>'
badge_repl = '<div class="part-drag-badge" id="partDragBadge"><span class="part-drag-dot"></span><span id="partTransformBadgeText">PART DRAG • touch a part and drag</span></div>'
if badge_marker not in s:
    raise SystemExit('Part Drag badge marker missing')
s = s.replace(badge_marker, badge_repl, 1)

# Expand only the Mesh Layers controls. The main Layers feature remains untouched.
actions_marker = '''      <div class="mesh-layer-actions">\n        <button class="outline" id="meshLayersDragBtn">☝ Part Drag in Preview</button>\n        <button class="outline" id="meshLayersResetPosBtn">↶ Reset Part Position</button>\n      </div>'''
actions_repl = '''      <div class="mesh-layer-actions">\n        <button class="outline" id="meshLayersDragBtn">☝ Part Drag in Preview</button>\n        <button class="outline" id="meshLayersResetPosBtn">↶ Reset Position</button>\n        <button class="outline" id="meshLayersRotateBtn">⟳ Part Rotate</button>\n        <button class="outline" id="meshLayersResetRotBtn">↶ Reset Rotation</button>\n        <button class="outline" id="meshLayersScaleBtn">⤢ Part Scale</button>\n        <button class="outline" id="meshLayersResetScaleBtn">↶ Reset Scale</button>\n      </div>'''
if actions_marker not in s:
    raise SystemExit('Mesh Layers Part Drag action block missing')
s = s.replace(actions_marker, actions_repl, 1)

# Add Rotate/Scale state after existing Part Drag state.
state_marker = 'let partDragEnabled=false;'
state_repl = '''let partDragEnabled=false;\nlet partRotateEnabled=false;\nlet partScaleEnabled=false;\nlet partTransformStartX=0, partTransformStartY=0;\nlet partRotateStart=null, partScaleStart=null;'''
if state_marker not in s:
    raise SystemExit('Part Drag state marker missing')
s = s.replace(state_marker, state_repl, 1)

# Replace the UI updater so all three mutually-exclusive modes are represented.
ui_start = 'function updatePartDragUI(){'
ui_end = '}\nfunction setPartDragEnabled(on){'
start = s.find(ui_start)
end = s.find(ui_end, start)
if start < 0 or end < 0:
    raise SystemExit('Part Drag UI function block missing')
new_ui = r'''function updatePartDragUI(){
  const moveBtn=$('partDragBtn');
  const rotateBtn=$('partRotateBtn');
  const scaleBtn=$('partScaleBtn');
  if(moveBtn) moveBtn.classList.toggle('active',partDragEnabled);
  if(rotateBtn) rotateBtn.classList.toggle('active',partRotateEnabled);
  if(scaleBtn) scaleBtn.classList.toggle('active',partScaleEnabled);
  const active=partDragEnabled||partRotateEnabled||partScaleEnabled;
  const badge=$('partDragBadge');
  if(badge) badge.classList.toggle('on',active);
  const badgeText=$('partTransformBadgeText');
  if(badgeText){
    badgeText.textContent=partRotateEnabled?'PART ROTATE • drag ↔ Y / ↕ X':partScaleEnabled?'PART SCALE • drag ↑ bigger / ↓ smaller':'PART DRAG • touch a part and drag';
  }
  const moveMeshBtn=$('meshLayersDragBtn');
  const rotateMeshBtn=$('meshLayersRotateBtn');
  const scaleMeshBtn=$('meshLayersScaleBtn');
  if(moveMeshBtn) moveMeshBtn.textContent=partDragEnabled?'✓ Part Drag Active':'☝ Part Drag in Preview';
  if(rotateMeshBtn) rotateMeshBtn.textContent=partRotateEnabled?'✓ Part Rotate Active':'⟳ Part Rotate';
  if(scaleMeshBtn) scaleMeshBtn.textContent=partScaleEnabled?'✓ Part Scale Active':'⤢ Part Scale';
}
function disableOtherPartModes(except){
  if(except!=='move') partDragEnabled=false;
  if(except!=='rotate') partRotateEnabled=false;
  if(except!=='scale') partScaleEnabled=false;
}
'''
s = s[:start] + new_ui + s[end+2:]

# Make enabling Move automatically turn off Rotate/Scale.
move_enable_marker = '''function setPartDragEnabled(on){\n  partDragEnabled=!!on;'''
move_enable_repl = '''function setPartDragEnabled(on){\n  if(on) disableOtherPartModes('move');\n  partDragEnabled=!!on;'''
if move_enable_marker not in s:
    raise SystemExit('setPartDragEnabled marker missing')
s = s.replace(move_enable_marker, move_enable_repl, 1)

# Insert Rotate/Scale touch behavior before the reset-position function.
reset_marker = 'function resetSelectedPartPosition(){'
rotate_scale_code = r'''function rememberPartRotateOriginal(mesh){
  if(!mesh.userData.__partRotateOriginal){
    mesh.userData.__partRotateOriginal={x:mesh.rotation.x,y:mesh.rotation.y,z:mesh.rotation.z,order:mesh.rotation.order};
  }
}
function rememberPartScaleOriginal(mesh){
  if(!mesh.userData.__partScaleOriginal){
    mesh.userData.__partScaleOriginal={x:mesh.scale.x,y:mesh.scale.y,z:mesh.scale.z};
  }
}
function setPartRotateEnabled(on){
  if(on) disableOtherPartModes('rotate');
  partRotateEnabled=!!on;
  finishPartTransform();
  updatePartDragUI();
  if(partRotateEnabled){ go('editorScreen'); msg('Part Rotate ON — drag horizontal/vertikal'); }
  else msg('Part Rotate OFF');
}
function setPartScaleEnabled(on){
  if(on) disableOtherPartModes('scale');
  partScaleEnabled=!!on;
  finishPartTransform();
  updatePartDragUI();
  if(partScaleEnabled){ go('editorScreen'); msg('Part Scale ON — drag atas/bawah'); }
  else msg('Part Scale OFF');
}
function beginPartTransform(ev){
  if((!partRotateEnabled && !partScaleEnabled) || !meshList.length || ev.button>0) return;
  if(!setPartDragPointer(ev)) return;
  const hits=partDragRaycaster.intersectObjects(meshList.filter(m=>m.visible),false);
  if(!hits.length)return;
  const mesh=hits[0].object;
  const index=meshList.indexOf(mesh);
  if(index<0)return;
  selectMeshLayer(index);
  showPartDragSelection(mesh);
  partDragMesh=mesh;
  partDragPointerId=ev.pointerId;
  partTransformStartX=ev.clientX;
  partTransformStartY=ev.clientY;
  if(partRotateEnabled){
    rememberPartRotateOriginal(mesh);
    partRotateStart=mesh.rotation.clone();
  }
  if(partScaleEnabled){
    rememberPartScaleOriginal(mesh);
    partScaleStart=mesh.scale.clone();
  }
  controls.enabled=false;
  try{canvas.setPointerCapture(ev.pointerId)}catch(_){ }
  ev.preventDefault();
  ev.stopPropagation();
}
function movePartTransform(ev){
  if(!partDragMesh || ev.pointerId!==partDragPointerId || (!partRotateEnabled && !partScaleEnabled))return;
  const dx=ev.clientX-partTransformStartX;
  const dy=ev.clientY-partTransformStartY;
  if(partRotateEnabled && partRotateStart){
    // Screen-space gesture: horizontal rotates around local Y, vertical around local X.
    partDragMesh.rotation.set(
      partRotateStart.x + dy*0.012,
      partRotateStart.y + dx*0.012,
      partRotateStart.z,
      partRotateStart.order
    );
  }else if(partScaleEnabled && partScaleStart){
    // Exponential scaling feels predictable on both small and large meshes.
    const factor=Math.max(0.05,Math.min(20,Math.exp(-dy*0.008)));
    partDragMesh.scale.set(
      partScaleStart.x*factor,
      partScaleStart.y*factor,
      partScaleStart.z*factor
    );
  }
  partDragMesh.updateMatrixWorld(true);
  if(partDragHelper) partDragHelper.update();
  ev.preventDefault();
  ev.stopPropagation();
}
function finishPartTransform(ev){
  if(ev && partDragPointerId!==null && ev.pointerId!==partDragPointerId)return;
  if((partRotateEnabled||partScaleEnabled) && partDragPointerId!==null){
    try{canvas.releasePointerCapture(partDragPointerId)}catch(_){ }
    partDragPointerId=null;
    partDragMesh=null;
    partRotateStart=null;
    partScaleStart=null;
    controls.enabled=true;
  }
}
function resetSelectedPartRotation(){
  const mesh=meshList[activeMeshLayerIndex];
  if(!mesh){msg('Pilih satu mesh dulu');return}
  const r=mesh.userData.__partRotateOriginal;
  if(!r){msg('Mesh ini belum pernah diputar');return}
  mesh.rotation.set(r.x,r.y,r.z,r.order||mesh.rotation.order);
  mesh.updateMatrixWorld(true);
  if(partDragHelper) partDragHelper.update();
  msg('Rotasi part dikembalikan');
}
function resetSelectedPartScale(){
  const mesh=meshList[activeMeshLayerIndex];
  if(!mesh){msg('Pilih satu mesh dulu');return}
  const sc=mesh.userData.__partScaleOriginal;
  if(!sc){msg('Mesh ini belum pernah di-scale');return}
  mesh.scale.set(sc.x,sc.y,sc.z);
  mesh.updateMatrixWorld(true);
  if(partDragHelper) partDragHelper.update();
  msg('Scale part dikembalikan');
}

'''
if reset_marker not in s:
    raise SystemExit('resetSelectedPartPosition marker missing')
s = s.replace(reset_marker, rotate_scale_code + reset_marker, 1)

# Bind UI and capture-phase pointer handlers. Existing move handlers remain unchanged.
handler_marker = "$('partDragBtn').addEventListener('click',()=>setPartDragEnabled(!partDragEnabled));"
handler_repl = r'''$('partRotateBtn').addEventListener('click',()=>setPartRotateEnabled(!partRotateEnabled));
$('partScaleBtn').addEventListener('click',()=>setPartScaleEnabled(!partScaleEnabled));
$('meshLayersRotateBtn').addEventListener('click',()=>setPartRotateEnabled(!partRotateEnabled));
$('meshLayersScaleBtn').addEventListener('click',()=>setPartScaleEnabled(!partScaleEnabled));
$('meshLayersResetRotBtn').addEventListener('click',resetSelectedPartRotation);
$('meshLayersResetScaleBtn').addEventListener('click',resetSelectedPartScale);
canvas.addEventListener('pointerdown',beginPartTransform,{capture:true});
canvas.addEventListener('pointermove',movePartTransform,{capture:true});
canvas.addEventListener('pointerup',finishPartTransform,{capture:true});
canvas.addEventListener('pointercancel',finishPartTransform,{capture:true});
$('partDragBtn').addEventListener('click',()=>setPartDragEnabled(!partDragEnabled));'''
if handler_marker not in s:
    raise SystemExit('Part Drag handler marker missing')
s = s.replace(handler_marker, handler_repl, 1)

p.write_text(s, encoding='utf-8')
print('Part Rotate/Scale patch applied')
