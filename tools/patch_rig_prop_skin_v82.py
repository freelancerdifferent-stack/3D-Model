#!/usr/bin/env python3
# RIG_PROP_SKIN_V82 - mesh tanpa skin bisa dirig manual di Skeleton -> Rig.
#
# Gejalanya: senjata pada berkas karakter (mis. Plane002/Plane003 di
# SK_NYX_bonus_animation.glb) diam di udara saat animasi diputar, dan tidak bisa
# diperbaiki lewat menu Rig karena benda itu tidak bisa disentuh sama sekali di
# sana.
#
# Sebabnya ada di pemilihan sasaran workspace Rig:
#
#   function skinnedMeshesV26(){ ... if(o.isSkinnedMesh)out.push(o) ... }
#   function pickRigMeshV26(x,y){ ... intersectObjects(skinnedMeshesV26(),false) }
#
# Sinar hanya ditembakkan ke mesh yang SUDAH ber-skin. Senjata itu THREE.Mesh
# biasa - tanpa JOINTS/WEIGHTS, induknya simpul akar, bukan tulang - jadi tidak
# pernah kena, dan tombol Apply Weight serta Bind tidak pernah bisa dijangkau
# untuknya.
#
# Mesin ini membuka jalannya: di mode Rig, mesh biasa ikut bisa disentuh, dan
# pada sentuhan pertama diubah menjadi SkinnedMesh yang terikat ke skeleton
# model. Sesudah itu Apply Weight dan Bind bekerja padanya persis seperti pada
# mesh lain, sehingga pengguna mengatur sendiri tulang mana yang memegangnya.
#
# Perubahan bentuk tidak dilakukan: mesh tetap di induk dan transform lokalnya
# semula, geometry dan material dipakai apa adanya. Yang ditambahkan hanya
# atribut skinIndex/skinWeight dan ikatan ke skeleton.
#
# Bind pada benda hasil konversi memberi bobot penuh ke tulang terpilih untuk
# SELURUH mesh - itulah arti "benda ini dipegang tulang ini", dan tanpa itu
# pengguna harus menyapu kuas yang radiusnya lebih besar dari modelnya. Apply
# Weight tetap bekerja seperti biasa untuk pengaturan sebagian.
#
# bindMatrix-nya dihitung supaya benda TIDAK melompat saat di-bind, berapa pun
# pose tulang saat itu:
#
#   bindMatrix = (tulang.matrixWorld * boneInverse)^-1 * mesh.matrixWorld
#
# Dengan itu, pada pose saat bind hasilnya persis posisi semula, dan sesudahnya
# benda mengikuti perubahan tulang apa adanya.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'RIG_PROP_SKIN_V82' in s:
    raise SystemExit('RIG_PROP_SKIN_V82 sudah ada - patch dijalankan dua kali')

# ---------------------------------------------------------------- sasaran sentuh
lama_pick = """ function skinnedMeshesV26(){const r=activeModelRoot(),out=[];if(r)r.traverse(o=>{if(o.isSkinnedMesh)out.push(o)});return out}
 function pickRigMeshV26(x,y){const rect=canvas.getBoundingClientRect();rigNdcV26.set(((x-rect.left)/rect.width)*2-1,-((y-rect.top)/rect.height)*2+1);rigRayV26.setFromCamera(rigNdcV26,camera);const hits=rigRayV26.intersectObjects(skinnedMeshesV26(),false);return hits[0]||null}
"""
if lama_pick not in s:
    raise SystemExit('pemilih sasaran Rig v26 tidak ditemukan')

