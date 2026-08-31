from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'SKELETON_VISUAL_V23' in s:
    print('Skeleton visual v23 already applied'); raise SystemExit(0)
if 'SKELETON_LIVE_EDIT_V20' not in s:
    raise SystemExit('Skeleton Live Edit v20 must run first')

anchor=" setInterval(()=>{syncHelper();if(skeletonLiveEditMode){controls.enabled=false;const badge=$('liveEditBadge');if(badge){badge.textContent='LIVE EDIT Skeleton';badge.classList.add('on')}}},300);"
if anchor not in s:
    raise SystemExit('Skeleton interval anchor missing')

js=r'''
 // SKELETON_VISUAL_V23
 // Custom skeleton display inspired by the supplied reference: lime bones, orange joints,
 // with only the selected bone/joint turning red. This changes visualization only;
 // THREE.Bone hierarchy, skinning and rig data are untouched.
 const skeletonVisualV23=new THREE.Group();
 skeletonVisualV23.name='SkeletonVisualV23';
 skeletonVisualV23.renderOrder=999;
 scene.add(skeletonVisualV23);
 const boneVisualsV23=new Map();
 const limeV23=0x9cff00, orangeV23=0xffad42, redV23=0xff2a2a;
 const boneGeoV23=new THREE.CylinderGeometry(1,1,1,8,1,false);
 const jointGeoV23=new THREE.SphereGeometry(1,12,8);
 const matV23=c=>new THREE.MeshBasicMaterial({color:c,depthTest:false,depthWrite:false,transparent:true,opacity:.98});
 const boneMatV23=matV23(limeV23), boneSelectedMatV23=matV23(redV23);
 const jointMatV23=matV23(orangeV23), jointSelectedMatV23=matV23(redV23);
 const yAxisV23=new THREE.Vector3(0,1,0), aV23=new THREE.Vector3(), bV23=new THREE.Vector3(), dV23=new THREE.Vector3();
 let skeletonVisualRootV23=null;
 function modelScaleV23(){
   const r=activeModelRoot();if(!r)return 1;
   const box=new THREE.Box3().setFromObject(r);if(box.isEmpty())return 1;
   const sz=new THREE.Vector3();box.getSize(sz);return Math.max(.001,Math.max(sz.x,sz.y,sz.z));
 }
 function disposeBoneVisualV23(v){
   if(!v)return;
   if(v.segment)skeletonVisualV23.remove(v.segment);
   if(v.joint)skeletonVisualV23.remove(v.joint);
 }
 function ensureBoneVisualV23(b){
   let v=boneVisualsV23.get(b.uuid);if(v)return v;
   const joint=new THREE.Mesh(jointGeoV23,jointMatV23);joint.renderOrder=1001;joint.frustumCulled=false;
   let segment=null;
   if(b.parent?.isBone){segment=new THREE.Mesh(boneGeoV23,boneMatV23);segment.renderOrder=1000;segment.frustumCulled=false;}
   v={bone:b,joint,segment};boneVisualsV23.set(b.uuid,v);skeletonVisualV23.add(joint);if(segment)skeletonVisualV23.add(segment);return v;
 }
 function rebuildSkeletonVisualV23(){
   for(const v of boneVisualsV23.values())disposeBoneVisualV23(v);boneVisualsV23.clear();
   skeletonVisualRootV23=activeModelRoot();
   for(const b of bones())ensureBoneVisualV23(b);
 }
 function updateSkeletonVisualV23(){
   const r=activeModelRoot();
   if(r!==skeletonVisualRootV23||boneVisualsV23.size!==bones().length)rebuildSkeletonVisualV23();
   const visible=!!skeletonVisible;
   skeletonVisualV23.visible=visible;
   // Hide the old THREE.SkeletonHelper so only the custom design is visible.
   if(skeletonHelper)skeletonHelper.visible=false;
   if(!visible)return;
   const unit=modelScaleV23();
   const radius=Math.max(unit*.0045,.0025), jointRadius=Math.max(unit*.0105,.006);
   for(const v of boneVisualsV23.values()){
     const b=v.bone, selected=(b===selectedBone);
     b.getWorldPosition(bV23);
     v.joint.position.copy(bV23);v.joint.scale.setScalar(jointRadius);v.joint.material=selected?jointSelectedMatV23:jointMatV23;
     if(v.segment&&b.parent?.isBone){
       b.parent.getWorldPosition(aV23);dV23.subVectors(bV23,aV23);const len=dV23.length();
       if(len>1e-7){
         v.segment.visible=true;v.segment.position.copy(aV23).addScaledVector(dV23,.5);
         v.segment.quaternion.setFromUnitVectors(yAxisV23,dV23.clone().normalize());
         v.segment.scale.set(radius,len,radius);v.segment.material=selected?boneSelectedMatV23:boneMatV23;
       }else v.segment.visible=false;
     }
   }
 }
 // Make touching the shaft count as touching that bone, not only the orange joint.
 function distPointSegV23(px,py,ax,ay,bx,by){
   const vx=bx-ax,vy=by-ay,wx=px-ax,wy=py-ay,den=vx*vx+vy*vy;
   const t=den?Math.max(0,Math.min(1,(wx*vx+wy*vy)/den)):0;
   return Math.hypot(px-(ax+t*vx),py-(ay+t*vy));
 }
 projectedBoneAt=function(x,y){
   const bs=bones();if(!bs.length)return null;
   const rect=canvas.getBoundingClientRect();let best=null,bestD=38;
   const wp=new THREE.Vector3(), pp=new THREE.Vector3(), sp=new Map();
   const screenOf=b=>{let q=sp.get(b);if(q)return q;b.getWorldPosition(wp);pp.copy(wp).project(camera);q={x:rect.left+(pp.x*.5+.5)*rect.width,y:rect.top+(-pp.y*.5+.5)*rect.height,z:pp.z};sp.set(b,q);return q};
   for(const b of bs){
     const q=screenOf(b);if(q.z<-1||q.z>1)continue;
     let d=Math.hypot(x-q.x,y-q.y);
     if(b.parent?.isBone){const p=screenOf(b.parent);if(p.z>=-1&&p.z<=1)d=Math.min(d,distPointSegV23(x,y,p.x,p.y,q.x,q.y));}
     if(d<bestD){bestD=d;best=b}
   }
   return best;
 };
 const oldSetSkeletonVisibleV23=setSkeletonVisible;
 setSkeletonVisible=function(on){oldSetSkeletonVisibleV23(on);updateSkeletonVisualV23()};
 setInterval(updateSkeletonVisualV23,50);
'''

s=s.replace(anchor,js+'\n'+anchor,1)
p.write_text(s,encoding='utf-8')
print('Skeleton visual v23 applied: lime bones, orange joints, selected bone red')
