from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'SKELETON_RIG_V26' in s:
    print('Skeleton rig v26 already applied'); raise SystemExit(0)
if 'SKELETON_BONE_MANAGE_V24' not in s:
    raise SystemExit('Skeleton bone manage v24 must run first')

# While the dedicated Rig workspace is open, Skeleton drag gestures must not move bones.
s=s.replace("if(!skeletonLiveEditMode||e.touches.length!==1)return;\n   const t=e.touches[0];\n   if(!selectedBone||!chooseBone(t.clientX,t.clientY))",
            "if(!skeletonLiveEditMode||window.skeletonRigModeV26||e.touches.length!==1)return;\n   const t=e.touches[0];\n   if(!selectedBone||!chooseBone(t.clientX,t.clientY))",1)
s=s.replace("if(!skeletonLiveEditMode||touchId==null||!selectedBone)return;",
            "if(!skeletonLiveEditMode||window.skeletonRigModeV26||touchId==null||!selectedBone)return;",1)

# Dedicated workspace styling. The canvas stays usable while Skeleton tool chrome is hidden.
css=r'''
/* RIG_WORKSPACE_V26 */
body.rig-workspace-v26 #editorScreen .toolrail,
body.rig-workspace-v26 #editorScreen .viewtools,
body.rig-workspace-v26 #editorScreen #objectCameraPad,
body.rig-workspace-v26 #editorScreen #objectTrackpadDrawer,
body.rig-workspace-v26 #editorScreen #liveEditBadge{display:none!important}
#rigWorkspaceV26{display:none;position:absolute;inset:0;z-index:60;pointer-events:none;color:#e7f2ff;font:12px system-ui}
body.rig-workspace-v26 #rigWorkspaceV26{display:block}
#rigWorkspaceV26 .rig-top{position:absolute;left:8px;right:8px;top:8px;height:42px;display:flex;align-items:center;gap:8px;padding:0 8px;background:rgba(12,18,26,.94);border:1px solid #315e87;border-radius:10px;box-shadow:0 6px 20px #0008;pointer-events:auto}
#rigWorkspaceV26 .rig-title{font-size:14px;font-weight:800;letter-spacing:.08em}
#rigWorkspaceV26 .rig-status{min-width:0;flex:1;opacity:.78;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#rigWorkspaceV26 button{min-height:34px;border:1px solid #376d9d;border-radius:7px;background:#152b40;color:#dcecff;font-weight:700}
#rigWorkspaceV26 .rig-bottom{position:absolute;left:8px;right:8px;bottom:8px;padding:10px;background:rgba(12,18,26,.96);border:1px solid #315e87;border-radius:12px;box-shadow:0 -6px 24px #0008;pointer-events:auto}
#rigWorkspaceV26 .rig-grid{display:grid;grid-template-columns:54px minmax(0,1fr);gap:7px 8px;align-items:center}
#rigWorkspaceV26 .rig-name{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#rigWorkspaceV26 .rig-slider{display:flex;align-items:center;gap:8px}
#rigWorkspaceV26 .rig-slider input{width:100%;min-width:0}
#rigWorkspaceV26 .rig-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
#rigWorkspaceV26 #rigApplyV26{background:#173f62}
#rigWorkspaceV26 #rigBindV26{background:#1b553c;border-color:#33795b}
'''
s=s.replace('</style>',css+'\n</style>',1)

anchor=" setInterval(updateSkeletonVisualV23,50);"
if anchor not in s:
    raise SystemExit('Skeleton visual interval anchor missing')