baru_pick = r""" function skinnedMeshesV26(){const r=activeModelRoot(),out=[];if(r)r.traverse(o=>{if(o.isSkinnedMesh)out.push(o)});return out}
 // RIG_PROP_SKIN_V82 - mesh biasa ikut jadi sasaran sentuh di mode Rig. Tanpa
 // ini, benda seperti senjata yang tidak ber-skin tidak pernah kena sinar,
 // sehingga Apply Weight dan Bind tidak bisa dipakai untuknya sama sekali.
 function sasaranRigV82(){const r=activeModelRoot(),out=[];if(r)r.traverse(o=>{if(o.isMesh||o.isSkinnedMesh)out.push(o)});return out}
 function skeletonModelV82(){
   const r=activeModelRoot();if(!r)return null;
   let sk=null;r.traverse(o=>{if(!sk&&o.isSkinnedMesh&&o.skeleton&&o.skeleton.bones.length)sk=o.skeleton});
   return sk;
 }
 // Mesh biasa diubah menjadi SkinnedMesh di tempatnya: induk, transform lokal,
 // nama, geometry, dan material dipakai apa adanya. Yang ditambahkan hanya
 // atribut skin dan ikatan ke skeleton model.
 function jadikanSkinV82(mesh){
   if(!mesh||mesh.isSkinnedMesh)return mesh;
   const sk=skeletonModelV82();
   if(!sk){msg('Model belum punya skeleton - jalankan Auto Rig dulu');return null}
   const g=mesh.geometry,pos=g&&g.getAttribute&&g.getAttribute('position');
   if(!pos){msg('Mesh ini tidak punya geometry yang bisa dirig');return null}
   if(!g.getAttribute('skinIndex'))
     g.setAttribute('skinIndex',new THREE.Uint16BufferAttribute(new Uint16Array(pos.count*4),4));
   if(!g.getAttribute('skinWeight')){
     const a=new Float32Array(pos.count*4);
     for(let i=0;i<pos.count;i++)a[i*4]=1;          // sementara penuh ke tulang 0
     g.setAttribute('skinWeight',new THREE.Float32BufferAttribute(a,4));
   }
   const baru=new THREE.SkinnedMesh(g,mesh.material);
   baru.name=mesh.name||'Prop';
   baru.position.copy(mesh.position);baru.quaternion.copy(mesh.quaternion);baru.scale.copy(mesh.scale);
   baru.castShadow=mesh.castShadow;baru.receiveShadow=mesh.receiveShadow;baru.visible=mesh.visible;
   baru.frustumCulled=false;                        // mesh ber-skin bisa keluar kotak batas bind
   baru.userData=Object.assign({},mesh.userData,{propSkinV82:true});
   const induk=mesh.parent;
   if(induk){induk.add(baru);induk.remove(mesh)}
   baru.updateMatrixWorld(true);
   baru.bind(sk,baru.matrixWorld);
   try{const mi=(typeof meshList!=='undefined'&&Array.isArray(meshList))?meshList.indexOf(mesh):-1;if(mi>=0)meshList[mi]=baru}catch(_){}
   console.log('RIG_PROP_SKIN_V82: "'+baru.name+'" diubah jadi SkinnedMesh, siap diberi weight/bind');
   return baru;
 }
 function pickRigMeshV26(x,y){const rect=canvas.getBoundingClientRect();rigNdcV26.set(((x-rect.left)/rect.width)*2-1,-((y-rect.top)/rect.height)*2+1);rigRayV26.setFromCamera(rigNdcV26,camera);const hits=rigRayV26.intersectObjects(sasaranRigV82(),false);return hits[0]||null}
"""
s = s.replace(lama_pick, baru_pick, 1)

# ---------------------------------------------------------------- sentuhan mesh
lama_tap = ("   if(hit){rigMeshV26=hit.object;rigHitWorldV26=hit.point.clone();"
            "rigStatusV26.textContent='Mesh/area dipilih • pilih bone atau Apply Weight';"
            "syncRigUiV26();ev.preventDefault();ev.stopPropagation()}")
if lama_tap not in s:
    raise SystemExit('penanganan sentuhan mesh di mode Rig tidak ditemukan')
baru_tap = ("   if(hit){\n"
            "     // RIG_PROP_SKIN_V82: mesh tanpa skin diubah dulu supaya bisa diberi weight.\n"
            "     let obj=hit.object;\n"
            "     if(!obj.isSkinnedMesh){const conv=jadikanSkinV82(obj);if(!conv){ev.preventDefault();ev.stopPropagation();return}obj=conv;refreshHelper();setSkeletonVisible(true)}\n"
            "     rigMeshV26=obj;rigHitWorldV26=hit.point.clone();\n"
            "     rigStatusV26.textContent=(obj.userData&&obj.userData.propSkinV82?'Benda siap dirig • pilih bone lalu Bind':'Mesh/area dipilih • pilih bone atau Apply Weight');\n"
            "     syncRigUiV26();ev.preventDefault();ev.stopPropagation();\n"
            "   }")
s = s.replace(lama_tap, baru_tap, 1)

# ---------------------------------------------------------------- Bind
lama_bind = ("   if(!skeletonRigModeV26)return;if(!rigMeshV26){msg('Tap mesh dulu');return}"
             "if(!selectedBone){msg('Pilih bone dulu');return}"
             "const idx=ensureBoneInSkeletonV26(rigMeshV26,selectedBone);if(idx<0){msg('Bind gagal');return}\n")
