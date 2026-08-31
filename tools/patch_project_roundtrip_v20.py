from pathlib import Path

html_path=Path('app/src/main/assets/index.html')
java_path=Path('app/src/main/java/com/differentfreelancer/model3d/MainActivity.java')
s=html_path.read_text(encoding='utf-8')
j=java_path.read_text(encoding='utf-8')

if 'PROJECT_ROUNDTRIP_V20' in s and 'PROJECT_CHUNK_WRITER_V20' in j:
    print('Project roundtrip v20 already applied')
    raise SystemExit(0)

# ---------- Android: chunked project writer ----------
if 'PROJECT_CHUNK_WRITER_V20' not in j:
    field_marker='    private String pendingProjectJson;\n'
    if field_marker not in j:
        raise SystemExit('MainActivity pending project field marker missing')
    fields='''    private String pendingProjectJson;\n    // PROJECT_CHUNK_WRITER_V20\n    private OutputStream projectChunkStream;\n    private Uri projectChunkUri;\n    private String projectChunkMode;\n    private String projectChunkDisplayName;\n'''
    j=j.replace(field_marker,fields,1)

    bridge_marker='    private class AndroidBridge{\n'
    if bridge_marker not in j:
        raise SystemExit('AndroidBridge marker missing')

    helpers=r'''    // PROJECT_CHUNK_WRITER_V20
    private synchronized void closeProjectChunkWriter(){
        if(projectChunkStream!=null){try{projectChunkStream.flush();}catch(Exception ignored){}try{projectChunkStream.close();}catch(Exception ignored){}}
        projectChunkStream=null; projectChunkUri=null; projectChunkMode=null; projectChunkDisplayName=null;
    }
    private synchronized String beginProjectChunkWrite(String mode,String projectName,String fileName){
        closeProjectChunkWriter();
        try{
            if("folder".equals(mode)){
                Uri tree=projectTree();
                if(tree==null)return "NEED_FOLDER";
                Uri dir=ensureProjectDir(tree,projectName);
                Uri file=upsertFile(dir,"project.json","application/json");
                projectChunkStream=openProjectOutput(file);
                projectChunkUri=file;
                projectChunkMode="folder";
                projectChunkDisplayName=safeName(projectName)+"/project.json";
                return "OK";
            }
            if("export".equals(mode)){
                String safeFile=safeName(fileName==null?"Project.df3dproject":fileName);
                if(!safeFile.toLowerCase().endsWith(".df3dproject"))safeFile += ".df3dproject";
                OutputStream out;
                Uri uri=null;
                if(Build.VERSION.SDK_INT>=Build.VERSION_CODES.Q){
                    ContentValues values=new ContentValues();
                    values.put(MediaStore.Downloads.DISPLAY_NAME,safeFile);
                    values.put(MediaStore.Downloads.MIME_TYPE,"application/octet-stream");
                    values.put(MediaStore.Downloads.RELATIVE_PATH,Environment.DIRECTORY_DOWNLOADS+"/3D-Model");
                    uri=getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,values);
                    if(uri==null)throw new Exception("Gagal membuat file Export Project");
                    out=getContentResolver().openOutputStream(uri,"w");
                }else{
                    File dir=new File(getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS),"3D-Model");
                    if(!dir.exists()&&!dir.mkdirs())throw new Exception("Gagal membuat folder export");
                    File f=new File(dir,safeFile);
                    out=new FileOutputStream(f,false);
                    uri=Uri.fromFile(f);
                }
                if(out==null)throw new Exception("Output Export Project tidak tersedia");
                projectChunkStream=out;
                projectChunkUri=uri;
                projectChunkMode="export";
                projectChunkDisplayName=safeFile;
                return "OK";
            }
            return "ERROR: Mode project tidak dikenal";
        }catch(Exception e){
            closeProjectChunkWriter();
            return "ERROR: "+(e.getMessage()==null?e.getClass().getSimpleName():e.getMessage());
        }
    }
    private synchronized String appendProjectChunkData(String base64){
        if(projectChunkStream==null)return "ERROR: Writer project belum dimulai";
        try{
            byte[] bytes=Base64.decode(base64,Base64.DEFAULT);
            projectChunkStream.write(bytes);
            return "OK";
        }catch(Exception e){
            closeProjectChunkWriter();
            return "ERROR: "+(e.getMessage()==null?e.getClass().getSimpleName():e.getMessage());
        }
    }
    private synchronized String finishProjectChunkWrite(){
        if(projectChunkStream==null)return "ERROR: Writer project tidak aktif";
        String label=projectChunkDisplayName==null?"Project":projectChunkDisplayName;
        String mode=projectChunkMode;
        try{
            projectChunkStream.flush(); projectChunkStream.close(); projectChunkStream=null;
            if("folder".equals(mode))runOnUiThread(()->Toast.makeText(MainActivity.this,"Project tersimpan: "+label,Toast.LENGTH_SHORT).show());
            else runOnUiThread(()->Toast.makeText(MainActivity.this,"Export Project tersimpan: "+label,Toast.LENGTH_LONG).show());
            projectChunkUri=null; projectChunkMode=null; projectChunkDisplayName=null;
            return "OK";
        }catch(Exception e){
            closeProjectChunkWriter();
            return "ERROR: "+(e.getMessage()==null?e.getClass().getSimpleName():e.getMessage());
        }
    }

'''
    j=j.replace(bridge_marker,helpers+bridge_marker,1)

    method_marker='        @JavascriptInterface public void chooseProjectFolder(){runOnUiThread(MainActivity.this::chooseProjectFolder);}\n'
    if method_marker not in j:
        raise SystemExit('AndroidBridge chooseProjectFolder marker missing')
    methods='''        @JavascriptInterface public void chooseProjectFolder(){runOnUiThread(MainActivity.this::chooseProjectFolder);}\n        @JavascriptInterface public String beginProjectWrite(String mode,String projectName,String fileName){return beginProjectChunkWrite(mode,projectName,fileName);}\n        @JavascriptInterface public String appendProjectWriteChunk(String base64Chunk){return appendProjectChunkData(base64Chunk);}\n        @JavascriptInterface public String finishProjectWrite(){return finishProjectChunkWrite();}\n        @JavascriptInterface public void cancelProjectWrite(){closeProjectChunkWriter();}\n'''
    j=j.replace(method_marker,methods,1)
    java_path.write_text(j,encoding='utf-8')

