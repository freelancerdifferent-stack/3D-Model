from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'SKELETON_TRACKPAD_ZOOM_V27' in s:
    print('Skeleton trackpad zoom v27 already applied'); raise SystemExit(0)
if 'SKELETON_LIVE_EDIT_V20' not in s:
    raise SystemExit('Skeleton Live Edit v20 must run first')

old=r''' const surf=$('objectTrackpadSurface');if(surf){
   let pId=null,lx=0,ly=0;
   surf.addEventListener('touchstart',e=>{if(!skeletonLiveEditMode||e.touches.length!==1)return;const t=e.touches[0];pId=t.identifier;lx=t.clientX;ly=t.clientY;e.preventDefault();e.stopPropagation()},{capture:true,passive:false});
   surf.addEventListener('touchmove',e=>{if(!skeletonLiveEditMode||pId==null)return;const t=[...e.touches].find(q=>q.identifier===pId);if(!t)return;const dx=t.clientX-lx,dy=t.clientY-ly;lx=t.clientX;ly=t.clientY;const off=camera.position.clone().sub(controls.target),sp=new THREE.Spherical().setFromVector3(off);sp.theta-=dx*.0105;sp.phi-=dy*.0105;sp.phi=Math.max(.035,Math.min(Math.PI-.035,sp.phi));off.setFromSpherical(sp);camera.position.copy(controls.target).add(off);camera.lookAt(controls.target);camera.updateMatrixWorld(true);e.preventDefault();e.stopPropagation()},{capture:true,passive:false});
   surf.addEventListener('touchend',()=>{pId=null},{capture:true});surf.addEventListener('touchcancel',()=>{pId=null},{capture:true});
 }'''
new=r''' const surf=$('objectTrackpadSurface');if(surf){
   // SKELETON_TRACKPAD_ZOOM_V27
   // One finger = orbit. Two fingers = pinch zoom, isolated to Skeleton Live Edit.
   let pId=null,lx=0,ly=0,pinchDist=0;
   const touchDistanceV27=ts=>ts.length<2?0:Math.hypot(ts[0].clientX-ts[1].clientX,ts[0].clientY-ts[1].clientY);
   const orbitDistanceV27=()=>Math.max(.0001,camera.position.distanceTo(controls.target));
   const clampZoomDistanceV27=d=>{
     const min=(Number.isFinite(controls.minDistance)&&controls.minDistance>0)?controls.minDistance:.02;
     const max=(Number.isFinite(controls.maxDistance)&&controls.maxDistance>min)?controls.maxDistance:1e7;
     return Math.max(min,Math.min(max,d));
   };
   surf.addEventListener('touchstart',e=>{
     if(!skeletonLiveEditMode)return;
     if(e.touches.length>=2){
       pId=null;pinchDist=touchDistanceV27(e.touches);
       e.preventDefault();e.stopPropagation();return;
     }
     if(e.touches.length===1){
       const t=e.touches[0];pId=t.identifier;lx=t.clientX;ly=t.clientY;pinchDist=0;
       e.preventDefault();e.stopPropagation();
     }
   },{capture:true,passive:false});
   surf.addEventListener('touchmove',e=>{
     if(!skeletonLiveEditMode)return;
     if(e.touches.length>=2){
       const d=touchDistanceV27(e.touches);
       if(pinchDist>0&&d>0){
         const current=orbitDistanceV27();
         // Fingers spreading apart => zoom in; pinching together => zoom out.
         const next=clampZoomDistanceV27(current*(pinchDist/d));
         const dir=camera.position.clone().sub(controls.target).normalize();
         camera.position.copy(controls.target).addScaledVector(dir,next);
         camera.lookAt(controls.target);camera.updateMatrixWorld(true);
       }
       pinchDist=d;pId=null;
       e.preventDefault();e.stopPropagation();return;
     }
     if(e.touches.length===1){
       const t=e.touches[0];
       if(pId==null){pId=t.identifier;lx=t.clientX;ly=t.clientY;pinchDist=0;e.preventDefault();e.stopPropagation();return;}
       if(t.identifier!==pId)return;
       const dx=t.clientX-lx,dy=t.clientY-ly;lx=t.clientX;ly=t.clientY;
       const off=camera.position.clone().sub(controls.target),sp=new THREE.Spherical().setFromVector3(off);
       sp.theta-=dx*.0105;sp.phi-=dy*.0105;sp.phi=Math.max(.035,Math.min(Math.PI-.035,sp.phi));
       off.setFromSpherical(sp);camera.position.copy(controls.target).add(off);camera.lookAt(controls.target);camera.updateMatrixWorld(true);
       e.preventDefault();e.stopPropagation();
     }
   },{capture:true,passive:false});
   const finishV27=e=>{
     if(!skeletonLiveEditMode)return;
     if(e.touches&&e.touches.length>=2){pinchDist=touchDistanceV27(e.touches);pId=null;return;}
     if(e.touches&&e.touches.length===1){const t=e.touches[0];pId=t.identifier;lx=t.clientX;ly=t.clientY;pinchDist=0;return;}
     pId=null;pinchDist=0;
   };
   surf.addEventListener('touchend',finishV27,{capture:true});surf.addEventListener('touchcancel',()=>{pId=null;pinchDist=0},{capture:true});
 }'''
if old not in s:
    raise SystemExit('Skeleton trackpad V20 marker missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('Skeleton trackpad zoom v27 applied: orbit + pinch zoom')
