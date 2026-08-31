from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

if 'PROJECT_EXPORT_V19' in s:
    print('Project Export v19 already applied')
    raise SystemExit(0)

css=r'''
/* PROJECT_EXPORT_V19 */
#projectsScreen .project-import-row{grid-template-columns:repeat(3,minmax(0,1fr))}
#projectsScreen .project-export-btn{height:44px;border:1px solid #4c9cff;border-radius:9px;background:#17304c;color:#8fc0ff;font-weight:700}
'''
s=s.replace('</style>',css+'\n</style>',1)

marker='<button type="button" class="project-import-btn" id="projectImportBtn">📂 Import Project</button>\n        <button type="button" class="project-import-btn" id="projectOpenFolderBtn">📁 Choose Folder</button>'
if marker not in s:
    raise SystemExit('Import Project button marker missing')
repl='<button type="button" class="project-import-btn" id="projectImportBtn">📂 Import Project</button>\n        <button type="button" class="project-export-btn" id="projectExportBtn">📦 Export Project</button>\n        <button type="button" class="project-import-btn" id="projectOpenFolderBtn">📁 Choose Folder</button>'
s=s.replace(marker,repl,1)

anchor='function base64ToArrayBufferProject(b64){'
if anchor not in s:
    raise SystemExit('Project import anchor missing')
code=r'''
// PROJECT_EXPORT_V19
function safeProjectExportName(name){
  return (name||'Project').toString().trim().replace(/[\\/:*?"<>|]+/g,'_')||'Project';
}
function utf8ToBase64Project(text){
  const bytes=new TextEncoder().encode(text);
  let binary='';
  const chunk=0x8000;
  for(let i=0;i<bytes.length;i+=chunk){
    binary+=String.fromCharCode(...bytes.subarray(i,Math.min(i+chunk,bytes.length)));
  }
  return btoa(binary);
}
async function exportCurrentProjectPackage(){
  if(!sceneLayers.length){msg('Belum ada project/model untuk diexport');return}
  const btn=$('projectExportBtn');
  if(btn){btn.disabled=true;btn.textContent='Exporting…'}
  try{
    const input=$('projectNameInput');
    let name=(input?.value||currentSafProjectName||'').trim();
    if(!name)name=defaultProjectName();
    if(input)input.value=name;
    const id=currentProjectId||newProjectId();
    const record=await buildProjectRecord(name,id,Date.now());
    const portable=projectRecordForJson(record);
    portable.storageFormat='df3dproject-json-v1';
    portable.exportedAt=Date.now();
    portable.app='3D Viewer & Editor';
    const json=JSON.stringify(portable);
    const filename=safeProjectExportName(name)+'.df3dproject';
    if(window.Android&&typeof Android.saveBase64File==='function'){
      Android.saveBase64File(utf8ToBase64Project(json),filename,'application/json');
    }else{
      const blob=new Blob([json],{type:'application/json'});
      const url=URL.createObjectURL(blob);
      const a=document.createElement('a');a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);
    }
    msg('Export Project dibuat: '+filename);
  }catch(e){
    console.error(e);msg('Export Project gagal: '+(e?.message||e));
  }finally{
    if(btn){btn.disabled=false;btn.textContent='📦 Export Project'}
  }
}

'''
s=s.replace(anchor,code+anchor,1)

end=s.rfind('</script>')
if end<0: raise SystemExit('script end missing')
handlers=r'''
(function(){
 const b=$('projectExportBtn');
 if(b)b.onclick=()=>exportCurrentProjectPackage();
})();
'''
s=s[:end]+handlers+'\n'+s[end:]

hint='Import project.json yang dibuat oleh Save Project. Model, Layers, texture, camera, dan state project akan dipulihkan dari file tersebut.'
new_hint='Import menerima project.json atau .df3dproject. Export Project membuat satu file portable yang berisi model, Layers, texture, camera, dan state project.'
s=s.replace(hint,new_hint,1)

p.write_text(s,encoding='utf-8')
print('Project Export v19 applied')
