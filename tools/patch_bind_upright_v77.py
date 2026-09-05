#!/usr/bin/env python3
# BIND_UPRIGHT_V77 - membetulkan penyegaran data bind pada koreksi sumbu Z-up
# di mesin Object "Animation".
#
# Gejalanya: saat FBX animasi diimpor, tulangnya benar tetapi kulitnya melenceng
# tetap terhadap tulang, sehingga badan tampak berantakan dan berputar salah.
#
# Sebabnya bukan animasi. v71 menyegarkan data bind dengan Skeleton
# .calculateInverses(), yang menghitung ulang boneInverses DARI POSE YANG SEDANG
# AKTIF. Pada FBX pose murni pose itu memang bind pose, jadi tidak berakibat apa
# apa - itu sebabnya cacat ini tidak pernah muncul di mesin Auto Rig. Pada FBX
# animasi, transform node yang tersimpan di berkas adalah satu bingkai gerak,
# bukan bind pose; menghitung ulang di situ berarti mendefinisikan ulang bind
# pose menjadi pose berjalan. Selisihnya tetap sepanjang klip - itu yang terukur
# sebagai simpangan yang besarnya tidak berubah pada tiap mesh.
#
# Yang benar: koreksi sumbu hanya menggeser matriks dunia setiap tulang dan mesh
# dengan satu matriks yang sama. Skinning tetap sahih kalau data bind digeser
# dengan matriks itu juga, bukan dikarang ulang:
#
#   boneInverse' = boneInverse * geser^-1
#   bindMatrix'  = geser * bindMatrix
#
# Dengan begitu hasil skinning ikut berputar utuh bersama modelnya, dan bind pose
# asli dari berkas tetap terjaga apa adanya.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'BIND_UPRIGHT_V77' in s:
    raise SystemExit('BIND_UPRIGHT_V77 sudah ada - patch dijalankan dua kali')

# 1) Rekam matriks geser bersih di root: keadaan sebelum dan sesudah rotasi
#    dipasang. Dipakai matriks penuh, bukan kuaternion, supaya posisi dan skala
#    bawaan berkas pada root ikut terhitung.
lama1 = "      obj.quaternion.premultiply(q);\n"
baru1 = (
    "      // BIND_UPRIGHT_V77 - rekam perubahan bersih pada root: matriks dunia\n"
    "      // sebelum dan sesudah rotasi dipasang. Inilah satu-satunya matriks\n"
    "      // yang menggeser seluruh tulang dan mesh, jadi data bind cukup\n"
    "      // digeser dengan matriks yang sama.\n"
    "      obj.updateMatrix();\n"
    "      const rootSebelumV77=obj.matrix.clone();\n"
    "      obj.quaternion.premultiply(q);\n"
    "      obj.updateMatrix();\n"
    "      const geserV77=obj.matrix.clone().multiply(rootSebelumV77.clone().invert());\n"
    "      const geserBalikV77=geserV77.clone().invert();\n"
)
if lama1 not in s:
    raise SystemExit('baris pemasangan rotasi root v71 tidak ditemukan')
s = s.replace(lama1, baru1, 1)

# 2) Ganti penyegaran data bind v71 dengan penggeseran yang setara secara aljabar.
lama2 = """      // Data bind disegarkan agar sepadan dengan susunan baru: boneInverses
      // dihitung ulang dari pose dunia sekarang, lalu tiap mesh diikat ulang
      // memakai matrixWorld-nya. Tanpa langkah ini bindMatrix tetap merujuk
      // susunan sebelum panggang dan skinning CPU tetap kacau.
      const skelsV71=new Set();
      obj.traverse(o=>{if(o.isSkinnedMesh&&o.skeleton)skelsV71.add(o.skeleton)});
      for(const sk of skelsV71){try{sk.calculateInverses()}catch(e){console.warn('FBX_UPRIGHT_BAKE_V71 inverses',e)}}
      obj.traverse(o=>{
        if(!o.isSkinnedMesh)return;
        try{o.updateMatrixWorld(true);o.bind(o.skeleton,o.matrixWorld)}
        catch(e){console.warn('FBX_UPRIGHT_BAKE_V71 bind',e)}
      });
"""
baru2 = """      // BIND_UPRIGHT_V77
      // Data bind digeser dengan matriks yang sama seperti yang menggeser dunia,
      // sehingga ikatan kulit ke tulang tidak berubah sedikit pun - hanya ikut
      // berputar. boneInverse dikali geser terbalik dari kanan, bindMatrix
      // dikali geser dari kiri; keduanya saling meniadakan di rumus skinning.
      //
      // Menghitung ulang boneInverses dari pose yang sedang aktif TIDAK boleh:
      // pada FBX animasi, transform node yang tersimpan di berkas adalah satu
      // bingkai gerak, bukan bind pose, sehingga bind pose akan terdefinisi
      // ulang menjadi pose berjalan dan kulit melenceng tetap sepanjang klip.
      const skelV77=new Set();
      obj.traverse(o=>{if(o.isSkinnedMesh&&o.skeleton)skelV77.add(o.skeleton)});
      let inversV77=0;
      for(const sk of skelV77){
        const inv=sk&&sk.boneInverses;
        if(!Array.isArray(inv))continue;
        for(const m of inv){if(m&&m.isMatrix4){m.multiply(geserBalikV77);inversV77++}}
      }
      let bindV77=0;
      obj.traverse(o=>{
        if(!o.isSkinnedMesh||!o.bindMatrix)return;
        o.bindMatrix.premultiply(geserV77);
        o.bindMatrixInverse.copy(o.bindMatrix).invert();
        bindV77++;
      });
"""
if lama2 not in s:
    raise SystemExit('blok penyegaran data bind v71 tidak ditemukan')
s = s.replace(lama2, baru2, 1)

# 3) Catatan konsol v71 menyebut variabel yang sudah tidak ada; ganti dengan
#    hitungan yang benar-benar dikerjakan v77.
lama3 = ("      console.log('FBX_UPRIGHT_BAKE_V71: rotasi dipanggangkan sampai tulang & mesh, "
         "simpul perantara identitas, '+skelsV71.size+' skeleton diikat ulang');\n")
baru3 = ("      console.log('FBX_UPRIGHT_BAKE_V71: rotasi dipanggangkan sampai tulang & mesh, simpul perantara identitas');\n"
         "      console.log('BIND_UPRIGHT_V77: '+inversV77+' boneInverse digeser, '+bindV77+' bindMatrix digeser, bind pose berkas dipertahankan');\n")
if lama3 not in s:
    raise SystemExit('baris catatan konsol v71 tidak ditemukan')
s = s.replace(lama3, baru3, 1)

# Penjaga: di dalam koreksi sumbu tidak boleh ada lagi penghitungan ulang bind
# pose. Di luar itu calculateInverses tetap sah - mesin Auto Rig memakainya untuk
# skeleton yang memang baru dibuat, di sana pose sekarang justru bind pose-nya.
i = s.index('async function fbxAxisUprightV65')
j = s.index('ANIMATION_FBX_UPRIGHT_V65: koreksi sumbu diterapkan', i)
if 'calculateInverses' in s[i:j]:
    raise SystemExit('masih ada calculateInverses di koreksi sumbu - bind pose bisa terdefinisi ulang lagi')
if 'skelsV71' in s:
    raise SystemExit('sisa skelsV71 masih ada - penggantian blok bind v71 tidak utuh')

p.write_text(s, encoding='utf-8')
print('BIND_UPRIGHT_V77 applied: data bind digeser, tidak lagi dihitung ulang dari pose aktif')
