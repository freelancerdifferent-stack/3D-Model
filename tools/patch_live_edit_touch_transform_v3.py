from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_TOUCH_TRANSFORM_V3' in s:
    print('Live Edit touch transform v3 already applied'); raise SystemExit(0)

# Persist the selected mesh independently from dropdown/list refreshes.
state='let liveEditSelectMode=false;\nlet liveEditTransformMode=null; // LIVE_EDIT_TRANSFORM_V1'
if state not in s: raise SystemExit('Live Edit state marker missing')
s=s.replace(state,"let liveEditSelectMode=false;\nlet liveEditSelectedMeshRef=null; // LIVE_EDIT_TOUCH_TRANSFORM_V3\nlet liveEditTransformMode=null; // LIVE_EDIT_TRANSFORM_V1",1)

# Store the exact object reference every time Select picks a part.
needle="  if(typeof selectMeshLayer==='function')selectMeshLayer(index);"
if needle not in s: raise SystemExit('selection state marker missing')
s=s.replace(needle,"  liveEditSelectedMeshRef=mesh;\n  if(typeof selectMeshLayer==='function')selectMeshLayer(index);",1)

# Dedicated gesture path must use the persistent object reference first, not UI index state.
old="""function liveV2ActiveMesh(){
  const mesh=(activeMeshLayerIndex>=0)?meshList[activeMeshLayerIndex]:null;
  if(!mesh || !mesh.isMesh || !mesh.visible)return null;
  if(typeof isMeshPartLocked==='function' && isMeshPartLocked(mesh))return null;
  return mesh;
}"""
new="""function liveV2ActiveMesh(){
  // LIVE_EDIT_TOUCH_TRANSFORM_V3: selection survives Mesh Layers/dropdown refreshes.
  let mesh=liveEditSelectedMeshRef;
  if(!mesh && activeMeshLayerIndex>=0)mesh=meshList[activeMeshLayerIndex];
  if(!mesh || !mesh.isMesh || !mesh.visible)return null;
  if(typeof isMeshPartLocked==='function' && isMeshPartLocked(mesh))return null;
  return mesh;
}"""
if old not in s: raise SystemExit('liveV2ActiveMesh block missing')
s=s.replace(old,new,1)

# Tool activation also uses the persistent selected object directly.
old="""  const mesh=(activeMeshLayerIndex>=0 && meshList[activeMeshLayerIndex])
    ? meshList[activeMeshLayerIndex]
    : ((typeof activePartMesh==='function')?activePartMesh():null);
  if(!mesh){msg('Pilih part dulu dengan Select');return}"""
new="""  const mesh=liveEditSelectedMeshRef || ((activeMeshLayerIndex>=0 && meshList[activeMeshLayerIndex])
    ? meshList[activeMeshLayerIndex]
    : ((typeof activePartMesh==='function')?activePartMesh():null));
  if(!mesh){msg('Pilih part dulu dengan Select');return}"""
if old not in s: raise SystemExit('tool target block missing')
s=s.replace(old,new,1)

# Keep the selected object highlighted when a transform mode is chosen and make
# the whole canvas a drag surface. No raycast is required after selection.
needle="  liveEditTransformMode=mode;\n  if(typeof setPartTransformAxis==='function')setPartTransformAxis('free');"
if needle not in s: raise SystemExit('transform mode marker missing')
s=s.replace(needle,"  liveEditSelectedMeshRef=mesh;\n  liveEditTransformMode=mode;\n  if(typeof setPartTransformAxis==='function')setPartTransformAxis('free');",1)

# When Live Edit exits, clear selection only after all gestures are stopped and
# explicitly restore OrbitControls. Entering Live Edit keeps the old selected
# mesh only if it still belongs to the current meshList.
needle="function setLiveEditSelectMode(on){\n  liveEditSelectMode=!!on;\n  liveEditTransformMode=null;"
if needle not in s: raise SystemExit('setLiveEditSelectMode v1 marker missing')
s=s.replace(needle,"function setLiveEditSelectMode(on){\n  liveEditSelectMode=!!on;\n  liveEditTransformMode=null;\n  if(!liveEditSelectMode){liveEditSelectedMeshRef=null;}\n  else if(liveEditSelectedMeshRef && !meshList.includes(liveEditSelectedMeshRef)){liveEditSelectedMeshRef=null;}",1)

# Improve message so device testing is unambiguous.
s=s.replace("+' aktif — drag langsung part yang terseleksi');","+' aktif — drag di mana saja pada preview untuk mengedit part terseleksi');",1)

# Add a small mode badge under LIVE EDIT so it is obvious which direct-touch mode owns the canvas.
css_marker='.live-edit-badge.on{display:block}'
if css_marker not in s: raise SystemExit('Live Edit badge css marker missing')
s=s.replace(css_marker,css_marker+"\n.live-edit-badge[data-mode=move]::after{content:' • MOVE'}.live-edit-badge[data-mode=rotate]::after{content:' • ROTATE'}.live-edit-badge[data-mode=scale]::after{content:' • SCALE'}",1)

# Update the badge whenever toolbar mode changes.
needle="function updateLiveEditToolUI(){\n  $('liveEditSelectBtn')?.classList.toggle('active',liveEditSelectMode && !liveEditTransformMode);"
if needle not in s: raise SystemExit('tool UI marker missing')
s=s.replace(needle,"function updateLiveEditToolUI(){\n  const badge=$('liveEditBadge');\n  if(badge){ if(liveEditTransformMode)badge.dataset.mode=liveEditTransformMode; else delete badge.dataset.mode; }\n  $('liveEditSelectBtn')?.classList.toggle('active',liveEditSelectMode && !liveEditTransformMode);",1)

p.write_text(s,encoding='utf-8')
print('Live Edit touch Move/Rotate/Scale now uses persistent selected mesh and whole-preview drag')
