from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'SKELETON_UNDO_REDO_V29' in s:
    print('Skeleton undo/redo v29 already applied'); raise SystemExit(0)
if 'SKELETON_BONE_MANAGE_V24' not in s:
    raise SystemExit('Skeleton bone manage v24 must run first')
if 'SKELETON_RIG_V26' not in s:
    raise SystemExit('Skeleton rig v26 must run first')
if 'skeletonUndoActionV21' in s:
    raise SystemExit('legacy Skeleton history still present; V29 must be the only engine')

css=r'''
/* SKELETON_UNDO_REDO_V29 */
#editorScreen .skel-history-tool[aria-disabled="true"]{opacity:.35}
#editorScreen .skel-history-tool:active{background:#192535;color:#61a6ff}
'''
s=s.replace('</style>',css+'\n</style>',1)

anchor=" setInterval(updateSkeletonVisualV23,50);"
if anchor not in s:
    raise SystemExit('Skeleton visual interval anchor missing')

# Skeleton history lives entirely inside the Skeleton Live Edit closure and is the only
# bone history in the app. It never touches LIVE_EDIT_SELECT_UNDO_V28, which owns mesh
# history and is already inert while Skeleton mode is on.
js=r'''
 // SKELETON_UNDO_REDO_V29
 const skelUndoBtn=makeTool('↶','Undo','skelUndoBtn','skeleton-only-tool skel-history-tool');
 const skelRedoBtn=makeTool('↷','Redo','skelRedoBtn','skeleton-only-tool skel-history-tool');
 const skelHistAnchorV29=$('liveEditSelectBtn')||skeletonModeBtn;
 rail.insertBefore(skelUndoBtn,skelHistAnchorV29);
 rail.insertBefore(skelRedoBtn,skelHistAnchorV29);

 const undoV29=[],redoV29=[];
 const MAX_V29=100;
 let pendingV29=null,lastRootV29=null,suppressClickV29=0;

 function snapV29(b){return b?{pos:b.position.clone(),quat:b.quaternion.clone(),scale:b.scale.clone()}:null}
 function applySnapV29(b,st){if(!b||!st)return;b.position.copy(st.pos);b.quaternion.copy(st.quat);b.scale.copy(st.scale)}
 function sameSnapV29(a,b){
   if(!a||!b)return false;
   return a.pos.distanceToSquared(b.pos)<1e-12 && 1-Math.abs(a.quat.dot(b.quat))<1e-12 && a.scale.distanceToSquared(b.scale)<1e-12;
 }
 // History must never resurrect a bone from a model that is no longer loaded.
 function inModelV29(o){const r=activeModelRoot();if(!r||!o)return false;let q=o;while(q){if(q===r)return true;q=q.parent}return false}
 // Three.js add() always appends, so restore the original sibling order explicitly.
 function attachAtV29(parent,child,index){
   if(!parent||!child)return;
   if(child.parent!==parent){if(child.parent)child.parent.remove(child);parent.add(child)}
   const arr=parent.children,cur=arr.indexOf(child);
   if(cur<0)return;
   let want=index;
   if(!(want>=0))want=arr.length-1;
   if(want>arr.length-1)want=arr.length-1;
   if(want!==cur){arr.splice(cur,1);arr.splice(want,0,child)}
 }
 function refreshStructV29(){
   try{refreshSkeletonAfterManageV24()}
   catch(_){try{refreshHelper();setSkeletonVisible(true)}catch(__){ }}
 }
 function refreshSkelHistUiV29(){
   const cu=skeletonLiveEditMode&&undoV29.length>0, cr=skeletonLiveEditMode&&redoV29.length>0;
   skelUndoBtn.setAttribute('aria-disabled',cu?'false':'true');
   skelRedoBtn.setAttribute('aria-disabled',cr?'false':'true');
 }
 function pushV29(entry){
   if(!entry)return false;
   undoV29.push(entry);
   if(undoV29.length>MAX_V29)undoV29.shift();
   redoV29.length=0;refreshSkelHistUiV29();return true;
 }
 function pushTransformV29(bone,before,after){
   if(!bone||!before||!after||sameSnapV29(before,after))return false;
   return pushV29({kind:'transform',label:'Transform',bone,before,after});
 }

 function applyEntryV29(e,undoing){
   if(e.kind==='transform'){
     if(!inModelV29(e.bone))return false;
     applySnapV29(e.bone,undoing?e.before:e.after);
     e.bone.updateMatrixWorld(true);
     if(skeletonHelper)skeletonHelper.update();
     setSkeletonSelectedBoneV21(e.bone);
     try{updateSkeletonVisualV23()}catch(_){ }
     return true;
   }
   if(e.kind==='add'){
     if(undoing){
       if(!inModelV29(e.bone))return false;
       e.parent.remove(e.bone);
       setSkeletonSelectedBoneV21(e.parent&&e.parent.isBone?e.parent:null);
     }else{
       if(!inModelV29(e.parent))return false;
       attachAtV29(e.parent,e.bone,e.index);
       applySnapV29(e.bone,e.state);
       setSkeletonSelectedBoneV21(e.bone);
     }
     refreshStructV29();return true;
   }
   if(e.kind==='remove'){
     if(undoing){
       if(!inModelV29(e.parent))return false;
       // Pull the promoted children back under the bone with their original local transforms,
       // then put the bone itself back at its original sibling index.
       for(const k of e.kidsBefore){attachAtV29(e.bone,k.bone,k.index);applySnapV29(k.bone,k.state)}
       attachAtV29(e.parent,e.bone,e.index);
       applySnapV29(e.bone,e.state);
       setSkeletonSelectedBoneV21(e.bone);
     }else{
       if(!inModelV29(e.bone))return false;
       for(const k of e.kidsAfter){attachAtV29(e.parent,k.bone,k.index);applySnapV29(k.bone,k.state)}
       e.parent.remove(e.bone);
       setSkeletonSelectedBoneV21(e.parent&&e.parent.isBone?e.parent:null);
     }
     refreshStructV29();return true;
   }
   return false;
 }

 function skeletonUndoActionV29(){
   if(!skeletonLiveEditMode){msg('Undo ini khusus mode Skeleton');return false}
   while(undoV29.length){
     const e=undoV29.pop();
     if(applyEntryV29(e,true)){redoV29.push(e);refreshSkelHistUiV29();msg('Skeleton Undo '+e.label);return true}
   }
   refreshSkelHistUiV29();msg('Skeleton: tidak ada Undo');return false;
 }
 function skeletonRedoActionV29(){
   if(!skeletonLiveEditMode){msg('Redo ini khusus mode Skeleton');return false}
   while(redoV29.length){
     const e=redoV29.pop();
     if(applyEntryV29(e,false)){undoV29.push(e);refreshSkelHistUiV29();msg('Skeleton Redo '+e.label);return true}
   }
   refreshSkelHistUiV29();msg('Skeleton: tidak ada Redo');return false;
 }

 // Android WebView drops synthetic clicks on rail buttons during Skeleton mode, so own the
 // touch sequence and swallow the click it replays afterwards.
 function wireSkelHistV29(btn,fn){
   btn.addEventListener('touchstart',ev=>{ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation()},{capture:true,passive:false});
   btn.addEventListener('touchend',ev=>{ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();suppressClickV29=performance.now()+700;fn()},{capture:true,passive:false});
   btn.addEventListener('click',ev=>{ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();if(performance.now()<suppressClickV29)return;fn()},{capture:true});
 }
 wireSkelHistV29(skelUndoBtn,skeletonUndoActionV29);
 wireSkelHistV29(skelRedoBtn,skeletonRedoActionV29);

 // One bone drag = one entry. These listeners are registered after the V20 gesture handlers,
 // so touchId and selectedBone are already settled when they run.
 canvas.addEventListener('touchstart',()=>{
   if(!skeletonLiveEditMode||window.skeletonRigModeV26)return;
   if(touchId===null||!selectedBone){pendingV29=null;return}
   pendingV29={bone:selectedBone,before:snapV29(selectedBone)};
 },{capture:true,passive:true});
 canvas.addEventListener('touchend',()=>{
   const pend=pendingV29;
   if(!pend)return;
   // Commit after the V20/V21 touchend handler has written the final bone transform.
   setTimeout(()=>{
     if(pendingV29!==pend)return;
     if(touchId!==null)return;
     pendingV29=null;
     pushTransformV29(pend.bone,pend.before,snapV29(pend.bone));
   },0);
 },{capture:true,passive:true});
 canvas.addEventListener('touchcancel',()=>{pendingV29=null},{capture:true,passive:true});

 // Transform panel fields route through applySkeletonFieldV21; wrap it so typed values record too.
 const oldApplySkeletonFieldV29=applySkeletonFieldV21;
 applySkeletonFieldV21=function(id,value){
   const bone=selectedBone, before=bone?snapV29(bone):null;
   const out=oldApplySkeletonFieldV29.apply(this,arguments);
   if(bone&&before)pushTransformV29(bone,before,snapV29(bone));
   return out;
 };

 // V24 assigned these handlers by value, so rebind the buttons rather than the functions.
 function recordAddV29(label,fn){
   if(!skeletonLiveEditMode)return;
   const seen=new Set(bones());
   fn();
   let added=null;
   for(const b of bones())if(!seen.has(b)){added=b;break}
   if(!added||!added.parent)return;
   pushV29({kind:'add',label,bone:added,parent:added.parent,index:added.parent.children.indexOf(added),state:snapV29(added)});
 }
 function recordRemoveV29(fn){
   if(!skeletonLiveEditMode)return;
   const bone=selectedBone;
   if(!bone||!bone.parent){fn();return}
   const parent=bone.parent;
   const index=parent.children.indexOf(bone);
   const state=snapV29(bone);
   const kidsBefore=bone.children.filter(c=>c.isBone).map(c=>({bone:c,index:bone.children.indexOf(c),state:snapV29(c)}));
   fn();
   if(bone.parent===parent)return;   // removal was refused, e.g. bone still used by skinning
   const kidsAfter=kidsBefore.map(k=>({bone:k.bone,index:parent.children.indexOf(k.bone),state:snapV29(k.bone)}));
   pushV29({kind:'remove',label:'Remove Bone',bone,parent,index,state,kidsBefore,kidsAfter});
 }
 addBoneBtn.onclick=()=>recordAddV29('Add Bone',addBoneV24);
 duplicateBoneBtn.onclick=()=>recordAddV29('Duplicate Bone',duplicateBoneV24);
 removeBoneBtn.onclick=()=>recordRemoveV29(removeBoneV24);

 window.skeletonUndoActionV29=skeletonUndoActionV29;
 window.skeletonRedoActionV29=skeletonRedoActionV29;
 window.skeletonHistoryClearV29=()=>{undoV29.length=0;redoV29.length=0;pendingV29=null;refreshSkelHistUiV29()};

 setInterval(()=>{
   const r=activeModelRoot();
   if(r!==lastRootV29){lastRootV29=r;undoV29.length=0;redoV29.length=0;pendingV29=null}
   refreshSkelHistUiV29();
 },250);
 refreshSkelHistUiV29();
'''
s=s.replace(anchor,js+'\n'+anchor,1)
p.write_text(s,encoding='utf-8')
print('Skeleton undo/redo v29 applied as the sole Skeleton history engine')
