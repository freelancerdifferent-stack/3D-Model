from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'MESH_TRANSFORM_PANEL_V14' in s:
 print('Mesh transform panel v14 already applied'); raise SystemExit(0)
css=r'''
/* MESH_TRANSFORM_PANEL_V14 */
#editorScreen .editor{position:relative}
#editorScreen #liveMoveBtn,#editorScreen #liveRotateBtn,#editorScreen #liveScaleBtn,#editorScreen #frameModel{display:block!important}
#editorScreen .mesh-transform-panel{display:none;position:absolute;left:58px;right:0;bottom:0;z-index:24;background:#0f151c;border-top:1px solid #2a3441;padding:10px 12px 12px;max-height:250px;overflow:auto}
#editorScreen .mesh-transform-panel.on{display:block}
#editorScreen .mesh-transform-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:9px}
#editorScreen .mesh-transform-head b{font-size:14px}
#editorScreen .mesh-transform-name{font-size:11px;color:#79b4ff;max-width:55%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#editorScreen .mesh-transform-close{width:36px;height:32px;border:1px solid #344150;border-radius:8px;background:#18222d}
#editorScreen .mesh-transform-grid{display:grid;grid-template-columns:82px repeat(3,minmax(0,1fr));gap:7px}
#editorScreen .mesh-transform-grid .lab{font-size:11px}
#editorScreen .mesh-adjust{position:relative;min-width:0}
#editorScreen .mesh-adjust input{padding-right:31px}
#editorScreen .mesh-scrub{position:absolute;right:2px;top:2px;bottom:2px;width:27px;border:0;border-left:1px solid #344150;border-radius:0 6px 6px 0;background:#1a2632;color:#83b8ff;touch-action:none;font-size:13px;font-weight:800}
#editorScreen .mesh-scrub.active{background:#28517d;color:white}
#editorScreen .mesh-transform-locked{display:none;margin-top:7px;color:#ffb35f;font-size:11px}
#editorScreen .mesh-transform-locked.on{display:block}
'''
s=s.replace('</style>',css+'\n</style>',1)
js=r'''
// MESH_TRANSFORM_PANEL_V14
(function(){
 const editor=$('editorScreen')?.querySelector('.editor'); if(!editor)return;
 const panel=document.createElement('section');panel.className='mesh-transform-panel';panel.id='meshTransformPanel';
 panel.innerHTML=`<div class="mesh-transform-head"><b>Mesh Transform</b><span class="mesh-transform-name" id="meshTransformName">No Mesh</span><button type="button" class="mesh-transform-close" id="meshTransformClose">⌄</button></div>
 <div class="mesh-transform-grid">
  <div class="lab">Position</div><div class="mesh-adjust"><input class="field" id="mpx"><button class="mesh-scrub" data-mid="mpx">↔</button></div><div class="mesh-adjust"><input class="field" id="mpy"><button class="mesh-scrub" data-mid="mpy">↔</button></div><div class="mesh-adjust"><input class="field" id="mpz"><button class="mesh-scrub" data-mid="mpz">↔</button></div>
  <div class="lab">Rotation</div><div class="mesh-adjust"><input class="field" id="mrx"><button class="mesh-scrub" data-mid="mrx">↔</button></div><div class="mesh-adjust"><input class="field" id="mry"><button class="mesh-scrub" data-mid="mry">↔</button></div><div class="mesh-adjust"><input class="field" id="mrz"><button class="mesh-scrub" data-mid="mrz">↔</button></div>
  <div class="lab">Scale</div><div class="mesh-adjust"><input class="field" id="msx"><button class="mesh-scrub" data-mid="msx">↔</button></div><div class="mesh-adjust"><input class="field" id="msy"><button class="mesh-scrub" data-mid="msy">↔</button></div><div class="mesh-adjust"><input class="field" id="msz"><button class="mesh-scrub" data-mid="msz">↔</button></div>
 </div><div class="mesh-transform-locked" id="meshTransformLocked">🔒 Mesh ini dikunci</div>`;
 editor.appendChild(panel);
 const ids=['mpx','mpy','mpz','mrx','mry','mrz','msx','msy','msz'];
 const inputs=Object.fromEntries(ids.map(id=>[id,$(id)]));
 let opened=false,lastMesh=null,editing=false,before=null;
 function selected(){let m=(typeof liveEditSelectedMeshRef!=='undefined')?liveEditSelectedMeshRef:null;if(!m&&typeof activeMeshLayerIndex!=='undefined'&&activeMeshLayerIndex>=0&&meshList[activeMeshLayerIndex])m=meshList[activeMeshLayerIndex];return m&&m.isMesh?m:null}
 function locked(m){return !!(m&&typeof isMeshPartLocked==='function'&&isMeshPartLocked(m))}
 function snap(m){return window.objectHistorySnapshot?window.objectHistorySnapshot(m):m?{mesh:m,pos:m.position.clone(),quat:m.quaternion.clone(),scale:m.scale.clone()}:null}
 function prepare(m){if(m?.isSkinnedMesh&&typeof liveV6PrepareSkinnedMesh==='function')try{liveV6PrepareSkinnedMesh(m)}catch(_){} }
 function applyMesh(m){if(!m||locked(m))return;prepare(m);m.position.set(parseFloat(inputs.mpx.value)||0,parseFloat(inputs.mpy.value)||0,parseFloat(inputs.mpz.value)||0);m.rotation.set(THREE.MathUtils.degToRad(parseFloat(inputs.mrx.value)||0),THREE.MathUtils.degToRad(parseFloat(inputs.mry.value)||0),THREE.MathUtils.degToRad(parseFloat(inputs.mrz.value)||0));m.scale.set(Math.max(.001,parseFloat(inputs.msx.value)||1),Math.max(.001,parseFloat(inputs.msy.value)||1),Math.max(.001,parseFloat(inputs.msz.value)||1));m.updateMatrix();m.updateMatrixWorld(true);if(m.isSkinnedMesh&&m.skeleton)try{m.skeleton.update()}catch(_){};if(typeof showStrongPartSelection==='function')try{showStrongPartSelection(m)}catch(_){};if(typeof partDragHelper!=='undefined'&&partDragHelper)try{partDragHelper.update()}catch(_){} }
 function write(m){if(!m||editing)return;inputs.mpx.value=m.position.x.toFixed(3);inputs.mpy.value=m.position.y.toFixed(3);inputs.mpz.value=m.position.z.toFixed(3);inputs.mrx.value=THREE.MathUtils.radToDeg(m.rotation.x).toFixed(1);inputs.mry.value=THREE.MathUtils.radToDeg(m.rotation.y).toFixed(1);inputs.mrz.value=THREE.MathUtils.radToDeg(m.rotation.z).toFixed(1);inputs.msx.value=m.scale.x.toFixed(3);inputs.msy.value=m.scale.y.toFixed(3);inputs.msz.value=m.scale.z.toFixed(3);$('meshTransformName').textContent=m.name||('Mesh '+(Math.max(0,meshList.indexOf(m))+1));$('meshTransformLocked').classList.toggle('on',locked(m));ids.forEach(id=>inputs[id].disabled=locked(m));}
 window.syncMeshTransformUI=()=>{const m=selected();if(m)write(m)};
 function open(){const m=selected();if(!liveEditSelectMode||!m){msg('Pilih mesh dulu di Live Edit');return}opened=true;panel.classList.add('on');const props=$('editorScreen').querySelector('.props');if(props)props.style.display='none';$('objectTransformToggle')?.classList.remove('active');const dr=$('objectTrackpadDrawer');if(dr)dr.classList.add('collapsed');write(m)}
 function close(){opened=false;panel.classList.remove('on')}
 $('meshTransformClose').onclick=close;
 ['liveMoveBtn','liveRotateBtn','liveScaleBtn'].forEach(id=>$(id)?.addEventListener('click',()=>setTimeout(open,0)));
 $('objectTransformToggle')?.addEventListener('click',close);
 inputs && ids.forEach(id=>{const el=inputs[id];el.addEventListener('focus',()=>{const m=selected();if(!m)return;editing=true;before=snap(m)});el.addEventListener('change',()=>{const m=selected();if(!m)return;applyMesh(m);const after=snap(m);if(before&&window.objectHistoryPush)window.objectHistoryPush(before,after,'Mesh Transform');before=null;editing=false;write(m)});el.addEventListener('blur',()=>{editing=false})});
 const cfg={mpx:[.005,3],mpy:[.005,3],mpz:[.005,3],mrx:[.25,1],mry:[.25,1],mrz:[.25,1],msx:[.005,3],msy:[.005,3],msz:[.005,3]};
 panel.querySelectorAll('.mesh-scrub').forEach(btn=>{let pid=null,sx=0,sv=0,moved=false;btn.addEventListener('pointerdown',e=>{const m=selected();if(!m||locked(m))return;e.preventDefault();e.stopPropagation();editing=true;before=snap(m);pid=e.pointerId;sx=e.clientX;sv=parseFloat(inputs[btn.dataset.mid].value)||0;moved=false;btn.classList.add('active');try{btn.setPointerCapture(pid)}catch(_){}});btn.addEventListener('pointermove',e=>{if(pid!==e.pointerId)return;e.preventDefault();const id=btn.dataset.mid,[step,dec]=cfg[id];const dx=e.clientX-sx;if(Math.abs(dx)>1)moved=true;let v=sv+dx*step;if(id.startsWith('ms'))v=Math.max(.001,v);inputs[id].value=v.toFixed(dec);applyMesh(selected())});const end=e=>{if(pid===null||(e.pointerId!=null&&e.pointerId!==pid))return;try{btn.releasePointerCapture(pid)}catch(_){}pid=null;btn.classList.remove('active');const m=selected();if(moved&&before&&m&&window.objectHistoryPush)window.objectHistoryPush(before,snap(m),'Mesh Transform');before=null;editing=false;if(m)write(m)};btn.addEventListener('pointerup',end);btn.addEventListener('pointercancel',end)});
 setInterval(()=>{const m=selected();if(m!==lastMesh){lastMesh=m;if(opened&&m)write(m)}if(opened){if(!liveEditSelectMode||!m)close();else write(m)}},120);
})();
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('script end missing')
s=s[:idx]+js+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Mesh Transform panel v14 applied')
