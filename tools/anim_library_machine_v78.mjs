// MESIN LIBRARY ANIMASI - ANIM_LIBRARY_V78
//
// Mesin ini membaca SEMUA file FBX animasi dari asset/anim-library/ memakai
// rantai loader yang SAMA PERSIS dengan mesin Auto Rig - createLoaderMachine()
// dari fbx_loader_machine_v67.mjs, yang menyalin loadernya langsung dari
// animation.html saat jalan. Tidak ada loader kedua yang ditulis di sini,
// jadi perilakunya tidak bisa menyimpang dari yang sudah teruji.
//
// Hasilnya ditulis ke app/src/main/assets/anim_library.json. Berkas FBX-nya
// sendiri TIDAK ikut masuk APK.
//
// YANG DIEKSTRAK, DAN KENAPA
//
// Bukan klip mentah. Track kuaternion di berkas FBX adalah rotasi LOKAL,
// yang hanya bermakna relatif terhadap rotasi bind rig itu sendiri. Rig hasil
// Auto Rig memakai rotasi rest identitas (lihat AUTO_RIG_REFERENCE_SKELETON_V70
// - "rotasi rest dibiarkan identitas"), jadi menempelkan rotasi lokal sumber
// apa adanya akan memuntir model.
//
// Yang disimpan adalah rotasi DUNIA tiap tulang per bingkai, berikut pose bind
// sumbernya. Dengan itu aplikasi bisa menghitung selisih terhadap bind:
//
//   selisih(b,t) = duniaSumber(b,t) * bindSumber(b)^-1
//   duniaTujuan(b,t) = selisih(b,t) * bindTujuan(b)
//   lokalTujuan(b,t) = duniaTujuan(induk,t)^-1 * duniaTujuan(b,t)
//
// Rumus itu tetap benar apa pun rotasi bind rig tujuan, jadi animasi bisa
// dipakai baik pada rig hasil Auto Rig maupun pada rig bawaan model.
//
// Posisi tidak disimpan per tulang - panjang tulang datang dari rig tujuan,
// bukan dari berkas animasi. Yang disimpan hanya posisi dunia tulang akar per
// bingkai, dipakai untuk gerak badan secara keseluruhan dan diskalakan menurut
// tinggi model tujuan.
//
// Berjalan saat BUILD di Node, bukan di dalam aplikasi.

import fs from 'node:fs';
import path from 'node:path';
import { createLoaderMachine } from './fbx_loader_machine_v67.mjs';

const REPO = process.cwd();
const ANIM_DIR = path.join(REPO, 'asset/anim-library');
const OUT = path.join(REPO, 'app/src/main/assets/anim_library.json');

// Pembulatan seragam supaya berkas tidak membengkak oleh ekor desimal yang
// tidak berarti. 5 angka di belakang koma pada kuaternion setara sudut jauh di
// bawah seperseribu derajat.
const bulatQ = v => +v.toFixed(5);
const bulatP = v => +v.toFixed(3);

function namaDariBerkas(file) {
  return path.basename(file).replace(/\.fbx$/i, '').replace(/[_-]+/g, ' ').trim();
}

// Kumpulkan tulang menurut nama. prepFbxV55 sudah melebur skeleton duplikat,
// tetapi salinan non-kanonis __dupV55 masih ada di pohon dan tidak boleh ikut.
function kumpulkanTulang(obj) {
  const map = new Map();
  obj.traverse(o => {
    if (!o.isBone) return;
    if (/__dupV55$/.test(o.name)) return;
    if (!map.has(o.name)) map.set(o.name, o);
  });
  return map;
}

function tinggiModel(THREE, obj) {
  const b = new THREE.Box3();
  const v = new THREE.Vector3();
  let ada = false;
  obj.traverse(o => {
    if (!o.isSkinnedMesh && !o.isMesh) return;
    const p = o.geometry?.attributes?.position;
    if (!p) return;
    const langkah = Math.max(1, Math.floor(p.count / 400));
    for (let i = 0; i < p.count; i += langkah) {
      if (o.isSkinnedMesh) o.getVertexPosition(i, v);
      else v.fromBufferAttribute(p, i);
      v.applyMatrix4(o.matrixWorld);
      b.expandByPoint(v);
      ada = true;
    }
  });
  if (!ada) return 0;
  return +b.getSize(new THREE.Vector3()).y.toFixed(3);
}

// Satu klip diubah menjadi rotasi dunia per bingkai. Bingkai diambil pada laju
// tetap supaya aplikasi tidak perlu menafsirkan waktu kunci yang tidak seragam.
function panggangKlip(THREE, obj, klip, tulang, fps) {
  const mixer = new THREE.AnimationMixer(obj);
  const aksi = mixer.clipAction(klip);
  aksi.play();

  const jumlah = Math.max(2, Math.round(klip.duration * fps) + 1);
  const nama = [...tulang.keys()];
  const dunia = {};
  for (const n of nama) dunia[n] = [];
  const akar = [...tulang.values()].find(b => !b.parent || !b.parent.isBone);
  const akarPos = [];

  const q = new THREE.Quaternion();
  const p = new THREE.Vector3();
  const s = new THREE.Vector3();

  for (let f = 0; f < jumlah; f++) {
    mixer.setTime((f / (jumlah - 1)) * klip.duration);
    obj.updateMatrixWorld(true);
    for (const n of nama) {
      tulang.get(n).matrixWorld.decompose(p, q, s);
      dunia[n].push(bulatQ(q.x), bulatQ(q.y), bulatQ(q.z), bulatQ(q.w));
    }
    if (akar) {
      akar.matrixWorld.decompose(p, q, s);
      akarPos.push(bulatP(p.x), bulatP(p.y), bulatP(p.z));
    }
  }
  aksi.stop();
  mixer.uncacheClip(klip);
  return { jumlah, dunia, akarPos, akar: akar ? akar.name : null };
}

