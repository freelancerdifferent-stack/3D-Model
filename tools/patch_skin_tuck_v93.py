#!/usr/bin/env python3
# SKIN_TUCK_V93 - "Rapikan Kulit": masukkan kulit yang tertutup baju ke dalam baju.
#
# Dilaporkan pengguna: pada model rakitannya, paha memperlihatkan serpihan
# hitam-putih berhamburan saat dilihat di preview.
#
# Terukur pada berkas itu (SK_NYX_BODY_FULL vs SK_NYX_SUIT, 400 titik kulit di
# daerah paha, POSE DIAM - bukan efek animasi):
#
#   kulit yang berada DI LUAR suit      83.8%
#   tonjolan median                     0.093 satuan
#   tonjolan p90                        0.88 satuan
#
# Jadi badannya memang lebih besar daripada pakaiannya. Model ini dibuat untuk
# mesin game yang menyembunyikan bagian badan yang tertutup baju; badannya tidak
# pernah dirancang agar muat di dalam.
#
# Menyembunyikan mesh badan bukan solusi - itu hanya membuang gejalanya. Menaikkan
# presisi kedalaman juga bukan: terbukti hanya membersihkan desir di tepinya,
# sedangkan tonjolan 0.88 satuan jauh di atas resolusi kedalaman mana pun.
#
# Arah yang dipakai: KULITNYA yang dimasukkan, bukan bajunya yang dibesarkan.
# Membesarkan baju mengubah siluet - pinggang menggembung, gesper dan tali korset
# ikut melar, dan di batas tempat baju bertemu kulit terbuka muncul undakan.
# Kulit yang tertutup baju tidak pernah terlihat, jadi mengecilkannya tidak
# mengubah apa pun di layar.
#
# Yang disentuh HANYA verteks yang benar-benar tertutup: sinar ditembakkan dari
# luar kulit menuju ke dalam, dan verteksnya diproses hanya bila mengenai
# permukaan pakaian yang menghadap keluar. Verteks yang tidak mengenai apa-apa -
# wajah, lengan, dada, betis - tidak disentuh sama sekali, sehingga tidak ada
# yang menciut dan tidak ada celah menganga di leher atau pergelangan.
#
# Dorongannya sebesar tonjolan + margin, bukan nilai tetap, supaya tiap verteks
# masuk secukupnya. Margin juga menyelamatkan verteks yang sudah di dalam tetapi
# terlalu rapat (di bawah resolusi kedalaman, tetap berdesir).
#
# Posisi asli disimpan, jadi bisa dikembalikan. Tombol yang sama berubah menjadi
# "Kembalikan Kulit" untuk mesh yang sudah dirapikan.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'SKIN_TUCK_V93' in s:
    raise SystemExit('SKIN_TUCK_V93 sudah ada - patch dijalankan dua kali')
if 'meshRenameSelectedBtn' not in s:
    raise SystemExit('bilah kelola mesh tidak ditemukan - urutan pipeline salah')

# ---------------------------------------------------------------- CSS
anchor_css = "#meshLayersScreen .mesh-action-btn{border:1px solid #34485e;background:#121d29;color:#dce7f3}\n"
if anchor_css not in s:
    raise SystemExit('CSS bilah kelola mesh tidak ditemukan')
css = """/* SKIN_TUCK_V93 */
#meshLayersScreen #meshTuckBtn{grid-column:1/-1;border:1px solid #2f6f52;background:#12291f;color:#d9f5e6}
#meshLayersScreen #meshTuckBtn.pulih{border-color:#6f5a2f;background:#292314;color:#f5ecd9}
"""
s = s.replace(anchor_css, anchor_css + css, 1)

# ---------------------------------------------------------------- markup
anchor_html = '        <button class="mesh-action-btn" id="meshRenameSelectedBtn">✎ Rename Selected</button>\n'
if anchor_html not in s:
    raise SystemExit('tombol Rename Selected tidak ditemukan')
html = '        <button class="mesh-action-btn" id="meshTuckBtn">⤵ Rapikan Kulit Tertutup</button>\n'
s = s.replace(anchor_html, anchor_html + html, 1)

# ---------------------------------------------------------------- JS
anchor_js = "function renderMeshLayers(){"
if anchor_js not in s:
    raise SystemExit('renderMeshLayers tidak ditemukan')

