from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist before Auto Rig machine patch')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_MACHINE_V42' in s:
    print('Auto Rig machine v42 already applied'); raise SystemExit(0)
if 'AUTO_RIG_PORTAL_V41' not in s: raise SystemExit('Auto Rig portal v41 must run first')
if "window.__OBJECT_MACHINE__='auto';" not in s: raise SystemExit('Auto Rig machine may only patch auto.html')

css=r'''
/* AUTO_RIG_MACHINE_V42 */
html[data-object-machine="auto"] body.auto-rig-v42 #editorScreen .toolrail,
html[data-object-machine="auto"] body.auto-rig-v42 #editorScreen .viewtools,
html[data-object-machine="auto"] body.auto-rig-v42 #editorScreen .overleft,
html[data-object-machine="auto"] body.auto-rig-v42 #editorScreen .overright,
html[data-object-machine="auto"] body.auto-rig-v42 #editorScreen .timeline,
html[data-object-machine="auto"] body.auto-rig-v42 #editorScreen #animSelect{display:none!important}
html[data-object-machine="auto"] body.auto-rig-v42 #editorScreen .editor{grid-template-columns:1fr!important}
html[data-object-machine="auto"] body.auto-rig-v42 #editorScreen .viewport{grid-column:1!important}
.auto-rig-shell-v42{position:absolute;inset:0;z-index:30;pointer-events:none;color:#f7f9fb}
.auto-rig-top-v42{position:absolute;left:12px;right:12px;top:10px;display:flex;justify-content:space-between;align-items:center;pointer-events:auto}
.auto-rig-chip-v42{border:1px solid #425026;background:rgba(12,16,11,.9);border-radius:11px;padding:8px 11px;font-size:12px}
.auto-rig-close-v42{width:36px;height:36px;border:1px solid #39432b;border-radius:10px;background:#171b13;color:#fff;font-size:20px}
.auto-rig-panel-v42{position:absolute;left:10px;right:10px;bottom:10px;max-height:48%;overflow:auto;pointer-events:auto;background:rgba(13,16,12,.96);border:1px solid #46552b;border-radius:16px;padding:14px;box-shadow:0 -12px 35px rgba(0,0,0,.3)}
.auto-rig-panel-v42 h3{margin:0 0 7px;font-size:16px}.auto-rig-panel-v42 p{margin:0 0 12px;color:#bac2b2;font-size:12px;line-height:1.45}
.arv42-actions{display:flex;gap:8px;margin-top:12px}.arv42-btn{height:42px;border-radius:10px;border:1px solid #46552b;background:#1b2018;padding:0 15px;font-weight:700}.arv42-btn.primary{margin:0;background:#baff31;color:#111;border-color:#baff31}.arv42-btn.back{margin-right:auto}
.arv42-example{display:grid;grid-template-columns:1fr 1fr;gap:9px}.arv42-example div{border:1px solid #32392d;border-radius:12px;padding:10px;background:#171b16}.arv42-example b{display:block;margin-bottom:4px}.arv42-good b{color:#9eea42}.arv42-bad b{color:#ff6363}.arv42-row{display:grid;grid-template-columns:72px 1fr 52px;gap:8px;align-items:center;margin:8px 0;font-size:12px}.arv42-row input[type=range]{width:100%}.arv42-num{height:31px;border:1px solid #39432f;border-radius:8px;background:#151914;color:#fff;text-align:center;width:52px}
.arv42-marker-layer{position:absolute;inset:0;pointer-events:none;z-index:29}.arv42-marker{position:absolute;width:22px;height:22px;margin:-11px 0 0 -11px;border:2px solid #d9ff55;border-radius:50%;background:rgba(30,36,21,.78);color:#fff;font:700 9px/18px system-ui;text-align:center;pointer-events:auto;touch-action:none;box-shadow:0 0 0 2px rgba(0,0,0,.35)}.arv42-marker.lr{border-color:#ff59d1}.arv42-marker.center{border-color:#71e6ff}
.arv42-marker-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;margin-top:8px}.arv42-marker-list span{font-size:10px;color:#cad0c4;background:#181c16;border:1px solid #30382b;padding:5px 7px;border-radius:8px}
.arv42-toggle{display:flex;align-items:center;justify-content:space-between;margin-top:10px;font-size:12px}.arv42-toggle button{width:48px;height:27px;border:0;border-radius:20px;background:#2b3028;position:relative}.arv42-toggle button:after{content:"";position:absolute;width:21px;height:21px;border-radius:50%;background:#fff;top:3px;left:3px}.arv42-toggle button.on{background:#9cd52e}.arv42-toggle button.on:after{left:24px}
.arv42-progress{height:8px;background:#252a22;border-radius:8px;overflow:hidden;margin:16px 0}.arv42-progress i{display:block;height:100%;width:0;background:#baff31;transition:width .25s}.arv42-percent{text-align:center;font-size:12px;color:#cdd4c7}.arv42-result{display:grid;grid-template-columns:1fr 1fr;gap:8px}.arv42-result div{border:1px solid #334028;border-radius:10px;padding:10px;background:#171c15}.arv42-result b{display:block;color:#baff31;font-size:18px}
@media(min-width:760px){.auto-rig-panel-v42{left:auto;width:380px;right:14px;bottom:14px;max-height:82%}}
'''
if '</style>' not in s: raise SystemExit('style end missing')
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// AUTO_RIG_MACHINE_V42
(function(){
  if(window.__autoRigMachineV42)return;
  const editor=document.getElementById('editorScreen');
  const viewport=editor?.querySelector('.viewport');
  const portal=document.getElementById('autoRigPortalV41');
  if(!editor||!viewport||!portal)return;

  const S={open:false,step:1,symmetry:true,box:null,size:null,center:null,markers:{},helper:null,bones:[],skeleton:null,skinned:0,original:null};
  window.__autoRigMachineV42=S;

  const shell=document.createElement('div');shell.className='auto-rig-shell-v42';shell.style.display='none';
  shell.innerHTML='<div class="auto-rig-top-v42"><span class="auto-rig-chip-v42" id="arv42Step">Auto Rig • Step 1/5</span><button class="auto-rig-close-v42" id="arv42Close">×</button></div><div class="arv42-marker-layer" id="arv42Markers"></div><div class="auto-rig-panel-v42" id="arv42Panel"></div>';
  viewport.appendChild(shell);
  const panel=shell.querySelector('#arv42Panel'), markerLayer=shell.querySelector('#arv42Markers'), stepChip=shell.querySelector('#arv42Step');

  function notify(msg){if(typeof toast==='function')toast(msg)}
  function modelBox(){if(!root)return null;root.updateMatrixWorld(true);const b=new THREE.Box3().setFromObject(root);if(b.isEmpty())return null;return b}
  function captureOriginal(){if(!root)return;S.original={position:root.position.clone(),quaternion:root.quaternion.clone(),scale:root.scale.clone()}}
  function closeRig(){S.open=false;document.body.classList.remove('auto-rig-v42');shell.style.display='none';markerLayer.innerHTML='';if(controls)controls.enabled=true}
  function openRig(){
    if(!root){notify('Import model terlebih dahulu sebelum Auto Rig.');return}
    S.box=modelBox();if(!S.box){notify('Model tidak memiliki geometry yang dapat di-rig.');return}
    S.size=S.box.getSize(new THREE.Vector3());S.center=S.box.getCenter(new THREE.Vector3());captureOriginal();
    S.open=true;S.step=1;document.body.classList.add('auto-rig-v42');shell.style.display='block';go('editorScreen');renderStep();
  }
  portal.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();openRig()},true);
  shell.querySelector('#arv42Close').onclick=closeRig;

  function btns(back,next,nextText='Next'){
    return '<div class="arv42-actions">'+(back?'<button class="arv42-btn back" id="arv42Back">Back</button>':'')+'<button class="arv42-btn primary" id="arv42Next">'+nextText+'</button></div>';
  }
  function wireNav(backFn,nextFn){const b=panel.querySelector('#arv42Back'),n=panel.querySelector('#arv42Next');if(b)b.onclick=backFn;if(n)n.onclick=nextFn}
  function step(n){S.step=n;renderStep()}

  function renderStep(){
    stepChip.textContent='Auto Rig • Step '+S.step+'/5';markerLayer.style.display=S.step===3?'block':'none';
    if(S.step===1){
      panel.innerHTML='<h3>Rig Model</h3><p>Posisikan karakter humanoid dengan anggota tubuh terlihat jelas. Pose A/T memberi hasil terbaik untuk marker dan weight.</p><div class="arv42-example"><div class="arv42-good"><b>✓ Good Example</b><span>Pose terbuka, lengan dan kaki tidak saling menutup.</span></div><div class="arv42-bad"><b>✕ Bad Example</b><span>Lengan menempel tubuh, anggota tubuh tertutup atau pose ekstrem.</span></div></div>'+btns(false,true);
      wireNav(null,()=>step(2));
    }else if(S.step===2){renderTransformStep()}
    else if(S.step===3){renderMarkerStep()}
    else if(S.step===4){renderProcessingStep()}
    else if(S.step===5){renderResultStep()}
  }

  function renderTransformStep(){
    const deg=[THREE.MathUtils.radToDeg(root.rotation.x),THREE.MathUtils.radToDeg(root.rotation.y),THREE.MathUtils.radToDeg(root.rotation.z)];
    const currentBox=modelBox(), h=Math.max(.001,currentBox.max.y-currentBox.min.y);
    panel.innerHTML='<h3>Orient & Size</h3><p>Hadapkan karakter ke depan, pusatkan tubuh, lalu sesuaikan tinggi sebelum menempatkan marker.</p>'+['X','Y','Z'].map((a,i)=>'<div class="arv42-row"><span>Rotate '+a+'</span><input type="range" min="-180" max="180" step="1" value="'+deg[i].toFixed(0)+'" data-rot="'+i+'"><input class="arv42-num" value="'+deg[i].toFixed(0)+'" data-rnum="'+i+'"></div>').join('')+'<div class="arv42-row"><span>Offset X</span><input type="range" min="-1" max="1" step=".01" value="'+root.position.x.toFixed(2)+'" data-pos="x"><input class="arv42-num" value="'+root.position.x.toFixed(2)+'" data-pnum="x"></div><div class="arv42-row"><span>Offset Z</span><input type="range" min="-1" max="1" step=".01" value="'+root.position.z.toFixed(2)+'" data-pos="z"><input class="arv42-num" value="'+root.position.z.toFixed(2)+'" data-pnum="z"></div><div class="arv42-row"><span>Height</span><input type="range" min="0.5" max="3" step=".01" value="'+h.toFixed(2)+'" id="arv42Height"><input class="arv42-num" value="'+h.toFixed(2)+'" id="arv42HeightNum"></div>'+btns(true,true);
    panel.querySelectorAll('[data-rot]').forEach(r=>r.oninput=()=>{const i=+r.dataset.rot;root.rotation[['x','y','z'][i]]=THREE.MathUtils.degToRad(+r.value);panel.querySelector('[data-rnum="'+i+'"]').value=r.value;root.updateMatrixWorld(true)});
    panel.querySelectorAll('[data-pos]').forEach(r=>r.oninput=()=>{const a=r.dataset.pos;root.position[a]=+r.value;panel.querySelector('[data-pnum="'+a+'"]').value=r.value;root.updateMatrixWorld(true)});
    const hr=panel.querySelector('#arv42Height'),hn=panel.querySelector('#arv42HeightNum');hr.oninput=()=>{const b=modelBox(),ch=Math.max(.001,b.max.y-b.min.y),f=(+hr.value)/ch;root.scale.multiplyScalar(f);root.updateMatrixWorld(true);hn.value=(+hr.value).toFixed(2)};
    wireNav(()=>step(1),()=>{initMarkers();step(3)});
  }

  function initMarkers(){
    S.box=modelBox();S.size=S.box.getSize(new THREE.Vector3());S.center=S.box.getCenter(new THREE.Vector3());const b=S.box,c=S.center,w=S.size.x,h=S.size.y,z=c.z;
    const P=(x,y)=>new THREE.Vector3(x,y,z);
    S.markers={
      chin:P(c.x,b.min.y+h*.88),
      shoulderL:P(c.x-w*.22,b.min.y+h*.77),shoulderR:P(c.x+w*.22,b.min.y+h*.77),
      elbowL:P(c.x-w*.36,b.min.y+h*.61),elbowR:P(c.x+w*.36,b.min.y+h*.61),
      wristL:P(c.x-w*.46,b.min.y+h*.48),wristR:P(c.x+w*.46,b.min.y+h*.48),
      groin:P(c.x,b.min.y+h*.48),
      kneeL:P(c.x-w*.12,b.min.y+h*.27),kneeR:P(c.x+w*.12,b.min.y+h*.27),
      ankleL:P(c.x-w*.12,b.min.y+h*.055),ankleR:P(c.x+w*.12,b.min.y+h*.055)
    };
  }
  const markerDefs=[['chin','C','center'],['shoulderL','SL','lr'],['shoulderR','SR','lr'],['elbowL','EL','lr'],['elbowR','ER','lr'],['wristL','WL','lr'],['wristR','WR','lr'],['groin','G','center'],['kneeL','KL','lr'],['kneeR','KR','lr'],['ankleL','AL','lr'],['ankleR','AR','lr']];
  function projectMarkers(){
    if(!S.open||S.step!==3)return;const r=viewport.getBoundingClientRect();
    markerDefs.forEach(([k])=>{const el=markerLayer.querySelector('[data-m="'+k+'"]'),p=S.markers[k]?.clone();if(!el||!p)return;p.project(camera);el.style.left=((p.x*.5+.5)*r.width)+'px';el.style.top=((-p.y*.5+.5)*r.height)+'px';el.style.display=(p.z<-1||p.z>1)?'none':'block'});
    requestAnimationFrame(projectMarkers);
  }
  function renderMarkerStep(){
    panel.innerHTML='<h3>Place Markers</h3><p>Geser marker ke titik anatomi yang sesuai. Marker ini menjadi sumber utama pembentukan skeleton.</p><div class="arv42-marker-list">'+markerDefs.map(([k])=>'<span>'+k+'</span>').join('')+'</div><div class="arv42-toggle"><span>Symmetry</span><button id="arv42Sym" class="'+(S.symmetry?'on':'')+'"></button></div>'+btns(true,true,'Confirm');
    markerLayer.innerHTML=markerDefs.map(([k,t,c])=>'<div class="arv42-marker '+c+'" data-m="'+k+'">'+t+'</div>').join('');
    panel.querySelector('#arv42Sym').onclick=e=>{S.symmetry=!S.symmetry;e.currentTarget.classList.toggle('on',S.symmetry)};
    const plane=new THREE.Plane(),raycaster=new THREE.Raycaster(),pt=new THREE.Vector3(),ndc=new THREE.Vector2();
    function dragMarker(ev,key){const r=viewport.getBoundingClientRect();ndc.x=((ev.clientX-r.left)/r.width)*2-1;ndc.y=-((ev.clientY-r.top)/r.height)*2+1;raycaster.setFromCamera(ndc,camera);const n=new THREE.Vector3();camera.getWorldDirection(n);plane.setFromNormalAndCoplanarPoint(n,S.markers[key]);if(raycaster.ray.intersectPlane(plane,pt)){S.markers[key].copy(pt);if(S.symmetry&&/[LR]$/.test(key)){const other=key.slice(0,-1)+(key.endsWith('L')?'R':'L');if(S.markers[other]){S.markers[other].copy(pt);S.markers[other].x=2*S.center.x-pt.x}}}}
    markerLayer.querySelectorAll('.arv42-marker').forEach(el=>{let down=false;el.onpointerdown=e=>{down=true;controls.enabled=false;el.setPointerCapture?.(e.pointerId);e.preventDefault()};el.onpointermove=e=>{if(down)dragMarker(e,el.dataset.m)};const up=()=>{down=false;controls.enabled=true};el.onpointerup=up;el.onpointercancel=up});
    requestAnimationFrame(projectMarkers);
    wireNav(()=>step(2),()=>step(4));
  }

  function localPoint(world){const q=world.clone();root.worldToLocal(q);return q}
  function makeBone(name,worldPos,parent,parentLocal){const b=new THREE.Bone();b.name=name;const lp=localPoint(worldPos);b.position.copy(parent?lp.clone().sub(parentLocal):lp);if(parent)parent.add(b);return {bone:b,local:lp}}
  function generateSkeleton(){
    if(S.helper){scene.remove(S.helper);S.helper=null}S.bones=[];
    const m=S.markers,b=S.box,h=S.size.y,c=S.center;const chestW=new THREE.Vector3(c.x,b.min.y+h*.69,c.z),neckW=new THREE.Vector3(c.x,b.min.y+h*.82,c.z),headW=new THREE.Vector3(c.x,b.min.y+h*.94,c.z);
    const hipLW=new THREE.Vector3(m.kneeL.x,m.groin.y,c.z),hipRW=new THREE.Vector3(m.kneeR.x,m.groin.y,c.z),footLW=new THREE.Vector3(m.ankleL.x,b.min.y+h*.015,c.z+h*.025),footRW=new THREE.Vector3(m.ankleR.x,b.min.y+h*.015,c.z+h*.025);
    const specs={};
    specs.hips=makeBone('Hips',m.groin,null,null);root.add(specs.hips.bone);S.bones.push(specs.hips.bone);
    specs.spine=makeBone('Spine',new THREE.Vector3(c.x,b.min.y+h*.58,c.z),specs.hips.bone,specs.hips.local);S.bones.push(specs.spine.bone);
    specs.chest=makeBone('Chest',chestW,specs.spine.bone,specs.spine.local);S.bones.push(specs.chest.bone);
    specs.neck=makeBone('Neck',neckW,specs.chest.bone,specs.chest.local);S.bones.push(specs.neck.bone);
    specs.head=makeBone('Head',headW,specs.neck.bone,specs.neck.local);S.bones.push(specs.head.bone);
    for(const side of ['L','R']){
      const sh=makeBone('Shoulder_'+side,m['shoulder'+side],specs.chest.bone,specs.chest.local);S.bones.push(sh.bone);
      const ua=makeBone('UpperArm_'+side,m['elbow'+side],sh.bone,sh.local);S.bones.push(ua.bone);
      const la=makeBone('LowerArm_'+side,m['wrist'+side],ua.bone,ua.local);S.bones.push(la.bone);
      const handPos=m['wrist'+side].clone();handPos.x+=(side==='L'?-1:1)*S.size.x*.07;const hand=makeBone('Hand_'+side,handPos,la.bone,la.local);S.bones.push(hand.bone);
      const hip=makeBone('UpperLeg_'+side,side==='L'?hipLW:hipRW,specs.hips.bone,specs.hips.local);S.bones.push(hip.bone);
      const knee=makeBone('LowerLeg_'+side,m['knee'+side],hip.bone,hip.local);S.bones.push(knee.bone);
      const ankle=makeBone('Foot_'+side,m['ankle'+side],knee.bone,knee.local);S.bones.push(ankle.bone);
      const toe=makeBone('Toe_'+side,side==='L'?footLW:footRW,ankle.bone,ankle.local);S.bones.push(toe.bone);
    }
    root.updateMatrixWorld(true);S.skeleton=new THREE.Skeleton(S.bones);S.skeleton.calculateInverses();S.helper=new THREE.SkeletonHelper(root);S.helper.material.depthTest=false;S.helper.material.transparent=true;S.helper.material.opacity=.95;scene.add(S.helper);
    return specs;
  }

  async function skinGeometry(){
    if(!S.skeleton)return 0;root.updateMatrixWorld(true);const bonePts=S.bones.map(b=>b.getWorldPosition(new THREE.Vector3()));let done=0;const targets=[];root.traverse(o=>{if(o.isMesh&&!o.isSkinnedMesh&&!o.isSkeletonHelper&&o.geometry?.attributes?.position)targets.push(o)});
    for(const mesh of targets){
      const g=mesh.geometry.clone(),pos=g.attributes.position,count=pos.count,idx=new Uint16Array(count*4),wei=new Float32Array(count*4),v=new THREE.Vector3();
      for(let i=0;i<count;i++){
        v.fromBufferAttribute(pos,i);mesh.localToWorld(v);const cand=bonePts.map((p,bi)=>({bi,d:v.distanceToSquared(p)})).sort((a,b)=>a.d-b.d).slice(0,4);let sum=0;for(let j=0;j<4;j++){const w=1/(Math.sqrt(cand[j].d)+1e-4);wei[i*4+j]=w;idx[i*4+j]=cand[j].bi;sum+=w}for(let j=0;j<4;j++)wei[i*4+j]/=sum;
        if((i%20000)===0)await new Promise(requestAnimationFrame);
      }
      g.setAttribute('skinIndex',new THREE.Uint16BufferAttribute(idx,4));g.setAttribute('skinWeight',new THREE.Float32BufferAttribute(wei,4));
      const sk=new THREE.SkinnedMesh(g,mesh.material);sk.name=mesh.name;sk.position.copy(mesh.position);sk.quaternion.copy(mesh.quaternion);sk.scale.copy(mesh.scale);sk.visible=mesh.visible;sk.castShadow=mesh.castShadow;sk.receiveShadow=mesh.receiveShadow;
      const parent=mesh.parent;const at=parent.children.indexOf(mesh);parent.remove(mesh);parent.add(sk);if(at>=0){parent.children.splice(parent.children.indexOf(sk),1);parent.children.splice(at,0,sk)};sk.updateMatrixWorld(true);sk.bind(S.skeleton,sk.matrixWorld.clone());done++;
    }
    S.skinned=done;return done;
  }

  async function renderProcessingStep(){
    markerLayer.innerHTML='';panel.innerHTML='<h3>Creating your model…</h3><p>Generating humanoid hierarchy, calculating skin weights, binding meshes, and validating the result.</p><div class="arv42-progress"><i id="arv42Bar"></i></div><div class="arv42-percent" id="arv42Pct">0%</div>';
    const bar=panel.querySelector('#arv42Bar'),pct=panel.querySelector('#arv42Pct');const set=v=>{bar.style.width=v+'%';pct.textContent=v+'%'};
    try{set(12);await new Promise(r=>setTimeout(r,80));generateSkeleton();set(38);await new Promise(r=>setTimeout(r,80));await skinGeometry();set(84);root.updateMatrixWorld(true);if(S.helper)S.helper.update();set(100);await new Promise(r=>setTimeout(r,180));step(5)}catch(e){console.error('AUTO_RIG_V42',e);panel.innerHTML='<h3>Auto Rig failed</h3><p>'+String(e?.message||e)+'</p>'+btns(true,false,'Back');wireNav(()=>step(3),null)}
  }
  function renderResultStep(){
    panel.innerHTML='<h3>Rig Complete</h3><p>Skeleton humanoid dibuat dari marker dan skin weights sudah dihitung untuk mesh yang belum memiliki skin.</p><div class="arv42-result"><div><b>'+S.bones.length+'</b><span>Bones</span></div><div><b>'+S.skinned+'</b><span>Meshes skinned</span></div></div><div class="arv42-actions"><button class="arv42-btn back" id="arv42Back">Markers</button><button class="arv42-btn primary" id="arv42Done">Done</button></div>';
    panel.querySelector('#arv42Back').onclick=()=>step(3);panel.querySelector('#arv42Done').onclick=()=>{closeRig();notify('Auto Rig selesai. Skeleton aktif pada model.')};
  }
})();
'''
i=s.rfind('</script>')
if i<0: raise SystemExit('script end missing')
s=s[:i]+js+'\n'+s[i:]
p.write_text(s,encoding='utf-8')
print('Auto Rig machine v42 applied: pose wizard, transform setup, draggable markers, skeleton generation, skin weighting, result preview')
