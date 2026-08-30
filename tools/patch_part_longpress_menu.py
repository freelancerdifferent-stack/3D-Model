from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

if 'PART_LONGPRESS_MENU_V1' in s:
    print('Part long-press menu already applied')
    raise SystemExit(0)

css_marker='.hidden{display:none!important}'
if css_marker not in s:
    raise SystemExit('CSS marker missing')
css=r'''
/* PART_LONGPRESS_MENU_V1 */
#partDragBtn,#partRotateBtn,#partScaleBtn,#meshLayersDragBtn,#meshLayersRotateBtn,#meshLayersScaleBtn{display:none!important}
.part-axis-panel,#partAxisOverlay,#partDragBadge{display:none!important}
.part-context-menu{position:absolute;z-index:30;display:none;min-width:220px;padding:10px;border:1px solid #4c9cff;border-radius:14px;background:rgba(8,15,24,.97);box-shadow:0 12px 36px rgba(0,0,0,.45);backdrop-filter:blur(8px)}
.part-context-menu.on{display:block}
.part-context-title{font-size:12px;color:#93c4ff;margin:0 0 8px;padding:0 3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.part-context-actions{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}
.part-context-actions button{height:48px;margin:0;border:1px solid #35506d;border-radius:10px;background:#111d2a;color:#d9e8f8;font-size:12px;font-weight:700}
.part-context-actions button:active{background:#1d4f83;border-color:#61a6ff}
.part-context-hint{font-size:10px;color:#8291a3;margin-top:8px;text-align:center}
.part-hold-ring{position:absolute;z-index:29;display:none;width:42px;height:42px;margin:-21px 0 0 -21px;border:3px solid #61a6ff;border-radius:50%;pointer-events:none;animation:partHoldPulse .7s ease-in-out infinite alternate}
.part-hold-ring.on{display:block}
@keyframes partHoldPulse{from{transform:scale(.85);opacity:.45}to{transform:scale(1.05);opacity:1}}
'''
s=s.replace(css_marker,css_marker+css,1)

viewport_marker='<div class="part-axis-overlay" id="partAxisOverlay">'
pos=s.find(viewport_marker)
if pos<0:
    raise SystemExit('Part axis overlay marker missing')
# Put menu immediately before the axis overlay so it stays inside the preview/viewport stacking context.
menu=r'''<div class="part-hold-ring" id="partHoldRing"></div>
          <div class="part-context-menu" id="partContextMenu">
            <div class="part-context-title" id="partContextTitle">Selected part</div>
            <div class="part-context-actions">
              <button data-part-context-mode="move">✥<br>MOVE</button>
              <button data-part-context-mode="scale">⤢<br>SCALE</button>
              <button data-part-context-mode="rotate">⟳<br>ROTATE</button>
            </div>
            <div class="part-context-hint">Tekan part 3 detik untuk memilih part lain</div>
          </div>
          '''
s=s[:pos]+menu+s[pos:]

# Insert behavior before the existing axis-lock helper so all transform state/functions already exist at runtime.
js_marker='function setPartTransformAxis(axis){'
if js_marker not in s:
    raise SystemExit('Axis function marker missing')
