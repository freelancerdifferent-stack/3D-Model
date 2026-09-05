from pathlib import Path

# HAPUS ANIMATION LIBRARY DARI MESIN ANIMATION - REMOVE_ANIM_LIBRARY_V75
#
# Atas permintaan: seluruh fitur Animation Library dibuang dari mesin Animation
# - tombolnya sekalian - untuk memberi lembar bersih bagi mesin baru yang akan
# dirancang. Yang dibuang: tombol rail, panel daftar klip, pemuat
# anim_library.glb, dan seluruh tumpukan retarget V56-V63, berikut CSS-nya.
#
# Penghapusan dikerjakan SESUDAH v64, dan HANYA pada animation.html. Patch
# v52-v63 sasarannya auto.html, lalu v64 menyalinnya menjadi animation.html;
# mencabut patch itu dari pipeline berarti mesin Auto ikut kehilangan Animation
# Library-nya, padahal pekerjaan ini hanya menyangkut mesin Animation. Mesin
# Auto karena itu tetap utuh, dan itu dikunci lewat cek CI.
#
# Fitur ini memang sudah tidak berfungsi sebelum dihapus: anim_library.glb
# sudah tidak ada di assets sejak commit 8176622, dan sejak v70 kode retargetnya
# masih mencari nama tulang rig lama (Hips, LeftUpLeg, ...) sedangkan Auto Rig
# kini menghasilkan nama mengikuti acuan FBX (pelvis, thigh_l, ...).
#
# Yang SENGAJA dibiarkan hidup: ekspor window.__mapCoreBonesV54 di wilayah Auto
# Rig. Penandanya menyebut ANIM_LIB_SMARTMAP_V56 sehingga tampak milik Animation
# Library, tapi letaknya di luar blok yang dihapus dan mencabutnya berarti
# menyentuh wilayah Auto Rig yang tidak diminta. Pemetaan peran tulang itu juga
# berguna bagi mesin baru nanti.

p = Path('app/src/main/assets/animation.html')
if not p.exists(): raise SystemExit('animation.html must exist')
s = p.read_text(encoding='utf-8')

if 'REMOVE_ANIM_LIBRARY_V75' in s:
    print('Remove anim library v75 already applied'); raise SystemExit(0)
if 'ANIMATION_MACHINE_V64' not in s: raise SystemExit('Animation machine v64 must run first')
if "window.__OBJECT_MACHINE__='animation';" not in s: raise SystemExit('bukan dokumen mesin Animation')
if '\n// ANIM_LIBRARY_V52\n' not in s: raise SystemExit('blok JS Animation Library tidak ditemukan')

# --- 1. Blok JS: dari penanda baris-komentar sampai tepat sebelum rute portal v64.
awal = s.index('\n// ANIM_LIBRARY_V52\n')
tanda_akhir = '\n// ANIMATION_MACHINE_V64 portal route'
akhir = s.find(tanda_akhir, awal)
if akhir < 0: raise SystemExit('penanda akhir (rute portal v64) tidak ditemukan sesudah blok library')
buang_js = s[awal:akhir]
if 'function retargetClip' not in buang_js or "id='animLibBtnV52'" not in buang_js.replace('"', "'"):
    raise SystemExit('blok yang akan dihapus tidak seperti yang diharapkan')
if 'AUTO_RIG' in buang_js:
    raise SystemExit('blok yang akan dihapus menyerempet wilayah Auto Rig - dibatalkan')
baris_js = buang_js.count('\n')
s = s[:awal] + '\n' + s[akhir:]

# --- 2. CSS: dua blok, masing-masing dibuang utuh dari komentar sampai baris terakhirnya.
css_v52_awal = '/* ANIM_LIBRARY_V52 */\n'
css_v52_akhir = ".anim-lib-close-v52{margin-top:12px;width:100%;padding:11px;border:0;border-radius:10px;background:#243141;color:#cfe0f2;font-size:14px}\n"
css_v58_awal = '/* ANIM_LIB_GROUPS_V58 */\n'
css_v58_akhir = ".anim-lib-group-v58:first-child{margin-top:0}\n"

def buang_css(teks, mulai, selesai, label):
    i = teks.find(mulai)
    if i < 0: raise SystemExit('blok CSS tidak ditemukan: ' + label)
    j = teks.find(selesai, i)
    if j < 0: raise SystemExit('akhir blok CSS tidak ditemukan: ' + label)
    return teks[:i] + teks[j + len(selesai):], teks[i:j + len(selesai)].count('\n')

s, baris_css_a = buang_css(s, css_v52_awal, css_v52_akhir, 'ANIM_LIBRARY_V52')
s, baris_css_b = buang_css(s, css_v58_awal, css_v58_akhir, 'ANIM_LIB_GROUPS_V58')

# --- 3. Pagar: tidak boleh ada sisa.
for sisa in ['anim-lib-', 'animLibBtnV52', 'anim_library.glb', 'retargetClip', 'groundFaceV62', '__animLibV52Debug']:
    if sisa in s:
        raise SystemExit('masih ada sisa Animation Library: ' + sisa)

penanda = "\n// REMOVE_ANIM_LIBRARY_V75: Animation Library dibuang dari mesin Animation (tombol, panel, pemuat, retarget V56-V63, dan CSS-nya). Mesin Auto tetap memilikinya.\n"
i = s.rfind('</script>')
if i < 0: raise SystemExit('akhir script tidak ditemukan')
s = s[:i] + penanda + s[i:]

p.write_text(s, encoding='utf-8')
print('Remove anim library v75 applied: %d baris JS + %d baris CSS dibuang dari animation.html' % (baris_js, baris_css_a + baris_css_b))
