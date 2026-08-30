from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'id="layersScreen"' in s:
    print('Layers patch already applied')
    raise SystemExit(0)

css_marker='.hidden{display:none!important}'
css='''\n.layers-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px}\n.layers-list{display:flex;flex-direction:column;gap:8px;margin-top:12px}\n.layer-item{display:grid;grid-template-columns:38px minmax(0,1fr) auto;gap:8px;align-items:center;background:var(--panel2);border:1px solid #283544;border-radius:12px;padding:8px}\n.layer-item.active{border-color:#4c9cff;box-shadow:0 0 0 1px rgba(76,156,255,.22) inset}\n.layer-eye,.layer-mini{height:36px;min-width:36px;border:0;border-radius:8px;background:#101821;color:#dce5ef}\n.layer-eye.off{opacity:.42}.layer-mini.on{background:#244f80;color:#7bb6ff}\n.layer-main{min-width:0}.layer-name{font-weight:650;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.layer-meta{font-size:11px;color:var(--muted);margin-top:3px}\n.layer-actions{display:flex;gap:4px;align-items:center}.layer-actions .layer-mini{font-size:14px;padding:0 9px}\n.layer-toolbar{display:grid;grid-template-columns:1fr 1fr;gap:8px}.layer-toolbar .outline{margin-top:0}\n.layer-opacity{margin-top:14px;background:#111924;border:1px solid #26313d;border-radius:12px;padding:12px}.layer-opacity .row{grid-template-columns:1fr 70px;margin:0 0 8px}.layer-opacity input[type=range]{width:100%}\n.layer-empty{padding:24px 12px;text-align:center;color:var(--muted);border:1px dashed #354251;border-radius:12px}\n'''
s=s.replace(css_marker, css_marker+css)

screen_marker='    <section class="screen form" id="exportScreen">'
layers_html='''    <section class="screen form" id="layersScreen">\n      <div class="head"><button class="back" data-go="editorScreen">←</button><h2>Layers</h2></div>\n      <div class="layers-head"><div><b>Scene Layers</b><div style="font-size:11px;color:var(--muted);margin-top:3px">FBX • GLB • PNG</div></div><span class="pill" id="layerCount">0 Layer</span></div>\n      <input id="layerInput" type="file" accept=".fbx,.glb,.png,image/png" class="hidden">\n      <label class="primary" for="layerInput" style="display:flex;align-items:center;justify-content:center;margin-top:0">＋ Add Layer (FBX / GLB / PNG)</label>\n      <div class="layer-opacity">\n        <div class="row"><span>Selected Opacity</span><b id="layerOpacityText" style="justify-self:end">100%</b></div>\n        <input type="range" id="layerOpacity" min="0" max="100" value="100">\n      </div>\n      <div class="layers-list" id="layersList"><div class="layer-empty">Import model atau tekan Add Layer.</div></div>\n      <div class="status" id="layerStatus">Pilih layer untuk Move / Rotate / Scale. Layer PNG diterapkan sebagai texture layer pada model aktif.</div>\n    </section>\n\n'''
if screen_marker not in s: raise SystemExit('export screen marker missing')
s=s.replace(screen_marker,layers_html+screen_marker)

s=s.replace('.bottomnav{height:66px;flex:none;display:grid;grid-template-columns:repeat(5,1fr);', '.bottomnav{height:66px;flex:none;display:grid;grid-template-columns:repeat(6,1fr);')
nav_marker='    <button class="nav" id="autoUVNav"><b>⌗</b>Auto UV</button>\n    <button class="nav" data-go="exportScreen"><b>⇧</b>Export</button>'
nav_repl='    <button class="nav" id="autoUVNav"><b>⌗</b>Auto UV</button>\n    <button class="nav" data-go="layersScreen"><b>▤</b>Layers</button>\n    <button class="nav" data-go="exportScreen"><b>⇧</b>Export</button>'
if nav_marker not in s: raise SystemExit('nav marker missing')
s=s.replace(nav_marker,nav_repl)

state_marker='let meshList=[];'
layer_state='''let meshList=[];\n\nlet sceneLayers=[];\nlet selectedLayerId=null;\nlet nextLayerId=1;\nlet suppressLayerSync=false;\nconst newLayerId=()=>`layer_${nextLayerId++}`;\nfunction layerById(id){ return sceneLayers.find(l=>l.id===id)||null; }\nfunction selectedLayer(){ return layerById(selectedLayerId); }\nfunction modelLayerForObject(obj){ return sceneLayers.find(l=>l.kind==='model' && l.object===obj)||null; }\nfunction activeModelLayer(){\n  const s=selectedLayer();\n  if(s?.kind==='model') return s;\n  if(s?.kind==='png') return layerById(s.targetModelId);\n  return modelLayerForObject(root) || sceneLayers.find(l=>l.kind==='model') || null;\n}\n'''
if state_marker not in s: raise SystemExit('meshList marker missing')
s=s.replace(state_marker,layer_state,1)

