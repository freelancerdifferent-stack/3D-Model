from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'MESH_LAYER_MANAGE_V15' in s:
    print('Mesh layer manage v15 already applied'); raise SystemExit(0)

css=r'''
/* MESH_LAYER_MANAGE_V15 */
#meshLayersScreen .mesh-manage-bar{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0 4px}
#meshLayersScreen .mesh-manage-bar button{height:42px;border-radius:9px;font-weight:700}
#meshLayersScreen .mesh-add-btn{border:0;background:linear-gradient(#438ff9,#2d75df)}
#meshLayersScreen .mesh-action-btn{border:1px solid #34485e;background:#121d29;color:#dce7f3}
#meshLayersScreen .mesh-layer-item{grid-template-columns:38px minmax(0,1fr) 54px 38px 38px}
#meshLayersScreen .mesh-mini{height:34px;width:38px;border:1px solid #34485e;border-radius:8px;background:#121d29;font-size:15px;padding:0}
#meshLayersScreen .mesh-mini.danger{color:#ff7777}
'''
s=s.replace('</style>',css+'\n</style>',1)

# Add dedicated Add Mesh input/button to Mesh Layers only.
needle='<div class="status" id="meshLayersStatus">Pilih satu mesh untuk dijadikan target Material & Texture.</div>'
repl=needle+r'''
      <!-- MESH_LAYER_MANAGE_V15 -->
      <input id="meshAddInput" type="file" accept=".glb,.fbx" class="hidden">
      <div class="mesh-manage-bar">
        <button class="mesh-add-btn" id="meshAddBtn">＋ Add Mesh</button>
        <button class="mesh-action-btn" id="meshRenameSelectedBtn">✎ Rename Selected</button>
      </div>'''
if needle not in s: raise SystemExit('Mesh status marker missing')
s=s.replace(needle,repl,1)

# Expand renderer rows with Rename/Delete mini buttons while keeping SELECT.
needle="    row.append(eye,main,pick);\n    list.appendChild(row);"
repl=r'''    const rename=document.createElement('button');
    rename.className='mesh-mini';rename.textContent='✎';rename.title='Rename mesh';
    rename.onclick=e=>{e.stopPropagation();renameMeshLayer(index)};
    const del=document.createElement('button');
    del.className='mesh-mini danger';del.textContent='⌫';del.title='Delete mesh';
    del.onclick=e=>{e.stopPropagation();deleteMeshLayer(index)};
    row.append(eye,main,pick,rename,del);
    list.appendChild(row);'''
if needle not in s: raise SystemExit('Mesh row append marker missing')
s=s.replace(needle,repl,1)

