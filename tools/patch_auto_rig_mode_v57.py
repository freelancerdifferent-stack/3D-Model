from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_MODE_V57' in s:
    print('Auto Rig mode v57 already applied'); raise SystemExit(0)
if 'ANIM_LIB_SMARTMAP_V56' not in s: raise SystemExit('v56 must run first')

# Saat rig terdeteksi & dikenali, layar 1 wizard kini menawarkan DUA mode:
#   1. Sejajarkan (v54, default) - rig lama utuh, tulang inti dirapikan.
#   2. Ganti rig standar 24 tulang - semua tulang lama dihapus dan diganti
#      skeleton referensi, TETAPI skin weights asli tidak dibuang: bobot tiap
#      vertex DIPETAKAN ke tulang baru lewat peran tulang lamanya (jari &
#      twist ikut leluhur intinya: jari->Hand, thigh_twist->UpLeg), sehingga
#      batas-batas weights buatan artis tetap dipakai, bukan tebakan jarak.
css=r'''
/* AUTO_RIG_MODE_V57 */
.arv57-modes{display:flex;flex-direction:column;gap:8px;margin:0 0 12px}
.arv57-mode{text-align:left;padding:10px 12px;border:1px solid #2c3a4d;border-radius:10px;background:#1b2430;color:#e8f1fb}
.arv57-mode b{display:block;font-size:14px;margin-bottom:3px}
.arv57-mode span{font-size:11.5px;color:#9db2c9;line-height:1.45}
.arv57-mode.sel{border-color:#a4f52a;box-shadow:0 0 0 1px #a4f52a66 inset}
'''
if '</style>' not in s: raise SystemExit('style end missing')
s=s.replace('</style>',css+'\n</style>',1)

old_open="    S.open=true;S.step=1;"
new_open="    S.rigModeV57='align';S.open=true;S.step=1;"
if old_open not in s: raise SystemExit('openRig anchor missing')
s=s.replace(old_open,new_open,1)

old_warn="""'<div class="arv42-warn50" style="border-color:#3f7a37;background:#12290f;color:#a8e78f">✔ Rig terdeteksi dan dikenali. Tulang inti akan DISEJAJARKAN ke marker — tulang lain (jari, twist, dll.) dan skin weights asli DIPERTAHANKAN.</div>'"""
new_warn="""'<div class="arv42-warn50" style="border-color:#3f7a37;background:#12290f;color:#a8e78f">✔ Rig terdeteksi dan dikenali — pilih mode:</div><div class="arv57-modes"><button type="button" id="arv57ModeAlign" class="arv57-mode'+(S.rigModeV57!=='rebuild'?' sel':'')+'"><b>📐 Sejajarkan rig lama</b><span>Semua tulang (jari, twist, dll.) dan skin weights asli dipertahankan; tulang inti dirapikan ke marker.</span></button><button type="button" id="arv57ModeRebuild" class="arv57-mode'+(S.rigModeV57==='rebuild'?' sel':'')+'"><b>🦴 Ganti rig standar 24 tulang</b><span>Semua tulang lama dihapus dan diganti skeleton standar — skin weights asli DIPETAKAN ke tulang baru. Cocok untuk library animasi dan export ringan.</span></button></div>'"""
if old_warn not in s: raise SystemExit('step1 green warn anchor missing')
s=s.replace(old_warn,new_warn,1)

old_wire="      wireNav(null,()=>step(2));"
new_wire="""      wireNav(null,()=>step(2));
      const mAV57=panel.querySelector('#arv57ModeAlign'),mBV57=panel.querySelector('#arv57ModeRebuild');
      if(mAV57&&mBV57){
        const selV57=md=>{S.rigModeV57=md;mAV57.classList.toggle('sel',md!=='rebuild');mBV57.classList.toggle('sel',md==='rebuild')};
        mAV57.addEventListener('click',()=>selV57('align'));
        mBV57.addEventListener('click',()=>selV57('rebuild'));
      }"""
if old_wire not in s: raise SystemExit('wireNav step1 anchor missing')
s=s.replace(old_wire,new_wire,1)

