from pathlib import Path

p=Path('app/src/main/assets/index.html')
if not p.exists(): raise SystemExit('index.html must exist')
s=p.read_text(encoding='utf-8')
if 'FBX_PRIMARY_FBXLOADER_V55' in s:
    print('FBX primary FBXLoader v55 already applied'); raise SystemExit(0)
if 'loadFbxWithAssimp' not in s: raise SystemExit('assimp fbx path must exist')

# Jalur FBX utama pindah ke FBXLoader three.js. Alasan (dibuktikan dengan
# SK_NYX_bonus_animation.fbx): Assimp membelah PreRotation/pivot FBX ke node
# perantara '$AssimpFbx$_...' sementara kurva animasinya tetap membawa rotasi
# lokal utuh, sehingga saat klip diputar rotasi terpasang DOBEL - rambut
# terbang dan sendi menekuk liar. FBXLoader menyusun lapisan transformasi FBX
# secara utuh (seperti Blender) sehingga animasi bawaan file diputar benar.
# Assimp tetap dipertahankan sebagai cadangan bila FBXLoader menolak file,
# dan tetap menjadi jalur utama format lain.
old_c='''// Primary FBX path: Assimp (WASM) -> GLB2 -> Three.js GLTFLoader.
// This preserves FBX hierarchy, bind transforms, skinning and animation more
// reliably than relying only on Three.js FBXLoader for complex character FBX.'''
new_c='''// FBX_PRIMARY_FBXLOADER_V55: jalur FBX utama adalah FBXLoader three.js
// (menangani PreRotation/pivot FBX dengan benar sehingga animasi bawaan file
// tidak terpasang dobel). Assimp (WASM) -> GLB2 menjadi CADANGAN untuk file
// yang ditolak FBXLoader, dan tetap jalur utama format non-FBX.'''
if old_c not in s: raise SystemExit('fbx comment anchor missing')
s=s.replace(old_c,new_c,1)

# Penyiapan lembut untuk hasil FBXLoader: JANGAN panggil prepareFBXForViewer
# (v38) - fungsi itu memaksa skeleton.pose() + bind ulang, obat untuk jalur
# lama yang justru mengacak hasil FBXLoader yang sudah benar. Cukup matikan
# frustum culling dan normalisasi bobot.
prep_js='''function prepFbxV55(obj){
  obj.updateMatrixWorld(true);
  // Gabungkan skeleton duplikat per nama. FBX ekspor per-mesh sering membawa
  // salinan pohon tulang untuk tiap kelompok mesh; Blender/UE meleburnya per
  // nama, sedangkan mixer three.js hanya menganimasikan salinan pertama -
  // mesh lain beku. Peleburan hanya dilakukan bila pose rest semua salinan
  // identik (pagar epsilon); kalau tidak, biarkan apa adanya.
  try{
    const all=[];obj.traverse(o=>{if(o.isBone)all.push(o)});
    const byName={};for(const b of all){(byName[b.name]=byName[b.name]||[]).push(b)}
    const hasDup=Object.values(byName).some(a=>a.length>1);
    if(hasDup){
      const subCount=b=>{let n=0;b.traverse(x=>{if(x.isBone)n++});return n};
      const treeOf=b=>{let n=b;while(n.parent&&n.parent.isBone)n=n.parent;return n};
      const treeSize={};for(const b of all){const r=treeOf(b);if(!treeSize[r.uuid])treeSize[r.uuid]=subCount(r)}
      const canon={};
      for(const [name,list] of Object.entries(byName)){
        let best=list[0];
        for(const b of list){if(treeSize[treeOf(b).uuid]>treeSize[treeOf(best).uuid])best=b}
        canon[name]=best;
      }
      // pagar: semua salinan harus punya world matrix rest yang sama
      let safe=true;
      outer:for(const [name,list] of Object.entries(byName)){
        const m0=canon[name].matrixWorld.elements;
        for(const b of list){
          const m=b.matrixWorld.elements;
          for(let i=0;i<16;i++){if(Math.abs(m[i]-m0[i])>1e-2){safe=false;break outer}}
        }
      }
      if(safe){
        // sambungkan bone kanonis ke induk kanonis (transform lokal sama)
        for(const b of Object.values(canon)){
          const par=b.parent;
          if(par&&par.isBone&&canon[par.name]&&canon[par.name]!==par){
            canon[par.name].add(b);
          }
        }
        // arahkan skeleton semua mesh ke bone kanonis
        obj.traverse(o=>{
          if(o.isSkinnedMesh&&o.skeleton){
            const bs=o.skeleton.bones;
            for(let i=0;i<bs.length;i++){const c=canon[bs[i].name];if(c)bs[i]=c}
          }
        });
        // ganti nama duplikat non-kanonis agar tak pernah kena binding animasi,
        // lalu buang subtree duplikat yang sudah tidak memuat bone kanonis
        const canonSet=new Set(Object.values(canon));
        for(const b of all){if(!canonSet.has(b))b.name=b.name+'__dupV55'}
        const roots=new Set();for(const b of all){roots.add(treeOf(b))}
        for(const r of roots){
          let keeps=false;r.traverse(x=>{if(x.isBone&&canonSet.has(x))keeps=true});
          if(!keeps&&r.parent)r.parent.remove(r);
        }
        obj.updateMatrixWorld(true);
        console.log('FBX_PRIMARY_FBXLOADER_V55: skeleton duplikat dilebur per nama');
      }
    }
  }catch(e){console.warn('FBX_PRIMARY_FBXLOADER_V55 merge',e)}
  // Material: FBX sering menunjuk file tekstur EKSTERNAL yang tidak ikut di
  // dalam .fbx - map-nya tidak pernah termuat dan mesh jadi hitam/transparan.
  // Buang map yang mati, kembalikan opasitas, cerahkan warna terlalu gelap.
  const fixMatsV55=()=>{
    obj.traverse(o=>{
      if(!o.isSkinnedMesh&&!o.isMesh)return;
      const ms=Array.isArray(o.material)?o.material:[o.material];
      for(const m of ms){
        if(!m)continue;
        if(m.map&&!(m.map.image&&(m.map.image.width>0||m.map.image.data))){
          try{m.map.dispose?.()}catch(_){ }
          m.map=null;m.needsUpdate=true;
        }
        if(m.map&&m.map.flipY!==false){m.map.flipY=false;m.map.needsUpdate=true;m.needsUpdate=true}
        if(!m.map){
          if(m.transparent&&(m.opacity===undefined||m.opacity>=0.99)){m.transparent=false;m.needsUpdate=true}
          if(m.color&&(m.color.r+m.color.g+m.color.b)<0.25){m.color.setHex(0xcccccc);m.needsUpdate=true}
        }
      }
    });
  };
  obj.traverse(o=>{
    if(o.isSkinnedMesh){
      o.frustumCulled=false;
      try{o.normalizeSkinWeights?.()}catch(e){}
    }
  });
  // Samakan konvensi UV dengan jalur GLB: glTF memakai V terbalik dari FBX,
  // dan seluruh pipeline app (Apply Texture flipY=false, export GLTF)
  // memakai konvensi glTF. UV hasil FBXLoader dibalik SEKALI di sini; tanpa
  // ini tekstur PNG yang dipasang pengguna tampil terbalik/berantakan.
  obj.traverse(o=>{
    if((o.isMesh||o.isSkinnedMesh)&&o.geometry&&!o.geometry.userData.uvFlippedV55){
      for(const key of ['uv','uv1','uv2','uv3']){
        const at=o.geometry.attributes[key];
        if(at){for(let i=0;i<at.count;i++)at.setY(i,1-at.getY(i));at.needsUpdate=true}
      }
      o.geometry.userData.uvFlippedV55=true;
    }
  });
  fixMatsV55();
  setTimeout(fixMatsV55,800);
  obj.updateMatrixWorld(true);
  return obj;
}
'''
anchor_prep='function prepareFBXForViewer(obj){'
if anchor_prep not in s: raise SystemExit('prepareFBXForViewer anchor missing')
s=s.replace(anchor_prep,prep_js+anchor_prep,1)

