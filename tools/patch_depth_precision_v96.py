#!/usr/bin/env python3
# DEPTH_PRECISION_V96 - rasio near/far kamera dirapatkan.
#
# PERINGATAN CAKUPAN: patch ini menyunting index.html, berkas dasar yang
# menurunkan keempat mesin (edit, create, auto, animation). Semua ikut berubah.
# Itu memang disengaja - ini setelan render, bukan fitur mesin - tetapi harus
# disebut karena melanggar kebiasaan patch lain yang hanya menyentuh satu mesin.
#
# URUTAN: patch ini HARUS dijalankan paling awal, sebelum patch_create_machine_v32,
# patch_auto_machine_v39, dan patch_animation_machine_v64 memecah berkas mesin
# dari index.html. Ditaruh di urutan nomornya sendiri (sesudah v95), hasilnya
# hanya masuk ke mesin edit - terukur: animation.html tetap memakai rumus lama
# dan kamera terbaca near 0.1745 / far 17451.
#
# Terukur di aplikasi pada model setinggi 267.8 satuan:
#
#   near  0.1844      far  18437.5      rasio  100.000
#
# Rasio sebesar itu menghabiskan hampir seluruh ketelitian depth buffer 24-bit
# di depan hidung kamera. Pada jarak kamera 557 satuan, dua permukaan baru bisa
# dibedakan bila terpisah 0.100 satuan. Pakaian menempel ke kulit jauh lebih
# rapat dari itu - terukur pada Test.glb, jarak mediannya 0.093 satuan, dan
# 35.8% titik berada di bawah 0.1 - sehingga piksel badan dan piksel baju
# bergantian menang dan tampak sebagai desir berbintik.
#
# Rumus lamanya melebar ke dua arah sekaligus: near dibagi 1000 dan far dikali
# 100. Padahal ketelitian kedalaman hampir seluruhnya ditentukan oleh NEAR;
# memperkecil far hampir tidak menolong. Karena itu near dinaikkan.
#
# far tetap harus memuat lantai grid. Grid dibangun selebar kira-kira 2.2 kali
# ukuran acuan model, jadi sudut terjauhnya sekitar 785 satuan dari kamera pada
# model itu. far = maxDim*6 memberi 1602 - lewat dua kali lipat, aman.
#
#   near  maxDim/150   far  maxDim*6    rasio  900
#
# Pada model yang sama: near 1.79, far 1607, dan permukaan sudah terbedakan
# pada jarak 0.0103 satuan - sepuluh kali lebih halus.
#
# Batas bawahnya dipertahankan supaya model yang sangat kecil tidak berakhir
# dengan near nol.
#
# Ini TIDAK menghapus tumpang-tindih geometri yang sungguhan. Terbukti: pada
# Test.glb sebagian kulit memang menonjol keluar dari baju sampai 0.245 satuan,
# dan itu tetap terlihat sesudah presisi diperbaiki. Untuk itu ada slider
# Kempis/Kembang. Yang hilang di sini hanya desirnya.

from pathlib import Path

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

if 'DEPTH_PRECISION_V96' in s:
    raise SystemExit('DEPTH_PRECISION_V96 sudah ada - patch dijalankan dua kali')

lama = ("    camera.near=Math.max(.001,maxDim/1000);\n"
        "    camera.far=Math.max(1000,maxDim*100);")
if lama not in s:
    raise SystemExit('rumus near/far kamera tidak ditemukan')

baru = ("    // DEPTH_PRECISION_V96 - rasio near/far dirapatkan dari 100.000 ke 900.\n"
        "    // Ketelitian kedalaman hampir seluruhnya ditentukan near, jadi near yang\n"
        "    // dinaikkan. far tetap memuat lantai grid, yang lebarnya sekitar 2.2 kali\n"
        "    // ukuran acuan model.\n"
        "    camera.near=Math.max(.005,maxDim/150);\n"
        "    camera.far=Math.max(50,maxDim*6);")
s = s.replace(lama, baru, 1)

p.write_text(s, encoding='utf-8')
print('DEPTH_PRECISION_V96 applied: near/far kamera dirapatkan di keempat mesin')
