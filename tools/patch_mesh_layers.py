from pathlib import Path

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

if 'id="meshLayersScreen"' in s:
    print('Mesh Layers patch already applied')
    raise SystemExit(0)

css_marker = '.hidden{display:none!important}'
css = '''\n.mesh-layers-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px}\n.mesh-layers-list{display:flex;flex-direction:column;gap:7px;margin-top:12px}\n.mesh-layer-item{display:grid;grid-template-columns:38px minmax(0,1fr) 58px;gap:8px;align-items:center;background:#111924;border:1px solid #283544;border-radius:11px;padding:8px}\n.mesh-layer-item.active{border-color:#4c9cff;background:#15243a;box-shadow:0 0 0 1px rgba(76,156,255,.18) inset}\n.mesh-layer-eye{height:36px;width:38px;border:0;border-radius:8px;background:#0c141d;color:#dce5ef;font-size:15px}.mesh-layer-eye.off{opacity:.42}\n.mesh-layer-main{min-width:0}.mesh-layer-name{font-weight:650;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.mesh-layer-meta{font-size:11px;color:var(--muted);margin-top:3px}\n.mesh-layer-select{height:34px;border:1px solid #34506f;border-radius:8px;background:#14263b;color:#79b5ff;font-size:11px}\n.mesh-layer-empty{padding:24px 12px;text-align:center;color:var(--muted);border:1px dashed #354251;border-radius:12px}\n'''
if css_marker not in s:
    raise SystemExit('CSS marker missing')
s = s.replace(css_marker, css_marker + css, 1)

screen_marker = '    <section class="screen form" id="exportScreen">'
mesh_screen = '''    <section class="screen form" id="meshLayersScreen">\n      <div class="head"><button class="back" data-go="editorScreen">←</button><h2>Mesh Layers</h2></div>\n      <div class="mesh-layers-head">\n        <div><b id="meshLayersModelName">No model loaded</b><div style="font-size:11px;color:var(--muted);margin-top:3px">Bagian-bagian mesh di dalam model aktif</div></div>\n        <span class="pill" id="meshLayersCount">0 Mesh</span>\n      </div>\n      <div class="status" id="meshLayersStatus">Pilih satu mesh untuk dijadikan target Material & Texture.</div>\n      <div class="mesh-layers-list" id="meshLayersList"><div class="mesh-layer-empty">Import FBX/GLB dulu.</div></div>\n      <button class="primary" id="meshLayersEditBtn">Edit Selected Material / Texture</button>\n    </section>\n\n'''
if screen_marker not in s:
    raise SystemExit('Export screen marker missing')
s = s.replace(screen_marker, mesh_screen + screen_marker, 1)

# Add a dedicated navigation item without changing the existing Layers screen.
nav_marker = '    <button class="nav" data-go="layersScreen"><b>▤</b>Layers</button>\n    <button class="nav" data-go="exportScreen"><b>⇧</b>Export</button>'
nav_repl = '    <button class="nav" data-go="layersScreen"><b>▤</b>Layers</button>\n    <button class="nav" id="meshLayersNav" data-go="meshLayersScreen"><b>≣</b>Mesh</button>\n    <button class="nav" data-go="exportScreen"><b>⇧</b>Export</button>'
if nav_marker not in s:
    raise SystemExit('Layers navigation marker missing')
s = s.replace(nav_marker, nav_repl, 1)

# Increase bottom-nav columns only to make room for the new independent feature.
s = s.replace('grid-template-columns:repeat(6,1fr);background:#0f151c', 'grid-template-columns:repeat(7,1fr);background:#0f151c', 1)