if lama_bind not in s:
    raise SystemExit('awal bindRigV26 tidak ditemukan')
baru_bind = lama_bind + r"""   // RIG_PROP_SKIN_V82 - untuk benda hasil konversi, Bind berarti "benda ini
   // dipegang tulang ini": seluruh vertex diberi bobot penuh ke tulang terpilih.
   // Tanpa ini pengguna harus menyapu kuas yang radiusnya melebihi modelnya.
   if(rigMeshV26.userData&&rigMeshV26.userData.propSkinV82){
     const gP=rigMeshV26.geometry,siP=gP.getAttribute('skinIndex'),swP=gP.getAttribute('skinWeight');
     if(siP&&swP){
       for(let i=0;i<siP.count;i++){siP.setXYZW(i,idx,0,0,0);swP.setXYZW(i,1,0,0,0)}
       siP.needsUpdate=true;swP.needsUpdate=true;
     }
     // bindMatrix disusun supaya benda tidak melompat, berapa pun pose tulang
     // saat ini: (tulang.matrixWorld * boneInverse)^-1 * mesh.matrixWorld.
     try{
       rigMeshV26.updateMatrixWorld(true);selectedBone.updateWorldMatrix(true,false);
       const invP=rigMeshV26.skeleton.boneInverses[idx];
       const dunia=new THREE.Matrix4().multiplyMatrices(selectedBone.matrixWorld,invP);
       const bm=new THREE.Matrix4().copy(dunia).invert().multiply(rigMeshV26.matrixWorld);
       rigMeshV26.bind(rigMeshV26.skeleton,bm);
       rigMeshV26.skeleton.update();rigMeshV26.updateMatrixWorld(true);
       refreshHelper();setSkeletonVisible(true);
       rigStatusV26.textContent='Terpasang di: '+(selectedBone.name||'Bone');
       console.log('RIG_PROP_SKIN_V82: "'+(rigMeshV26.name||'Prop')+'" dipasang penuh ke '+(selectedBone.name||'Bone'));
       msg('"'+(rigMeshV26.name||'Benda')+'" dipasang ke '+(selectedBone.name||'Bone'));
       return;
     }catch(e){msg('Bind gagal: '+(e&&e.message||e));return}
   }
"""
s = s.replace(lama_bind, baru_bind, 1)
# ---------------------------------------------------------------- pegangan debug
# Pola yang sudah dipakai dokumen ini (__autoRigV50Debug, __animPortalV79):
# jalur yang sama dengan UI, tetapi bisa dipanggil dari konsol - untuk memeriksa
# hasil rig tanpa harus menebak koordinat sentuhan.
lama_hook = " window.openRigWorkspaceV26=()=>setRigModeV26(true);\n"
if lama_hook not in s:
    raise SystemExit('titik ekspor workspace Rig tidak ditemukan')
baru_hook = lama_hook + """ // RIG_PROP_SKIN_V82
 window.__rigPropV82={
   sasaran:()=>sasaranRigV82().map(o=>({nama:o.name||'(tanpa nama)',skin:!!o.isSkinnedMesh})),
   pilihMesh:nama=>{
     const r=activeModelRoot();let m=null;
     if(r)r.traverse(o=>{if(!m&&(o.isMesh||o.isSkinnedMesh)&&o.name===nama)m=o});
     if(!m)return false;
     if(!m.isSkinnedMesh){const c=jadikanSkinV82(m);if(!c)return false;m=c;refreshHelper()}
     rigMeshV26=m;rigHitWorldV26=m.getWorldPosition(new THREE.Vector3());syncRigUiV26();return true;
   },
   pilihTulang:nama=>{
     const r=activeModelRoot();let b=null;
     if(r)r.traverse(o=>{if(!b&&o.isBone&&o.name===nama)b=o});
     if(!b)return false;setSkeletonSelectedBoneV21(b);syncRigUiV26();return true;
   },
   bind:()=>{bindRigV26();return rigStatusV26.textContent},
 };
"""
s = s.replace(lama_hook, baru_hook, 1)

p.write_text(s, encoding='utf-8')
print('RIG_PROP_SKIN_V82 applied: mesh tanpa skin bisa disentuh, dikonversi, dan di-bind manual di menu Rig')
