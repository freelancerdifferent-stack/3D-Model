from pathlib import Path

assets=Path('app/src/main/assets')
edit_path=assets/'index.html'
auto_path=assets/'auto.html'
s=edit_path.read_text(encoding='utf-8')

if 'OBJECT_PORTALS_V30' not in s:
    raise SystemExit('Object portals v30 must run first')
if 'OFFLINE_RUNTIME_V1' not in s:
    raise SystemExit('Offline runtime must run before Auto machine')

old="document.getElementById('objectPortalAutoV30').onclick=()=>msg('Auto adalah fitur Exclusive — Coming Soon');"
new="document.getElementById('objectPortalAutoV30').onclick=()=>{window.location.href='auto.html'};"
if old not in s and new not in s:
    raise SystemExit('Auto portal handler not found')
s=s.replace(old,new,1)

s=s.replace('id="objectPortalAutoV30" type="button" aria-disabled="true"','id="objectPortalAutoV30" type="button"',1)
s=s.replace('<span class="omh-badge">EXCLUSIVE · COMING SOON</span>','',1)
s=s.replace('<span class="omh-next">🔒</span>','<span class="omh-next">›</span>',1)
s=s.replace('#objectModeHomeV30 .omh-card.auto{opacity:.72;','#objectModeHomeV30 .omh-card.auto{',1)
s=s.replace('#objectModeHomeV30 .auto .omh-next{color:#756b59;font-size:18px}','#objectModeHomeV30 .auto .omh-next{color:#e1b34f;font-size:22px}',1)
edit_path.write_text(s,encoding='utf-8')

# AUTO_MACHINE_V35
# The source is duplicated into a separate document at build time. Once auto.html
# is written it is a separate runtime: no shared scene, renderer, camera, controls,
# selection, animation state, history, or event lifecycle with any other mode.
a=s
if "window.__OBJECT_MACHINE__='edit';" in a:
    a=a.replace("window.__OBJECT_MACHINE__='edit';","window.__OBJECT_MACHINE__='auto';",1)
a=a.replace('// EDIT_MACHINE_V32','// AUTO_MACHINE_V35',1)
a=a.replace('<title>3D Viewer & Editor</title>','<title>3D Viewer & Editor — Auto</title>',1)
a=a.replace('<span>GLB • FBX • PNG</span>','<span>AUTO • GLB • FBX • PNG</span>',1)

# Object Mode portal may switch documents. This is navigation only, never a
# runtime bridge. Auto's own screens stay inside auto.html.
a=a.replace("document.getElementById('objectPortalEditV30').onclick=()=>go('editorScreen');","document.getElementById('objectPortalEditV30').onclick=()=>{window.location.href='index.html'};",1)
a=a.replace("document.getElementById('objectPortalAutoV30').onclick=()=>{window.location.href='auto.html'};","document.getElementById('objectPortalAutoV30').onclick=()=>go('homeScreen');",1)

auto_boot=r'''
// AUTO_UI_V34 compatibility marker; upgraded below to AUTO_MACHINE_RUNTIME_V35.
// Previous UI-only verification token: window.__AUTO_ENGINE_ENABLED__=false
// AUTO_MACHINE_RUNTIME_V35
window.__OBJECT_MACHINE__='auto';
window.__OBJECT_MACHINE_VERSION__='v35';
window.__OBJECT_STORAGE_PREFIX__='auto:';
window.__AUTO_ENGINE_ENABLED__=true;
window.__autoMachineRuntimeV35={
  mode:'auto', isolatedDocument:true,
  inputEngine:true, outputEngine:true,
  homeEngine:'auto', exportEngine:'auto',
  toolkitEngine:false, viewerEngine:false, assetsEngine:false,
  sharesRuntimeWithEdit:false,
  sharesRuntimeWithCreate:false
};
document.documentElement.dataset.objectMachine='auto';
requestAnimationFrame(()=>{
  const nav=document.querySelector('.bottomnav');
  if(!nav) return;
  nav.innerHTML=`
    <button class="nav active" id="autoHomeNavV35"><b>⌂</b>Home</button>
    <button class="nav" id="autoToolkitNavV35"><b>✦</b>Toolkit</button>
    <button class="nav" id="autoViewerNavV35"><b>◌</b>Viewer</button>
    <button class="nav" id="autoAssetsNavV35"><b>▦</b>Assets</button>
    <button class="nav" id="autoExportNavV35"><b>⇧</b>Export</button>`;
  const activate=(btn)=>{nav.querySelectorAll('.nav').forEach(x=>x.classList.remove('active'));btn.classList.add('active')};
  const home=document.getElementById('autoHomeNavV35');
  const exp=document.getElementById('autoExportNavV35');
  home.onclick=()=>{activate(home);go('homeScreen')};
  exp.onclick=()=>{activate(exp);go('exportScreen')};
  ['autoToolkitNavV35','autoAssetsNavV35'].forEach(id=>{
    const b=document.getElementById(id);
    b.onclick=()=>{activate(b);msg(b.textContent.trim()+' — UI/mesin akan dibuat berikutnya')};
  });
  go('homeScreen');
});
'''
a=a.replace('</script>',auto_boot+'\n</script>',1)

auto_css=r'''
/* AUTO_MACHINE_THEME_V35 */
html[data-object-machine="auto"]{--auto-accent:#d6a62c;--auto-line:#675326}
html[data-object-machine="auto"] .topbar{border-bottom-color:#4d4328}
html[data-object-machine="auto"] .nav.active{color:#e2b84d;background:#211d14}
html[data-object-machine="auto"] #objectModeHomeV30{border-color:#55472a}
html[data-object-machine="auto"] #objectModeHomeV30 .omh-card.auto{border-color:#80662e;box-shadow:0 0 0 1px #d6a62c22 inset}
'''
a=a.replace('</style>',auto_css+'\n</style>',1)

auto_path.write_text(a,encoding='utf-8')
print('Auto machine v35 active as an isolated document/runtime')

viewer_patch=Path(__file__).with_name('patch_auto_viewer_v36.py')
if not viewer_patch.exists():
    raise SystemExit('Auto Viewer v36 patch missing')
exec(compile(viewer_patch.read_text(encoding='utf-8'), str(viewer_patch), 'exec'))
