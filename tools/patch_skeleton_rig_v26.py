from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'SKELETON_RIG_V26' in s:
    print('Skeleton rig v26 already applied'); raise SystemExit(0)
if 'SKELETON_BONE_MANAGE_V24' not in s:
    raise SystemExit('Skeleton bone manage v24 must run first')

anchor=" setInterval(updateSkeletonVisualV23,50);"
if anchor not in s:
    raise SystemExit('Skeleton visual interval anchor missing')

js=r'''
 // SKELETON_RIG_V26
 // Make the Rig button actually rebuild each SkinnedMesh skeleton from the
 // current bone hierarchy. Existing skin weights are preserved by remapping
 // skinIndex values from the old skeleton order to the new skeleton order.
 // Newly-added bones become valid skeleton members, but receive no vertex
 // weight automatically; weighting remains a separate operation.
 function setSkinIndexCompV26(attr,i,c,v){
   if(c===0)attr.setX(i,v);else if(c===1)attr.setY(i,v);else if(c===2)attr.setZ(i,v);else attr.setW(i,v);
 }
 function getSkinIndexCompV26(attr,i,c){
   return c===0?attr.getX(i):c===1?attr.getY(i):c===2?attr.getZ(i):attr.getW(i);
 }
 function getSkinWeightCompV26(attr,i,c){
   if(!attr)return 0;
   return c===0?attr.getX(i):c===1?attr.getY(i):c===2?attr.getZ(i):attr.getW(i);
 }
 function collectRigBonesV26(){
   const r=activeModelRoot(),out=[];if(!r)return out;
   r.updateMatrixWorld(true);r.traverse(o=>{if(o.isBone)out.push(o)});return out;
 }
 function rebuildSkinnedMeshRigV26(mesh,currentBones){
   const oldSkel=mesh.skeleton;if(!oldSkel)return {ok:false,reason:'no-skeleton'};
   const oldBones=[...oldSkel.bones], oldInv=[...oldSkel.boneInverses];
   const present=new Set(currentBones);
   // Keep only bones that still exist in the hierarchy, preserving hierarchy order.
   const newBones=[...currentBones];
   if(!newBones.length)return {ok:false,reason:'no-bones'};
   const newIndex=new Map(newBones.map((b,i)=>[b,i]));
   const oldToNew=new Map();for(let i=0;i<oldBones.length;i++){const ni=newIndex.get(oldBones[i]);if(ni!=null)oldToNew.set(i,ni)}
   const si=mesh.geometry?.getAttribute?.('skinIndex');
   const sw=mesh.geometry?.getAttribute?.('skinWeight');
   if(si){
     for(let i=0;i<si.count;i++){
       for(let c=0;c<4;c++){
         const oi=Math.round(getSkinIndexCompV26(si,i,c));
         const w=getSkinWeightCompV26(sw,i,c);
         const ni=oldToNew.get(oi);
         if(ni==null){
           if(w>1e-6)throw new Error('Weighted bone hilang dari hierarchy');
           setSkinIndexCompV26(si,i,c,0);
         }else setSkinIndexCompV26(si,i,c,ni);
       }
     }
     si.needsUpdate=true;
   }
   // Preserve inverse bind matrices for existing bones; new bones use their
   // current world transform as bind pose.
   const oldInverseByBone=new Map();for(let i=0;i<oldBones.length;i++)if(oldInv[i])oldInverseByBone.set(oldBones[i],oldInv[i].clone());
   const newInv=[];for(const b of newBones){
     const inv=oldInverseByBone.get(b);newInv.push(inv||new THREE.Matrix4().copy(b.matrixWorld).invert());
   }
   const bindMatrix=mesh.bindMatrix?.clone?.()||new THREE.Matrix4();
   const next=new THREE.Skeleton(newBones,newInv);
   mesh.bind(next,bindMatrix);next.update();
   return {ok:true,added:newBones.filter(b=>!oldBones.includes(b)).length,removed:oldBones.filter(b=>!present.has(b)).length};
 }
 function rigSkeletonV26(){
   if(!skeletonLiveEditMode)return;
   const r=activeModelRoot();if(!r){msg('Model tidak ditemukan');return}
   const currentBones=collectRigBonesV26();if(!currentBones.length){msg('Skeleton tidak ditemukan');return}
   const meshes=[];r.traverse(o=>{if(o.isSkinnedMesh&&o.skeleton)meshes.push(o)});
   if(!meshes.length){msg('SkinnedMesh tidak ditemukan');return}
   let ok=0,added=0,removed=0;
   try{
     for(const m of meshes){const res=rebuildSkinnedMeshRigV26(m,currentBones);if(res.ok){ok++;added+=res.added||0;removed+=res.removed||0}}
   }catch(err){msg('Rig gagal: '+(err?.message||err));return}
   refreshHelper();setSkeletonVisible(true);rebuildSkeletonVisualV23();updateSkeletonVisualV23();
   msg('Rig diterapkan • '+ok+' mesh • +'+added+' bone'+(removed?' • -'+removed+' bone':''));
 }
 rigBtn.onclick=rigSkeletonV26;
'''

s=s.replace(anchor,js+'\n'+anchor,1)
p.write_text(s,encoding='utf-8')
print('Skeleton rig v26 applied')
