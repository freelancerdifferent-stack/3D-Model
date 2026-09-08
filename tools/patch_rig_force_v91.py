#!/usr/bin/env python3
# RIG_FORCE_V91 - "Bind Paksa": pasang mesh apa pun ke rangka model apa pun.
#
# Dilaporkan pengguna: sepatu model A dulu bisa di-bind; sesudah bone model A
# diubah, sepatu yang sama tidak mau di-bind lagi. Maunya: mesh apa pun,
# digabung ke model apa pun, bind tetap jalan, tidak peduli tulangnya.
#
# All Rig (v86) memang menolak, lewat dua pagar, dan keduanya sah untuk apa
# yang dikerjakannya - ia MENCOCOKKAN rangka lama mesh ke rangka model:
#
#   1. nama    - tiap tulang di rangka mesh harus ada namanya di rangka model.
#                Diperiksa untuk SEMUA tulang, termasuk yang berbobot nol.
#                Rangka sepatu punya 12 tulang, hanya 6 yang dipakai; satu
#                nama hilang saja - termasuk nama yang tidak pernah menggerakkan
#                satu vertex pun - dan penggabungan ditolak.
#   2. rest pose - tulang mesh harus berimpit dengan tulang model, karena
#                boneInverses milik mesh hanya sah dipakai pada tulang model
#                bila rest pose keduanya sama. Begitu bone model digeser atau
#                diputar, syarat itu batal.
#
# Mesin ini tidak menambal kedua pagar itu dan tidak menyentuh All Rig sama
# sekali. Ia menempuh jalan lain yang membuat kedua syarat tadi tidak pernah
# ada:
#
#   - skinIndex dan skinWeight TIDAK disentuh. Bobot lama dipakai apa adanya.
#     Menghitung ulang bobot justru merusak: bentuk tekukan yang sudah benar
#     hilang, dan hasilnya berantakan.
#   - yang ditukar hanya ISI daftar tulang. Slot ke-i di rangka mesh diisi
#     tulang milik model. Karena bobot menunjuk NOMOR slot, bukan tulang,
#     menukar isinya sudah cukup - tidak ada satu bobot pun yang berubah.
#   - slot dicocokkan lewat nama bila namanya ada; bila tidak ada, dipakai
#     tulang model yang posisinya PALING DEKAT. Karena itu nama tidak pernah
#     bisa menggagalkan apa pun.
#   - sesudah daftarnya jadi, mesh di-bind ulang dengan Skeleton BARU berisi
#     tulang model. Skeleton baru menghitung boneInverses dari pose tulang
#     model saat ini, jadi syarat "rest pose harus berimpit" hilang dengan
#     sendirinya: pose model sekarang MENJADI bind pose mesh itu.
#
# Yang sengaja TIDAK dikerjakan: pohon tulang bawaan mesh tidak dihapus,
# meski sesudah ini tidak dirujuk skeleton mana pun. Menghapus tulang adalah
# tindakan yang tidak bisa dibatalkan, dan pengguna tidak memintanya.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'RIG_FORCE_V91' in s:
    raise SystemExit('RIG_FORCE_V91 sudah ada - patch dijalankan dua kali')
if 'RIG_ALL_V86' not in s:
    raise SystemExit('mesin All Rig v86 tidak ditemukan - urutan pipeline salah')

# ---------------------------------------------------------------- CSS
anchor_css = "#rigWorkspaceV26 #rigAllV86[disabled]{opacity:.5}\n"
if anchor_css not in s:
    raise SystemExit('blok CSS All Rig v86 tidak ditemukan')
css = """/* RIG_FORCE_V91 */
#rigWorkspaceV26 #rigForceV91{width:100%;min-height:46px;margin-top:8px;border-radius:10px;border:1px solid #1f7a5a;background:linear-gradient(180deg,#17694e,#0f4d39);color:#e6fff5;font-size:14px;font-weight:800;letter-spacing:.04em}
#rigWorkspaceV26 #rigForceV91:active{transform:scale(0.985)}
#rigWorkspaceV26 #rigForceV91[disabled]{opacity:.5}
"""
s = s.replace(anchor_css, anchor_css + css, 1)

# ---------------------------------------------------------------- markup
anchor_html = '     <button id="rigAllV86" type="button">All Rig — sambungkan semua mesh</button>\n'
if anchor_html not in s:
    raise SystemExit('tombol All Rig v86 tidak ditemukan')
html = '     <button id="rigForceV91" type="button">Bind Paksa — abaikan nama &amp; rest pose</button>\n'
s = s.replace(anchor_html, anchor_html + html, 1)

# ---------------------------------------------------------------- JS
anchor_js = " function skinnedMeshesV26(){"
if anchor_js not in s:
    raise SystemExit('titik sisip fungsi rig v26 tidak ditemukan')

