from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'SKELETON_LIVE_EDIT_V20' in s:
    print('Skeleton Live Edit v20 already applied'); raise SystemExit(0)

css=r'''
/* SKELETON_LIVE_EDIT_V20 */
#editorScreen #skeletonViewBtn.on{background:#214777;color:#61a6ff}
#editorScreen #skeletonModeBtn{margin-top:5px;border:1px solid #2868a7;background:#17304c;color:#65aaff}
#editorScreen #skeletonModeBtn.active{box-shadow:inset 0 0 0 2px #2e75ba;background:#17304c;color:#65aaff}
#editorScreen .skeleton-only-tool{display:none}
body.skeleton-live-v20 #editorScreen .skeleton-only-tool{display:block}
body.skeleton-live-v20 #editorScreen #objectCameraPad{display:flex!important}
body.skeleton-live-v20 #editorScreen #objectTrackpadDrawer{display:block!important}
body.skeleton-live-v20 #editorScreen #liveEditBadge{display:block!important}
'''
s=s.replace('</style>',css+'\n</style>',1)

idx=s.rfind('</script>')
if idx<0: raise SystemExit('script end missing')
js=r'''
// SKELETON_LIVE_EDIT_V20
(function(){
 const editor=$('editorScreen'), rail=editor?.querySelector('.toolrail'), viewport=editor?.querySelector('.viewport'), viewtools=editor?.querySelector('.viewtools');
 if(!editor||!rail||!viewport||!viewtools)return;

 let skeletonLiveEditMode=false;
 let skeletonVisible=false;
 let skeletonHelper=null;
 let selectedBone=null;
 let skeletonTransformMode='rotate';
 let touchId=null,startX=0,startY=0,startPos=null,startQuat=null,startScale=null;

 const makeTool=(icon,label,id,cls='')=>{const b=document.createElement('button');b.type='button';b.id=id;b.className='object-extra-tool '+cls;b.innerHTML='<b>'+icon+'</b>'+label;return b};

 // Right-side Skeleton show/hide button — exactly under Visible.
 const skeletonViewBtn=document.createElement('button');
 skeletonViewBtn.type='button';skeletonViewBtn.id='skeletonViewBtn';
 skeletonViewBtn.innerHTML='<strong>☠</strong>Skeleton';
 viewtools.appendChild(skeletonViewBtn);

 // Bottom-left dedicated Skeleton mode button, below Select.
 const skeletonModeBtn=makeTool('☠','Skeleton','skeletonModeBtn');
 rail.appendChild(skeletonModeBtn);

 // Skeleton-mode-only tools positioned where the design shows them.
 const addBoneBtn=makeTool('☠','Add<br>bone','skeletonAddBoneBtn','skeleton-only-tool');
 const duplicateBoneBtn=makeTool('◩','Duplicate<br>bone','skeletonDuplicateBoneBtn','skeleton-only-tool');
 const rigBtn=makeTool('🕹️','Rig','skeletonRigBtn','skeleton-only-tool');
 const selectBtn=$('liveEditSelectBtn');
 const insertBefore=selectBtn||skeletonModeBtn;
 rail.insertBefore(addBoneBtn,insertBefore);
 rail.insertBefore(duplicateBoneBtn,insertBefore);
 rail.insertBefore(rigBtn,insertBefore);

 function activeModelRoot(){
   try{const l=(typeof selectedModelLayer==='function')?selectedModelLayer():null;if(l?.object)return l.object}catch(_){}
   return root||null;
 }
 function bones(){
   const out=[];const r=activeModelRoot();if(!r)return out;r.traverse(o=>{if(o.isBone)out.push(o)});return out;
 }
 function refreshHelper(){
   if(skeletonHelper){scene.remove(skeletonHelper);try{skeletonHelper.geometry?.dispose?.()}catch(_){}skeletonHelper=null}
   const r=activeModelRoot();if(!r)return;
   const bs=bones();if(!bs.length)return;
   skeletonHelper=new THREE.SkeletonHelper(r);skeletonHelper.visible=skeletonVisible;scene.add(skeletonHelper);
 }
 function syncHelper(){if(!skeletonHelper||skeletonHelper.root!==activeModelRoot())refreshHelper();if(skeletonHelper)skeletonHelper.visible=skeletonVisible}
 function setSkeletonVisible(on){skeletonVisible=!!on;syncHelper();skeletonViewBtn.classList.toggle('on',skeletonVisible)}

 function setSkeletonMode(on){
   skeletonLiveEditMode=!!on;
   window.skeletonLiveEditMode=skeletonLiveEditMode;
   document.body.classList.toggle('skeleton-live-v20',skeletonLiveEditMode);
   skeletonModeBtn.classList.toggle('active',skeletonLiveEditMode);
   if(skeletonLiveEditMode){
     if(typeof setLiveEditSelectMode==='function' && typeof liveEditSelectMode!=='undefined' && liveEditSelectMode)setLiveEditSelectMode(false);
     controls.enabled=false;setSkeletonVisible(true);
     const badge=$('liveEditBadge');if(badge){badge.textContent='LIVE EDIT Skeleton';badge.classList.add('on')}
   }else{
     controls.enabled=true;selectedBone=null;touchId=null;
     const badge=$('liveEditBadge');if(badge){badge.textContent='LIVE EDIT';badge.classList.remove('on')}
   }
 }

 skeletonViewBtn.onclick=()=>setSkeletonVisible(!skeletonVisible);
 skeletonModeBtn.onclick=()=>setSkeletonMode(!skeletonLiveEditMode);

 function projectedBoneAt(x,y){
   const bs=bones();if(!bs.length)return null;
   const rect=canvas.getBoundingClientRect();let best=null,bestD=34;
   const v=new THREE.Vector3();
   for(const b of bs){
     b.getWorldPosition(v);v.project(camera);
     if(v.z<-1||v.z>1)continue;
     const sx=rect.left+(v.x*.5+.5)*rect.width, sy=rect.top+(-v.y*.5+.5)*rect.height;
     const d=Math.hypot(x-sx,y-sy);if(d<bestD){bestD=d;best=b}
   }
   return best;
 }
 function chooseBone(x,y){const b=projectedBoneAt(x,y);if(b){selectedBone=b;return true}return false}

 function currentRailMode(){
   const tools=[...rail.querySelectorAll('.tool')];
   const active=tools.find(b=>b.classList.contains('active'));
   const t=(active?.textContent||'').toLowerCase();
   if(t.includes('move'))return'move';if(t.includes('scale'))return'scale';return'rotate';
 }
 rail.addEventListener('click',e=>{
   if(!skeletonLiveEditMode)return;const b=e.target.closest('.tool');if(!b)return;
   const t=(b.textContent||'').toLowerCase();if(t.includes('move'))skeletonTransformMode='move';else if(t.includes('scale'))skeletonTransformMode='scale';else if(t.includes('rotate'))skeletonTransformMode='rotate';
 },true);

 canvas.addEventListener('touchstart',e=>{
   if(!skeletonLiveEditMode||e.touches.length!==1)return;
   const t=e.touches[0];
   if(!selectedBone||!chooseBone(t.clientX,t.clientY)){ if(!chooseBone(t.clientX,t.clientY))return; }
   touchId=t.identifier;startX=t.clientX;startY=t.clientY;
   startPos=selectedBone.position.clone();startQuat=selectedBone.quaternion.clone();startScale=selectedBone.scale.clone();
   skeletonTransformMode=currentRailMode();
   e.preventDefault();e.stopPropagation();
 },{capture:true,passive:false});
 canvas.addEventListener('touchmove',e=>{
   if(!skeletonLiveEditMode||touchId==null||!selectedBone)return;
   const t=[...e.touches].find(q=>q.identifier===touchId);if(!t)return;
   const dx=t.clientX-startX,dy=t.clientY-startY;
   if(skeletonTransformMode==='move'){
     const dist=Math.max(.1,camera.position.distanceTo(controls.target)),k=dist*.0035;
     const right=new THREE.Vector3(1,0,0).applyQuaternion(camera.quaternion);
     const up=new THREE.Vector3(0,1,0).applyQuaternion(camera.quaternion);
     const worldDelta=right.multiplyScalar(dx*k).add(up.multiplyScalar(-dy*k));
     const parent=selectedBone.parent;
     if(parent){const inv=new THREE.Matrix4().copy(parent.matrixWorld).invert();const local0=startPos.clone();const wp=parent.localToWorld(local0.clone());wp.add(worldDelta);selectedBone.position.copy(parent.worldToLocal(wp));}
     else selectedBone.position.copy(startPos).add(worldDelta);
   }else if(skeletonTransformMode==='scale'){
     const f=Math.max(.05,Math.min(20,Math.exp(-dy*.012)));selectedBone.scale.copy(startScale).multiplyScalar(f);
   }else{
     const qx=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1,0,0),dy*.012);
     const qy=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),dx*.012);
     selectedBone.quaternion.copy(startQuat).multiply(qy).multiply(qx);
   }
   selectedBone.updateMatrixWorld(true);if(typeof skeletonHelper?.update==='function')skeletonHelper.update();
   e.preventDefault();e.stopPropagation();
 },{capture:true,passive:false});
 const endTouch=e=>{if(!skeletonLiveEditMode)return;touchId=null;startPos=startQuat=startScale=null};
 canvas.addEventListener('touchend',endTouch,{capture:true});canvas.addEventListener('touchcancel',endTouch,{capture:true});

 addBoneBtn.onclick=()=>{
   if(!skeletonLiveEditMode)return;
   const parent=selectedBone||bones()[0];if(!parent){msg('Skeleton tidak ditemukan');return}
   const b=new THREE.Bone();b.name='Bone';b.position.set(0,.1,0);parent.add(b);selectedBone=b;refreshHelper();setSkeletonVisible(true);
 };
 duplicateBoneBtn.onclick=()=>{
   if(!skeletonLiveEditMode||!selectedBone){msg('Pilih bone dulu');return}
   const parent=selectedBone.parent;if(!parent)return;
   const b=new THREE.Bone();b.name=(selectedBone.name||'Bone')+'_copy';b.position.copy(selectedBone.position);b.quaternion.copy(selectedBone.quaternion);b.scale.copy(selectedBone.scale);parent.add(b);selectedBone=b;refreshHelper();setSkeletonVisible(true);
 };
 rigBtn.onclick=()=>{
   if(!skeletonLiveEditMode)return;
   const r=activeModelRoot();if(!r){msg('Model tidak ditemukan');return}
   let count=0;r.traverse(o=>{if(o.isSkinnedMesh&&o.skeleton){o.bind(o.skeleton,o.bindMatrix);count++}});refreshHelper();setSkeletonVisible(true);msg(count?'Rig diperbarui':'SkinnedMesh tidak ditemukan');
 };

 // Trackpad behavior in Skeleton mode, using the exact same drawer/surface from the Object design.
 const surf=$('objectTrackpadSurface');if(surf){
   let pId=null,lx=0,ly=0;
   surf.addEventListener('touchstart',e=>{if(!skeletonLiveEditMode||e.touches.length!==1)return;const t=e.touches[0];pId=t.identifier;lx=t.clientX;ly=t.clientY;e.preventDefault();e.stopPropagation()},{capture:true,passive:false});
   surf.addEventListener('touchmove',e=>{if(!skeletonLiveEditMode||pId==null)return;const t=[...e.touches].find(q=>q.identifier===pId);if(!t)return;const dx=t.clientX-lx,dy=t.clientY-ly;lx=t.clientX;ly=t.clientY;const off=camera.position.clone().sub(controls.target),sp=new THREE.Spherical().setFromVector3(off);sp.theta-=dx*.0105;sp.phi-=dy*.0105;sp.phi=Math.max(.035,Math.min(Math.PI-.035,sp.phi));off.setFromSpherical(sp);camera.position.copy(controls.target).add(off);camera.lookAt(controls.target);camera.updateMatrixWorld(true);e.preventDefault();e.stopPropagation()},{capture:true,passive:false});
   surf.addEventListener('touchend',()=>{pId=null},{capture:true});surf.addEventListener('touchcancel',()=>{pId=null},{capture:true});
 }

 setInterval(()=>{syncHelper();if(skeletonLiveEditMode){controls.enabled=false;const badge=$('liveEditBadge');if(badge){badge.textContent='LIVE EDIT Skeleton';badge.classList.add('on')}}},300);
})();
'''
s=s[:idx]+js+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Skeleton Live Edit v20 applied')
