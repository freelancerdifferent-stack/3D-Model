#!/usr/bin/env python3
# RIG_ALL_V86 - tombol "All Rig": sambungkan semua mesh sekaligus ke rangka model.
#
# Gejalanya (dilaporkan pengguna, lalu direproduksi dan diukur di Chromium):
# sesudah SK_NYX_nude.fbx diimpor lalu SK_F_LINGERIE_BRA.fbx dipasang lewat Add
# Mesh, BRA diam di tempat ketika animasi diputar.
#
#   SK_NYX_BODY_FULL (bawaan model) ikut tulang spine_05 diputar 40°  -> 10.10
#   SK_F_LINGERIE_BRA                                                 ->  0.00
#
#   rangka BRA: 145 tulang, nama identik dengan model,
#               objek yang benar-benar sama: 0, terpisah semua: 145
#   akar tulang BRA menempel di 'root_$AssimpFbx$_PreRotation'
#
# Sebabnya: berkas FBX per-bagian membawa SALINAN LENGKAP pohon tulangnya
# sendiri. Mesh tambahan terikat ke salinan miliknya, bukan ke rangka model,
# sehingga animasi yang menggerakkan tulang model tidak pernah menyentuhnya.
# Bind senjata tidak ada hubungannya - diukur, BRA tetap 0.00 bahkan tanpa
# senjata sama sekali.
#
# Peleburan rangka duplikat sebenarnya sudah dijalankan saat impor model utama
# (prepFbxV55), tetapi Add Mesh memakai jalur Assimp dan tidak pernah
# melewatinya. Itulah sebabnya '$AssimpFbx$' masih tersisa di pohon BRA.
#
# Tombol ini menyelesaikannya dalam satu ketukan, dan sengaja MANUAL - bukan
# otomatis saat Add Mesh - supaya perilaku Add Mesh yang sekarang tidak berubah
# dan pengguna yang menentukan kapan penyambungan terjadi.
#
# Cara kerjanya:
#   1. Rangka model = milik mesh ber-skin pertama yang ditemukan. Add Mesh
#      selalu menempel sebagai anak terakhir, jadi yang datang lebih dulu -
#      model yang diimpor - selalu tersentuh lebih dahulu.
#   2. Tiap mesh yang memakai pohon lain dipetakan per nama ke tulang model.
#   3. PAGAR: hanya dilebur bila rest pose kedua pohon berimpit dalam batas
#      epsilon (2% ukuran model), dan hanya tulang yang berbobot yang
#      diperiksa. Kalau meleset, mesh itu dilewati dan
#      dilaporkan - model tidak diacak diam-diam.
#   4. boneInverses milik mesh dipertahankan apa adanya; itu sah justru karena
#      pagar di langkah 3 sudah memastikan rest pose-nya sama.
#   5. Pohon tulang duplikat yang sudah tidak dirujuk siapa pun dibuang.
#
# Mesh polos tanpa bobot (senjata, aksesori) TIDAK ikut disambung: tidak ada
# cara menebak tulang mana yang seharusnya memegangnya. Mesh seperti itu
# dihitung dan dilaporkan agar dikerjakan manual lewat Apply Weight + Bind.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'RIG_ALL_V86' in s:
    raise SystemExit('RIG_ALL_V86 sudah ada - patch dijalankan dua kali')
if 'RIG_MESH_LIST_V84' not in s:
    raise SystemExit('mesin v84 tidak ditemukan - urutan pipeline salah')

# ---------------------------------------------------------------- CSS
anchor_css = ("#rigWorkspaceV26 #rigMeshListV84 .rig-item-tag{flex:none;font-size:11px;"
              "font-weight:700;padding:2px 7px;border-radius:999px;background:#4a3410;color:#ffce7a}\n")
if anchor_css not in s:
    raise SystemExit('blok CSS daftar mesh v84 tidak ditemukan')
css = """/* RIG_ALL_V86 */
#rigWorkspaceV26 #rigAllV86{width:100%;min-height:46px;margin-top:9px;border-radius:10px;border:1px solid #6a4bd0;background:linear-gradient(180deg,#4b34a8,#35257a);color:#efe8ff;font-size:14px;font-weight:800;letter-spacing:.04em}
#rigWorkspaceV26 #rigAllV86:active{transform:scale(0.985)}
#rigWorkspaceV26 #rigAllV86[disabled]{opacity:.5}
"""
s = s.replace(anchor_css, anchor_css + css, 1)

# ---------------------------------------------------------------- markup
anchor_html = '     <div id="rigMeshListV84" hidden></div>\n'
if anchor_html not in s:
    raise SystemExit('markup daftar mesh v84 tidak ditemukan')
html = '     <button id="rigAllV86" type="button">All Rig — sambungkan semua mesh</button>\n'
s = s.replace(anchor_html, anchor_html + html, 1)

