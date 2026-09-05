// MESIN EKSTRAK STRUKTUR BONE - BONE_EXTRACT_MACHINE_V68
//
// Mengambil objek hasil MESIN LOADER FBX v67, lalu mengekstrak struktur
// tulangnya menjadi data. Data itu yang masuk APK; file FBX-nya tidak.
//
// Yang diekstrak per tulang:
//   name    - nama tulang apa adanya dari file
//   parent  - nama tulang induk (null untuk akar)
//   depth   - kedalaman dari akar
//   local   - posisi rest relatif induk, satuan asli file
//   quat    - rotasi rest lokal
//   scale   - skala rest lokal
//   world   - posisi rest dunia, satuan asli file
//   unit    - posisi rest dunia yang DINORMALKAN: titik nol di telapak kaki
//             pada sumbu tegak, lalu dibagi tinggi model. Dengan begitu
//             struktur ini bisa dipakai sebagai acuan untuk model lain yang
//             tingginya berbeda - tinggal dikalikan tinggi model sasaran.
//
// Tulang bertanda __dupV55 TIDAK ikut. Penanda itu dipasang oleh prepFbxV55
// milik mesin Animation untuk salinan skeleton non-kanonis yang sengaja
// dijauhkan dari binding animasi. Jumlahnya tetap dilaporkan, tidak disembunyikan.
//
// Mesin ini tidak menafsirkan peran tulang (mana panggul, mana paha, dsb).
// Tugasnya hanya menyalin struktur apa adanya menjadi data.

// ---------------------------------------------------------------------------
// BELUM SELESAI - MASALAH BIND POSE (terbukti lewat pengujian, bukan dugaan)
//
// Mesin ini BELUM didaftarkan ke workflow, jadi belum memengaruhi build.
//
// 1. FBX animasi menyimpan transform lokal tulang pada pose take-nya, bukan
//    pose rest. Pada Anim_Warrior_Walk.FBX itu terlihat dari asimetri
//    kiri/kanan: thigh_l x=8.22 vs thigh_r x=-9.61; clavicle_l x=3.47 vs
//    clavicle_r x=-3.81. Struktur yang keluar sekarang = pose berjalan.
//
// 2. skeleton.pose() TIDAK bisa dipakai untuk memperbaikinya di sini. Model ini
//    punya 17 skeleton dan prepFbxV55 sudah melebur tulang per nama, sehingga
//    pose() dari tiap skeleton menimpa tulang kanonis yang sama dengan
//    boneInverses milik salinan lain. Hasilnya rusak: tulang melompat dari
//    rentang Y 3.7..157.4 menjadi -189.6..96.8.
//
// 3. Arah yang menjanjikan: bind pose dihitung dari inverse(boneInverse).
//    Hasilnya simetris sempurna - thigh_l/r x=+-9.01, clavicle_l/r x=+-3.78,
//    hand_l/r x=+-56.65. TAPI rentang Y-nya hanya -9.6..11.9 (model tinggi
//    173.8) dan hanya mencakup 60 dari 61 tulang. Dugaan sementara: ruang
//    koordinat bindMatrix. Belum dipastikan, jadi belum dipakai.
// ---------------------------------------------------------------------------

import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createLoaderMachine, findReferenceFbx } from './fbx_loader_machine_v67.mjs';

const REPO = process.cwd();
const OUT = path.join(REPO, 'app/src/main/assets/rig_reference.json');
const DUP = '__dupV55';

const r3 = n => Math.round(n * 1e3) / 1e3;
const r5 = n => Math.round(n * 1e5) / 1e5;

