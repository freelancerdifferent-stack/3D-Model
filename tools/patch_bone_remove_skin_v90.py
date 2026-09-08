#!/usr/bin/env python3
# BONE_REMOVE_SKIN_V90 - Remove bone yang masih dipakai skinning.
#
# Dilaporkan pengguna: menekan Remove bone pada tulang SK_NYX_SHOES hanya
# menghasilkan penolakan "Bone masih dipakai skinning. Hapus weight/rig dulu",
# dan di aplikasi ini tidak ada alat untuk menghapus weight satu tulang. Jadi
# penolakan itu buntu: tidak ada jalan keluar yang ditawarkannya.
#
# v24 menolak karena alasan yang benar. Menghapus tulang yang masih memegang
# bobot tanpa membereskan bobotnya membuat verteksnya menunjuk indeks tulang
# yang sudah tidak ada - mesh-nya rusak saat dianimasikan.
#
# Yang kurang bukan penjagaannya, melainkan langkah sebelumnya: memindahkan
# bobot tulang itu ke induknya lebih dulu (di Blender namanya "dissolve").
# Verteksnya tetap punya total bobot yang sama, hanya berpindah pemilik, jadi
# mesh-nya tidak melar dan tidak ada indeks yang menggantung.
#
# Tulangnya juga dikeluarkan dari skeleton.bones, bukan sekadar dilepas dari
# pohon. Melepasnya dari pohon saja - perlakuan v24 untuk tulang tanpa bobot -
# menyisakan entri yang tidak lagi punya node, dan GLTFExporter membaca larik
# itu apa adanya: processSkin menulis nodeMap.get(bones[i]), yang untuk tulang
# lepas bernilai undefined dan menjadi null di berkas hasilnya. Terukur pada
# L.glb sesudah foot_r dihapus: 5 dari 32 skin punya satu joint null - berkas
# glTF-nya tidak sah.
#
# Karena itu entri tulangnya dibuang dari bones DAN boneInverses, lalu setiap
# skinIndex yang lebih besar dari indeks itu digeser turun satu, pada semua
# mesh yang memakai skeleton bersangkutan. Pergeserannya dikelompokkan menurut
# objek Skeleton, bukan menurut mesh: satu skeleton bisa dipakai banyak mesh,
# dan dua mesh bisa memegang skeleton berbeda yang menaruh tulang yang sama di
# indeks berbeda.
#
# Undo tidak menyimpan salinan indeks seluruh verteks untuk itu, melainkan
# membalik operasinya: tulangnya disisipkan kembali di indeks semula lalu
# setiap indeks >= indeks itu digeser naik satu. Turun-untuk->, naik-untuk-
# kembali adalah kebalikan yang tepat, jadi bolak-balik Undo/Redo tidak
# menggeser apa pun secara diam-diam.
#
# Bobot lama dicatat supaya Undo Skeleton mengembalikannya. Tanpa itu Undo
# hanya memasang kembali tulangnya sementara bobotnya tetap di induk: tulang
# kembali, tetapi tidak lagi menggerakkan apa pun.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'BONE_REMOVE_SKIN_V90' in s:
    raise SystemExit('BONE_REMOVE_SKIN_V90 sudah ada - patch dijalankan dua kali')
if 'recordRemoveV29' not in s:
    raise SystemExit('riwayat skeleton v29 tidak ditemukan - urutan pipeline salah')
if 'removeBoneV24' not in s:
    raise SystemExit('penghapus tulang v24 tidak ditemukan - urutan pipeline salah')

anchor = " removeBoneBtn.onclick=()=>recordRemoveV29(removeBoneV24);"
if anchor not in s:
    raise SystemExit('pengikat tombol Remove bone tidak ditemukan')

