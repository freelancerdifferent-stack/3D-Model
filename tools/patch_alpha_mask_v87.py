#!/usr/bin/env python3
# ALPHA_MASK_V87 - saluran tekstur "Alpha Mask" di menu Material.
#
# Gejalanya: rambut model tampil sebagai gumpalan padat, bukan helai.
#
# Terukur pada SK_NYX.glb dan pada berkas paket aslinya:
#
#   tekstur                      alpha min  alpha maks  bagian tembus
#   woman-haircard 8-color.png       255        255         0.00%
#   topeng helai (berkas terpisah)     -          -        76.32%
#   atlas pakaian                      0        255         6.79%
#
# Kartu rambut adalah bidang datar; helainya dipotong oleh kanal alpha. Paket
# aslinya menyimpan potongan itu di BERKAS TERPISAH, bukan di kanal alpha
# berkas warnanya - kanal alpha berkas warna rata 255 seluruhnya. Karena tidak
# ada tempat memasukkan berkas topeng, potongannya tidak pernah sampai ke
# material, dan rambut tergambar sebagai kotak penuh.
#
# Menu Material sebelumnya punya lima saluran (Base Color, Normal, Roughness,
# Metallic, Emissive) - tidak satu pun bisa menerima topeng, dan alphaTest
# tidak pernah disetel, hanya diwariskan (alphaTest: m?.alphaTest || 0).
#
# Saluran baru ini menuliskan kecerahan topeng ke kanal alpha tekstur Base
# Color mesh itu, lalu menyalakan alphaTest.
#
# Kenapa digabung ke Base Color, bukan dipasang sebagai alphaMap terpisah:
# three.js menerima alphaMap, tetapi glTF TIDAK mengenal peta alpha terpisah -
# alpha harus berada di kanal keempat baseColorTexture. Kalau dipasang
# terpisah, hasilnya benar di layar tetapi hilang begitu ditekan Export, dan
# persoalannya kembali ke awal. Penggabungan membuatnya ikut terbawa.
#
# alphaTest, bukan transparent: potong tegas tidak punya masalah urutan
# gambar. Rambut yang bertumpuk dengan transparent sering memperlihatkan
# lubang saat kepala berputar.
#
# Ukuran hasil mengikuti tekstur Base Color, bukan topeng - topeng
# diskalakan menyesuaikan. Mesh yang belum punya Base Color dilewati dan
# dilaporkan, bukan gagal diam-diam.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'ALPHA_MASK_V87' in s:
    raise SystemExit('ALPHA_MASK_V87 sudah ada - patch dijalankan dua kali')

# ---------------------------------------------------------------- pilihan saluran
anchor_opt = '            <option value="emissiveMap">Emissive Map</option>\n'
if anchor_opt not in s:
    raise SystemExit('daftar Texture Channel tidak ditemukan')
s = s.replace(anchor_opt,
              anchor_opt + '            <option value="alphaMaskV87">Alpha Mask</option>\n', 1)

# ---------------------------------------------------------------- fungsi penggabung
anchor_fn = "function ensureUsableMaterial(oldMat){"
if anchor_fn not in s:
    raise SystemExit('ensureUsableMaterial tidak ditemukan')

fn = r"""// ALPHA_MASK_V87 - tuliskan kecerahan topeng ke kanal alpha tekstur Base Color.
// Mengembalikan true bila berhasil, false bila mesh belum punya Base Color.
function terapkanTopengAlphaV87(nm, imgTopeng){
  const lama = nm && nm.map;
  const gbr = lama && lama.image;
  if(!gbr || !gbr.width || !gbr.height) return false;   // belum ada Base Color
  const W = gbr.width, H = gbr.height;                  // ukuran ikut Base Color
  const cv = document.createElement('canvas'); cv.width=W; cv.height=H;
  const cx = cv.getContext('2d',{willReadFrequently:true});
  cx.drawImage(gbr,0,0,W,H);
  const warna = cx.getImageData(0,0,W,H);
  const cv2 = document.createElement('canvas'); cv2.width=W; cv2.height=H;
  const cx2 = cv2.getContext('2d',{willReadFrequently:true});
  cx2.drawImage(imgTopeng,0,0,W,H);                     // topeng diskalakan menyesuaikan
  const topeng = cx2.getImageData(0,0,W,H);
  // Kanal merah topeng dipakai sebagai kecerahan: topeng ini hitam-putih,
  // jadi R, G, dan B-nya sama - membaca satu kanal sudah cukup dan lebih murah.
  for(let i=0;i<warna.data.length;i+=4) warna.data[i+3]=topeng.data[i];
  cx.putImageData(warna,0,0);
  const baru = new THREE.CanvasTexture(cv);
  baru.colorSpace = THREE.SRGBColorSpace;
  // Salin sifat tekstur lama: flipY glTF (false) berbeda dari bawaan PNG,
  // dan wrap/repeat/offset menentukan letak UV. Kalau tidak disalin, rambutnya
  // terbalik atau bergeser.
  baru.flipY = lama.flipY;
  baru.wrapS = lama.wrapS; baru.wrapT = lama.wrapT;
  baru.repeat.copy(lama.repeat); baru.offset.copy(lama.offset);
  baru.center.copy(lama.center); baru.rotation = lama.rotation;
  baru.magFilter = lama.magFilter; baru.minFilter = lama.minFilter;
  baru.anisotropy = lama.anisotropy;
  baru.name = lama.name || 'alphaMaskV87';
  baru.needsUpdate = true;
  // emissiveMap sering menunjuk tekstur yang sama (lihat cabang 'map' di
  // Apply Texture); dibiarkan menunjuk yang lama akan membuat pancaran cahaya
  // tetap memenuhi kotak sementara warnanya sudah terpotong.
  if(nm.emissiveMap === lama) nm.emissiveMap = baru;
  nm.map = baru;
  nm.alphaTest = 0.5;        // potong tegas
  nm.transparent = false;    // bukan campur - tidak ada masalah urutan gambar
  nm.side = THREE.DoubleSide;
  if(lama.dispose) { try{ lama.dispose(); }catch(_){} }
  return true;
}
function ensureUsableMaterial(oldMat){"""
s = s.replace(anchor_fn, fn, 1)

