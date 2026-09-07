#!/usr/bin/env python3
# TEXTURE_BADGE_V88 - daftar mesh menampilkan peta tekstur yang menempel.
#
# Gejalanya (dilaporkan pengguna): tidak ada cara mengetahui sebuah mesh sudah
# diberi tekstur atau belum, apalagi peta apa saja yang terpasang.
#
# Memang tidak ada. Tiap baris daftar mesh hanya menulis tiga hal:
#
#   nomor • Skinned Mesh • MAT_NYX_HAIR
#
# Sesudah menekan Apply Texture, satu-satunya cara memastikan adalah menebak
# dari tampilan di layar - dan itu gagal justru pada kasus yang paling perlu
# dipastikan. Rambut kemarin contohnya: teksturnya terpasang, kanal alphanya
# ada, tetapi isinya rata 255 sehingga tampilannya sama persis dengan mesh
# yang tidak punya alpha sama sekali.
#
# Baris ketiga ditambahkan, berisi tanda peta yang menempel:
#
#   BC 1024²  N  —  —  E  A
#
#   BC  Base Color, berikut ukuran teksturnya
#   N   Normal Map
#   R   Roughness Map
#   M   Metallic Map
#   E   Emissive Map
#   A   alpha yang benar-benar berlubang
#
# 'A' dinilai dari ISI, bukan dari ada tidaknya kanal alpha. Kanal alpha yang
# rata 255 tidak memotong apa pun, jadi menandainya 'punya alpha' akan
# menyesatkan - persis jebakan yang membuat rambut kemarin sulit didiagnosis.
# Pembacaan isi hanya dilakukan bila material memang menyalakan alphaTest atau
# transparent; tanpa itu alpha tidak dipakai menggambar sehingga tidak perlu
# diperiksa.
#
# Isi tekstur dibaca lewat canvas, dan itu tidak murah pada 32 mesh bertekstur
# 4096. Hasilnya disimpan di texture.userData sehingga satu tekstur hanya
# dibaca sekali, bukan tiap kali daftar digambar ulang. Tekstur yang sama
# dipakai beberapa mesh pun ikut hemat.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'TEXTURE_BADGE_V88' in s:
    raise SystemExit('TEXTURE_BADGE_V88 sudah ada - patch dijalankan dua kali')

# ---------------------------------------------------------------- CSS
anchor_css = ".mesh-layer-meta{font-size:11px;color:var(--muted);margin-top:3px}"
if anchor_css not in s:
    raise SystemExit('CSS mesh-layer-meta tidak ditemukan')
css = (anchor_css +
       "\n/* TEXTURE_BADGE_V88 */"
       "\n.mesh-layer-maps{font-size:10px;margin-top:3px;display:flex;flex-wrap:wrap;gap:5px;align-items:center}"
       ".mesh-layer-maps .pm{padding:1px 4px;border-radius:4px;font-weight:800;letter-spacing:.02em;white-space:nowrap;"
       "background:#16324c;color:#8fd0ff;border:1px solid #2d6ea3}"
       ".mesh-layer-maps .pm.off{background:transparent;color:#54606d;border-color:#2a3542;font-weight:600}"
       ".mesh-layer-maps .pm.alpha{background:#3d2a52;color:#d7aaff;border-color:#6a498f}")
s = s.replace(anchor_css, css, 1)

# ---------------------------------------------------------------- pembaca isi alpha
anchor_fn = "function renderMeshLayers(){"
if anchor_fn not in s:
    raise SystemExit('renderMeshLayers tidak ditemukan')

fn = r"""// TEXTURE_BADGE_V88 - apakah kanal alpha sebuah tekstur benar-benar memotong?
// Kanal alpha yang rata 255 tidak menghilangkan satu piksel pun, jadi menandai
// tekstur seperti itu 'punya alpha' justru menyesatkan. Dibaca dari isinya.
// Hasilnya disimpan di texture.userData: satu tekstur cukup dibaca sekali,
// betapapun sering daftar mesh digambar ulang.
function alphaBerlubangV88(tex){
  if(!tex) return false;
  if(tex.userData && tex.userData.alphaBerlubangV88!==undefined) return tex.userData.alphaBerlubangV88;
  let hasil=false;
  try{
    const img=tex.image;
    if(img && img.width && img.height){
      // Dibaca pada petak kecil saja - cukup untuk membedakan alpha rata dari
      // alpha yang memotong, tanpa memindai jutaan piksel.
      const N=Math.min(128,img.width,img.height);
      const cv=document.createElement('canvas'); cv.width=N; cv.height=N;
      const cx=cv.getContext('2d',{willReadFrequently:true});
      cx.drawImage(img,0,0,N,N);
      const d=cx.getImageData(0,0,N,N).data;
      for(let i=3;i<d.length;i+=4){ if(d[i]<250){hasil=true;break} }
    }
  }catch(e){ hasil=false; }   // tekstur lintas-asal tidak bisa dibaca; jangan sampai daftar ikut gagal
  if(!tex.userData) tex.userData={};
  tex.userData.alphaBerlubangV88=hasil;
  return hasil;
}
/** Baris tanda peta untuk satu mesh. */
function barisPetaV88(mesh){
  const el=document.createElement('div');
  el.className='mesh-layer-maps';
  const mats=Array.isArray(mesh.material)?mesh.material:[mesh.material];
  const m=mats.find(x=>x)||null;
  const tandai=(teks,ada,kelasTambahan)=>{
    const b=document.createElement('span');
    b.className='pm'+(ada?(kelasTambahan?' '+kelasTambahan:''):' off');
    b.textContent=teks;
    el.appendChild(b);
  };
  if(!m){ tandai('tanpa material',false); return el; }
  const peta=m.map;
  const ukuran=peta&&peta.image&&peta.image.width
    ? (peta.image.width===peta.image.height ? peta.image.width+'²'
                                            : peta.image.width+'×'+peta.image.height)
    : '';
  tandai(peta?('BC '+ukuran).trim():'BC', !!peta);
  tandai('N', !!m.normalMap);
  tandai('R', !!m.roughnessMap);
  tandai('M', !!m.metalnessMap);
  tandai('E', !!m.emissiveMap);
  // Alpha hanya diperiksa bila material memang memakainya untuk menggambar.
  const pakaiAlpha=(m.alphaTest>0)||m.transparent===true;
  tandai('A', pakaiAlpha && alphaBerlubangV88(peta), 'alpha');
  return el;
}
function renderMeshLayers(){"""
s = s.replace(anchor_fn, fn, 1)

# ---------------------------------------------------------------- pasang barisnya
anchor_meta = ("    main.querySelector('.mesh-layer-meta').textContent="
               "`${index+1} • ${type}${mesh.material?.name?' • '+mesh.material.name:''}`;")
if anchor_meta not in s:
    raise SystemExit('baris meta daftar mesh tidak ditemukan')
s = s.replace(anchor_meta,
              anchor_meta + "\n    main.appendChild(barisPetaV88(mesh));   // TEXTURE_BADGE_V88", 1)

p.write_text(s, encoding='utf-8')
print('TEXTURE_BADGE_V88 applied: tanda peta tekstur di daftar mesh')
