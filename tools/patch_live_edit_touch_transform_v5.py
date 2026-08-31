from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_TOUCH_TRANSFORM_V5' in s:
    print('Live Edit touch transform v5 already applied'); raise SystemExit(0)

marker='// Manual horizontal/vertical camera pan. Move camera and OrbitControls target together,'
if marker not in s: raise SystemExit('Live Edit insertion marker missing')

js=r'''// LIVE_EDIT_TOUCH_TRANSFORM_V5
// Android WebView fix: use native Touch Events for drag gestures instead of relying
// on PointerEvent move/capture. Tap selection may stay on Pointer Events, but all
// transform drags below are owned by touchstart/touchmove/touchend.
let liveV5TouchId=null;
let liveV5Mesh=null;
let liveV5StartX=0,liveV5StartY=0;
let liveV5StartPos=null,liveV5StartRot=null,liveV5StartScale=null;
let liveV5RightLocal=null,liveV5UpLocal=null;

function liveV5SelectedMesh(){
  let mesh=(typeof liveEditSelectedMeshRef!=='undefined')?liveEditSelectedMeshRef:null;
  if(!mesh && activeMeshLayerIndex>=0)mesh=meshList[activeMeshLayerIndex];
  if(!mesh || !mesh.isMesh || !mesh.visible)return null;
  if(typeof isMeshPartLocked==='function' && isMeshPartLocked(mesh))return null;
  return mesh;
}
function liveV5FindTouch(list,id){
  for(let i=0;i<list.length;i++)if(list[i].identifier===id)return list[i];
  return null;
}
function liveV5Stop(){
  liveV5TouchId=null;liveV5Mesh=null;
  liveV5StartPos=liveV5StartRot=liveV5StartScale=null;
  liveV5RightLocal=liveV5UpLocal=null;
  controls.enabled=!liveEditSelectMode;
}
function liveV5Start(ev){
  if(!liveEditSelectMode || !liveEditTransformMode)return;
  if(ev.target!==canvas)return;
  if(!ev.changedTouches || !ev.changedTouches.length)return;
  const mesh=liveV5SelectedMesh();
  if(!mesh){msg('Pilih part dulu dengan Select');return;}
  const t=ev.changedTouches[0];
  liveV5TouchId=t.identifier;liveV5Mesh=mesh;
  liveV5StartX=t.clientX;liveV5StartY=t.clientY;
  liveV5StartPos=mesh.position.clone();
  liveV5StartRot=mesh.rotation.clone();
  liveV5StartScale=mesh.scale.clone();
  camera.updateMatrixWorld(true);
  const rightW=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,0).normalize();
  const upW=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,1).normalize();
  if(mesh.parent){
    mesh.parent.updateMatrixWorld(true);
    const invQ=mesh.parent.getWorldQuaternion(new THREE.Quaternion()).invert();
    liveV5RightLocal=rightW.clone().applyQuaternion(invQ);
    liveV5UpLocal=upW.clone().applyQuaternion(invQ);
  }else{liveV5RightLocal=rightW;liveV5UpLocal=upW;}
  controls.enabled=false;
  if(typeof showStrongPartSelection==='function')showStrongPartSelection(mesh);
  ev.preventDefault();
  ev.stopPropagation();
  if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
}
function liveV5Move(ev){
  if(liveV5TouchId===null || !liveV5Mesh)return;
  const t=liveV5FindTouch(ev.touches,liveV5TouchId) || liveV5FindTouch(ev.changedTouches,liveV5TouchId);
  if(!t)return;
  const mesh=liveV5Mesh;
  if(typeof isMeshPartLocked==='function' && isMeshPartLocked(mesh)){liveV5Stop();msg('Part ini dikunci');return;}
  const dx=t.clientX-liveV5StartX,dy=t.clientY-liveV5StartY;
  if(liveEditTransformMode==='move'){
    const dist=Math.max(.1,camera.position.distanceTo(controls.target));
    const k=dist*.0035;
    const d=liveV5RightLocal.clone().multiplyScalar(dx*k).add(liveV5UpLocal.clone().multiplyScalar(-dy*k));
    mesh.position.copy(liveV5StartPos).add(d);
  }else if(liveEditTransformMode==='rotate'){
    mesh.rotation.copy(liveV5StartRot);
    mesh.rotation.y+=dx*0.014;
    mesh.rotation.x+=dy*0.014;
  }else if(liveEditTransformMode==='scale'){
    const factor=Math.max(.05,Math.min(20,Math.exp(-dy*0.012)));
    mesh.scale.set(liveV5StartScale.x*factor,liveV5StartScale.y*factor,liveV5StartScale.z*factor);
  }
  mesh.updateMatrixWorld(true);
  if(typeof partDragHelper!=='undefined' && partDragHelper){try{partDragHelper.update()}catch(_){ }}
  ev.preventDefault();
  ev.stopPropagation();
  if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
}
function liveV5End(ev){
  if(liveV5TouchId===null)return;
  const ended=liveV5FindTouch(ev.changedTouches,liveV5TouchId);
  if(!ended)return;
  // Apply the final position once more using the ending touch coordinates.
  const fake={touches:[],changedTouches:[ended],preventDefault(){},stopPropagation(){},stopImmediatePropagation(){}};
  liveV5Move(fake);
  liveV5Stop();
  ev.preventDefault();
  ev.stopPropagation();
  if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
}

const liveV5Surface=canvas.parentElement;
liveV5Surface.addEventListener('touchstart',liveV5Start,{capture:true,passive:false});
liveV5Surface.addEventListener('touchmove',liveV5Move,{capture:true,passive:false});
liveV5Surface.addEventListener('touchend',liveV5End,{capture:true,passive:false});
liveV5Surface.addEventListener('touchcancel',ev=>{if(liveV5TouchId!==null){liveV5Stop();ev.preventDefault();}},{capture:true,passive:false});

// Final toolbar ownership. Do not enable any legacy part gesture mode here.
function liveV5SetMode(mode){
  if(!liveEditSelectMode){controls.enabled=true;msg('Tekan Select untuk masuk Live Edit');return;}
  const mesh=liveV5SelectedMesh();
  if(!mesh){msg('Pilih part dulu dengan Select');return;}
  if(typeof isMeshPartLocked==='function' && isMeshPartLocked(mesh)){msg('Part ini dikunci');return;}
  try{setExclusivePartMode('move',false)}catch(_){ }
  liveEditSelectedMeshRef=mesh;
  liveEditTransformMode=mode;
  controls.enabled=false;
  updateLiveEditToolUI();
  if(typeof showStrongPartSelection==='function')showStrongPartSelection(mesh);
  msg((mode==='move'?'Move':mode==='rotate'?'Rotate':'Scale')+' aktif — touch lalu geser di preview');
}
$('liveMoveBtn').onclick=()=>liveV5SetMode('move');
$('liveRotateBtn').onclick=()=>liveV5SetMode('rotate');
$('liveScaleBtn').onclick=()=>liveV5SetMode('scale');

'''
s=s.replace(marker,js+marker,1)
p.write_text(s,encoding='utf-8')
print('Live Edit v5 native Android Touch Events applied')