# Insert management functions before refreshMeshLayersAfterModelChange.
marker='function refreshMeshLayersAfterModelChange(){'
if marker not in s: raise SystemExit('mesh refresh marker missing')
code=r'''
// MESH_LAYER_MANAGE_V15
function renameMeshLayer(index){
  const mesh=meshList[Number(index)];if(!mesh)return;
  if(typeof isMeshPartLocked==='function'&&isMeshPartLocked(mesh)){msg('Part ini dikunci');return}
  const old=meshLayerDisplayName(mesh,Number(index));
  const name=prompt('Nama mesh',old);
  if(name==null)return;
  const clean=name.trim();if(!clean){msg('Nama mesh tidak boleh kosong');return}
  mesh.name=clean;
  if(typeof updateMeshSelect==='function')updateMeshSelect();
  activeMeshLayerIndex=meshList.indexOf(mesh);
  if($('targetMesh'))$('targetMesh').value=String(activeMeshLayerIndex);
  renderMeshLayers();msg('Mesh diubah menjadi: '+clean);
}
function deleteMeshLayer(index){
  index=Number(index);const mesh=meshList[index];if(!mesh)return;
  if(typeof isMeshPartLocked==='function'&&isMeshPartLocked(mesh)){msg('Part ini dikunci');return}
  const name=meshLayerDisplayName(mesh,index);
  if(!confirm('Hapus mesh "'+name+'" dari model?'))return;
  try{if(typeof finishPartDrag==='function')finishPartDrag();if(typeof finishPartTransform==='function')finishPartTransform()}catch(_){}
  if(mesh.parent)mesh.parent.remove(mesh);
  meshList.splice(index,1);
  if(activeMeshLayerIndex===index)activeMeshLayerIndex=-1;
  else if(activeMeshLayerIndex>index)activeMeshLayerIndex--;
  if(typeof hidePartSelection==='function')try{hidePartSelection()}catch(_){}
  if(typeof updateMeshSelect==='function')updateMeshSelect();
  if(activeMeshLayerIndex>=0&&meshList[activeMeshLayerIndex]&&$('targetMesh'))$('targetMesh').value=String(activeMeshLayerIndex);
  renderMeshLayers();
  $('meshLabel').textContent=meshList.length+' Mesh';
  msg('Mesh dihapus: '+name);
}
function rebuildAnimationUiAfterMeshAdd(extraClips){
  if(!Array.isArray(extraClips)||!extraClips.length)return;
  clips=[...(clips||[]),...extraClips];
  const sel=$('animSelect');if(sel){sel.innerHTML='';clips.forEach((clip,i)=>{const o=document.createElement('option');o.value=String(i);o.textContent=clip.name&&clip.name.trim()?`${i+1}. ${clip.name}`:`Animation ${i+1}`;sel.appendChild(o)})}
  if($('animClipCount'))$('animClipCount').textContent=String(clips.length);
  try{if(mixer)mixer.stopAllAction();mixer=new THREE.AnimationMixer(root);activeClipIndex=0;activeAction=mixer.clipAction(clips[0]);activeAction.reset().play();mixer.timeScale=0;if($('durationText'))$('durationText').textContent=clips[0].duration.toFixed(2)+'s'}catch(e){console.warn('Animation rebuild after Add Mesh',e)}
}
async function addMeshFile(file){
  if(!root){msg('Import model utama dulu');return}
  if(!file)return;
  const ext=(file.name.split('.').pop()||'').toLowerCase();
  if(ext!=='glb'&&ext!=='fbx'){msg('Add Mesh mendukung GLB / FBX');return}
  const beforeCount=meshList.length;
  $('meshLayersStatus').textContent='Menambahkan mesh dari '+file.name+'…';
  try{
    let obj,animations=[];
    if(ext==='glb'){
      const buf=await file.arrayBuffer();
      const gltf=await new Promise((res,rej)=>new GLTFLoader().parse(buf,'',res,rej));
      obj=gltf.scene;animations=gltf.animations||[];
    }else{
      try{const gltf=await loadFbxWithAssimp(file);obj=gltf.scene;animations=gltf.animations||[]}
      catch(err){console.warn('Assimp Add Mesh fallback',err);const url=URL.createObjectURL(file);try{obj=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));animations=obj.animations||[]}finally{URL.revokeObjectURL(url)}}
    }
    if(!obj)throw new Error('Model tambahan kosong');
    obj.name=obj.name||('Added_'+file.name.replace(/\.[^.]+$/,''));
    // Add the imported hierarchy as one child of the current model. Do not reparent
    // individual SkinnedMesh nodes, so skeleton/bind relationships remain intact.
    root.add(obj);obj.updateMatrixWorld(true);
    const added=[];
    obj.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.frustumCulled=false;meshList.push(o);added.push(o)}});
    if(!added.length){root.remove(obj);throw new Error('File tidak memiliki mesh')}
    rebuildAnimationUiAfterMeshAdd(animations);
    activeMeshLayerIndex=beforeCount;
    if(typeof updateMeshSelect==='function')updateMeshSelect();
    activeMeshLayerIndex=beforeCount;
    if($('targetMesh'))$('targetMesh').value=String(beforeCount);
    $('meshLabel').textContent=meshList.length+' Mesh';
    renderMeshLayers();
    if(typeof showStrongPartSelection==='function')try{showStrongPartSelection(meshList[beforeCount])}catch(_){}
    msg(added.length+' mesh ditambahkan');
  }catch(e){console.error(e);$('meshLayersStatus').textContent='Add Mesh gagal: '+(e?.message||e);msg('Add Mesh gagal')}
}

'''
s=s.replace(marker,code+marker,1)

# Add handlers near existing Mesh Layers handlers.
marker="$('meshLayersNav').addEventListener('click',()=>renderMeshLayers());"
if marker not in s: raise SystemExit('mesh nav handler missing')
handlers=r'''$('meshAddBtn').onclick=()=>$('meshAddInput').click();
$('meshAddInput').onchange=async()=>{const f=$('meshAddInput').files?.[0];await addMeshFile(f);$('meshAddInput').value=''};
$('meshRenameSelectedBtn').onclick=()=>{if(activeMeshLayerIndex<0||!meshList[activeMeshLayerIndex]){msg('Pilih mesh dulu');return}renameMeshLayer(activeMeshLayerIndex)};
'''
s=s.replace(marker,marker+'\n'+handlers,1)

p.write_text(s,encoding='utf-8')
print('Mesh Layers management v15 applied')
