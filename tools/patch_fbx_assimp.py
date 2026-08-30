from pathlib import Path

path = Path('app/src/main/assets/index.html')
text = path.read_text(encoding='utf-8')

ASSIMP_TAG = '<script src="https://cdn.jsdelivr.net/npm/assimpjs@0.0.10/dist/assimpjs.js"></script>'
if ASSIMP_TAG not in text:
    marker = '<script type="importmap">'
    if marker not in text:
        raise SystemExit('importmap marker not found')
    text = text.replace(marker, ASSIMP_TAG + '\n\n' + marker, 1)

MODEL_MARKER = "const modelInput=$('modelInput');"
HELPER_MARKER = 'async function loadFbxWithAssimp(file)'
if HELPER_MARKER not in text:
    if MODEL_MARKER not in text:
        raise SystemExit('modelInput marker not found')
    helper = r'''

// Primary FBX path: Assimp (WASM) -> GLB2 -> Three.js GLTFLoader.
// This preserves FBX hierarchy, bind transforms, skinning and animation more
// reliably than relying only on Three.js FBXLoader for complex character FBX.
let assimpModulePromise=null;
async function getAssimpModule(){
  if(typeof globalThis.assimpjs!=='function'){
    throw new Error('AssimpJS belum termuat. Periksa koneksi internet.');
  }
  if(!assimpModulePromise) assimpModulePromise=globalThis.assimpjs();
  return assimpModulePromise;
}

async function loadFbxWithAssimp(file){
  $('importStatus').textContent='FBX: membaca dengan Assimp/WASM...';
  const ajs=await getAssimpModule();
  const bytes=new Uint8Array(await file.arrayBuffer());
  const fileList=new ajs.FileList();
  fileList.AddFile(file.name,bytes);

  $('importStatus').textContent='FBX: normalisasi skeleton/skin ke GLB2...';
  const result=ajs.ConvertFileList(fileList,'glb2');
  if(!result.IsSuccess() || result.FileCount()===0){
    let code='unknown';
    try{ code=String(result.GetErrorCode()); }catch(_){ }
    throw new Error('Assimp gagal mengonversi FBX (code '+code+')');
  }

  const resultFile=result.GetFile(0);
  const out=resultFile.GetContent();
  const arrayBuffer=out.buffer.slice(out.byteOffset,out.byteOffset+out.byteLength);
  $('importStatus').textContent='FBX: memuat hasil GLB2...';
  return await new Promise((resolve,reject)=>{
    new GLTFLoader().parse(arrayBuffer,'',resolve,reject);
  });
}
'''
    text = text.replace(MODEL_MARKER, MODEL_MARKER + helper, 1)

old = """    }else if(ext==='fbx'){
      const obj=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));
      registerModel(obj,f.name,obj.animations||[]);
    }else throw new Error('Format tidak didukung');"""
new = """    }else if(ext==='fbx'){
      try{
        const gltf=await loadFbxWithAssimp(f);
        registerModel(gltf.scene,f.name,gltf.animations||[]);
        msg('FBX dimuat via Assimp/WASM');
      }catch(assimpError){
        console.warn('Assimp FBX gagal, mencoba FBXLoader fallback:',assimpError);
        $('importStatus').textContent='Assimp gagal. Mencoba FBXLoader fallback...';
        const obj=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));
        registerModel(obj,f.name,obj.animations||[]);
        msg('FBX dimuat via fallback');
      }
    }else throw new Error('Format tidak didukung');"""

if old in text:
    text = text.replace(old, new, 1)
elif 'loadFbxWithAssimp(f)' not in text:
    raise SystemExit('FBX import branch not found')

path.write_text(text, encoding='utf-8')
print('Patched FBX pipeline: Assimp/WASM -> GLB2 -> GLTFLoader')
