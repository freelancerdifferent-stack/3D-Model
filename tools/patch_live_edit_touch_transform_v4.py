from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_TOUCH_TRANSFORM_V4' in s:
    print('Live Edit touch transform v4 already applied'); raise SystemExit(0)

marker='// Manual horizontal/vertical camera pan. Move camera and OrbitControls target together,'
if marker not in s: raise SystemExit('Live Edit insertion marker missing')

js=r'''// LIVE_EDIT_TOUCH_TRANSFORM_V4
// Final Android touch path: the VIEWPORT capture listener owns Move/Rotate/Scale
// before any canvas/OrbitControls/legacy part handler can consume the gesture.
let liveV4PointerId=null;
let liveV4Mesh=null;
let liveV4StartX=0,liveV4StartY=0;
let liveV4StartPos=null,liveV4StartRot=null,liveV4StartScale=null;
let liveV4RightLocal=null,liveV4UpLocal=null;

function liveV4SelectedMesh(){
  let mesh=(typeof liveEditSelectedMeshRef!=='undefined')?liveEditSelectedMeshRef:null;
  if(!mesh && activeMeshLayerIndex>=0)mesh=meshList[activeMeshLayerIndex];
  if(!mesh || !mesh.isMesh || !mesh.visible)return null;
  if(typeof isMeshPartLocked==='function' && isMeshPartLocked(mesh))return null;
  return mesh;
}
function liveV4Stop(){
  if(liveV4PointerId!==null){try{canvas.releasePointerCapture(liveV4PointerId)}catch(_){ }}
  liveV4PointerId=null;liveV4Mesh=null;
  liveV4StartPos=liveV4StartRot=liveV4StartScale=null;
  liveV4RightLocal=liveV4UpLocal=null;
  controls.enabled=!liveEditSelectMode;
}
function liveV4Begin(ev){
  if(!liveEditSelectMode || !liveEditTransformMode)return false;
  if(ev.target!==canvas)return false;
  if(ev.pointerType==='mouse' && ev.button!==0)return false;
  const mesh=liveV4SelectedMesh();
  if(!mesh){msg('Pilih part dulu dengan Select');return true;}
  liveV4PointerId=ev.pointerId;liveV4Mesh=mesh;
  liveV4StartX=ev.clientX;liveV4StartY=ev.clientY;
  liveV4StartPos=mesh.position.clone();
  liveV4StartRot=mesh.rotation.clone();
  liveV4StartScale=mesh.scale.clone();
  camera.updateMatrixWorld(true);
  const rightW=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,0).normalize();
  const upW=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,1).normalize();
  if(mesh.parent){
    mesh.parent.updateMatrixWorld(true);
    const invQ=mesh.parent.getWorldQuaternion(new THREE.Quaternion()).invert();
    liveV4RightLocal=rightW.clone().applyQuaternion(invQ);
    liveV4UpLocal=upW.clone().applyQuaternion(invQ);
  }else{liveV4RightLocal=rightW;liveV4UpLocal=upW;}
  controls.enabled=false;
  try{canvas.setPointerCapture(ev.pointerId)}catch(_){ }
  if(typeof showStrongPartSelection==='function')showStrongPartSelection(mesh);
  return true;
}
function liveV4Apply(ev){
  if(ev.pointerId!==liveV4PointerId || !liveV4Mesh)return false;
  const mesh=liveV4Mesh;
  if(typeof isMeshPartLocked==='function' && isMeshPartLocked(mesh)){liveV4Stop();msg('Part ini dikunci');return true;}
  const dx=ev.clientX-liveV4StartX,dy=ev.clientY-liveV4StartY;
  if(liveEditTransformMode==='move'){
    const dist=Math.max(.1,camera.position.distanceTo(controls.target));
    const k=dist*.0028;
    const d=liveV4RightLocal.clone().multiplyScalar(dx*k).add(liveV4UpLocal.clone().multiplyScalar(-dy*k));
    mesh.position.copy(liveV4StartPos).add(d);
  }else if(liveEditTransformMode==='rotate'){
    mesh.rotation.copy(liveV4StartRot);
    mesh.rotation.y += dx*0.012;
    mesh.rotation.x += dy*0.012;
  }else if(liveEditTransformMode==='scale'){
    const factor=Math.max(.05,Math.min(20,Math.exp(-dy*0.010)));
    mesh.scale.set(liveV4StartScale.x*factor,liveV4StartScale.y*factor,liveV4StartScale.z*factor);
  }
  mesh.updateMatrixWorld(true);
  if(partDragHelper){try{partDragHelper.update()}catch(_){ }}
  return true;
}

const liveV4Surface=canvas.parentElement;
liveV4Surface.addEventListener('pointerdown',ev=>{
  if(!liveV4Begin(ev))return;
  ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
},{capture:true});
liveV4Surface.addEventListener('pointermove',ev=>{
  if(!liveV4Apply(ev))return;
  ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
},{capture:true});
liveV4Surface.addEventListener('pointerup',ev=>{
  if(ev.pointerId!==liveV4PointerId)return;
  liveV4Apply(ev);liveV4Stop();
  ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
},{capture:true});
liveV4Surface.addEventListener('pointercancel',ev=>{
  if(ev.pointerId!==liveV4PointerId)return;
  liveV4Stop();
  ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
},{capture:true});

// Replace toolbar activation with a minimal state change. Legacy part modes are
// explicitly switched off so they cannot fight the dedicated Live Edit path.
function liveV4SetMode(mode){
  if(!liveEditSelectMode){msg('Tekan Select dulu untuk masuk Live Edit');controls.enabled=true;return;}
  const mesh=liveV4SelectedMesh();
  if(!mesh){msg('Pilih part dulu dengan Select');return;}
  try{setExclusivePartMode('move',false)}catch(_){ }
  liveEditTransformMode=mode;
  liveEditSelectedMeshRef=mesh;
  controls.enabled=false;
  updateLiveEditToolUI();
  if(typeof showStrongPartSelection==='function')showStrongPartSelection(mesh);
  msg((mode==='move'?'Move':mode==='rotate'?'Rotate':'Scale')+' aktif — sentuh lalu drag di preview');
}
$('liveMoveBtn').onclick=()=>liveV4SetMode('move');
$('liveRotateBtn').onclick=()=>liveV4SetMode('rotate');
$('liveScaleBtn').onclick=()=>liveV4SetMode('scale');

'''
s=s.replace(marker,js+marker,1)
p.write_text(s,encoding='utf-8')
print('Live Edit v4 viewport-capture touch transforms applied')
