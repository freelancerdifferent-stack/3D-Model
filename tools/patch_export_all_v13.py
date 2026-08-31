from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'EXPORT_ALL_V13' in s:
 print('Export all v13 already applied'); raise SystemExit(0)
css=r'''
/* EXPORT_ALL_V13 */
#exportScreen .export-scope{display:grid;gap:9px;margin-top:10px}
#exportScreen .export-scope-row{display:grid;grid-template-columns:1fr auto;align-items:center;gap:12px;min-height:46px}
#exportScreen .export-scope-row small{display:block;color:var(--muted);margin-top:3px}
#exportScreen .export-check{width:28px;height:28px;border:1px solid #526173;border-radius:7px;background:#17212c;display:grid;place-items:center;font-weight:900;color:transparent}
#exportScreen .export-check.on{background:#347fe7;border-color:#5ba2ff;color:white}
#exportScreen .export-preset{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:12px 0 4px}
#exportScreen .export-preset button{height:42px;border:1px solid #33465b;border-radius:9px;background:#15202b;font-weight:700}
#exportScreen .export-preset button.active{border-color:#4b98ff;background:#1b416c;color:#8fc0ff}
'''
s=s.replace('</style>',css+'\n</style>',1)
js=r'''
// EXPORT_ALL_V13
(function(){
 const screen=$('exportScreen'), oldBtn=$('exportBtn'); if(!screen||!oldBtn)return;
 const status=$('exportStatus');
 const section=document.createElement('div');section.className='section';section.id='exportAllOptions';
 section.innerHTML=`<h3>Export Content</h3>
 <div class="export-preset"><button type="button" id="exportPresetAll" class="active">SAVE / EXPORT ALL</button><button type="button" id="exportPresetCustom">CUSTOM</button></div>
 <div class="export-scope">
  <div class="export-scope-row"><div><b>All Model</b><small>Semua model/object Layers</small></div><button class="export-check on" data-export-key="models">✓</button></div>
  <div class="export-scope-row"><div><b>All Mesh</b><small>Semua geometry/mesh di model yang dipilih</small></div><button class="export-check on" data-export-key="meshes">✓</button></div>
  <div class="export-scope-row"><div><b>All Texture</b><small>Material dan texture yang terpasang</small></div><button class="export-check on" data-export-key="textures">✓</button></div>
  <div class="export-scope-row"><div><b>All Animation</b><small>Semua animation clips</small></div><button class="export-check on" data-export-key="animations">✓</button></div>
  <div class="export-scope-row"><div><b>All UV</b><small>Semua UV attributes pada geometry</small></div><button class="export-check on" data-export-key="uv">✓</button></div>
 </div>`;
 oldBtn.parentNode.insertBefore(section,oldBtn);
 const checks=[...section.querySelectorAll('.export-check')], allBtn=$('exportPresetAll'), customBtn=$('exportPresetCustom');
 const state=()=>Object.fromEntries(checks.map(b=>[b.dataset.exportKey,b.classList.contains('on')]));
 function preset(all){checks.forEach(b=>b.classList.toggle('on',all));allBtn.classList.toggle('active',all);customBtn.classList.toggle('active',!all)}
 allBtn.onclick=()=>preset(true);customBtn.onclick=()=>{customBtn.classList.add('active');allBtn.classList.remove('active')};
 checks.forEach(b=>b.onclick=()=>{b.classList.toggle('on');allBtn.classList.toggle('active',checks.every(x=>x.classList.contains('on')));customBtn.classList.toggle('active',!checks.every(x=>x.classList.contains('on')))});
 function roots(){
   if(typeof sceneLayers!=='undefined'&&Array.isArray(sceneLayers)){
     const a=sceneLayers.filter(l=>l&&l.kind==='model'&&l.object).map(l=>l.object); if(a.length)return a;
   }
   return root?[root]:[];
 }
 function cloneForExport(src,opt){
   const c=src.clone(true);
   c.traverse(o=>{
     if(!o.isMesh)return;
     if(!opt.meshes){o.visible=false;return}
     if(o.geometry){o.geometry=o.geometry.clone();if(!opt.uv){o.geometry.deleteAttribute('uv');o.geometry.deleteAttribute('uv1');o.geometry.deleteAttribute('uv2')}}
     if(o.material){const arr=Array.isArray(o.material)?o.material:[o.material];const mats=arr.map(m=>{const n=m.clone();if(!opt.textures){for(const k in n){const v=n[k];if(v&&v.isTexture)n[k]=null}n.needsUpdate=true}return n});o.material=Array.isArray(o.material)?mats:mats[0]}
   });
   return c;
 }
 async function exportSelective(){
   if(!root){msg('Belum ada model untuk diexport');return}
   const format=document.querySelector('.choice.active')?.dataset.format||'glb';
   if(format==='png'){renderer.render(scene,camera);canvas.toBlob(b=>downloadBlob(b,(currentFileName.replace(/\.[^.]+$/,'')||'snapshot')+'.png'),'image/png');msg('PNG snapshot dibuat');return}
   const opt=state(); if(!opt.models&&!opt.meshes){msg('Aktifkan All Model atau All Mesh');return}
   status.textContent='Membuat GLB...';
   try{
     const src=opt.models?roots():(root?[root]:[]); const exportScene=new THREE.Scene(); src.forEach(x=>exportScene.add(cloneForExport(x,opt)));
     const anims=opt.animations?(typeof sceneLayers!=='undefined'&&Array.isArray(sceneLayers)?sceneLayers.flatMap(l=>l?.object?.animations||[]):clips):[];
     const finalAnims=anims.length?anims:opt.animations?clips:[];
     const out=await new GLTFExporter().parseAsync(exportScene,{binary:true,trs:false,onlyVisible:false,maxTextureSize:4096,animations:finalAnims});
     const suffix=Object.values(opt).every(Boolean)?'_all.glb':'_custom.glb';
     downloadBlob(new Blob([out],{type:'model/gltf-binary'}),(currentFileName.replace(/\.[^.]+$/,'')||'model')+suffix);
     status.textContent=`Selesai • Model ${opt.models?'ALL':'active'} • Mesh ${opt.meshes?'ALL':'OFF'} • Texture ${opt.textures?'ALL':'OFF'} • Animation ${opt.animations?'ALL':'OFF'} • UV ${opt.uv?'ALL':'OFF'}`;msg('GLB berhasil diexport');
   }catch(e){console.error(e);status.textContent='Export gagal: '+e.message;msg('Export gagal')}
 }
 oldBtn.onclick=exportSelective;
 oldBtn.textContent='Save / Export GLB';
})();
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('script end missing')
s=s[:idx]+js+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Export all v13 applied')
