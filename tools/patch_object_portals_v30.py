from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

if 'OBJECT_PORTALS_V30' in s:
    print('Object portals v30 already applied')
    raise SystemExit(0)
if 'OBJECT_UI_V9' not in s:
    raise SystemExit('Object UI v9 must run first')

# Keep the original Object navigation behavior: Object opens the existing editor directly.
object_nav='<button class="nav" data-go="editorScreen"><b>⬡</b>Object</button>'
if object_nav not in s:
    raise SystemExit('Original Object bottom navigation anchor missing')

# Put Object Mode chooser inside Home, above Quick Actions.
home_anchor='<div class="titleline" style="margin-top:20px"><h2>Quick Actions</h2></div>'
if home_anchor not in s:
    raise SystemExit('Home Quick Actions anchor missing')
portal_html=r'''
      <section id="objectModeHomeV30" class="object-mode-home-v30">
        <div class="omh-title"><b>Object Mode</b><span>Pilih workspace untuk model 3D</span></div>
        <div class="omh-list">
          <button class="omh-card edit" id="objectPortalEditV30" type="button">
            <span class="omh-icon">✦</span>
            <span class="omh-copy"><b>Edit</b><small>Workspace editor lengkap yang sudah dibuat sejauh ini.</small></span>
            <span class="omh-next">›</span>
          </button>
          <button class="omh-card create" id="objectPortalCreateV30" type="button">
            <span class="omh-icon">＋</span>
            <span class="omh-copy"><b>Create</b><small>Mulai dari mesh polos: Skeleton → Rig → Animation.</small></span>
            <span class="omh-next">›</span>
          </button>
        </div>
      </section>
'''
s=s.replace(home_anchor,portal_html+'\n'+home_anchor,1)

css=r'''
/* OBJECT_PORTALS_V30 */
#objectModeHomeV30{margin:8px 0 20px;padding:14px;background:linear-gradient(180deg,#151e29,#101720);border:1px solid #2d3e51;border-radius:18px;box-shadow:0 12px 36px #0005}
#objectModeHomeV30 .omh-title{margin:0 2px 13px}
#objectModeHomeV30 .omh-title b{display:block;font-size:19px;letter-spacing:.01em}
#objectModeHomeV30 .omh-title span{display:block;margin-top:4px;color:#8fa0b4;font-size:12px}
#objectModeHomeV30 .omh-list{display:grid;gap:10px}
#objectModeHomeV30 .omh-card{position:relative;width:100%;min-height:92px;border:1px solid #2d3a49;border-radius:16px;background:#151e28;color:#eef5ff;text-align:left;padding:13px 14px;display:grid;grid-template-columns:52px 1fr 24px;align-items:center;gap:12px;overflow:hidden}
#objectModeHomeV30 .omh-card:active{transform:scale(.99)}
#objectModeHomeV30 .omh-card.edit{border-color:#315d86;background:linear-gradient(135deg,#162538,#15202b)}
#objectModeHomeV30 .omh-card.create{border-color:#27694f;background:linear-gradient(135deg,#122d25,#15221f)}
#objectModeHomeV30 .omh-icon{width:50px;height:50px;border-radius:13px;display:grid;place-items:center;border:1px solid #36506a;background:#101820;font-size:25px}
#objectModeHomeV30 .create .omh-icon{border-color:#34775e;color:#73e2b0}
#objectModeHomeV30 .omh-copy b{display:block;font-size:15px;margin-bottom:4px}
#objectModeHomeV30 .omh-copy small{display:block;color:#9baaba;font-size:11px;line-height:1.4}
#objectModeHomeV30 .omh-next{font-size:22px;color:#78aee7;text-align:right}
'''
if '</style>' not in s:
    raise SystemExit('Style closing tag missing')
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// OBJECT_PORTALS_V30
// Edit is the default application mode and keeps the complete existing editor infrastructure.
document.getElementById('objectPortalEditV30').onclick=()=>go('editorScreen');
document.getElementById('objectPortalCreateV30').onclick=()=>msg('Create workspace dipilih — Skeleton → Rig → Animation');

// App startup goes directly to the existing Edit workspace.
requestAnimationFrame(()=>go('editorScreen'));
'''
idx=s.rfind('</script>')
if idx<0:
    raise SystemExit('Script closing tag missing')
s=s[:idx]+js+'\n'+s[idx:]

p.write_text(s,encoding='utf-8')
print('Object portals v30 applied: original Object restored, chooser on Home, Edit default')
