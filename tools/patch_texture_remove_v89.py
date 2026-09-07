#!/usr/bin/env python3
# TEXTURE_REMOVE_V89 - tombol "Hapus Texture" di menu Material.
#
# Dilaporkan pengguna: tidak ada cara membatalkan tekstur yang terlanjur
# dipasang. Apply Texture hanya menimpa; untuk mengosongkan sebuah saluran
# satu-satunya jalan adalah mengimpor ulang modelnya dan mengulang semuanya
# dari awal.
#
# Tombol ini memakai dua pemilih yang sudah ada - Apply to dan Texture
# Channel - jadi tidak ada tata cara baru yang perlu dihafal: pilih mesh,
# pilih saluran, tekan Hapus Texture.
#
# Alpha Mask ditangani berbeda dari saluran lain. Empat saluran biasa cukup
# dikosongkan petanya. Alpha Mask tidak punya peta sendiri - v87 menuliskan
# topeng ke dalam kanal alpha tekstur Base Color, jadi membatalkannya berarti
# MENGEMBALIKAN tekstur Base Color yang belum bertopeng.
#
# Karena itu satu baris v87 ikut diubah di sini: tekstur lama tidak lagi
# dibuang sesudah topeng dipasang, melainkan disimpan di userData tekstur
# baru. Tanpa perubahan itu tidak ada yang bisa dikembalikan - tekstur aslinya
# sudah dilepas dari memori dan Base Color akan hilang sama sekali begitu
# topengnya dibatalkan.
#
# Base Color juga menyeret emissive: cabang 'map' di Apply Texture memasang
# emissiveMap dengan tekstur yang sama dan emissiveIntensity 0.32. Menghapus
# Base Color tanpa membereskan itu menyisakan mesh yang tetap bercahaya
# sendiri dari tekstur yang sudah tidak ada.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'TEXTURE_REMOVE_V89' in s:
    raise SystemExit('TEXTURE_REMOVE_V89 sudah ada - patch dijalankan dua kali')
if 'ALPHA_MASK_V87' not in s:
    raise SystemExit('mesin v87 tidak ditemukan - urutan pipeline salah')

# --------------------------------------------- v87: simpan yang lama, jangan dibuang
lama_dispose = "  if(lama.dispose) { try{ lama.dispose(); }catch(_){} }\n  return true;"
if lama_dispose not in s:
    raise SystemExit('baris pembuangan tekstur v87 tidak ditemukan')
baru_dispose = (
    "  // TEXTURE_REMOVE_V89 - tekstur asli TIDAK dibuang, disimpan supaya Hapus\n"
    "  // Texture pada saluran Alpha Mask bisa mengembalikannya. Membuangnya di\n"
    "  // sini membuat pembatalan mustahil: Base Color ikut lenyap.\n"
    "  if(!baru.userData) baru.userData={};\n"
    "  baru.userData.sebelumTopengV89 = lama;\n"
    "  return true;")
s = s.replace(lama_dispose, baru_dispose, 1)

# --------------------------------------------- tombol
anchor_btn = '      <button class="primary" id="applyTextureBtn">Apply Texture</button>\n'
if anchor_btn not in s:
    raise SystemExit('tombol Apply Texture tidak ditemukan')
s = s.replace(anchor_btn,
              anchor_btn + '      <button class="outline" id="removeTextureBtn">Hapus Texture</button>\n', 1)

anchor_css = "/* TEXTURE_BADGE_V88 */"
if anchor_css not in s:
    raise SystemExit('penanda CSS v88 tidak ditemukan')
s = s.replace(anchor_css,
              "/* TEXTURE_REMOVE_V89 */\n#removeTextureBtn{margin-top:8px;width:100%}\n" + anchor_css, 1)

# --------------------------------------------- kerjanya
anchor_js = "$('wireBtn').onclick=()=>{"
if anchor_js not in s:
    raise SystemExit('titik sisip sesudah Apply Texture tidak ditemukan')

js = r"""// TEXTURE_REMOVE_V89 - kosongkan satu saluran tekstur dari mesh terpilih.
function hapusSaluranV89(nm, saluran){
  if(!nm) return false;
  if(saluran==='map'){
    if(!nm.map) return false;
    // Base Color memasang emissiveMap dengan tekstur yang sama (lihat cabang
    // 'map' di Apply Texture). Dibiarkan, mesh tetap bercahaya dari tekstur
    // yang sudah tidak ada.
    if(nm.emissiveMap===nm.map){ nm.emissiveMap=null; if('emissiveIntensity' in nm) nm.emissiveIntensity=0; }
    nm.map=null;
    return true;
  }
  if(saluran==='alphaMaskV87'){
    const asli = nm.map && nm.map.userData ? nm.map.userData.sebelumTopengV89 : null;
    if(!asli) return false;                 // mesh ini memang belum pernah ditopengi
    const bertopeng = nm.map;
    if(nm.emissiveMap===bertopeng) nm.emissiveMap=asli;
    nm.map = asli;
    nm.alphaTest = 0;
    if(bertopeng.dispose){ try{ bertopeng.dispose(); }catch(_){} }
    return true;
  }
  const petaLain = { normalMap:'normalMap', roughnessMap:'roughnessMap',
                     metalnessMap:'metalnessMap', emissiveMap:'emissiveMap' }[saluran];
  if(!petaLain || !nm[petaLain]) return false;
  nm[petaLain]=null;
  if(petaLain==='emissiveMap' && 'emissiveIntensity' in nm) nm.emissiveIntensity=0;
  return true;
}
$('removeTextureBtn').onclick=()=>{
  if(!root){msg('Import GLB/FBX dulu');return}
  const targets=getTargets();
  if(!targets.length){msg('Tidak ada mesh target');return}
  const saluran=$('channel').value;
  let kena=0, lewat=0;
  for(const mesh of targets){
    const mats=Array.isArray(mesh.material)?mesh.material:[mesh.material];
    let adaYangKena=false;
    for(const m of mats){
      if(!m) continue;
      if(hapusSaluranV89(m,saluran)){ m.needsUpdate=true; adaYangKena=true; }
    }
    if(adaYangKena) kena++; else lewat++;
  }
  if(typeof renderMeshLayers==='function') renderMeshLayers();
  const namaSaluran=$('channel').options[$('channel').selectedIndex].textContent;
  if(!kena){
    msg(saluran==='alphaMaskV87'
      ? 'Tidak ada topeng alpha untuk dibatalkan pada mesh itu'
      : namaSaluran+' memang belum terpasang pada mesh itu');
    return;
  }
  let info=namaSaluran+' dihapus dari '+kena+' mesh';
  if(lewat) info+=' • '+lewat+' mesh dilewati: saluran itu memang kosong';
  msg(info);
  $('exportStatus').textContent='Texture diubah. Export GLB akan menyimpan keadaan terbaru.';
  go('editorScreen');
};
$('wireBtn').onclick=()=>{"""
s = s.replace(anchor_js, js, 1)

p.write_text(s, encoding='utf-8')
print('TEXTURE_REMOVE_V89 applied: tombol Hapus Texture di menu Material')
