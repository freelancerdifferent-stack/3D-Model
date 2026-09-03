# Asset Model

Gudang aset 3D untuk proyek ini. Upload file ke folder yang sesuai:

| Folder | Isi | Format |
|---|---|---|
| `character/` | Model karakter (ber-rig maupun polos) | `.glb` `.gltf` `.fbx` |
| `animation/` | Klip animasi (bahan Animation Library / retarget) | `.fbx` `.glb` |
| `texture/` | Tekstur untuk dipasang lewat Apply Texture | `.png` `.jpg` |
| `reference/` | File acuan (rig referensi, pose contoh, dll.) | bebas |

Catatan:

- Folder ini adalah **penyimpanan di repo**, bukan bagian APK. File yang ingin
  ditanam ke aplikasi (mis. klip untuk `anim_library.glb`) diproses dulu oleh
  rantai build atau diminta lewat Claude.
- Penamaan disarankan huruf kecil tanpa spasi, mis.
  `character/sk_nyx_lingerie.fbx`, `animation/warrior_attack_01.fbx`.
- Batas ukuran file GitHub 100MB per file. Untuk file lebih besar, pecah atau
  kompres dulu.
