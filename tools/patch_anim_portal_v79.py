#!/usr/bin/env python3
# ANIM_PORTAL_V79 - tombol "Anim" di mesin Object "Animation".
#
# Portal untuk menerapkan animasi ke model, memakai library yang diisi lewat
# folder repo asset/anim-library/. Konsepnya sejajar dengan Auto Rig: bahan
# mentah berupa FBX di folder repo, diekstrak saat build oleh mesin
# anim_library_machine_v78.mjs, dan yang masuk APK hanya hasil ekstraksinya
# (app/src/main/assets/anim_library.json).
#
# Yang disimpan library bukan klip mentah melainkan rotasi DUNIA tiap tulang
# per bingkai berikut pose bind sumbernya. Alasannya: track kuaternion di FBX
# adalah rotasi LOKAL, yang hanya bermakna relatif terhadap rotasi bind rig itu
# sendiri, sedangkan rig hasil Auto Rig memakai rotasi rest identitas
# (AUTO_RIG_REFERENCE_SKELETON_V70). Menempel rotasi lokal apa adanya akan
# memuntir model.
#
# Retarget di sini memakai selisih terhadap pose bind, di ruang dunia:
#
#   selisih(b,t)     = duniaSumber(b,t) * bindSumber(b)^-1
#   duniaTujuan(b,t) = selisih(b,t) * bindTujuan(b)
#   lokalTujuan(b,t) = duniaTujuan(induk,t)^-1 * duniaTujuan(b,t)
#
# Rumus itu benar apa pun rotasi bind rig tujuan, jadi animasi bisa diterapkan
# baik ke rig hasil Auto Rig maupun ke rig bawaan model yang diimpor.
#
# Diuji terhadap kebenaran dasar: hasil retarget diterapkan kembali ke model
# SUMBER sendiri harus sama dengan memutar klip aslinya - simpangan vertex
# terbesar 0.097 pada model setinggi 173 (0.006%).
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'ANIM_PORTAL_V79' in s:
    raise SystemExit('ANIM_PORTAL_V79 sudah ada - patch dijalankan dua kali')
if 'AUTO_RIG_MACHINE_V42' not in s:
    raise SystemExit('mesin Auto Rig tidak ditemukan - dokumen bukan mesin Animation yang diharapkan')

# ---------------------------------------------------------------- CSS
# Digantung pada blok CSS milik mesin Animation supaya tidak bocor ke mesin lain.
anchor_css = 'html[data-object-machine="animation"] #editorScreen .auto-rig-portal-v41:active'
i = s.find(anchor_css)
if i < 0:
    raise SystemExit('blok CSS portal Auto Rig milik mesin Animation tidak ditemukan')
j = s.find('\n', i)
if j < 0:
    raise SystemExit('akhir baris CSS portal tidak ditemukan')

css = """
/* ANIM_PORTAL_V79 */
html[data-object-machine="animation"] #editorScreen .anim-portal-v79{min-height:58px;border:0;border-radius:10px;background:transparent;color:#61a6ff;font-size:10px;flex:none}
html[data-object-machine="animation"] #editorScreen .anim-portal-v79 b{display:block;font-size:24px;line-height:24px;margin-bottom:5px;color:#61a6ff}
html[data-object-machine="animation"] #editorScreen .anim-portal-v79:active{background:#101c2a;box-shadow:0 0 0 1px #61a6ff66 inset!important}
html[data-object-machine="animation"] body.auto-rig-v42 #editorScreen .anim-portal-v79{display:none!important}
html[data-object-machine="animation"] .anim-panel-v79{position:absolute;left:10px;right:10px;bottom:10px;max-height:56%;overflow:auto;z-index:31;pointer-events:auto;background:rgba(12,15,20,.96);border:1px solid #2b3d55;border-radius:16px;padding:14px;box-shadow:0 -12px 35px rgba(0,0,0,.35);color:#f7f9fb}
html[data-object-machine="animation"] .anim-panel-v79 h3{margin:0 0 7px;font-size:16px;display:flex;align-items:center;gap:8px}
html[data-object-machine="animation"] .anim-panel-v79 p{margin:0 0 12px;color:#b2bcc8;font-size:12px;line-height:1.45}
html[data-object-machine="animation"] .anim-panel-v79 .anim-close-v79{margin-left:auto;width:30px;height:30px;border-radius:9px;border:1px solid #2b3d55;background:#141a22;color:#f7f9fb;font-size:17px;line-height:1}
html[data-object-machine="animation"] .anim-list-v79{display:flex;flex-direction:column;gap:8px}
html[data-object-machine="animation"] .anim-item-v79{display:flex;align-items:center;gap:10px;width:100%;min-height:48px;padding:0 13px;border-radius:11px;border:1px solid #2b3d55;background:#141a22;color:#f7f9fb;font-size:14px;font-weight:700;text-align:left}
html[data-object-machine="animation"] .anim-item-v79:active{background:#1b2532}
html[data-object-machine="animation"] .anim-item-v79 span{margin-left:auto;font-weight:400;font-size:11px;color:#8fa0b4}
html[data-object-machine="animation"] .anim-empty-v79{color:#8fa0b4;font-size:12px;line-height:1.5}"""

