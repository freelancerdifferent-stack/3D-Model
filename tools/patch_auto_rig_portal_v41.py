from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist before Auto Rig portal UI patch')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_PORTAL_V41' in s:
    print('Auto Rig portal v41 already applied'); raise SystemExit(0)
if "window.__OBJECT_MACHINE__='auto';" not in s: raise SystemExit('This patch is Auto-machine only')
css=r'''
/* AUTO_RIG_PORTAL_V41 */
html[data-object-machine="auto"] #editorScreen .auto-rig-portal-v41{margin-top:auto;min-height:58px;border:0;border-radius:10px;background:transparent;color:#19ef45;font-size:10px;flex:none}
html[data-object-machine="auto"] #editorScreen .auto-rig-portal-v41 b{display:block;font-size:24px;line-height:24px;margin-bottom:5px;color:#19ef45}
html[data-object-machine="auto"] #editorScreen .auto-rig-portal-v41:active{background:#102a19;box-shadow:0 0 0 1px #19ef4566 inset!important}
'''
s=s.replace('</style>',css+'\n</style>',1)
js=r'''
// AUTO_RIG_PORTAL_V41
(function(){const editor=document.getElementById('editorScreen');const rail=editor?.querySelector('.toolrail');if(!editor||!rail||document.getElementById('autoRigPortalV41'))return;const btn=document.createElement('button');btn.type='button';btn.id='autoRigPortalV41';btn.className='object-extra-tool auto-rig-portal-v41';btn.innerHTML='<b>☠</b>Auto Rig';const select=rail.querySelector('.object-select-bottom')||rail.querySelector('.tool');if(select)rail.insertBefore(btn,select);else rail.appendChild(btn);btn.addEventListener('click',()=>{if(typeof toast==='function')toast('Auto Rig machine belum aktif pada build ini.')});})();
'''
i=s.rfind('</script>');s=s[:i]+js+'\n'+s[i:];p.write_text(s,encoding='utf-8')
print('Auto Rig portal UI v41 applied to Auto machine only')
for script,label in [
 ('tools/patch_auto_rig_machine_v42.py','Auto Rig machine v42'),('tools/patch_auto_rig_fix_v43.py','Auto Rig fix v43'),('tools/patch_auto_rig_height_fix_v44.py','Auto Rig height fix v44'),('tools/patch_auto_rig_centerline_fix_v45.py','Auto Rig centerline fix v45'),('tools/patch_auto_rig_reference_skeleton_v46.py','Auto Rig reference skeleton v46'),('tools/patch_auto_vertical_guide_v47.py','Auto vertical guide v47'),('tools/patch_auto_rig_camera_hide_v48.py','Auto Rig camera/hide v48'),('tools/patch_auto_rig_zoom_v49.py','Auto Rig zoom v49')]:
    q=Path(script)
    if not q.exists(): raise SystemExit(label+' patch missing')
    exec(compile(q.read_text(encoding='utf-8'),str(q),'exec'))
