from pathlib import Path

assets=Path('app/src/main/assets')
edit_path=assets/'index.html'
create_path=assets/'create.html'
s=edit_path.read_text(encoding='utf-8')

if 'OBJECT_PORTALS_V30' not in s:
    raise SystemExit('Object portals v30 must run first')
if 'OFFLINE_RUNTIME_V1' not in s:
    raise SystemExit('Offline runtime must run before Create machine split')

old="document.getElementById('objectPortalCreateV30').onclick=()=>msg('Create workspace dipilih — Skeleton → Rig → Animation');"
new="document.getElementById('objectPortalCreateV30').onclick=()=>{window.location.href='create.html'};"
if old not in s and new not in s:
    raise SystemExit('Create portal handler not found')
s=s.replace(old,new,1)

if 'EDIT_MACHINE_V32' not in s:
    marker="""
// EDIT_MACHINE_V32
window.__OBJECT_MACHINE__='edit';
window.__OBJECT_MACHINE_VERSION__='v32';
"""
    s=s.replace('</script>',marker+'\n</script>',1)
edit_path.write_text(s,encoding='utf-8')

c=s
c=c.replace('// EDIT_MACHINE_V32','// CREATE_MACHINE_V32',1)
c=c.replace("window.__OBJECT_MACHINE__='edit';","window.__OBJECT_MACHINE__='create';",1)
c=c.replace("<title>3D Viewer & Editor</title>","<title>3D Viewer & Editor — Create</title>",1)

# Create owns its own portal routing. Returning to Edit reloads the Edit runtime,
# while Create remains inside this independent document/runtime instance.
c=c.replace("document.getElementById('objectPortalEditV30').onclick=()=>go('editorScreen');",
            "document.getElementById('objectPortalEditV30').onclick=()=>{window.location.href='index.html'};",1)
c=c.replace("document.getElementById('objectPortalCreateV30').onclick=()=>{window.location.href='create.html'};",
            "document.getElementById('objectPortalCreateV30').onclick=()=>go('editorScreen');",1)

# Create is distinguished only by its emerald visual theme. No mode labels/badges are injected.
create_theme=r'''
/* CREATE_MACHINE_THEME_V33 */
html[data-object-machine="create"]{--create-accent:#43e0a1;--create-accent-soft:#173d31;--create-line:#2d735a}
html[data-object-machine="create"] body{background:radial-gradient(circle at 50% -10%,#16372d 0,#0d1817 34%,#090f12 72%)!important}
html[data-object-machine="create"] .topbar{background:linear-gradient(180deg,#173a30,#101b1a)!important;border-bottom-color:#2d735a!important}
html[data-object-machine="create"] .bottomnav{background:linear-gradient(180deg,#101a19,#0b1214)!important;border-top-color:#285e4b!important}
html[data-object-machine="create"] .nav.active,html[data-object-machine="create"] .nav:active{color:#68edb7!important}
html[data-object-machine="create"] .tool.active,html[data-object-machine="create"] button.active{border-color:#43e0a1!important;box-shadow:0 0 0 1px #43e0a155 inset!important}
html[data-object-machine="create"] #objectModeHomeV30{border-color:#2d735a!important;background:linear-gradient(180deg,#16352c,#101b19)!important}
'''
if '</style>' not in c:
    raise SystemExit('Style closing tag missing for Create theme')
c=c.replace('</style>',create_theme+'\n</style>',1)

# Give the Create runtime its own browser-storage namespace for future Create-only state.
create_boot="""
// CREATE_MACHINE_STORAGE_V32
window.__OBJECT_STORAGE_PREFIX__='create:';
window.__createMachineRuntimeV32={
  mode:'create',
  isolatedDocument:true,
  sceneOwner:'create',
  historyOwner:'create',
  selectionOwner:'create',
  projectOwner:'create'
};
document.documentElement.dataset.objectMachine='create';
"""
c=c.replace('</script>',create_boot+'\n</script>',1)

create_path.write_text(c,encoding='utf-8')
print('Create machine v32 generated with isolated runtime and emerald-only Create theme v33')
