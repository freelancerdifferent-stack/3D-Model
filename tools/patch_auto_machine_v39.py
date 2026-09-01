from pathlib import Path

assets=Path('app/src/main/assets')
edit_path=assets/'index.html'
create_path=assets/'create.html'
auto_path=assets/'auto.html'
s=edit_path.read_text(encoding='utf-8')

if 'AUTO_MACHINE_V39' in s:
    print('Auto machine v39 already applied'); raise SystemExit(0)
if 'OBJECT_PORTALS_V30' not in s: raise SystemExit('Object portals v30 must run first')
if 'EDIT_MACHINE_V32' not in s: raise SystemExit('Create machine v32 must run first')
if 'MODE_STORAGE_SPLIT_V40' not in s: raise SystemExit('Mode storage split v40 must run first')
if not create_path.exists(): raise SystemExit('create.html must exist before the Auto machine is built')

# The Auto machine mirrors Edit completely: auto.html is a full copy of the finished
# index.html, so it carries the entire editor with its own scene, renderer, history and
# listeners. Switching machines is document navigation only — never a runtime bridge.
create_card='''          <button class="omh-card create" id="objectPortalCreateV30" type="button">
            <span class="omh-icon">＋</span>
            <span class="omh-copy"><b>Create</b><small>Mulai dari mesh polos: Skeleton → Rig → Animation.</small></span>
            <span class="omh-next">›</span>
          </button>
'''
auto_card=create_card+'''          <button class="omh-card autov39" id="objectPortalAutoV39" type="button">
            <span class="omh-icon">⚡</span>
            <span class="omh-copy"><b>Auto</b><small>Mesin mandiri untuk rigging dan animation otomatis.</small></span>
            <span class="omh-next">›</span>
          </button>
'''
card_css=r'''
/* AUTO_MACHINE_V39 portal card */
#objectModeHomeV30 .omh-card.autov39{border-color:#7a642e;background:linear-gradient(135deg,#2e2712,#201d14)}
#objectModeHomeV30 .autov39 .omh-icon{border-color:#8a6f33;color:#f2c66f}
'''
card_js=r'''
// AUTO_MACHINE_V39 portal route (document navigation only, no runtime bridge)
document.getElementById('objectPortalAutoV39').onclick=()=>{window.location.href='auto.html'};
'''

def add_card(doc,extra_note):
    if create_card not in doc: raise SystemExit('Create portal card anchor missing '+extra_note)
    doc=doc.replace(create_card,auto_card,1)
    if '</style>' not in doc: raise SystemExit('style end missing '+extra_note)
    doc=doc.replace('</style>',card_css+'\n</style>',1)
    i=doc.rfind('</script>')
    if i<0: raise SystemExit('module script end missing '+extra_note)
    return doc[:i]+card_js+'\n'+doc[i:]

s=add_card(s,'(index)')
edit_path.write_text(s,encoding='utf-8')

c=create_path.read_text(encoding='utf-8')
c=add_card(c,'(create)')
create_path.write_text(c,encoding='utf-8')

# Build the Auto machine from the finished Edit document.
a=s
mach_old="window.__OBJECT_MACHINE__='edit';"
if mach_old not in a: raise SystemExit('edit machine id marker missing')
a=a.replace(mach_old,"window.__OBJECT_MACHINE__='auto';",1)
a=a.replace('// EDIT_MACHINE_V32','// AUTO_MACHINE_V39',1)
a=a.replace('<title>3D Viewer & Editor</title>','<title>3D Viewer & Editor — Auto</title>',1)
a=a.replace('<span>GLB • FBX • PNG</span>','<span>AUTO • GLB • FBX • PNG</span>',1)

# Portal routing inside Auto: Edit and Create leave this document, Auto stays home.
edit_h="document.getElementById('objectPortalEditV30').onclick=()=>go('editorScreen');"
if edit_h not in a: raise SystemExit('edit portal handler missing for auto copy')
a=a.replace(edit_h,"document.getElementById('objectPortalEditV30').onclick=()=>{window.location.href='index.html'};",1)
auto_h="document.getElementById('objectPortalAutoV39').onclick=()=>{window.location.href='auto.html'};"
if auto_h not in a: raise SystemExit('auto portal handler missing for auto copy')
a=a.replace(auto_h,"document.getElementById('objectPortalAutoV39').onclick=()=>go('editorScreen');",1)

auto_boot=r'''
// AUTO_MACHINE_STORAGE_V39
window.__OBJECT_STORAGE_PREFIX__='auto:';
window.__autoMachineRuntimeV39={
  mode:'auto',
  isolatedDocument:true,
  sceneOwner:'auto',
  historyOwner:'auto',
  selectionOwner:'auto',
  projectOwner:'auto'
};
document.documentElement.dataset.objectMachine='auto';
'''
a=a.replace('</script>',auto_boot+'\n</script>',1)

auto_theme=r'''
/* AUTO_MACHINE_THEME_V39 — amber-only Auto identity */
html[data-object-machine="auto"] body{background:radial-gradient(circle at 50% -10%,#332a12 0,#181510 34%,#0f0d09 72%)!important}
html[data-object-machine="auto"] .topbar{background:linear-gradient(180deg,#37300f,#1b1710)!important;border-bottom-color:#6f5b26!important}
html[data-object-machine="auto"] .bottomnav{background:linear-gradient(180deg,#1a170e,#120f0a)!important;border-top-color:#5c4c21!important}
html[data-object-machine="auto"] .nav.active,html[data-object-machine="auto"] .nav:active{color:#f2c66f!important}
html[data-object-machine="auto"] .tool.active,html[data-object-machine="auto"] button.active{border-color:#e0b843!important;box-shadow:0 0 0 1px #e0b84355 inset!important}
html[data-object-machine="auto"] #objectModeHomeV30{border-color:#6f5b26!important;background:linear-gradient(180deg,#332a12,#1b170e)!important}
'''
if '</style>' not in a: raise SystemExit('style end missing for auto theme')
a=a.replace('</style>',auto_theme+'\n</style>',1)

auto_path.write_text(a,encoding='utf-8')
print('Auto machine v39 generated: full Edit mirror, own identity, amber theme, isolated runtime')
