from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'SKELETON_DEDICATED_REDO_V28' in s:
    print('Skeleton dedicated Redo v28 already applied'); raise SystemExit(0)
if 'SKELETON_TOOL_ROUTES_V21' not in s:
    raise SystemExit('Skeleton tool routes v21 must run first')

# Add explicit UI separation: the normal Object/Mesh Redo button disappears in
# Skeleton mode, and Skeleton gets its own physical DOM button + event route.
s=s.replace('</style>',r'''
/* SKELETON_DEDICATED_REDO_V28 */
body.skeleton-live-v20 #editorScreen #objectRedoBtn{display:none!important}
#editorScreen #skeletonRedoBtn{display:none}
body.skeleton-live-v20 #editorScreen #skeletonRedoBtn{display:block!important;border:1px solid #7a2b35;background:#24151a;color:#ff6d78}
body.skeleton-live-v20 #editorScreen #skeletonRedoBtn b{color:#ff6d78}
body.skeleton-live-v20 #editorScreen #skeletonRedoBtn.ready{border-color:#2d73b8;background:#132a43;color:#69adff}
body.skeleton-live-v20 #editorScreen #skeletonRedoBtn.ready b{color:#69adff}
</style>''',1)

anchor=" setInterval(()=>{syncHelper();if(skeletonLiveEditMode){controls.enabled=false;const badge=$('liveEditBadge');if(badge){badge.textContent='LIVE EDIT Skeleton';badge.classList.add('on')}}},300);"
if anchor not in s:
    raise SystemExit('Skeleton interval anchor missing')

js=r'''
 // SKELETON_DEDICATED_REDO_V28
 // Dedicated physical Redo control for Skeleton mode. Object/Mesh Redo remains
 // objectRedoBtn and is never used by this route.
 const objectRedoPhysicalV28=$('objectRedoBtn');
 const skeletonRedoPhysicalV28=document.createElement('button');
 skeletonRedoPhysicalV28.type='button';
 skeletonRedoPhysicalV28.id='skeletonRedoBtn';
 skeletonRedoPhysicalV28.className='object-extra-tool';
 skeletonRedoPhysicalV28.innerHTML='<b>↪</b>Redo<br>Skeleton';
 if(objectRedoPhysicalV28?.parentNode){
   objectRedoPhysicalV28.parentNode.insertBefore(skeletonRedoPhysicalV28,objectRedoPhysicalV28.nextSibling);
 }

 function syncDedicatedSkeletonRedoV28(){
   if(!skeletonLiveEditMode)return;
   skeletonRedoPhysicalV28.disabled=false;
   skeletonRedoPhysicalV28.style.pointerEvents='auto';
   const ready=typeof skeletonRedoV21!=='undefined' && skeletonRedoV21.length>0;
   skeletonRedoPhysicalV28.classList.toggle('ready',ready);
   skeletonRedoPhysicalV28.style.opacity=ready?'1':'.48';
   skeletonRedoPhysicalV28.setAttribute('aria-disabled',ready?'false':'true');
 }
 function runDedicatedSkeletonRedoV28(ev){
   if(!skeletonLiveEditMode)return;
   if(ev){ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();}
   skeletonRedoActionV21();
   syncDedicatedSkeletonRedoV28();
 }
 // Own both Android touch and desktop click; suppress synthetic click after touch.
 let dedicatedRedoTouchAtV28=0;
 skeletonRedoPhysicalV28.addEventListener('touchstart',ev=>{
   if(!skeletonLiveEditMode)return;
   ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();
 },{capture:true,passive:false});
 skeletonRedoPhysicalV28.addEventListener('touchend',ev=>{
   if(!skeletonLiveEditMode)return;
   dedicatedRedoTouchAtV28=Date.now();
   runDedicatedSkeletonRedoV28(ev);
 },{capture:true,passive:false});
 skeletonRedoPhysicalV28.addEventListener('click',ev=>{
   if(!skeletonLiveEditMode)return;
   if(Date.now()-dedicatedRedoTouchAtV28<1000){ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();return;}
   runDedicatedSkeletonRedoV28(ev);
 },true);

 // Keep the visual state tied only to the Skeleton redo stack.
 setInterval(syncDedicatedSkeletonRedoV28,80);
'''

s=s.replace(anchor,js+'\n'+anchor,1)
p.write_text(s,encoding='utf-8')
print('Skeleton dedicated Redo v28 applied')
