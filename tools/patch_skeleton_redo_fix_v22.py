from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'SKELETON_REDO_FIX_V22' in s:
    print('Skeleton redo fix v22 already applied'); raise SystemExit(0)
if 'SKELETON_TOOL_ROUTES_V21' not in s:
    raise SystemExit('Skeleton tool routes v21 must run first')

# A disabled HTML button does not dispatch click/touch events in Android WebView.
# Object history v12 and Skeleton history v21 both manipulated the same disabled
# attribute, which could leave Redo physically unclickable after Skeleton Undo.
old=""" function syncSkeletonUndoButtonsV21(){
   if(!skeletonLiveEditMode)return;
   if(undoBtnV21){undoBtnV21.disabled=!skeletonUndoV21.length;undoBtnV21.style.opacity=skeletonUndoV21.length?'1':'.38'}
   if(redoBtnV21){redoBtnV21.disabled=!skeletonRedoV21.length;redoBtnV21.style.opacity=skeletonRedoV21.length?'1':'.38'}
 }"""
new=""" function syncSkeletonUndoButtonsV21(){
   if(!skeletonLiveEditMode)return;
   // SKELETON_REDO_FIX_V22: never use native disabled in Skeleton mode.
   // Keep the visual state only; the dedicated Skeleton handler decides whether
   // an Undo/Redo entry exists. This guarantees Android WebView still delivers
   // the event to the Skeleton route.
   if(undoBtnV21){undoBtnV21.disabled=false;undoBtnV21.setAttribute('aria-disabled',skeletonUndoV21.length?'false':'true');undoBtnV21.style.opacity=skeletonUndoV21.length?'1':'.38'}
   if(redoBtnV21){redoBtnV21.disabled=false;redoBtnV21.setAttribute('aria-disabled',skeletonRedoV21.length?'false':'true');redoBtnV21.style.opacity=skeletonRedoV21.length?'1':'.38'}
 }"""
if old not in s: raise SystemExit('Skeleton undo button sync marker missing')
s=s.replace(old,new,1)

# Make Undo/Redo transitions explicit and update world/skeleton matrices before
# changing the opposite stack. This also makes repeated Undo -> Redo cycles stable.
old2=""" function skeletonUndoActionV21(){const h=skeletonUndoV21.pop();if(!h){msg('Skeleton: tidak ada Undo');return}applyBoneStateV21(h.before);skeletonRedoV21.push(h);syncSkeletonUndoButtonsV21()}
 function skeletonRedoActionV21(){const h=skeletonRedoV21.pop();if(!h){msg('Skeleton: tidak ada Redo');return}applyBoneStateV21(h.after);skeletonUndoV21.push(h);syncSkeletonUndoButtonsV21()}"""
new2=""" function skeletonUndoActionV21(){
   const h=skeletonUndoV21.pop();if(!h){syncSkeletonUndoButtonsV21();msg('Skeleton: tidak ada Undo');return}
   applyBoneStateV21(h.before);if(h.before?.bone?.skeleton)try{h.before.bone.skeleton.update()}catch(_){}
   skeletonRedoV21.push(h);syncSkeletonUndoButtonsV21();msg('Skeleton Undo');
 }
 function skeletonRedoActionV21(){
   const h=skeletonRedoV21.pop();if(!h){syncSkeletonUndoButtonsV21();msg('Skeleton: tidak ada Redo');return}
   applyBoneStateV21(h.after);if(h.after?.bone?.skeleton)try{h.after.bone.skeleton.update()}catch(_){}
   skeletonUndoV21.push(h);syncSkeletonUndoButtonsV21();msg('Skeleton Redo');
 }"""
if old2 not in s: raise SystemExit('Skeleton undo/redo action marker missing')
s=s.replace(old2,new2,1)

# When leaving Skeleton mode, remove only Skeleton accessibility state and let
# the normal Object/Mesh route restore its own native disabled state later.
old3="""else{if(undoBtnV21){undoBtnV21.disabled=false;undoBtnV21.style.opacity=''}if(redoBtnV21){redoBtnV21.disabled=false;redoBtnV21.style.opacity=''}}"""
new3="""else{if(undoBtnV21){undoBtnV21.disabled=false;undoBtnV21.removeAttribute('aria-disabled');undoBtnV21.style.opacity=''}if(redoBtnV21){redoBtnV21.disabled=false;redoBtnV21.removeAttribute('aria-disabled');redoBtnV21.style.opacity=''}}"""
if old3 not in s: raise SystemExit('Skeleton mode exit button marker missing')
s=s.replace(old3,new3,1)

p.write_text(s,encoding='utf-8')
print('Skeleton Redo v22 fixed for Android WebView')
