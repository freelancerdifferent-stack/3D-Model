from pathlib import Path

p=Path('app/src/main/assets/autorig.html')
if not p.exists():
    raise SystemExit('autorig.html must be built by patch_autorig_machine_v42 first')
s=p.read_text(encoding='utf-8')
if 'AUTORIG_ENGINE_V43' in s:
    print('Auto Rig engine v43 already applied'); raise SystemExit(0)
if 'AUTORIG_MACHINE_V42' not in s:
    raise SystemExit('Auto Rig machine v42 marker missing')

css=r'''
/* AUTORIG_ENGINE_V43 */
#arMachineBadgeV43{position:absolute;left:50%;top:10px;transform:translateX(-50%);z-index:8;padding:6px 12px;border:1px solid #baff36;border-radius:999px;background:#12280cd9;color:#baff36;font-size:10px;font-weight:900;letter-spacing:.1em;pointer-events:none}
#arRigStartV43{position:absolute;left:50%;bottom:78px;transform:translateX(-50%);z-index:6;height:46px;padding:0 22px;border:0;border-radius:14px;background:#baff36;color:#0a1406;font-size:15px;font-weight:900;display:flex;align-items:center;gap:8px;box-shadow:0 8px 24px #0009}
#arWizardV43{display:none;position:absolute;inset:0;z-index:40;pointer-events:none}
#arWizardV43.on{display:block}
#arWizardV43 .ar-sheet{position:absolute;left:0;right:0;bottom:0;max-height:58%;transition:max-height .2s;overflow:auto;background:#0d1a12f2;border-top:1px solid #2c6d42;border-radius:18px 18px 0 0;padding:14px 16px 18px;pointer-events:auto;color:#e8f7ec}
#arWizardV43.markers .ar-sheet{max-height:40%}
#arWizardV43 .ar-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
#arWizardV43 .ar-head b{font-size:16px}
#arWizardV43 .ar-close{width:34px;height:34px;border:1px solid #2c6d42;border-radius:9px;background:#122718;color:#cfe9d6}
#arWizardV43 .ar-step{display:none}
#arWizardV43 .ar-step.on{display:block}
#arWizardV43 .ar-note{font-size:12px;color:#9fc7ab;line-height:1.5;margin:6px 0 10px}
#arWizardV43 .ar-warn{font-size:12px;color:#ffd57a;background:#332711;border:1px solid #7a6237;border-radius:9px;padding:8px 10px;margin:6px 0}
#arWizardV43 .ar-actions{display:flex;gap:9px;justify-content:flex-end;margin-top:12px}
#arWizardV43 .ar-btn{height:42px;padding:0 18px;border-radius:10px;border:1px solid #2c6d42;background:#122718;color:#d9f3e0;font-weight:700}
#arWizardV43 .ar-btn.primary{border:0;background:#baff36;color:#0a1406;font-weight:900}
#arWizardV43 .ar-btn[disabled]{opacity:.4}
#arWizardV43 .ar-ex{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:8px 0}
#arWizardV43 .ar-ex div{border:1px solid #27313d;border-radius:11px;padding:10px;font-size:11px;line-height:1.45;background:#0f1d14}
#arWizardV43 .ar-ex .good{border-color:#2c6d42}#arWizardV43 .ar-ex .good b{color:#5be27f}
#arWizardV43 .ar-ex .bad{border-color:#6d3434}#arWizardV43 .ar-ex .bad b{color:#e2665b}
#arWizardV43 .ar-row{display:grid;grid-template-columns:74px 1fr 64px 34px;gap:8px;align-items:center;margin:7px 0;font-size:12px}
#arWizardV43 .ar-row input[type=range]{width:100%}
#arWizardV43 .ar-row input[type=number]{width:100%;height:32px;border:1px solid #2c6d42;background:#0f1d14;color:#fff;border-radius:7px;padding:0 6px}
#arWizardV43 .ar-row button{height:32px;border:1px solid #2c6d42;border-radius:7px;background:#122718;color:#9fc7ab}
#arWizardV43 .ar-mk{display:flex;align-items:center;gap:9px;padding:7px 9px;border:1px solid #21402c;border-radius:10px;margin:5px 0;font-size:13px}
#arWizardV43 .ar-mk.active{border-color:#baff36;background:#15290e}
#arWizardV43 .ar-mk .dot{width:14px;height:14px;border-radius:50%;border:2px solid #555}
#arWizardV43 .ar-mk .st{margin-left:auto;font-size:11px;color:#87a892}
#arWizardV43 .ar-mk.done .st{color:#5be27f}
#arWizardV43 .ar-sym{display:flex;align-items:center;justify-content:space-between;margin-top:9px;font-size:13px}
#arWizardV43 .ar-progress{height:14px;border-radius:8px;background:#122718;border:1px solid #2c6d42;overflow:hidden;margin:14px 0}
#arWizardV43 .ar-progress i{display:block;height:100%;width:0%;background:linear-gradient(90deg,#5be27f,#baff36)}
#arWizardV43 .ar-ptext{text-align:center;font-size:13px;color:#c9ecd2}
'''
if '</style>' not in s: raise SystemExit('style end missing')
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// AUTORIG_ENGINE_V43 — marker-guided humanoid auto rig, fully on-device.
(function(){
 const viewport=$('editorScreen')?.querySelector('.viewport');
 if(!viewport)return;

 // Identitas mesin selalu terlihat, termasuk di tab Object yang tanpa topbar.
 const arBadge=document.createElement('div');
 arBadge.id='arMachineBadgeV43';arBadge.textContent='☠ AUTO RIG';
 viewport.appendChild(arBadge);

 const startBtn=document.createElement('button');
 startBtn.id='arRigStartV43';startBtn.type='button';startBtn.innerHTML='⚡ Rig';
 viewport.appendChild(startBtn);

 const wiz=document.createElement('div');wiz.id='arWizardV43';
 wiz.innerHTML=`
  <div class="ar-sheet">
   <div class="ar-head"><b id="arTitleV43">Rig Model</b><button type="button" class="ar-close" id="arCloseV43">✕</button></div>
   <div class="ar-step" id="arStep2V43">
     <div class="ar-ex">
       <div class="good"><b>😊 Good Example</b><br>Mendekati pose T/A, jarak jelas antara lengan dan badan, seluruh tubuh terlihat.</div>
       <div class="bad"><b>🙁 Bad Example</b><br>Anggota badan saling menempel atau tertutup, tubuh tidak lengkap.</div>
     </div>
     <div class="ar-note">Hasil terbaik: karakter humanoid menghadap ke depan.</div>
     <div class="ar-warn" id="arHadRigWarnV43" style="display:none">⚠ Model ini sudah punya skeleton. Rig lama akan DIGANTI dengan hasil Auto Rig — tombol "Batalkan Rig" mengembalikannya.</div>
     <div class="ar-actions"><button class="ar-btn primary" id="arNext2V43">Next ›</button></div>
   </div>
   <div class="ar-step" id="arStep3V43">
     <div class="ar-note">Pusatkan karakter, hadapkan ke depan, dan sesuaikan tingginya.</div>
     <div class="ar-row"><span>Rotate X</span><input type="range" id="arRotX" min="-180" max="180" value="0"><input type="number" id="arRotXn" value="0"><button data-ar-reset="arRotX">⟲</button></div>
     <div class="ar-row"><span>Rotate Y</span><input type="range" id="arRotY" min="-180" max="180" value="0"><input type="number" id="arRotYn" value="0"><button data-ar-reset="arRotY">⟲</button></div>
     <div class="ar-row"><span>Rotate Z</span><input type="range" id="arRotZ" min="-180" max="180" value="0"><input type="number" id="arRotZn" value="0"><button data-ar-reset="arRotZ">⟲</button></div>
     <div class="ar-row"><span>Offset Y</span><input type="range" id="arOffY" min="-2" max="2" step="0.01" value="0"><input type="number" id="arOffYn" value="0" step="0.01"><button data-ar-reset="arOffY">⟲</button></div>
     <div class="ar-row"><span>Height m</span><input type="range" id="arHgt" min="0.3" max="4" step="0.01" value="1.7"><input type="number" id="arHgtn" value="1.7" step="0.01"><button data-ar-reset="arHgt">⟲</button></div>
     <div class="ar-actions"><button class="ar-btn" id="arBack3V43">‹ Back</button><button class="ar-btn primary" id="arNext3V43">Next ›</button></div>
   </div>
   <div class="ar-step" id="arStep4V43">
     <div class="ar-note">Tap model untuk memasang marker pada posisi yang sesuai. Marker yang tepat memberi hasil animasi lebih baik.</div>
     <div id="arMarkerListV43"></div>
     <div class="ar-sym"><span>Symmetry (sisi B otomatis dicerminkan)</span><input type="checkbox" id="arSymV43" checked></div>
     <div class="ar-actions"><button class="ar-btn" id="arBack4V43">‹ Back</button><button class="ar-btn primary" id="arConfirmV43" disabled>Confirm ›</button></div>
   </div>
   <div class="ar-step" id="arStep5V43">
     <div class="ar-ptext" id="arPTextV43">Creating your rig… 0%</div>
     <div class="ar-progress"><i id="arPBarV43"></i></div>
     <div class="ar-note">Skeleton dibangun dari marker, lalu bobot kulit dihitung per vertex — semuanya di perangkat ini.</div>
   </div>
   <div class="ar-step" id="arStep6V43">
     <div class="ar-note" id="arResultNoteV43">Rig selesai.</div>
     <div class="ar-row" style="grid-template-columns:110px 1fr 60px"><span>Kehalusan</span><input type="range" id="arSmooth" min="2" max="8" step="1" value="4"><span id="arSmoothVal">4</span></div>
     <div class="ar-actions">
       <button class="ar-btn" id="arUndoRigV43">Batalkan Rig</button>
       <button class="ar-btn" id="arWiggleV43">▶ Tes Gerak</button>
       <button class="ar-btn primary" id="arDoneV43">Selesai</button>
     </div>
     <div class="ar-note">Setelah selesai: rapikan bobot di mode Skeleton → Rig bila perlu, lalu Export GLB atau simpan project.</div>
   </div>
  </div>`;
 viewport.appendChild(wiz);

 const MARKS=[
  {id:'chin',   label:'Chin',      color:'#4dd7e0', pair:false},
  {id:'shoulder',label:'Shoulders',color:'#e6e14a', pair:true},
  {id:'elbow',  label:'Elbows',    color:'#e07adf', pair:true},
  {id:'wrist',  label:'Wrists',    color:'#e0567a', pair:true},
  {id:'groin',  label:'Groin',     color:'#ffffff', pair:false},
  {id:'knee',   label:'Knees',     color:'#e6a44a', pair:true},
  {id:'ankle',  label:'Ankles',    color:'#8de04d', pair:true},
 ];
 const state={open:false,step:0,points:{},active:null,helper:null,rigged:null,markerMeshes:[],raycaster:new THREE.Raycaster()};

 const steps=[null,null,$('arStep2V43'),$('arStep3V43'),$('arStep4V43'),$('arStep5V43'),$('arStep6V43')];
 function show(step){
   state.step=step;
   steps.forEach(el=>el&&el.classList.remove('on'));
   if(steps[step])steps[step].classList.add('on');
   $('arTitleV43').textContent=step===6?'Rig Result':'Rig Model';
   wiz.classList.toggle('markers',step===4);
   if(step===4)frameForMarkers();else restoreMarkerCam();
 }
 // Selama layar marker, seluruh model dibingkai ke area di atas sheet supaya
 // setiap titik anatomi bisa di-tap; pose kamera semula dipulihkan sesudahnya.
 let arCamSaveV43=null;
 function frameForMarkers(){
   if(arCamSaveV43||!root)return;
   arCamSaveV43={pos:camera.position.clone(),tgt:controls.target.clone()};
   root.updateMatrixWorld(true);
   const bb=new THREE.Box3().setFromObject(root);
   const r=canvas.getBoundingClientRect();
   const yLimit=r.top+r.height*0.52, yTop=r.top+r.height*0.06;
   const cx=(bb.min.x+bb.max.x)/2, cz=(bb.min.z+bb.max.z)/2;
   const projY=w=>{const v=w.clone().project(camera);return r.top+(-v.y*0.5+0.5)*r.height};
   for(let it=0;it<4;it++){
     camera.updateMatrixWorld(true);
     const yb=projY(new THREE.Vector3(cx,bb.min.y,cz));
     const yt=projY(new THREE.Vector3(cx,bb.max.y,cz));
     const span=yb-yt, avail=yLimit-yTop;
     if(span>avail){
       const f=(span/avail)*1.06;
       const dir=camera.position.clone().sub(controls.target);
       camera.position.copy(controls.target).add(dir.multiplyScalar(f));
       continue;
     }
     const off=yb-yLimit;
     if(Math.abs(off)>4){
       const dist=camera.position.distanceTo(controls.target);
       const wpp=2*dist*Math.tan(THREE.MathUtils.degToRad(camera.fov/2))/r.height;
       camera.position.y-=off*wpp;controls.target.y-=off*wpp;
     } else break;
   }
   camera.updateMatrixWorld(true);
 }
 function restoreMarkerCam(){
   if(!arCamSaveV43)return;
   camera.position.copy(arCamSaveV43.pos);controls.target.copy(arCamSaveV43.tgt);
   camera.updateMatrixWorld(true);arCamSaveV43=null;
 }
 function openWiz(){
   if(!root){msg('Import model dulu sebelum Auto Rig');return}
   state.hadRig=rootHasBones();
   const w=$('arHadRigWarnV43');if(w)w.style.display=state.hadRig?'block':'none';
   wiz.classList.add('on');state.open=true;show(2);
 }
 function closeWiz(){
   wiz.classList.remove('on');state.open=false;clearMarkers();restoreMarkerCam();
 }
 startBtn.onclick=openWiz;
 $('arCloseV43').onclick=closeWiz;
 function rootHasBones(){let n=0;if(root)root.traverse(o=>{if(o.isBone)n++});return n>0}

 // ---- Step 3: normalize ----
 function bindPair(rid,apply){
   const r=$(rid),n=$(rid+'n');
   const sync=v=>{r.value=v;n.value=v;apply(parseFloat(v)||0)};
   r.oninput=()=>sync(r.value);
   n.onchange=()=>sync(n.value);
 }
 const deg=THREE.MathUtils.degToRad;
 let baseScale=1,baseY=0;
 function currentHeight(){
   if(!root)return 1;
   const b=new THREE.Box3().setFromObject(root);
   return Math.max(1e-6,b.max.y-b.min.y);
 }
 function enterStep3(){
   baseScale=root.scale.x;baseY=root.position.y;
   const h=currentHeight();
   $('arHgt').value=$('arHgtn').value=h.toFixed(2);
 }
 bindPair('arRotX',v=>{root.rotation.x=deg(v);root.updateMatrixWorld(true)});
 bindPair('arRotY',v=>{root.rotation.y=deg(v);root.updateMatrixWorld(true)});
 bindPair('arRotZ',v=>{root.rotation.z=deg(v);root.updateMatrixWorld(true)});
 bindPair('arOffY',v=>{root.position.y=baseY+v;root.updateMatrixWorld(true)});
 bindPair('arHgt',v=>{
   const cur=currentHeight();
   if(cur>1e-6&&v>0){root.scale.multiplyScalar(v/cur);root.updateMatrixWorld(true)}
 });
 wiz.querySelectorAll('[data-ar-reset]').forEach(b=>b.onclick=()=>{
   const id=b.dataset.arReset,def=id==='arHgt'?'1.7':'0';
   $(id).value=$(id+'n').value=def;$(id).oninput();
 });

 // ---- Step 4: markers ----
 function slots(){
   const out=[];
   for(const m of MARKS){ if(m.pair){out.push(m.id+'A');out.push(m.id+'B')} else out.push(m.id) }
   return out;
 }
 function renderMarkerList(){
   const box=$('arMarkerListV43');box.innerHTML='';
   for(const m of MARKS){
     const row=document.createElement('div');row.className='ar-mk';row.dataset.mid=m.id;
     const ids=m.pair?[m.id+'A',m.id+'B']:[m.id];
     const done=ids.every(k=>state.points[k]);
     if(done)row.classList.add('done');
     if(state.active&&ids.includes(state.active))row.classList.add('active');
     row.innerHTML=`<span class="dot" style="border-color:${m.color}"></span>${m.label}<span class="st">${ids.filter(k=>state.points[k]).length}/${ids.length}</span>`;
     row.onclick=()=>{state.active=ids.find(k=>!state.points[k])||ids[0];renderMarkerList();msg('Tap model untuk marker: '+m.label)};
     box.appendChild(row);
   }
   const all=slots().every(k=>state.points[k]);
   $('arConfirmV43').disabled=!all;
   if(!state.active){const nx=slots().find(k=>!state.points[k]);state.active=nx||null;}
 }
 function markColor(slot){const m=MARKS.find(x=>slot.startsWith(x.id));return m?m.color:'#fff'}
 function addMarkerMesh(slot,pos){
   const old=state.markerMeshes.find(m=>m.userData.arSlot===slot);
   if(old){old.position.copy(pos);return}
   const g=new THREE.SphereGeometry(currentHeight()*0.014,12,12);
   const mm=new THREE.Mesh(g,new THREE.MeshBasicMaterial({color:markColor(slot),depthTest:false}));
   mm.renderOrder=999;mm.userData.arSlot=slot;mm.position.copy(pos);
   scene.add(mm);state.markerMeshes.push(mm);
 }
 function clearMarkers(){
   for(const m of state.markerMeshes){scene.remove(m);m.geometry.dispose();m.material.dispose()}
   state.markerMeshes=[];state.points={};state.active=null;
 }
 function mirrorPoint(p){
   const b=new THREE.Box3().setFromObject(root);
   const cx=(b.min.x+b.max.x)/2;
   return new THREE.Vector3(2*cx-p.x,p.y,p.z);
 }
 function placeAt(clientX,clientY){
   if(!state.open||state.step!==4||!state.active)return false;
   const rect=canvas.getBoundingClientRect();
   const nd=new THREE.Vector2(((clientX-rect.left)/rect.width)*2-1,-((clientY-rect.top)/rect.height)*2+1);
   state.raycaster.setFromCamera(nd,camera);
   const hits=state.raycaster.intersectObjects(meshList,false);
   if(!hits.length){msg('Tap tepat pada permukaan model');return true}
   const p=hits[0].point.clone();
   const slot=state.active;
   state.points[slot]=p;addMarkerMesh(slot,p);
   if($('arSymV43').checked&&slot.endsWith('A')){
     const b=slot.slice(0,-1)+'B',mp=mirrorPoint(p);
     state.points[b]=mp;addMarkerMesh(b,mp);
   }
   state.active=slots().find(k=>!state.points[k])||null;
   renderMarkerList();
   return true;
 }
 // Selama layar marker, kamera dikunci: pointerdown diblok di fase capture supaya
 // OrbitControls tidak pernah memulai drag (kalau tidak, pointerup yang kita telan
 // meninggalkan OrbitControls "menggantung" dan sentuhan berikutnya memutar kamera).
 canvas.addEventListener('pointerdown',ev=>{
   if(state.open&&state.step===4){ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation()}
 },{capture:true});
 canvas.addEventListener('pointerup',ev=>{
   if(placeAt(ev.clientX,ev.clientY)){ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation()}
 },{capture:true});

 // ---- Step 5: build skeleton + auto weights ----
 // Model yang sudah ter-rig: lepaskan skeleton & skin lamanya secara UTUH-PULIH —
 // objek lama disimpan apa adanya supaya "Batalkan Rig" mengembalikannya persis.
 function stripExistingRig(){
   const saved={meshes:[],boneRoots:[]};
   const roots=[];
   root.traverse(o=>{if(o.isBone&&(!o.parent||!o.parent.isBone))roots.push(o)});
   for(const b of roots){saved.boneRoots.push({bone:b,parent:b.parent});if(b.parent)b.parent.remove(b)}
   for(let i=0;i<meshList.length;i++){
     const m=meshList[i];
     if(!m||!m.isSkinnedMesh)continue;
     const g=m.geometry.clone();
     g.deleteAttribute('skinIndex');g.deleteAttribute('skinWeight');
     const nm=new THREE.Mesh(g,m.material);
     nm.name=m.name;nm.castShadow=m.castShadow;nm.receiveShadow=m.receiveShadow;
     nm.position.copy(m.position);nm.quaternion.copy(m.quaternion);nm.scale.copy(m.scale);
     m.parent.add(nm);
     saved.meshes.push({old:m,parent:m.parent,replacement:nm,index:i});
     m.parent.remove(m);
     meshList[i]=nm;
   }
   root.updateMatrixWorld(true);
   return saved;
 }
 function restoreStrippedRig(){
   const sv=state.stripped;if(!sv)return;
   for(const e of sv.meshes){
     if(e.replacement.parent)e.replacement.parent.remove(e.replacement);
     e.parent.add(e.old);
     if(e.index>=0)meshList[e.index]=e.old;
   }
   for(const r of sv.boneRoots){if(r.parent)r.parent.add(r.bone)}
   root.updateMatrixWorld(true);
   state.stripped=null;
 }
 function lerpV(a,b,t){return new THREE.Vector3().lerpVectors(a,b,t)}
 function buildBoneWorldMap(){
   const P=state.points;
   const chin=P.chin,groin=P.groin;
   const H=chin.clone().sub(groin).length()||1;
   const m={};
   m.Hips=groin.clone();
   m.Spine=lerpV(groin,chin,0.28);
   m.Chest=lerpV(groin,chin,0.55);
   m.Neck=lerpV(groin,chin,0.85);
   m.Head=chin.clone();
   for(const side of ['A','B']){
     m['Shoulder'+side]=P['shoulder'+side].clone();
     m['Elbow'+side]=P['elbow'+side].clone();
     m['Wrist'+side]=P['wrist'+side].clone();
     m['UpLeg'+side]=new THREE.Vector3(P['knee'+side].x,groin.y-H*0.03,P['knee'+side].z);
     m['Knee'+side]=P['knee'+side].clone();
     m['Ankle'+side]=P['ankle'+side].clone();
   }
   return m;
 }
 const TOPO=[
   ['Hips',null],['Spine','Hips'],['Chest','Spine'],['Neck','Chest'],['Head','Neck'],
   ['ShoulderA','Chest'],['ElbowA','ShoulderA'],['WristA','ElbowA'],
   ['ShoulderB','Chest'],['ElbowB','ShoulderB'],['WristB','ElbowB'],
   ['UpLegA','Hips'],['KneeA','UpLegA'],['AnkleA','KneeA'],
   ['UpLegB','Hips'],['KneeB','UpLegB'],['AnkleB','KneeB'],
 ];
 function buildSkeleton(){
   const wm=buildBoneWorldMap();
   root.updateMatrixWorld(true);
   const toLocal=v=>root.worldToLocal(v.clone());
   const bones={},list=[];
   for(const [name,parent] of TOPO){
     const b=new THREE.Bone();b.name='AR_'+name;
     const lp=toLocal(wm[name]);
     if(parent){const pl=toLocal(wm[parent]);b.position.copy(lp.sub(pl));bones[parent].add(b)}
     else b.position.copy(lp);
     bones[name]=b;list.push(b);
   }
   root.add(bones.Hips);
   root.updateMatrixWorld(true);
   return {bones,list,world:wm};
 }
 function boneSegments(sk){
   const segs=[];
   const child={};for(const [n,p] of TOPO)if(p&&!child[p])child[p]=n;
   for(const [name] of TOPO){
     const a=sk.world[name];
     let b;
     if(child[name])b=sk.world[child[name]];
     else{
       const par=TOPO.find(t=>t[0]===name)[1];
       const dir=a.clone().sub(sk.world[par]).normalize();
       b=a.clone().add(dir.multiplyScalar(a.distanceTo(sk.world[par])*0.5));
     }
     segs.push({index:sk.list.findIndex(x=>x.name==='AR_'+name),a,b});
   }
   return segs;
 }
 function distToSeg(p,a,b){
   const ab=b.clone().sub(a),t=Math.max(0,Math.min(1,p.clone().sub(a).dot(ab)/Math.max(1e-9,ab.lengthSq())));
   return p.distanceTo(a.clone().add(ab.multiplyScalar(t)));
 }
 async function runAutoRig(){
   show(5);
   if(state.hadRig&&!state.stripped)state.stripped=stripExistingRig();
   const k=parseFloat($('arSmooth').value)||4;
   const sk=buildSkeleton();
   const segs=boneSegments(sk);
   const skeleton=new THREE.Skeleton(sk.list);
   const originals=[];
   const targets=meshList.slice();
   const total=targets.reduce((n,m)=>n+(m.geometry?.getAttribute('position')?.count||0),0)||1;
   let doneV=0;
   const setP=pct=>{$('arPBarV43').style.width=pct+'%';$('arPTextV43').textContent='Creating your rig… '+pct+'%'};
   for(let mi=0;mi<targets.length;mi++){
     const mesh=targets[mi];
     const geo=mesh.geometry,pos=geo.getAttribute('position');
     if(!pos)continue;
     mesh.updateMatrixWorld(true);
     const n=pos.count;
     const si=new Uint16Array(n*4),sw=new Float32Array(n*4);
     const v=new THREE.Vector3();
     const meshBase=doneV;
     let i=0;
     while(i<n){
       const end=Math.min(n,i+1500);
       for(;i<end;i++){
         v.fromBufferAttribute(pos,i).applyMatrix4(mesh.matrixWorld);
         let best=[];
         for(const s of segs){
           const d=distToSeg(v,s.a,s.b);
           best.push([d,s.index]);
         }
         best.sort((x,y)=>x[0]-y[0]);best=best.slice(0,4);
         let sum=0;const ws=best.map(([d])=>{const w=1/Math.pow(d+1e-6,k);sum+=w;return w});
         for(let j=0;j<4;j++){si[i*4+j]=best[j][1];sw[i*4+j]=ws[j]/sum}
       }
       doneV=Math.min(total,meshBase+i);
       setP(Math.round((doneV/total)*100));
       await new Promise(r=>setTimeout(r,0));
     }
     geo.setAttribute('skinIndex',new THREE.Uint16BufferAttribute(si,4));
     geo.setAttribute('skinWeight',new THREE.Float32BufferAttribute(sw,4));
     const smesh=new THREE.SkinnedMesh(geo,mesh.material);
     smesh.name=mesh.name;smesh.castShadow=mesh.castShadow;smesh.receiveShadow=mesh.receiveShadow;
     smesh.position.copy(mesh.position);smesh.quaternion.copy(mesh.quaternion);smesh.scale.copy(mesh.scale);
     smesh.frustumCulled=false;
     mesh.parent.add(smesh);
     originals.push({mesh,parent:mesh.parent,smesh,index:meshList.indexOf(mesh)});
     mesh.parent.remove(mesh);
     if(originals[originals.length-1].index>=0)meshList[originals[originals.length-1].index]=smesh;
     smesh.updateMatrixWorld(true);
     smesh.bind(skeleton,smesh.matrixWorld);
   }
   setP(100);
   state.rigged={skeleton,sk,originals};
   state.helper=new THREE.SkeletonHelper(root);
   scene.add(state.helper);
   clearMarkerVisualOnly();
   $('arResultNoteV43').textContent='Rig selesai: '+sk.list.length+' tulang, '+targets.length+' mesh di-skin, '+total.toLocaleString()+' vertex.';
   show(6);
   msg('Auto Rig selesai — coba Tes Gerak');
 }
 function clearMarkerVisualOnly(){
   for(const m of state.markerMeshes){scene.remove(m);m.geometry.dispose();m.material.dispose()}
   state.markerMeshes=[];
 }
 function undoRig(){
   const r=state.rigged;if(!r)return;
   for(const o of r.originals){
     if(o.smesh.parent)o.smesh.parent.remove(o.smesh);
     o.parent.add(o.mesh);
     if(o.index>=0)meshList[o.index]=o.mesh;
     o.mesh.geometry.deleteAttribute('skinIndex');
     o.mesh.geometry.deleteAttribute('skinWeight');
   }
   if(r.sk.bones.Hips.parent)r.sk.bones.Hips.parent.remove(r.sk.bones.Hips);
   if(state.helper){scene.remove(state.helper);state.helper=null}
   state.rigged=null;
   restoreStrippedRig();
   msg('Rig dibatalkan — model kembali seperti semula');
   show(4);renderMarkerList();
   for(const slot of Object.keys(state.points))addMarkerMesh(slot,state.points[slot]);
 }
 let wiggling=false;
 function wiggle(){
   const r=state.rigged;if(!r||wiggling)return;
   const bone=r.sk.bones.ShoulderA||r.sk.list[5];
   const orig=bone.quaternion.clone();
   const t0=performance.now();wiggling=true;
   (function anim(){
     const t=(performance.now()-t0)/1200;
     if(t>=1){bone.quaternion.copy(orig);wiggling=false;return}
     bone.quaternion.copy(orig);
     bone.rotateZ(Math.sin(t*Math.PI*4)*0.5);
     requestAnimationFrame(anim);
   })();
 }

 $('arNext2V43').onclick=()=>{enterStep3();show(3)};
 $('arBack3V43').onclick=()=>show(2);
 $('arNext3V43').onclick=()=>{show(4);renderMarkerList();msg('Pasang marker: tap model pada posisi '+MARKS[0].label)};
 $('arBack4V43').onclick=()=>show(3);
 $('arConfirmV43').onclick=()=>runAutoRig();
 $('arSmooth').oninput=()=>$('arSmoothVal').textContent=$('arSmooth').value;
 $('arUndoRigV43').onclick=undoRig;
 $('arWiggleV43').onclick=wiggle;
 $('arDoneV43').onclick=()=>{closeWiz();msg('Model ter-rig — lanjut Export atau rapikan di mode Skeleton')};

 // bbox dunia model & proyeksi titik dunia (dipakai hint marker & verifikasi)
 state.modelBox=()=>{
   if(!root)return null;
   root.updateMatrixWorld(true);
   const b=new THREE.Box3().setFromObject(root);
   return {min:{x:b.min.x,y:b.min.y,z:b.min.z},max:{x:b.max.x,y:b.max.y,z:b.max.z}};
 };
 state.screenOfWorld=(x,y,z)=>{
   const v=new THREE.Vector3(x,y,z).project(camera);
   const r=canvas.getBoundingClientRect();
   return {x:r.left+(v.x*0.5+0.5)*r.width,y:r.top+(-v.y*0.5+0.5)*r.height};
 };
 // proyeksi titik lokal-model ke koordinat layar (dipakai hint marker & verifikasi)
 state.screenOf=(x,y,z)=>{
   if(!root)return null;
   root.updateMatrixWorld(true);
   const v=new THREE.Vector3(x,y,z).applyMatrix4(root.matrixWorld).project(camera);
   const r=canvas.getBoundingClientRect();
   return {x:r.left+(v.x*0.5+0.5)*r.width,y:r.top+(-v.y*0.5+0.5)*r.height};
 };
 // AUTORIG_HANDOFF_RECEIVE_V43 — ambil titipan model dari mesin Auto (slot sekali-pakai,
 // dihapus begitu dibaca; kedaluwarsa 2 menit). Jalur data lewat storage, bukan runtime.
 (async function(){
   try{
     const rec=await new Promise(res=>{
       const rq=indexedDB.open('DF3D_MACHINE_HANDOFF',1);
       rq.onupgradeneeded=()=>rq.result.createObjectStore('slot');
       rq.onerror=()=>res(null);
       rq.onsuccess=()=>{
         const db=rq.result,tx=db.transaction('slot','readwrite'),st=tx.objectStore('slot');
         const g=st.get('autorig');
         g.onsuccess=()=>{const v=g.result||null;st.delete('autorig');tx.oncomplete=()=>{db.close();res(v)}};
         g.onerror=()=>{db.close();res(null)};
       };
     });
     if(!rec||!rec.buffer||(Date.now()-(rec.time||0))>120000)return;
     const url=URL.createObjectURL(new Blob([rec.buffer],{type:'model/gltf-binary'}));
     try{
       const g=await new Promise((res,rej)=>new GLTFLoader().load(url,res,undefined,rej));
       registerModel(g.scene,rec.name||'Model dari Auto',g.animations||[]);
       if(typeof registerPrimaryLayer==='function'){try{registerPrimaryLayer()}catch(_){ }}
       go('editorScreen');
       msg('Model dibawa dari mesin Auto — tekan ⚡ Rig untuk mulai');
     }finally{URL.revokeObjectURL(url)}
   }catch(e){console.warn('Handoff receive gagal',e)}
 })();

 window.__autoRigStateV43=state;   // dipakai verifikasi build/e2e, bukan jembatan antar mesin
})();
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('module script end missing')
s=s[:idx]+js+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Auto Rig engine v43: wizard + marker skeleton + chunked auto weights')
