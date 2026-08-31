from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_TRANSFORM_V2' in s:
    print('Live Edit transform v2 already applied'); raise SystemExit(0)

marker='// Manual horizontal/vertical camera pan. Move camera and OrbitControls target together,'
if marker not in s: raise SystemExit('Live Edit insertion marker missing')

js=r'''// LIVE_EDIT_TRANSFORM_V2
// Dedicated Live Edit gesture path. This intentionally does not depend on the
// older Part Drag/Rotate/Scale pointer handlers, which can conflict with the
// Select capture listener and Android WebView event ordering.
let liveV2PointerId=null;
let liveV2Mesh=null;
let liveV2StartX=0,liveV2StartY=0;
let liveV2StartPos=null,liveV2StartRot=null,liveV2StartScale=null;
let liveV2RightLocal=null,liveV2UpLocal=null;

function liveV2ActiveMesh(){
  const mesh=(activeMeshLayerIndex>=0)?meshList[activeMeshLayerIndex]:null;
  if(!mesh || !mesh.isMesh || !mesh.visible)return null;
  if(typeof isMeshPartLocked==='function' && isMeshPartLocked(mesh))return null;
  return mesh;
}
function liveV2Stop(){
  if(liveV2PointerId!==null){try{canvas.releasePointerCapture(liveV2PointerId)}catch(_){ }}
  liveV2PointerId=null;liveV2Mesh=null;
  liveV2StartPos=liveV2StartRot=liveV2StartScale=null;
  liveV2RightLocal=liveV2UpLocal=null;
  if(liveEditSelectMode)controls.enabled=false;
}
function liveV2Begin(ev){
  if(!liveEditSelectMode || !liveEditTransformMode)return false;
  if(ev.pointerType==='mouse'&&ev.button!==0)return false;
  const mesh=liveV2ActiveMesh();
  if(!mesh){msg('Pilih part yang tidak dikunci dulu');return true;}
  liveV2PointerId=ev.pointerId;liveV2Mesh=mesh;
  liveV2StartX=ev.clientX;liveV2StartY=ev.clientY;
  liveV2StartPos=mesh.position.clone();
  liveV2StartRot=mesh.rotation.clone();
  liveV2StartScale=mesh.scale.clone();
  // Camera screen axes converted into the mesh parent's local space.
  camera.updateMatrixWorld(true);
  const rightW=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,0).normalize();
  const upW=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,1).normalize();
  if(mesh.parent){
    mesh.parent.updateMatrixWorld(true);
    const invQ=mesh.parent.getWorldQuaternion(new THREE.Quaternion()).invert();
    liveV2RightLocal=rightW.clone().applyQuaternion(invQ);
    liveV2UpLocal=upW.clone().applyQuaternion(invQ);
  }else{
    liveV2RightLocal=rightW;liveV2UpLocal=upW;
  }
  try{canvas.setPointerCapture(ev.pointerId)}catch(_){ }
  controls.enabled=false;
  if(typeof showStrongPartSelection==='function')showStrongPartSelection(mesh);
  return true;
}
function liveV2Move(ev){
  if(ev.pointerId!==liveV2PointerId || !liveV2Mesh)return false;
  if(typeof isMeshPartLocked==='function' && isMeshPartLocked(liveV2Mesh)){liveV2Stop();msg('Part ini dikunci');return true;}
  const dx=ev.clientX-liveV2StartX,dy=ev.clientY-liveV2StartY;
  const mesh=liveV2Mesh;
  if(liveEditTransformMode==='move'){
    const dist=Math.max(.1,camera.position.distanceTo(controls.target));
    const k=dist*.0022;
    const delta=liveV2RightLocal.clone().multiplyScalar(dx*k).add(liveV2UpLocal.clone().multiplyScalar(-dy*k));
    mesh.position.copy(liveV2StartPos).add(delta);
  }else if(liveEditTransformMode==='rotate'){
    // Horizontal drag = yaw, vertical drag = pitch.
    mesh.rotation.copy(liveV2StartRot);
    mesh.rotation.y+=dx*0.010;
    mesh.rotation.x+=dy*0.010;
  }else if(liveEditTransformMode==='scale'){
    // Up enlarges, down shrinks. Exponential response keeps scale positive.
    const factor=Math.max(.05,Math.min(20,Math.exp(-dy*0.008)));
    mesh.scale.set(liveV2StartScale.x*factor,liveV2StartScale.y*factor,liveV2StartScale.z*factor);
  }
  mesh.updateMatrixWorld(true);
  if(partDragHelper){try{partDragHelper.update()}catch(_){ }}
  return true;
}

// Register after V1 in capture phase. stopImmediatePropagation guarantees this
// one path owns the gesture whenever a Live Edit transform tool is active.
canvas.addEventListener('pointerdown',ev=>{
  if(!liveV2Begin(ev))return;
  ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
},{capture:true});
canvas.addEventListener('pointermove',ev=>{
  if(!liveV2Move(ev))return;
  ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
},{capture:true});
canvas.addEventListener('pointerup',ev=>{
  if(ev.pointerId!==liveV2PointerId)return;
  liveV2Move(ev);liveV2Stop();
  ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
},{capture:true});
canvas.addEventListener('pointercancel',ev=>{
  if(ev.pointerId!==liveV2PointerId)return;
  liveV2Stop();
  ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
},{capture:true});

'''
s=s.replace(marker,js+marker,1)
p.write_text(s,encoding='utf-8')
print('Live Edit transform v2 dedicated gesture handler applied')
