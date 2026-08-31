from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_SELECT_V1' in s:
    print('Live Edit Select already applied'); raise SystemExit(0)

# Give the existing upper-left Select button a stable id. Do not create another Select button.
old='<button class="tool active"><b>➤</b>Select</button>'
new='<button class="tool" id="liveEditSelectBtn"><b>➤</b>Select</button>'
if old not in s: raise SystemExit('Existing Select tool marker missing')
s=s.replace(old,new,1)

# Manual camera pan pad shown only while Select/Live Edit is active.
vp='<canvas id="threeCanvas"></canvas>'
ui=r'''<canvas id="threeCanvas"></canvas>
          <!-- LIVE_EDIT_SELECT_V1 -->
          <div id="liveEditBadge" class="live-edit-badge">LIVE EDIT</div>
          <div id="livePanPad" class="live-pan-pad" aria-label="Manual camera pan">
            <button type="button" data-pan="up">▲</button>
            <div><button type="button" data-pan="left">◀</button><button type="button" data-pan="right">▶</button></div>
            <button type="button" data-pan="down">▼</button>
          </div>'''
if vp not in s: raise SystemExit('viewport canvas marker missing')
s=s.replace(vp,ui,1)

css_marker='#threeCanvas{width:100%;height:100%;display:block;touch-action:none}'
css=css_marker+r'''
/* LIVE_EDIT_SELECT_V1 */
.live-edit-badge{display:none;position:absolute;left:50%;top:10px;transform:translateX(-50%);z-index:8;padding:6px 10px;border:1px solid #3d8bfd;border-radius:999px;background:rgba(12,28,48,.92);color:#70b2ff;font-size:10px;font-weight:800;letter-spacing:.08em;pointer-events:none}
.live-edit-badge.on{display:block}
.live-pan-pad{display:none;position:absolute;right:12px;bottom:64px;z-index:9;width:126px;text-align:center;padding:6px;border:1px solid #34485f;border-radius:14px;background:rgba(10,18,27,.88)}
.live-pan-pad.on{display:block}
.live-pan-pad>button,.live-pan-pad div button{width:46px;height:42px;margin:2px;border:1px solid #3b4b5d;border-radius:9px;background:#152231;color:#dce9f8;font-size:18px}
.live-pan-pad div{display:flex;justify-content:center}
#liveEditSelectBtn.active{background:#193454;color:#69adff;box-shadow:inset 0 0 0 1px #326aa4}
'''
if css_marker not in s: raise SystemExit('canvas CSS marker missing')
s=s.replace(css_marker,css,1)

# Insert behavior late in the module, before animation loop marker used by the base editor.
marker='function animate(){'
if marker not in s: raise SystemExit('animate marker missing')
js=r'''// LIVE_EDIT_SELECT_V1
let liveEditSelectMode=false;
let liveEditPointerId=null;
let liveEditDownX=0,liveEditDownY=0;

function setLiveEditSelectMode(on){
  liveEditSelectMode=!!on;
  const btn=$('liveEditSelectBtn');
  if(btn)btn.classList.toggle('active',liveEditSelectMode);
  $('liveEditBadge')?.classList.toggle('on',liveEditSelectMode);
  $('livePanPad')?.classList.toggle('on',liveEditSelectMode);
  // Select is an explicit portal: camera gestures are fully disabled while editing.
  controls.enabled=!liveEditSelectMode;
  if(liveEditSelectMode){
    try{cancelPartLongPress()}catch(_){ }
    try{closePartContextMenu()}catch(_){ }
    msg('Live Edit aktif — sentuh part untuk memilih. Kamera: tombol pan manual.');
  }else{
    try{finishPartDrag()}catch(_){ }
    try{finishPartTransform()}catch(_){ }
    msg('Live Edit nonaktif — OrbitControls aktif kembali');
  }
}

function liveEditPick(clientX,clientY){
  if(!liveEditSelectMode)return;
  const hit=(typeof partPickAt==='function')?partPickAt(clientX,clientY):null;
  if(!hit||!hit.object){msg('Tidak ada part pada titik ini');return}
  const mesh=hit.object;
  if(typeof isMeshPartLocked==='function' && isMeshPartLocked(mesh)){
    msg('Part ini dikunci');return;
  }
  const index=meshList.indexOf(mesh);
  if(index<0)return;
  activeMeshLayerIndex=index;
  if(typeof showStrongPartSelection==='function')showStrongPartSelection(mesh);
  else if(typeof showPartDragSelection==='function')showPartDragSelection(mesh);
  if(typeof renderMeshLayers==='function')renderMeshLayers();
  if(typeof updateMeshSelect==='function')updateMeshSelect();
  msg('Part dipilih: '+(typeof meshLayerDisplayName==='function'?meshLayerDisplayName(mesh,index):(mesh.name||('Mesh '+(index+1)))));
}

// In Live Edit, a short tap selects a part. Capture phase prevents old transform/long-press handlers
// from stealing the selection gesture.
canvas.addEventListener('pointerdown',ev=>{
  if(!liveEditSelectMode)return;
  if(ev.pointerType==='mouse'&&ev.button!==0)return;
  liveEditPointerId=ev.pointerId;liveEditDownX=ev.clientX;liveEditDownY=ev.clientY;
  ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
},{capture:true});
canvas.addEventListener('pointerup',ev=>{
  if(!liveEditSelectMode||ev.pointerId!==liveEditPointerId)return;
  const moved=Math.hypot(ev.clientX-liveEditDownX,ev.clientY-liveEditDownY);
  liveEditPointerId=null;
  ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
  if(moved<18)liveEditPick(ev.clientX,ev.clientY);
},{capture:true});
canvas.addEventListener('pointercancel',()=>{liveEditPointerId=null},{capture:true});

$('liveEditSelectBtn').onclick=()=>setLiveEditSelectMode(!liveEditSelectMode);

// Manual horizontal/vertical camera pan. Move camera and OrbitControls target together,
// preserving current viewing angle and distance.
function liveEditPan(dx,dy){
  if(!liveEditSelectMode)return;
  const dist=Math.max(.1,camera.position.distanceTo(controls.target));
  const step=dist*.055;
  const right=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,0).normalize();
  const up=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,1).normalize();
  const delta=right.multiplyScalar(dx*step).add(up.multiplyScalar(dy*step));
  camera.position.add(delta);controls.target.add(delta);camera.updateMatrixWorld(true);
}
$('livePanPad').querySelectorAll('[data-pan]').forEach(btn=>{
  const run=()=>{
    const d=btn.dataset.pan;
    if(d==='left')liveEditPan(-1,0);else if(d==='right')liveEditPan(1,0);else if(d==='up')liveEditPan(0,1);else liveEditPan(0,-1);
  };
  let timer=null;
  btn.addEventListener('pointerdown',ev=>{ev.preventDefault();ev.stopPropagation();run();timer=setInterval(run,80)});
  const stop=()=>{if(timer){clearInterval(timer);timer=null}};
  btn.addEventListener('pointerup',stop);btn.addEventListener('pointercancel',stop);btn.addEventListener('pointerleave',stop);
});

'''
s=s.replace(marker,js+marker,1)
p.write_text(s,encoding='utf-8')
print('Existing Select tool converted to Live Edit portal')
