from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

if 'function chooseProjectFolderSaf' in s:
    print('SAF project folder patch already applied')
    raise SystemExit(0)

# The Project Manager currently uses saveProjectBtn/projectQuickSave, not the old projectSaveBtn/projectNewBtn ids.
if 'id="projectsScreen"' not in s or 'id="saveProjectBtn"' not in s:
    raise SystemExit('Current Project Manager UI missing')
if 'async function buildProjectRecord' not in s:
    raise SystemExit('buildProjectRecord marker missing')

# Add a persistent-folder chooser without changing the existing Layers/Mesh Layers UI.
ui_marker='<div class="project-current" id="projectCurrentLabel">Belum ada project aktif. Save pertama akan membuat satu slot project.</div>'
if ui_marker not in s:
    raise SystemExit('Project current label marker missing')
ui_repl=ui_marker+'\n      <button class="outline" id="projectFolderBtn" style="margin-top:8px">📁 Choose Project Folder</button>'
s=s.replace(ui_marker,ui_repl,1)

# Android SAF stores the project record as JSON. Binary GLB ArrayBuffers are encoded as base64 so model data is not lost.
func_marker='async function saveCurrentProject(forceNew=false){'
if func_marker not in s:
    raise SystemExit('saveCurrentProject function marker missing')
code=r'''let currentSafProjectName='';
function androidProjectFolderAvailable(){
  return !!(window.Android && typeof Android.chooseProjectFolder==='function' && typeof Android.saveProjectFile==='function');
}
function chooseProjectFolderSaf(){
  if(!androidProjectFolderAvailable()){msg('Folder project hanya tersedia di aplikasi Android');return}
  Android.chooseProjectFolder();
}
window.onProjectFolderChosen=function(name){
  const b=$('projectFolderBtn');
  if(b)b.textContent='📁 '+(name||'Project Folder Selected');
  msg('Folder project siap digunakan');
};
window.onProjectFolderError=function(text){msg(text||'Gagal memilih folder project')};
function arrayBufferToBase64(buffer){
  const bytes=new Uint8Array(buffer);
  let binary='';
  const chunk=0x8000;
  for(let i=0;i<bytes.length;i+=chunk){
    binary+=String.fromCharCode(...bytes.subarray(i,Math.min(i+chunk,bytes.length)));
  }
  return btoa(binary);
}
function projectRecordForJson(record){
  return {
    ...record,
    storageFormat:'df3d-project-json-v1',
    layers:(record.layers||[]).map(layer=>{
      if(layer.kind==='model' && layer.data instanceof ArrayBuffer){
        return {...layer,dataBase64:arrayBufferToBase64(layer.data),data:undefined};
      }
      return layer;
    })
  };
}
async function saveCurrentProjectToFolder(forceNew=false){
  if(!androidProjectFolderAvailable()) return saveCurrentProject(forceNew);
  if(!sceneLayers.length){msg('Belum ada model untuk disimpan');return}
  const input=$('projectNameInput');
  let name=(input?.value||currentSafProjectName||'').trim();
  if(!name)name=defaultProjectName();
  if(input)input.value=name;
  const btn=$('saveProjectBtn');
  if(btn){btn.disabled=true;btn.textContent='Saving…'}
  try{
    const record=await buildProjectRecord(name,currentProjectId||newProjectId(),Date.now());
    Android.saveProjectFile(name,JSON.stringify(projectRecordForJson(record)));
    currentSafProjectName=name;
    currentProjectId=record.id;
    const label=$('projectCurrentLabel');
    if(label)label.textContent='Project aktif: '+name+' • Save berikutnya akan memperbarui folder project ini.';
    msg('Menyimpan project ke folder pilihan…');
  }catch(e){
    console.error(e);msg('Save project gagal: '+(e?.message||e));
  }finally{
    if(btn){btn.disabled=false;btn.textContent='💾 Save'}
  }
}

'''
s=s.replace(func_marker,code+func_marker,1)

# Route Save controls to SAF on Android; retain IndexedDB as browser fallback only.
old_save="$('saveProjectBtn').addEventListener('click',()=>saveCurrentProject(false));"
if old_save not in s:
    raise SystemExit('saveProjectBtn handler marker missing')
s=s.replace(old_save,"$('saveProjectBtn').addEventListener('click',()=>saveCurrentProjectToFolder(false));\n$('projectFolderBtn').addEventListener('click',chooseProjectFolderSaf);",1)

old_quick="""$('projectQuickSave').onclick=()=>{\n  if(currentProjectId) saveCurrentProject(false);\n  else openProjectsScreen();\n};"""
if old_quick not in s:
    raise SystemExit('projectQuickSave handler marker missing')
new_quick="""$('projectQuickSave').onclick=()=>{\n  if(androidProjectFolderAvailable() && (currentProjectId||currentSafProjectName)) saveCurrentProjectToFolder(false);\n  else if(currentProjectId) saveCurrentProject(false);\n  else openProjectsScreen();\n};"""
s=s.replace(old_quick,new_quick,1)

# Correct the description shown in Android-capable builds.
old_status='Project disimpan di dalam aplikasi. Menekan Save lagi akan memperbarui slot yang sama, bukan membuat file baru di Downloads.'
new_status='Pilih folder project sekali. Save berikutnya memperbarui project yang sama di folder pilihan, bukan membuat file baru di Downloads.'
s=s.replace(old_status,new_status,1)

p.write_text(s,encoding='utf-8')
print('SAF project folder patch applied')
