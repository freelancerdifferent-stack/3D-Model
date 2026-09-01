from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_SELECT_UNDO_V28' in s:
    print('Live Edit Select undo/redo v28 already applied'); raise SystemExit(0)
if 'LIVE_EDIT_SELECT_V1' not in s:
    raise SystemExit('Live Edit Select must be patched first')
if 'LIVE_EDIT_TOUCH_TRANSFORM_V5' not in s:
    raise SystemExit('Live Edit touch transform v5 must be patched first')
if 'OBJECT_UI_V9' not in s:
    raise SystemExit('Object UI v9 must be patched first')

# Undo/Redo belongs to Live Edit Select only. Skeleton Live Edit keeps its own Undo
# (skeletonUndoActionV21) and this engine stays inert while Skeleton mode is on, so the
# two histories can never fight over the same gesture again.
css=r'''
/* LIVE_EDIT_SELECT_UNDO_V28 */
#editorScreen .live-history-tool{display:none}
body.live-edit-history-on #editorScreen .live-history-tool{display:block}
body.skeleton-live-v20 #editorScreen .live-history-tool{display:none!important}
#editorScreen .live-history-tool[aria-disabled="true"]{opacity:.35}
#editorScreen .live-history-tool:active{background:#192535;color:#61a6ff}
'''
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// LIVE_EDIT_SELECT_UNDO_V28
(function(){
 const editor=$('editorScreen'), rail=editor?.querySelector('.toolrail');
 if(!editor||!rail)return;

 const MAX=100;
 const undoStack=[],redoStack=[];
 let pending=null,suppressClickUntil=0;

 const skeletonMode=()=>!!window.skeletonLiveEditMode;
 const liveOn=()=>(typeof liveEditSelectMode!=='undefined')&&!!liveEditSelectMode;
 const rootObj=()=>(typeof root!=='undefined')?root:null;
 const modeLabel=m=>m==='move'?'Move':m==='rotate'?'Rotate':m==='scale'?'Scale':'Transform';

 function selectedMesh(){
   if(typeof liveV5SelectedMesh==='function'){const m=liveV5SelectedMesh();if(m)return m}
   if(typeof liveEditSelectedMeshRef!=='undefined'&&liveEditSelectedMeshRef)return liveEditSelectedMeshRef;
   if(typeof activeMeshLayerIndex!=='undefined'&&activeMeshLayerIndex>=0&&typeof meshList!=='undefined')return meshList[activeMeshLayerIndex]||null;
   return null;
 }
 function snap(o){return o?{obj:o,pos:o.position.clone(),quat:o.quaternion.clone(),scale:o.scale.clone()}:null}
 function same(a,b){
   if(!a||!b||a.obj!==b.obj)return false;
   return a.pos.distanceToSquared(b.pos)<1e-12 && 1-Math.abs(a.quat.dot(b.quat))<1e-12 && a.scale.distanceToSquared(b.scale)<1e-12;
 }
 // A mesh removed by Mesh Layers must not be resurrected by history.
 function alive(o){return !!o && (!!o.parent || o===rootObj())}

 function apply(st){
   if(!st||!alive(st.obj))return false;
   const o=st.obj;
   o.position.copy(st.pos);o.quaternion.copy(st.quat);o.scale.copy(st.scale);
   o.updateMatrix();o.updateMatrixWorld(true);
   if(o.isSkinnedMesh&&o.skeleton){try{o.skeleton.update()}catch(_){ }}
   if(o.isMesh&&typeof showStrongPartSelection==='function'){try{showStrongPartSelection(o)}catch(_){ }}
   if(typeof partDragHelper!=='undefined'&&partDragHelper){try{partDragHelper.update()}catch(_){ }}
   try{window.syncMeshTransformUI?.()}catch(_){ }
   if(typeof updateTransformFields==='function'){try{updateTransformFields()}catch(_){ }}
   return true;
 }

 function refresh(){
   const cu=!skeletonMode()&&undoStack.length>0, cr=!skeletonMode()&&redoStack.length>0;
   undoBtn.setAttribute('aria-disabled',cu?'false':'true');
   redoBtn.setAttribute('aria-disabled',cr?'false':'true');
 }
 function push(before,after,label){
   if(!before||!after||same(before,after))return false;
   undoStack.push({before,after,label:label||'Transform'});
   if(undoStack.length>MAX)undoStack.shift();
   redoStack.length=0;refresh();return true;
 }
 function undo(){
   if(skeletonMode()){msg('Skeleton memakai Undo sendiri');return false}
   while(undoStack.length){
     const c=undoStack.pop();
     if(apply(c.before)){redoStack.push(c);refresh();msg('Undo '+c.label);return true}
   }
   refresh();msg('Tidak ada perubahan untuk Undo');return false;
 }
 function redo(){
   if(skeletonMode()){msg('Skeleton tidak punya Redo');return false}
   while(redoStack.length){
     const c=redoStack.pop();
     if(apply(c.after)){undoStack.push(c);refresh();msg('Redo '+c.label);return true}
   }
   refresh();msg('Tidak ada perubahan untuk Redo');return false;
 }

 const mk=(icon,label,id)=>{
   const b=document.createElement('button');
   b.type='button';b.id=id;b.className='object-extra-tool live-history-tool';
   b.setAttribute('aria-label',label);b.setAttribute('aria-disabled','true');
   b.innerHTML='<b>'+icon+'</b>'+label;return b;
 };
 const undoBtn=mk('↶','Undo','liveUndoBtn');
 const redoBtn=mk('↷','Redo','liveRedoBtn');
 const selectBtn=$('liveEditSelectBtn');
 if(selectBtn&&selectBtn.parentElement===rail){rail.insertBefore(undoBtn,selectBtn);rail.insertBefore(redoBtn,selectBtn)}
 else{rail.appendChild(undoBtn);rail.appendChild(redoBtn)}

 // Android WebView drops synthetic clicks on rail buttons during Live Edit, so own the touch
 // sequence outright and keep a short window that swallows the click it replays afterwards.
 function wire(btn,fn){
   btn.addEventListener('touchstart',ev=>{ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation()},{capture:true,passive:false});
   btn.addEventListener('touchend',ev=>{
     ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();
     suppressClickUntil=performance.now()+700;fn();
   },{capture:true,passive:false});
   btn.addEventListener('click',ev=>{
     ev.preventDefault();ev.stopPropagation();
     if(performance.now()<suppressClickUntil)return;
     fn();
   });
 }
 wire(undoBtn,undo);wire(redoBtn,redo);

 // One finger drag on the viewport = exactly one history entry. Listening on document in the
 // capture phase runs before LIVE_EDIT_TOUCH_TRANSFORM_V5 stops propagation at the viewport,
 // so the "before" state is read while the mesh is still untouched.
 document.addEventListener('touchstart',ev=>{
   if(skeletonMode()||!liveOn())return;
   if(typeof liveEditTransformMode==='undefined'||!liveEditTransformMode)return;
   if(ev.target!==canvas)return;
   const m=selectedMesh();
   pending=m?{before:snap(m),mesh:m,label:modeLabel(liveEditTransformMode)}:null;
 },{capture:true,passive:true});

 document.addEventListener('touchend',()=>{
   const p=pending;
   if(!p)return;
   // Commit after the V5 touchend handler has written the final transform.
   setTimeout(()=>{
     if(pending!==p)return;
     if(typeof liveV5TouchId!=='undefined'&&liveV5TouchId!==null)return;
     pending=null;
     push(p.before,snap(p.mesh),p.label);
   },0);
 },{capture:true,passive:true});
 document.addEventListener('touchcancel',()=>{pending=null},{capture:true,passive:true});

 // Root Transform panel fields. Registered last, so the base change handler has already applied
 // the value; Skeleton mode blocks this earlier via stopImmediatePropagation.
 ['px','py','pz','rx','ry','rz','sx','sy','sz'].forEach(id=>{
   const el=$(id);if(!el)return;
   let before=null;
   el.addEventListener('focus',()=>{before=(!skeletonMode()&&liveOn())?snap(rootObj()):null});
   el.addEventListener('change',()=>{
     const b=before;before=null;
     if(!b||skeletonMode()||!liveOn())return;
     push(b,snap(rootObj()),'Transform');
   });
 });

 // MESH_TRANSFORM_PANEL_V14 already calls these hooks for typed values and scrub sliders.
 window.objectHistorySnapshot=o=>snap(o);
 window.objectHistoryPush=(b,a,l)=>push(b,a,l||'Mesh Transform');
 window.objectHistoryRefresh=refresh;
 window.objectHistoryClear=()=>{undoStack.length=0;redoStack.length=0;pending=null;refresh()};
 window.liveEditUndoActionV28=undo;
 window.liveEditRedoActionV28=redo;

 // A freshly imported model starts with an empty history.
 if(typeof registerModel==='function'){
   const oldRegisterModel=registerModel;
   registerModel=function(){const r=oldRegisterModel.apply(this,arguments);window.objectHistoryClear();return r};
 }

 setInterval(()=>{
   document.body.classList.toggle('live-edit-history-on',liveOn()&&!skeletonMode());
   refresh();
 },250);
 refresh();
})();
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('script end missing')
s=s[:idx]+js+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Live Edit Select undo/redo v28 applied')