funcs=r'''  // AUTO_RIG_MODE_V57: ganti rig standar tapi weights asli dipetakan
  function rebuildRigKeepWeightsV57(map){
    root.updateMatrixWorld(true);
    const coreName=new Map();
    if(map.hips)coreName.set(map.hips,'Hips');
    const spN=['Spine02','Spine01','Spine'];
    map.spine.forEach((b,i)=>{const t=map.spine.length<=1?2:Math.round(i*(spN.length-1)/(map.spine.length-1));coreName.set(b,spN[t])});
    map.neck.forEach(b=>coreName.set(b,'neck'));
    if(map.head)coreName.set(map.head,'Head');
    const sideNames={L:{clav:'LeftShoulder',upperarm:'LeftArm',forearm:'LeftForeArm',hand:'LeftHand',thigh:'LeftUpLeg',calf:'LeftLeg',foot:'LeftFoot',toe:'LeftToeBase'},
                     R:{clav:'RightShoulder',upperarm:'RightArm',forearm:'RightForeArm',hand:'RightHand',thigh:'RightUpLeg',calf:'RightLeg',foot:'RightFoot',toe:'RightToeBase'}};
    for(const sk2 of ['L','R'])for(const role in sideNames[sk2]){const b=map.sided[role]&&map.sided[role][sk2];if(b)coreName.set(b,sideNames[sk2][role])}
    const nameOf=b=>{let n=b;while(n&&n.isBone){if(coreName.has(n))return coreName.get(n);n=n.parent}return 'Hips'};
    // bake pose tampil per-vertex + simpan tabel peran bone lama tiap mesh
    const olds=[];root.traverse(o=>{if(o.isSkinnedMesh)olds.push(o)});
    const jobs=[];const v=new THREE.Vector3();
    for(const m of olds){
      m.updateMatrixWorld(true);
      const g=m.geometry.clone();
      const pos=g.getAttribute('position');
      for(let i=0;i<pos.count;i++){m.getVertexPosition(i,v);v.applyMatrix4(m.matrixWorld);root.worldToLocal(v);pos.setXYZ(i,v.x,v.y,v.z)}
      pos.needsUpdate=true;g.computeVertexNormals();g.computeBoundingBox();g.computeBoundingSphere();
      jobs.push({g,material:m.material,name:m.name,cast:m.castShadow,recv:m.receiveShadow,
        table:m.skeleton.bones.map(b=>nameOf(b)),old:m});
    }
    // buang rig+mesh lama, bersihkan pemutar (klip lama menarget tulang lama)
    const boneRootsR=[];root.traverse(o=>{if(o.isBone&&(!o.parent||!o.parent.isBone))boneRootsR.push(o)});
    for(const j of jobs){j.li=(typeof meshList!=='undefined')?meshList.indexOf(j.old):-1;if(j.old.parent)j.old.parent.remove(j.old)}
    for(const b of boneRootsR){if(b.parent)b.parent.remove(b)}
    try{if(typeof mixer!=='undefined'&&mixer){mixer.stopAllAction();mixer.uncacheRoot(mixer.getRoot())}}catch(_){ }
    mixer=null;clips=[];activeAction=null;playing=false;activeClipIndex=0;
    const selR=document.getElementById('animSelect');if(selR)selR.innerHTML='<option value="">No Animation</option>';
    const cntR=document.getElementById('animClipCount');if(cntR)cntR.textContent='0';
    const durR=document.getElementById('durationText');if(durR)durR.textContent='0s';
    const pbR=document.getElementById('playBtn');if(pbR)pbR.textContent='▶';
    root.userData.animRestV52=null;
    root.updateMatrixWorld(true);
    // skeleton standar dari marker + weights lama yang dipetakan
    generateSkeleton();
    const idxOf={};S.bones.forEach((b,i)=>{idxOf[b.name]=i});
    let done=0;
    for(const j of jobs){
      const oldIdx=j.g.getAttribute('skinIndex'),oldW=j.g.getAttribute('skinWeight');
      const n=j.g.getAttribute('position').count;
      const ni=new Uint16Array(n*4),nw=new Float32Array(n*4);
      if(oldIdx&&oldW){
        const acc=new Map();
        for(let i=0;i<n;i++){
          acc.clear();
          for(let k=0;k<4;k++){
            const w=oldW.getComponent(i,k);if(w<=0)continue;
            const bi=idxOf[j.table[oldIdx.getComponent(i,k)]||'Hips'];
            if(bi===undefined)continue;
            acc.set(bi,(acc.get(bi)||0)+w);
          }
          const ent=[...acc.entries()].sort((a,c)=>c[1]-a[1]).slice(0,4);
          let sum=0;for(const e of ent)sum+=e[1];
          if(sum<=0){ni[i*4]=idxOf.Hips||0;nw[i*4]=1;continue}
          for(let k=0;k<ent.length;k++){ni[i*4+k]=ent[k][0];nw[i*4+k]=ent[k][1]/sum}
        }
      }else{for(let i=0;i<n;i++){ni[i*4]=idxOf.Hips||0;nw[i*4]=1}}
      j.g.setAttribute('skinIndex',new THREE.Uint16BufferAttribute(ni,4));
      j.g.setAttribute('skinWeight',new THREE.Float32BufferAttribute(nw,4));
      const sk=new THREE.SkinnedMesh(j.g,j.material);
      sk.name=j.name;sk.castShadow=j.cast;sk.receiveShadow=j.recv;sk.frustumCulled=false;sk.visible=true;
      root.add(sk);sk.updateMatrixWorld(true);
      sk.bind(S.skeleton,sk.matrixWorld);
      sk.normalizeSkinWeights();
      if(j.li>=0&&typeof meshList!=='undefined')meshList[j.li]=sk;
      done++;
    }
    S.skinned=done;S.rebuiltV57=true;
    window.__autoRigRebuildV57={meshes:done,bones:S.bones.length};
    return done;
  }

'''
anchor='  async function renderProcessingStep(){'
if anchor not in s: raise SystemExit('renderProcessingStep anchor missing')
s=s.replace(anchor,funcs+anchor,1)

