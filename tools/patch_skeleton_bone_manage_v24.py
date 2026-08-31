from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'SKELETON_BONE_MANAGE_V24' in s:
    print('Skeleton bone manage v24 already applied'); raise SystemExit(0)
if 'SKELETON_VISUAL_V23' not in s:
    raise SystemExit('Skeleton visual v23 must run first')

anchor=" setInterval(updateSkeletonVisualV23,50);"
if anchor not in s:
    raise SystemExit('Skeleton visual interval anchor missing')

js=r'''
 // SKELETON_BONE_MANAGE_V24
 const removeBoneBtn=makeTool('✕','Remove<br>bone','skeletonRemoveBoneBtn','skeleton-only-tool');
 rail.insertBefore(removeBoneBtn,rigBtn);

 function uniqueBoneNameV24(base){
   const used=new Set(bones().map(b=>b.name));let i=1,name=base;
   while(used.has(name))name=base+'_'+i++;
   return name;
 }
 function refreshSkeletonAfterManageV24(){
   refreshHelper();setSkeletonVisible(true);rebuildSkeletonVisualV23();updateSkeletonVisualV23();
   try{syncSkeletonTransformFieldsV21()}catch(_){}
 }
 function selectedBoneReferencedBySkinV24(b){
   const r=activeModelRoot();if(!r||!b)return false;
   let referenced=false;
   r.traverse(o=>{
     if(referenced||!o.isSkinnedMesh||!o.skeleton)return;
     const idx=o.skeleton.bones.indexOf(b);if(idx<0)return;
     const si=o.geometry?.getAttribute?.('skinIndex'), sw=o.geometry?.getAttribute?.('skinWeight');
     if(!si){referenced=true;return}
     const n=si.count;
     for(let i=0;i<n&&!referenced;i++){
       for(let c=0;c<4;c++){
         const boneIndex=c===0?si.getX(i):c===1?si.getY(i):c===2?si.getZ(i):si.getW(i);
         const weight=sw?(c===0?sw.getX(i):c===1?sw.getY(i):c===2?sw.getZ(i):sw.getW(i)):1;
         if(boneIndex===idx&&weight>1e-6){referenced=true;break}
       }
     }
   });
   return referenced;
 }
 function addBoneV24(){
   if(!skeletonLiveEditMode)return;
   const parent=selectedBone||bones()[0];
   if(!parent){msg('Skeleton tidak ditemukan');return}
   const b=new THREE.Bone();
   b.name=uniqueBoneNameV24((parent.name||'Bone')+'_child');
   let len=.1;
   const childBone=parent.children.find(c=>c.isBone);
   if(childBone)len=Math.max(.02,childBone.position.length()*.65);
   b.position.set(0,len,0);parent.add(b);parent.updateMatrixWorld(true);
   setSkeletonSelectedBoneV21(b);refreshSkeletonAfterManageV24();
   msg('Bone ditambahkan');
 }
 function duplicateBoneV24(){
   if(!skeletonLiveEditMode||!selectedBone){msg('Pilih bone dulu');return}
   const src=selectedBone,parent=src.parent;
   if(!parent){msg('Root bone tidak dapat diduplikasi di sini');return}
   const b=new THREE.Bone();
   b.name=uniqueBoneNameV24((src.name||'Bone')+'_copy');
   b.position.copy(src.position);b.quaternion.copy(src.quaternion);b.scale.copy(src.scale);
   parent.add(b);parent.updateMatrixWorld(true);
   setSkeletonSelectedBoneV21(b);refreshSkeletonAfterManageV24();
   msg('Bone diduplikasi');
 }
 function removeBoneV24(){
   if(!skeletonLiveEditMode||!selectedBone){msg('Pilih bone dulu');return}
   const b=selectedBone,parent=b.parent;
   if(!parent){msg('Root bone tidak dapat dihapus');return}
   if(selectedBoneReferencedBySkinV24(b)){
     msg('Bone masih dipakai skinning. Hapus weight/rig dulu');return;
   }
   // Preserve child-bone world transforms while promoting them to the removed bone parent.
   b.updateMatrixWorld(true);parent.updateMatrixWorld(true);
   const boneChildren=b.children.filter(c=>c.isBone);
   const world=new Map();for(const c of boneChildren){c.updateMatrixWorld(true);world.set(c,c.matrixWorld.clone())}
   for(const c of boneChildren){
     parent.add(c);
     const local=new THREE.Matrix4().copy(parent.matrixWorld).invert().multiply(world.get(c));
     local.decompose(c.position,c.quaternion,c.scale);
   }
   parent.remove(b);parent.updateMatrixWorld(true);
   setSkeletonSelectedBoneV21(parent.isBone?parent:null);refreshSkeletonAfterManageV24();
   msg('Bone dihapus');
 }

 // Replace the original placeholder handlers with the active Skeleton management route.
 addBoneBtn.onclick=addBoneV24;
 duplicateBoneBtn.onclick=duplicateBoneV24;
 removeBoneBtn.onclick=removeBoneV24;
'''

s=s.replace(anchor,js+'\n'+anchor,1)
p.write_text(s,encoding='utf-8')
print('Skeleton bone manage v24 applied: add duplicate remove')
