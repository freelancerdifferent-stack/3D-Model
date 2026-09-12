#!/usr/bin/env python3
# MESH_SCALE_SLIDER_V94 - slider Kembang/Kempis: mesh digeser sepanjang
# permukaannya sendiri, sebanyak yang pengguna mau.
#
# Diminta pengguna: mesh badan atau pakaian diubah MANUAL di aplikasi, bukan
# otomatis. v93 menebak sendiri bagian mana yang tertutup lalu mendorongnya -
# dan tebakan itu terbukti salah pada mesh yang bukan lapisan terdalam. Di sini
# tidak ada yang ditebak: pengguna menarik slider dan melihat hasilnya.
#
# Yang dipakai dari v93 hanya gagasannya. Bagian tersulitnya - matriks kulit
# per-verteks - justru TIDAK diperlukan. v93 membutuhkannya karena menembakkan
# sinar di ruang dunia, sehingga pergeseran yang dihitung di sana harus
# dikembalikan ke ruang lokal. Menggeser sepanjang normal tidak butuh itu:
# geometri lokal dan normalnya berputar bersama-sama saat dikulitkan, jadi
# menggeser verteks lokal sepanjang normal lokal menghasilkan pergeseran yang
# sama persis sesudah dikulitkan. Tanpa sinar, tanpa grid, tanpa matriks -
# seketika bahkan pada 50 ribu verteks.
#
# Posisi asli disimpan sekali, dan SETIAP perubahan slider dihitung ulang dari
# posisi asli itu - bukan ditambahkan ke keadaan sekarang. Kalau ditambahkan,
# menarik slider maju-mundur akan menumpuk galat pembulatan dan bentuknya
# perlahan melenceng; dengan cara ini, kembali ke 0 berarti kembali persis.
#
# Jangkauannya dinyatakan sebagai persen ukuran model, bukan angka tetap, supaya
# rasa slidernya sama pada model besar maupun kecil.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'MESH_SCALE_SLIDER_V94' in s:
    raise SystemExit('MESH_SCALE_SLIDER_V94 sudah ada - patch dijalankan dua kali')
if 'meshTuckBtn' not in s:
    raise SystemExit('bilah kelola mesh v93 tidak ditemukan - urutan pipeline salah')

def ganti(lama, baru, apa):
    global s
    if lama not in s:
        raise SystemExit(apa + ' tidak ditemukan')
    s = s.replace(lama, baru, 1)

# ---------------------------------------------------------------- CSS
ganti("#meshLayersScreen #meshTuckBtn.pulih{border-color:#6f5a2f;background:#292314;color:#f5ecd9}\n",
      "#meshLayersScreen #meshTuckBtn.pulih{border-color:#6f5a2f;background:#292314;color:#f5ecd9}\n"
      "/* MESH_SCALE_SLIDER_V94 */\n"
      "#meshLayersScreen .geser-v94{grid-column:1/-1;display:grid;grid-template-columns:auto 1fr auto auto;"
      "align-items:center;gap:8px;margin-top:4px;padding:8px 10px;border:1px solid #34485e;"
      "border-radius:9px;background:#101a24}\n"
      "#meshLayersScreen .geser-v94 .judul{font-size:11px;font-weight:700;color:#9fb6cc;white-space:nowrap}\n"
      "#meshLayersScreen .geser-v94 .nilai{font-size:12px;font-weight:800;color:#dce7f3;min-width:52px;"
      "text-align:right;font-variant-numeric:tabular-nums}\n"
      "#meshLayersScreen .geser-v94 input[type=range]{width:100%;accent-color:#4da3ff}\n"
      "#meshLayersScreen .geser-v94 button{height:28px;min-width:34px;border-radius:7px;border:1px solid #34485e;"
      "background:#16232f;color:#dce7f3;font-weight:800;font-size:11px}\n"
      "#meshLayersScreen .geser-v94.mati{opacity:.45}\n",
      'CSS tombol v93')

# ---------------------------------------------------------------- markup
ganti('        <button class="mesh-action-btn" id="meshTuckBtn">⤵ Rapikan Kulit Tertutup</button>\n',
      '        <button class="mesh-action-btn" id="meshTuckBtn">⤵ Rapikan Kulit Tertutup</button>\n'
      '        <div class="geser-v94" id="meshGeserBarV94">\n'
      '          <span class="judul">Kempis ↔ Kembang</span>\n'
      '          <input type="range" id="meshGeserV94" min="-200" max="200" value="0" step="1">\n'
      '          <span class="nilai" id="meshGeserNilaiV94">0.00</span>\n'
      '          <button type="button" id="meshGeserResetV94" title="Kembali ke 0">0</button>\n'
      '        </div>\n',
      'tombol Rapikan Kulit v93')

