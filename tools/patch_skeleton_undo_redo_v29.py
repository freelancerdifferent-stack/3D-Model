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
 let pendingV29=null,lastRootV29=null;

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
     if(typeof skeletonHelper?.update==='function')skeletonHelper.update();
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

 function depthV29(){return ' · undo '+undoV29.length+' redo '+redoV29.length}
 // A stale entry is dropped one at a time; a throw puts the entry back so a single bad step can
 // never wipe the rest of the history.
 function stepV29(from,to,undoing,label){
   while(from.length){
     const e=from[from.length-1];
     let ok=false;
     try{ok=applyEntryV29(e,undoing)}
     catch(err){refreshSkelHistUiV29();msg('Skeleton '+label+' gagal: '+(err&&err.message?err.message:err));return false}
     from.pop();
     if(ok){to.push(e);refreshSkelHistUiV29();msg('Skeleton '+label+' '+e.label+depthV29());return true}
   }
   refreshSkelHistUiV29();msg('Skeleton: tidak ada '+label+depthV29());return false;
 }
 function skeletonUndoActionV29(){
   if(!skeletonLiveEditMode){msg('Undo ini khusus mode Skeleton');return false}
   return stepV29(undoV29,redoV29,true,'Undo');
 }
 function skeletonRedoActionV29(){
   if(!skeletonLiveEditMode){msg('Redo ini khusus mode Skeleton');return false}
   return stepV29(redoV29,undoV29,false,'Redo');
 }

 // One tap must run the action exactly once. On Android WebView a tap delivers touchend and
 // then replays a synthetic click; running both made Redo fire twice, so the second call found
 // an empty stack, greyed the button and overwrote the success toast. Once this button has seen
 // a real touch, every click on it is a replay and is ignored outright.
 function wireSkelHistV29(btn,fn){
   let sawTouch=false,lastFire=0;
   const run=()=>{
     const now=performance.now();
     if(now-lastFire<60)return;   // kills a duplicate delivery without throttling real taps
     lastFire=now;fn();
   };
   const stop=ev=>{ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation()};
   btn.addEventListener('touchstart',stop,{capture:true,passive:false});
   btn.addEventListener('touchend',ev=>{stop(ev);sawTouch=true;run()},{capture:true,passive:false});
   btn.addEventListener('touchcancel',ev=>{stop(ev);sawTouch=true},{capture:true,passive:false});
   btn.addEventListener('click',ev=>{stop(ev);if(sawTouch)return;run()},{capture:true});
 }
 wireSkelHistV29(skelUndoBtn,skeletonUndoActionV29);
 wireSkelHistV29(skelRedoBtn,skeletonRedoActionV29);

 // One bone drag = one entry. These listeners are registered after the V20 gesture handlers,
 // so touchId and selectedBone are already settled when they run.
 canvas.addEventListener('touchstart',ev=>{
   if(!skeletonLiveEditMode||window.skeletonRigModeV26)return;
   if(touchId===null||!selectedBone){pendingV29=null;return}
   const t=ev.touches&&ev.touches[0];
   pendingV29={bone:selectedBone,before:snapV29(selectedBone),x:t?t.clientX:0,y:t?t.clientY:0};
 },{capture:true,passive:true});
 canvas.addEventListener('touchend',ev=>{
   const pend=pendingV29;
   if(!pend)return;
   // A stationary tap only picks a bone. Recording it would clear the redo stack for nothing,
   // which is exactly what made Redo look broken, so require a real drag first.
   const t=ev.changedTouches&&ev.changedTouches[0];
   const moved=t?Math.hypot(t.clientX-pend.x,t.clientY-pend.y):0;
   // Commit after the V20/V21 touchend handler has written the final bone transform.
   setTimeout(()=>{
     if(pendingV29!==pend)return;
     if(touchId!==null)return;
     pendingV29=null;
     if(moved<6)return;
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