# ---------------------------------------------------------------- cabang di Apply Texture
anchor_branch = """        }else if(channel==='emissiveMap'){
          nm.emissiveMap=tex; if(nm.emissive) nm.emissive.set(0xffffff); if('emissiveIntensity' in nm) nm.emissiveIntensity=1;
        }
        nm.needsUpdate=true;"""
if anchor_branch not in s:
    raise SystemExit('cabang saluran tekstur tidak ditemukan')
branch = """        }else if(channel==='emissiveMap'){
          nm.emissiveMap=tex; if(nm.emissive) nm.emissive.set(0xffffff); if('emissiveIntensity' in nm) nm.emissiveIntensity=1;
        }else if(channel==='alphaMaskV87'){
          // ALPHA_MASK_V87 - butuh Base Color lebih dulu; kalau belum ada,
          // material lama dikembalikan apa adanya supaya tidak ada yang rusak.
          if(!terapkanTopengAlphaV87(nm,img)){ tanpaBaseV87++; return oldMat; }
        }
        nm.needsUpdate=true;"""
s = s.replace(anchor_branch, branch, 1)

# ---------------------------------------------------------------- penghitung
anchor_count = "    let applied=0, uvGenerated=0, failedUV=0;"
if anchor_count not in s:
    raise SystemExit('penghitung Apply Texture tidak ditemukan')
s = s.replace(anchor_count, anchor_count + "\n    let tanpaBaseV87=0;   // ALPHA_MASK_V87", 1)

# ---------------------------------------------------------------- jangan hitung yang dilewati
anchor_assign = """      mesh.material=Array.isArray(mesh.material)?replacements:replacements[0];
      applied++;"""
if anchor_assign not in s:
    raise SystemExit('titik pemasangan material tidak ditemukan')
assign = """      // ALPHA_MASK_V87 - kalau semua material mesh ini dikembalikan apa adanya,
      // berarti tidak ada Base Color untuk ditumpangi: jangan dihitung berhasil.
      if(channel==='alphaMaskV87' && replacements.every((r,i)=>r===original[i])) continue;
      mesh.material=Array.isArray(mesh.material)?replacements:replacements[0];
      applied++;"""
s = s.replace(anchor_assign, assign, 1)

# ---------------------------------------------------------------- laporan
anchor_msg = "    if(failedUV) info+=` • UV gagal: ${failedUV}`;"
if anchor_msg not in s:
    raise SystemExit('baris laporan Apply Texture tidak ditemukan')
s = s.replace(anchor_msg,
              anchor_msg + "\n    if(tanpaBaseV87) info+=` • ${tanpaBaseV87} material dilewati: pasang Base Color dulu`;   // ALPHA_MASK_V87", 1)

# Pesan gagal total juga harus menyebut sebabnya, bukan sekadar 'tidak ada mesh'.
anchor_err = "    if(!applied) throw new Error('Tidak ada mesh yang bisa diberi texture');"
if anchor_err not in s:
    raise SystemExit('pesan gagal Apply Texture tidak ditemukan')
s = s.replace(anchor_err,
              "    if(!applied) throw new Error(tanpaBaseV87\n"
              "      ? 'Alpha Mask butuh Base Color lebih dulu - pasang tekstur warnanya, baru topengnya'\n"
              "      : 'Tidak ada mesh yang bisa diberi texture');   // ALPHA_MASK_V87", 1)

p.write_text(s, encoding='utf-8')
print('ALPHA_MASK_V87 applied: saluran Alpha Mask di menu Material')