js=r'''
 // SKELETON_RIG_V26
 // RIG_WORKSPACE_V26 — Rig button is a portal into a dedicated Rig workspace.
 let skeletonRigModeV26=false;
 let rigMeshV26=null,rigHitWorldV26=null;
 const rigRayV26=new THREE.Raycaster(),rigNdcV26=new THREE.Vector2(),rigTmpV26=new THREE.Vector3();
 window.skeletonRigModeV26=false;

 const rigWorkspaceV26=document.createElement('div');
 rigWorkspaceV26.id='rigWorkspaceV26';
 rigWorkspaceV26.innerHTML=`
   <div class="rig-top">
     <button id="rigBackV26" type="button">← Skeleton</button>
     <div class="rig-title">RIG</div>
     <div id="rigStatusV26" class="rig-status">Tap mesh, lalu pilih bone</div>
   </div>
   <div class="rig-bottom">
     <div class="rig-grid">
       <span>Mesh</span><b id="rigMeshNameV26" class="rig-name">—</b>
       <span>Bone</span><b id="rigBoneNameV26" class="rig-name">—</b>
       <span>Weight</span><div class="rig-slider"><input id="rigWeightV26" type="range" min="0" max="1" step="0.05" value="1"><b id="rigWeightTextV26">1.00</b></div>
       <span>Radius</span><div class="rig-slider"><input id="rigRadiusV26" type="range" min="1" max="30" step="1" value="5"><b id="rigRadiusTextV26">5%</b></div>
     </div>
     <div class="rig-actions"><button id="rigApplyV26" type="button">Apply Weight</button><button id="rigBindV26" type="button">Bind</button></div>
   </div>`;
 viewport.appendChild(rigWorkspaceV26);
 const rigStatusV26=$('rigStatusV26'),rigMeshNameV26=$('rigMeshNameV26'),rigBoneNameV26=$('rigBoneNameV26');
 const rigWeightV26=$('rigWeightV26'),rigWeightTextV26=$('rigWeightTextV26'),rigRadiusV26=$('rigRadiusV26'),rigRadiusTextV26=$('rigRadiusTextV26');

 const rigMarkerV26=new THREE.Mesh(new THREE.SphereGeometry(1,16,10),new THREE.MeshBasicMaterial({color:0x34c8ff,wireframe:true,depthTest:false,depthWrite:false,transparent:true,opacity:.9}));
 rigMarkerV26.visible=false;rigMarkerV26.renderOrder=1100;scene.add(rigMarkerV26);

 function modelUnitV26(){const r=activeModelRoot();if(!r)return 1;const box=new THREE.Box3().setFromObject(r);if(box.isEmpty())return 1;const z=new THREE.Vector3();box.getSize(z);return Math.max(.001,z.x,z.y,z.z)}
 function brushRadiusWorldV26(){return modelUnitV26()*(Number(rigRadiusV26?.value)||5)/100}
 function updateRigMarkerV26(){if(!skeletonRigModeV26||!rigHitWorldV26){rigMarkerV26.visible=false;return}rigMarkerV26.visible=true;rigMarkerV26.position.copy(rigHitWorldV26);rigMarkerV26.scale.setScalar(brushRadiusWorldV26())}
 function syncRigUiV26(){
   rigMeshNameV26.textContent=rigMeshV26?(rigMeshV26.name||'SkinnedMesh'):'—';
   rigBoneNameV26.textContent=selectedBone?(selectedBone.name||'Bone'):'—';
   rigWeightTextV26.textContent=Number(rigWeightV26.value).toFixed(2);
   rigRadiusTextV26.textContent=rigRadiusV26.value+'%';updateRigMarkerV26();
 }
 function setRigModeV26(on){
   skeletonRigModeV26=!!on&&!!skeletonLiveEditMode;
   window.skeletonRigModeV26=skeletonRigModeV26;
   document.body.classList.toggle('rig-workspace-v26',skeletonRigModeV26);
   rigBtn.classList.toggle('active',skeletonRigModeV26);
   if(skeletonRigModeV26){
     controls.enabled=false;setSkeletonVisible(true);
     rigStatusV26.textContent='Tap mesh, lalu pilih bone';
     msg('Rig workspace dibuka');
   }else{
     rigMarkerV26.visible=false;rigHitWorldV26=null;
     rigStatusV26.textContent='Tap mesh, lalu pilih bone';
     if(skeletonLiveEditMode)controls.enabled=false;
   }
   syncRigUiV26();
 }
 window.openRigWorkspaceV26=()=>setRigModeV26(true);
 window.closeRigWorkspaceV26=()=>setRigModeV26(false);

 function skinnedMeshesV26(){const r=activeModelRoot(),out=[];if(r)r.traverse(o=>{if(o.isSkinnedMesh)out.push(o)});return out}
 function pickRigMeshV26(x,y){const rect=canvas.getBoundingClientRect();rigNdcV26.set(((x-rect.left)/rect.width)*2-1,-((y-rect.top)/rect.height)*2+1);rigRayV26.setFromCamera(rigNdcV26,camera);const hits=rigRayV26.intersectObjects(skinnedMeshesV26(),false);return hits[0]||null}
 function ensureBoneInSkeletonV26(mesh,bone){
   if(!mesh?.skeleton||!bone)return-1;let idx=mesh.skeleton.bones.indexOf(bone);if(idx>=0)return idx;
   bone.updateMatrixWorld(true);mesh.skeleton.bones.push(bone);mesh.skeleton.boneInverses.push(new THREE.Matrix4().copy(bone.matrixWorld).invert());try{mesh.skeleton.init()}catch(_){}return mesh.skeleton.bones.indexOf(bone);
 }
 function ensureSkinAttrsV26(mesh){
   const g=mesh.geometry,pos=g?.getAttribute?.('position');if(!g||!pos)return null;let si=g.getAttribute('skinIndex'),sw=g.getAttribute('skinWeight');
   if(!si){si=new THREE.Uint16BufferAttribute(new Uint16Array(pos.count*4),4);g.setAttribute('skinIndex',si)}
   if(!sw){const a=new Float32Array(pos.count*4);for(let i=0;i<pos.count;i++)a[i*4]=1;sw=new THREE.Float32BufferAttribute(a,4);g.setAttribute('skinWeight',sw)}return{pos,si,sw};
 }
 function get4V26(a,i){return[a.getX(i),a.getY(i),a.getZ(i),a.getW(i)]}
 function set4V26(a,i,v){a.setXYZW(i,v[0],v[1],v[2],v[3])}
 function applyInfluenceV26(indices,weights,boneIndex,targetWeight){
   targetWeight=Math.max(0,Math.min(1,targetWeight));let slot=indices.indexOf(boneIndex);if(slot<0){slot=0;for(let j=1;j<4;j++)if(weights[j]<weights[slot])slot=j;indices[slot]=boneIndex}
   const oldOther=weights.reduce((a,w,j)=>a+(j===slot?0:Math.max(0,w)),0),remain=1-targetWeight;weights[slot]=targetWeight;
   if(remain<=1e-8){for(let j=0;j<4;j++)if(j!==slot)weights[j]=0;return}
   if(oldOther>1e-8){for(let j=0;j<4;j++)if(j!==slot)weights[j]=Math.max(0,weights[j])/oldOther*remain}
   else{const other=slot===0?1:0;indices[other]=indices[other]===boneIndex?0:indices[other];weights[other]=remain;for(let j=0;j<4;j++)if(j!==slot&&j!==other)weights[j]=0}
 }
 function applyRigWeightV26(){
   if(!skeletonRigModeV26)return;if(!rigMeshV26){msg('Tap mesh dulu');return}if(!selectedBone){msg('Pilih bone dulu');return}if(!rigHitWorldV26){msg('Tap area mesh yang akan diberi weight');return}
   const attrs=ensureSkinAttrsV26(rigMeshV26);if(!attrs){msg('Geometry tidak mendukung skinning');return}const boneIndex=ensureBoneInSkeletonV26(rigMeshV26,selectedBone);if(boneIndex<0){msg('Bone gagal ditambahkan ke skeleton');return}
   const r2=brushRadiusWorldV26()**2,w=Number(rigWeightV26.value);let changed=0;rigMeshV26.updateMatrixWorld(true);
   for(let i=0;i<attrs.pos.count;i++){rigTmpV26.fromBufferAttribute(attrs.pos,i).applyMatrix4(rigMeshV26.matrixWorld);if(rigTmpV26.distanceToSquared(rigHitWorldV26)>r2)continue;const ii=get4V26(attrs.si,i).map(v=>Math.round(v)),ww=get4V26(attrs.sw,i);applyInfluenceV26(ii,ww,boneIndex,w);set4V26(attrs.si,i,ii);set4V26(attrs.sw,i,ww);changed++}
   attrs.si.needsUpdate=true;attrs.sw.needsUpdate=true;try{rigMeshV26.normalizeSkinWeights()}catch(_){}try{rigMeshV26.skeleton.update()}catch(_){}rigStatusV26.textContent=changed+' vertex • weight '+w.toFixed(2);msg(changed?'Weight diterapkan ke '+changed+' vertex':'Tidak ada vertex dalam radius');
 }
 function bindRigV26(){
   if(!skeletonRigModeV26)return;if(!rigMeshV26){msg('Tap mesh dulu');return}if(!selectedBone){msg('Pilih bone dulu');return}const idx=ensureBoneInSkeletonV26(rigMeshV26,selectedBone);if(idx<0){msg('Bind gagal');return}
   try{rigMeshV26.bind(rigMeshV26.skeleton,rigMeshV26.bindMatrix);rigMeshV26.skeleton.update();rigMeshV26.updateMatrixWorld(true);refreshHelper();setSkeletonVisible(true);rebuildSkeletonVisualV23();updateSkeletonVisualV23();rigStatusV26.textContent='Bound: '+(selectedBone.name||'Bone');msg('Rig berhasil di-bind')}catch(e){msg('Bind gagal: '+(e?.message||e))}
 }

 // Portal behavior: Rig never toggles an inline panel; it opens the dedicated workspace.
 rigBtn.onclick=()=>setRigModeV26(true);
 $('rigBackV26').onclick=()=>setRigModeV26(false);
 $('rigApplyV26').onclick=applyRigWeightV26;
 $('rigBindV26').onclick=bindRigV26;
 rigWeightV26.oninput=syncRigUiV26;rigRadiusV26.oninput=syncRigUiV26;

 canvas.addEventListener('touchstart',ev=>{
   if(!skeletonLiveEditMode||!skeletonRigModeV26||ev.touches.length!==1)return;
   const t=ev.touches[0],b=projectedBoneAt(t.clientX,t.clientY);
   if(b){setSkeletonSelectedBoneV21(b);rigStatusV26.textContent='Bone: '+(b.name||'Bone');syncRigUiV26();ev.preventDefault();ev.stopPropagation();return}
   const hit=pickRigMeshV26(t.clientX,t.clientY);
   if(hit){rigMeshV26=hit.object;rigHitWorldV26=hit.point.clone();rigStatusV26.textContent='Mesh/area dipilih • pilih bone atau Apply Weight';syncRigUiV26();ev.preventDefault();ev.stopPropagation()}
 },{capture:true,passive:false});

 setInterval(()=>{if(!skeletonLiveEditMode&&skeletonRigModeV26)setRigModeV26(false);if(skeletonRigModeV26){controls.enabled=false;syncRigUiV26()}},120);
'''

s=s.replace(anchor,js+'\n'+anchor,1)
p.write_text(s,encoding='utf-8')
print('Skeleton Rig v26 applied: dedicated Rig workspace portal + weight + bind')
