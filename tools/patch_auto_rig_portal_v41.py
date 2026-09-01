from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist before Auto Rig portal UI patch')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_PORTAL_V41' in s:
    print('Auto Rig portal v41 already applied'); raise SystemExit(0)
if "window.__OBJECT_MACHINE__='auto';" not in s:
    raise SystemExit('This patch is Auto-machine only')

css=r'''
/* AUTO_RIG_PORTAL_V41 */
html[data-object-machine="auto"] #editorScreen .auto-rig-portal-v41{
  margin-top:auto;min-height:58px;border:0;border-radius:10px;background:transparent;
  color:#19ef45;font-size:10px;flex:none;
}
html[data-object-machine="auto"] #editorScreen .auto-rig-portal-v41 b{
  display:block;font-size:24px;line-height:24px;margin-bottom:5px;color:#19ef45;
}
html[data-object-machine="auto"] #editorScreen .auto-rig-portal-v41:active{
  background:#102a19;box-shadow:0 0 0 1px #19ef4566 inset!important;
}
'''
if '</style>' not in s: raise SystemExit('style end missing')
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// AUTO_RIG_PORTAL_V41
(function(){
  const editor=document.getElementById('editorScreen');
  const rail=editor?.querySelector('.toolrail');
  if(!editor||!rail||document.getElementById('autoRigPortalV41')) return;

  const btn=document.createElement('button');
  btn.type='button';
  btn.id='autoRigPortalV41';
  btn.className='object-extra-tool auto-rig-portal-v41';
  btn.innerHTML='<b>☠</b>Auto Rig';

  const select=rail.querySelector('.object-select-bottom') || rail.querySelector('.tool');
  if(select) rail.insertBefore(btn,select);
  else rail.appendChild(btn);

  btn.addEventListener('click',()=>{
    if(typeof toast==='function') toast('Auto Rig machine belum aktif pada build ini.');
  });
})();
'''
i=s.rfind('</script>')
if i<0: raise SystemExit('script end missing')
s=s[:i]+js+'\n'+s[i:]
p.write_text(s,encoding='utf-8')
print('Auto Rig portal UI v41 applied to Auto machine only')

# Atomic Auto-only pipeline: portal -> machine -> runtime repair.
v42=Path('tools/patch_auto_rig_machine_v42.py')
if not v42.exists(): raise SystemExit('Auto Rig machine v42 patch missing')
exec(compile(v42.read_text(encoding='utf-8'),str(v42),'exec'))

v43=Path('tools/patch_auto_rig_fix_v43.py')
if not v43.exists(): raise SystemExit('Auto Rig fix v43 patch missing')
exec(compile(v43.read_text(encoding='utf-8'),str(v43),'exec'))