func_marker='function updateMeshSelect(){'
layer_funcs=r'''function collectLayerMeshes(obj){
  const arr=[]; obj?.traverse?.(o=>{if(o.isMesh) arr.push(o)}); return arr;
}
function disposeLayerObject(obj){
  if(!obj)return;
  scene.remove(obj);
  obj.traverse?.(o=>{
    o.geometry?.dispose?.();
    const mats=Array.isArray(o.material)?o.material:[o.material];
    mats.filter(Boolean).forEach(m=>{for(const k in m){const v=m[k]; if(v?.isTexture)v.dispose?.()} m.dispose?.()});
  });
}
function setLayerOpacity(layer,value){
  layer.opacity=Math.max(0,Math.min(1,value));
  if(layer.kind==='model'){
    collectLayerMeshes(layer.object).forEach(mesh=>{
      const mats=Array.isArray(mesh.material)?mesh.material:[mesh.material];
      mats.filter(Boolean).forEach(m=>{m.transparent=layer.opacity<.999 || !!m.transparent; m.opacity=layer.opacity; m.needsUpdate=true});
    });
  }else if(layer.kind==='png') applyPngLayerVisibility(layer);
}
function setLayerVisible(layer,visible){
  layer.visible=!!visible;
  if(layer.kind==='model' && layer.object) layer.object.visible=layer.visible;
  if(layer.kind==='png') applyPngLayerVisibility(layer);
}
function ensureMeshLayerBase(mesh){
  if(mesh.userData.__layerBaseMaterial)return;
  const mats=Array.isArray(mesh.material)?mesh.material:[mesh.material];
  mesh.userData.__layerBaseMaterial=mats.map(m=>m?.clone?m.clone():m);
  mesh.userData.__layerWasArray=Array.isArray(mesh.material);
}
function restoreModelBaseMaterials(modelLayer){
  collectLayerMeshes(modelLayer?.object).forEach(mesh=>{
    if(!mesh.userData.__layerBaseMaterial)return;
    const clones=mesh.userData.__layerBaseMaterial.map(m=>m?.clone?m.clone():m);
    mesh.material=mesh.userData.__layerWasArray?clones:clones[0];
  });
}
function textureFromDataUrl(dataUrl){
  return new Promise((resolve,reject)=>{
    const img=new Image();
    img.onload=()=>{const tex=new THREE.Texture(img); tex.needsUpdate=true; tex.flipY=false; tex.colorSpace=THREE.SRGBColorSpace; resolve(tex)};
    img.onerror=()=>reject(new Error('PNG layer tidak dapat dibaca'));
    img.src=dataUrl;
  });
}
async function rebuildPngLayers(modelId){
  const model=layerById(modelId); if(!model?.object)return;
  const meshes=collectLayerMeshes(model.object);
  meshes.forEach(ensureMeshLayerBase);
  restoreModelBaseMaterials(model);
  const pngs=sceneLayers.filter(l=>l.kind==='png' && l.targetModelId===modelId && l.visible);
  for(const layer of pngs){
    if(!layer.texture){ try{layer.texture=await textureFromDataUrl(layer.dataUrl)}catch(e){continue} }
    meshes.forEach(mesh=>{
      const mats=Array.isArray(mesh.material)?mesh.material:[mesh.material];
      const repl=mats.map(old=>{
        const m=old?.clone?old.clone():new THREE.MeshStandardMaterial({color:0xffffff});
        if(m.color)m.color.set(0xffffff);
        m.map=layer.texture;
        m.transparent=layer.opacity<.999 || !!m.transparent;
        m.opacity=layer.opacity;
        m.needsUpdate=true;
        return m;
      });
      mesh.material=Array.isArray(mesh.material)?repl:repl[0];
    });
  }
}
function applyPngLayerVisibility(layer){ if(layer?.targetModelId) rebuildPngLayers(layer.targetModelId); }
function syncSelectedLayerToEditor(layer){
  if(!layer)return;
  selectedLayerId=layer.id;
  if(layer.kind==='model' && layer.object){
    root=layer.object;
    meshList=collectLayerMeshes(root);
    currentFileName=layer.name;
    $('fileLabel').textContent=layer.name;
    $('meshLabel').textContent=meshList.length+' Mesh';
    updateMeshSelect(); updateTransformFields();
  }
  $('layerOpacity').value=Math.round((layer.opacity??1)*100);
  $('layerOpacityText').textContent=Math.round((layer.opacity??1)*100)+'%';
  renderLayers();
}
function renderLayers(){
  const list=$('layersList'); if(!list)return;
  $('layerCount').textContent=`${sceneLayers.length} Layer${sceneLayers.length===1?'':'s'}`;
  if(!sceneLayers.length){list.innerHTML='<div class="layer-empty">Import model atau tekan Add Layer.</div>';return}
  list.innerHTML='';
  [...sceneLayers].reverse().forEach(layer=>{
    const row=document.createElement('div'); row.className='layer-item'+(layer.id===selectedLayerId?' active':''); row.dataset.id=layer.id;
    const eye=document.createElement('button'); eye.className='layer-eye'+(layer.visible?'':' off'); eye.textContent=layer.visible?'👁':'◌'; eye.onclick=e=>{e.stopPropagation();setLayerVisible(layer,!layer.visible);renderLayers()};
    const main=document.createElement('div'); main.className='layer-main';
    main.innerHTML=`<div class="layer-name"></div><div class="layer-meta">${layer.kind==='model'?layer.format.toUpperCase()+' • '+collectLayerMeshes(layer.object).length+' Mesh':'PNG Texture'}${layer.locked?' • Locked':''}</div>`;
    main.querySelector('.layer-name').textContent=layer.name;
    const actions=document.createElement('div'); actions.className='layer-actions';
    const lock=document.createElement('button'); lock.className='layer-mini'+(layer.locked?' on':''); lock.textContent=layer.locked?'🔒':'🔓'; lock.onclick=e=>{e.stopPropagation();layer.locked=!layer.locked;renderLayers()};
    const up=document.createElement('button'); up.className='layer-mini'; up.textContent='↑'; up.onclick=e=>{e.stopPropagation();moveLayer(layer.id,1)};
    const down=document.createElement('button'); down.className='layer-mini'; down.textContent='↓'; down.onclick=e=>{e.stopPropagation();moveLayer(layer.id,-1)};
    const more=document.createElement('button'); more.className='layer-mini'; more.textContent='⋮'; more.onclick=e=>{e.stopPropagation();layerMenu(layer)};
    actions.append(lock,up,down,more); row.append(eye,main,actions); row.onclick=()=>syncSelectedLayerToEditor(layer); list.appendChild(row);
  });
}
function moveLayer(id,dir){
  const i=sceneLayers.findIndex(l=>l.id===id); if(i<0)return;
  const j=Math.max(0,Math.min(sceneLayers.length-1,i+dir)); if(i===j)return;
  [sceneLayers[i],sceneLayers[j]]=[sceneLayers[j],sceneLayers[i]];
  const l=layerById(id); if(l?.kind==='png') rebuildPngLayers(l.targetModelId); renderLayers();
}
function layerMenu(layer){
  const action=prompt(`Layer: ${layer.name}\nKetik: rename, duplicate, delete`,'rename');
  if(!action)return;
  if(action.toLowerCase()==='rename'){
    const n=prompt('Nama layer',layer.name); if(n?.trim()){layer.name=n.trim(); if(layer.id===selectedLayerId)$('fileLabel').textContent=layer.name; renderLayers()}
  }else if(action.toLowerCase()==='duplicate') duplicateLayer(layer);
  else if(action.toLowerCase()==='delete') deleteLayer(layer);
}
function duplicateLayer(layer){
  if(layer.kind==='model'){
    const clone=layer.object.clone(true); scene.add(clone);
    const copy={...layer,id:newLayerId(),name:layer.name+' Copy',object:clone,locked:false}; sceneLayers.push(copy); syncSelectedLayerToEditor(copy);
  }else{
    const copy={...layer,id:newLayerId(),name:layer.name+' Copy',texture:null,locked:false}; sceneLayers.push(copy); rebuildPngLayers(copy.targetModelId); syncSelectedLayerToEditor(copy);
  }
}
function deleteLayer(layer){
  if(layer.locked){msg('Layer terkunci');return}
  if(!confirm(`Hapus layer ${layer.name}?`))return;
  const wasSelected=layer.id===selectedLayerId;
  if(layer.kind==='model'){
    const pngChildren=sceneLayers.filter(l=>l.kind==='png'&&l.targetModelId===layer.id);
    pngChildren.forEach(p=>p.texture?.dispose?.());
    sceneLayers=sceneLayers.filter(l=>l.id!==layer.id && l.targetModelId!==layer.id);
    disposeLayerObject(layer.object);
  }else{
    const target=layer.targetModelId; layer.texture?.dispose?.(); sceneLayers=sceneLayers.filter(l=>l.id!==layer.id); rebuildPngLayers(target);
  }
  if(wasSelected){const next=[...sceneLayers].reverse().find(l=>l.kind==='model')||sceneLayers.at(-1); selectedLayerId=next?.id||null; if(next)syncSelectedLayerToEditor(next)}
  renderLayers();
}
function addModelLayer(obj,name,format){
  obj.traverse(o=>{
    if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.frustumCulled=false;if(o.geometry&&!o.geometry.getAttribute('normal'))o.geometry.computeVertexNormals();if(Array.isArray(o.material))o.material=o.material.map(m=>normalizeImportedMaterial(m,o));else o.material=normalizeImportedMaterial(o.material,o)}
  });
  scene.add(obj); centerAndFit(obj);
  const layer={id:newLayerId(),kind:'model',format,name,object:obj,visible:true,locked:false,opacity:1};
  sceneLayers.push(layer); syncSelectedLayerToEditor(layer); return layer;
}
async function addPngLayer(file){
  const model=activeModelLayer(); if(!model){throw new Error('Tambahkan FBX/GLB dulu sebelum PNG')}
  const dataUrl=await new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(r.result);r.onerror=()=>rej(new Error('PNG gagal dibaca'));r.readAsDataURL(file)});
  const layer={id:newLayerId(),kind:'png',format:'png',name:file.name,targetModelId:model.id,dataUrl,texture:null,visible:true,locked:false,opacity:1};
  sceneLayers.push(layer); await rebuildPngLayers(model.id); syncSelectedLayerToEditor(layer); return layer;
}
function registerPrimaryLayer(){
  if(!root)return;
  sceneLayers.filter(l=>l.kind==='model'&&l.object!==root).forEach(l=>disposeLayerObject(l.object));
  sceneLayers.forEach(l=>{if(l.kind==='png')l.texture?.dispose?.()});
  sceneLayers=[];
  const ext=(currentFileName.split('.').pop()||'glb').toLowerCase();
  const layer={id:newLayerId(),kind:'model',format:ext,name:currentFileName,object:root,visible:true,locked:false,opacity:1};
  sceneLayers.push(layer); selectedLayerId=layer.id; renderLayers();
}

'''
if func_marker not in s: raise SystemExit('updateMeshSelect marker missing')
s=s.replace(func_marker,layer_funcs+func_marker,1)

