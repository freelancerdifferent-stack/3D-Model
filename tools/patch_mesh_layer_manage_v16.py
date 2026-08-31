from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'MESH_LAYER_MANAGE_V16' in s:
    print('Mesh layer manage v16 already applied'); raise SystemExit(0)

css=r'''
/* MESH_LAYER_MANAGE_V16 */
#meshLayersScreen .mesh-manage-bar{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0 4px}
#meshLayersScreen .mesh-manage-bar button{height:42px;border-radius:9px;font-weight:700}
#meshLayersScreen .mesh-add-btn{border:0;background:linear-gradient(#438ff9,#2d75df)}
#meshLayersScreen .mesh-action-btn{border:1px solid #34485e;background:#121d29;color:#dce7f3}
#meshLayersScreen .mesh-layer-item{grid-template-columns:38px minmax(0,1fr) 54px 38px 38px!important}
#meshLayersScreen .mesh-mini{height:34px;width:38px;border:1px solid #34485e;border-radius:8px;background:#121d29;font-size:15px;padding:0}
#meshLayersScreen .mesh-mini.danger{color:#ff7777}
'''
s=s.replace('</style>',css+'\n</style>',1)

needle='<div class="status" id="meshLayersStatus">Pilih satu mesh untuk dijadikan target Material & Texture.</div>'
if needle not in s: raise SystemExit('Mesh status marker missing')
s=s.replace(needle,needle+r'''\n      <!-- MESH_LAYER_MANAGE_V16 -->
      <input id="meshAddInput" type="file" accept=".glb,.fbx" class="hidden">
      <div class="mesh-manage-bar">
        <button class="mesh-add-btn" id="meshAddBtn">＋ Add Mesh</button>
        <button class="mesh-action-btn" id="meshRenameSelectedBtn">✎ Rename Selected</button>
      </div>''',1)

js=r'''
// MESH_LAYER_MANAGE_V16
(function(){
 function selectedIndex(){return (typeof activeMeshLayerIndex!=='undefined')?activeMeshLayerIndex:-1}
 function selectedMesh(){const i=selectedIndex();return i>=0&&meshList[i]?meshList[i]:null}
 function locked(m){return !!(m&&typeof isMeshPartLocked==='function'&&isMeshPartLocked(m))}
 window.renameMeshLayer=function(index){
   index=Number(index);const mesh=meshList[index];if(!mesh)return;
   if(locked(mesh)){msg('Part ini dikunci');return}
   const old=(typeof meshLayerDisplayName==='function')?meshLayerDisplayName(mesh,index):(mesh.name||('Mesh '+(index+1)));
   const name=prompt('Nama mesh',old);if(name==null)return;const clean=name.trim();if(!clean){msg('Nama mesh tidak boleh kosong');return}
   mesh.name=clean;
   if(typeof updateMeshSelect==='function')updateMeshSelect();
   activeMeshLayerIndex=meshList.indexOf(mesh);if($('targetMesh'))$('targetMesh').value=String(activeMeshLayerIndex);
   renderMeshLayers();msg('Mesh diubah menjadi: '+clean);
 };
 window.deleteMeshLayer=function(index){
   index=Number(index);const mesh=meshList[index];if(!mesh)return;
   if(locked(mesh)){msg('Part ini dikunci');return}
   const name=(typeof meshLayerDisplayName==='function')?meshLayerDisplayName(mesh,index):(mesh.name||('Mesh '+(index+1)));
   if(!confirm('Hapus mesh "'+name+'" dari model?'))return;
   try{finishPartDrag?.();finishPartTransform?.()}catch(_){}
   if(mesh.parent)mesh.parent.remove(mesh);
   meshList.splice(index,1);
   if(activeMeshLayerIndex===index)activeMeshLayerIndex=-1;else if(activeMeshLayerIndex>index)activeMeshLayerIndex--;
   if(typeof updateMeshSelect==='function')updateMeshSelect();
   if($('meshLabel'))$('meshLabel').textContent=meshList.length+' Mesh';
   renderMeshLayers();msg('Mesh dihapus: '+name);
 };
 function decorateRows(){
   const list=$('meshLayersList');if(!list)return;
   [...list.querySelectorAll('.mesh-layer-item')].forEach((row,index)=>{
     if(row.querySelector('.mesh-mini'))return;
     const rn=document.createElement('button');rn.type='button';rn.className='mesh-mini';rn.textContent='✎';rn.title='Rename mesh';rn.onclick=e=>{e.stopPropagation();renameMeshLayer(index)};
     const del=document.createElement('button');del.type='button';del.className='mesh-mini danger';del.textContent='⌫';del.title='Delete mesh';del.onclick=e=>{e.stopPropagation();deleteMeshLayer(index)};
     row.append(rn,del);
   });
 }
 const baseRender=renderMeshLayers;
 renderMeshLayers=function(){const r=baseRender.apply(this,arguments);decorateRows();return r};
 async function addMeshFile(file){
   if(!root){msg('Import model utama dulu');return}if(!file)return;
   const ext=(file.name.split('.').pop()||'').toLowerCase();if(ext!=='glb'&&ext!=='fbx'){msg('Add Mesh mendukung GLB / FBX');return}
   const before=meshList.length;$('meshLayersStatus').textContent='Menambahkan '+file.name+'…';
   try{
     let obj,animations=[];
     if(ext==='glb'){
       const buf=await file.arrayBuffer();const gltf=await new Promise((res,rej)=>new GLTFLoader().parse(buf,'',res,rej));obj=gltf.scene;animations=gltf.animations||[];
     }else{
       try{const gltf=await loadFbxWithAssimp(file);obj=gltf.scene;animations=gltf.animations||[]}
       catch(err){const u=URL.createObjectURL(file);try{obj=await new Promise((res,rej)=>new FBXLoader().load(u,res,undefined,rej));animations=obj.animations||[]}finally{URL.revokeObjectURL(u)}}
     }
     if(!obj)throw new Error('Model tambahan kosong');
     root.add(obj);obj.updateMatrixWorld(true);const added=[];
     obj.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.frustumCulled=false;meshList.push(o);added.push(o)}});
     if(!added.length){root.remove(obj);throw new Error('File tidak memiliki mesh')}
     if(animations.length){clips=[...(clips||[]),...animations]}
     activeMeshLayerIndex=before;if(typeof updateMeshSelect==='function')updateMeshSelect();activeMeshLayerIndex=before;if($('targetMesh'))$('targetMesh').value=String(before);
     if($('meshLabel'))$('meshLabel').textContent=meshList.length+' Mesh';renderMeshLayers();msg(added.length+' mesh ditambahkan');
   }catch(e){console.error(e);$('meshLayersStatus').textContent='Add Mesh gagal: '+(e?.message||e);msg('Add Mesh gagal')}
 }
 $('meshAddBtn').onclick=()=>$('meshAddInput').click();
 $('meshAddInput').onchange=async()=>{const f=$('meshAddInput').files?.[0];await addMeshFile(f);$('meshAddInput').value=''};
 $('meshRenameSelectedBtn').onclick=()=>{const m=selectedMesh();if(!m){msg('Pilih mesh dulu');return}renameMeshLayer(selectedIndex())};
 decorateRows();
})();
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('script end missing')
s=s[:idx]+js+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Mesh Layers management v16 applied')