js = r"""// SKIN_TUCK_V93 - masukkan kulit yang tertutup pakaian ke dalam pakaiannya.

// Ukuran model dipakai sebagai satuan acuan supaya angka-angkanya ikut skala
// berkas, bukan nilai tetap yang benar hanya untuk satu model.
// Akar model ditelusuri dari mesh-nya sendiri, bukan lewat activeModelRoot():
// fungsi itu berada di lingkup lain dan tidak terjangkau dari sini.
function akarModelV93(mesh){
  let n=mesh;
  while(n&&n.parent&&!n.parent.isScene)n=n.parent;
  return n||mesh;
}
function ukuranModelV93(akar){
  if(!akar)return 1;
  const b=new THREE.Box3().setFromObject(akar), s=b.getSize(new THREE.Vector3());
  return Math.max(s.x,s.y,s.z)||1;
}
// Matriks kulit satu verteks: gabungan tulang berbobot, dikembalikan ke ruang
// lokal mesh. Dipakai untuk DUA arah - membaca posisi terkulit, dan menulis
// balik pergeseran yang dihitung di ruang dunia.
function matriksV93(mesh,i,M,tmp){
  const g=mesh.geometry, si=g.getAttribute('skinIndex'), sw=g.getAttribute('skinWeight');
  if(!si||!sw||!mesh.skeleton)return false;
  const e=M.elements; for(let k=0;k<16;k++)e[k]=0;
  const bi=[si.getX(i),si.getY(i),si.getZ(i),si.getW(i)];
  const w=[sw.getX(i),sw.getY(i),sw.getZ(i),sw.getW(i)];
  let ada=false;
  for(let c=0;c<4;c++){
    if(!(w[c]>0))continue;
    const b=mesh.skeleton.bones[bi[c]], inv=mesh.skeleton.boneInverses[bi[c]];
    if(!b||!inv)continue;
    tmp.multiplyMatrices(b.matrixWorld,inv);
    const te=tmp.elements; for(let k=0;k<16;k++)e[k]+=te[k]*w[c];
    ada=true;
  }
  if(!ada)return false;
  M.multiply(mesh.bindMatrix);
  M.premultiply(mesh.bindMatrixInverse);
  return true;
}
// Pakaian = semua mesh lain yang tergambar. Mesh yang disembunyikan tidak
// dihitung menutupi apa pun, karena memang tidak terlihat.
function pakaianV93(kulit,akar){
  const keluar=[];
  if(!akar)return keluar;
  akar.traverse(o=>{
    if(o===kulit||!o.isMesh||!o.visible||!o.geometry)return;
    if(!o.geometry.getAttribute('position'))return;
    keluar.push(o);
  });
  return keluar;
}
function rapikanKulitV93(kulit){
  const g=kulit.geometry, pos=g.getAttribute('position'), nor=g.getAttribute('normal');
  if(!pos||!nor)return {gagal:'mesh ini tidak punya posisi/normal'};
  const akar=akarModelV93(kulit);
  const baju=pakaianV93(kulit,akar);
  if(!baju.length)return {gagal:'tidak ada mesh lain yang menutupi'};
  akar.updateMatrixWorld(true);

  const skala=ukuranModelV93(akar);
  const jangkau=skala*0.045;       // panjang sinar: cukup menembus pakaian tertebal
  const margin=skala*0.002;        // sisa ruang supaya tidak berdesir di batas
  const batas=skala*0.03;          // dorongan terjauh yang diizinkan

  const sinar=new THREE.Raycaster();
  const M=new THREE.Matrix4(), tmp=new THREE.Matrix4(), A=new THREE.Matrix4();
  const A3=new THREE.Matrix3();
  const p=new THREE.Vector3(), n=new THREE.Vector3(), asal=new THREE.Vector3();
  const arah=new THREE.Vector3(), geser=new THREE.Vector3(), lokal=new THREE.Vector3();
  const berkulit=!!(kulit.isSkinnedMesh&&kulit.skeleton);

  const asli=new Float32Array(pos.count*3);
  for(let i=0;i<pos.count;i++){asli[i*3]=pos.getX(i);asli[i*3+1]=pos.getY(i);asli[i*3+2]=pos.getZ(i)}

  let kena=0, terbuka=0, rapi=0, terjauh=0;
  for(let i=0;i<pos.count;i++){
    let punyaM=false;
    if(berkulit)punyaM=matriksV93(kulit,i,M,tmp);
    A.copy(kulit.matrixWorld); if(punyaM)A.multiply(M);
    p.fromBufferAttribute(pos,i).applyMatrix4(A);
    A3.setFromMatrix4(A);
    n.fromBufferAttribute(nor,i).applyMatrix3(A3).normalize();

    asal.copy(p).addScaledVector(n,jangkau);
    arah.copy(n).multiplyScalar(-1);
    sinar.set(asal,arah);
    sinar.far=jangkau*2;
    const tumbukan=sinar.intersectObjects(baju,false);
    // Hanya permukaan yang MENGHADAP KELUAR yang dianggap menutupi. Tanpa syarat
    // ini, sinar yang masuk lewat sisi dalam sepatu atau sarung tangan mengenai
    // dinding seberangnya dan menghasilkan dorongan sebesar panjang sinar.
    let t=null;
    for(const h of tumbukan){
      if(!h.face)continue;
      if(h.face.normal.clone().transformDirection(h.object.matrixWorld).dot(arah)>=0)continue;
      t=jangkau-h.distance; break;
    }
    if(t===null){terbuka++;continue}          // tidak tertutup apa pun: biarkan
    // t = letak permukaan baju sepanjang +n dihitung dari kulit.
    //   t > 0  -> baju di LUAR kulit: sudah benar, tinggal seberapa longgar
    //   t <= 0 -> kulit menonjol keluar dari baju
    // Yang perlu didorong masuk hanya yang jaraknya di bawah margin - termasuk
    // yang sudah di dalam tetapi terlalu rapat sehingga tetap berdesir.
    const dorong=margin-t;
    if(dorong<=0){rapi++;continue}            // sudah cukup longgar
    const pakai=Math.min(dorong,batas);
    if(pakai>terjauh)terjauh=pakai;
    geser.copy(n).multiplyScalar(-pakai);
    // Pergeseran dihitung di ruang dunia; dikembalikan ke ruang lokal lewat
    // kebalikan matriks yang sama, supaya benar pada pose apa pun.
    lokal.copy(geser).applyMatrix3(A3.clone().invert());
    pos.setXYZ(i, pos.getX(i)+lokal.x, pos.getY(i)+lokal.y, pos.getZ(i)+lokal.z);
    kena++;
  }
  if(!kena)return {gagal:'tidak ada kulit yang tertutup pakaian pada mesh ini'};
  pos.needsUpdate=true;
  g.computeBoundingBox(); g.computeBoundingSphere();
  if(!kulit.userData)kulit.userData={};
  kulit.userData.posisiAsliV93=asli;
  return {kena:kena, terbuka:terbuka, rapi:rapi, total:pos.count, terjauh:+terjauh.toFixed(3)};
}
function kembalikanKulitV93(kulit){
  const asli=kulit.userData&&kulit.userData.posisiAsliV93;
  if(!asli)return false;
  const pos=kulit.geometry.getAttribute('position');
  if(!pos||pos.count*3!==asli.length)return false;
  for(let i=0;i<pos.count;i++)pos.setXYZ(i,asli[i*3],asli[i*3+1],asli[i*3+2]);
  pos.needsUpdate=true;
  kulit.geometry.computeBoundingBox(); kulit.geometry.computeBoundingSphere();
  delete kulit.userData.posisiAsliV93;
  return true;
}
function segarkanTombolTuckV93(){
  const t=$('meshTuckBtn'); if(!t)return;
  const i=(typeof activeMeshLayerIndex!=='undefined')?activeMeshLayerIndex:-1;
  const m=(i>=0&&typeof meshList!=='undefined')?meshList[i]:null;
  const sudah=!!(m&&m.userData&&m.userData.posisiAsliV93);
  t.textContent=sudah?'↩ Kembalikan Kulit':'⤵ Rapikan Kulit Tertutup';
  t.classList.toggle('pulih',sudah);
}
"""

