# Folder Library Animasi

Taruh file FBX animasi di folder ini. Isinya menjadi daftar animasi yang bisa
diterapkan ke model lewat tombol **Anim** di Object mode "animation".

Mesin library (`tools/anim_library_machine_v78.mjs`) membaca SEMUA file `.fbx`
di folder ini saat build, memuatnya dengan rantai loader yang sama persis
dengan mesin Auto Rig, lalu mengekstrak klipnya menjadi
`app/src/main/assets/anim_library.json`.

## Cara pakai

Unggah satu atau beberapa file `.fbx` ke folder ini lewat GitHub. Menambah
animasi cukup dengan menambah file - tidak ada kode yang perlu diubah. Nama
berkas dipakai sebagai nama animasi di daftar, jadi beri nama yang jelas
(contoh: `Anim_Warrior_Walk.FBX` tampil sebagai "Anim Warrior Walk").

Berkas yang tidak punya klip animasi dilewati dan disebutkan di log build.
Kalau folder kosong, build tetap jalan; tombol Anim akan bilang librarynya
masih kosong.

## Yang masuk APK

File FBX di folder ini TIDAK ikut dibungkus ke dalam APK. Yang masuk APK hanya
hasil ekstraksinya, yaitu rotasi dunia tiap tulang per bingkai. Folder ini
murni bahan mentah untuk build.

## Kenapa rotasi dunia, bukan klip mentah

Rig hasil Auto Rig memakai rotasi rest identitas, sedangkan rig di berkas
animasi punya rotasi bind sendiri. Menempelkan rotasi lokal dari berkas apa
adanya akan memuntir model. Karena itu mesin menyimpan rotasi DUNIA tiap
tulang per bingkai berikut pose bind sumbernya, sehingga aplikasi bisa
menghitung selisihnya terhadap pose bind rig tujuan - cara yang tetap benar
apa pun rotasi bind model penggunanya.
