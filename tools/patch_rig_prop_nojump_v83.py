#!/usr/bin/env python3
# RIG_PROP_NOJUMP_V83 - benda tidak melompat saat diubah jadi SkinnedMesh.
#
# Gejalanya: di mode Rig, benda seperti senjata langsung berpindah jauh begitu
# disentuh - di layar yang sedang di-zoom, ia tampak hilang.
#
# Terukur pada SK_NYX_bonus_animation.glb, Plane002:
#
#   sebelum konversi   pusat (-21.9, 112.2,  -0.5)
#   sesudah konversi   pusat (-13.7, 115.2, +27.7)   <- melompat ~28 satuan
#   sesudah Bind       pusat (-21.9, 112.2,  -0.5)   <- kembali persis
#
# Sebabnya: RIG_PROP_SKIN_V82 memberi seluruh vertex bobot penuh ke tulang nomor
# 0 sebagai keadaan awal, lalu mengikatnya dengan bindMatrix = mesh.matrixWorld.
# Itu hanya benar bila skeleton sedang berada di pose bind. Pada berkas ini pose
# node yang tersimpan adalah satu bingkai gerak, bukan bind - sehingga
# (tulang0.matrixWorld * boneInverse0) bukan matriks identitas, dan benda ikut
# tergeser sebesar selisih tulang itu.
#
# Kompensasinya sudah dipakai di Bind dan kini dipakai juga di konversi:
#
#   bindMatrix = (tulang0.matrixWorld * boneInverse0)^-1 * mesh.matrixWorld
#
# Dengan itu hasil skinning pada pose saat itu persis sama dengan posisi semula,
# jadi konversi tidak mengubah apa pun yang terlihat - benda baru bergerak
# setelah pengguna sendiri memberi weight atau menekan Bind.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'RIG_PROP_NOJUMP_V83' in s:
    raise SystemExit('RIG_PROP_NOJUMP_V83 sudah ada - patch dijalankan dua kali')
if 'RIG_PROP_SKIN_V82' not in s:
    raise SystemExit('mesin v82 tidak ditemukan - urutan pipeline salah')

lama = """   baru.updateMatrixWorld(true);
   baru.bind(sk,baru.matrixWorld);
"""
if lama not in s:
    raise SystemExit('titik pengikatan pada konversi v82 tidak ditemukan')

baru = r"""   baru.updateMatrixWorld(true);
   // RIG_PROP_NOJUMP_V83 - bindMatrix dikompensasi terhadap pose tulang yang
   // sedang aktif. Keadaan awal memberi bobot penuh ke tulang 0; kalau skeleton
   // tidak sedang di pose bind, mengikat dengan matrixWorld apa adanya membuat
   // benda melompat sebesar selisih tulang itu.
   let bmV83=baru.matrixWorld;
   try{
     const t0=sk.bones[0];
     if(t0){
       t0.updateWorldMatrix(true,false);
       const dunia0=new THREE.Matrix4().multiplyMatrices(t0.matrixWorld,sk.boneInverses[0]);
       bmV83=new THREE.Matrix4().copy(dunia0).invert().multiply(baru.matrixWorld);
     }
   }catch(e){console.warn('RIG_PROP_NOJUMP_V83',e)}
   baru.bind(sk,bmV83);
"""
s = s.replace(lama, baru, 1)

p.write_text(s, encoding='utf-8')
print('RIG_PROP_NOJUMP_V83 applied: konversi tidak lagi menggeser benda')