s = s.replace(anchor_js, js + anchor_js, 1)

# handler dipasang di dekat tombol lain pada bilah yang sama
anchor_bind = " $('meshRenameSelectedBtn').onclick=()=>{const m=selectedMesh();if(!m){msg('Pilih mesh dulu');return}renameMeshLayer(selectedIndex())};\n"
if anchor_bind not in s:
    raise SystemExit('pengikat tombol Rename Selected tidak ditemukan')
bind = r""" // SKIN_TUCK_V93
 $('meshTuckBtn').onclick=()=>{
   const m=selectedMesh();
   if(!m){msg('Pilih dulu mesh badan/kulitnya di daftar');return}
   if(m.userData&&m.userData.posisiAsliV93){
     kembalikanKulitV93(m);
     $('meshLayersStatus').textContent='Kulit '+(m.name||'mesh')+' dikembalikan ke bentuk aslinya.';
     msg('Kulit dikembalikan');
     renderMeshLayers(); segarkanTombolTuckV93(); return;
   }
   const h=rapikanKulitV93(m);
   if(h.gagal){msg(h.gagal);return}
   $('meshLayersStatus').textContent='Kulit '+(m.name||'mesh')+': '+h.kena+' verteks dimasukkan (terjauh '
     +h.terjauh+') • '+h.rapi+' sudah longgar • '+h.terbuka+' terbuka, tidak disentuh';
   msg('Rapikan Kulit: '+h.kena+' verteks dimasukkan, '+h.rapi+' sudah longgar, '+h.terbuka+' terbuka dibiarkan');
   renderMeshLayers(); segarkanTombolTuckV93();
 };
 segarkanTombolTuckV93();
"""
s = s.replace(anchor_bind, anchor_bind + bind, 1)

# label tombol ikut berubah setiap daftar mesh digambar ulang
anchor_akhir = "  main.appendChild(barisPetaV88(mesh));   // TEXTURE_BADGE_V88"
if anchor_akhir not in s:
    raise SystemExit('penanda v88 di baris mesh tidak ditemukan')
s = s.replace(anchor_akhir,
              anchor_akhir + "\n    try{segarkanTombolTuckV93()}catch(_){}   // SKIN_TUCK_V93", 1)

p.write_text(s, encoding='utf-8')
print('SKIN_TUCK_V93 applied: tombol Rapikan Kulit Tertutup di daftar mesh')
