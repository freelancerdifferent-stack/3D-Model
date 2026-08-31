from pathlib import Path
import subprocess

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'SKELETON_REDO_TOUCH_V25' in s:
    print('Skeleton redo touch v25 already applied')
else:
    if 'SKELETON_REDO_FIX_V22' not in s:
        raise SystemExit('Skeleton redo fix v22 must run first')

    anchor=" setInterval(()=>{syncHelper();if(skeletonLiveEditMode){controls.enabled=false;const badge=$('liveEditBadge');if(badge){badge.textContent='LIVE EDIT Skeleton';badge.classList.add('on')}}},300);"
    if anchor not in s:
        raise SystemExit('Skeleton interval anchor missing')

    js=r'''
 // SKELETON_REDO_TOUCH_V25
 // Android WebView can still let the Object history route overwrite the shared
 // button state between Skeleton updates. Own the physical touch route directly
 // while Skeleton mode is active, and keep the shared buttons natively enabled.
 let skeletonHistoryTouchHandledV25=false;
 function forceSkeletonHistoryButtonsV25(){
   if(!skeletonLiveEditMode)return;
   if(undoBtnV21){undoBtnV21.disabled=false;undoBtnV21.style.pointerEvents='auto'}
   if(redoBtnV21){redoBtnV21.disabled=false;redoBtnV21.style.pointerEvents='auto'}
   syncSkeletonUndoButtonsV21();
 }
 function bindSkeletonHistoryTouchV25(btn,action){
   if(!btn)return;
   btn.addEventListener('touchstart',ev=>{
     if(!skeletonLiveEditMode)return;
     btn.disabled=false;
     ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();
   },{capture:true,passive:false});
   btn.addEventListener('touchend',ev=>{
     if(!skeletonLiveEditMode)return;
     ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();
     skeletonHistoryTouchHandledV25=true;
     action();
     setTimeout(()=>{skeletonHistoryTouchHandledV25=false;forceSkeletonHistoryButtonsV25()},0);
   },{capture:true,passive:false});
 }
 bindSkeletonHistoryTouchV25(undoBtnV21,skeletonUndoActionV21);
 bindSkeletonHistoryTouchV25(redoBtnV21,skeletonRedoActionV21);
 // Prevent the synthetic click fired after touchend from executing Undo/Redo twice.
 document.addEventListener('click',ev=>{
   if(!skeletonLiveEditMode||!skeletonHistoryTouchHandledV25)return;
   const b=ev.target.closest('button');
   if(b===undoBtnV21||b===redoBtnV21){ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation()}
 },true);
 setInterval(forceSkeletonHistoryButtonsV25,80);
'''

    s=s.replace(anchor,js+'\n'+anchor,1)
    p.write_text(s,encoding='utf-8')
    print('Skeleton Redo touch v25 applied')

# Build pipeline already executes v25 after v24. Chain the functional Rig patch
# here so existing workflow order stays stable while Rig v26 is applied immediately.
subprocess.run(['python3','tools/patch_skeleton_rig_v26.py'],check=True)
