from pathlib import Path

assets=Path('app/src/main/assets')
edit_path=assets/'index.html'
auto_path=assets/'auto.html'
autorig_path=assets/'autorig.html'
s=edit_path.read_text(encoding='utf-8')

if 'AUTORIG_MACHINE_V42' in s or autorig_path.exists():
    print('Auto Rig machine v42 already applied'); raise SystemExit(0)
if 'AUTO_MACHINE_V39' not in auto_path.read_text(encoding='utf-8'):
    raise SystemExit('Auto machine v39 must run first')
if 'MODE_STORAGE_SPLIT_V40' not in s:
    raise SystemExit('Mode storage split v40 must run first')

a_html=auto_path.read_text(encoding='utf-8')
if 'AUTO_RIG_BUTTON_V41' not in a_html:
    raise SystemExit('Auto Rig button v41 must run first')

# The Auto Rig machine is a fourth isolated document: a full copy of the finished
# Edit editor with its own identity, green theme and storage namespace. It is only
# reachable from the Auto machine's Auto Rig button; switching stays document
# navigation, never a runtime bridge.
r=s
mach="window.__OBJECT_MACHINE__='edit';"
if mach not in r: raise SystemExit('edit machine id marker missing')
r=r.replace(mach,"window.__OBJECT_MACHINE__='autorig';",1)
r=r.replace('// EDIT_MACHINE_V32','// AUTORIG_MACHINE_V42',1)
r=r.replace('<title>3D Viewer & Editor</title>','<title>3D Viewer & Editor — Auto Rig</title>',1)
r=r.replace('<span>GLB • FBX • PNG</span>','<span>AUTO RIG • GLB • FBX</span>',1)

edit_h="document.getElementById('objectPortalEditV30').onclick=()=>go('editorScreen');"
if edit_h not in r: raise SystemExit('edit portal handler missing for autorig copy')
r=r.replace(edit_h,"document.getElementById('objectPortalEditV30').onclick=()=>{window.location.href='index.html'};",1)
# Create and Auto cards already navigate by document in the Edit source; keep them.

boot=r'''
// AUTORIG_MACHINE_STORAGE_V42
window.__OBJECT_STORAGE_PREFIX__='autorig:';
window.__autoRigMachineRuntimeV42={
  mode:'autorig',
  isolatedDocument:true,
  sceneOwner:'autorig',
  historyOwner:'autorig',
  selectionOwner:'autorig',
  projectOwner:'autorig'
};
document.documentElement.dataset.objectMachine='autorig';
'''
r=r.replace('</script>',boot+'\n</script>',1)

theme=r'''
/* AUTORIG_MACHINE_THEME_V42 — green-only Auto Rig identity */
html[data-object-machine="autorig"] body{background:radial-gradient(circle at 50% -10%,#0f2f1a 0,#0c1712 34%,#080f0b 72%)!important}
html[data-object-machine="autorig"] .topbar{background:linear-gradient(180deg,#123a20,#0d1a12)!important;border-bottom-color:#2c6d42!important}
html[data-object-machine="autorig"] .bottomnav{background:linear-gradient(180deg,#0e1a12,#0a120d)!important;border-top-color:#245c38!important}
html[data-object-machine="autorig"] .nav.active,html[data-object-machine="autorig"] .nav:active{color:#baff36!important}
html[data-object-machine="autorig"] .tool.active,html[data-object-machine="autorig"] button.active{border-color:#baff36!important;box-shadow:0 0 0 1px #baff3655 inset!important}
html[data-object-machine="autorig"] #objectModeHomeV30{border-color:#2c6d42!important;background:linear-gradient(180deg,#10301c,#0d1a12)!important}
'''
if '</style>' not in r: raise SystemExit('style end missing for autorig theme')
r=r.replace('</style>',theme+'\n</style>',1)
autorig_path.write_text(r,encoding='utf-8')

# Rewire the Auto machine's portal button from placeholder toast to real navigation.
old_btn="b.onclick=()=>msg('Auto Rig — mesin khususnya akan dibangun berikutnya');"
if old_btn not in a_html: raise SystemExit('Auto Rig placeholder handler missing in auto.html')
a_html=a_html.replace(old_btn,"b.onclick=()=>{sendModelToAutoRigV42()};",1)
sender=r'''
// AUTORIG_HANDOFF_SEND_V42 — titipan satu-arah lewat storage, bukan jembatan runtime:
// model saat ini diekspor ke GLB, disimpan di slot IndexedDB sekali-pakai, lalu
// dokumen berpindah. Mesin Auto mati total sebelum mesin Auto Rig hidup.
async function sendModelToAutoRigV42(){
  if(!root){window.location.href='autorig.html';return}
  msg('Membawa model ke Auto Rig…');
  try{
    const glb=await new Promise((res,rej)=>{
      try{new GLTFExporter().parse(root,r=>res(r),e=>rej(e),{binary:true,animations:(typeof clips!=='undefined'&&clips)?clips:[]})}
      catch(e){rej(e)}
    });
    await new Promise((res,rej)=>{
      const rq=indexedDB.open('DF3D_MACHINE_HANDOFF',1);
      rq.onupgradeneeded=()=>rq.result.createObjectStore('slot');
      rq.onerror=()=>rej(rq.error);
      rq.onsuccess=()=>{
        const db=rq.result,tx=db.transaction('slot','readwrite');
        tx.objectStore('slot').put({buffer:glb,name:String($('fileLabel')?.textContent||'Model'),time:Date.now()},'autorig');
        tx.oncomplete=()=>{db.close();res()};
        tx.onerror=()=>rej(tx.error);
      };
    });
  }catch(e){console.warn('Handoff Auto Rig gagal, pindah tanpa model',e)}
  window.location.href='autorig.html';
}
'''
ai=a_html.rfind('</script>')
if ai<0: raise SystemExit('auto.html module end missing')
a_html=a_html[:ai]+sender+'\n'+a_html[ai:]
auto_path.write_text(a_html,encoding='utf-8')
print('Auto Rig machine v42 generated; Auto button now navigates to autorig.html')
