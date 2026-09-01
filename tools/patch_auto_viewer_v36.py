from pathlib import Path

p=Path('app/src/main/assets/auto.html')
s=p.read_text(encoding='utf-8')
if 'AUTO_MACHINE_RUNTIME_V35' not in s: raise SystemExit('Auto machine v35 must run first')
if 'AUTO_VIEWER_V37' in s: raise SystemExit(0)

css=r'''
/* AUTO_VIEWER_V37 */
html[data-object-machine="auto"] #editorScreen .viewport{background:#17191b}
html[data-object-machine="auto"] #threeCanvas{display:none!important}
html[data-object-machine="auto"] #autoViewerCanvasV37{position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:none;z-index:1}
html[data-object-machine="auto"] #editorScreen .overleft{display:none!important}
html[data-object-machine="auto"] #editorScreen .overright,html[data-object-machine="auto"] #editorScreen .viewtools,html[data-object-machine="auto"] #editorScreen .timeline{z-index:4}
html[data-object-machine="auto"] #autoViewerAnimBarV37{position:absolute;z-index:7;left:14px;top:12px;display:flex;gap:9px;align-items:center}
html[data-object-machine="auto"] #autoViewerAnimBarV37 .anim-shell{display:flex;align-items:center;width:min(260px,55vw);height:48px;padding:0 12px;border-radius:15px;background:#242424e8;border:1px solid #313131}
html[data-object-machine="auto"] #autoViewerAnimBarV37 select{width:100%;border:0;background:transparent;color:#fff;outline:none}
html[data-object-machine="auto"] #autoViewerDownloadV37{width:48px;height:48px;border:0;border-radius:13px;background:#baff36;color:#071006;font-size:22px;font-weight:900}
html[data-object-machine="auto"] #autoViewerClipBarV37{position:absolute;z-index:7;left:12px;right:12px;bottom:16px;height:50px;display:flex;align-items:center;gap:12px;padding:0 12px;background:#151515dd;border-top:1px solid #242a31}
html[data-object-machine="auto"] #autoViewerClipSourceV37{margin-left:auto;color:#73777d;max-width:45%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
'''
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// AUTO_VIEWER_V37 — dedicated Auto-owned renderer/scene/camera/model/animation.
window.__autoMachineRuntimeV35.viewerEngine=true;
window.__autoMachineRuntimeV35.viewerEngineVersion='v37-dedicated-auto';
window.__autoViewerRuntimeV37={owner:'auto',isolated:true,crossModeBridge:false,sharesRenderer:false,sharesScene:false,sharesCamera:false,sharesModelState:false};
requestAnimationFrame(()=>{
 const editor=$('editorScreen'), viewport=editor?.querySelector('.viewport'), sourceSelect=$('animSelect');
 if(!editor||!viewport||!sourceSelect)return;

 const c=document.createElement('canvas'); c.id='autoViewerCanvasV37'; viewport.prepend(c);
 const autoRenderer=new THREE.WebGLRenderer({canvas:c,antialias:true,preserveDrawingBuffer:true,alpha:false});
 autoRenderer.setPixelRatio(Math.min(devicePixelRatio,2)); autoRenderer.outputColorSpace=THREE.SRGBColorSpace; autoRenderer.toneMapping=THREE.ACESFilmicToneMapping; autoRenderer.toneMappingExposure=1.45; autoRenderer.shadowMap.enabled=true;
 const autoScene=new THREE.Scene(); autoScene.background=new THREE.Color(0x20262e);
 const autoCamera=new THREE.PerspectiveCamera(45,1,.01,10000); autoCamera.position.set(3,2.4,4.2);
 const autoControls=new OrbitControls(autoCamera,c); autoControls.enableDamping=true; autoControls.dampingFactor=.08;
 const aa=new THREE.AmbientLight(0xffffff,2.2), ah=new THREE.HemisphereLight(0xffffff,0x667788,2.4), ak=new THREE.DirectionalLight(0xffffff,4.2), af=new THREE.DirectionalLight(0xffffff,2); ak.position.set(4,7,5); af.position.set(-4,3,-2); autoScene.add(aa,ah,ak,af);
 const autoGrid=new THREE.GridHelper(20,20,0x4b5968,0x35404d); autoScene.add(autoGrid);
 let autoRoot=null,autoMeshes=[],autoMixer=null,autoClips=[],autoAction=null,autoPlaying=false,autoClock=new THREE.Clock(),loadedKey='';

 const fit=()=>{if(!autoRoot)return;autoRoot.updateMatrixWorld(true);let b=new THREE.Box3().setFromObject(autoRoot),sz=b.getSize(new THREE.Vector3()),ct=b.getCenter(new THREE.Vector3());autoRoot.position.x-=ct.x;autoRoot.position.z-=ct.z;autoRoot.position.y-=b.min.y;autoRoot.updateMatrixWorld(true);b=new THREE.Box3().setFromObject(autoRoot);autoRoot.position.y-=b.min.y;autoRoot.updateMatrixWorld(true);b=new THREE.Box3().setFromObject(autoRoot);sz=b.getSize(new THREE.Vector3());const m=Math.max(sz.x,sz.y,sz.z)||1,d=m*2.3;autoCamera.position.set(d*.85,Math.max(sz.y*.55,m*.45),d);autoControls.target.set(0,Math.max(sz.y*.45,0),0);autoCamera.near=Math.max(.001,m/1000);autoCamera.far=Math.max(1000,m*100);autoCamera.updateProjectionMatrix();autoControls.update();autoGrid.position.y=0};
 const dispose=()=>{if(autoRoot){autoScene.remove(autoRoot);autoRoot.traverse(o=>{o.geometry?.dispose?.();const ms=Array.isArray(o.material)?o.material:[o.material];ms.forEach(m=>m?.dispose?.())})}autoRoot=null;autoMeshes=[];autoMixer=null;autoClips=[];autoAction=null;autoPlaying=false};
 const setModel=(obj,name,animations=[])=>{dispose();autoRoot=obj;autoScene.add(obj);obj.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;autoMeshes.push(o);if(o.material){const ms=Array.isArray(o.material)?o.material:[o.material];ms.forEach(m=>{if(m){m.side=THREE.DoubleSide;m.needsUpdate=true}})}}});autoClips=animations||[];fit();$('meshLabel').textContent=autoMeshes.length+' Mesh';$('fileLabel').textContent=name;sourceSelect.innerHTML='';if(autoClips.length){autoMixer=new THREE.AnimationMixer(autoRoot);autoClips.forEach((x,i)=>{const o=document.createElement('option');o.value=i;o.textContent=x.name?.trim()?`${i+1}. ${x.name}`:`Animation ${i+1}`;sourceSelect.appendChild(o)});autoAction=autoMixer.clipAction(autoClips[0]);autoAction.play();autoMixer.timeScale=0;$('durationText').textContent=autoClips[0].duration.toFixed(2)+'s'}else{const o=document.createElement('option');o.value='';o.textContent='No Animation';sourceSelect.appendChild(o);$('durationText').textContent='0s'};syncClip()};
 const loadAuto=async()=>{const f=$('modelInput')?.files?.[0];if(!f)return;const key=f.name+':'+f.size+':'+f.lastModified;if(key===loadedKey&&autoRoot)return;loadedKey=key;const ext=f.name.split('.').pop().toLowerCase();try{if(ext==='glb'){const u=URL.createObjectURL(f);try{const g=await new Promise((r,j)=>new GLTFLoader().load(u,r,undefined,j));setModel(g.scene,f.name,g.animations)}finally{URL.revokeObjectURL(u)}}else if(ext==='fbx'){const g=await loadFbxWithAssimp(f);setModel(g.scene,f.name,g.animations||[])} }catch(e){loadedKey='';console.error('Auto Viewer load failed',e);msg('Auto Viewer gagal memuat model: '+e.message)}};
 const resizeAuto=()=>{const r=c.getBoundingClientRect();if(!r.width||!r.height)return;autoRenderer.setSize(r.width,r.height,false);autoCamera.aspect=r.width/r.height;autoCamera.updateProjectionMatrix()}; new ResizeObserver(resizeAuto).observe(viewport);

 const oldWrap=sourceSelect.parentElement,bar=document.createElement('div');bar.id='autoViewerAnimBarV37';bar.innerHTML='<div class="anim-shell"></div><button id="autoViewerDownloadV37" type="button">⇩</button>';viewport.appendChild(bar);bar.querySelector('.anim-shell').appendChild(sourceSelect);if(oldWrap&&oldWrap.children.length===0)oldWrap.remove();
 const cb=document.createElement('div');cb.id='autoViewerClipBarV37';cb.innerHTML='<span>⌄</span><span id="autoViewerClipNameV37">No Animation</span><span id="autoViewerClipSourceV37">No model loaded</span>';viewport.appendChild(cb);
 function syncClip(){const l=$('autoViewerClipNameV37'),q=$('autoViewerClipSourceV37');if(l)l.textContent=sourceSelect.options[sourceSelect.selectedIndex]?.textContent||'No Animation';if(q)q.textContent=$('fileLabel')?.textContent||'No model loaded'}
 sourceSelect.onchange=()=>{if(!autoMixer||!autoClips.length)return;autoMixer.stopAllAction();autoAction=autoMixer.clipAction(autoClips[+sourceSelect.value||0]);autoAction.reset().play();autoMixer.timeScale=autoPlaying?1:0;$('durationText').textContent=autoClips[+sourceSelect.value||0].duration.toFixed(2)+'s';syncClip()};
 $('playBtn').onclick=()=>{if(!autoMixer||!autoAction){msg('Model tidak punya animasi');return}autoPlaying=!autoPlaying;autoMixer.timeScale=autoPlaying?1:0;$('playBtn').textContent=autoPlaying?'❚❚':'▶'};
 $('animRange').oninput=()=>{if(!autoMixer||!autoClips.length)return;const d=autoClips[+sourceSelect.value||0].duration;autoMixer.setTime((+$('animRange').value/100)*d)};
 $('wireBtn').onclick=()=>{const on=$('wireBtn').classList.toggle('on');autoMeshes.forEach(x=>(Array.isArray(x.material)?x.material:[x.material]).forEach(m=>{if(m){m.wireframe=on;m.needsUpdate=true}}))};
 $('gridBtn').onclick=()=>autoGrid.visible=$('gridBtn').classList.toggle('on');
 $('lightBtn').onclick=()=>{const on=$('lightBtn').classList.toggle('on');aa.visible=ah.visible=ak.visible=af.visible=on};
 $('safeBtn').onclick=()=>{if(autoRoot)autoRoot.visible=!autoRoot.visible};
 $('frameModel').onclick=fit;
 $('autoViewerDownloadV37').onclick=()=>$('exportBtn')?.click();

 const viewer=$('autoViewerNavV35'),nav=document.querySelector('.bottomnav');
 const activate=()=>{nav?.querySelectorAll('.nav').forEach(x=>x.classList.remove('active'));viewer?.classList.add('active');go('editorScreen');requestAnimationFrame(()=>{resizeAuto();loadAuto()})}; if(viewer)viewer.onclick=activate;
 new MutationObserver(()=>{if(editor.classList.contains('active'))activate()}).observe(editor,{attributes:true,attributeFilter:['class']});
 function loop(){requestAnimationFrame(loop);const dt=autoClock.getDelta();if(autoMixer&&autoPlaying)autoMixer.update(dt);autoControls.update();autoRenderer.render(autoScene,autoCamera)}resizeAuto();loop();
});
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('module script missing')
s=s[:idx]+js+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('AUTO_VIEWER_V37 dedicated Auto engine installed')