js=r'''// PART_LONGPRESS_MENU_V1
let partLongPressTimer=null;
let partLongPressPointerId=null;
let partLongPressStartX=0,partLongPressStartY=0;
let partLongPressLastX=0,partLongPressLastY=0;
let partLongPressTriggered=false;
const PART_LONGPRESS_MS=3000;
const PART_LONGPRESS_MOVE_TOLERANCE=14;

function closePartContextMenu(){
  const m=$('partContextMenu');if(m)m.classList.remove('on');
  const r=$('partHoldRing');if(r)r.classList.remove('on');
}
function cancelPartLongPress(){
  if(partLongPressTimer){clearTimeout(partLongPressTimer);partLongPressTimer=null}
  partLongPressPointerId=null;
  const r=$('partHoldRing');if(r)r.classList.remove('on');
}
function partPickAt(clientX,clientY){
  const ev={clientX,clientY};
  if(!setPartDragPointer(ev))return null;
  if(root)root.updateMatrixWorld(true);
  camera.updateMatrixWorld(true);
  const hits=partDragRaycaster.intersectObjects(partDragVisibleMeshes(),false);
  return hits.length?hits[0]:null;
}
function showStrongPartSelection(mesh){
  showPartDragSelection(mesh);
  if(partDragHelper && partDragHelper.material){
    partDragHelper.material.transparent=true;
    partDragHelper.material.opacity=1;
    partDragHelper.material.depthTest=false;
    partDragHelper.renderOrder=999;
  }
}
function openPartContextMenu(mesh,clientX,clientY){
  const index=meshList.indexOf(mesh);if(index<0)return;
  // End any old gesture/mode first, then lock selection to the newly long-pressed part.
  try{finishPartDrag()}catch(_){ }
  try{finishPartTransform()}catch(_){ }
  partDragEnabled=false;partRotateEnabled=false;partScaleEnabled=false;
  updatePartDragUI();
  selectMeshLayer(index);
  showStrongPartSelection(mesh);
  controls.enabled=false;

  const menu=$('partContextMenu');
  const title=$('partContextTitle');
  if(title)title.textContent=meshLayerDisplayName(mesh,index);
  if(!menu)return;
  const vr=canvas.parentElement.getBoundingClientRect();
  let x=clientX-vr.left+12;
  let y=clientY-vr.top+12;
  menu.classList.add('on');
  // Clamp after display so dimensions are measurable.
  const mw=menu.offsetWidth||220,mh=menu.offsetHeight||120;
  x=Math.max(8,Math.min(x,vr.width-mw-8));
  y=Math.max(8,Math.min(y,vr.height-mh-8));
  menu.style.left=x+'px';menu.style.top=y+'px';
}
function triggerPartLongPress(){
  partLongPressTimer=null;
  const hit=partPickAt(partLongPressLastX,partLongPressLastY);
  if(!hit){cancelPartLongPress();return}
  partLongPressTriggered=true;
  if(navigator.vibrate)try{navigator.vibrate(35)}catch(_){ }
  openPartContextMenu(hit.object,partLongPressLastX,partLongPressLastY);
  const r=$('partHoldRing');if(r)r.classList.remove('on');
}
function beginPartLongPress(ev){
  if(ev.pointerType==='mouse'&&ev.button!==0)return;
  closePartContextMenu();
  cancelPartLongPress();
  partLongPressPointerId=ev.pointerId;
  partLongPressStartX=partLongPressLastX=ev.clientX;
  partLongPressStartY=partLongPressLastY=ev.clientY;
  partLongPressTriggered=false;
  const vr=canvas.parentElement.getBoundingClientRect();
  const ring=$('partHoldRing');
  if(ring){ring.style.left=(ev.clientX-vr.left)+'px';ring.style.top=(ev.clientY-vr.top)+'px'}
  partLongPressTimer=setTimeout(()=>{
    if(ring)ring.classList.add('on');
    triggerPartLongPress();
  },PART_LONGPRESS_MS);
}
function trackPartLongPress(ev){
  if(ev.pointerId!==partLongPressPointerId)return;
  partLongPressLastX=ev.clientX;partLongPressLastY=ev.clientY;
  if(Math.hypot(ev.clientX-partLongPressStartX,ev.clientY-partLongPressStartY)>PART_LONGPRESS_MOVE_TOLERANCE){
    cancelPartLongPress();
  }
}
function endPartLongPress(ev){
  if(ev.pointerId!==partLongPressPointerId)return;
  cancelPartLongPress();
  if(partLongPressTriggered){
    ev.preventDefault();ev.stopPropagation();
    if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
  }
}
function choosePartContextMode(mode){
  const mesh=activePartMesh();
  if(!mesh){closePartContextMenu();controls.enabled=true;msg('Part tidak ditemukan');return}
  setPartTransformAxis('free');
  closePartContextMenu();
  controls.enabled=true;
  if(mode==='move')setExclusivePartMode('move',true);
  else if(mode==='scale')setExclusivePartMode('scale',true);
  else if(mode==='rotate')setExclusivePartMode('rotate',true);
  showStrongPartSelection(mesh);
  msg((mode==='move'?'Move':mode==='scale'?'Scale':'Rotate')+' aktif — drag part yang menyala');
}

'''
s=s.replace(js_marker,js+js_marker,1)

# Bind on the viewport parent in capture phase. Parent capture runs before the canvas transform handlers.
handler_marker="document.querySelectorAll('[data-part-axis]').forEach(btn=>{"
if handler_marker not in s:
    raise SystemExit('Axis handler marker missing')
handlers=r'''const partGestureSurface=canvas.parentElement;
partGestureSurface.addEventListener('pointerdown',beginPartLongPress,{capture:true});
partGestureSurface.addEventListener('pointermove',trackPartLongPress,{capture:true});
partGestureSurface.addEventListener('pointerup',endPartLongPress,{capture:true});
partGestureSurface.addEventListener('pointercancel',endPartLongPress,{capture:true});
document.querySelectorAll('[data-part-context-mode]').forEach(btn=>{
  btn.addEventListener('click',ev=>{
    ev.preventDefault();ev.stopPropagation();
    choosePartContextMode(btn.dataset.partContextMode);
  });
});
$('partContextMenu').addEventListener('pointerdown',ev=>ev.stopPropagation());

'''
s=s.replace(handler_marker,handlers+handler_marker,1)

p.write_text(s,encoding='utf-8')
print('Part long-press contextual transform menu applied')