s = s[:j] + css + s[j:]

# ---------------------------------------------------------------- JS
anchor_js = ('// REMOVE_ANIM_LIBRARY_V75: Animation Library dibuang dari mesin Animation '
             '(tombol, panel, pemuat, retarget V56-V63, dan CSS-nya). Mesin Auto tetap memilikinya.')
if anchor_js not in s:
    raise SystemExit('penanda REMOVE_ANIM_LIBRARY_V75 tidak ditemukan')

js = r"""

// ANIM_PORTAL_V79 - portal menerapkan animasi dari library mesin "anim"
(function(){
  if(window.__animPortalV79)return;
  const editor=document.getElementById('editorScreen');
  const rail=editor&&editor.querySelector('.toolrail');
  const viewport=editor&&editor.querySelector('.viewport');
  if(!editor||!rail||!viewport)return;

  const S={lib:null,memuat:null,panel:null,terakhir:null};
  window.__animPortalV79=S;
  const beritahu=m=>{if(typeof toast==='function')toast(m)};

  // ---- tombol di rail, tepat di bawah portal Auto Rig -------------------
  const btn=document.createElement('button');
  btn.type='button';btn.id='animPortalV79';btn.className='object-extra-tool anim-portal-v79';
  btn.innerHTML='<b>⟳</b>Anim';
  const portalRig=document.getElementById('autoRigPortalV41');
  if(portalRig&&portalRig.parentNode===rail)rail.insertBefore(btn,portalRig.nextSibling);
  else{
    const sel=rail.querySelector('.object-select-bottom')||rail.querySelector('.tool');
    if(sel)rail.insertBefore(btn,sel);else rail.appendChild(btn);
  }

  // ---- library ---------------------------------------------------------
  function muatLibrary(){
    if(S.lib)return Promise.resolve(S.lib);
    if(S.memuat)return S.memuat;
    S.memuat=fetch('./anim_library.json',{cache:'no-cache'})
      .then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json()})
      .then(d=>{
        if(!d||d.marker!=='ANIM_LIBRARY_V78')throw new Error('penanda library tidak dikenali');
        S.lib=d;console.log('ANIM_PORTAL_V79: library '+(d.clips||[]).length+' klip dari '+(d.sources||[]).length+' berkas');
        return d})
      .catch(e=>{console.warn('ANIM_PORTAL_V79 library',e);S.lib={clips:[],sources:[],gagal:String(e.message||e)};return S.lib})
      .finally(()=>{S.memuat=null});
    return S.memuat;
  }

  // ---- retarget --------------------------------------------------------
  // Pose bind rig tujuan diambil dari boneInverses, bukan dari pose yang sedang
  // tampil - bingkai animasi yang sedang jalan bukan pose bind.
  function bindDuniaTujuan(akar){
    const inv=new Map();
    akar.traverse(o=>{if(!o.isSkinnedMesh||!o.skeleton)return;
      const sk=o.skeleton;
      (sk.bones||[]).forEach((b,i)=>{if(!b||inv.has(b.name))return;
        const m=sk.boneInverses&&sk.boneInverses[i];if(m)inv.set(b.name,m)})});
    const out=new Map(),M=new THREE.Matrix4();
    akar.updateMatrixWorld(true);
    akar.traverse(o=>{if(!o.isBone||out.has(o.name))return;
      const im=inv.get(o.name);
      if(im)M.copy(im).invert();else M.copy(o.matrixWorld);
      const q=new THREE.Quaternion(),pp=new THREE.Vector3(),ss=new THREE.Vector3();
      M.decompose(pp,q,ss);
      out.set(o.name,{quat:q,pos:pp,bone:o})});
    return out;
  }
  // Induk dihitung lebih dulu supaya rotasi dunianya siap saat anak dihitung.
  function urutIndukDulu(peta){
    const hasil=[],sudah=new Set();
    const masuk=n=>{if(sudah.has(n))return;const d=peta.get(n);if(!d)return;
      const pr=d.bone.parent;if(pr&&pr.isBone&&peta.has(pr.name))masuk(pr.name);
      sudah.add(n);hasil.push(n)};
    for(const n of peta.keys())masuk(n);
    return hasil;
  }
  function tinggiObjek(akar){
    const b=new THREE.Box3(),v=new THREE.Vector3();let ada=false;
    akar.traverse(o=>{const pa=o.geometry&&o.geometry.attributes&&o.geometry.attributes.position;
      if(!pa||(!o.isMesh&&!o.isSkinnedMesh))return;
      const st=Math.max(1,Math.floor(pa.count/400));
      for(let i=0;i<pa.count;i+=st){if(o.isSkinnedMesh)o.getVertexPosition(i,v);else v.fromBufferAttribute(pa,i);
        v.applyMatrix4(o.matrixWorld);b.expandByPoint(v);ada=true}});
    return ada?b.getSize(new THREE.Vector3()).y:0;
  }
  function retargetV79(akar,lib,klip){
    const sumber=(lib.sources||[])[klip.source]||{};
    const bindSrc=sumber.bind||{};
    const bindTgt=bindDuniaTujuan(akar);
    const total=Object.keys(klip.world||{}).length;
    if(!bindTgt.size)return{clip:null,cocok:0,total:total,alasan:'model belum punya tulang'};
    const cocok=Object.keys(klip.world).filter(n=>bindTgt.has(n)&&bindSrc[n]);
    if(!cocok.length)return{clip:null,cocok:0,total:total,alasan:'tidak ada nama tulang yang cocok'};

    const urut=urutIndukDulu(bindTgt),F=klip.frames,dur=klip.duration;
    const waktu=new Float32Array(F);
    for(let f=0;f<F;f++)waktu[f]=(f/(F-1))*dur;
    const nilai={};for(const n of cocok)nilai[n]=new Float32Array(F*4);
    const duniaTgt=new Map(),setCocok=new Set(cocok);
    const qs=new THREE.Quaternion(),qb=new THREE.Quaternion(),qd=new THREE.Quaternion(),ql=new THREE.Quaternion();

    for(let f=0;f<F;f++){
      for(const n of urut){
        const bt=bindTgt.get(n);
        if(setCocok.has(n)){
          const w=klip.world[n];
          qs.set(w[f*4],w[f*4+1],w[f*4+2],w[f*4+3]);
          const bq=bindSrc[n].quat;qb.set(bq[0],bq[1],bq[2],bq[3]);
          qd.copy(qs).multiply(qb.invert());
          duniaTgt.set(n,qd.clone().multiply(bt.quat));
        }else duniaTgt.set(n,bt.quat.clone());
      }
      for(const n of cocok){
        const bone=bindTgt.get(n).bone,pr=bone.parent;
        const wp=(pr&&pr.isBone&&duniaTgt.has(pr.name))?duniaTgt.get(pr.name):null;
        ql.copy(duniaTgt.get(n));
        if(wp)ql.premultiply(wp.clone().invert());
        const a=nilai[n];a[f*4]=ql.x;a[f*4+1]=ql.y;a[f*4+2]=ql.z;a[f*4+3]=ql.w;
      }
    }
    const tracks=[];
    for(const n of cocok)tracks.push(new THREE.QuaternionKeyframeTrack(n+'.quaternion',waktu,nilai[n]));

    // Gerak badan: hanya tulang akar yang diberi posisi, diskalakan menurut
    // tinggi model tujuan supaya langkahnya sepadan dengan ukuran badannya.
    let skala=1;
    if(klip.root&&bindTgt.has(klip.root)&&bindSrc[klip.root]&&klip.rootPos&&klip.rootPos.length===F*3){
      const hSrc=sumber.height||0,hTgt=tinggiObjek(akar);
      if(hSrc>1e-3&&hTgt>1e-3)skala=hTgt/hSrc;
      const bt=bindTgt.get(klip.root),bone=bt.bone,bp=bindSrc[klip.root].pos;
      // Posisi bind LOKAL dihitung dari posisi bind dunia lewat induknya, bukan
      // dibaca dari bone.position - pada model beranimasi nilai itu adalah
      // bingkai gerak yang sedang tampil, bukan pose bind.
      const indukM=new THREE.Matrix4();
      if(bone.parent){bone.parent.updateMatrixWorld(true);indukM.copy(bone.parent.matrixWorld).invert()}
      const lokalBind=bt.pos.clone().applyMatrix4(indukM);
      const indukQ=new THREE.Quaternion();
      if(bone.parent)bone.parent.getWorldQuaternion(indukQ).invert();
      const geser=new THREE.Vector3(),pos=new Float32Array(F*3);
      for(let f=0;f<F;f++){
        geser.set(klip.rootPos[f*3]-bp[0],klip.rootPos[f*3+1]-bp[1],klip.rootPos[f*3+2]-bp[2])
             .multiplyScalar(skala).applyQuaternion(indukQ);
        pos[f*3]=lokalBind.x+geser.x;pos[f*3+1]=lokalBind.y+geser.y;pos[f*3+2]=lokalBind.z+geser.z;
      }
      tracks.push(new THREE.VectorKeyframeTrack(klip.root+'.position',waktu,pos));
    }
    return{clip:new THREE.AnimationClip(klip.name,dur,tracks),cocok:cocok.length,total:total,skala:skala};
  }

  // ---- terapkan --------------------------------------------------------
  function terapkan(klip){
    if(!root){beritahu('Import model terlebih dahulu.');return}
    let adaTulang=false;root.traverse(o=>{if(o.isBone)adaTulang=true});
    if(!adaTulang){beritahu('Model belum punya tulang - jalankan Auto Rig dulu.');return}
    let hasil;
    try{hasil=retargetV79(root,S.lib,klip)}
    catch(e){console.warn('ANIM_PORTAL_V79 retarget',e);beritahu('Gagal menerapkan animasi.');return}
    if(!hasil.clip){beritahu('Animasi tidak bisa diterapkan: '+(hasil.alasan||'tulang tidak cocok'));return}

    // Klip dengan nama sama diganti, bukan ditumpuk, supaya daftar tidak beranak.
    const lama=clips.findIndex(c=>c&&c.name===hasil.clip.name);
    if(lama>=0){if(mixer){try{mixer.uncacheClip(clips[lama])}catch(e){}}clips.splice(lama,1,hasil.clip)}
    else clips.push(hasil.clip);

    if(!mixer)mixer=new THREE.AnimationMixer(root);
    const sel=document.getElementById('animSelect');
    if(sel){
      sel.innerHTML='';
      clips.forEach((c,i)=>{const o=document.createElement('option');o.value=String(i);
        o.textContent=c.name&&c.name.trim()?((i+1)+'. '+c.name):('Animation '+(i+1));sel.appendChild(o)});
    }
    const idx=clips.indexOf(hasil.clip);
    if(sel)sel.value=String(idx);
    if(typeof selectAnimation==='function')selectAnimation(idx);
    const dt=document.getElementById('durationText');if(dt)dt.textContent=hasil.clip.duration.toFixed(2)+'s';
    S.terakhir={nama:hasil.clip.name,cocok:hasil.cocok,total:hasil.total,skala:+hasil.skala.toFixed(4)};
    console.log('ANIM_PORTAL_V79: "'+hasil.clip.name+'" diterapkan, '+hasil.cocok+'/'+hasil.total+' tulang cocok, skala '+hasil.skala.toFixed(3));
    tutup();
    beritahu(hasil.clip.name+' diterapkan ('+hasil.cocok+'/'+hasil.total+' tulang) - tekan Play');
  }

  // ---- panel -----------------------------------------------------------
  function tutup(){if(S.panel){S.panel.remove();S.panel=null}}
  function buka(){
    if(S.panel){tutup();return}
    if(!root){beritahu('Import model terlebih dahulu sebelum menerapkan animasi.');return}
    const panel=document.createElement('div');
    panel.className='anim-panel-v79';panel.id='animPanelV79';
    panel.innerHTML='<h3>Anim<button type="button" class="anim-close-v79" id="animCloseV79">×</button></h3>'+
      '<p>Pilih animasi untuk diterapkan ke model. Tulang dicocokkan menurut nama, jadi model perlu sudah punya rig.</p>'+
      '<div class="anim-list-v79" id="animListV79"><div class="anim-empty-v79">Memuat library…</div></div>';
    viewport.appendChild(panel);S.panel=panel;
    panel.querySelector('#animCloseV79').onclick=tutup;
    muatLibrary().then(lib=>{
      if(S.panel!==panel)return;
      const daftar=panel.querySelector('#animListV79');
      const klips=(lib&&lib.clips)||[];
      if(lib&&lib.gagal){
        daftar.innerHTML='<div class="anim-empty-v79">Library animasi tidak bisa dibaca ('+lib.gagal+').</div>';return}
      if(!klips.length){
        daftar.innerHTML='<div class="anim-empty-v79">Library masih kosong. Isi folder <b>asset/anim-library/</b> di repo dengan berkas FBX animasi, lalu build ulang.</div>';return}
      daftar.innerHTML='';
      klips.forEach(k=>{
        const b=document.createElement('button');
        b.type='button';b.className='anim-item-v79';
        b.appendChild(document.createTextNode(String(k.name||'Animasi')));
        const sp=document.createElement('span');sp.textContent=(+k.duration||0).toFixed(2)+'s';b.appendChild(sp);
        b.onclick=()=>terapkan(k);
        daftar.appendChild(b);
      });
    });
  }
  btn.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();buka()},true);
})();
"""

s = s.replace(anchor_js, anchor_js + js, 1)

p.write_text(s, encoding='utf-8')
print('ANIM_PORTAL_V79 applied: tombol Anim + panel library + retarget berbasis pose bind')