export function extractBoneStructure(object, THREE, meta = {}) {
  // BELUM SELESAI - lihat catatan "BIND POSE" di kepala berkas.
  // Untuk sekarang transform dibaca APA ADANYA dari file.
  object.updateMatrixWorld(true);

  const all = [];
  object.traverse(o => { if (o.isBone) all.push(o); });
  const dupCount = all.filter(b => b.name.includes(DUP)).length;
  const bones = all.filter(b => !b.name.includes(DUP));
  if (!bones.length) throw new Error('tidak ada tulang untuk diekstrak');

  const kept = new Set(bones);
  // Induk efektif: tulang terdekat ke atas yang ikut diekstrak.
  const parentOf = b => {
    let n = b.parent;
    while (n && n.isBone && !kept.has(n)) n = n.parent;
    return (n && n.isBone && kept.has(n)) ? n : null;
  };
  const depthOf = b => { let d = 0, n = parentOf(b); while (n) { d++; n = parentOf(n); } return d; };

  // Tinggi dan titik nol diambil dari kotak batas seluruh objek, bukan dari
  // tulang saja, supaya telapak kaki mesh jadi acuan - sama seperti Auto Rig
  // yang memakai kotak batas model.
  const box = new THREE.Box3().setFromObject(object);
  const size = box.getSize(new THREE.Vector3());
  const height = size.y;
  if (!(height > 0)) throw new Error('tinggi model nol - tidak bisa menormalkan');
  const origin = new THREE.Vector3((box.min.x + box.max.x) / 2, box.min.y, (box.min.z + box.max.z) / 2);

  const wp = new THREE.Vector3();
  const rows = bones.map(b => {
    b.getWorldPosition(wp);
    const par = parentOf(b);
    const u = wp.clone().sub(origin).divideScalar(height);
    return {
      name: b.name,
      parent: par ? par.name : null,
      depth: depthOf(b),
      local: [r5(b.position.x), r5(b.position.y), r5(b.position.z)],
      quat: [r5(b.quaternion.x), r5(b.quaternion.y), r5(b.quaternion.z), r5(b.quaternion.w)],
      scale: [r5(b.scale.x), r5(b.scale.y), r5(b.scale.z)],
      world: [r3(wp.x), r3(wp.y), r3(wp.z)],
      unit: [r5(u.x), r5(u.y), r5(u.z)],
    };
  });
  rows.sort((a, b) => a.depth - b.depth || a.name.localeCompare(b.name));

  const roots = rows.filter(r => r.parent === null).map(r => r.name);
  const names = rows.map(r => r.name);
  const dupNames = names.filter((n, i) => names.indexOf(n) !== i);
  if (dupNames.length) throw new Error('nama tulang kembar setelah peleburan: ' + [...new Set(dupNames)].join(', '));

  return {
    marker: 'RIG_REFERENCE_V68',
    source: meta.name || null,
    readVia: meta.via || null,
    axisCorrected: !!meta.uprighted,
    boneCount: rows.length,
    skippedDuplicates: dupCount,
    roots,
    height: r3(height),
    size: [r3(size.x), r3(size.y), r3(size.z)],
    bones: rows,
  };
}

async function main() {
  console.log('MESIN EKSTRAK STRUKTUR BONE v68');
  const fbx = findReferenceFbx();
  if (!fbx) {
    console.log('PERINGATAN: asset/fbx-loader/ belum berisi file .fbx - tidak ada struktur yang diekstrak.');
    if (fs.existsSync(OUT)) { fs.unlinkSync(OUT); console.log('  rig_reference.json lama dihapus supaya tidak basi.'); }
    return;
  }

  const machine = await createLoaderMachine();
  const loaded = await machine.load(fbx);
  const data = extractBoneStructure(loaded.object, machine.THREE, loaded);

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(data, null, 1), 'utf8');

  console.log(`  sumber        : ${data.source} (via ${data.readVia})`);
  console.log(`  koreksi sumbu : ${data.axisCorrected ? 'ya' : 'tidak perlu'}`);
  console.log(`  tulang        : ${data.boneCount}${data.skippedDuplicates ? ` (${data.skippedDuplicates} duplikat __dupV55 dilewati)` : ''}`);
  console.log(`  akar          : ${data.roots.join(', ')}`);
  console.log(`  tinggi        : ${data.height}`);
  console.log(`  ditulis ke    : ${path.relative(REPO, OUT)} (${fs.statSync(OUT).size} byte)`);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(e => { console.error('MESIN EKSTRAK v68 GAGAL:', e.message); process.exit(1); });
}
