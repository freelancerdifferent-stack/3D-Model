#!/usr/bin/env python3
# DROP_TUCK_BUTTON_V95 - tombol "Rapikan Kulit Tertutup" (v93) dibuang.
#
# Tombol itu menebak sendiri lapisan mana yang menutupi lapisan mana, dan
# tebakannya terbukti salah pada mesh yang bukan lapisan terdalam: menekannya
# pada SK_NYX_SUIT di Test.glb membuat celana gelapnya terdorong masuk sampai
# hilang sama sekali, dan yang tampak jadi kulit telanjang.
#
# Dua percobaan memperbaiki tebakannya gagal juga. Yang pertama memakai ambang
# jarak; gagal karena sesudah badan dirapikan, badan duduk hanya 0.36 satuan di
# dalam suit - tidak terbedakan dari tembusan yang sungguhan (terburuk 0.245).
# Yang kedua menilai urutan lapisan antar-mesh; membaik banyak tetapi masih
# menyisakan 10.3% dan satu titik terdorong 5.53 satuan.
#
# Slider Kempis/Kembang (v94) menggantikannya sepenuhnya dan lebih baik di
# setiap ukuran - terukur pada mesh dan model yang sama:
#
#                      kulit menonjol   terlalu rapat   waktu
#   v93 otomatis            1.8%            7.3%        7.2 detik
#   v94 slider manual         0%              0%         13 ms
#
# Jadi tombolnya tidak punya alasan untuk tetap ada, dan selama masih ada ia
# tetap bisa merusak model pengguna dengan satu ketukan.
#
# Yang dibuang HANYA tombol dan pengikatnya. Fungsi bantu v93 - akarModelV93
# dan ukuranModelV93 - tetap dipakai v94 untuk menghitung jangkauan slider,
# jadi tidak ikut dibuang. segarkanTombolTuckV93 sudah menjaga diri terhadap
# tombol yang tidak ada, jadi pemanggilannya aman ditinggal.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'DROP_TUCK_BUTTON_V95' in s:
    raise SystemExit('DROP_TUCK_BUTTON_V95 sudah ada - patch dijalankan dua kali')
if 'MESH_SCALE_SLIDER_V94' not in s:
    raise SystemExit('slider v94 belum ada - tombol v93 tidak boleh dibuang sebelum penggantinya ada')

# ---------------------------------------------------------------- markup
tombol = '        <button class="mesh-action-btn" id="meshTuckBtn">⤵ Rapikan Kulit Tertutup</button>\n'
if tombol not in s:
    raise SystemExit('tombol Rapikan Kulit tidak ditemukan')
s = s.replace(tombol, '        <!-- DROP_TUCK_BUTTON_V95: tombol Rapikan Kulit dibuang, digantikan slider -->\n', 1)

# ---------------------------------------------------------------- pengikat
pengikat = """ $('meshTuckBtn').onclick=()=>{
   const m=selectedMesh();
   if(!m){msg('Pilih dulu mesh badan/kulitnya di daftar');return}
   if(m.userData&&m.userData.posisiAsliV93){
     kembalikanKulitV93(m);
     $('meshLayersStatus').textContent='Kulit '+(m.name||'mesh')+' dikembalikan ke bentuk aslinya.';
     msg('Kulit dikembalikan');
     renderMeshLayers(); segarkanTombolTuckV93(); return;
   }
   const h=rapikanKulitV93(m);
   if(h.gagal){msg(h.gagal);return}
   $('meshLayersStatus').textContent='Kulit '+(m.name||'mesh')+': '+h.kena+' verteks dimasukkan (terjauh '
     +h.terjauh+') • '+h.rapi+' sudah longgar • '+h.terbuka+' terbuka, tidak disentuh';
   msg('Rapikan Kulit: '+h.kena+' verteks dimasukkan, '+h.rapi+' sudah longgar, '+h.terbuka+' terbuka dibiarkan');
   renderMeshLayers(); segarkanTombolTuckV93();
 };
"""
if pengikat not in s:
    raise SystemExit('pengikat tombol Rapikan Kulit tidak ditemukan')
s = s.replace(pengikat, ' // DROP_TUCK_BUTTON_V95: pengikat tombol Rapikan Kulit dibuang\n', 1)

# ---------------------------------------------------------------- CSS tombol
for css in ("#meshLayersScreen #meshTuckBtn{grid-column:1/-1;border:1px solid #2f6f52;background:#12291f;color:#d9f5e6}\n",
            "#meshLayersScreen #meshTuckBtn.pulih{border-color:#6f5a2f;background:#292314;color:#f5ecd9}\n"):
    if css in s:
        s = s.replace(css, '', 1)

p.write_text(s, encoding='utf-8')
print('DROP_TUCK_BUTTON_V95 applied: tombol Rapikan Kulit dibuang, slider yang dipakai')
