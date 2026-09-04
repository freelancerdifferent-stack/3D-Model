from pathlib import Path

assets=Path('app/src/main/assets')
edit_path=assets/'index.html'
create_path=assets/'create.html'
auto_path=assets/'auto.html'
anim_path=assets/'animation.html'
s=edit_path.read_text(encoding='utf-8')

if 'ANIMATION_MACHINE_V64' in s:
    print('Animation machine v64 already applied'); raise SystemExit(0)
if 'AUTO_MACHINE_V39' not in s: raise SystemExit('Auto machine v39 must run first')
if not auto_path.exists(): raise SystemExit('auto.html must exist before the Animation machine is built')

# Mesin Object ke-4 "Animation": animation.html adalah salinan penuh auto.html
# yang sudah selesai dipatch (identitas, tema, dan storage sendiri; isi fitur
# SAMA PERSIS dengan Auto sesuai permintaan). Pindah mesin = navigasi dokumen
# saja, tanpa jembatan runtime — pola yang sama dengan v32/v39.
auto_card='''          <button class="omh-card autov39" id="objectPortalAutoV39" type="button">
            <span class="omh-icon">⚡</span>
            <span class="omh-copy"><b>Auto</b><small>Mesin mandiri untuk rigging dan animation otomatis.</small></span>
            <span class="omh-next">›</span>
          </button>
'''
anim_card=auto_card+'''          <button class="omh-card animv64" id="objectPortalAnimV64" type="button">
            <span class="omh-icon">\U0001f3ae</span>
            <span class="omh-copy"><b>Animation</b><small>Mesin mandiri khusus animasi.</small></span>
            <span class="omh-next">›</span>
          </button>
'''
card_css=r'''
/* ANIMATION_MACHINE_V64 portal card */
#objectModeHomeV30 .omh-card.animv64{border-color:#6b4fa0;background:linear-gradient(135deg,#2a1f3d,#1d1830)}
#objectModeHomeV30 .animv64 .omh-icon{border-color:#7a5cb5;color:#c9a6ff}
'''
card_js=r'''
// ANIMATION_MACHINE_V64 portal route (document navigation only, no runtime bridge)
document.getElementById('objectPortalAnimV64').onclick=()=>{window.location.href='animation.html'};
'''

def add_card(doc,extra_note):
    if auto_card not in doc: raise SystemExit('Auto portal card anchor missing '+extra_note)
    doc=doc.replace(auto_card,anim_card,1)
    if '</style>' not in doc: raise SystemExit('style end missing '+extra_note)
    doc=doc.replace('</style>',card_css+'\n</style>',1)
    i=doc.rfind('</script>')
    if i<0: raise SystemExit('script end missing '+extra_note)
    return doc[:i]+card_js+'\n'+doc[i:]

s=add_card(s,'(index)')
edit_path.write_text(s,encoding='utf-8')

c=create_path.read_text(encoding='utf-8')
c=add_card(c,'(create)')
create_path.write_text(c,encoding='utf-8')

a0=auto_path.read_text(encoding='utf-8')
a0=add_card(a0,'(auto)')
auto_path.write_text(a0,encoding='utf-8')

# Bangun mesin Animation dari auto.html yang sudah final.
a=a0
mach_old="window.__OBJECT_MACHINE__='auto';"
if mach_old not in a: raise SystemExit('auto machine id marker missing')
a=a.replace(mach_old,"window.__OBJECT_MACHINE__='animation';",1)
a=a.replace('<title>3D Viewer & Editor — Auto</title>','<title>3D Viewer & Editor — Animation</title>',1)

# Identitas & storage: prefix + runtime owner + dataset dokumen
if "window.__OBJECT_STORAGE_PREFIX__='auto:';" not in a: raise SystemExit('auto storage prefix missing')
a=a.replace("window.__OBJECT_STORAGE_PREFIX__='auto:';","window.__OBJECT_STORAGE_PREFIX__='animation:';",1)
own_old="""window.__autoMachineRuntimeV39={
  mode:'auto',
  isolatedDocument:true,
  sceneOwner:'auto',
  historyOwner:'auto',
  selectionOwner:'auto',
  projectOwner:'auto'
};
document.documentElement.dataset.objectMachine='auto';"""
own_new="""window.__autoMachineRuntimeV39={
  mode:'animation',
  isolatedDocument:true,
  sceneOwner:'animation',
  historyOwner:'animation',
  selectionOwner:'animation',
  projectOwner:'animation'
};
document.documentElement.dataset.objectMachine='animation';"""
if own_old not in a: raise SystemExit('auto runtime owner block missing')
a=a.replace(own_old,own_new,1)

# Routing portal di dalam mesin Animation: Auto keluar ke auto.html,
# kartu Animation tetap di rumah sendiri.
auto_h="document.getElementById('objectPortalAutoV39').onclick=()=>go('editorScreen');"
if auto_h not in a: raise SystemExit('auto portal handler missing for animation copy')
a=a.replace(auto_h,"document.getElementById('objectPortalAutoV39').onclick=()=>{window.location.href='auto.html'};",1)
anim_h="document.getElementById('objectPortalAnimV64').onclick=()=>{window.location.href='animation.html'};"
if anim_h not in a: raise SystemExit('animation portal handler missing for animation copy')
a=a.replace(anim_h,"document.getElementById('objectPortalAnimV64').onclick=()=>go('editorScreen');",1)

anim_theme=r'''
/* ANIMATION_MACHINE_THEME_V64 — ungu-only Animation identity */
html[data-object-machine="animation"] body{background:radial-gradient(circle at 50% -10%,#241636 0,#161020 34%,#0d0a14 72%)!important}
html[data-object-machine="animation"] .topbar{background:linear-gradient(180deg,#2c1d45,#171126)!important;border-bottom-color:#5b4390!important}
html[data-object-machine="animation"] .bottomnav{background:linear-gradient(180deg,#181226,#100c1a)!important;border-top-color:#4c3878!important}
html[data-object-machine="animation"] .nav.active,html[data-object-machine="animation"] .nav:active{color:#c9a6ff!important}
html[data-object-machine="animation"] .tool.active,html[data-object-machine="animation"] button.active{border-color:#9a6ee8!important;box-shadow:0 0 0 1px #9a6ee855 inset!important}
html[data-object-machine="animation"] #objectModeHomeV30{border-color:#5b4390!important;background:linear-gradient(180deg,#2c1d45,#171126)!important}
'''
if '</style>' not in a: raise SystemExit('style end missing for animation theme')
a=a.replace('</style>',anim_theme+'\n</style>',1)

anim_path.write_text(a,encoding='utf-8')
print('Animation machine v64 generated: salinan penuh Auto, identitas & tema ungu, storage terisolasi')