# ---------------------------------------------------------------- JS
anchor_js = " function skinnedMeshesV26(){"
if anchor_js not in s:
    raise SystemExit('titik sisip fungsi rig v26 tidak ditemukan')

js = r""" // RIG_ALL_V86 - sambungkan semua mesh sekaligus ke rangka model.
 function akarTulangV86(b){let n=b;while(n&&n.parent&&n.parent.isBone)n=n.parent;return n}
 function kelompokRangkaV86(){
   const r=activeModelRoot();if(!r)return null;
   const kel=new Map();
   r.traverse(o=>{
     if(!o.isSkinnedMesh||!o.skeleton||!o.skeleton.bones.length)return;
     const a=akarTulangV86(o.skeleton.bones[0]);if(!a)return;
     if(!kel.has(a))kel.set(a,[]);kel.get(a).push(o);
   });
   return kel.size?kel:null;
 }
 /** Pohon tulang milik model = milik mesh ber-skin PERTAMA yang ditemukan saat
  *  menelusuri model dari akarnya.
  *
  *  Bukan "yang dipakai paling banyak mesh": aturan itu terbalik begitu berkas
  *  tambahan membawa lebih banyak mesh daripada modelnya. Terukur - nude 8 mesh
  *  ditambah AllPartsTogether 41 mesh menghasilkan kelompok [8, 41], dan
  *  jumlah terbanyak memilih pohon berkas tambahan, sehingga MODEL yang
  *  dipindahkan ke rangka pendatang. Terbalik sama sekali.
  *
  *  Bukan pula "yang tulangnya terbanyak": berkas per-bagian bisa membawa pohon
  *  lebih besar daripada milik model (BRA 145 tulang, model 129).
  *
  *  Urutan penelusuran menjawabnya tanpa menghitung apa pun. Add Mesh
  *  menempelkan objeknya sebagai anak TERAKHIR dari akar model, jadi apa pun
  *  yang datang lebih dulu - yaitu model yang diimpor - selalu tersentuh lebih
  *  dahulu. Yang pertama ditemukan adalah tuan rumah. */
 function pohonModelV86(){
   const r=activeModelRoot();if(!r)return null;
   let pertama=null;
   r.traverse(o=>{ if(pertama)return;
     if(o.isSkinnedMesh&&o.skeleton&&o.skeleton.bones.length)pertama=o; });
   if(!pertama)return null;
   const akar=akarTulangV86(pertama.skeleton.bones[0]);
   if(!akar)return null;
   const peta=new Map();akar.traverse(x=>{if(x.isBone&&!peta.has(x.name))peta.set(x.name,x)});
   return {akar,peta};
 }
 /** Indeks tulang yang benar-benar berbobot pada sebuah mesh. Mengembalikan
  *  null bila mesh tidak punya atribut skin, supaya pemanggil memeriksa semua
  *  tulang alih-alih menganggap tak ada yang dipakai. */
 function tulangTerpakaiV86(mesh){
   const g=mesh.geometry,si=g&&g.getAttribute&&g.getAttribute('skinIndex'),sw=g&&g.getAttribute('skinWeight');
   if(!si||!sw)return null;
   const set=new Set();
   for(let i=0;i<si.count;i++){
     if(sw.getX(i)>0.001)set.add(si.getX(i));
     if(sw.getY(i)>0.001)set.add(si.getY(i));
     if(sw.getZ(i)>0.001)set.add(si.getZ(i));
     if(sw.getW(i)>0.001)set.add(si.getW(i));
   }
   return set;
 }
 function batasImpitV86(){
   const r=activeModelRoot();if(!r)return 1;
   const b=new THREE.Box3().setFromObject(r);if(b.isEmpty())return 1;
   const s=b.getSize(new THREE.Vector3());
   return Math.max(0.001,Math.max(s.x,s.y,s.z)*0.02);   // 2% ukuran model
 }
 function semuaRigV86(){
   if(!skeletonRigModeV26)return;
   const kel=kelompokRangkaV86();
   if(!kel){msg('Model belum punya mesh ber-skin');return}
   const model=pohonModelV86();
   if(!model){msg('Rangka model tidak ditemukan');return}
   const eps=batasImpitV86(),pa=new THREE.Vector3(),pb=new THREE.Vector3();
   let disambung=0,dilewatiNama=0,dilewatiPose=0,sudahBenar=0,pesanPose='';
   for(const [akar,daftar] of kel){
     if(akar===model.akar){sudahBenar+=daftar.length;continue}
     for(const m of daftar){
       const bs=m.skeleton.bones,kanon=[];let lengkap=true;
       for(const b of bs){const c=model.peta.get(b.name);if(!c){lengkap=false;break}kanon.push(c)}
       if(!lengkap){dilewatiNama++;continue}
       // Pagar rest pose: tulang duplikat harus berimpit dengan tulang model,
       // karena boneInverses milik mesh hanya sah dipakai pada tulang model
       // bila rest pose keduanya sama. Kalau meleset, hasilnya terpelintir.
       //
       // Yang diperiksa HANYA tulang yang benar-benar dipakai mesh itu
       // (bobot > 0). Tulang berbobot nol tidak dapat menggeser satu vertex
       // pun, jadi selisihnya tidak relevan. Diukur pada SK_NYX.glb + bra:
       // selisih terburuk keseluruhan 50.43 (nyx_ponytail_07 31.03,
       // thumb_03_r 30.93 - rambut dan jari, yang tidak disentuh bra sama
       // sekali), sedangkan di antara tulang yang dipakai bra terburuknya
       // hanya 2.96 (upperarm_twist_01_r). Memeriksa semua tulang menolak
       // penggabungan yang sebenarnya aman.
       const terpakai=tulangTerpakaiV86(m);
       let meleset=0,tulangMeleset='';
       for(let i=0;i<bs.length;i++){
         if(terpakai&&!terpakai.has(i))continue;
         bs[i].updateMatrixWorld(true);kanon[i].updateMatrixWorld(true);
         pa.setFromMatrixPosition(bs[i].matrixWorld);pb.setFromMatrixPosition(kanon[i].matrixWorld);
         const d=pa.distanceTo(pb);
         if(d>meleset){meleset=d;tulangMeleset=bs[i].name||('tulang '+i)}
       }
       if(meleset>eps){
         dilewatiPose++;
         if(!pesanPose)pesanPose=tulangMeleset+' meleset '+meleset.toFixed(2)+' (batas '+eps.toFixed(2)+')';
         continue;
       }
       for(let i=0;i<bs.length;i++)bs[i]=kanon[i];
       try{m.skeleton.init()}catch(_){}
       // Daftar tulang berubah isinya, jadi boneTexture lama memegang larik
       // yang sudah tidak dipakai - sebab yang sama seperti RIG_BONETEXTURE_V85.
       try{if(m.skeleton.boneTexture){m.skeleton.boneTexture.dispose();m.skeleton.boneTexture=null}}catch(_){}
       try{m.skeleton.update()}catch(_){}
       m.frustumCulled=false;
       disambung++;
     }
   }
   // Pohon duplikat yang sudah tidak dirujuk skeleton mana pun dibuang, supaya
   // tidak ada tulang hantu yang ikut terbaca saat memilih bone atau menggambar.
   const dipakai=new Set();
   const r=activeModelRoot();
   if(r)r.traverse(o=>{if(o.isSkinnedMesh&&o.skeleton)for(const b of o.skeleton.bones)dipakai.add(b)});
   let dibuang=0;
   for(const [akar] of kel){
     if(akar===model.akar)continue;
     let masihDipakai=false;akar.traverse(x=>{if(dipakai.has(x))masihDipakai=true});
     if(!masihDipakai&&akar.parent){akar.parent.remove(akar);dibuang++}
   }
   // Mesh polos tanpa bobot tidak bisa disambung otomatis: tulangnya tak
   // tertebak. Dihitung agar pengguna tahu mana yang masih harus manual.
   let polos=0;
   if(r)r.traverse(o=>{if(o.isMesh&&!o.isSkinnedMesh)polos++});
   refreshHelper();setSkeletonVisible(true);
   if(typeof rebuildSkeletonVisualV23==='function')rebuildSkeletonVisualV23();
   if(typeof updateSkeletonVisualV23==='function')updateSkeletonVisualV23();
   const bagian=[disambung+' mesh disambung'];
   if(sudahBenar)bagian.push(sudahBenar+' sudah benar');
   if(dilewatiNama)bagian.push(dilewatiNama+' nama tulang tak cocok');
   if(dilewatiPose)bagian.push(dilewatiPose+' rest pose beda'+(pesanPose?(' ('+pesanPose+')'):''));
   if(polos)bagian.push(polos+' mesh polos perlu Bind manual');
   if(dibuang)bagian.push(dibuang+' pohon duplikat dibuang');
   rigStatusV26.textContent=bagian.join(' • ');
   msg(disambung?('All Rig: '+disambung+' mesh tersambung ke rangka model'):'All Rig: tidak ada yang perlu disambung');
 }
 $('rigAllV86').onclick=semuaRigV86;
 window.__rigAllV86=semuaRigV86;

"""
s = s.replace(anchor_js, js + anchor_js, 1)

p.write_text(s, encoding='utf-8')
print('RIG_ALL_V86 applied: tombol All Rig menyambungkan semua mesh ke rangka model')
