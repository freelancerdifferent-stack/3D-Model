from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

if 'MESH_PART_LOCK_V2' in s:
    print('Mesh Part Lock v2 already applied')
    raise SystemExit(0)

marker='// MESH_PART_LOCK_V1'
if marker not in s:
    raise SystemExit('Mesh Part Lock v1 marker missing')

# Add a hard guard layer after all part-edit features have been installed.
insert_marker='function isMeshPartLocked(mesh){'
if insert_marker not in s:
    raise SystemExit('isMeshPartLocked missing')

hard_guard=r'''// MESH_PART_LOCK_V2
function lockedPartGuard(mesh,action){
  if(!isMeshPartLocked(mesh)) return false;
  try{finishPartDrag()}catch(_){ }
  try{finishPartTransform()}catch(_){ }
  try{closePartContextMenu()}catch(_){ }
  partDragEnabled=false;partRotateEnabled=false;partScaleEnabled=false;
  try{updatePartDragUI()}catch(_){ }
  controls.enabled=true;
  msg('🔒 Part dikunci'+(action?' — '+action+' tidak diizinkan':''));
  return true;
}
'''
s=s.replace(insert_marker,hard_guard+'\n'+insert_marker,1)

# Lock button itself must never select/activate the row accidentally.
old="lock.onclick=e=>{e.stopPropagation();toggleMeshPartLock(index)};"
new="lock.onclick=e=>{e.preventDefault();e.stopPropagation();if(e.stopImmediatePropagation)e.stopImmediatePropagation();toggleMeshPartLock(index)};"
if old not in s: raise SystemExit('lock onclick marker missing')
s=s.replace(old,new,1)

# Row/SELECT may still highlight a locked part for visibility, but direct edit entry is blocked.
old="pick.onclick=e=>{e.stopPropagation();selectMeshLayer(index)};"
new="pick.onclick=e=>{e.stopPropagation();selectMeshLayer(index);if(isMeshPartLocked(mesh))msg('🔒 Part dikunci — hanya bisa dilihat')};"
if old in s:s=s.replace(old,new,1)

# Hard block preview long-press picking of locked parts.
old='return hits.length?hits[0]:null;\n}\nfunction showStrongPartSelection(mesh){'
new="return hits.find(h=>!isMeshPartLocked(h.object))||null;\n}\nfunction showStrongPartSelection(mesh){"
if old not in s: raise SystemExit('partPickAt return marker missing')
s=s.replace(old,new,1)

# Guard all transform starts regardless of which earlier patch selected the target.
for fn, action in [('beginPartDrag','Move'),('beginPartTransform','Rotate/Scale')]:
    start=s.find('function '+fn+'(ev){')
    if start<0: raise SystemExit(fn+' missing')
    brace=s.find('\n',start)
    guard=f"\n  const __lockedTarget=activeMeshLayerIndex>=0?meshList[activeMeshLayerIndex]:null;\n  if(__lockedTarget && lockedPartGuard(__lockedTarget,'{action}')) return;"
    s=s[:brace]+guard+s[brace:]

# Guard context-mode choice as well.
needle="  const mesh=activePartMesh();\n  if(!mesh){closePartContextMenu();controls.enabled=true;msg('Part tidak ditemukan');return}"
repl="  const mesh=(activeMeshLayerIndex>=0)?meshList[activeMeshLayerIndex]:null;\n  if(!mesh){closePartContextMenu();controls.enabled=true;msg('Part tidak ditemukan');return}\n  if(lockedPartGuard(mesh,'Edit'))return;"
if needle not in s: raise SystemExit('choosePartContextMode target marker missing')
s=s.replace(needle,repl,1)

# Guard reset operations too: a lock means absolutely no transform editing.
for fn,label in [('resetSelectedPartPosition','Reset Position'),('resetSelectedPartRotation','Reset Rotation'),('resetSelectedPartScale','Reset Scale')]:
    start=s.find('function '+fn+'(){')
    if start<0: continue
    target="  const mesh=meshList[activeMeshLayerIndex];"
    pos=s.find(target,start)
    if pos<0: continue
    end=pos+len(target)
    s=s[:end]+f"\n  if(lockedPartGuard(mesh,'{label}'))return;"+s[end:]

# Material/texture writes: filter locked targets at the final target provider every time.
# Also make the Material screen show a clear locked target state.
needle="function getTargets(){\n  const targets=getTargetsUnlockedSource();\n  return (targets||[]).filter(mesh=>!isMeshPartLocked(mesh));\n}"
repl="function getTargets(){\n  const targets=getTargetsUnlockedSource();\n  const unlocked=(targets||[]).filter(mesh=>!isMeshPartLocked(mesh));\n  if((targets||[]).length && !unlocked.length)msg('🔒 Target dikunci — Material/Texture tidak diubah');\n  return unlocked;\n}"
if needle not in s: raise SystemExit('getTargets lock wrapper missing')
s=s.replace(needle,repl,1)

# Locked parts should look unmistakably locked and SELECT button should reflect that.
needle="pick.textContent=index===activeMeshLayerIndex?'ACTIVE':'SELECT';"
repl="pick.textContent=isMeshPartLocked(mesh)?'LOCKED':(index===activeMeshLayerIndex?'ACTIVE':'SELECT');\n    pick.disabled=isMeshPartLocked(mesh);"
if needle not in s: raise SystemExit('pick text marker missing')
s=s.replace(needle,repl,1)

# When locking currently active part, clear the active transform selection helper.
needle="  if(next){\n    try{finishPartDrag()}catch(_){ }"
repl="  if(next){\n    try{finishPartDrag()}catch(_){ }\n    if(activeMeshLayerIndex===index){try{showPartDragSelection(null)}catch(_){ }}"
if needle not in s: raise SystemExit('toggle lock next marker missing')
s=s.replace(needle,repl,1)

p.write_text(s,encoding='utf-8')
print('Mesh Layer hard lock v2 applied')
