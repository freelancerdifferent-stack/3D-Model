from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html missing')
s=p.read_text(encoding='utf-8')
if 'AUTO_VERTICAL_GUIDE_V47' in s:
    print('Auto vertical guide v47 already applied'); raise SystemExit(0)
if 'AUTO_RIG_REFERENCE_SKELETON_V46' not in s: raise SystemExit('Auto Rig reference skeleton v46 must run first')
if "window.__OBJECT_MACHINE__='auto';" not in s: raise SystemExit('Auto-only patch')

css=r'''
/* AUTO_VERTICAL_GUIDE_V47 */
html[data-object-machine="auto"] #verticalGuideBtnV47 strong{font-size:22px;line-height:18px;color:#ff9418}
html[data-object-machine="auto"] #verticalGuideBtnV47.on{background:#214777}
'''
if '</style>' not in s: raise SystemExit('style end missing')
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// AUTO_VERTICAL_GUIDE_V47
(function(){
  if(window.__autoVerticalGuideV47)return;
  const editor=document.getElementById('editorScreen');
  const viewtools=editor?.querySelector('.viewtools');
  if(!editor||!viewtools)return;

  const btn=document.createElement('button');
  btn.type='button';
  btn.id='verticalGuideBtnV47';
  btn.innerHTML='<strong>│</strong>Vertical';
  viewtools.appendChild(btn);

  const material=new THREE.LineBasicMaterial({color:0xff9418,transparent:true,opacity:.95,depthTest:false,depthWrite:false});
  const geometry=new THREE.BufferGeometry();
  const line=new THREE.Line(geometry,material);
  line.name='AutoVerticalGuideV47';
  line.renderOrder=9999;
  line.visible=false;
  scene.add(line);

  const state={enabled:false,line,button:btn};
  window.__autoVerticalGuideV47=state;

  function guideRange(){
    if(root){
      root.updateMatrixWorld(true);
      const b=new THREE.Box3().setFromObject(root);
      if(!b.isEmpty()){
        const size=b.getSize(new THREE.Vector3());
        const c=b.getCenter(new THREE.Vector3());
        const pad=Math.max(size.y*.18,.25);
        return {x:c.x,z:c.z,y0:b.min.y-pad,y1:b.max.y+pad};
      }
    }
    return {x:0,z:0,y0:0,y1:4};
  }

  function refresh(){
    const g=guideRange();
    geometry.setFromPoints([new THREE.Vector3(g.x,g.y0,g.z),new THREE.Vector3(g.x,g.y1,g.z)]);
    geometry.computeBoundingSphere();
    line.visible=state.enabled;
  }

  btn.onclick=()=>{
    state.enabled=!state.enabled;
    btn.classList.toggle('on',state.enabled);
    refresh();
    if(typeof toast==='function')toast(state.enabled?'Vertical guide ON':'Vertical guide OFF');
  };

  // Keep the guide centered on the current model while transforms / Auto Rig setup change it.
  let last='';
  function tick(){
    if(state.enabled){
      const g=guideRange();
      const sig=[g.x,g.z,g.y0,g.y1].map(v=>v.toFixed(5)).join('|');
      if(sig!==last){last=sig;refresh()}
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
})();
'''
i=s.rfind('</script>')
if i<0: raise SystemExit('script end missing')
s=s[:i]+js+'\n'+s[i:]
p.write_text(s,encoding='utf-8')
print('Auto vertical guide v47 applied: right-side toggle, orange model-centered guide, Auto-only')
