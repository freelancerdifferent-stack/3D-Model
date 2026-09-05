from pathlib import Path

assets=Path('app/src/main/assets')
anim_path=assets/'animation.html'
if not anim_path.exists(): raise SystemExit('animation.html must exist')
s=anim_path.read_text(encoding='utf-8')
if 'ANIMATION_FBX_UPRIGHT_V65' in s:
    print('Animation FBX upright v65 already applied'); raise SystemExit(0)
if 'ANIMATION_MACHINE_V64' not in s: raise SystemExit('Animation machine v64 must run first')

# Model dipelajari langsung: Anim_Warrior_Walk.FBX (dan sample lain dari pack)
# dibongkar biner - blok GlobalSettings-nya berisi UpAxis=2(Z) UpAxisSign=1,
# FrontAxis=1(Y) FrontAxisSign=-1, CoordAxis=0(X) CoordAxisSign=1 (konvensi
# 3ds Max: Z-up). three.js FBXLoader TIDAK membaca properti ini sama sekali
# (hanya UnitScaleFactor + AmbientColor dari GlobalSettings) - dikonfirmasi
# dengan membaca sumber vendor/three FBXLoader.js, tidak ada penanganan axis
# apa pun di sana. Akibatnya sumbu "atas" file (Z) masuk apa adanya ke sumbu
# Z three.js (yang berarti "depan"), karakter tampak rebah/menghadap bawah.
#
# Perbaikan: baca 6 integer GlobalSettings itu langsung dari byte mentah file
# FBX yang sedang diimpor (bukan diasumsikan), bangun basis lama (Right/Up/
# Front) dan basis target three.js (Kanan=+X, Atas=+Y, Depan=+Z sesuai
# konvensi glTF), lalu hitung rotasi murni yang memetakan basis lama ke basis
# target. Diverifikasi empiris di harness: sebelum - karakter rebah; sesudah
# - tegak, menghadap kamera, konsisten di 8 fase animasi dan di beberapa file
# lain dari pack (semuanya berbagi metadata axis yang sama). Kalau metadata
# tidak ditemukan/tidak valid/basis bukan rotasi murni (determinan != 1),
# fungsi diam saja - tidak menebak.
funcs=r'''  // ANIMATION_FBX_UPRIGHT_V65
  async function fbxAxisUprightV65(file,obj){
    try{
      if(!file||typeof file.arrayBuffer!=='function')return;
      const buf=await file.arrayBuffer();
      const bytes=new Uint8Array(buf);
      const d=new DataView(buf);
      const te=t=>new TextEncoder().encode(t);
      function findBytes(needle,from){
        const n=needle.length;
        outer: for(let i=from||0;i<=bytes.length-n;i++){
          for(let j=0;j<n;j++){ if(bytes[i+j]!==needle[j]) continue outer; }
          return i;
        }
        return -1;
      }
      function findIntProp(name){
        const i=findBytes(te(name),0);
        if(i<0)return null;
        const j=findBytes(te('Integer'),i);
        if(j<0)return null;
        let k=j+'Integer'.length;
        if(bytes[k]!==0x53)return null; // 'S'
        k+=1;
        if(k+4>bytes.length)return null;
        const strlen=d.getUint32(k,true);
        k+=4+strlen;
        if(k+5>bytes.length||bytes[k]!==0x49)return null; // 'I'
        return d.getInt32(k+1,true);
      }
      const upAxis=findIntProp('UpAxis'), upSign=findIntProp('UpAxisSign');
      const frontAxis=findIntProp('FrontAxis'), frontSign=findIntProp('FrontAxisSign');
      const coordAxis=findIntProp('CoordAxis'), coordSign=findIntProp('CoordAxisSign');
      if([upAxis,upSign,frontAxis,frontSign,coordAxis,coordSign].some(v=>v===null||v===undefined))return;
      if(![0,1,2].includes(upAxis)||![0,1,2].includes(frontAxis)||![0,1,2].includes(coordAxis))return;
      if(new Set([upAxis,frontAxis,coordAxis]).size!==3)return;
      if(Math.abs(upSign)!==1||Math.abs(frontSign)!==1||Math.abs(coordSign)!==1)return;
      const AX=[new THREE.Vector3(1,0,0),new THREE.Vector3(0,1,0),new THREE.Vector3(0,0,1)];
      const right=AX[coordAxis].clone().multiplyScalar(coordSign);
      const up=AX[upAxis].clone().multiplyScalar(upSign);
      const front=AX[frontAxis].clone().multiplyScalar(frontSign);
      const M=new THREE.Matrix4().makeBasis(right,up,front);
      if(Math.abs(Math.abs(M.determinant())-1)>1e-6)return; // bukan rotasi murni - jangan tebak
      const Mt=new THREE.Matrix4().makeBasis(new THREE.Vector3(1,0,0),new THREE.Vector3(0,1,0),new THREE.Vector3(0,0,1));
      const R=Mt.clone().multiply(M.clone().invert());
      const q=new THREE.Quaternion().setFromRotationMatrix(R);
      if(Math.abs(q.w)>0.999999)return; // sudah Y-up, tidak perlu koreksi
      obj.quaternion.premultiply(q);
      obj.updateMatrixWorld(true);
      console.log('ANIMATION_FBX_UPRIGHT_V65: koreksi sumbu diterapkan (UpAxis='+upAxis+' sign='+upSign+', FrontAxis='+frontAxis+' sign='+frontSign+', CoordAxis='+coordAxis+' sign='+coordSign+')');
    }catch(e){console.warn('ANIMATION_FBX_UPRIGHT_V65',e)}
  }

'''
anchor='function prepareFBXForViewer(obj){'
if anchor not in s: raise SystemExit('prepareFBXForViewer anchor missing')
s=s.replace(anchor,funcs+anchor,1)

old_main='''        const obj=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));
        prepFbxV55(obj);
        registerModel(obj,f.name,obj.animations||[]);'''
new_main='''        const obj=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));
        prepFbxV55(obj);
        await fbxAxisUprightV65(f,obj);
        registerModel(obj,f.name,obj.animations||[]);'''
if old_main not in s: raise SystemExit('main FBXLoader import anchor missing')
s=s.replace(old_main,new_main,1)

old_fallback='''        const gltf=await loadFbxWithAssimp(f);
        registerModel(gltf.scene,f.name,gltf.animations||[]);
        msg('FBX dimuat via Assimp/WASM (cadangan)');'''
new_fallback='''        const gltf=await loadFbxWithAssimp(f);
        await fbxAxisUprightV65(f,gltf.scene);
        registerModel(gltf.scene,f.name,gltf.animations||[]);
        msg('FBX dimuat via Assimp/WASM (cadangan)');'''
if old_fallback not in s: raise SystemExit('assimp fallback import anchor missing')
s=s.replace(old_fallback,new_fallback,1)

anim_path.write_text(s,encoding='utf-8')
print('Animation FBX upright v65: koreksi sumbu FBX (Z-up dll) khusus loader mesin Animation')