js = r""" // BONE_REMOVE_SKIN_V90 - pindahkan bobot ke induk lebih dulu, baru tulangnya dihapus.

 // Induk yang dipakai bukan sekadar bone.parent: yang dicari adalah leluhur
 // terdekat yang benar-benar terdaftar di skeleton mesh ini. Tulang yang tidak
 // ada di larik itu tidak punya indeks, jadi tidak bisa menerima bobot.
 function indukBerangkaV90(skeleton,bone){
   let n=bone&&bone.parent;
   while(n&&n.isBone){
     const i=skeleton.bones.indexOf(n);
     if(i>=0)return {tulang:n,indeks:i};
     n=n.parent;
   }
   return null;
 }
 function meshMemakaiTulangV90(bone){
   const r=activeModelRoot(),keluar=[];
   if(!r||!bone)return keluar;
   r.traverse(o=>{
     if(!o.isSkinnedMesh||!o.skeleton||!o.geometry)return;
     const idx=o.skeleton.bones.indexOf(bone);
     if(idx<0)return;
     const si=o.geometry.getAttribute('skinIndex'), sw=o.geometry.getAttribute('skinWeight');
     if(!si||!sw)return;
     keluar.push({mesh:o,idx});
   });
   return keluar;
 }
 // Catatan bobot ditulis jarang - hanya verteks yang benar-benar berubah - supaya
 // satu entri Undo tidak menyalin seluruh atribut skinning 32 mesh.
 function bacaV90(a,i){return [a.getX(i),a.getY(i),a.getZ(i),a.getW(i)]}
 function tulisV90(a,i,v){a.setXYZW(i,v[0],v[1],v[2],v[3])}

 function pindahBobotKeIndukV90(bone){
   const dipakai=meshMemakaiTulangV90(bone);
   if(!dipakai.length)return {catatan:[],mesh:0,verteks:0,induk:null};
   let namaInduk=null;
   const catatan=[];
   let jumlahVerteks=0;
   for(const pakai of dipakai){
     const mesh=pakai.mesh, idx=pakai.idx;
     const induk=indukBerangkaV90(mesh.skeleton,bone);
     if(!induk){
       // Belum ada yang diubah pada mesh ini, tetapi mesh sebelumnya sudah -
       // kembalikan semuanya supaya tidak tertinggal setengah jadi.
       pasangBobotV90(catatan,true);
       return {gagal:mesh.name||'mesh tanpa nama'};
     }
     namaInduk=induk.tulang.name||'induk';
     const si=mesh.geometry.getAttribute('skinIndex'), sw=mesh.geometry.getAttribute('skinWeight');
     const verteks=[],sebelum=[],sesudah=[];
     for(let i=0;i<si.count;i++){
       const bi=bacaV90(si,i), bw=bacaV90(sw,i);
       let kena=false;
       for(let c=0;c<4;c++)if(bi[c]===idx&&bw[c]>0){kena=true;break}
       if(!kena)continue;
       const ni=bi.slice(), nw=bw.slice();
       for(let c=0;c<4;c++)if(ni[c]===idx)ni[c]=induk.indeks;
       // Setelah dialihkan, satu verteks bisa menyebut induk dua kali. Slot kembar
       // dijumlahkan lalu dikosongkan; totalnya tetap, jadi tidak perlu dinormalkan
       // ulang dan bentuk mesh di pose bind tidak berubah.
       for(let a=0;a<4;a++){
         if(nw[a]<=0)continue;
         for(let b=a+1;b<4;b++){
           if(nw[b]>0&&ni[b]===ni[a]){nw[a]+=nw[b];nw[b]=0;ni[b]=0}
         }
       }
       verteks.push(i);sebelum.push(bi.concat(bw));sesudah.push(ni.concat(nw));
       tulisV90(si,i,ni);tulisV90(sw,i,nw);
     }
     if(!verteks.length)continue;
     si.needsUpdate=true;sw.needsUpdate=true;
     catatan.push({mesh:mesh,verteks:verteks,sebelum:sebelum,sesudah:sesudah});
     jumlahVerteks+=verteks.length;
   }
   return {catatan:catatan,mesh:catatan.length,verteks:jumlahVerteks,induk:namaInduk};
 }
 function pasangBobotV90(catatan,kembalikan){
   if(!catatan)return;
   for(const c of catatan){
     const g=c.mesh&&c.mesh.geometry;if(!g)continue;
     const si=g.getAttribute('skinIndex'), sw=g.getAttribute('skinWeight');
     if(!si||!sw)continue;
     const sumber=kembalikan?c.sebelum:c.sesudah;
     for(let k=0;k<c.verteks.length;k++){
       const v=sumber[k];
       si.setXYZW(c.verteks[k],v[0],v[1],v[2],v[3]);
       sw.setXYZW(c.verteks[k],v[4],v[5],v[6],v[7]);
     }
     si.needsUpdate=true;sw.needsUpdate=true;
   }
 }

 // Kelompokkan menurut objek Skeleton: satu skeleton dipakai banyak mesh, dan
 // dua mesh bisa memegang skeleton berbeda yang menaruh tulang sama di indeks
 // berbeda. skinIndex sebuah mesh selalu menunjuk larik skeleton-nya sendiri.
 function kelompokRangkaV90(bone){
   const r=activeModelRoot(),kel=new Map();
   if(!r||!bone)return kel;
   r.traverse(o=>{
     if(!o.isSkinnedMesh||!o.skeleton||!o.geometry)return;
     const idx=o.skeleton.bones.indexOf(bone);
     if(idx<0)return;
     if(!kel.has(o.skeleton))kel.set(o.skeleton,{idx:idx,mesh:[]});
     kel.get(o.skeleton).mesh.push(o);
   });
   return kel;
 }
 // arah -1 dipakai saat tulangnya dibuang (indeks > idx turun satu), +1 saat
 // disisipkan kembali (indeks >= idx naik satu). Slot berindeks idx sendiri
 // sengaja tidak disentuh: bobotnya sudah nol, dan membiarkannya membuat
 // kedua arah menjadi kebalikan yang tepat.
 function geserIndeksV90(mesh,idx,arah){
   const si=mesh.geometry&&mesh.geometry.getAttribute('skinIndex');
   if(!si)return;
   for(let i=0;i<si.count;i++){
     const v=[si.getX(i),si.getY(i),si.getZ(i),si.getW(i)];
     let ubah=false;
     for(let c=0;c<4;c++){
       if(arah<0){ if(v[c]>idx){v[c]-=1;ubah=true} }
       else { if(v[c]>=idx){v[c]+=1;ubah=true} }
     }
     if(ubah)si.setXYZW(i,v[0],v[1],v[2],v[3]);
   }
   si.needsUpdate=true;
 }
 // init() mengalokasikan ulang boneMatrices sesuai jumlah tulang yang baru, dan
 // mempertahankan boneInverses selama jumlahnya cocok - jadi keduanya harus
 // di-splice berpasangan. boneTexture lama tidak ikut disegarkan olehnya dan
 // ukurannya kini salah, jadi dibuang supaya dibuat ulang (pelajaran v85).
 function segarkanRangkaV90(sk){
   try{ sk.init() }catch(_){}
   if(sk.boneTexture){ try{ sk.boneTexture.dispose() }catch(_){} sk.boneTexture=null }
 }
 function padatkanRangkaV90(bone){
   const kel=kelompokRangkaV90(bone),catatan=[];
   for(const pasangan of kel){
     const sk=pasangan[0], info=pasangan[1];
     const balikan=sk.boneInverses?sk.boneInverses[info.idx]:null;
     sk.bones.splice(info.idx,1);
     if(sk.boneInverses)sk.boneInverses.splice(info.idx,1);
     for(const m of info.mesh)geserIndeksV90(m,info.idx,-1);
     segarkanRangkaV90(sk);
     catatan.push({skeleton:sk,idx:info.idx,balikan:balikan,mesh:info.mesh});
   }
   return catatan;
 }
 function kembalikanRangkaV90(catatan,bone){
   for(let k=catatan.length-1;k>=0;k--){
     const c=catatan[k];
     c.skeleton.bones.splice(c.idx,0,bone);
     if(c.skeleton.boneInverses)c.skeleton.boneInverses.splice(c.idx,0,c.balikan);
     for(const m of c.mesh)geserIndeksV90(m,c.idx,+1);
     segarkanRangkaV90(c.skeleton);
   }
 }
 function buangRangkaV90(catatan,bone){
   for(const c of catatan){
     const i=c.skeleton.bones.indexOf(bone);
     if(i<0)continue;
     c.skeleton.bones.splice(i,1);
     if(c.skeleton.boneInverses)c.skeleton.boneInverses.splice(i,1);
     for(const m of c.mesh)geserIndeksV90(m,i,-1);
     segarkanRangkaV90(c.skeleton);
   }
 }
 // Undo membuka pemadatan lebih dulu supaya ruang indeksnya kembali seperti
 // semula, baru bobot lamanya ditulis - catatan bobot memakai indeks lama.
 // Redo urutannya kebalikannya.
 function pasangV90(rec,kembalikan){
   if(!rec)return;
   if(kembalikan){
     kembalikanRangkaV90(rec.padat,rec.tulang);
     pasangBobotV90(rec.bobot,true);
   }else{
     pasangBobotV90(rec.bobot,false);
     buangRangkaV90(rec.padat,rec.tulang);
   }
 }

 // Catatan dititipkan lewat variabel ini karena entri riwayatnya dibuat oleh
 // recordRemoveV29, bukan oleh kode di sini.
 let titipanV90=null;
 const pushLamaV90=pushV29;
 pushV29=function(entry){
   if(entry&&entry.kind==='remove'&&titipanV90){entry.bobotV90=titipanV90;titipanV90=null}
   return pushLamaV90.apply(this,arguments);
 };
 const terapkanLamaV90=applyEntryV29;
 applyEntryV29=function(e,undoing){
   const ok=terapkanLamaV90.apply(this,arguments);
   if(ok&&e&&e.kind==='remove'&&e.bobotV90)pasangV90(e.bobotV90,!!undoing);
   return ok;
 };

 function removeBoneV90(){
   titipanV90=null;
   if(!skeletonLiveEditMode||!selectedBone){msg('Pilih bone dulu');return}
   const bone=selectedBone, nama=bone.name||'Bone';
   if(!bone.parent){msg('Root bone tidak dapat dihapus');return}
   if(!selectedBoneReferencedBySkinV24(bone)){
     // Tanpa bobot pun entrinya harus dikeluarkan dari skeleton.bones, kalau
     // tidak berkas hasil Export tetap punya joint null.
     removeBoneV24();
     if(!bone.parent){
       const padatKosong=padatkanRangkaV90(bone);
       if(padatKosong.length)titipanV90={bobot:[],padat:padatKosong,tulang:bone};
     }
     return;
   }
   const hasil=pindahBobotKeIndukV90(bone);
   if(hasil.gagal){
     msg('Bone '+nama+' tidak punya induk di rangka '+hasil.gagal+'. Bobotnya tidak ada yang menampung');
     return;
   }
   if(selectedBoneReferencedBySkinV24(bone)){
     pasangBobotV90(hasil.catatan,true);
     msg('Bobot bone '+nama+' tidak bisa dipindahkan seluruhnya. Tidak ada yang diubah');
     return;
   }
   removeBoneV24();
   if(bone.parent){pasangBobotV90(hasil.catatan,true);return}   // penghapusan ditolak
   const padat=padatkanRangkaV90(bone);
   titipanV90={bobot:hasil.catatan,padat:padat,tulang:bone};
   msg('Bone '+nama+' dihapus • bobot '+hasil.verteks+' verteks di '+hasil.mesh+
       ' mesh dipindah ke '+(hasil.induk||'induk')+' • Undo mengembalikan keduanya');
 }
 removeBoneBtn.onclick=()=>recordRemoveV29(removeBoneV90);
"""

s = s.replace(anchor, js, 1)
p.write_text(s, encoding='utf-8')
print('BONE_REMOVE_SKIN_V90 applied: Remove bone memindahkan bobot ke induk lebih dulu')
