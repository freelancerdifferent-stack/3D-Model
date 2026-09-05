// MESIN LOADER FBX - FBX_LOADER_MACHINE_V67
//
// Mesin ini memuat FBX acuan dari asset/fbx-loader/ memakai rantai loader yang
// SAMA PERSIS dengan mesin Object "Animation": FBXLoader sebagai pembaca utama,
// Assimp/WASM sebagai cadangan, lalu prepFbxV55 dan fbxAxisUprightV65.
//
// Rantai itu tidak diketik ulang di sini. Sumbernya DISALIN saat jalan, dibaca
// langsung dari app/src/main/assets/animation.html, sehingga perilakunya tidak
// bisa menyimpang dari mesin Animation. Kalau loader di sana berubah, mesin ini
// ikut berubah; kalau penandanya hilang, mesin ini berhenti dengan error, bukan
// diam-diam memakai versi lama.
//
// Mesin Animation dipilih karena hanya dokumen itu yang membawa
// ANIMATION_FBX_UPRIGHT_V65 - koreksi sumbu Z-up yang dibaca dari metadata
// GlobalSettings file FBX. FBX acuan (konvensi UE4/3ds Max) Z-up, jadi tanpa
// koreksi itu struktur tulang yang diekstrak akan rebah.
//
// Berjalan saat BUILD di Node, bukan di dalam aplikasi. File FBX tidak ikut
// masuk APK.

import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

const REPO = process.cwd();
const ANIM_HTML = path.join(REPO, 'app/src/main/assets/animation.html');
const FBX_DIR = path.join(REPO, 'asset/fbx-loader');

// Lokasi node_modules yang memuat three + assimpjs. Workflow memasangnya di
// /tmp/df3d-runtime; boleh ditimpa lewat argumen --modules atau env DF3D_MODULES.
function modulesDir() {
  const fromArg = process.argv.find(a => a.startsWith('--modules='));
  if (fromArg) return path.resolve(fromArg.slice('--modules='.length));
  if (process.env.DF3D_MODULES) return path.resolve(process.env.DF3D_MODULES);
  return path.join(REPO, 'node_modules');
}

// FBXLoader dan GLTFLoader menyentuh DOM HANYA untuk memuat gambar tekstur.
// Struktur tulang tidak menyentuh DOM sama sekali, jadi pengganjal kosong sudah
// cukup dan tidak mengubah satu pun data tulang.
//
// Tanpa createImageBitmap, GLTFLoader menggantung tanpa error: promise tekstur
// tidak pernah selesai, event loop Node kosong, proses keluar dengan kode 0 dan
// tanpa hasil. Karena itu stub-nya harus menyelesaikan promise, bukan sekadar ada.
function installDomShim() {
  if (globalThis.__df3dDomShim) return;
  globalThis.__df3dDomShim = true;
  if (!globalThis.document) {
    globalThis.document = {
      createElementNS: () => ({
        addEventListener() {}, removeEventListener() {},
        set src(_v) {}, get src() { return ''; },
        style: {}, width: 0, height: 0,
      }),
    };
  }
  globalThis.self = globalThis;
  if (typeof globalThis.createImageBitmap !== 'function') {
    globalThis.createImageBitmap = async () => ({ width: 1, height: 1, close() {} });
  }
  if (typeof URL.createObjectURL !== 'function') {
    URL.createObjectURL = () => 'blob:df3d-stub';
    URL.revokeObjectURL = () => {};
  }
}

// Ambil kode sumber satu fungsi dari animation.html, apa adanya.
function copyFunctionSource(html, startAnchor, endAnchor, label) {
  const i = html.indexOf(startAnchor);
  if (i < 0) throw new Error(`loader mesin Animation tidak ditemukan: ${label} (anchor awal hilang)`);
  const j = html.indexOf(endAnchor, i + startAnchor.length);
  if (j < 0) throw new Error(`loader mesin Animation tidak ditemukan: ${label} (anchor akhir hilang)`);
  return html.slice(i, j + endAnchor.length);
}

export function readAnimationLoaderChain() {
  if (!fs.existsSync(ANIM_HTML)) throw new Error('animation.html belum ada - jalankan pipeline patch dulu');
  const html = fs.readFileSync(ANIM_HTML, 'utf8');

  if (!html.includes('ANIMATION_FBX_UPRIGHT_V65'))
    throw new Error('animation.html tidak membawa ANIMATION_FBX_UPRIGHT_V65 - loader yang mau disalin tidak lengkap');
  if (!html.includes('FBX_PRIMARY_FBXLOADER_V55'))
    throw new Error('animation.html tidak membawa FBX_PRIMARY_FBXLOADER_V55 - loader yang mau disalin tidak lengkap');

  const prepSrc = copyFunctionSource(html, 'function prepFbxV55(obj){', '\n}\n', 'prepFbxV55');
  const uprightSrc = copyFunctionSource(html, '  async function fbxAxisUprightV65(file,obj){', '\n  }\n', 'fbxAxisUprightV65');
  return { prepSrc, uprightSrc };
}

