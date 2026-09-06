#!/usr/bin/env python3
# EXPORT_ANIM_ONLY_V81 - export berisi animasi saja, tanpa mesh dan texture.
#
# Untuk dipakai di game engine, berkas berisi model lengkap itu berat padahal
# yang dibutuhkan hanya geraknya. Mesin ini menulis GLB yang isinya cuma susunan
# tulang berikut klip animasinya; engine memasangkannya ke rig yang nama
# tulangnya sama.
#
# Mesin Export yang sudah ada (EXPORT_ALL_V13) tidak bisa dipakai untuk ini dan
# tidak disentuh sama sekali:
#   - exportSelective() berhenti dengan pesan "Aktifkan All Model atau All Mesh"
#     kalau keduanya dimatikan, jadi animasi-saja memang tidak dilayani;
#   - mematikan All Mesh hanya menyetel visible=false, sedangkan pemanggilan
#     exporternya memakai onlyVisible:false - mesh tetap ikut tertulis dan
#     ukuran berkas tidak berkurang.
#
# Karena itu jalur ini berdiri sendiri: tombolnya sendiri, penyusun adegannya
# sendiri. Yang disalin ke adegan export hanya simpul yang merupakan tulang atau
# yang punya keturunan tulang; mesh, material, dan texture tidak ikut sama sekali,
# bukan disembunyikan.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'EXPORT_ANIM_ONLY_V81' in s:
    raise SystemExit('EXPORT_ANIM_ONLY_V81 sudah ada - patch dijalankan dua kali')
if 'EXPORT_ALL_V13' not in s:
    raise SystemExit('mesin Export v13 tidak ditemukan - dokumen bukan yang diharapkan')

# ---------------------------------------------------------------- CSS
anchor_css = 'html[data-object-machine="animation"] .anim-empty-v79{'
i = s.find(anchor_css)
if i < 0:
    raise SystemExit('blok CSS portal Anim tidak ditemukan')
j = s.find('\n', i)

css = """
/* EXPORT_ANIM_ONLY_V81 */
html[data-object-machine="animation"] #exportAnimOnlySectionV81 p{margin:0 0 12px;color:#8fa0b4;font-size:12px;line-height:1.5}
html[data-object-machine="animation"] #exportAnimOnlyV81{width:100%;height:52px;border-radius:12px;border:1px solid #2b3d55;background:#141a22;color:#61a6ff;font-size:15px;font-weight:700}
html[data-object-machine="animation"] #exportAnimOnlyV81:active{background:#1b2532}
html[data-object-machine="animation"] #exportAnimOnlyV81[disabled]{opacity:.45}"""
s = s[:j] + css + s[j:]

# ---------------------------------------------------------------- JS
anchor_js = "// ANIM_PORTAL_V79 - portal menerapkan animasi dari library mesin \"anim\""
if anchor_js not in s:
    raise SystemExit('penanda portal Anim v79 tidak ditemukan')

