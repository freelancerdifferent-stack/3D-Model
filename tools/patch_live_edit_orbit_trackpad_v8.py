from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'LIVE_EDIT_ORBIT_TRACKPAD_V8' in s:
    print('Live Edit orbit trackpad v8 already applied'); raise SystemExit(0)

if 'LIVE_EDIT_SELECT_V1' not in s:
    raise SystemExit('Live Edit Select must be patched first')

# Insert a dedicated orbit trackpad next to the existing manual pan pad.
needle='''          <div id="livePanPad" class="live-pan-pad" aria-label="Manual camera pan">\n            <button type="button" data-pan="up">▲</button>\n            <div><button type="button" data-pan="left">◀</button><button type="button" data-pan="right">▶</button></div>\n            <button type="button" data-pan="down">▼</button>\n          </div>'''
replacement=needle+'''\n          <!-- LIVE_EDIT_ORBIT_TRACKPAD_V8 -->\n          <div id="liveOrbitTrackpad" class="live-orbit-trackpad" aria-label="Live Edit orbit trackpad">\n            <div class="orbit-trackpad-title">ORBIT</div>\n            <div class="orbit-trackpad-surface" id="liveOrbitSurface">\n              <div class="orbit-trackpad-cross"></div>\n              <span>Drag</span>\n            </div>\n            <div class="orbit-trackpad-hint">1 jari: orbit • 2 jari: zoom</div>\n          </div>'''
if needle not in s:
    raise SystemExit('livePanPad marker missing')
s=s.replace(needle,replacement,1)

css_anchor='#liveEditSelectBtn.active{background:#193454;color:#69adff;box-shadow:inset 0 0 0 1px #326aa4}'
css=css_anchor+r'''
/* LIVE_EDIT_ORBIT_TRACKPAD_V8 */
.live-orbit-trackpad{display:none;position:absolute;left:12px;bottom:64px;z-index:9;width:150px;padding:8px;border:1px solid #34485f;border-radius:14px;background:rgba(10,18,27,.9);user-select:none;-webkit-user-select:none}
.live-orbit-trackpad.on{display:block}
.orbit-trackpad-title{text-align:center;font-size:10px;font-weight:800;letter-spacing:.12em;color:#79b8ff;margin:0 0 6px}
.orbit-trackpad-surface{height:112px;border:1px solid #40546c;border-radius:12px;background:linear-gradient(145deg,#142231,#0e1823);position:relative;overflow:hidden;touch-action:none;display:grid;place-items:center;color:#9fb5cc;font-size:11px}
.orbit-trackpad-surface:active{background:#17283a}
.orbit-trackpad-cross:before,.orbit-trackpad-cross:after{content:"";position:absolute;background:rgba(114,165,216,.18);pointer-events:none}
.orbit-trackpad-cross:before{left:50%;top:12px;bottom:12px;width:1px}.orbit-trackpad-cross:after{top:50%;left:12px;right:12px;height:1px}
.orbit-trackpad-hint{text-align:center;color:#8192a5;font-size:9px;margin-top:5px;line-height:1.25}
'''
if css_anchor not in s:
    raise SystemExit('Live Edit CSS anchor missing')
s=s.replace(css_anchor,css,1)

# Show/hide trackpad with Live Edit without enabling OrbitControls on the model canvas.
show_anchor="$('livePanPad')?.classList.toggle('on',liveEditSelectMode);"
if show_anchor not in s:
    raise SystemExit('Live Edit mode visibility anchor missing')
s=s.replace(show_anchor,show_anchor+"\n  $('liveOrbitTrackpad')?.classList.toggle('on',liveEditSelectMode);",1)

# Insert camera-trackpad behavior before animate(). It manually changes camera spherical position
# around controls.target; OrbitControls itself remains disabled so canvas touches cannot fight editing.
marker='function animate(){'
if marker not in s:
    raise SystemExit('animate marker missing')
js=r'''// LIVE_EDIT_ORBIT_TRACKPAD_V8
const liveOrbitSurface=$('liveOrbitSurface');
let liveOrbitTouches=new Map();
let liveOrbitLastCenter=null;
let liveOrbitLastPinch=null;

function liveOrbitApply(dx,dy){
  if(!liveEditSelectMode)return;
  const target=controls.target;
  const offset=camera.position.clone().sub(target);
  const spherical=new THREE.Spherical().setFromVector3(offset);
  spherical.theta-=dx*0.0105;
  spherical.phi-=dy*0.0105;
  spherical.phi=Math.max(0.035,Math.min(Math.PI-0.035,spherical.phi));
  offset.setFromSpherical(spherical);
  camera.position.copy(target).add(offset);
  camera.lookAt(target);
  camera.updateMatrixWorld(true);
}
function liveOrbitZoom(delta){
  if(!liveEditSelectMode)return;
  const target=controls.target;
  const offset=camera.position.clone().sub(target);
  const dist=Math.max(.02,offset.length());
  const factor=Math.exp(delta*0.008);
  const next=Math.max(.03,Math.min(10000,dist*factor));
  offset.setLength(next);
  camera.position.copy(target).add(offset);
  camera.lookAt(target);
  camera.updateMatrixWorld(true);
}
function liveOrbitResetGesture(){
  liveOrbitLastCenter=null;liveOrbitLastPinch=null;
}
if(liveOrbitSurface){
  liveOrbitSurface.addEventListener('pointerdown',ev=>{
    if(!liveEditSelectMode)return;
    ev.preventDefault();ev.stopPropagation();
    try{liveOrbitSurface.setPointerCapture(ev.pointerId)}catch(_){ }
    liveOrbitTouches.set(ev.pointerId,{x:ev.clientX,y:ev.clientY});
    liveOrbitResetGesture();
  },{passive:false});
  liveOrbitSurface.addEventListener('pointermove',ev=>{
    if(!liveEditSelectMode||!liveOrbitTouches.has(ev.pointerId))return;
    ev.preventDefault();ev.stopPropagation();
    liveOrbitTouches.set(ev.pointerId,{x:ev.clientX,y:ev.clientY});
    const pts=[...liveOrbitTouches.values()];
    if(pts.length===1){
      const p=pts[0];
      if(liveOrbitLastCenter)liveOrbitApply(p.x-liveOrbitLastCenter.x,p.y-liveOrbitLastCenter.y);
      liveOrbitLastCenter={x:p.x,y:p.y};liveOrbitLastPinch=null;
    }else{
      const a=pts[0],b=pts[1];
      const center={x:(a.x+b.x)/2,y:(a.y+b.y)/2};
      const pinch=Math.hypot(a.x-b.x,a.y-b.y);
      if(liveOrbitLastCenter)liveOrbitApply((center.x-liveOrbitLastCenter.x)*.65,(center.y-liveOrbitLastCenter.y)*.65);
      if(liveOrbitLastPinch!=null)liveOrbitZoom(liveOrbitLastPinch-pinch);
      liveOrbitLastCenter=center;liveOrbitLastPinch=pinch;
    }
  },{passive:false});
  const end=ev=>{
    if(liveOrbitTouches.has(ev.pointerId))liveOrbitTouches.delete(ev.pointerId);
    liveOrbitResetGesture();
  };
  liveOrbitSurface.addEventListener('pointerup',end);
  liveOrbitSurface.addEventListener('pointercancel',end);
}

'''
s=s.replace(marker,js+marker,1)
p.write_text(s,encoding='utf-8')
print('Live Edit orbit trackpad v8 applied: isolated camera orbit + pinch zoom')
