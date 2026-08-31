from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'OBJECT_UI_V9' in s:
    print('Object UI v9 already applied'); raise SystemExit(0)
marker='</style>'
css=r'''
/* OBJECT_UI_V9 — Object screen only */
#editorScreen .editor{grid-template-columns:58px 1fr;grid-template-rows:1fr;}
#editorScreen .toolrail{grid-row:1;padding:8px 5px 74px;gap:2px;z-index:12}
#editorScreen .viewport{grid-column:2;grid-row:1;min-height:0}
#editorScreen .props{display:none}
#editorScreen .tool{min-height:58px}
#editorScreen .object-extra-tool{min-height:58px;border:0;border-radius:10px;background:transparent;color:#ccd4de;font-size:10px}
#editorScreen .object-extra-tool b{display:block;font-size:25px;line-height:24px;margin-bottom:5px;color:#fff}
#editorScreen .object-extra-tool.active{background:#192535;color:#61a6ff}
#editorScreen .object-select-bottom{margin-top:auto;border:1px solid #2868a7;background:#17304c;color:#65aaff}
#editorScreen .overleft{left:12px;top:8px}
#editorScreen .overright{right:12px;top:8px}
#editorScreen #liveEditBadge{top:8px!important}
#editorScreen .viewtools{right:10px;top:70px}
#editorScreen .timeline{left:10%;right:5%;bottom:76px;height:46px}
#editorScreen #animSelect{height:42px!important;font-size:15px}
#editorScreen .object-camera-pad{display:none;position:absolute;right:9px;top:310px;z-index:10;width:50px;gap:5px;flex-direction:column}
#editorScreen .object-camera-pad.on{display:flex}
#editorScreen .object-camera-pad button{width:46px;height:46px;border:1px solid #33465b;border-radius:9px;background:#142131;font-size:25px;font-weight:900;line-height:1}
#editorScreen .object-camera-pad [data-pan="up"]{color:#ff1720}
#editorScreen .object-camera-pad [data-pan="down"]{color:#00f13c}
#editorScreen .object-camera-pad [data-pan="left"]{color:#fff}
#editorScreen .object-camera-pad [data-pan="right"]{color:#ffe51e}
#editorScreen #livePanPad{display:none!important}
#editorScreen .object-trackpad-drawer{display:none;position:absolute;left:0;right:0;bottom:0;z-index:8;background:#0d151e;border-top:1px solid #2a3948}
#editorScreen .object-trackpad-drawer.on{display:block}
#editorScreen .object-trackpad-toggle{height:42px;width:100%;border:0;background:#0d151e;color:#fff;font-weight:800;font-size:12px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0}
#editorScreen .object-trackpad-toggle i{font-style:normal;font-size:27px;line-height:18px}
#editorScreen .object-trackpad-body{height:210px;padding:8px 14px 14px}
#editorScreen .object-trackpad-drawer.collapsed .object-trackpad-body{display:none}
#editorScreen .object-trackpad-drawer.collapsed{height:42px}
#editorScreen .object-trackpad-surface{height:100%;border:1px solid #26394c;border-radius:14px;background:linear-gradient(145deg,#111e2b,#0a131c);touch-action:none;position:relative;overflow:hidden}
#editorScreen .object-trackpad-surface:before,#editorScreen .object-trackpad-surface:after{content:"";position:absolute;background:rgba(105,173,255,.12);pointer-events:none}
#editorScreen .object-trackpad-surface:before{width:1px;top:12px;bottom:12px;left:50%}
#editorScreen .object-trackpad-surface:after{height:1px;left:12px;right:12px;top:50%}
#editorScreen .object-trackpad-drawer.on:not(.collapsed)~.timeline{bottom:286px}
body.object-ui-v9 .topbar{display:none}
body.object-ui-v9 .content{height:calc(100dvh - 66px)}
@media (max-height:720px){#editorScreen .object-trackpad-body{height:160px}}
'''
s=s.replace(marker,css+'\n'+marker,1)
js=r'''
// OBJECT_UI_V9
(function(){
 const editor=$('editorScreen'), rail=editor?.querySelector('.toolrail'), viewport=editor?.querySelector('.viewport');
 if(!editor||!rail||!viewport)return;
 const oldTools=[...rail.querySelectorAll('.tool')];
 const select=oldTools[0], move=oldTools[1], rotate=oldTools[2], scale=oldTools[3], frame=oldTools[4];
 if(select) select.classList.add('object-select-bottom');
 const mk=(icon,label,id)=>{const b=document.createElement('button');b.type='button';b.className='object-extra-tool';b.id=id;b.innerHTML='<b>'+icon+'</b>'+label;return b};
 const transform=mk('＋','Transform','objectTransformToggle');
 const undo=mk('←','Undo','objectUndoBtn');
 const redo=mk('→','Redo','objectRedoBtn');
 rail.innerHTML='';
 [move,rotate,scale,frame,transform,undo,redo,select].filter(Boolean).forEach(x=>rail.appendChild(x));
 transform.onclick=()=>{const props=editor.querySelector('.props'); if(!props)return; const open=props.style.display!=='block'; props.style.display=open?'block':'none'; if(open){props.style.position='absolute';props.style.left='58px';props.style.right='0';props.style.bottom='0';props.style.zIndex='20';props.style.maxHeight='245px'} transform.classList.toggle('active',open)};
 undo.onclick=()=>{try{document.execCommand('undo')}catch(_){};msg('Undo')};
 redo.onclick=()=>{try{document.execCommand('redo')}catch(_){};msg('Redo')};
 const cam=document.createElement('div');cam.className='object-camera-pad';cam.id='objectCameraPad';
 cam.innerHTML='<button type="button" data-pan="up">▲</button><button type="button" data-pan="down">▼</button><button type="button" data-pan="left">◀</button><button type="button" data-pan="right">▶</button>';
 viewport.appendChild(cam);
 const drawer=document.createElement('div');drawer.className='object-trackpad-drawer collapsed';drawer.id='objectTrackpadDrawer';
 drawer.innerHTML='<button type="button" class="object-trackpad-toggle" id="objectTrackpadToggle"><span>TRACKPAD</span><i>⌄</i></button><div class="object-trackpad-body"><div class="object-trackpad-surface" id="objectTrackpadSurface"></div></div>';
 viewport.appendChild(drawer);
 const toggle=$('objectTrackpadToggle');toggle.onclick=()=>{drawer.classList.toggle('collapsed');toggle.querySelector('i').textContent=drawer.classList.contains('collapsed')?'⌄':'⌃'};
 function syncObjectLiveUi(){const on=!!liveEditSelectMode;cam.classList.toggle('on',on);drawer.classList.toggle('on',on)}
 const oldUpdate=typeof updateLiveEditToolUI==='function'?updateLiveEditToolUI:null;
 if(oldUpdate) updateLiveEditToolUI=function(){const r=oldUpdate.apply(this,arguments);syncObjectLiveUi();return r};
 setInterval(syncObjectLiveUi,350);
 cam.querySelectorAll('[data-pan]').forEach(b=>b.addEventListener('pointerdown',ev=>{ev.preventDefault();ev.stopPropagation();const dir=b.dataset.pan;const target=controls.target;const dist=Math.max(.1,camera.position.distanceTo(target));const step=dist*.045;const right=new THREE.Vector3(1,0,0).applyQuaternion(camera.quaternion);const up=new THREE.Vector3(0,1,0).applyQuaternion(camera.quaternion);const d=new THREE.Vector3();if(dir==='left')d.addScaledVector(right,-step);if(dir==='right')d.addScaledVector(right,step);if(dir==='up')d.addScaledVector(up,step);if(dir==='down')d.addScaledVector(up,-step);camera.position.add(d);target.add(d);camera.lookAt(target);camera.updateMatrixWorld(true)}));
 const surf=$('objectTrackpadSurface');let pts=new Map(),last=null,pinch=null;
 const orbit=(dx,dy)=>{const off=camera.position.clone().sub(controls.target),sp=new THREE.Spherical().setFromVector3(off);sp.theta-=dx*.0105;sp.phi-=dy*.0105;sp.phi=Math.max(.035,Math.min(Math.PI-.035,sp.phi));off.setFromSpherical(sp);camera.position.copy(controls.target).add(off);camera.lookAt(controls.target);camera.updateMatrixWorld(true)};
 surf.addEventListener('pointerdown',e=>{if(!liveEditSelectMode)return;e.preventDefault();e.stopPropagation();try{surf.setPointerCapture(e.pointerId)}catch(_){}pts.set(e.pointerId,{x:e.clientX,y:e.clientY});last=null;pinch=null},{passive:false});
 surf.addEventListener('pointermove',e=>{if(!pts.has(e.pointerId))return;e.preventDefault();e.stopPropagation();pts.set(e.pointerId,{x:e.clientX,y:e.clientY});const a=[...pts.values()];if(a.length===1){if(last)orbit(a[0].x-last.x,a[0].y-last.y);last=a[0];pinch=null}else{const c={x:(a[0].x+a[1].x)/2,y:(a[0].y+a[1].y)/2},p=Math.hypot(a[0].x-a[1].x,a[0].y-a[1].y);if(last)orbit((c.x-last.x)*.65,(c.y-last.y)*.65);if(pinch!=null){const off=camera.position.clone().sub(controls.target);off.setLength(Math.max(.03,Math.min(10000,off.length()*Math.exp((pinch-p)*.008))));camera.position.copy(controls.target).add(off);camera.lookAt(controls.target)}last=c;pinch=p}}, {passive:false});
 const end=e=>{pts.delete(e.pointerId);last=null;pinch=null};surf.addEventListener('pointerup',end);surf.addEventListener('pointercancel',end);
 function shell(){document.body.classList.toggle('object-ui-v9',editor.classList.contains('active'))}new MutationObserver(shell).observe(editor,{attributes:true,attributeFilter:['class']});shell();
})();
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('script end missing')
s=s[:idx]+js+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Object UI v9 applied')
