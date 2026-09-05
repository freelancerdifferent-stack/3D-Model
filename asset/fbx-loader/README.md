# Folder Loader FBX

Taruh file FBX acuan di folder ini.

Mesin loader (`tools/fbx_loader_machine_v67.mjs`) membaca file dari sini saat
build, memuatnya dengan rantai loader yang sama persis dengan mesin Object
"Animation", lalu menyerahkan hasilnya untuk diekstrak.

## Cara pakai

Unggah satu file `.fbx` ke folder ini. Mengganti rig acuan cukup dengan
mengganti isi folder - tidak ada kode yang perlu diubah.

Kalau folder berisi lebih dari satu FBX, mesin memakai yang namanya paling
awal secara alfabet dan menyebutkan pilihannya di log build.

Kalau folder kosong, build tetap jalan; mesin hanya memberi peringatan.

## Yang masuk APK

File FBX di folder ini TIDAK ikut dibungkus ke dalam APK. Yang masuk APK
hanya hasil ekstraksinya. Folder ini murni bahan mentah untuk build.
