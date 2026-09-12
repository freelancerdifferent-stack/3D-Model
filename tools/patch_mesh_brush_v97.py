#!/usr/bin/env python3
# MESH_BRUSH_V97 - kuas usap: bagian yang diusap saja yang bergeser.
#
# Slider v94 menggeser SELURUH mesh sama rata. Itu cukup untuk memasukkan badan
# ke dalam baju, tetapi tidak untuk kasus setempat - misalnya hanya paha yang
# menonjol sementara bagian lain sudah pas. Mengecilkan seluruh badan demi satu
# bagian membuat bagian lain terlalu masuk.
#
# Kuas menambah simpanan pergeseran PER VERTEKS di atas nilai slider, jadi
# keduanya menumpuk dan tidak saling menghapus:
#
#   posisi = asli + normal * (nilai_slider + pergeseran_kuas[verteks])
#
# Karena itu geserMeshV94 ditulis ulang di sini supaya ikut menjumlahkan suku
# per-verteks. Tanpa itu, menggerakkan slider sesudah mengusap akan menghapus
# hasil usapan.
#
# Jarak antar verteks dihitung di ruang LOKAL, bukan ruang dunia. Menghitungnya
# di ruang dunia berarti memanggil applyBoneTransform untuk tiap verteks pada
# tiap gerakan jari - puluhan ribu kali per detik. Verteks benih diambil dari
# muka yang kena sinar, lalu jaraknya diukur dari benih itu di ruang lokal;
# untuk radius sekecil kuas, selisihnya terhadap jarak permukaan terdeformasi
# tidak berarti.
#
# Usapan dibatasi 30 kali per detik. Tanpa batas itu, satu gerakan jari memicu
# ratusan lintasan atas 50 ribu verteks dan gambarnya tersendat.
#
# Tombol 0 yang sudah ada dijadikan penghapus keduanya - slider dan usapan -
# supaya tetap ada satu jalan kembali yang pasti.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'MESH_BRUSH_V97' in s:
    raise SystemExit('MESH_BRUSH_V97 sudah ada - patch dijalankan dua kali')
if 'MESH_SCALE_SLIDER_V94' not in s:
    raise SystemExit('slider v94 tidak ditemukan - urutan pipeline salah')

def ganti(lama, baru, apa):
    # Jangkar WAJIB tunggal. Dua kali dalam mesin ini pengikat tersisip ke dalam
    # handler tombol karena jangkarnya cocok sebagai substring di tempat lain,
    # dan fiturnya diam-diam tidak berfungsi. Lebih baik patch-nya gagal keras.
    global s
    n = s.count(lama)
    if n == 0:
        raise SystemExit(apa + ' tidak ditemukan')
    if n > 1:
        raise SystemExit(apa + ' muncul ' + str(n) + ' kali - jangkar tidak tunggal')
    s = s.replace(lama, baru, 1)

# ---------------------------------------------------------------- CSS
ganti("#meshLayersScreen .geser-v94.mati{opacity:.45}\n",
      "#meshLayersScreen .geser-v94.mati{opacity:.45}\n"
      "/* MESH_BRUSH_V97 */\n"
      "#meshLayersScreen .kuas-v97{grid-column:1/-1;display:grid;grid-template-columns:auto 1fr auto;"
      "align-items:center;gap:8px;margin-top:4px;padding:8px 10px;border:1px solid #34485e;"
      "border-radius:9px;background:#101a24}\n"
      "#meshLayersScreen .kuas-v97 .judul{font-size:11px;font-weight:700;color:#9fb6cc;white-space:nowrap}\n"
      "#meshLayersScreen .kuas-v97 .nilai{font-size:12px;font-weight:800;color:#dce7f3;min-width:46px;"
      "text-align:right;font-variant-numeric:tabular-nums}\n"
      "#meshLayersScreen .kuas-v97 input[type=range]{width:100%;accent-color:#4da3ff}\n"
      "#meshLayersScreen #meshKuasBtnV97{grid-column:1/-1;height:40px;border-radius:9px;font-weight:800;"
      "border:1px solid #34485e;background:#16232f;color:#dce7f3}\n"
      "#meshLayersScreen #meshKuasBtnV97.on{border-color:#4da3ff;background:#123049;color:#e8f4ff}\n"
      "#meshLayersScreen .kuas-v97.mati{opacity:.45}\n",
      'CSS slider v94')