export async function createLoaderMachine() {
  installDomShim();
  const mods = modulesDir();
  if (!fs.existsSync(path.join(mods, 'three')))
    throw new Error(`three tidak ada di ${mods} - pasang three@0.180.0 atau beri --modules=<dir>`);

  const THREE = await import(pathToFileURL(path.join(mods, 'three/build/three.module.js')).href);
  const { FBXLoader } = await import(pathToFileURL(path.join(mods, 'three/examples/jsm/loaders/FBXLoader.js')).href);

  const { prepSrc, uprightSrc } = readAnimationLoaderChain();
  // Kode disalin dijalankan dengan THREE disuntikkan; tidak ada yang diubah.
  const prepFbxV55 = new Function('THREE', `${prepSrc}\nreturn prepFbxV55;`)(THREE);
  const fbxAxisUprightV65 = new Function('THREE', `${uprightSrc}\nreturn fbxAxisUprightV65;`)(THREE);

  let assimpFactory = null;
  const loadAssimp = () => {
    if (!assimpFactory) {
      const require = createRequire(pathToFileURL(path.join(mods, 'noop.cjs')).href);
      assimpFactory = require('assimpjs')();
    }
    return assimpFactory;
  };

  // Cadangan: jalur yang sama dengan loadFbxWithAssimp di mesin Animation.
  // Target konversi WAJIB 'glb2' - satu file biner utuh. Keluaran 'gltf2'
  // memisahkan .bin sehingga GLTFLoader mencarinya sebagai URL dan gagal.
  async function loadWithAssimp(bytes, name) {
    const ajs = await loadAssimp();
    const list = new ajs.FileList();
    list.AddFile(name, new Uint8Array(bytes));
    const res = ajs.ConvertFileList(list, 'glb2');
    if (!res.IsSuccess() || res.FileCount() === 0) {
      let code = 'unknown';
      try { code = String(res.GetErrorCode()); } catch (_) {}
      throw new Error('Assimp gagal mengonversi FBX (code ' + code + ')');
    }
    const out = res.GetFile(0).GetContent();
    const ab = out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength);
    const { GLTFLoader } = await import(pathToFileURL(path.join(mods, 'three/examples/jsm/loaders/GLTFLoader.js')).href);
    const gltf = await new Promise((ok, err) => new GLTFLoader().parse(ab, '', ok, err));
    return gltf.scene;
  }

  // Urutan persis mesin Animation: FBXLoader dulu, Assimp kalau gagal,
  // lalu prepFbxV55 dan koreksi sumbu v65.
  async function load(fbxPath) {
    const buf = fs.readFileSync(fbxPath);
    const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
    const name = path.basename(fbxPath);
    const file = { name, arrayBuffer: async () => ab };

    let obj = null, via = '';
    try {
      obj = new FBXLoader().parse(ab, '');
      via = 'FBXLoader';
    } catch (e) {
      console.warn('  FBXLoader gagal, mencoba Assimp/WASM:', e.message);
      obj = await loadWithAssimp(ab, name);
      via = 'Assimp/WASM (cadangan)';
    }

    prepFbxV55(obj);
    const before = obj.quaternion.clone();
    await fbxAxisUprightV65(file, obj);
    const uprighted = !before.equals(obj.quaternion);
    obj.updateMatrixWorld(true);
    return { object: obj, via, uprighted, name };
  }

  return { load, THREE };
}

export function findReferenceFbx() {
  if (!fs.existsSync(FBX_DIR)) return null;
  const files = fs.readdirSync(FBX_DIR)
    .filter(f => f.toLowerCase().endsWith('.fbx'))
    .sort((a, b) => a.localeCompare(b));
  if (!files.length) return null;
  if (files.length > 1) console.log(`  ${files.length} FBX di folder, dipakai: ${files[0]}`);
  return path.join(FBX_DIR, files[0]);
}

async function main() {
  console.log('MESIN LOADER FBX v67 - rantai loader disalin dari mesin Animation');
  const fbx = findReferenceFbx();
  if (!fbx) {
    console.log('PERINGATAN: asset/fbx-loader/ belum berisi file .fbx - tidak ada yang dimuat.');
    return;
  }
  const machine = await createLoaderMachine();
  const { object, via, uprighted, name } = await machine.load(fbx);

  const bones = [];
  object.traverse(o => { if (o.isBone) bones.push(o); });
  const roots = bones.filter(b => !b.parent?.isBone);
  const box = new machine.THREE.Box3().setFromObject(object);
  const size = box.getSize(new machine.THREE.Vector3());

  console.log(`  file        : ${name}`);
  console.log(`  dibaca via  : ${via}`);
  console.log(`  koreksi sb. : ${uprighted ? 'ya (Z-up ditegakkan)' : 'tidak perlu'}`);
  console.log(`  tulang      : ${bones.length}`);
  console.log(`  akar tulang : ${roots.map(b => b.name).join(', ') || '(tidak ada)'}`);
  console.log(`  ukuran      : ${size.x.toFixed(1)} x ${size.y.toFixed(1)} x ${size.z.toFixed(1)}`);
  if (!bones.length) throw new Error('FBX acuan tidak memuat tulang sama sekali');
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(e => { console.error('MESIN LOADER FBX v67 GAGAL:', e.message); process.exit(1); });
}