js = r""" // RIG_FORCE_V91 - pasang mesh apa pun ke rangka model apa pun.
 function akarRangkaV91(b){let n=b;while(n&&n.parent&&n.parent.isBone)n=n.parent;return n}

 /** Rangka model = milik mesh ber-skin PERTAMA saat model ditelusuri dari
  *  akarnya. Mesh yang baru ditambahkan lewat Add Mesh selalu masuk paling
  *  belakang, jadi yang pertama ditemukan adalah model itu sendiri. */
 function rangkaModelV91(){
   const r=activeModelRoot();if(!r)return null;
   let awal=null;
   r.traverse(o=>{ if(awal)return;
     if(o.isSkinnedMesh&&o.skeleton&&o.skeleton.bones.length)awal=o; });
   if(!awal)return null;
   const akar=akarRangkaV91(awal.skeleton.bones[0]);
   if(!akar)return null;
   const peta=new Map(), daftar=[];
   akar.traverse(x=>{ if(!x.isBone)return; daftar.push(x); if(!peta.has(x.name))peta.set(x.name,x) });
   return {akar:akar,peta:peta,daftar:daftar,rangka:awal.skeleton};
 }
 // GLTFLoader menomori ulang simpul bernama sama menjadi nama_1, nama_2, jadi
 // nama persis dicoba lebih dulu, baru namanya tanpa akhiran nomor.
 function namaTulangV91(peta,nama){
   const tepat=peta.get(nama); if(tepat)return tepat;
   const dasar=String(nama||'').replace(/_\d+$/,'');
   return dasar!==nama?peta.get(dasar):undefined;
 }
 function terdekatV91(daftar,tulang,pa,pb){
   tulang.updateMatrixWorld(true);
   pa.setFromMatrixPosition(tulang.matrixWorld);
   let pilih=null,jarak=Infinity;
   for(const c of daftar){
     c.updateMatrixWorld(true);
     pb.setFromMatrixPosition(c.matrixWorld);
     const d=pa.distanceToSquared(pb);
     if(d<jarak){jarak=d;pilih=c}
   }
   return pilih;
 }
 /** Slot mana saja yang benar-benar memegang bobot. Slot berbobot nol tidak
  *  dapat menggeser satu vertex pun, jadi salah-cocok di situ tidak berakibat
  *  apa-apa - tetapi tetap harus diisi tulang yang sah. */
 function slotTerpakaiV91(mesh){
   const g=mesh.geometry, si=g&&g.getAttribute('skinIndex'), sw=g&&g.getAttribute('skinWeight');
   if(!si||!sw)return null;
   const pakai=new Set();
   for(let i=0;i<si.count;i++){
     if(sw.getX(i)>0)pakai.add(si.getX(i));
     if(sw.getY(i)>0)pakai.add(si.getY(i));
     if(sw.getZ(i)>0)pakai.add(si.getZ(i));
     if(sw.getW(i)>0)pakai.add(si.getW(i));
   }
   return pakai;
 }
 function pasangPaksaV91(){
   if(!skeletonRigModeV26)return;
   const model=rangkaModelV91();
   if(!model){msg('Model belum punya mesh ber-skin');return}
   const r=activeModelRoot();
   if(!r){msg('Model tidak ditemukan');return}
   r.updateMatrixWorld(true);

   const sasaran=[];
   r.traverse(o=>{
     if(!o.isSkinnedMesh||!o.skeleton||!o.skeleton.bones.length)return;
     if(akarRangkaV91(o.skeleton.bones[0])===model.akar)return;   // sudah memakai rangka model
     sasaran.push(o);
   });
   if(!sasaran.length){msg('Bind Paksa: semua mesh sudah memakai rangka model');return}

   const pa=new THREE.Vector3(), pb=new THREE.Vector3();
   let kena=0, lewatNama=0, lewatDekat=0, gagal=0, contoh='';
   for(const m of sasaran){
     const lama=m.skeleton.bones, baru=[];
     const pakai=slotTerpakaiV91(m);
     let cocokNama=0, cocokDekat=0, kosong=0;
     for(let i=0;i<lama.length;i++){
       const b=lama[i];
       let c=b?namaTulangV91(model.peta,b.name):null;
       if(c){cocokNama++}
       else{
         c=b?terdekatV91(model.daftar,b,pa,pb):model.daftar[0];
         if(c)cocokDekat++; else kosong++;
       }
       baru.push(c||model.daftar[0]);
     }
     if(kosong||!baru.length){gagal++;continue}
     try{
       // Skeleton baru menghitung boneInverses dari pose tulang model SEKARANG,
       // jadi pose model sekarang menjadi bind pose mesh ini. Itulah yang
       // membuat perbedaan rest pose tidak lagi berarti apa-apa.
       const rangka=new THREE.Skeleton(baru);
       m.updateMatrixWorld(true);
       m.bind(rangka,m.matrixWorld);
       rangka.update();
       m.frustumCulled=false;    // mesh ber-skin bisa keluar kotak batas bind
     }catch(e){gagal++;continue}
     kena++;
     lewatNama+=cocokNama; lewatDekat+=cocokDekat;
     if(!contoh)contoh=(m.name||'mesh')+': '+cocokNama+' lewat nama, '+cocokDekat+' lewat tulang terdekat'
                       +(pakai?(' • '+pakai.size+' slot berbobot'):'');
   }
   refreshHelper();setSkeletonVisible(true);
   if(typeof rebuildSkeletonVisualV23==='function')rebuildSkeletonVisualV23();
   if(typeof updateSkeletonVisualV23==='function')updateSkeletonVisualV23();
   const bagian=[kena+' mesh dipasang ke rangka model'];
   if(contoh)bagian.push(contoh);
   if(gagal)bagian.push(gagal+' mesh gagal');
   bagian.push('bobot tidak diubah');
   rigStatusV26.textContent=bagian.join(' • ');
   msg(kena?('Bind Paksa: '+kena+' mesh dipasang, bobot lama dipakai apa adanya')
           :'Bind Paksa: tidak ada yang bisa dipasang');
 }
 $('rigForceV91').onclick=pasangPaksaV91;
 window.__rigForceV91=pasangPaksaV91;

"""
s = s.replace(anchor_js, js + anchor_js, 1)

p.write_text(s, encoding='utf-8')
print('RIG_FORCE_V91 applied: tombol Bind Paksa memasang mesh apa pun ke rangka model')
