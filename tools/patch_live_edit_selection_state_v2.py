from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

if 'LIVE_EDIT_SELECTION_STATE_V2' in s:
    print('Live Edit selection state v2 already applied'); raise SystemExit(0)

# The original Live Edit picker set activeMeshLayerIndex, then called updateMeshSelect().
# Mesh Layers patches rebuild that dropdown and reset activeMeshLayerIndex to -1,
# so Move/Rotate/Scale immediately thought no part was selected.
old="""  activeMeshLayerIndex=index;\n  if(typeof showStrongPartSelection==='function')showStrongPartSelection(mesh);\n  else if(typeof showPartDragSelection==='function')showPartDragSelection(mesh);\n  if(typeof renderMeshLayers==='function')renderMeshLayers();\n  if(typeof updateMeshSelect==='function')updateMeshSelect();"""
new="""  // LIVE_EDIT_SELECTION_STATE_V2\n  // selectMeshLayer() is the single source of truth for the active mesh.\n  // Do NOT call updateMeshSelect() here because it rebuilds the dropdown and\n  // refreshMeshLayersAfterModelChange() clears activeMeshLayerIndex.\n  if(typeof selectMeshLayer==='function')selectMeshLayer(index);\n  else {\n    activeMeshLayerIndex=index;\n    const target=$('targetMesh'); if(target)target.value=String(index);\n    if(typeof renderMeshLayers==='function')renderMeshLayers();\n  }\n  if(typeof showStrongPartSelection==='function')showStrongPartSelection(mesh);\n  else if(typeof showPartDragSelection==='function')showPartDragSelection(mesh);"""
if old not in s:
    raise SystemExit('Live Edit pick state block missing')
s=s.replace(old,new,1)

# Strengthen transform-mode lookup: use activeMeshLayerIndex directly first so the
# selected part survives regardless of helper implementation details.
old="""  const mesh=(typeof activePartMesh==='function')?activePartMesh():null;\n  if(!mesh){msg('Pilih part dulu dengan Select');return}"""
new="""  const mesh=(activeMeshLayerIndex>=0 && meshList[activeMeshLayerIndex])\n    ? meshList[activeMeshLayerIndex]\n    : ((typeof activePartMesh==='function')?activePartMesh():null);\n  if(!mesh){msg('Pilih part dulu dengan Select');return}"""
if old not in s:
    raise SystemExit('Live Edit transform target block missing')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('Fixed Live Edit selected-part persistence')
