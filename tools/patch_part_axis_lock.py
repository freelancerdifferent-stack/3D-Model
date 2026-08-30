from pathlib import Path

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

if 'id="partAxisOverlay"' in s:
    print('Part Axis Lock patch already applied')
    raise SystemExit(0)

# Axis controls are a new Part Transform feature; existing Layers stays untouched.
css_marker = '.mesh-layer-actions button{margin-top:0}'
css = '''\n.part-axis-panel{display:flex;align-items:center;gap:7px;margin-top:10px;padding:9px;background:#101923;border:1px solid #283544;border-radius:10px}\n.part-axis-panel span{font-size:11px;color:var(--muted);margin-right:auto}\n.part-axis-btn{min-width:42px;height:38px;border:1px solid #34465a;border-radius:8px;background:#121d28;color:#cbd6e2;font-weight:700}\n.part-axis-btn.active{border-color:#4c9cff;background:#1b3c63;color:#8fc0ff}\n.part-axis-overlay{position:absolute;left:72px;top:48px;z-index:6;display:none;align-items:center;gap:5px;padding:5px;background:rgba(13,20,29,.92);border:1px solid #34465a;border-radius:10px}\n.part-axis-overlay.on{display:flex}\n.part-axis-overlay .part-axis-btn{min-width:38px;width:38px;height:34px;font-size:11px;padding:0}\n'''
if css_marker not in s:
    raise SystemExit('Part actions CSS marker missing')
s = s.replace(css_marker, css_marker + css, 1)

# Add axis selector in the preview so it remains reachable while editing a part.
badge_marker = '<div class="part-drag-badge" id="partDragBadge"><span class="part-drag-dot"></span><span id="partTransformBadgeText">PART DRAG • touch a part and drag</span></div>'
axis_overlay = '''<div class="part-axis-overlay" id="partAxisOverlay">\n            <button class="part-axis-btn active" data-part-axis="free">FREE</button>\n            <button class="part-axis-btn" data-part-axis="x">X</button>\n            <button class="part-axis-btn" data-part-axis="y">Y</button>\n            <button class="part-axis-btn" data-part-axis="z">Z</button>\n          </div>'''
if badge_marker not in s:
    raise SystemExit('Part transform badge marker missing')
s = s.replace(badge_marker, badge_marker + '\n          ' + axis_overlay, 1)

# Add the same axis selector to Mesh Layers for discoverability.
actions_marker = '''      <div class="mesh-layer-actions">\n        <button class="outline" id="meshLayersDragBtn">☝ Part Drag in Preview</button>\n        <button class="outline" id="meshLayersResetPosBtn">↶ Reset Position</button>\n        <button class="outline" id="meshLayersRotateBtn">⟳ Part Rotate</button>\n        <button class="outline" id="meshLayersResetRotBtn">↶ Reset Rotation</button>\n        <button class="outline" id="meshLayersScaleBtn">⤢ Part Scale</button>\n        <button class="outline" id="meshLayersResetScaleBtn">↶ Reset Scale</button>\n      </div>'''
axis_panel = '''      <div class="part-axis-panel">\n        <span>Axis Lock</span>\n        <button class="part-axis-btn active" data-part-axis="free">FREE</button>\n        <button class="part-axis-btn" data-part-axis="x">X</button>\n        <button class="part-axis-btn" data-part-axis="y">Y</button>\n        <button class="part-axis-btn" data-part-axis="z">Z</button>\n      </div>\n'''
if actions_marker not in s:
    raise SystemExit('Part transform action block missing')
s = s.replace(actions_marker, axis_panel + actions_marker, 1)

# State is local-axis based. FREE preserves the current gesture behavior.
state_marker = 'let partTransformStartX=0, partTransformStartY=0;'
state_repl = '''let partTransformStartX=0, partTransformStartY=0;\nlet partTransformAxis='free';\nlet partAxisStartPosition=null;'''
if state_marker not in s:
    raise SystemExit('Part transform state marker missing')
s = s.replace(state_marker, state_repl, 1)

# Axis UI synchronization and selection.
ui_marker = 'function updatePartDragUI(){'
axis_funcs = r'''function setPartTransformAxis(axis){
  axis=String(axis||'free').toLowerCase();
  if(!['free','x','y','z'].includes(axis)) axis='free';
  partTransformAxis=axis;
  document.querySelectorAll('[data-part-axis]').forEach(btn=>{
    btn.classList.toggle('active',btn.dataset.partAxis===partTransformAxis);
  });
  const name=partTransformAxis==='free'?'FREE':partTransformAxis.toUpperCase();
  msg('Axis Lock: '+name);
}
function updatePartAxisOverlay(){
  const overlay=$('partAxisOverlay');
  if(overlay) overlay.classList.toggle('on',partDragEnabled||partRotateEnabled||partScaleEnabled);
  document.querySelectorAll('[data-part-axis]').forEach(btn=>{
    btn.classList.toggle('active',btn.dataset.partAxis===partTransformAxis);
  });
}

'''
if ui_marker not in s:
    raise SystemExit('Part UI marker missing')
s = s.replace(ui_marker, axis_funcs + ui_marker, 1)

