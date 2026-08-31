from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'OBJECT_UNDO_REDO_V10' in s:
    print('Object undo redo v10 already applied'); raise SystemExit(0)
js=r'''
// OBJECT_UNDO_REDO_V10
(function(){
 const undoBtn=$('objectUndoBtn'), redoBtn=$('objectRedoBtn');
 if(!undoBtn||!redoBtn)return;
 const undoStack=[], redoStack=[]; const MAX=80;
 let pending=null;
 const snap=m=>m?{mesh:m,pos:m.position.clone(),quat:m.quaternion.clone(),scale:m.scale.clone()}:null;
 const same=(a,b)=>a&&b&&a.pos.distanceToSquared(b.pos)<1e-12&&1-Math.abs(a.quat.dot(b.quat))<1e-12&&a.scale.distanceToSquared(b.scale)<1e-12;
 function apply(st){if(!st?.mesh)return;const m=st.mesh;m.position.copy(st.pos);m.quaternion.copy(st.quat);m.scale.copy(st.scale);m.updateMatrix();m.updateMatrixWorld(true);if(m.isSkinnedMesh&&m.skeleton){try{m.skeleton.update()}catch(_){}}if(typeof showStrongPartSelection==='function')try{showStrongPartSelection(m)}catch(_){};if(typeof partDragHelper!=='undefined'&&partDragHelper)try{partDragHelper.update()}catch(_){};}
 function refresh(){undoBtn.disabled=!undoStack.length;redoBtn.disabled=!redoStack.length;undoBtn.style.opacity=undoStack.length?'1':'.35';redoBtn.style.opacity=redoStack.length?'1':'.35'}
 function push(before,after,label){if(!before||!after||same(before,after))return;undoStack.push({before,after,label:label||'Transform'});if(undoStack.length>MAX)undoStack.shift();redoStack.length=0;refresh()}
 undoBtn.onclick=()=>{const cmd=undoStack.pop();if(!cmd){msg('Tidak ada perubahan untuk Undo');return;}apply(cmd.before);redoStack.push(cmd);refresh();msg('Undo '+cmd.label)};
 redoBtn.onclick=()=>{const cmd=redoStack.pop();if(!cmd){msg('Tidak ada perubahan untuk Redo');return;}apply(cmd.after);undoStack.push(cmd);refresh();msg('Redo '+cmd.label)};
 // Hook native Android Live Edit touch gesture. One drag = one history command.
 if(typeof liveV5Start==='function'){
   const oldStart=liveV5Start; liveV5Start=function(ev){pending=null;const m=(typeof liveV5SelectedMesh==='function')?liveV5SelectedMesh():null;if(m)pending={before:snap(m),mode:liveEditTransformMode};const r=oldStart(ev);if(liveV5TouchId===null)pending=null;return r};
 }
 if(typeof liveV5End==='function'){
   const oldEnd=liveV5End; liveV5End=function(ev){const m=liveV5Mesh;const p=pending;const r=oldEnd(ev);if(p&&m)push(p.before,snap(m),p.mode==='move'?'Move':p.mode==='rotate'?'Rotate':'Scale');pending=null;return r};
 }
 // Also capture manual Transform fields on focus/change.
 ['px','py','pz','rx','ry','rz','sx','sy','sz'].forEach(id=>{const el=$(id);if(!el)return;let before=null;el.addEventListener('focus',()=>{const m=(typeof activeModel!=='undefined'&&activeModel)?activeModel:null;before=snap(m)});el.addEventListener('change',()=>{const m=(typeof activeModel!=='undefined'&&activeModel)?activeModel:null;if(before&&m)push(before,snap(m),'Transform');before=null})});
 refresh();
 window.objectUndoRedoClear=function(){undoStack.length=redoStack.length=0;pending=null;refresh()};
})();
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('script end missing')
s=s[:idx]+js+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Object undo/redo v10 applied')
