#!/usr/bin/env python3
# RIG_BONETEXTURE_V85 - segarkan boneTexture saat daftar tulang skeleton berubah.
#
# Gejalanya: sesudah Bind, statusnya benar ("Terpasang di: hand_r") tetapi
# senjatanya HILANG dari layar.
#
# Terukur di Chromium pada SK_NYX_bonus_animation.glb, Plane002:
#
#                      tulang   boneMatrices   boneTexture
#   sesudah konversi      21         36         12x12 = 36 slot
#   sesudah Bind          22         22         12x12 = 36 slot   <- basi
#
#   skinIndex tertinggi pada senjata: 21
#
# Sebabnya: THREE.Skeleton.init() mengalokasikan ULANG boneMatrices ketika
# jumlah tulang berubah, tetapi boneTexture yang sudah terlanjur dibuat masih
# memegang larik LAMA sebagai image.data. Skeleton.update() menandai texture itu
# perlu diperbarui, namun yang disalin ke GPU tetap larik lama - matriks tulang
# baru tidak pernah sampai.
#
# Akibatnya perhitungan CPU dan GPU berbeda: getVertexPosition() membaca
# boneMatrices yang benar (karena itu pengukuran posisi tampak sempurna),
# sedangkan shader membaca texture basi sehingga vertex senjata terlempar keluar
# pandangan. Cacat ini hanya terlihat sebagai gambar, tidak sebagai angka - dan
# itulah sebabnya lolos dari pengujian sebelumnya, yang hanya mengukur.
#
# Perbaikannya di sumbernya, ensureBoneInSkeletonV26(): sesudah tulang
# ditambahkan dan skeleton.init() dipanggil, boneTexture dibuang dan dikosongkan.
# Three.js membuatnya ulang dengan ukuran yang benar dan terhubung ke larik yang
# baru (materials.js: `if (skeleton.boneTexture === null) computeBoneTexture()`).
#
# Karena ensureBoneInSkeletonV26 dipakai Apply Weight DAN Bind, keduanya ikut
# terbetulkan.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'RIG_BONETEXTURE_V85' in s:
    raise SystemExit('RIG_BONETEXTURE_V85 sudah ada - patch dijalankan dua kali')

lama = ("   bone.updateMatrixWorld(true);mesh.skeleton.bones.push(bone);"
        "mesh.skeleton.boneInverses.push(new THREE.Matrix4().copy(bone.matrixWorld).invert());"
        "try{mesh.skeleton.init()}catch(_){}return mesh.skeleton.bones.indexOf(bone);")
if lama not in s:
    raise SystemExit('blok penambahan tulang ke skeleton v26 tidak ditemukan')

baru = ("   bone.updateMatrixWorld(true);mesh.skeleton.bones.push(bone);"
        "mesh.skeleton.boneInverses.push(new THREE.Matrix4().copy(bone.matrixWorld).invert());"
        "try{mesh.skeleton.init()}catch(_){}\n"
        "   // RIG_BONETEXTURE_V85 - init() mengalokasikan ulang boneMatrices, tetapi\n"
        "   // boneTexture yang sudah ada tetap memegang larik LAMA sebagai image.data.\n"
        "   // Tanpa dibuang, GPU terus membaca matriks basi sementara CPU membaca yang\n"
        "   // baru - mesh yang memakai indeks tulang baru lenyap dari layar meski\n"
        "   // hitungan posisinya benar. Dikosongkan agar three.js membuatnya ulang.\n"
        "   try{if(mesh.skeleton.boneTexture){mesh.skeleton.boneTexture.dispose();mesh.skeleton.boneTexture=null}}"
        "catch(e){console.warn('RIG_BONETEXTURE_V85',e)}\n"
        "   return mesh.skeleton.bones.indexOf(bone);")
s = s.replace(lama, baru, 1)

p.write_text(s, encoding='utf-8')
print('RIG_BONETEXTURE_V85 applied: boneTexture disegarkan saat daftar tulang berubah')
