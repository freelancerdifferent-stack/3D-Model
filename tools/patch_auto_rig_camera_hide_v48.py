from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html missing')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_CAMERA_HIDE_V48' in s:
    print('Auto Rig camera/hide v48 already applied'); raise SystemExit(0)
if 'AUTO_VERTICAL_GUIDE_V47' not in s: raise SystemExit('Auto vertical guide v47 must run first')
if 'AUTO_RIG_MACHINE_V42' not in s: raise SystemExit('Auto Rig machine v42 missing')

css=r'''
/* AUTO_RIG_CAMERA_HIDE_V48 */
.auto-rig-camera-v48{position:absolute;left:12px;top:62px;z-index:34;display:none;flex-direction:column;gap:5px;pointer-events:auto}
body.auto-rig-v42 .auto-rig-camera-v48{display:flex}
.auto-rig-camera-v48 button{min-width:62px;height:31px;padding:0 9px;border:1px solid #39432b;border-radius:9px;background:rgba(18,23,18,.91);color:#eef2ec;font-size:11px;text-align:left}
.auto-rig-camera-v48 button.active{border-color:#baff31;color:#baff31;background:#1c2917}
.auto-rig-hide-v48{position:absolute;left:50%;bottom:calc(48% + 16px);transform:translateX(-50%);z-index:35;width:44px;height:32px;border:1px solid #526132;border-radius:12px;background:rgba(15,19,14,.96);color:#fff;font-size:22px;line-height:26px;pointer-events:auto;display:none}
body.auto-rig-v42 .auto-rig-hide-v48{display:block}
body.auto-rig-v42.auto-rig-panel-hidden-v48 .auto-rig-panel-v42{display:none!important}
body.auto-rig-v42.auto-rig-panel-hidden-v48 .auto-rig-hide-v48{bottom:74px}
@media(min-width:760px){.auto-rig-hide-v48{left:auto;right:190px;transform:none;bottom:calc(82% + 20px)}body.auto-rig-v42.auto-rig-panel-hidden-v48 .auto-rig-hide-v48{bottom:74px}}
'''
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// AUTO_RIG_CAMERA_HIDE_V48
(function(){
  if(window.__autoRigCameraHideV48)return;
  const editor=document.getElementById('editorScreen');
  const viewport=editor?.querySelector('.viewport');
  const S=window.__autoRigMachineV42;
  if(!viewport||!S)return;

  const cam=document.createElement('div');
  cam.className='auto-rig-camera-v48';cam.id='autoRigCameraV48';
  cam.innerHTML='<button data-view="front">Front</button><button data-view="back">Back</button><button data-view="right">Right</button><button data-view="left">Left</button>';
  viewport.appendChild(cam);

  const hide=document.createElement('button');
  hide.type='button';hide.id='autoRigHidePanelV48';hide.className='auto-rig-hide-v48';hide.textContent='⌄';hide.title='Hide controls';
  viewport.appendChild(hide);

  const state={panelHidden:false,view:null};
  window.__autoRigCameraHideV48=state;

  function targetAndDistance(){
    let b=null;
    if(root){root.updateMatrixWorld(true);b=new THREE.Box3().setFromObject(root)}
    const target=b&&!b.isEmpty()?b.getCenter(new THREE.Vector3()):(controls?.target?.clone()||new THREE.Vector3());
    const size=b&&!b.isEmpty()?b.getSize(new THREE.Vector3()):new THREE.Vector3(2,2,2);
    const dist=Math.max(size.x,size.y,size.z,1)*1.65;
    return {target,dist};
  }
  function setView(name){
    const {target,dist}=targetAndDistance();
    const pos=target.clone();
    if(name==='front')pos.z+=dist;
    else if(name==='back')pos.z-=dist;
    else if(name==='right')pos.x+=dist;
    else if(name==='left')pos.x-=dist;
    else return;
    camera.position.copy(pos);camera.up.set(0,1,0);camera.lookAt(target);
    if(controls){controls.target.copy(target);controls.update()}
    camera.updateMatrixWorld(true);
    state.view=name;
    cam.querySelectorAll('button').forEach(b=>b.classList.toggle('active',b.dataset.view===name));
  }
  cam.querySelectorAll('button').forEach(b=>b.onclick=()=>setView(b.dataset.view));

  hide.onclick=()=>{
    state.panelHidden=!state.panelHidden;
    document.body.classList.toggle('auto-rig-panel-hidden-v48',state.panelHidden);
    hide.textContent=state.panelHidden?'⌃':'⌄';
    hide.title=state.panelHidden?'Show controls':'Hide controls';
  };

  // Reset panel visibility every time a new Auto Rig session opens.
  const portal=document.getElementById('autoRigPortalV41');
  portal?.addEventListener('click',()=>{
    state.panelHidden=false;state.view=null;
    document.body.classList.remove('auto-rig-panel-hidden-v48');hide.textContent='⌄';
    cam.querySelectorAll('button').forEach(b=>b.classList.remove('active'));
  },true);

  window.__autoRigCameraHideV48.setView=setView;
})();
'''
i=s.rfind('</script>')
if i<0: raise SystemExit('script end missing')
s=s[:i]+js+'\n'+s[i:]
p.write_text(s,encoding='utf-8')
print('Auto Rig camera/hide v48 applied: Front Back Right Left + collapsible control panel')