func_marker = 'function updateMeshSelect(){'
mesh_funcs = r'''let activeMeshLayerIndex=-1;
function meshLayerDisplayName(mesh,index){
  const raw=(mesh?.name||'').trim();
  return raw || `Mesh ${index+1}`;
}
function selectMeshLayer(index){
  index=Number(index);
  if(!Number.isInteger(index) || !meshList[index]) return;
  activeMeshLayerIndex=index;
  const target=$('targetMesh');
  if(target) target.value=String(index);
  const mesh=meshList[index];
  $('meshLayersStatus').textContent=`Target aktif: ${meshLayerDisplayName(mesh,index)} • Material/Texture hanya diterapkan ke mesh ini.`;
  renderMeshLayers();
}
function toggleMeshLayerVisibility(index){
  const mesh=meshList[index]; if(!mesh)return;
  mesh.visible=!mesh.visible;
  renderMeshLayers();
}
function renderMeshLayers(){
  const list=$('meshLayersList'); if(!list)return;
  const count=meshList?.length||0;
  $('meshLayersCount').textContent=`${count} Mesh`;
  $('meshLayersModelName').textContent=currentFileName||'No model loaded';
  if(!count){
    activeMeshLayerIndex=-1;
    list.innerHTML='<div class="mesh-layer-empty">Import FBX/GLB dulu.</div>';
    $('meshLayersStatus').textContent='Belum ada mesh untuk ditampilkan.';
    return;
  }
  const target=$('targetMesh');
  const targetValue=target?.value;
  if(targetValue!==undefined && targetValue!=='all' && meshList[Number(targetValue)]) activeMeshLayerIndex=Number(targetValue);
  list.innerHTML='';
  meshList.forEach((mesh,index)=>{
    const row=document.createElement('div');
    row.className='mesh-layer-item'+(index===activeMeshLayerIndex?' active':'');
    const eye=document.createElement('button');
    eye.className='mesh-layer-eye'+(mesh.visible?'':' off');
    eye.textContent=mesh.visible?'👁':'◌';
    eye.title=mesh.visible?'Hide mesh':'Show mesh';
    eye.onclick=e=>{e.stopPropagation();toggleMeshLayerVisibility(index)};
    const main=document.createElement('div');
    main.className='mesh-layer-main';
    const type=mesh.isSkinnedMesh?'Skinned Mesh':'Mesh';
    main.innerHTML='<div class="mesh-layer-name"></div><div class="mesh-layer-meta"></div>';
    main.querySelector('.mesh-layer-name').textContent=meshLayerDisplayName(mesh,index);
    main.querySelector('.mesh-layer-meta').textContent=`${index+1} • ${type}${mesh.material?.name?' • '+mesh.material.name:''}`;
    const pick=document.createElement('button');
    pick.className='mesh-layer-select';
    pick.textContent=index===activeMeshLayerIndex?'ACTIVE':'SELECT';
    pick.onclick=e=>{e.stopPropagation();selectMeshLayer(index)};
    row.onclick=()=>selectMeshLayer(index);
    row.append(eye,main,pick);
    list.appendChild(row);
  });
}
function refreshMeshLayersAfterModelChange(){
  activeMeshLayerIndex=-1;
  renderMeshLayers();
}

'''
if func_marker not in s:
    raise SystemExit('updateMeshSelect marker missing')
s = s.replace(func_marker, mesh_funcs + func_marker, 1)

# Keep Mesh Layers synchronized whenever the regular target dropdown is rebuilt.
update_select_end = "  meshList.forEach((m,i)=>{ const o=document.createElement('option'); o.value=String(i); o.textContent=m.name||`Mesh ${i+1}`; s.appendChild(o); });\n}"
update_select_repl = "  meshList.forEach((m,i)=>{ const o=document.createElement('option'); o.value=String(i); o.textContent=m.name||`Mesh ${i+1}`; s.appendChild(o); });\n  refreshMeshLayersAfterModelChange();\n}"
if update_select_end not in s:
    raise SystemExit('updateMeshSelect body marker missing')
s = s.replace(update_select_end, update_select_repl, 1)

# Sync dropdown changes made from Material screen back to Mesh Layers.
get_targets_marker = "function getTargets(){\n  const v=$('targetMesh').value;"
get_targets_repl = "$('targetMesh').addEventListener('change',()=>{\n  const v=$('targetMesh').value;\n  activeMeshLayerIndex=(v==='all')?-1:Number(v);\n  renderMeshLayers();\n});\nfunction getTargets(){\n  const v=$('targetMesh').value;"
if get_targets_marker not in s:
    raise SystemExit('getTargets marker missing')
s = s.replace(get_targets_marker, get_targets_repl, 1)

# Render immediately when opening the dedicated screen and jump to Material on request.
handler_marker = "const textureInput=$('textureInput');"
handler = r'''$('meshLayersNav').addEventListener('click',()=>renderMeshLayers());
$('meshLayersEditBtn').onclick=()=>{
  if(activeMeshLayerIndex<0 || !meshList[activeMeshLayerIndex]){msg('Pilih satu mesh dulu');return}
  $('targetMesh').value=String(activeMeshLayerIndex);
  go('materialScreen');
  msg('Target material: '+meshLayerDisplayName(meshList[activeMeshLayerIndex],activeMeshLayerIndex));
};

'''
if handler_marker not in s:
    raise SystemExit('textureInput marker missing')
s = s.replace(handler_marker, handler + handler_marker, 1)

p.write_text(s, encoding='utf-8')
print('Mesh Layers patch applied')