old_run="S.alignedV54=false;const mapV54=hasOldRigV50()?mapCoreBonesV54():null;if(mapV54&&mapV54.ok){set(30);alignExistingRigV54(mapV54);set(70);await new Promise(r=>setTimeout(r,80))}else{"
new_run="S.alignedV54=false;S.rebuiltV57=false;const mapV54=hasOldRigV50()?mapCoreBonesV54():null;if(mapV54&&mapV54.ok&&S.rigModeV57==='rebuild'){set(22);rebuildRigKeepWeightsV57(mapV54);set(60);await new Promise(r=>setTimeout(r,80));await skinGeometry()}else if(mapV54&&mapV54.ok){set(30);alignExistingRigV54(mapV54);set(70);await new Promise(r=>setTimeout(r,80))}else{"
if old_run not in s: raise SystemExit('processing branch anchor missing')
s=s.replace(old_run,new_run,1)

old_res="'<h3>Rig Complete</h3><p>'+(S.alignedV54?'Tulang inti disejajarkan ke marker. Struktur rig, tulang tambahan, dan skin weights asli dipertahankan.':'Skeleton humanoid dibuat dari marker dan skin weights sudah dihitung untuk mesh yang belum memiliki skin.')+'</p><div"
new_res="'<h3>Rig Complete</h3><p>'+(S.alignedV54?'Tulang inti disejajarkan ke marker. Struktur rig, tulang tambahan, dan skin weights asli dipertahankan.':(S.rebuiltV57?'Rig lama diganti skeleton standar 24 tulang — skin weights asli dipetakan ke tulang baru.':'Skeleton humanoid dibuat dari marker dan skin weights sudah dihitung untuk mesh yang belum memiliki skin.'))+'</p><div"
if old_res not in s: raise SystemExit('result text anchor missing')
s=s.replace(old_res,new_res,1)

p.write_text(s,encoding='utf-8')
print('Auto Rig mode v57: pilihan Sejajarkan / Ganti rig standar dengan weights dipetakan')
