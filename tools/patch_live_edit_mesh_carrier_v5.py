from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_MESH_CARRIER_V5' in s:
    print('Live Edit mesh carrier v5 already applied'); raise SystemExit(0)

marker='// LIVE_EDIT_TOUCH_TRANSFORM_V4'
if marker not in s: raise SystemExit('Live Edit v4 marker missing')

js=r'''// LIVE_EDIT_MESH_CARRIER_V5
// For SkinnedMesh, changing mesh.position/rotation/scale can move helpers while
// the skinned vertices remain driven by the skeleton/bind matrices. Transform an
// identity parent carrier instead, so the rendered geometry itself moves.
function liveEditCarrierFor(mesh){
  if(!mesh || !mesh.parent)return mesh;
  if(mesh.userData && mesh.userData.__liveEditCarrier && mesh.parent===mesh.userData.__liveEditCarrier){
    return mesh.userData.__liveEditCarrier;
  }
  // Reuse an existing carrier directly above this mesh.
  if(mesh.parent?.userData?.__liveEditCarrierOwner===mesh.uuid){
    mesh.userData.__liveEditCarrier=mesh.parent;
    return mesh.parent;
  }
  const oldParent=mesh.parent;
  const carrier=new THREE.Group();
  carrier.name='__LiveEditCarrier_'+(mesh.name||mesh.uuid);
  carrier.userData.__liveEditCarrierOwner=mesh.uuid;
  const idx=oldParent.children.indexOf(mesh);
  oldParent.add(carrier);
  // Keep draw/order position near the original child where possible.
  if(idx>=0){
    const ci=oldParent.children.indexOf(carrier);
    if(ci>=0){oldParent.children.splice(ci,1);oldParent.children.splice(idx,0,carrier);}
  }
  carrier.add(mesh); // identity carrier under the same old parent preserves world transform
  mesh.userData.__liveEditCarrier=carrier;
  carrier.updateMatrixWorld(true);
  mesh.updateMatrixWorld(true);
  return carrier;
}
function liveEditActualTransformTarget(mesh){
  // Use a carrier for SkinnedMesh to ensure the visible skinned geometry moves.
  // Rigid meshes can be transformed directly.
  return mesh?.isSkinnedMesh ? liveEditCarrierFor(mesh) : mesh;
}

// Patch native-touch v5 variables/functions when present.
if(typeof liveTouchBegin==='function'){
  const _liveTouchBegin=liveTouchBegin;
  liveTouchBegin=function(ev){
    const ok=_liveTouchBegin(ev);
    if(ok && liveTouchMesh){
      const source=liveTouchMesh;
      liveTouchMesh=liveEditActualTransformTarget(source);
      if(liveTouchMesh!==source){
        liveTouchStartPos=liveTouchMesh.position.clone();
        liveTouchStartRot=liveTouchMesh.rotation.clone();
        liveTouchStartScale=liveTouchMesh.scale.clone();
        camera.updateMatrixWorld(true);
        const rightW=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,0).normalize();
        const upW=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,1).normalize();
        if(liveTouchMesh.parent){
          liveTouchMesh.parent.updateMatrixWorld(true);
          const invQ=liveTouchMesh.parent.getWorldQuaternion(new THREE.Quaternion()).invert();
          liveTouchRightLocal=rightW.clone().applyQuaternion(invQ);
          liveTouchUpLocal=upW.clone().applyQuaternion(invQ);
        }else{liveTouchRightLocal=rightW;liveTouchUpLocal=upW;}
      }
      if(typeof showStrongPartSelection==='function')showStrongPartSelection(source);
    }
    return ok;
  };
}

// Patch v4 pointer path too, so both Android pointer and native-touch routes move
// the rendered object rather than only its helper/bounds.
if(typeof liveV4Begin==='function'){
  const _liveV4Begin=liveV4Begin;
  liveV4Begin=function(ev){
    const ok=_liveV4Begin(ev);
    if(ok && liveV4Mesh){
      const source=liveV4Mesh;
      liveV4Mesh=liveEditActualTransformTarget(source);
      if(liveV4Mesh!==source){
        liveV4StartPos=liveV4Mesh.position.clone();
        liveV4StartRot=liveV4Mesh.rotation.clone();
        liveV4StartScale=liveV4Mesh.scale.clone();
        camera.updateMatrixWorld(true);
        const rightW=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,0).normalize();
        const upW=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,1).normalize();
        if(liveV4Mesh.parent){
          liveV4Mesh.parent.updateMatrixWorld(true);
          const invQ=liveV4Mesh.parent.getWorldQuaternion(new THREE.Quaternion()).invert();
          liveV4RightLocal=rightW.clone().applyQuaternion(invQ);
          liveV4UpLocal=upW.clone().applyQuaternion(invQ);
        }else{liveV4RightLocal=rightW;liveV4UpLocal=upW;}
      }
      if(typeof showStrongPartSelection==='function')showStrongPartSelection(source);
    }
    return ok;
  };
}

'''
s=s.replace(marker,js+'\n'+marker,1)
p.write_text(s,encoding='utf-8')
print('Live Edit mesh carrier v5 applied: SkinnedMesh transforms now move rendered geometry')