# Keep overlay visibility synchronized with the existing mode buttons/badge.
ui_tail = "  if(scaleMeshBtn) scaleMeshBtn.textContent=partScaleEnabled?'✓ Part Scale Active':'⤢ Part Scale';\n}"
ui_tail_repl = "  if(scaleMeshBtn) scaleMeshBtn.textContent=partScaleEnabled?'✓ Part Scale Active':'⤢ Part Scale';\n  updatePartAxisOverlay();\n}"
if ui_tail not in s:
    raise SystemExit('Part UI tail marker missing')
s = s.replace(ui_tail, ui_tail_repl, 1)

# Capture the selected mesh local position at the start of Move.
begin_move_marker = '''  partDragMesh=mesh;\n  partDragPointerId=ev.pointerId;\n  mesh.getWorldPosition(partDragStartWorld);'''
begin_move_repl = '''  partDragMesh=mesh;\n  partDragPointerId=ev.pointerId;\n  partAxisStartPosition=mesh.position.clone();\n  mesh.getWorldPosition(partDragStartWorld);'''
if begin_move_marker not in s:
    raise SystemExit('Part Drag begin marker missing')
s = s.replace(begin_move_marker, begin_move_repl, 1)

# After the existing camera-plane drag calculation, freeze non-selected local axes.
move_marker = '''  }else{\n    partDragMesh.position.copy(desiredWorld);\n  }\n  partDragMesh.updateMatrixWorld(true);'''
move_repl = '''  }else{\n    partDragMesh.position.copy(desiredWorld);\n  }\n  if(partTransformAxis!=='free' && partAxisStartPosition){\n    if(partTransformAxis!=='x') partDragMesh.position.x=partAxisStartPosition.x;\n    if(partTransformAxis!=='y') partDragMesh.position.y=partAxisStartPosition.y;\n    if(partTransformAxis!=='z') partDragMesh.position.z=partAxisStartPosition.z;\n  }\n  partDragMesh.updateMatrixWorld(true);'''
if move_marker not in s:
    raise SystemExit('Part Drag movement marker missing')
s = s.replace(move_marker, move_repl, 1)

# Clear transient Move axis state when the gesture ends.
finish_move_marker = '''  partDragPointerId=null;\n  partDragMesh=null;\n  controls.enabled=true;'''
finish_move_repl = '''  partDragPointerId=null;\n  partDragMesh=null;\n  partAxisStartPosition=null;\n  controls.enabled=true;'''
if finish_move_marker not in s:
    raise SystemExit('Part Drag finish marker missing')
s = s.replace(finish_move_marker, finish_move_repl, 1)

# Replace Rotate/Scale gesture math with axis-aware behavior.
transform_block = r'''  if(partRotateEnabled && partRotateStart){
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
  }'''
axis_transform_block = r'''  if(partRotateEnabled && partRotateStart){
    const speed=0.012;
    if(partTransformAxis==='x'){
      partDragMesh.rotation.set(partRotateStart.x+dy*speed,partRotateStart.y,partRotateStart.z,partRotateStart.order);
    }else if(partTransformAxis==='y'){
      partDragMesh.rotation.set(partRotateStart.x,partRotateStart.y+dx*speed,partRotateStart.z,partRotateStart.order);
    }else if(partTransformAxis==='z'){
      partDragMesh.rotation.set(partRotateStart.x,partRotateStart.y,partRotateStart.z+dx*speed,partRotateStart.order);
    }else{
      partDragMesh.rotation.set(partRotateStart.x+dy*speed,partRotateStart.y+dx*speed,partRotateStart.z,partRotateStart.order);
    }
  }else if(partScaleEnabled && partScaleStart){
    const factor=Math.max(0.05,Math.min(20,Math.exp(-dy*0.008)));
    if(partTransformAxis==='x'){
      partDragMesh.scale.set(partScaleStart.x*factor,partScaleStart.y,partScaleStart.z);
    }else if(partTransformAxis==='y'){
      partDragMesh.scale.set(partScaleStart.x,partScaleStart.y*factor,partScaleStart.z);
    }else if(partTransformAxis==='z'){
      partDragMesh.scale.set(partScaleStart.x,partScaleStart.y,partScaleStart.z*factor);
    }else{
      partDragMesh.scale.set(partScaleStart.x*factor,partScaleStart.y*factor,partScaleStart.z*factor);
    }
  }'''
if transform_block not in s:
    raise SystemExit('Rotate/Scale gesture block missing')
s = s.replace(transform_block, axis_transform_block, 1)

# Buttons in both locations control one shared axis state.
handler_marker = "$('partRotateBtn').addEventListener('click',()=>setPartRotateEnabled(!partRotateEnabled));"
handler_repl = r'''document.querySelectorAll('[data-part-axis]').forEach(btn=>{
  btn.addEventListener('click',ev=>{
    ev.preventDefault();
    ev.stopPropagation();
    setPartTransformAxis(btn.dataset.partAxis);
  });
});
$('partRotateBtn').addEventListener('click',()=>setPartRotateEnabled(!partRotateEnabled));'''
if handler_marker not in s:
    raise SystemExit('Part Rotate handler marker missing')
s = s.replace(handler_marker, handler_repl, 1)

p.write_text(s, encoding='utf-8')
print('Part Axis Lock patch applied')
