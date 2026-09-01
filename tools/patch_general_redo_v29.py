from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'GENERAL_REDO_V29' in s:
    print('General Redo v29 already applied'); raise SystemExit(0)
if 'SKELETON_TOOL_ROUTES_V21' not in s or 'OBJECT_UNDO_REDO_V12' not in s:
    raise SystemExit('Redo dependencies missing')

s=s.replace('</style>',r'''
/* GENERAL_REDO_V29 — one standalone Redo UI for every edit mode */
#editorScreen #objectRedoBtn,#editorScreen #skeletonRedoBtn{display:none!important}
#editorScreen #generalRedoBtn{display:block!important;border:1px solid #33465b;background:transparent;color:#ccd4de}
#editorScreen #generalRedoBtn b{color:#fff}
#editorScreen #generalRedoBtn:active{background:#17304c;color:#69adff}
</style>''',1)

anchor=" setInterval(()=>{syncHelper();if(skeletonLiveEditMode){controls.enabled=false;const badge=$('liveEditBadge');if(badge){badge.textContent='LIVE EDIT Skeleton';badge.classList.add('on')}}},300);"
if anchor not in s:
    raise SystemExit('Skeleton interval anchor missing')

js=r'''
 // GENERAL_REDO_V29
 // A completely new physical Redo button. It is not objectRedoBtn and not
 // skeletonRedoBtn, so legacy touch/click handlers cannot intercept it.
 const generalRedoBtnV29=document.createElement('button');
 generalRedoBtnV29.type='button';
 generalRedoBtnV29.id='generalRedoBtn';
 generalRedoBtnV29.className='object-extra-tool';
 generalRedoBtnV29.innerHTML='<b>→</b>Redo';
 const undoPhysicalV29=$('objectUndoBtn');
 if(undoPhysicalV29?.parentNode)undoPhysicalV29.parentNode.insertBefore(generalRedoBtnV29,undoPhysicalV29.nextSibling);

 function runGeneralRedoV29(){
   // Redo is general at UI level; the current editor owns the operation.
   if(window.skeletonLiveEditMode){
     skeletonRedoActionV21();
     return;
   }
   if(typeof window.objectRedoActionV12==='function'){
     window.objectRedoActionV12();
     return;
   }
   msg('Tidak ada perubahan untuk Redo');
 }

 let generalRedoTouchAtV29=0;
 generalRedoBtnV29.addEventListener('touchstart',ev=>{
   ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();
 },{capture:true,passive:false});
 generalRedoBtnV29.addEventListener('touchend',ev=>{
   ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();
   generalRedoTouchAtV29=Date.now();runGeneralRedoV29();
 },{capture:true,passive:false});
 generalRedoBtnV29.addEventListener('click',ev=>{
   ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();
   if(Date.now()-generalRedoTouchAtV29<900)return;
   runGeneralRedoV29();
 },true);

 // Never native-disable the general Redo button. Empty-history handling happens
 // inside the owning history engine, avoiding Android WebView disabled-state bugs.
 setInterval(()=>{
   generalRedoBtnV29.disabled=false;
   generalRedoBtnV29.style.pointerEvents='auto';
   generalRedoBtnV29.style.opacity='1';
 },100);
'''

s=s.replace(anchor,js+'\n'+anchor,1)
p.write_text(s,encoding='utf-8')
print('General Redo v29 applied')
