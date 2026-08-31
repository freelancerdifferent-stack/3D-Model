from pathlib import Path

html_path=Path('app/src/main/assets/index.html')
java_path=Path('app/src/main/java/com/differentfreelancer/model3d/MainActivity.java')
s=html_path.read_text(encoding='utf-8')
j=java_path.read_text(encoding='utf-8')

if 'PROJECT_IMPORT_V18' not in s:
    css=r'''
/* PROJECT_IMPORT_V18 */
#projectsScreen .project-import-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
#projectsScreen .project-import-btn{height:44px;border:1px solid #4c9cff;border-radius:9px;background:#11243a;color:#79b4ff;font-weight:700}
#projectsScreen .project-import-hint{margin-top:8px;font-size:11px;color:var(--muted);line-height:1.4}
'''
    s=s.replace('</style>',css+'\n</style>',1)

    marker='<div class="project-current" id="projectCurrentLabel">Belum ada project aktif. Save pertama akan membuat satu slot project.</div>'
    if marker not in s:
        raise SystemExit('project current marker missing')
    ui=marker+r'''
      <!-- PROJECT_IMPORT_V18 -->
      <input id="projectImportInput" type="file" accept=".json,.df3dproject,application/json" class="hidden">
      <div class="project-import-row">
        <button type="button" class="project-import-btn" id="projectImportBtn">📂 Import Project</button>
        <button type="button" class="project-import-btn" id="projectOpenFolderBtn">📁 Choose Folder</button>
      </div>
      <div class="project-import-hint">Import project.json yang dibuat oleh Save Project. Model, Layers, texture, camera, dan state project akan dipulihkan dari file tersebut.</div>'''
    s=s.replace(marker,ui,1)

    anchor='function projectDateText(ts){'
    if anchor not in s:
        raise SystemExit('projectDateText marker missing')
    code=r'''
// PROJECT_IMPORT_V18
function base64ToArrayBufferProject(b64){
  const binary=atob(b64||'');
  const bytes=new Uint8Array(binary.length);
  for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
  return bytes.buffer;
}
function normalizeImportedProjectRecord(raw){
  if(!raw||typeof raw!=='object')throw new Error('File project tidak valid');
  if(!Array.isArray(raw.layers))throw new Error('Project tidak memiliki Layers');
  const record={...raw};
  record.id=record.id||newProjectId();
  record.name=(record.name||'Imported Project').toString();
  record.createdAt=Number(record.createdAt)||Date.now();
  record.updatedAt=Date.now();
  record.layers=raw.layers.map(layer=>{
    const copy={...layer};
    if(copy.kind==='model'){
      if(copy.dataBase64 && !copy.data) copy.data=base64ToArrayBufferProject(copy.dataBase64);
      if(Array.isArray(copy.data)) copy.data=new Uint8Array(copy.data).buffer;
      if(!(copy.data instanceof ArrayBuffer))throw new Error('Data model project tidak lengkap: '+(copy.name||'Model'));
    }
    return copy;
  });
  return record;
}
async function importProjectFile(file){
  if(!file)return;
  const status=$('projectCurrentLabel');
  if(status)status.textContent='Mengimport project…';
  try{
    const text=await file.text();
    const raw=JSON.parse(text);
    const record=normalizeImportedProjectRecord(raw);
    await projectDbPut(record);
    currentProjectId=record.id;
    currentSafProjectName=record.name||'';
    if($('projectNameInput'))$('projectNameInput').value=record.name||'Project';
    await renderProjectList();
    await openSavedProject(record.id);
    msg('Project berhasil diimport');
  }catch(e){
    console.error(e);
    if(status)status.textContent='Import project gagal: '+(e?.message||e);
    msg('Import project gagal: '+(e?.message||e));
  }
}

'''
    s=s.replace(anchor,code+anchor,1)

    handler_anchor="$('projectsHomeBtn').addEventListener('click',()=>{"
    if handler_anchor not in s:
        # fallback before openProjectsScreen definition use final script insertion
        end=s.rfind('</script>')
        if end<0: raise SystemExit('script end missing')
        handlers=r'''
(function(){
 const b=$('projectImportBtn'),inp=$('projectImportInput'),folder=$('projectOpenFolderBtn');
 if(b&&inp){b.onclick=()=>inp.click();inp.onchange=async()=>{const f=inp.files?.[0];await importProjectFile(f);inp.value='';};}
 if(folder)folder.onclick=()=>{if(typeof chooseProjectFolderSaf==='function')chooseProjectFolderSaf();else msg('Folder project hanya tersedia di Android');};
})();
'''
        s=s[:end]+handlers+'\n'+s[end:]
    else:
        handlers=r'''$('projectImportBtn').onclick=()=>$('projectImportInput').click();
$('projectImportInput').onchange=async()=>{const f=$('projectImportInput').files?.[0];await importProjectFile(f);$('projectImportInput').value=''};
$('projectOpenFolderBtn').onclick=()=>{if(typeof chooseProjectFolderSaf==='function')chooseProjectFolderSaf();else msg('Folder project hanya tersedia di Android')};
'''
        s=s.replace(handler_anchor,handlers+'\n'+handler_anchor,1)

    html_path.write_text(s,encoding='utf-8')

if 'PROJECT_IMPORT_JSON_MIME_V18' not in j:
    old='new String[]{"model/gltf-binary","model/gltf+json","application/octet-stream","application/x-fbx","application/vnd.autodesk.fbx","image/png"}'
    new='new String[]{"model/gltf-binary","model/gltf+json","application/octet-stream","application/x-fbx","application/vnd.autodesk.fbx","image/png","application/json","text/json","text/plain"} /* PROJECT_IMPORT_JSON_MIME_V18 */'
    if old not in j:
        raise SystemExit('Android MIME marker missing')
    j=j.replace(old,new,1)
    java_path.write_text(j,encoding='utf-8')

print('Project Import v18 applied')