reg_marker='  updateMeshSelect();\n  updateTransformFields();\n}\n\nfunction collectLayerMeshes(obj){'
reg_repl='  updateMeshSelect();\n  updateTransformFields();\n  if(!suppressLayerSync) registerPrimaryLayer();\n}\n\nfunction collectLayerMeshes(obj){'
if reg_marker not in s: raise SystemExit('registerModel end marker missing')
s=s.replace(reg_marker,reg_repl,1)

handler_marker="const textureInput=$('textureInput');"
handler=r'''const layerInput=$('layerInput');
layerInput.onchange=async()=>{
  const f=layerInput.files?.[0]; if(!f)return;
  const ext=(f.name.split('.').pop()||'').toLowerCase();
  $('layerStatus').textContent=`Adding ${f.name}...`;
  try{
    if(ext==='png'){
      await addPngLayer(f);
    }else if(ext==='glb'){
      const url=URL.createObjectURL(f);
      try{const gltf=await new Promise((res,rej)=>new GLTFLoader().load(url,res,undefined,rej)); addModelLayer(gltf.scene,f.name,'glb')}finally{URL.revokeObjectURL(url)}
    }else if(ext==='fbx'){
      let loaded=null;
      if(typeof loadFbxWithAssimp==='function'){
        try{const gltf=await loadFbxWithAssimp(f); loaded=gltf.scene||gltf.scenes?.[0]}catch(e){console.warn('Assimp layer fallback',e)}
      }
      if(!loaded){const url=URL.createObjectURL(f);try{loaded=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej))}finally{URL.revokeObjectURL(url)}}
      addModelLayer(loaded,f.name,'fbx');
    }else throw new Error('Format layer tidak didukung');
    $('layerStatus').textContent=`Layer ditambahkan: ${f.name}`; msg('Layer berhasil ditambahkan');
  }catch(e){console.error(e);$('layerStatus').textContent='Gagal add layer: '+e.message;msg('Add Layer gagal')}
  finally{layerInput.value=''}
};
$('layerOpacity').oninput=e=>{
  const layer=selectedLayer(); if(!layer)return;
  if(layer.locked){e.target.value=Math.round((layer.opacity??1)*100);msg('Layer terkunci');return}
  const v=(+e.target.value)/100; setLayerOpacity(layer,v); $('layerOpacityText').textContent=Math.round(v*100)+'%';
};

'''
if handler_marker not in s: raise SystemExit('textureInput marker missing')
s=s.replace(handler_marker,handler+handler_marker,1)

old="""    if(!root)return;\n    root.position.set("""
new="""    if(!root)return;\n    const __layer=selectedLayer(); if(__layer?.locked){msg('Layer terkunci');updateTransformFields();return;}\n    root.position.set("""
if old not in s: raise SystemExit('transform handler marker missing')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('Layers patch applied')