function bindSumber(THREE, obj, tulang) {
  // Pose bind diambil dari boneInverses, bukan dari pose yang sedang aktif.
  // Pada FBX animasi pose node di berkas adalah satu bingkai gerak - memakainya
  // sebagai bind akan membuat seluruh animasi melenceng tetap (cacat yang sama
  // yang diperbaiki BIND_UPRIGHT_V77 di sisi aplikasi).
  const inv = new Map();
  obj.traverse(o => {
    if (!o.isSkinnedMesh || !o.skeleton) return;
    const sk = o.skeleton;
    (sk.bones || []).forEach((b, i) => {
      if (!b || inv.has(b.name)) return;
      const m = sk.boneInverses && sk.boneInverses[i];
      if (m) inv.set(b.name, m);
    });
  });

  const hasil = {};
  const q = new THREE.Quaternion(), p = new THREE.Vector3(), s = new THREE.Vector3();
  const M = new THREE.Matrix4();
  let dariInverses = 0, dariPose = 0;
  for (const [n, b] of tulang) {
    const im = inv.get(n);
    if (im) { M.copy(im).invert(); dariInverses++; }
    else { M.copy(b.matrixWorld); dariPose++; }
    M.decompose(p, q, s);
    hasil[n] = {
      quat: [bulatQ(q.x), bulatQ(q.y), bulatQ(q.z), bulatQ(q.w)],
      pos: [bulatP(p.x), bulatP(p.y), bulatP(p.z)],
      parent: b.parent && b.parent.isBone && tulang.has(b.parent.name) ? b.parent.name : null,
    };
  }
  return { bind: hasil, dariInverses, dariPose };
}

export function daftarFbx() {
  if (!fs.existsSync(ANIM_DIR)) return [];
  return fs.readdirSync(ANIM_DIR)
    .filter(f => f.toLowerCase().endsWith('.fbx'))
    .sort((a, b) => a.localeCompare(b))
    .map(f => path.join(ANIM_DIR, f));
}

async function main() {
  console.log('MESIN LIBRARY ANIMASI v78 - loader disalin dari mesin Auto Rig');
  const berkas = daftarFbx();
  const keluar = { marker: 'ANIM_LIBRARY_V78', fps: 30, sources: [], clips: [] };

  if (!berkas.length) {
    console.log('PERINGATAN: asset/anim-library/ belum berisi file .fbx - library ditulis kosong.');
    fs.writeFileSync(OUT, JSON.stringify(keluar), 'utf8');
    console.log(`  ditulis ke    : app/src/main/assets/anim_library.json (${fs.statSync(OUT).size} byte, 0 klip)`);
    return;
  }

  const mesin = await createLoaderMachine();
  const THREE = mesin.THREE;

  for (const f of berkas) {
    const label = path.basename(f);
    console.log(`\n  berkas        : ${label}`);
    let hasil;
    try {
      hasil = await mesin.load(f);
    } catch (e) {
      console.log(`  DILEWATI      : gagal dimuat - ${e.message}`);
      continue;
    }
    const obj = hasil.object;
    const klips = obj.animations || [];
    if (!klips.length) {
      console.log('  DILEWATI      : tidak ada klip animasi di berkas ini');
      continue;
    }
    const tulang = kumpulkanTulang(obj);
    if (!tulang.size) {
      console.log('  DILEWATI      : tidak ada tulang di berkas ini');
      continue;
    }
    obj.updateMatrixWorld(true);
    const tinggi = tinggiModel(THREE, obj);
    const { bind, dariInverses, dariPose } = bindSumber(THREE, obj, tulang);

    const idSumber = keluar.sources.length;
    keluar.sources.push({ file: label, via: hasil.via, height: tinggi, boneCount: tulang.size, bind });
    console.log(`  dimuat lewat  : ${hasil.via}`);
    console.log(`  tulang        : ${tulang.size} (bind: ${dariInverses} dari boneInverses, ${dariPose} dari pose)`);
    console.log(`  tinggi        : ${tinggi}`);

    klips.forEach((klip, i) => {
      const { jumlah, dunia, akarPos, akar } = panggangKlip(THREE, obj, klip, tulang, keluar.fps);
      const nama = klips.length > 1
        ? `${namaDariBerkas(f)} ${i + 1}`
        : namaDariBerkas(f);
      keluar.clips.push({
        name: nama,
        source: idSumber,
        duration: +klip.duration.toFixed(4),
        frames: jumlah,
        root: akar,
        rootPos: akarPos,
        world: dunia,
      });
      console.log(`  klip          : "${nama}" ${klip.duration.toFixed(3)}s, ${jumlah} bingkai @${keluar.fps}fps, akar ${akar}`);
    });
  }

  fs.writeFileSync(OUT, JSON.stringify(keluar), 'utf8');
  const byte = fs.statSync(OUT).size;
  console.log(`\n  ditulis ke    : app/src/main/assets/anim_library.json (${byte} byte, ${keluar.clips.length} klip dari ${keluar.sources.length} berkas)`);

  if (!keluar.clips.length) console.log('PERINGATAN: tidak satu pun klip berhasil diekstrak.');
}

const dipanggilLangsung = process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname);
if (dipanggilLangsung) {
  main().catch(e => { console.error('MESIN LIBRARY ANIMASI v78 GAGAL:', e.message); process.exit(1); });
}
