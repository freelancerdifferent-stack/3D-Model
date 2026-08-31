from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

if 'MESH_PART_LOCK_V1' in s:
    print('Mesh Part Lock patch already applied')
    raise SystemExit(0)

# Visual lock state inside the independent Mesh Layers screen.
css_marker='.mesh-layer-select{height:34px;border:1px solid #34506f;border-radius:8px;background:#14263b;color:#79b5ff;font-size:11px}'
if css_marker not in s:
    raise SystemExit('Mesh Layers select CSS marker missing')
css=r'''
/* MESH_PART_LOCK_V1 */
.mesh-layer-item{grid-template-columns:38px minmax(0,1fr) 46px 58px}
.mesh-layer-item.locked{border-color:#8a6d33;background:#211d14}
.mesh-layer-lock{height:34px;width:46px;border:1px solid #3a4654;border-radius:8px;background:#0d151f;color:#aab7c6;font-size:15px}
.mesh-layer-lock.on{border-color:#d6a84a;background:#3a2c12;color:#ffd778}
.mesh-layer-item.locked .mesh-layer-select{opacity:.62}
'''
s=s.replace(css_marker,css_marker+css,1)

# Helpers are inserted before Mesh Layers rendering so the renderer can use them.
marker='function meshLayerDisplayName(mesh,index){'
if marker not in s:
    raise SystemExit('Mesh Layers display helper marker missing')
helpers=r'''// MESH_PART_LOCK_V1
function isMeshPartLocked(mesh){
  return !!(mesh && mesh.userData && mesh.userData.__meshPartLocked);
}
function setMeshPartLocked(mesh,on){
  if(!mesh)return;
  mesh.userData=mesh.userData||{};
  mesh.userData.__meshPartLocked=!!on;
}
function toggleMeshPartLock(index){
  const mesh=meshList[index];if(!mesh)return;
  const next=!isMeshPartLocked(mesh);
  setMeshPartLocked(mesh,next);
  if(next){
    try{finishPartDrag()}catch(_){ }
    try{finishPartTransform()}catch(_){ }
    if(typeof setExclusivePartMode==='function')setExclusivePartMode('move',false);
    if(typeof closePartContextMenu==='function')closePartContextMenu();
    msg('Part dikunci — transform dan Material/Texture dinonaktifkan');
  }else{
    msg('Part dibuka — editing aktif kembali');
  }
  renderMeshLayers();
}

'''
s=s.replace(marker,helpers+marker,1)

# Add lock state and button to every Mesh Layer row.
row_marker="    row.className='mesh-layer-item'+(index===activeMeshLayerIndex?' active':'');"
row_repl="    row.className='mesh-layer-item'+(index===activeMeshLayerIndex?' active':'')+(isMeshPartLocked(mesh)?' locked':'');"
if row_marker not in s:
    raise SystemExit('Mesh Layer row marker missing')
s=s.replace(row_marker,row_repl,1)

pick_marker="    const pick=document.createElement('button');\n    pick.className='mesh-layer-select';"
lock_block=r'''    const lock=document.createElement('button');
    lock.className='mesh-layer-lock'+(isMeshPartLocked(mesh)?' on':'');
    lock.textContent=isMeshPartLocked(mesh)?'🔒':'🔓';
    lock.title=isMeshPartLocked(mesh)?'Unlock part':'Lock part';
    lock.onclick=e=>{e.stopPropagation();toggleMeshPartLock(index)};
    const pick=document.createElement('button');
    pick.className='mesh-layer-select';'''
if pick_marker not in s:
    raise SystemExit('Mesh Layer SELECT marker missing')
s=s.replace(pick_marker,lock_block,1)

append_marker='    row.append(eye,main,pick);'
if append_marker not in s:
    raise SystemExit('Mesh Layer append marker missing')
s=s.replace(append_marker,'    row.append(eye,main,lock,pick);',1)

# Locked parts are never eligible for preview transform picking.
visible_marker='return meshList.filter(m=>m && m.isMesh && m.visible && (!m.parent || m.parent.visible!==false));'
if visible_marker not in s:
    raise SystemExit('Part visible mesh marker missing')
s=s.replace(visible_marker,"return meshList.filter(m=>m && m.isMesh && m.visible && !isMeshPartLocked(m) && (!m.parent || m.parent.visible!==false));",1)

# A locked selected mesh cannot become an active transform target through fallback targeting.
active_marker="  return (m && m.isMesh && m.visible)?m:null;"
if active_marker not in s:
    raise SystemExit('activePartMesh marker missing')
s=s.replace(active_marker,"  return (m && m.isMesh && m.visible && !isMeshPartLocked(m))?m:null;",1)

# Guard the long-press popup too, including models where another code path supplies a mesh directly.
context_marker='function openPartContextMenu(mesh,clientX,clientY){\n  const index=meshList.indexOf(mesh);if(index<0)return;'
context_repl="function openPartContextMenu(mesh,clientX,clientY){\n  const index=meshList.indexOf(mesh);if(index<0)return;\n  if(isMeshPartLocked(mesh)){msg('Part ini dikunci');return;}"
if context_marker not in s:
    raise SystemExit('Long-press context marker missing')
s=s.replace(context_marker,context_repl,1)

# Prevent Material/Texture writes to locked meshes. Bulk/all-target edits automatically skip locked parts.
get_targets_hook="function getTargets(){"
if get_targets_hook not in s:
    raise SystemExit('getTargets marker missing')
# Rename the original and install a filtered wrapper immediately after the function block by locating its compact body.
# Base editor uses a short getTargets helper ending before the next function declaration.
start=s.find(get_targets_hook)
end=s.find('\nfunction ',start+len(get_targets_hook))
if start<0 or end<0:
    raise SystemExit('getTargets function block end missing')
original=s[start:end]
renamed=original.replace('function getTargets(){','function getTargetsUnlockedSource(){',1)
wrapper=renamed+r'''
function getTargets(){
  const targets=getTargetsUnlockedSource();
  return (targets||[]).filter(mesh=>!isMeshPartLocked(mesh));
}
'''
s=s[:start]+wrapper+s[end:]

# Direct button guard gives immediate feedback instead of letting the user enter Material screen for a locked part.
edit_handler="$('meshLayersEditBtn').onclick=()=>{\n  if(activeMeshLayerIndex<0 || !meshList[activeMeshLayerIndex]){msg('Pilih satu mesh dulu');return}"
edit_repl="$('meshLayersEditBtn').onclick=()=>{\n  if(activeMeshLayerIndex<0 || !meshList[activeMeshLayerIndex]){msg('Pilih satu mesh dulu');return}\n  if(isMeshPartLocked(meshList[activeMeshLayerIndex])){msg('Part ini dikunci — buka Lock untuk edit Material/Texture');return}"
if edit_handler not in s:
    raise SystemExit('Mesh Layers edit handler marker missing')
s=s.replace(edit_handler,edit_repl,1)

p.write_text(s,encoding='utf-8')
print('Mesh Layer part lock applied')
