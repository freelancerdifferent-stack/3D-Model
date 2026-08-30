from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

if 'id="projectsScreen"' in s:
    print('Project Manager patch already applied')
    raise SystemExit(0)

css_marker='.hidden{display:none!important}'
css=r'''
.project-toolbar{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;margin-bottom:10px}
.project-toolbar .field{height:44px}
.project-save-btn{height:44px;min-width:106px;border:0;border-radius:9px;background:linear-gradient(#438ff9,#2d75df);font-weight:700}
.project-list{display:flex;flex-direction:column;gap:9px;margin-top:14px}
.project-item{background:var(--panel2);border:1px solid #283544;border-radius:12px;padding:11px}
.project-item.active{border-color:#4c9cff;box-shadow:0 0 0 1px rgba(76,156,255,.2) inset}
.project-item-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.project-item-name{font-weight:700;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.project-item-meta{font-size:11px;color:var(--muted);margin-top:4px}
.project-item-actions{display:grid;grid-template-columns:1fr 1fr 1fr;gap:7px;margin-top:10px}
.project-item-actions button{height:37px;border:1px solid #34485e;border-radius:8px;background:#121d29;color:#dce7f3;font-size:11px}
.project-empty{padding:28px 12px;text-align:center;color:var(--muted);border:1px dashed #354251;border-radius:12px}
.project-current{margin:10px 0 4px;padding:10px 12px;border:1px solid #26313d;border-radius:10px;background:#111924;font-size:12px;color:#c5ced9}
'''
if css_marker not in s: raise SystemExit('CSS marker missing')
s=s.replace(css_marker,css_marker+css,1)

top_marker='<div><button class="iconbtn" id="homeImport">＋</button><button class="iconbtn" id="topMenu">⋮</button></div>'
top_repl='<div><button class="iconbtn" id="projectQuickSave" title="Save Project">💾</button><button class="iconbtn" id="homeImport">＋</button><button class="iconbtn" id="topMenu">⋮</button></div>'
if top_marker not in s: raise SystemExit('Topbar marker missing')
s=s.replace(top_marker,top_repl,1)

screen_marker='    <section class="screen form" id="exportScreen">'
project_screen=r'''    <section class="screen form" id="projectsScreen">
      <div class="head"><button class="back" data-go="editorScreen">←</button><h2>Projects</h2></div>
      <div class="project-toolbar">
        <input class="field" id="projectNameInput" maxlength="80" placeholder="Nama project">
        <button class="project-save-btn" id="saveProjectBtn">💾 Save</button>
      </div>
      <div class="project-current" id="projectCurrentLabel">Belum ada project aktif. Save pertama akan membuat satu slot project.</div>
      <div class="status">Project disimpan di dalam aplikasi. Menekan Save lagi akan memperbarui slot yang sama, bukan membuat file baru di Downloads.</div>
      <div class="project-list" id="projectList"><div class="project-empty">Belum ada project tersimpan.</div></div>
    </section>

'''
if screen_marker not in s: raise SystemExit('Export screen marker missing')
s=s.replace(screen_marker,project_screen+screen_marker,1)

# Add Projects entry to the Home quick actions without touching existing Layers/navigation.
quick_marker='        <button class="qbtn" data-go="exportScreen"><i>⇧</i>Export</button>'
quick_repl=quick_marker+'\n        <button class="qbtn" id="projectsHomeBtn" data-go="projectsScreen"><i>💾</i>Projects</button>'
if quick_marker not in s: raise SystemExit('Home quick action marker missing')
s=s.replace(quick_marker,quick_repl,1)

