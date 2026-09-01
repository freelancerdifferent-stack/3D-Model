from pathlib import Path

p=Path('app/src/main/assets/auto.html')
s=p.read_text(encoding='utf-8')

if 'AUTO_MACHINE_RUNTIME_V35' not in s:
    raise SystemExit('Auto machine v35 must run first')
if 'AUTO_VIEWER_V36' in s:
    print('Auto Viewer v36 already applied')
    raise SystemExit(0)

# Viewer uses the existing proven Three.js/animation engine inside Auto, but gets
# an Auto-specific presentation matching the supplied Viewer reference.
css=r'''
/* AUTO_VIEWER_V36 */
html[data-object-machine="auto"] #editorScreen .editor{grid-template-columns:1fr;grid-template-rows:1fr}
html[data-object-machine="auto"] #editorScreen .toolrail{display:none!important}
html[data-object-machine="auto"] #editorScreen .props{display:none!important}
html[data-object-machine="auto"] #editorScreen .viewport{grid-column:1;grid-row:1;background:#17191b}
html[data-object-machine="auto"] #editorScreen .overleft{top:14px;left:18px}
html[data-object-machine="auto"] #editorScreen .overright{top:14px;right:82px}
html[data-object-machine="auto"] #editorScreen .viewtools{top:14px;right:10px;border-radius:12px;background:#101820e8}
html[data-object-machine="auto"] #editorScreen .viewtools button{width:48px;height:46px}
html[data-object-machine="auto"] #editorScreen .timeline{left:13%;right:10%;bottom:112px;height:64px;border-radius:16px;padding:0 14px;background:#0b1018ee;border:1px solid #242d38}
html[data-object-machine="auto"] #editorScreen .timeline #playBtn{font-size:25px}
html[data-object-machine="auto"] #editorScreen .timeline #frameText{font-size:22px;min-width:28px;text-align:center}
html[data-object-machine="auto"] #editorScreen .timeline #durationText{font-size:21px;min-width:44px;text-align:right}
html[data-object-machine="auto"] #editorScreen .timeline input{accent-color:#2f80ff}
html[data-object-machine="auto"] #autoViewerAnimBarV36{position:absolute;z-index:7;left:18px;top:14px;display:flex;gap:10px;align-items:center;max-width:calc(100% - 190px)}
html[data-object-machine="auto"] #autoViewerAnimBarV36 .anim-shell{display:flex;align-items:center;min-width:210px;max-width:340px;height:54px;padding:0 10px 0 16px;border-radius:18px;background:#242424e8;border:1px solid #313131;box-shadow:0 8px 24px #0005}
html[data-object-machine="auto"] #autoViewerAnimBarV36 select{width:100%;border:0;background:transparent;color:#f1f1f1;font-size:18px;outline:none}
html[data-object-machine="auto"] #autoViewerAnimBarV36 select option{background:#14191f;color:#fff}
html[data-object-machine="auto"] #autoViewerDownloadV36{width:54px;height:54px;border:0;border-radius:14px;background:#baff36;color:#071006;font-size:25px;font-weight:900;box-shadow:0 6px 18px #0005}
html[data-object-machine="auto"] #autoViewerClipBarV36{position:absolute;z-index:7;left:24px;right:24px;bottom:28px;height:58px;display:flex;align-items:center;gap:14px;padding:0 14px;border-top:1px solid #242a31;background:#151515dd;color:#f3f3f3;font-size:20px}
html[data-object-machine="auto"] #autoViewerClipBarV36 .clip-arrow{font-size:28px;font-weight:900}
html[data-object-machine="auto"] #autoViewerClipNameV36{font-size:21px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
html[data-object-machine="auto"] #autoViewerClipSourceV36{margin-left:auto;color:#73777d;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:45%}
html[data-object-machine="auto"] #editorScreen .overleft{display:none!important}
@media(max-width:600px){html[data-object-machine="auto"] #autoViewerAnimBarV36{left:12px;max-width:calc(100% - 92px)}html[data-object-machine="auto"] #autoViewerAnimBarV36 .anim-shell{min-width:155px;max-width:250px;height:48px;border-radius:15px}html[data-object-machine="auto"] #autoViewerAnimBarV36 select{font-size:15px}html[data-object-machine="auto"] #autoViewerDownloadV36{width:48px;height:48px;font-size:21px}html[data-object-machine="auto"] #editorScreen .overright{right:66px;top:12px}html[data-object-machine="auto"] #editorScreen .timeline{left:12%;right:10%;bottom:92px;height:54px}html[data-object-machine="auto"] #autoViewerClipBarV36{left:12px;right:12px;bottom:18px;height:50px;font-size:16px}html[data-object-machine="auto"] #autoViewerClipNameV36{font-size:17px}}
'''
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// AUTO_VIEWER_V36
window.__autoMachineRuntimeV35.viewerEngine=true;
window.__autoMachineRuntimeV35.viewerEngineVersion='v36';
requestAnimationFrame(()=>{
  const viewport=document.querySelector('#editorScreen .viewport');
  const animSelect=document.getElementById('animSelect');
  const timeline=document.querySelector('#editorScreen .timeline');
  if(!viewport || !animSelect || !timeline) return;

  // Move the real animation selector into the Viewer top control. Its existing
  // onchange handler stays attached, so clip switching still uses the base engine.
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
  const obs=new MutationObserver(syncClip);
  obs.observe(animSelect,{childList:true,subtree:true});
  const fileLabel=document.getElementById('fileLabel');
  if(fileLabel) new MutationObserver(syncClip).observe(fileLabel,{childList:true,subtree:true});
  syncClip();

  document.getElementById('autoViewerDownloadV36').onclick=()=>{
    const exportBtn=document.getElementById('exportBtn');
    if(!exportBtn){msg('Mesin export tidak tersedia');return}
    exportBtn.click();
  };

  const viewer=document.getElementById('autoViewerNavV35');
  const nav=document.querySelector('.bottomnav');
  if(viewer && nav){
    viewer.onclick=()=>{
      nav.querySelectorAll('.nav').forEach(x=>x.classList.remove('active'));
      viewer.classList.add('active');
      go('editorScreen');
      setTimeout(()=>window.dispatchEvent(new Event('resize')),80);
    };
  }

  // Any successful import that lands on editorScreen is a Viewer transition in Auto.
  const viewerObserver=new MutationObserver(()=>{
    const editor=document.getElementById('editorScreen');
    if(editor?.classList.contains('active') && viewer && nav){
      nav.querySelectorAll('.nav').forEach(x=>x.classList.remove('active'));
      viewer.classList.add('active');
      syncClip();
    }
  });
  viewerObserver.observe(document.getElementById('editorScreen'),{attributes:true,attributeFilter:['class']});
});
'''
s=s.replace('</script>',js+'\n</script>',1)

p.write_text(s,encoding='utf-8')
print('Auto Viewer v36 active: viewport, animation selection/playback/scrub, mesh/view tools and viewer export control')
