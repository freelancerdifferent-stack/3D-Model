from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist')
s=p.read_text(encoding='utf-8')
if 'ANIM_LIBRARY_V52' in s:
    print('Animation library v52 already applied'); raise SystemExit(0)
if 'AUTO_RIG_PORTAL_V41' not in s: raise SystemExit('portal v41 must run first')
if not Path('app/src/main/assets/anim_library.glb').exists(): print('PERINGATAN: anim_library.glb tidak ada - tombol Animation akan gagal memuat library saat runtime')

# Tombol "Animation" di bawah tombol Auto Rig pada rail mesin Auto. Klik ->
# panel library sample animasi (Running/Walking dari rig biped referensi).
# Klip diterapkan lewat retarget-by-name: nama+hierarki tulang hasil Auto Rig
# identik dengan rig referensi, jadi keyframe-nya bisa dipetakan; karena rest
# pose kedua rig berbeda (referensi punya orientasi rest per tulang, hasil
# Auto Rig rest-nya identitas), tiap keyframe rotasi dikoreksi
# q' = inv(Qtp)*Qp*q*inv(Qb)*Qtb (Q* = rotasi dunia rest) sehingga rotasi
# DUNIA-nya sama; posisi hanya dipakai untuk Hips, diskala ke tinggi model.
css=r'''
/* ANIM_LIBRARY_V52 */
.anim-lib-btn-v52{margin-top:10px;min-height:58px;border:0;border-radius:10px;background:transparent;color:#ffb84d;font-size:10px;flex:none}
.anim-lib-btn-v52 b{display:block;font-size:24px;line-height:24px;margin-bottom:5px}
.anim-lib-btn-v52:active{background:#2a2210;box-shadow:0 0 0 1px #ffb84d66 inset!important}
.anim-lib-panel-v52{position:fixed;left:0;right:0;bottom:0;z-index:60;background:#141a22;border-top:1px solid #2c3a4d;border-radius:16px 16px 0 0;padding:14px 16px 20px;box-shadow:0 -12px 30px #000a}
.anim-lib-panel-v52 h3{margin:0 0 4px;font-size:16px;color:#ffb84d}
.anim-lib-panel-v52 p{margin:0 0 12px;font-size:12px;color:#9db2c9;line-height:1.5}
.anim-lib-list-v52{display:flex;flex-direction:column;gap:8px}
.anim-lib-item-v52{display:flex;align-items:center;gap:10px;padding:12px 14px;border:1px solid #2c3a4d;border-radius:10px;background:#1b2430;color:#e8f1fb;font-size:14px;text-align:left}
.anim-lib-item-v52:disabled{opacity:.5}
.anim-lib-item-v52 b{font-size:20px}
.anim-lib-close-v52{margin-top:12px;width:100%;padding:11px;border:0;border-radius:10px;background:#243141;color:#cfe0f2;font-size:14px}
'''
if '</style>' not in s: raise SystemExit('style end missing')
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// ANIM_LIBRARY_V52
(function(){
  const rail=document.querySelector('#editorScreen .toolrail');
  const portal=document.getElementById('autoRigPortalV41');
  if(!rail||!portal||document.getElementById('animLibBtnV52'))return;
  const btn=document.createElement('button');btn.type='button';btn.id='animLibBtnV52';
  btn.className='object-extra-tool anim-lib-btn-v52';btn.innerHTML='<b>🎮</b>Animation';
  portal.insertAdjacentElement('afterend',btn);
  const say=t=>{if(typeof msg==='function')msg(t);else if(typeof toast==='function')toast(t)};
  let panel=null,libPromise=null;

  function loadLib(){
    if(libPromise)return libPromise;
    libPromise=fetch('anim_library.glb').then(r=>{if(!r.ok)throw new Error('anim_library.glb '+r.status);return r.arrayBuffer()})
      .then(buf=>new Promise((ok,err)=>new GLTFLoader().parse(buf,'',ok,err)))
      .then(g=>{g.scene.updateMatrixWorld(true);return {scene:g.scene,clips:g.animations||[]}})
      .catch(e=>{libPromise=null;throw e});
    return libPromise;
  }

  function captureRest(bones){
    if(root.userData.animRestV52)return root.userData.animRestV52;
    root.updateMatrixWorld(true);
    const rest={};
    for(const k in bones){const b=bones[k];rest[k]={p:b.position.clone(),
      wq:b.getWorldQuaternion(new THREE.Quaternion()),wp:b.getWorldPosition(new THREE.Vector3())}}
    const bb=new THREE.Box3().setFromObject(root);
    root.userData.animRestV52={rest,groundY:bb.min.y,
      rootWQ:root.getWorldQuaternion(new THREE.Quaternion()),rootWS:root.getWorldScale(new THREE.Vector3())};
    return root.userData.animRestV52;
  }

  function retargetClip(lib,clip,bones,R){
    const refNodes={};lib.scene.traverse(o=>{if(o.name)refNodes[o.name]=o});
    const tracks=[];const q=new THREE.Quaternion();const v=new THREE.Vector3();
    for(const tr of clip.tracks){
      const dot=tr.name.lastIndexOf('.');
      const nodeName=tr.name.slice(0,dot).split('/').pop();
      const prop=tr.name.slice(dot+1);
      const rn=refNodes[nodeName],tb=bones[nodeName];
      if(!rn||!tb)continue;
      if(prop==='quaternion'){
        const Qp=rn.parent.getWorldQuaternion(new THREE.Quaternion());
        const QbI=rn.getWorldQuaternion(new THREE.Quaternion()).invert();
        const tqp=(tb.parent&&tb.parent.isBone&&R.rest[tb.parent.name])?R.rest[tb.parent.name].wq:R.rootWQ;
        const pre=tqp.clone().invert().multiply(Qp);
        const post=QbI.clone().multiply(R.rest[nodeName].wq);
        const vals=new Float32Array(tr.values.length);
        for(let i=0;i<tr.values.length;i+=4){
          q.fromArray(tr.values,i);
          q.copy(pre.clone().multiply(q).multiply(post)).normalize();
          q.toArray(vals,i);
        }
        tracks.push(new THREE.QuaternionKeyframeTrack(nodeName+'.quaternion',Array.from(tr.times),Array.from(vals)));
      }else if(prop==='position'&&nodeName==='Hips'){
        const pm=rn.parent.matrixWorld;
        const refRestW=rn.getWorldPosition(new THREE.Vector3());
        const tgtH=Math.max(R.rest.Hips.wp.y-R.groundY,1e-4);
        const ratio=tgtH/Math.max(refRestW.y,1e-4);
        const rq=R.rootWQ.clone().invert();
        const vals=new Float32Array(tr.values.length);
        for(let i=0;i<tr.values.length;i+=3){
          v.fromArray(tr.values,i).applyMatrix4(pm).sub(refRestW).multiplyScalar(ratio);
          v.applyQuaternion(rq).divide(R.rootWS).add(R.rest.Hips.p);
          v.toArray(vals,i);
        }
        tracks.push(new THREE.VectorKeyframeTrack('Hips.position',Array.from(tr.times),Array.from(vals)));
      }
    }
    if(!tracks.length)return null;
    return new THREE.AnimationClip(clip.name,clip.duration,tracks);
  }

  function applyClip(lib,srcClip){
    const bones={};root.traverse(o=>{if(o.isBone)bones[o.name]=o});
    if(!bones.Hips||!bones.LeftArm||!bones.RightUpLeg){
      say('Model belum punya rig yang cocok — jalankan Auto Rig dulu');return false}
    const R=captureRest(bones);
    const nc=retargetClip(lib,srcClip,bones,R);
    if(!nc){say('Tidak ada tulang yang cocok untuk animasi ini');return false}
    const dup=clips.findIndex(c=>c.name===nc.name&&c.userData?.animLibV52);
    nc.userData={animLibV52:true};
    if(!mixer)mixer=new THREE.AnimationMixer(root);
    const sel=document.getElementById('animSelect');
    let idx;
    if(dup>=0){clips[dup]=nc;idx=dup}
    else{
      if(!clips.length)sel.innerHTML='';
      clips.push(nc);idx=clips.length-1;
      const opt=document.createElement('option');opt.value=String(idx);
      opt.textContent=(idx+1)+'. '+(nc.name||'Animation');sel.appendChild(opt);
    }
    const cnt=document.getElementById('animClipCount');if(cnt)cnt.textContent=String(clips.length);
    sel.value=String(idx);
    selectAnimation(idx);
    playing=true;mixer.timeScale=1;
    const pb=document.getElementById('playBtn');if(pb)pb.textContent='❚❚';
    say('Animasi "'+(nc.name||'?')+'" diterapkan');
    return true;
  }

  function closePanel(){if(panel){panel.remove();panel=null}}
  function openPanel(){
    if(panel){closePanel();return}
    if(!root){say('Import model dulu sebelum memilih animasi');return}
    panel=document.createElement('div');panel.className='anim-lib-panel-v52';panel.id='animLibPanelV52';
    panel.innerHTML='<h3>🎮 Animation Library</h3><p>Sample animasi untuk rig hasil Auto Rig (retarget mengikuti nama tulang).</p><div class="anim-lib-list-v52" id="animLibListV52">Memuat library…</div><button type="button" class="anim-lib-close-v52" id="animLibCloseV52">Tutup</button>';
    document.body.appendChild(panel);
    panel.querySelector('#animLibCloseV52').addEventListener('click',closePanel);
    loadLib().then(lib=>{
      if(!panel)return;
      const list=panel.querySelector('#animLibListV52');list.innerHTML='';
      if(!lib.clips.length){list.textContent='Library kosong';return}
      for(const c of lib.clips){
        const it=document.createElement('button');it.type='button';it.className='anim-lib-item-v52';
        it.innerHTML='<b>🏃</b>'+(c.name||'Animation')+' • '+c.duration.toFixed(2)+'s';
        it.addEventListener('click',()=>{if(applyClip(lib,c))closePanel()});
        list.appendChild(it);
      }
    }).catch(e=>{
      console.error('ANIM_LIBRARY_V52',e);
      if(panel)panel.querySelector('#animLibListV52').textContent='Gagal memuat library: '+String(e?.message||e);
    });
  }
  btn.addEventListener('click',openPanel);
  window.__animLibV52Debug={clips:()=>clips,mixer:()=>mixer,active:()=>activeAction,lib:loadLib};
})();
'''
i=s.rfind('</script>')
if i<0: raise SystemExit('module script end missing')
s=s[:i]+js+'\n'+s[i:]
p.write_text(s,encoding='utf-8')
print('Animation library v52: tombol Animation + panel sample (Running/Walking) di mesin Auto')
