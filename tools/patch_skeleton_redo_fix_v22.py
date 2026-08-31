from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'SKELETON_REDO_FIX_V22' in s:
    print('Skeleton redo fix v22 already applied'); raise SystemExit(0)
if 'SKELETON_TOOL_ROUTES_V21' not in s:
    raise SystemExit('Skeleton tool routes v21 must run first')

# V21 now owns immutable/cloned history snapshots and already keeps the shared
# Undo/Redo buttons natively enabled in Skeleton mode. V22 remains as the
# Android-WebView compatibility layer, but must accept both the old multiline
# V21 implementation and the newer compact implementation.
legacy=""" function syncSkeletonUndoButtonsV21(){
   if(!skeletonLiveEditMode)return;
   if(undoBtnV21){undoBtnV21.disabled=!skeletonUndoV21.length;undoBtnV21.style.opacity=skeletonUndoV21.length?'1':'.38'}
   if(redoBtnV21){redoBtnV21.disabled=!skeletonRedoV21.length;redoBtnV21.style.opacity=skeletonRedoV21.length?'1':'.38'}
 }"""
legacy_fixed=""" function syncSkeletonUndoButtonsV21(){
   if(!skeletonLiveEditMode)return;
   // SKELETON_REDO_FIX_V22
   if(undoBtnV21){undoBtnV21.disabled=false;undoBtnV21.setAttribute('aria-disabled',skeletonUndoV21.length?'false':'true');undoBtnV21.style.opacity=skeletonUndoV21.length?'1':'.38'}
   if(redoBtnV21){redoBtnV21.disabled=false;redoBtnV21.setAttribute('aria-disabled',skeletonRedoV21.length?'false':'true');redoBtnV21.style.opacity=skeletonRedoV21.length?'1':'.38'}
 }"""
compact="function syncSkeletonUndoButtonsV21(){if(!skeletonLiveEditMode)return;if(undoBtnV21){undoBtnV21.disabled=false;undoBtnV21.style.opacity=skeletonUndoV21.length?'1':'.38'}if(redoBtnV21){redoBtnV21.disabled=false;redoBtnV21.style.opacity=skeletonRedoV21.length?'1':'.38'}}"
compact_fixed="function syncSkeletonUndoButtonsV21(){/* SKELETON_REDO_FIX_V22 */if(!skeletonLiveEditMode)return;if(undoBtnV21){undoBtnV21.disabled=false;undoBtnV21.setAttribute('aria-disabled',skeletonUndoV21.length?'false':'true');undoBtnV21.style.opacity=skeletonUndoV21.length?'1':'.38'}if(redoBtnV21){redoBtnV21.disabled=false;redoBtnV21.setAttribute('aria-disabled',skeletonRedoV21.length?'false':'true');redoBtnV21.style.opacity=skeletonRedoV21.length?'1':'.38'}}"

if legacy in s:
    s=s.replace(legacy,legacy_fixed,1)
elif compact in s:
    s=s.replace(compact,compact_fixed,1)
else:
    # If V21 changes formatting again, do not break the whole APK build. Confirm
    # the required behavior exists, then attach the V22 marker beside the route.
    required=['undoBtnV21.disabled=false','redoBtnV21.disabled=false','skeletonRedoActionV21']
    if not all(x in s for x in required):
        raise SystemExit('Skeleton V21 Redo compatibility behavior missing')
    s=s.replace('// SKELETON_TOOL_ROUTES_V21','// SKELETON_TOOL_ROUTES_V21\n // SKELETON_REDO_FIX_V22',1)

# The current V21 cloned-history implementation already performs the stable
# Undo -> Redo stack transfer. Do not rewrite those functions again here.
# Just make Skeleton accessibility state explicit when leaving the mode.
exit_old="else{if(undoBtnV21){undoBtnV21.disabled=false;undoBtnV21.style.opacity=''}if(redoBtnV21){redoBtnV21.disabled=false;redoBtnV21.style.opacity=''}}"
exit_new="else{if(undoBtnV21){undoBtnV21.disabled=false;undoBtnV21.removeAttribute('aria-disabled');undoBtnV21.style.opacity=''}if(redoBtnV21){redoBtnV21.disabled=false;redoBtnV21.removeAttribute('aria-disabled');redoBtnV21.style.opacity=''}}"
if exit_old in s:
    s=s.replace(exit_old,exit_new,1)

p.write_text(s,encoding='utf-8')
print('Skeleton Redo v22 compatibility applied')
