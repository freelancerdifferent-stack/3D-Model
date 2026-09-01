from pathlib import Path

p=Path('app/src/main/assets/auto.html')
s=p.read_text(encoding='utf-8')

if 'AUTO_MACHINE_RUNTIME_V35' not in s:
    raise SystemExit('Auto machine v35 must run first')
if 'AUTO_VIEWER_V36' in s:
    print('Auto Viewer v36 already applied')
    raise SystemExit(0)

# Auto Viewer runs only inside auto.html and only against Auto-owned DOM/state.
# No cross-document bridge, parent/opener channel, shared renderer, or external
# mode runtime is referenced here.
css=r'''
/* AUTO_VIEWER_V36 */
html[data-object-machine="auto"] #editorScreen .viewport{background:#17191b}
html[data-object-machine="auto"] #editorScreen .overleft{display:none!important}
html[data-object-machine="auto"] #editorScreen .viewtools{border-radius:12px;background:#101820e8}
html[data-object-machine="auto"] #editorScreen .timeline{border-radius:16px;background:#0b1018ee;border:1px solid #242d38}
html[data-object-machine="auto"] #editorScreen .timeline input{accent-color:#2f80ff}
html[data-object-machine="auto"] #autoViewerAnimBarV36{position:absolute;z-index:7;left:18px;top:14px;display:flex;gap:10px;align-items:center;max-width:calc(100% - 190px)}
html[data-object-machine="auto"] #autoViewerAnimBarV36 .anim-shell{display:flex;align-items:center;min-width:210px;max-width:340px;height:54px;padding:0 10px 0 16px;border-radius:18px;background:#242424e8;border:1px solid #313131;box-shadow:0 8px 24px #0005}
html[data-object-machine="auto"] #autoViewerAnimBarV36 select{width:100%;border:0;background:transparent;color:#f1f1f1;font-size:18px;outline:none}
html[data-object-machine="auto"] #autoViewerAnimBarV36 select option{background:#14191f;color:#fff}
html[data-object-machine="auto"] #autoViewerDownloadV36{width:54px;height:54px;border:0;border-radius:14px;background:#baff36;color:#071006;font-size:25px;font-weight:900;box-shadow:0 6px 18px #0005}
html[data-object-machine="auto"] #autoViewerClipBarV36{position:absolute;z-index:7;left:18px;right:18px;bottom:18px;height:58px;display:flex;align-items:center;gap:14px;padding:0 14px;border-top:1px solid #242a31;background:#151515dd;color:#f3f3f3;font-size:20px}
html[data-object-machine="auto"] #autoViewerClipBarV36 .clip-arrow{font-size:28px;font-weight:900}
html[data-object-machine="auto"] #autoViewerClipNameV36{font-size:21px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
html[data-object-machine="auto"] #autoViewerClipSourceV36{margin-left:auto;color:#73777d;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:45%}
@media(max-width:600px){html[data-object-machine="auto"] #autoViewerAnimBarV36{left:12px;max-width:calc(100% - 92px)}html[data-object-machine="auto"] #autoViewerAnimBarV36 .anim-shell{min-width:155px;max-width:250px;height:48px;border-radius:15px}html[data-object-machine="auto"] #autoViewerAnimBarV36 select{font-size:15px}html[data-object-machine="auto"] #autoViewerDownloadV36{width:48px;height:48px;font-size:21px}html[data-object-machine="auto"] #autoViewerClipBarV36{left:12px;right:12px;bottom:12px;height:50px;font-size:16px}html[data-object-machine="auto"] #autoViewerClipNameV36{font-size:17px}}
'''
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// AUTO_VIEWER_V36
window.__autoMachineRuntimeV35.viewerEngine=true;
window.__autoMachineRuntimeV35.viewerEngineVersion='v36-auto-native';
window.__autoViewerRuntimeV36={
  owner:'auto',
  isolated:true,
  crossModeBridge:false
};
requestAnimationFrame(()=>{
  const editor=document.getElementById('editorScreen');
  const viewport=editor?.querySelector('.viewport');
  const animSelect=document.getElementById('animSelect');
  if(!editor || !viewport || !animSelect) return;

  const oldWrap=animSelect.parentElement;
  const bar=document.createElement('div');
  bar.id='autoViewerAnimBarV36';
  bar.innerHTML='<div class="anim-shell"></div><button id="autoViewerDownloadV36" type="button">⇩</button>';
  viewport.appendChild(bar);
  bar.querySelector('.anim-shell').appendChild(animSelect);
  if(oldWrap && oldWrap!==bar && oldWrap.children.length===0) oldWrap.remove();

  const clipBar=document.createElement('div');
  clipBar.id='autoViewerClipBarV36';
  clipBar.innerHTML='<span class="clip-arrow">⌄</span><span id="autoViewerClipNameV36">No Animation</span><span id="autoViewerClipSourceV36">No model loaded</span>';
  viewport.appendChild(clipBar);

  const syncClip=()=>{
    const label=document.getElementById('autoViewerClipNameV36');
    const source=document.getElementById('autoViewerClipSourceV36');
    if(label) label.textContent=animSelect.options[animSelect.selectedIndex]?.textContent || 'No Animation';
    if(source) source.textContent=document.getElementById('fileLabel')?.textContent || 'No model loaded';
  };
  animSelect.addEventListener('change',syncClip);
  new MutationObserver(syncClip).observe(animSelect,{childList:true,subtree:true});
  const fileLabel=document.getElementById('fileLabel');
  if(fileLabel) new MutationObserver(syncClip).observe(fileLabel,{childList:true,subtree:true});
  syncClip();

  document.getElementById('autoViewerDownloadV36').onclick=()=>document.getElementById('exportBtn')?.click();

  const viewer=document.getElementById('autoViewerNavV35');
  const nav=document.querySelector('.bottomnav');
  const activateViewer=()=>{
    if(viewer && nav){nav.querySelectorAll('.nav').forEach(x=>x.classList.remove('active'));viewer.classList.add('active')}
    go('editorScreen');
    requestAnimationFrame(()=>window.dispatchEvent(new Event('resize')));
  };
  if(viewer) viewer.onclick=activateViewer;

  new MutationObserver(()=>{
    if(editor.classList.contains('active')){
      if(viewer && nav){nav.querySelectorAll('.nav').forEach(x=>x.classList.remove('active'));viewer.classList.add('active')}
      syncClip();
      requestAnimationFrame(()=>window.dispatchEvent(new Event('resize')));
    }
  }).observe(editor,{attributes:true,attributeFilter:['class']});
});
'''
s=s.replace('</script>',js+'\n</script>',1)

p.write_text(s,encoding='utf-8')
print('Auto Viewer v36 isolated: no cross-mode runtime bridge')