# Insert project persistence after layer helpers exist.
func_marker='function collectLayerMeshes(obj){'
project_code=r'''let currentProjectId=null;
const PROJECT_DB_NAME='DF3DProjects';
const PROJECT_DB_VERSION=1;
const PROJECT_STORE='projects';

function openProjectDb(){
  return new Promise((resolve,reject)=>{
    const req=indexedDB.open(PROJECT_DB_NAME,PROJECT_DB_VERSION);
    req.onupgradeneeded=()=>{
      const db=req.result;
      if(!db.objectStoreNames.contains(PROJECT_STORE)) db.createObjectStore(PROJECT_STORE,{keyPath:'id'});
    };
    req.onsuccess=()=>resolve(req.result);
    req.onerror=()=>reject(req.error||new Error('Database project gagal dibuka'));
  });
}
async function projectDbPut(record){
  const db=await openProjectDb();
  return new Promise((resolve,reject)=>{
    const tx=db.transaction(PROJECT_STORE,'readwrite');
    tx.objectStore(PROJECT_STORE).put(record);
    tx.oncomplete=()=>{db.close();resolve()};
    tx.onerror=()=>{const e=tx.error;db.close();reject(e||new Error('Project gagal disimpan'))};
  });
}
async function projectDbGet(id){
  const db=await openProjectDb();
  return new Promise((resolve,reject)=>{
    const tx=db.transaction(PROJECT_STORE,'readonly');
    const req=tx.objectStore(PROJECT_STORE).get(id);
    req.onsuccess=()=>resolve(req.result||null);
    req.onerror=()=>reject(req.error);
    tx.oncomplete=()=>db.close();
  });
}
async function projectDbAll(){
  const db=await openProjectDb();
  return new Promise((resolve,reject)=>{
    const tx=db.transaction(PROJECT_STORE,'readonly');
    const req=tx.objectStore(PROJECT_STORE).getAll();
    req.onsuccess=()=>resolve(req.result||[]);
    req.onerror=()=>reject(req.error);
    tx.oncomplete=()=>db.close();
  });
}
async function projectDbDelete(id){
  const db=await openProjectDb();
  return new Promise((resolve,reject)=>{
    const tx=db.transaction(PROJECT_STORE,'readwrite');
    tx.objectStore(PROJECT_STORE).delete(id);
    tx.oncomplete=()=>{db.close();resolve()};
    tx.onerror=()=>{const e=tx.error;db.close();reject(e)};
  });
}
function newProjectId(){
  return 'project_'+Date.now().toString(36)+'_'+Math.random().toString(36).slice(2,8);
}
function defaultProjectName(){
  const n=(currentFileName||'Project').replace(/\.[^.]+$/,'').trim();
  return n && n!=='untitled' ? n : 'Project '+new Date().toLocaleDateString();
}
function exportProjectObject(obj){
  return new Promise((resolve,reject)=>{
    try{
      new GLTFExporter().parse(obj,result=>{
        if(result instanceof ArrayBuffer) resolve(result);
        else reject(new Error('Project exporter tidak menghasilkan GLB binary'));
      },reject,{binary:true,onlyVisible:false,trs:true});
    }catch(e){reject(e)}
  });
}
async function buildProjectRecord(name,id,createdAt){
  const layers=[];
  for(const layer of sceneLayers){
    if(layer.kind==='model'){
      const data=await exportProjectObject(layer.object);
      layers.push({
        id:layer.id,kind:'model',format:layer.format||'glb',name:layer.name||'Model',
        visible:layer.visible!==false,locked:!!layer.locked,opacity:layer.opacity??1,data
      });
    }else if(layer.kind==='png'){
      layers.push({
        id:layer.id,kind:'png',format:'png',name:layer.name||'Texture.png',targetModelId:layer.targetModelId,
        dataUrl:layer.dataUrl,visible:layer.visible!==false,locked:!!layer.locked,opacity:layer.opacity??1
      });
    }
  }
  return {
    version:1,id,name,createdAt:createdAt||Date.now(),updatedAt:Date.now(),
    selectedLayerId,
    layers,
    camera:{position:[camera.position.x,camera.position.y,camera.position.z],target:[controls.target.x,controls.target.y,controls.target.z]},
    view:{gridVisible:grid.visible,axis:typeof partTransformAxis!=='undefined'?partTransformAxis:'free'}
  };
}
async function saveCurrentProject(forceNew=false){
  if(!sceneLayers.length){msg('Belum ada model untuk disimpan');return}
  const input=$('projectNameInput');
  let name=(input?.value||'').trim();
  if(!name) name=defaultProjectName();
  if(input) input.value=name;
  const oldId=!forceNew?currentProjectId:null;
  const id=oldId||newProjectId();
  let createdAt=Date.now();
  if(oldId){
    try{const old=await projectDbGet(oldId); if(old?.createdAt)createdAt=old.createdAt}catch(_){ }
  }
  const btn=$('saveProjectBtn');
  if(btn){btn.disabled=true;btn.textContent='Saving…'}
  try{
    const record=await buildProjectRecord(name,id,createdAt);
    await projectDbPut(record);
    currentProjectId=id;
    $('projectCurrentLabel').textContent='Project aktif: '+name+' • Save berikutnya akan memperbarui project ini.';
    await renderProjectList();
    msg('Project tersimpan');
  }catch(e){
    console.error(e);msg('Save project gagal: '+(e?.message||e));
  }finally{
    if(btn){btn.disabled=false;btn.textContent='💾 Save'}
  }
}
function loadProjectGlb(data){
  return new Promise((resolve,reject)=>{
    try{new GLTFLoader().parse(data,'',g=>resolve(g.scene),reject)}catch(e){reject(e)}
  });
}
function clearProjectScene(){
  if(typeof finishPartDrag==='function') finishPartDrag();
  if(typeof finishPartTransform==='function') finishPartTransform();
  if(typeof partDragHelper!=='undefined' && partDragHelper){scene.remove(partDragHelper);partDragHelper=null}
  sceneLayers.filter(l=>l.kind==='model').forEach(l=>disposeLayerObject(l.object));
  sceneLayers.filter(l=>l.kind==='png').forEach(l=>l.texture?.dispose?.());
  sceneLayers=[];selectedLayerId=null;root=null;meshList=[];
  mixer=null;clips=[];activeAction=null;playing=false;
  $('fileLabel').textContent='No model loaded';$('meshLabel').textContent='0 Mesh';
  updateMeshSelect();renderLayers();
  if(typeof renderMeshLayers==='function')renderMeshLayers();
}
async function openSavedProject(id){
  const record=await projectDbGet(id);
  if(!record){msg('Project tidak ditemukan');return}
  const label=$('projectCurrentLabel');
  if(label)label.textContent='Membuka project…';
  try{
    clearProjectScene();
    for(const saved of record.layers||[]){
      if(saved.kind!=='model')continue;
      const obj=await loadProjectGlb(saved.data);
      obj.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.frustumCulled=false}});
      scene.add(obj);
      const layer={id:saved.id,kind:'model',format:saved.format||'glb',name:saved.name||'Model',object:obj,visible:saved.visible!==false,locked:!!saved.locked,opacity:saved.opacity??1};
      obj.visible=layer.visible;
      sceneLayers.push(layer);
      setLayerOpacity(layer,layer.opacity);
    }
    for(const saved of record.layers||[]){
      if(saved.kind!=='png')continue;
      sceneLayers.push({id:saved.id,kind:'png',format:'png',name:saved.name||'Texture.png',targetModelId:saved.targetModelId,dataUrl:saved.dataUrl,texture:null,visible:saved.visible!==false,locked:!!saved.locked,opacity:saved.opacity??1});
    }
    const numeric=sceneLayers.map(l=>Number(String(l.id||'').replace(/^layer_/,''))).filter(Number.isFinite);
    if(numeric.length) nextLayerId=Math.max(nextLayerId,Math.max(...numeric)+1);
    for(const model of sceneLayers.filter(l=>l.kind==='model')){
      if(sceneLayers.some(l=>l.kind==='png'&&l.targetModelId===model.id)) await rebuildPngLayers(model.id);
    }
    const wanted=layerById(record.selectedLayerId);
    const active=wanted?.kind==='model'?wanted:(wanted?.kind==='png'?layerById(wanted.targetModelId):null)||sceneLayers.find(l=>l.kind==='model');
    if(active)syncSelectedLayerToEditor(active);
    renderLayers();
    if(typeof renderMeshLayers==='function')renderMeshLayers();
    if(record.camera?.position?.length===3)camera.position.fromArray(record.camera.position);
    if(record.camera?.target?.length===3)controls.target.fromArray(record.camera.target);
    controls.update();
    if(record.view && typeof record.view.gridVisible==='boolean')grid.visible=record.view.gridVisible;
    if(record.view?.axis && typeof setPartTransformAxis==='function')setPartTransformAxis(record.view.axis,false);
    currentProjectId=record.id;
    $('projectNameInput').value=record.name||'Project';
    $('projectCurrentLabel').textContent='Project aktif: '+(record.name||'Project')+' • Save berikutnya akan memperbarui project ini.';
    go('editorScreen');
    msg('Project dibuka');
  }catch(e){console.error(e);msg('Open project gagal: '+(e?.message||e))}
}
function projectDateText(ts){
  try{return new Date(ts).toLocaleString()}catch(_){return ''}
}
async function renderProjectList(){
  const list=$('projectList');if(!list)return;
  let projects=[];
  try{projects=await projectDbAll()}catch(e){list.innerHTML='<div class="project-empty">Database project gagal dibaca.</div>';return}
  projects.sort((a,b)=>(b.updatedAt||0)-(a.updatedAt||0));
  if(!projects.length){list.innerHTML='<div class="project-empty">Belum ada project tersimpan.</div>';return}
  list.innerHTML='';
  projects.forEach(project=>{
    const row=document.createElement('div');row.className='project-item'+(project.id===currentProjectId?' active':'');
    const head=document.createElement('div');head.className='project-item-head';
    const left=document.createElement('div');left.style.minWidth='0';
    const name=document.createElement('div');name.className='project-item-name';name.textContent=project.name||'Project';
    const meta=document.createElement('div');meta.className='project-item-meta';meta.textContent=`Updated ${projectDateText(project.updatedAt)} • ${(project.layers||[]).filter(l=>l.kind==='model').length} model • ${(project.layers||[]).filter(l=>l.kind==='png').length} PNG`;
    left.append(name,meta);head.append(left);
    const actions=document.createElement('div');actions.className='project-item-actions';
    const open=document.createElement('button');open.textContent='OPEN';open.onclick=()=>openSavedProject(project.id);
    const rename=document.createElement('button');rename.textContent='RENAME';rename.onclick=async()=>{const n=prompt('Nama project',project.name||'Project');if(!n?.trim())return;project.name=n.trim();project.updatedAt=Date.now();await projectDbPut(project);if(project.id===currentProjectId)$('projectNameInput').value=project.name;await renderProjectList();msg('Nama project diubah')};
    const del=document.createElement('button');del.textContent='DELETE';del.onclick=async()=>{if(!confirm(`Hapus project ${project.name||'Project'}?`))return;await projectDbDelete(project.id);if(currentProjectId===project.id){currentProjectId=null;$('projectCurrentLabel').textContent='Belum ada project aktif. Save berikutnya akan membuat slot baru.'}await renderProjectList();msg('Project dihapus')};
    actions.append(open,rename,del);row.append(head,actions);list.appendChild(row);
  });
}
function openProjectsScreen(){
  if(!$('projectNameInput').value.trim())$('projectNameInput').value=defaultProjectName();
  go('projectsScreen');renderProjectList();
}

'''
if func_marker not in s: raise SystemExit('collectLayerMeshes marker missing')
s=s.replace(func_marker,project_code+func_marker,1)

handler_marker="$('homeImport').onclick=()=>go('importScreen');"
handler_repl=r'''$('projectQuickSave').onclick=()=>{
  if(currentProjectId) saveCurrentProject(false);
  else openProjectsScreen();
};
$('projectsHomeBtn').addEventListener('click',()=>{if(!$('projectNameInput').value.trim())$('projectNameInput').value=defaultProjectName();renderProjectList()});
$('saveProjectBtn').addEventListener('click',()=>saveCurrentProject(false));
$('homeImport').onclick=()=>go('importScreen');'''
if handler_marker not in s: raise SystemExit('homeImport handler marker missing')
s=s.replace(handler_marker,handler_repl,1)

# Existing generic data-go listener opens Projects; refresh list whenever its screen is tapped/opened from nav-like controls.
end_marker="$('topMenu').onclick=()=>msg('3D Viewer & Editor');"
end_repl=end_marker+"\ndocument.querySelectorAll('[data-go=\"projectsScreen\"]').forEach(b=>b.addEventListener('click',()=>renderProjectList()));"
if end_marker not in s: raise SystemExit('topMenu marker missing')
s=s.replace(end_marker,end_repl,1)

p.write_text(s,encoding='utf-8')
print('Project Manager patch applied')