# ---------- Web editor: one canonical portable format for Save + Export + Import ----------
if 'PROJECT_ROUNDTRIP_V20' not in s:
    css=r'''
/* PROJECT_ROUNDTRIP_V20 */
#projectsScreen .project-roundtrip-status{margin-top:10px;padding:10px 12px;border-radius:9px;border:1px solid #28394b;background:#101a25;color:#c8d3df;font-size:11px;line-height:1.45}
#projectsScreen .project-roundtrip-status.busy{border-color:#3e7fc7;color:#8fc0ff}
#projectsScreen .project-roundtrip-status.ok{border-color:#287b52;color:#8ee2b6}
#projectsScreen .project-roundtrip-status.err{border-color:#8a3b46;color:#ff9ca8}
'''
    s=s.replace('</style>',css+'\n</style>',1)

    marker='<div class="project-import-hint">'
    pos=s.find(marker)
    if pos<0:
        raise SystemExit('Project import hint marker missing')
    close=s.find('</div>',pos)
    if close<0: raise SystemExit('Project import hint close missing')
    close+=6
    s=s[:close]+'\n      <div class="project-roundtrip-status" id="projectRoundtripStatus">Save Project, Export Project, dan Import Project menggunakan format project yang sama.</div>'+s[close:]

    end=s.rfind('</script>')
    if end<0: raise SystemExit('script end missing')
    js=r'''
// PROJECT_ROUNDTRIP_V20
(function(){
 const statusEl=()=>document.getElementById('projectRoundtripStatus');
 function projectV20Status(text,type=''){
   const el=statusEl(); if(el){el.textContent=text;el.className='project-roundtrip-status'+(type?' '+type:'');}
 }
 function v20SafeName(name){return (name||'Project').toString().trim().replace(/[\\/:*?"<>|]+/g,'_')||'Project'}
 function v20BytesToBase64(bytes){
   let binary=''; const sub=0x8000;
   for(let i=0;i<bytes.length;i+=sub)binary+=String.fromCharCode(...bytes.subarray(i,Math.min(i+sub,bytes.length)));
   return btoa(binary);
 }
 function v20PortableRecord(record){
   const portable={...record,storageFormat:'df3dproject-json-v2',projectFormatVersion:2,app:'3D Viewer & Editor'};
   portable.layers=(record.layers||[]).map(layer=>{
     const copy={...layer};
     if(copy.kind==='model'){
       if(copy.data instanceof ArrayBuffer){copy.dataBase64=arrayBufferToBase64(copy.data);delete copy.data;}
       else if(ArrayBuffer.isView(copy.data)){copy.dataBase64=arrayBufferToBase64(copy.data.buffer);delete copy.data;}
     }
     return copy;
   });
   return portable;
 }
 async function v20BuildPortable(name){
   const id=currentProjectId||newProjectId();
   const record=await buildProjectRecord(name,id,Date.now());
   record.id=id; record.name=name; record.updatedAt=Date.now();
   return v20PortableRecord(record);
 }
 async function v20WriteTextNative(mode,name,fileName,text){
   if(!(window.Android&&typeof Android.beginProjectWrite==='function'&&typeof Android.appendProjectWriteChunk==='function'&&typeof Android.finishProjectWrite==='function')){
     if(mode==='export'){
       const blob=new Blob([text],{type:'application/octet-stream'});const u=URL.createObjectURL(blob);const a=document.createElement('a');a.href=u;a.download=fileName;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1500);return 'OK';
     }
     throw new Error('Penyimpanan folder Project membutuhkan aplikasi Android');
   }
   const begin=Android.beginProjectWrite(mode,name,fileName);
   if(begin==='NEED_FOLDER')return 'NEED_FOLDER';
   if(begin!=='OK')throw new Error(String(begin||'Gagal membuka file project').replace(/^ERROR:\s*/,''));
   try{
     const bytes=new TextEncoder().encode(text); const chunkSize=160*1024;
     for(let off=0;off<bytes.length;off+=chunkSize){
       const chunk=bytes.subarray(off,Math.min(off+chunkSize,bytes.length));
       const r=Android.appendProjectWriteChunk(v20BytesToBase64(chunk));
       if(r!=='OK')throw new Error(String(r||'Gagal menulis project').replace(/^ERROR:\s*/,''));
       if((off/chunkSize)%8===7)await new Promise(requestAnimationFrame);
       projectV20Status(`Menulis project… ${Math.min(100,Math.round((off+chunk.length)/bytes.length*100))}%`,'busy');
     }
     const done=Android.finishProjectWrite();
     if(done!=='OK')throw new Error(String(done||'Gagal menyelesaikan project').replace(/^ERROR:\s*/,''));
     return 'OK';
   }catch(e){try{Android.cancelProjectWrite()}catch(_){}throw e}
 }
 let pendingFolderSave=false;
 async function saveProjectV20(){
   if(!sceneLayers?.length){msg('Belum ada model untuk disimpan');return}
   const input=$('projectNameInput');let name=(input?.value||currentSafProjectName||'').trim();if(!name)name=defaultProjectName();if(input)input.value=name;
   projectV20Status('Menyiapkan Save Project…','busy');
   const btn=$('saveProjectBtn');if(btn)btn.disabled=true;
   try{
     const portable=await v20BuildPortable(name);const text=JSON.stringify(portable);
     const r=await v20WriteTextNative('folder',name,'project.json',text);
     if(r==='NEED_FOLDER'){
       pendingFolderSave=true;projectV20Status('Pilih folder project. Save akan dilanjutkan otomatis setelah folder dipilih.','busy');
       if(window.Android&&typeof Android.chooseProjectFolder==='function')Android.chooseProjectFolder();
       return;
     }
     pendingFolderSave=false;currentProjectId=portable.id;currentSafProjectName=name;
     try{const normalized=normalizeImportedProjectRecord(portable);await projectDbPut(normalized)}catch(e){console.warn('IndexedDB mirror save skipped',e)}
     const label=$('projectCurrentLabel');if(label)label.textContent='Project aktif: '+name+' • Save berikutnya memperbarui project ini.';
     projectV20Status('✓ Save Project berhasil: '+name,'ok');msg('Project tersimpan');
   }catch(e){console.error(e);projectV20Status('Save Project gagal: '+(e?.message||e),'err');msg('Save Project gagal: '+(e?.message||e))}
   finally{if(btn)btn.disabled=false}
 }
 async function exportProjectV20(){
   if(!sceneLayers?.length){msg('Belum ada model/project untuk diexport');return}
   const input=$('projectNameInput');let name=(input?.value||currentSafProjectName||'').trim();if(!name)name=defaultProjectName();if(input)input.value=name;
   const file=v20SafeName(name)+'.df3dproject';const btn=$('projectExportBtn');if(btn)btn.disabled=true;projectV20Status('Menyiapkan Export Project…','busy');
   try{
     const portable=await v20BuildPortable(name);portable.exportedAt=Date.now();const text=JSON.stringify(portable);
     await v20WriteTextNative('export',name,file,text);
     currentProjectId=portable.id;currentSafProjectName=name;
     projectV20Status('✓ Export Project berhasil: '+file+' • file ini bisa langsung di-Import Project.','ok');msg('Export Project berhasil');
   }catch(e){console.error(e);projectV20Status('Export Project gagal: '+(e?.message||e),'err');msg('Export Project gagal: '+(e?.message||e))}
   finally{if(btn)btn.disabled=false}
 }
 async function importProjectV20(file){
   if(!file)return;projectV20Status('Membaca '+file.name+'…','busy');
   try{
     const text=await file.text();const raw=JSON.parse(text);
     if(!Array.isArray(raw.layers))throw new Error('File bukan project 3D Viewer & Editor');
     if(!raw.layers.some(l=>l&&l.kind==='model'))throw new Error('Project tidak memiliki model');
     const record=normalizeImportedProjectRecord(raw);
     await projectDbPut(record);currentProjectId=record.id;currentSafProjectName=record.name||'';
     if($('projectNameInput'))$('projectNameInput').value=record.name||'Project';
     await openSavedProject(record.id);
     projectV20Status('✓ Import Project berhasil: '+(record.name||file.name),'ok');msg('Project berhasil diimport');
   }catch(e){console.error(e);projectV20Status('Import Project gagal: '+(e?.message||e),'err');msg('Import Project gagal: '+(e?.message||e))}
 }
 // Capture listeners run before the older project handlers, preventing two save/export/import paths from firing.
 const save=$('saveProjectBtn');if(save)save.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();saveProjectV20()},{capture:true});
 const exp=$('projectExportBtn');if(exp)exp.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();exportProjectV20()},{capture:true});
 const imp=$('projectImportBtn'),inp=$('projectImportInput');
 if(imp&&inp)imp.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();inp.click()},{capture:true});
 if(inp)inp.addEventListener('change',e=>{e.stopImmediatePropagation();const f=inp.files?.[0];importProjectV20(f).finally(()=>{inp.value=''})},{capture:true});
 const oldFolderChosen=window.onProjectFolderChosen;
 window.onProjectFolderChosen=function(name){try{oldFolderChosen&&oldFolderChosen(name)}catch(_){}if(pendingFolderSave){pendingFolderSave=false;setTimeout(saveProjectV20,120)}};
 window.saveProjectV20=saveProjectV20;window.exportProjectV20=exportProjectV20;window.importProjectV20=importProjectV20;
})();
'''
    s=s[:end]+js+'\n'+s[end:]
    html_path.write_text(s,encoding='utf-8')

print('Project roundtrip v20 applied')