js = r"""// EXPORT_ANIM_ONLY_V81 - simpan animasi saja, tanpa mesh dan texture
(function(){
  if(window.__exportAnimOnlyV81)return;
  const layar=document.getElementById('exportScreen');
  const tombolLama=document.getElementById('exportBtn');
  if(!layar||!tombolLama)return;
  const status=document.getElementById('exportStatus');
  window.__exportAnimOnlyV81={};

  const sec=document.createElement('div');
  sec.className='section';sec.id='exportAnimOnlySectionV81';
  sec.innerHTML='<h3>Export Animasi Saja</h3><p>Hanya susunan tulang dan klip animasinya - tanpa mesh, material, dan texture. Berkasnya jauh lebih ringan; game engine memasangkannya ke rig yang nama tulangnya sama.</p>';
  const btn=document.createElement('button');
  btn.type='button';btn.className='primary';btn.id='exportAnimOnlyV81';
  btn.textContent='Save / Export Animasi (GLB)';
  sec.appendChild(btn);
  tombolLama.parentNode.insertBefore(sec,tombolLama.nextSibling);

  // Simpul yang disalin hanya tulang dan simpul yang punya keturunan tulang.
  // Mesh tidak disembunyikan melainkan memang tidak ikut disalin, jadi tidak ada
  // geometry maupun texture yang tertulis ke berkas.
  function susunKerangkaV81(sumber){
    const perlu=new Set();
    (function tandai(n){
      let punya=!!n.isBone;
      for(const c of n.children)if(tandai(c))punya=true;
      if(punya)perlu.add(n);
      return punya;
    })(sumber);
    if(!perlu.has(sumber))return null;
    const salin=n=>{
      const baru=n.isBone?new THREE.Bone():new THREE.Object3D();
      baru.name=n.name;
      baru.position.copy(n.position);baru.quaternion.copy(n.quaternion);baru.scale.copy(n.scale);
      for(const c of n.children)if(perlu.has(c))baru.add(salin(c));
      return baru;
    };
    return salin(sumber);
  }
  function hitungTulangV81(n){let j=0;n.traverse(o=>{if(o.isBone)j++});return j}

  btn.onclick=async()=>{
    if(typeof root==='undefined'||!root){if(typeof msg==='function')msg('Belum ada model untuk diexport');return}
    const daftar=(typeof clips!=='undefined'&&Array.isArray(clips))?clips.filter(Boolean):[];
    if(!daftar.length){if(typeof msg==='function')msg('Model belum punya animasi - terapkan lewat tombol Anim dulu');return}
    const kerangka=susunKerangkaV81(root);
    if(!kerangka||!hitungTulangV81(kerangka)){if(typeof msg==='function')msg('Model belum punya tulang - jalankan Auto Rig dulu');return}
    btn.disabled=true;
    if(status)status.textContent='Membuat GLB animasi...';
    try{
      const adegan=new THREE.Scene();adegan.add(kerangka);
      // trs:true - setiap simpul di sini memang dianimasikan lewat TRS, bukan matriks.
      const out=await new GLTFExporter().parseAsync(adegan,{binary:true,trs:true,onlyVisible:false,animations:daftar});
      const blob=new Blob([out],{type:'model/gltf-binary'});
      const nama=((typeof currentFileName!=='undefined'&&currentFileName)?currentFileName.replace(/\.[^.]+$/,''):'model')+'_anim.glb';
      downloadBlob(blob,nama);
      const kb=(blob.size/1024).toFixed(0);
      const tulang=hitungTulangV81(kerangka);
      if(status)status.textContent='Selesai • '+daftar.length+' klip • '+tulang+' tulang • '+kb+' KB • tanpa mesh/texture';
      console.log('EXPORT_ANIM_ONLY_V81: '+nama+' '+kb+' KB, '+daftar.length+' klip, '+tulang+' tulang');
      window.__exportAnimOnlyV81.terakhir={nama:nama,byte:blob.size,klip:daftar.length,tulang:tulang};
      if(typeof msg==='function')msg('Animasi diexport ('+kb+' KB)');
    }catch(e){
      console.error('EXPORT_ANIM_ONLY_V81',e);
      if(status)status.textContent='Export animasi gagal: '+e.message;
      if(typeof msg==='function')msg('Export animasi gagal');
    }finally{btn.disabled=false}
  };
})();


"""

s = s.replace(anchor_js, js + anchor_js, 1)

# Penghitung "Animation Clips" di layar Export hanya disetel saat model dimuat,
# jadi setelah animasi diterapkan lewat tombol Anim angkanya masih menunjukkan
# jumlah klip bawaan berkas. Disegarkan di tempat klip memang berubah.
lama_hitung = ("    const dt=document.getElementById('durationText');"
               "if(dt)dt.textContent=hasil.clip.duration.toFixed(2)+'s';")
if lama_hitung not in s:
    raise SystemExit('baris durationText pada penerapan animasi tidak ditemukan')
baru_hitung = (lama_hitung +
               "\n    const jk=document.getElementById('animClipCount');"
               "if(jk)jk.textContent=String(clips.length);")
s = s.replace(lama_hitung, baru_hitung, 1)

p.write_text(s, encoding='utf-8')
print('EXPORT_ANIM_ONLY_V81 applied: tombol export animasi saja (tulang + klip, tanpa mesh/texture)')