# ---------------------------------------------------------------- markup
ganti('          <button type="button" id="meshGeserResetV94" title="Kembali ke 0">0</button>\n'
      '        </div>\n',
      '          <button type="button" id="meshGeserResetV94" title="Kembali ke 0">0</button>\n'
      '        </div>\n'
      '        <button type="button" id="meshKuasBtnV97">🖌 Kuas: MATI</button>\n'
      '        <div class="kuas-v97" id="meshKuasBarV97">\n'
      '          <span class="judul">Radius</span>\n'
      '          <input type="range" id="meshKuasRadiusV97" min="5" max="200" value="40" step="1">\n'
      '          <span class="nilai" id="meshKuasRadiusNilaiV97">—</span>\n'
      '          <span class="judul">Kekuatan</span>\n'
      '          <input type="range" id="meshKuasKuatV97" min="-100" max="100" value="-30" step="1">\n'
      '          <span class="nilai" id="meshKuasKuatNilaiV97">—</span>\n'
      '        </div>\n',
      'tombol reset slider v94')

# ---------------------------------------------------------------- geserMeshV94 ditulis ulang
ganti("""  for(let i=0;i<pos.count;i++){
    pos.setXYZ(i, asli[i*3]  +nor.getX(i)*jumlah,
                  asli[i*3+1]+nor.getY(i)*jumlah,
                  asli[i*3+2]+nor.getZ(i)*jumlah);
  }""",
"""  // MESH_BRUSH_V97 - suku per-verteks dari kuas dijumlahkan di atas nilai slider,
  // supaya menggerakkan slider tidak menghapus hasil usapan.
  const kuas=mesh.userData.kuasV97||null;
  for(let i=0;i<pos.count;i++){
    const t=jumlah+(kuas?kuas[i]:0);
    pos.setXYZ(i, asli[i*3]  +nor.getX(i)*t,
                  asli[i*3+1]+nor.getY(i)*t,
                  asli[i*3+2]+nor.getZ(i)*t);
  }""",
      'perulangan geserMeshV94')

# ---------------------------------------------------------------- mesin kuas
ganti("function meshAktifV94(){",
r"""// MESH_BRUSH_V97 - keadaan kuas.
let kuasAktifV97=false, kuasPointerV97=null, kuasWaktuV97=0;
function ukuranKuasV97(mesh){
  try{ return ukuranModelV93(akarModelV93(mesh)) }catch(_){ return 1 }
}
function radiusKuasV97(mesh){ return ukuranKuasV97(mesh)*(Number($('meshKuasRadiusV97').value)/2000); }
function kuatKuasV97(mesh){ return ukuranKuasV97(mesh)*(Number($('meshKuasKuatV97').value)/20000); }
// Simpanan pergeseran per verteks, satu angka skalar sepanjang normal.
function simpananKuasV97(mesh){
  const pos=mesh.geometry.getAttribute('position');
  if(!mesh.userData)mesh.userData={};
  if(!mesh.userData.kuasV97||mesh.userData.kuasV97.length!==pos.count)
    mesh.userData.kuasV97=new Float32Array(pos.count);
  return mesh.userData.kuasV97;
}
// Verteks benih diambil dari muka yang kena sinar, lalu jaraknya diukur di ruang
// LOKAL. Mengukurnya di ruang dunia berarti applyBoneTransform puluhan ribu kali
// tiap gerakan jari.
function usapKuasV97(mesh,benih,radius,kuat){
  const g=mesh.geometry, pos=g.getAttribute('position'), nor=g.getAttribute('normal');
  if(!pos||!nor)return 0;
  const asli=mesh.userData.asliGeserV94;
  if(!asli)return 0;
  const simp=simpananKuasV97(mesh);
  const jumlah=(mesh.userData&&mesh.userData.geserV94)||0;
  const bx=asli[benih*3], by=asli[benih*3+1], bz=asli[benih*3+2];
  const r2=radius*radius;
  let kena=0;
  for(let i=0;i<pos.count;i++){
    const dx=asli[i*3]-bx, dy=asli[i*3+1]-by, dz=asli[i*3+2]-bz;
    const d2=dx*dx+dy*dy+dz*dz;
    if(d2>r2)continue;
    const f=1-d2/r2;            // melembut ke tepi, kuadrat supaya tidak bertepi tajam
    simp[i]+=kuat*f*f;
    const t=jumlah+simp[i];
    pos.setXYZ(i, asli[i*3]  +nor.getX(i)*t,
                  asli[i*3+1]+nor.getY(i)*t,
                  asli[i*3+2]+nor.getZ(i)*t);
    kena++;
  }
  if(kena){ pos.needsUpdate=true; g.computeBoundingSphere(); }
  return kena;
}
function segarkanKuasV97(){
  const btn=$('meshKuasBtnV97'), bar=$('meshKuasBarV97');
  if(!btn||!bar)return;
  const m=meshAktifV94();
  btn.textContent=kuasAktifV97?'🖌 Kuas: HIDUP':'🖌 Kuas: MATI';
  btn.classList.toggle('on',kuasAktifV97);
  bar.classList.toggle('mati',!m);
  if(!m){$('meshKuasRadiusNilaiV97').textContent='—';$('meshKuasKuatNilaiV97').textContent='—';return}
  $('meshKuasRadiusNilaiV97').textContent=radiusKuasV97(m).toFixed(2);
  const k=kuatKuasV97(m);
  $('meshKuasKuatNilaiV97').textContent=(k>0?'+':'')+k.toFixed(3);
}
function setKuasV97(on){
  kuasAktifV97=!!on;
  if(kuasAktifV97){
    try{ setExclusivePartMode('move',false) }catch(_){}
    go('editorScreen');
    msg('Kuas HIDUP — usap bagian yang mau digeser');
  }else{
    if(kuasPointerV97!==null){ try{canvas.releasePointerCapture(kuasPointerV97)}catch(_){} }
    kuasPointerV97=null; controls.enabled=true;
    msg('Kuas MATI');
  }
  segarkanKuasV97();
}
function meshAktifV94(){""",
      'meshAktifV94')

