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

# Auto is selectable from the shared Object Mode portal.
s=s.replace('id="objectPortalAutoV30" type="button" aria-disabled="true"','id="objectPortalAutoV30" type="button"',1)
s=s.replace('<span class="omh-badge">EXCLUSIVE · COMING SOON</span>','',1)
s=s.replace('<span class="omh-next">🔒</span>','<span class="omh-next">›</span>',1)
s=s.replace('#objectModeHomeV30 .omh-card.auto{opacity:.72;','#objectModeHomeV30 .omh-card.auto{',1)
s=s.replace('#objectModeHomeV30 .auto .omh-next{color:#756b59;font-size:18px}','#objectModeHomeV30 .auto .omh-next{color:#e1b34f;font-size:22px}',1)
edit_path.write_text(s,encoding='utf-8')

# AUTO_MACHINE_V35
# Clone the complete, already-patched Edit runtime so Home/input and Export/output
# use the same proven engine. Auto runs in its own document/runtime instance.
a=s
if "window.__OBJECT_MACHINE__='edit';" in a:
    a=a.replace("window.__OBJECT_MACHINE__='edit';","window.__OBJECT_MACHINE__='auto';",1)
a=a.replace('// EDIT_MACHINE_V32','// AUTO_MACHINE_V35',1)
a=a.replace('<title>3D Viewer & Editor</title>','<title>3D Viewer & Editor — Auto</title>',1)
a=a.replace('<span>GLB • FBX • PNG</span>','<span>AUTO • GLB • FBX • PNG</span>',1)

# Portal routing is isolated: switching mode reloads the selected runtime.
a=a.replace("document.getElementById('objectPortalEditV30').onclick=()=>go('editorScreen');",
            "document.getElementById('objectPortalEditV30').onclick=()=>{window.location.href='index.html'};",1)
a=a.replace("document.getElementById('objectPortalCreateV30').onclick=()=>{window.location.href='create.html'};",
            "document.getElementById('objectPortalCreateV30').onclick=()=>{window.location.href='create.html'};",1)
a=a.replace("document.getElementById('objectPortalAutoV30').onclick=()=>{window.location.href='auto.html'};",
            "document.getElementById('objectPortalAutoV30').onclick=()=>go('homeScreen');",1)

# Auto owns a separate state/storage identity. Home and Export are live now;
# Toolkit, Viewer and Assets are deliberately UI placeholders for later engines.
auto_boot=r'''
// AUTO_MACHINE_RUNTIME_V35
window.__OBJECT_MACHINE__='auto';
window.__OBJECT_MACHINE_VERSION__='v35';
window.__OBJECT_STORAGE_PREFIX__='auto:';
window.__AUTO_ENGINE_ENABLED__=true;
window.__autoMachineRuntimeV35={
  mode:'auto', isolatedDocument:true,
  inputEngine:true, outputEngine:true,
  homeEngine:'edit-baseline', exportEngine:'edit-baseline',
  toolkitEngine:false, viewerEngine:false, assetsEngine:false
};
document.documentElement.dataset.objectMachine='auto';

// Rebuild only Auto bottom navigation. Home and Export route to real Edit-baseline
// screens; the middle three are intentionally non-engine placeholders.
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
  ['autoToolkitNavV35','autoViewerNavV35','autoAssetsNavV35'].forEach(id=>{
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
print('Auto machine v35: isolated runtime active; Home/input and Export/output use Edit baseline; Toolkit/Viewer/Assets reserved')
