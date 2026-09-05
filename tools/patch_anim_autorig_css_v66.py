from pathlib import Path

# Salin CSS Auto Rig dari auto.html ke animation.html.
#
# Sebagian besar aturan Auto Rig (.auto-rig-shell-v42, .auto-rig-camera-v48,
# .auto-rig-zoom-v49, dst.) tidak terikat identitas mesin, jadi sudah berlaku
# di animation.html. Yang tidak berlaku adalah aturan yang selectornya dikunci
# ke html[data-object-machine="auto"]: animation.html memasang identitas
# 'animation' (lihat dataset.objectMachine), sehingga selector itu tidak pernah
# cocok dan tool rail, viewtools, overleft/overright, timeline serta #animSelect
# tetap tampil saat Auto Rig dibuka - berbeda dengan mesin Auto.
#
# Aturan itu disalin apa adanya dari auto.html (dibaca langsung dari file, bukan
# diketik ulang) lalu scope-nya dipindah ke mesin animation. Blok tema mesin
# (AUTO_MACHINE_THEME_V39) sengaja tidak ikut: letaknya sebelum penanda
# AUTO_RIG_PORTAL_V41 dan bukan bagian dari Auto Rig.

assets = Path('app/src/main/assets')
auto_path = assets / 'auto.html'
anim_path = assets / 'animation.html'

if not auto_path.exists(): raise SystemExit('auto.html must exist')
if not anim_path.exists(): raise SystemExit('animation.html must exist')

a = auto_path.read_text(encoding='utf-8')
s = anim_path.read_text(encoding='utf-8')

if 'ANIM_AUTORIG_CSS_V66' in s:
    print('Animation Auto Rig CSS v66 already applied'); raise SystemExit(0)
if 'ANIMATION_MACHINE_V64' not in s: raise SystemExit('Animation machine v64 must run first')
if 'AUTO_RIG_PORTAL_V41' not in a: raise SystemExit('Auto Rig portal v41 missing in auto.html')

SCOPE_AUTO = 'html[data-object-machine="auto"]'
SCOPE_ANIM = 'html[data-object-machine="animation"]'

start = a.find('/* AUTO_RIG_PORTAL_V41 */')
end = a.find('</style>', start)
if start < 0 or end < 0: raise SystemExit('Auto Rig CSS region not found in auto.html')

rows = [ln for ln in a[start:end].splitlines() if SCOPE_AUTO in ln]
if not rows: raise SystemExit('no machine-scoped Auto Rig CSS found in auto.html')

copied = [ln.replace(SCOPE_AUTO, SCOPE_ANIM) for ln in rows]
block = '\n'.join(copied)

# Selector bertingkat (grup .toolrail/.viewtools/... dipisah baris) hanya utuh
# kalau setiap barisnya membawa scope. Kurung tak seimbang = grup terpotong.
if block.count('{') != block.count('}'):
    raise SystemExit('copied Auto Rig CSS is unbalanced; selector group was split')
if SCOPE_AUTO in block:
    raise SystemExit('auto scope still present after rescope')

css = '\n\n/* ANIM_AUTORIG_CSS_V66 - CSS Auto Rig disalin dari auto.html, scope dipindah ke mesin animation */\n' + block + '\n'

if '</style>' not in s: raise SystemExit('style end missing in animation.html')
s = s.replace('</style>', css + '\n</style>', 1)
anim_path.write_text(s, encoding='utf-8')
print('Animation Auto Rig CSS v66 applied: %d baris CSS disalin dari auto.html' % len(copied))
