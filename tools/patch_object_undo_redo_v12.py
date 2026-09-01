from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'OBJECT_UNDO_REDO_V12' in s:
    print('Object undo redo v12 already applied'); raise SystemExit(0)
js=r'''
// OBJECT_UNDO_REDO_V12
(function(){
 const undoBtn=$('objectUndoBtn'), redoBtn=$('objectRedoBtn');
 if(!undoBtn||!redoBtn)return;
 const undoStack=[],redoStack=[]; const MAX=100;
 let meshPending=null, fieldPending=new Map();
 const cloneState=m=>m?{mesh:m,pos:m.position.clone(),quat:m.quaternion.clone(),scale:m.scale.clone()}:null;
 const equal=(a,b)=>!!(a&&b&&a.mesh===b.mesh&&a.pos.distanceToSquared(b.pos)<1e-12&&1-Math.abs(a.quat.dot(b.quat))<1e-12&&a.scale.distanceToSquared(b.scale)<1e-12);
 function selectedMesh(){
   let m=(typeof liveEditSelectedMeshRef!=='undefined')?liveEditSelectedMeshRef:null;
   if(!m&&typeof activeMeshLayerIndex!=='undefined'&&activeMeshLayerIndex>=0&&typeof meshList!=='undefined')m=meshList[activeMeshLayerIndex];
   return m&&m.isMesh?m:null;
 }
 function modelTarget(){
   if(typeof activeModel!=='undefined'&&activeModel)return activeModel;
   if(typeof currentModel!=='undefined'&&currentModel)return currentModel;
   if(typeof sceneLayers!=='undefined'&&Array.isArray(sceneLayers)){
     const layer=sceneLayers.find(x=>x&&x.object&&(x.active||x.selected))||sceneLayers.find(x=>x&&x.object);
     if(layer)return layer.object;
   }
   return null;
 }
 function apply(st){
   if(!st||!st.mesh)return;
   const m=st.mesh;
   m.position.copy(st.pos);m.quaternion.copy(st.quat);m.scale.copy(st.scale);
   m.updateMatrix();m.updateMatrixWorld(true);
   if(m.isSkinnedMesh&&m.skeleton){try{m.skeleton.update()}catch(_){}}
   if(typeof showStrongPartSelection==='function'&&m.isMesh)try{showStrongPartSelection(m)}catch(_){}
   if(typeof partDragHelper!=='undefined'&&partDragHelper)try{partDragHelper.update()}catch(_){}
   try{if(typeof syncTransformUI==='function')syncTransformUI()}catch(_){}
   try{if(typeof syncMeshTransformUI==='function')syncMeshTransformUI()}catch(_){}
 }
 function skeletonOwnsHistoryV12(){return !!window.skeletonLiveEditMode;}
 function refresh(){
   // Critical route separation: while Skeleton Live Edit is active, Object/Mesh
   // history must not touch native disabled/opacity state of the shared buttons.
   if(skeletonOwnsHistoryV12())return;
   undoBtn.disabled=!undoStack.length;redoBtn.disabled=!redoStack.length;
   undoBtn.style.opacity=undoStack.length?'1':'.35';redoBtn.style.opacity=redoStack.length?'1':'.35';
 }
 function push(before,after,label){
   if(!before||!after||equal(before,after))return;
   undoStack.push({before,after,label:label||'Transform'});if(undoStack.length>MAX)undoStack.shift();
   redoStack.length=0;refresh();
 }
 function objectUndoActionV12(){
   const c=undoStack.pop();if(!c){msg('Tidak ada perubahan untuk Undo');return false;}
   apply(c.before);redoStack.push(c);refresh();msg('Undo '+c.label);return true;
 }
 function objectRedoActionV12(){
   const c=redoStack.pop();if(!c){msg('Tidak ada perubahan untuk Redo');return false;}
   apply(c.after);undoStack.push(c);refresh();msg('Redo '+c.label);return true;
 }
 undoBtn.onclick=e=>{
   // Object/Mesh route NEVER runs in Skeleton mode. Skeleton has a different
   // stack and different action functions in SKELETON_TOOL_ROUTES_V21.
   if(skeletonOwnsHistoryV12())return;
   e.preventDefault();e.stopPropagation();objectUndoActionV12();
 };
 redoBtn.onclick=e=>{
   if(skeletonOwnsHistoryV12())return;
   e.preventDefault();e.stopPropagation();objectRedoActionV12();
 };
 document.addEventListener('touchstart',ev=>{
   if(skeletonOwnsHistoryV12())return;
   if(typeof liveEditSelectMode==='undefined'||!liveEditSelectMode||typeof liveEditTransformMode==='undefined'||!liveEditTransformMode)return;
   if(ev.target!==canvas)return;
   const m=selectedMesh(); if(!m)return;
   meshPending={before:cloneState(m),mesh:m,mode:liveEditTransformMode,touchId:ev.changedTouches&&ev.changedTouches[0]?ev.changedTouches[0].identifier:null};
 },{capture:true,passive:true});
 document.addEventListener('touchend',()=>{
   if(skeletonOwnsHistoryV12()){meshPending=null;return;}
   if(!meshPending)return;
   const p=meshPending;
   setTimeout(()=>{if(meshPending!==p)return;push(p.before,cloneState(p.mesh),p.mode==='move'?'Move Mesh':p.mode==='rotate'?'Rotate Mesh':'Scale Mesh');meshPending=null;},0);
 },{capture:true,passive:true});
 document.addEventListener('touchcancel',()=>{meshPending=null},{capture:true,passive:true});
 ['px','py','pz','rx','ry','rz','sx','sy','sz'].forEach(id=>{
   const el=$(id);if(!el)return;
   const begin=()=>{if(skeletonOwnsHistoryV12())return;const m=modelTarget();if(m&&!fieldPending.has(id))fieldPending.set(id,cloneState(m));};
   el.addEventListener('focus',begin,true);
   el.addEventListener('pointerdown',begin,true);
   el.addEventListener('change',()=>{if(skeletonOwnsHistoryV12()){fieldPending.delete(id);return;}const before=fieldPending.get(id);fieldPending.delete(id);const m=modelTarget();if(before&&m)push(before,cloneState(m),'Transform Model')},true);
 });
 // Public Object/Mesh-only route. Skeleton never calls these functions.
 window.objectHistorySnapshot=cloneState;
 window.objectHistoryPush=push;
 window.objectHistoryApply=apply;
 window.objectUndoActionV12=objectUndoActionV12;
 window.objectRedoActionV12=objectRedoActionV12;
 window.objectHistoryRefreshV12=refresh;
 window.objectUndoRedoClear=function(){undoStack.length=0;redoStack.length=0;meshPending=null;fieldPending.clear();refresh()};
 refresh();
})();
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('script end missing')
s=s[:idx]+js+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Object undo/redo v12 applied: separate Object/Mesh route, Skeleton excluded')