# ---------------------------------------------------------------- penyegar di daftar mesh
ganti("    try{segarkanGeserV94()}catch(_){}        // MESH_SCALE_SLIDER_V94",
      "    try{segarkanGeserV94()}catch(_){}        // MESH_SCALE_SLIDER_V94\n"
      "    try{segarkanKuasV97()}catch(_){}         // MESH_BRUSH_V97",
      'penyegar slider di baris mesh')

# ---------------------------------------------------------------- pengikat
ganti(" };\n segarkanGeserV94();\n",
r""" };
 segarkanGeserV94();
 // MESH_BRUSH_V97
 $('meshKuasBtnV97').onclick=()=>setKuasV97(!kuasAktifV97);
 $('meshKuasRadiusV97').oninput=segarkanKuasV97;
 $('meshKuasKuatV97').oninput=segarkanKuasV97;
 // Pola pointer mengikuti Part Drag: tangkap pointer, matikan orbit, dan
 // hentikan penyebaran supaya gerakan jari tidak ikut memutar kamera.
 canvas.addEventListener('pointerdown',ev=>{
   if(!kuasAktifV97)return;
   const m=meshAktifV94();
   if(!m){msg('Pilih mesh dulu di daftar');return}
   if(!m.userData||!m.userData.asliGeserV94)geserMeshV94(m,(m.userData&&m.userData.geserV94)||0);
   const hit=hitForSpecificMesh(ev,m);
   if(!hit||!hit.face)return;
   kuasPointerV97=ev.pointerId;
   controls.enabled=false;
   try{canvas.setPointerCapture(ev.pointerId)}catch(_){}
   usapKuasV97(m,hit.face.a,radiusKuasV97(m),kuatKuasV97(m));
   ev.preventDefault(); ev.stopPropagation();
 },{capture:true});
 canvas.addEventListener('pointermove',ev=>{
   if(!kuasAktifV97||kuasPointerV97===null||ev.pointerId!==kuasPointerV97)return;
   const kini=(typeof performance!=='undefined')?performance.now():Date.now();
   if(kini-kuasWaktuV97<33){ev.preventDefault();return}   // 30 usapan/detik
   kuasWaktuV97=kini;
   const m=meshAktifV94();
   if(!m)return;
   const hit=hitForSpecificMesh(ev,m);
   if(hit&&hit.face)usapKuasV97(m,hit.face.a,radiusKuasV97(m),kuatKuasV97(m));
   ev.preventDefault(); ev.stopPropagation();
 },{capture:true});
 const lepasKuasV97=ev=>{
   if(kuasPointerV97===null)return;
   if(ev&&ev.pointerId!==undefined&&ev.pointerId!==kuasPointerV97)return;
   try{canvas.releasePointerCapture(kuasPointerV97)}catch(_){}
   kuasPointerV97=null;
   if(!kuasAktifV97)controls.enabled=true; else controls.enabled=false;
 };
 canvas.addEventListener('pointerup',lepasKuasV97,{capture:true});
 canvas.addEventListener('pointercancel',lepasKuasV97,{capture:true});
 segarkanKuasV97();
""",
      'pemanggilan segarkanGeserV94 yang berdiri sendiri')

# ---------------------------------------------------------------- tombol 0 menghapus keduanya
ganti("""   geserMeshV94(m,0);
   if(m.userData)delete m.userData.geserV94;""",
"""   // MESH_BRUSH_V97 - satu jalan kembali: slider dan usapan dihapus bersama.
   if(m.userData&&m.userData.kuasV97)m.userData.kuasV97.fill(0);
   geserMeshV94(m,0);
   if(m.userData)delete m.userData.geserV94;""",
      'isi tombol reset slider')

p.write_text(s, encoding='utf-8')
print('MESH_BRUSH_V97 applied: kuas usap per-verteks di atas slider')
