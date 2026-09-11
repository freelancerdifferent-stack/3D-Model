#!/usr/bin/env python3
# RIG_FORCE_TIDY_V92 - buang pohon tulang bawaan mesh yang sudah tidak dipakai
# sesudah Bind Paksa.
#
# Sesudah v91 memasang mesh ke rangka model, pohon tulang bawaan mesh itu
# tidak lagi dirujuk skeleton mana pun - tetapi masih menempel di model dan
# masih tergambar di mode Skeleton, sehingga tulang model dan tulang hantu
# bertumpuk di layar dan sama-sama bisa tersentuh saat memilih bone.
#
# v91 sengaja tidak membuangnya karena menghapus tulang tidak bisa dibatalkan
# dan waktu itu tidak diminta. Sekarang diminta.
#
# Pagarnya dibuat sesempit mungkin, karena ini tindakan yang menghapus:
#
#   1. Hanya pohon yang SEBELUM Bind Paksa memang akar rangka asing - dicatat
#      lebih dulu, sebab sesudah dipasang pohon itu tidak bisa ditemukan lagi
#      lewat skeleton mana pun.
#   2. Hanya bila SESUDAHNYA tidak satu pun tulang di dalam pohon itu dirujuk
#      oleh skeleton mesh ber-skin mana pun di model.
#   3. Akar rangka model tidak pernah masuk daftar calon.
#
# Kalau Bind Paksa tidak jadi memasang apa-apa, mesh-nya masih memegang
# tulangnya sendiri, syarat kedua gagal, dan tidak ada yang dibuang. Jadi
# pembersihan ini tidak pernah berjalan sendiri tanpa pemasangan yang berhasil.
#
# Bone yang sedang terpilih ikut dilepas kalau kebetulan berada di pohon yang
# dibuang, supaya tidak ada acuan ke tulang yang sudah lepas dari model.
#
# v91 mengikat tombolnya dengan nilai fungsi, jadi yang diikat ulang di sini
# adalah TOMBOLNYA, bukan cukup menimpa nama fungsinya.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'RIG_FORCE_TIDY_V92' in s:
    raise SystemExit('RIG_FORCE_TIDY_V92 sudah ada - patch dijalankan dua kali')
if 'RIG_FORCE_V91' not in s:
    raise SystemExit('mesin Bind Paksa v91 tidak ditemukan - urutan pipeline salah')

anchor = " $('rigForceV91').onclick=pasangPaksaV91;\n window.__rigForceV91=pasangPaksaV91;\n"
if anchor not in s:
    raise SystemExit('pengikat tombol Bind Paksa v91 tidak ditemukan')

js = r""" // RIG_FORCE_TIDY_V92 - pohon tulang bawaan mesh dibuang bila sudah tidak dirujuk.

 /** Akar rangka yang BUKAN milik model, dicatat sebelum pemasangan. Sesudah
  *  dipasang, pohon-pohon ini tidak bisa ditemukan lagi lewat skeleton mana
  *  pun - karena itu harus dikumpulkan lebih dulu. */
 function akarAsingV92(akarModel){
   const r=activeModelRoot(),keluar=new Set();
   if(!r)return keluar;
   r.traverse(o=>{
     if(!o.isSkinnedMesh||!o.skeleton||!o.skeleton.bones.length)return;
     const a=akarRangkaV91(o.skeleton.bones[0]);
     if(a&&a!==akarModel)keluar.add(a);
   });
   return keluar;
 }
 function buangAkarKosongV92(calon,akarModel){
   const r=activeModelRoot();
   if(!r||!calon.size)return [];
   const dipakai=new Set();
   r.traverse(o=>{
     if(!o.isSkinnedMesh||!o.skeleton)return;
     for(const b of o.skeleton.bones)if(b)dipakai.add(b);
   });
   const dibuang=[];
   for(const akar of calon){
     if(!akar||akar===akarModel||!akar.parent)continue;
     let masih=false;
     akar.traverse(x=>{ if(dipakai.has(x))masih=true });
     if(masih)continue;                      // masih ada mesh yang memakainya
     // Bone terpilih tidak boleh tertinggal menunjuk tulang yang dilepas.
     if(selectedBone){
       let lepas=false;
       akar.traverse(x=>{ if(x===selectedBone)lepas=true });
       if(lepas)setSkeletonSelectedBoneV21(null);
     }
     // Yang dilaporkan jumlah TULANG, bukan jumlah pohon: satu pohon bisa
     // berisi beberapa cabang tulang yang terpisah oleh simpul $AssimpFbx$
     // hasil pemecahan transform, sehingga di layar tampak seperti beberapa
     // pohon padahal satu subpohon yang sama.
     let isi=0; akar.traverse(x=>{ if(x.isBone)isi++ });
     akar.parent.remove(akar);
     dibuang.push({nama:akar.name||'(tanpa nama)',tulang:isi});
   }
   return dibuang;
 }

 const pasangLamaV92=pasangPaksaV91;
 function pasangPaksaRapiV92(){
   const model=rangkaModelV91();
   const akarModel=model?model.akar:null;
   const calon=akarModel?akarAsingV92(akarModel):new Set();
   const hasil=pasangLamaV92.apply(this,arguments);
   const dibuang=buangAkarKosongV92(calon,akarModel);
   if(dibuang.length){
     refreshHelper();setSkeletonVisible(true);
     if(typeof rebuildSkeletonVisualV23==='function')rebuildSkeletonVisualV23();
     if(typeof updateSkeletonVisualV23==='function')updateSkeletonVisualV23();
     const jumlahTulang=dibuang.reduce((n,d)=>n+d.tulang,0);
     rigStatusV26.textContent+=' • '+jumlahTulang+' tulang bawaan mesh dibuang ('
                               +dibuang.map(d=>d.nama).slice(0,3).join(', ')
                               +(dibuang.length>3?'…':'')+')';
   }
   return hasil;
 }
 // v91 mengikat tombolnya dengan NILAI fungsi, jadi tombolnya yang diikat ulang.
 $('rigForceV91').onclick=pasangPaksaRapiV92;
 window.__rigForceV91=pasangPaksaRapiV92;

"""

s = s.replace(anchor, anchor + js, 1)
p.write_text(s, encoding='utf-8')
print('RIG_FORCE_TIDY_V92 applied: pohon tulang bawaan dibuang sesudah Bind Paksa')
