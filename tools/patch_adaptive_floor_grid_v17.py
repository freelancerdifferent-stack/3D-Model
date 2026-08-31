from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'ADAPTIVE_FLOOR_GRID_V17' in s:
    print('Adaptive floor grid v17 already applied'); raise SystemExit(0)
old="const grid = new THREE.GridHelper(20,20,0x4b5968,0x35404d); scene.add(grid);"
new=r'''// ADAPTIVE_FLOOR_GRID_V17
let grid = new THREE.GridHelper(20,20,0x4b5968,0x35404d); scene.add(grid);
function refreshVisualBounds(obj){
  if(!obj)return new THREE.Box3();
  obj.updateMatrixWorld(true);
  // Skinned meshes need a fresh deformed bounding box; otherwise the floor can
  // end up around the ankles/hips for FBX characters.
  obj.traverse(o=>{
    if(o?.isSkinnedMesh && typeof o.computeBoundingBox==='function'){
      try{o.computeBoundingBox()}catch(_){}
    }else if(o?.isMesh && o.geometry && !o.geometry.boundingBox){
      try{o.geometry.computeBoundingBox()}catch(_){}
    }
  });
  obj.updateMatrixWorld(true);
  return new THREE.Box3().setFromObject(obj);
}
function rebuildFloorGrid(obj){
  if(!obj)return;
  const box=refreshVisualBounds(obj);
  if(box.isEmpty())return;
  const size=box.getSize(new THREE.Vector3());
  const center=box.getCenter(new THREE.Vector3());
  // Character files use wildly different units (meters, cm, FBX units).
  // Make the grid proportional to the model instead of a fixed 20x20 square.
  const footprint=Math.max(size.x,size.z,1e-6);
  const reference=Math.max(footprint,size.y*.55,1);
  const gridSize=Math.max(reference*2.2,footprint*2.5);
  const divisions=20;
  const wasVisible=grid?.visible!==false;
  if(grid){scene.remove(grid);grid.geometry?.dispose?.();const mats=Array.isArray(grid.material)?grid.material:[grid.material];mats.forEach(m=>m?.dispose?.())}
  grid=new THREE.GridHelper(gridSize,divisions,0x60758a,0x35404d);
  grid.position.set(center.x,box.min.y-Math.max(gridSize*0.00035,0.0001),center.z);
  grid.visible=wasVisible;
  grid.renderOrder=-10;
  scene.add(grid);
}
'''
if old not in s: raise SystemExit('base grid marker missing')
s=s.replace(old,new,1)
old2="  grid.position.y=0;\n  const maxDim=Math.max(size.x,size.y,size.z)||1;"
new2="  rebuildFloorGrid(obj);\n  const maxDim=Math.max(size.x,size.y,size.z)||1;"
if old2 not in s: raise SystemExit('centerAndFit grid marker missing')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')
print('Adaptive floor grid v17 applied')
