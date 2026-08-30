from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'chooseProjectFolderSaf' in s:
    print('SAF project folder patch already applied')
    raise SystemExit(0)
marker="$('projectSaveBtn').addEventListener('click',saveCurrentProject);"
if marker not in s: raise SystemExit('Project save handler marker missing')
code=r'''function androidProjectFolderAvailable(){
  return !!(window.Android && typeof Android.chooseProjectFolder==='function' && typeof Android.saveProjectFile==='function');
}
function chooseProjectFolderSaf(){
  if(!androidProjectFolderAvailable()){msg('Folder project hanya tersedia di aplikasi Android');return}
  Android.chooseProjectFolder();
}
window.onProjectFolderChosen=function(name){
  msg('Folder project: '+(name||'dipilih'));
  const b=$('projectFolderBtn'); if(b)b.textContent='📁 '+(name||'Project Folder');
};
window.onProjectFolderError=function(text){msg(text||'Gagal memilih folder project')};
async function saveCurrentProjectToFolder(){
  if(!androidProjectFolderAvailable()){return saveCurrentProject()}
  if(!root){msg('Belum ada model untuk disimpan');return}
  let name=currentProjectName||prompt('Nama project',currentFileName.replace(/\.[^.]+$/,''));
  if(!name?.trim())return;
  name=name.trim(); currentProjectName=name;
  try{
    const data=await serializeProject();
    data.name=name; data.updatedAt=Date.now();
    Android.saveProjectFile(name,JSON.stringify(data));
    updateProjectActiveLabel();
  }catch(e){msg('Save project gagal: '+e.message)}
}
'''
s=s.replace(marker,code+"\n"+marker,1)
# Replace top save behavior: Android uses selected folder; browser keeps IndexedDB fallback.
s=s.replace("$('projectSaveBtn').addEventListener('click',saveCurrentProject);","$('projectSaveBtn').addEventListener('click',saveCurrentProjectToFolder);",1)
# Add folder picker to project manager.
ui_marker='<button class="primary" id="projectNewBtn" style="margin-top:0">＋ Save Current as New Project</button>'
if ui_marker not in s: raise SystemExit('Project manager UI marker missing')
s=s.replace(ui_marker,'<button class="outline" id="projectFolderBtn" style="margin-top:0">📁 Choose Project Folder</button>\n      '+ui_marker,1)
handler="$('projectNewBtn').addEventListener('click',async()=>{currentProjectId=null;currentProjectName='';await saveCurrentProject();renderProjectList()});"
if handler not in s: raise SystemExit('Project new handler missing')
s=s.replace(handler,"$('projectFolderBtn').addEventListener('click',chooseProjectFolderSaf);\n"+handler.replace('await saveCurrentProject()','await saveCurrentProjectToFolder()'),1)
p.write_text(s,encoding='utf-8')
print('SAF project folder patch applied')
