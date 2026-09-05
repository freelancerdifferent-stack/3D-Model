from pathlib import Path

# KOREKSI SUMBU DIPANGGANGKAN, ROOT TETAP IDENTITAS - FBX_UPRIGHT_BAKE_V71
#
# Deteksi sumbu milik v65 TIDAK diubah - bagian itu membaca metadata
# GlobalSettings dari byte mentah FBX dan sudah terbukti benar. Yang diganti
# hanya cara koreksinya DITERAPKAN.
#
# Masalahnya, v65 meninggalkan rotasi pada root:
#     obj.quaternion.premultiply(q)
# sementara bindMatrix dan boneInverses tiap SkinnedMesh sudah direkam sebelum
# rotasi itu, dan tidak ada yang menyegarkannya. Skinning three.js tidak kebal
# terhadap rotasi leluhur dengan data bind basi, sehingga getVertexPosition
# (skinning CPU) mengembalikan posisi kacau - sementara render GPU tetap tampak
# benar, jadi preview menyesatkan.
#
# Terukur pada SK_Mannequin.FBX (Z-up, UE4):
#     vertex mentah  -> dunia : 138.2 x 182.6 x 36.6   benar
#     vertex terskin -> dunia : 192.5 x 237.8 x 295.7  kacau
# Pada SK_NYX_Lingerie.fbx (sudah Y-up, v65 tidak memutar apa pun) ketiganya
# identik 97.6 x 179 x 47.3 - aman.
#
# Akibat lanjutannya: rebuildRigKeepWeightsV57 memanggang vertex lewat
# getVertexPosition, jadi yang dibakar geometri kacau itu dan mesh hancur.
# Diuji tanpa rotasi sama sekali, kedua model sehat walau prepFbxV55 tetap
# melebur skeleton di keduanya - jadi peleburan skeleton BUKAN penyebabnya.
# Rotasi root satu-satunya pemicu.
#
# Ada akibat kedua: THREE.Skeleton.pose() menyalin matriks dunia bind menjadi
# matriks LOKAL untuk tulang akar. Itu hanya benar bila induk tulang akar
# berada di titik asal tanpa rotasi. openRig() memanggil pose(), sehingga root
# yang berotasi merusaknya juga.
#
# Perbaikannya: rotasi tidak lagi ditinggalkan sebagai transform di root.
# Transform root dipanggangkan ke anak-anaknya sehingga root kembali identitas,
# lalu data bind disegarkan agar sepadan dengan susunan baru. Dengan root
# identitas, worldToLocal menjadi identitas, pose() kembali sah, dan skinning
# CPU maupun GPU membaca hal yang sama.
#
# Hanya menyentuh animation.html.

p = Path('app/src/main/assets/animation.html')
if not p.exists(): raise SystemExit('animation.html must exist')
s = p.read_text(encoding='utf-8')

if 'FBX_UPRIGHT_BAKE_V71' in s:
    print('FBX upright bake v71 already applied'); raise SystemExit(0)
if 'ANIMATION_FBX_UPRIGHT_V65' not in s: raise SystemExit('ANIMATION_FBX_UPRIGHT_V65 must exist first')
if "window.__OBJECT_MACHINE__='animation';" not in s: raise SystemExit('bukan dokumen mesin Animation')

old = """      obj.quaternion.premultiply(q);
      obj.updateMatrixWorld(true);
      console.log('ANIMATION_FBX_UPRIGHT_V65: koreksi sumbu diterapkan (UpAxis='+upAxis+' sign='+upSign+', FrontAxis='+frontAxis+' sign='+frontSign+', CoordAxis='+coordAxis+' sign='+coordSign+')');"""

new = r"""      // FBX_UPRIGHT_BAKE_V71
      // Rotasi dipakai dulu di root supaya arah dunianya benar, lalu SELURUH
      // transform root dipanggangkan ke anak-anaknya dan root dikembalikan ke
      // identitas. Memanggang lewat matriks penuh, bukan hanya kuaternion,
      // supaya transform bawaan berkas FBX pada root ikut terbawa.
      obj.quaternion.premultiply(q);
      // Panggang transform ke bawah dan lanjut menembus simpul perantara.
      // Berhenti di tulang dan mesh, karena keduanya memang harus memikul
      // transformnya sendiri. Menembus simpul perantara itu WAJIB, bukan
      // kerapian: FBX ini menaruh tulang akar 'pelvis' di bawah sebuah Group
      // bernama 'root' di dalam berkas. Kalau Group itu yang memikul rotasi,
      // THREE.Skeleton.pose() - yang menyalin matriks DUNIA bind menjadi
      // matriks LOKAL untuk tulang akar - mengabaikan rotasi induk, lalu
      // rotasi Group terpakai lagi di atasnya dan rig terbalik.
      const bakeDownV71=node=>{
        node.updateMatrix();
        const M=node.matrix.clone();
        for(const c of node.children){
          c.updateMatrix();
          c.matrix.premultiply(M);
          c.matrix.decompose(c.position,c.quaternion,c.scale);
        }
        node.position.set(0,0,0);
        node.quaternion.set(0,0,0,1);
        node.scale.set(1,1,1);
        node.updateMatrix();
        for(const c of node.children){
          if(!c.isBone&&!c.isMesh&&!c.isSkinnedMesh)bakeDownV71(c);
        }
      };
      bakeDownV71(obj);
      obj.updateMatrixWorld(true);

      // Data bind disegarkan agar sepadan dengan susunan baru: boneInverses
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
      obj.updateMatrixWorld(true);
      console.log('ANIMATION_FBX_UPRIGHT_V65: koreksi sumbu diterapkan (UpAxis='+upAxis+' sign='+upSign+', FrontAxis='+frontAxis+' sign='+frontSign+', CoordAxis='+coordAxis+' sign='+coordSign+')');
      console.log('FBX_UPRIGHT_BAKE_V71: rotasi dipanggangkan sampai tulang & mesh, simpul perantara identitas, '+skelsV71.size+' skeleton diikat ulang');"""

if old not in s: raise SystemExit('blok penerapan rotasi v65 tidak ditemukan')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('FBX upright bake v71 applied: rotasi dipanggangkan, root identitas, data bind disegarkan')