old_a='''    }else if(ext==='fbx'){
      try{
        const gltf=await loadFbxWithAssimp(f);
        registerModel(gltf.scene,f.name,gltf.animations||[]);
        msg('FBX dimuat via Assimp/WASM');
      }catch(assimpError){
        console.warn('Assimp FBX gagal, mencoba FBXLoader fallback:',assimpError);
        $('importStatus').textContent='Assimp gagal. Mencoba FBXLoader fallback...';
        const obj=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));
        prepareFBXForViewer(obj);
        registerModel(obj,f.name,obj.animations||[]);
        requestAnimationFrame(()=>requestAnimationFrame(()=>{
          if(root===obj){prepareFBXForViewer(obj);centerAndFit(obj);updateTransformFields();}
        }));
        msg('FBX dimuat via fallback');
      }'''
new_a='''    }else if(ext==='fbx'){
      try{
        $('importStatus').textContent='FBX: membaca dengan FBXLoader...';
        const obj=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));
        prepFbxV55(obj);
        registerModel(obj,f.name,obj.animations||[]);
        requestAnimationFrame(()=>requestAnimationFrame(()=>{
          if(root===obj){prepFbxV55(obj);centerAndFit(obj);updateTransformFields();}
        }));
        msg('FBX dimuat via FBXLoader');
      }catch(fbxError){
        console.warn('FBXLoader gagal, mencoba Assimp fallback:',fbxError);
        $('importStatus').textContent='FBXLoader gagal. Mencoba Assimp/WASM...';
        const gltf=await loadFbxWithAssimp(f);
        registerModel(gltf.scene,f.name,gltf.animations||[]);
        msg('FBX dimuat via Assimp/WASM (cadangan)');
      }'''
if old_a not in s: raise SystemExit('fbx import anchor missing')
s=s.replace(old_a,new_a,1)

old_b='''      let loaded=null;
      if(typeof loadFbxWithAssimp==='function'){
        try{const gltf=await loadFbxWithAssimp(f); loaded=gltf.scene||gltf.scenes?.[0]}catch(e){console.warn('Assimp layer fallback',e)}
      }
      if(!loaded){const url=URL.createObjectURL(f);try{loaded=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej))}finally{URL.revokeObjectURL(url)}}'''
new_b='''      let loaded=null;
      {const url=URL.createObjectURL(f);
       try{loaded=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));
         prepFbxV55(loaded);
       }catch(e){console.warn('FBXLoader layer gagal, mencoba Assimp:',e)}
       finally{URL.revokeObjectURL(url)}}
      if(!loaded&&typeof loadFbxWithAssimp==='function'){
        const gltf=await loadFbxWithAssimp(f); loaded=gltf.scene||gltf.scenes?.[0];
      }'''
if old_b not in s: raise SystemExit('fbx layer anchor missing')
s=s.replace(old_b,new_b,1)

p.write_text(s,encoding='utf-8')
print('FBX primary v55: FBXLoader utama, Assimp cadangan (import utama + layer)')
