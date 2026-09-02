from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html missing')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_ZOOM_V49' in s:
    print('Auto Rig zoom v49 already applied'); raise SystemExit(0)
if 'AUTO_RIG_CAMERA_HIDE_V48' not in s: raise SystemExit('Auto Rig camera/hide v48 must run first')

css=r'''
/* AUTO_RIG_ZOOM_V49 */
.auto-rig-zoom-v49{position:absolute;right:12px;top:92px;z-index:34;display:none;flex-direction:column;gap:7px;pointer-events:auto}
body.auto-rig-v42 .auto-rig-zoom-v49{display:flex}
.auto-rig-zoom-v49 button{width:46px;height:42px;border:1px solid #394b62;border-radius:11px;background:rgba(18,26,35,.94);color:#fff;font-size:25px;font-weight:600;line-height:36px}
.auto-rig-zoom-v49 button:active{background:#214777;border-color:#5797e8}
'''
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// AUTO_RIG_ZOOM_V49
(function(){
  if(window.__autoRigZoomV49)return;
  const editor=document.getElementById('editorScreen');
  const viewport=editor?.querySelector('.viewport');
  if(!viewport)return;

  const box=document.createElement('div');
  box.id='autoRigZoomV49';box.className='auto-rig-zoom-v49';
  box.innerHTML='<button type="button" data-zoom="in" title="Zoom In">＋</button><button type="button" data-zoom="out" title="Zoom Out">−</button>';
  viewport.appendChild(box);

  function zoom(factor){
    const target=controls?.target?.clone() || (root ? new THREE.Box3().setFromObject(root).getCenter(new THREE.Vector3()) : new THREE.Vector3());
    const delta=camera.position.clone().sub(target);
    let distance=delta.length();
    if(!Number.isFinite(distance)||distance<.001)return;
    const minDistance=Math.max(camera.near*4,.03);
    const maxDistance=Math.max(minDistance+1,10000);
    distance=THREE.MathUtils.clamp(distance*factor,minDistance,maxDistance);
    delta.normalize().multiplyScalar(distance);
    camera.position.copy(target).add(delta);
    camera.lookAt(target);
    if(controls){controls.target.copy(target);controls.update()}
    camera.updateMatrixWorld(true);
  }

  box.querySelector('[data-zoom="in"]').onclick=()=>zoom(.82);
  box.querySelector('[data-zoom="out"]').onclick=()=>zoom(1.22);
  window.__autoRigZoomV49={zoomIn:()=>zoom(.82),zoomOut:()=>zoom(1.22)};
})();
'''
i=s.rfind('</script>')
if i<0: raise SystemExit('script end missing')
s=s[:i]+js+'\n'+s[i:]
p.write_text(s,encoding='utf-8')
print('Auto Rig zoom v49 applied: Zoom In + Zoom Out, Auto-only')