# ---------------------------------------------------------------- JS
ganti("function renderMeshLayers(){",
r"""// MESH_SCALE_SLIDER_V94 - geser mesh sepanjang normalnya, sebanyak yang diminta.

// Jangkauan slider: 2% ukuran model ke tiap arah. Dinyatakan relatif supaya
// terasa sama pada model setinggi 2 satuan maupun 270 satuan.
function jangkauGeserV94(mesh){
  try{ return ukuranModelV93(akarModelV93(mesh))*0.02 }catch(_){ return 1 }
}
// Selalu dihitung ulang dari posisi asli, tidak pernah ditambahkan ke keadaan
// sekarang - supaya maju-mundur slider tidak menumpuk galat.
function geserMeshV94(mesh,jumlah){
  const g=mesh&&mesh.geometry, pos=g&&g.getAttribute('position'), nor=g&&g.getAttribute('normal');
  if(!pos||!nor)return false;
  if(!mesh.userData)mesh.userData={};
  let asli=mesh.userData.asliGeserV94;
  if(!asli){
    asli=new Float32Array(pos.count*3);
    for(let i=0;i<pos.count;i++){asli[i*3]=pos.getX(i);asli[i*3+1]=pos.getY(i);asli[i*3+2]=pos.getZ(i)}
    mesh.userData.asliGeserV94=asli;
  }
  for(let i=0;i<pos.count;i++){
    pos.setXYZ(i, asli[i*3]  +nor.getX(i)*jumlah,
                  asli[i*3+1]+nor.getY(i)*jumlah,
                  asli[i*3+2]+nor.getZ(i)*jumlah);
  }
  pos.needsUpdate=true;
  g.computeBoundingBox(); g.computeBoundingSphere();
  mesh.userData.geserV94=jumlah;
  return true;
}
function meshAktifV94(){
  const i=(typeof activeMeshLayerIndex!=='undefined')?activeMeshLayerIndex:-1;
  return (i>=0&&typeof meshList!=='undefined')?(meshList[i]||null):null;
}
// Slider mengikuti mesh yang sedang aktif: tiap mesh punya nilainya sendiri.
function segarkanGeserV94(){
  const bar=$('meshGeserBarV94'), sl=$('meshGeserV94'), lb=$('meshGeserNilaiV94');
  if(!bar||!sl||!lb)return;
  const m=meshAktifV94();
  const bisa=!!(m&&m.geometry&&m.geometry.getAttribute('position')&&m.geometry.getAttribute('normal'));
  bar.classList.toggle('mati',!bisa);
  sl.disabled=!bisa;
  if(!bisa){sl.value='0';lb.textContent='—';return}
  const jangkau=jangkauGeserV94(m);
  const nilai=(m.userData&&m.userData.geserV94)||0;
  sl.value=String(Math.round(nilai/jangkau*200));
  lb.textContent=(nilai>0?'+':'')+nilai.toFixed(2);
}
""" + "function renderMeshLayers(){",
      'renderMeshLayers')

ganti("    try{segarkanTombolTuckV93()}catch(_){}   // SKIN_TUCK_V93",
      "    try{segarkanTombolTuckV93()}catch(_){}   // SKIN_TUCK_V93\n"
      "    try{segarkanGeserV94()}catch(_){}        // MESH_SCALE_SLIDER_V94",
      'penyegar tombol v93 di baris mesh')

# ---------------------------------------------------------------- pengikat
# Jangkarnya HARUS pemanggilan terakhir yang berdiri sendiri, bukan yang di
# dalam handler tombol v93 - pernah salah sasaran ke sana dan pengikat slider
# jadi hanya terpasang kalau tombol itu ditekan.
ganti(" };\n segarkanTombolTuckV93();\n",
      " };\n segarkanTombolTuckV93();\n"
      r""" // MESH_SCALE_SLIDER_V94
 $('meshGeserV94').oninput=()=>{
   const m=meshAktifV94();
   if(!m){segarkanGeserV94();return}
   const jangkau=jangkauGeserV94(m);
   const jumlah=(Number($('meshGeserV94').value)/200)*jangkau;
   if(!geserMeshV94(m,jumlah)){msg('Mesh ini tidak bisa digeser');return}
   $('meshGeserNilaiV94').textContent=(jumlah>0?'+':'')+jumlah.toFixed(2);
   $('meshLayersStatus').textContent=(m.name||'mesh')+': '+(jumlah>0?'dikembangkan ':'dikempiskan ')
     +Math.abs(jumlah).toFixed(2)+' • 0 untuk kembali ke bentuk asli';
 };
 $('meshGeserResetV94').onclick=()=>{
   const m=meshAktifV94();
   if(!m)return;
   geserMeshV94(m,0);
   if(m.userData)delete m.userData.geserV94;
   segarkanGeserV94();
   $('meshLayersStatus').textContent=(m.name||'mesh')+' kembali ke bentuk aslinya.';
   msg('Kembali ke bentuk asli');
 };
 segarkanGeserV94();
""",
      'pemanggilan segarkanTombolTuckV93 yang berdiri sendiri')

p.write_text(s, encoding='utf-8')
print('MESH_SCALE_SLIDER_V94 applied: slider Kempis/Kembang per mesh')
