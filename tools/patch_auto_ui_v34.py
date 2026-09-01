from pathlib import Path

assets=Path('app/src/main/assets')
edit_path=assets/'index.html'
auto_path=assets/'auto.html'
s=edit_path.read_text(encoding='utf-8')

if 'OBJECT_PORTALS_V30' not in s:
    raise SystemExit('Object portals v30 must run first')

old="document.getElementById('objectPortalAutoV30').onclick=()=>msg('Auto adalah fitur Exclusive — Coming Soon');"
new="document.getElementById('objectPortalAutoV30').onclick=()=>{window.location.href='auto.html'};"
if old not in s and new not in s:
    raise SystemExit('Auto portal handler not found')
s=s.replace(old,new,1)

# Auto is now selectable in the portal. Keep its gold identity but remove disabled/locked UI.
s=s.replace('id="objectPortalAutoV30" type="button" aria-disabled="true"','id="objectPortalAutoV30" type="button"',1)
s=s.replace('<span class="omh-badge">EXCLUSIVE · COMING SOON</span>','',1)
s=s.replace('<span class="omh-next">🔒</span>','<span class="omh-next">›</span>',1)
s=s.replace('#objectModeHomeV30 .omh-card.auto{opacity:.72;','#objectModeHomeV30 .omh-card.auto{',1)
s=s.replace('#objectModeHomeV30 .auto .omh-next{color:#756b59;font-size:18px}','#objectModeHomeV30 .auto .omh-next{color:#e1b34f;font-size:22px}',1)
edit_path.write_text(s,encoding='utf-8')

auto=r'''<!doctype html>
<html lang="id" data-object-machine="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>3D Viewer & Editor — Auto</title>
<style>
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:#080f13;color:#f4f7fb;font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}body{padding-bottom:92px}.topbar{height:112px;padding:20px 22px;display:flex;align-items:center;gap:18px;border-bottom:1px solid #263441;background:#0d151d}.brand-icon{width:72px;height:72px;border-radius:18px;display:grid;place-items:center;background:linear-gradient(145deg,#58a3ff,#2166d5);font-size:34px}.brand{min-width:0;flex:1}.brand b{display:block;font-size:27px;line-height:1.05}.brand span{display:block;margin-top:5px;color:#67a8ff;font-size:19px}.top-action{border:0;background:transparent;color:#eef5ff;font-size:34px;padding:7px}.page{padding:40px 26px}.mode-card{padding:28px;border:1px solid #314252;border-radius:32px;background:linear-gradient(180deg,#151f2b,#111923);box-shadow:0 18px 48px #0005}.mode-title b{display:block;font-size:36px}.mode-title span{display:block;margin-top:7px;color:#93a1b3;font-size:23px}.mode-list{display:grid;gap:18px;margin-top:25px}.mode{width:100%;min-height:172px;border-radius:28px;padding:26px;border:1px solid;text-align:left;color:#f5f7fa;display:grid;grid-template-columns:94px 1fr 30px;align-items:center;gap:24px;background:#15202a}.mode .icon{width:94px;height:94px;border-radius:24px;display:grid;place-items:center;background:#111a21;border:1px solid;font-size:48px}.mode b{display:block;font-size:28px}.mode small{display:block;margin-top:8px;color:#9ba7b7;font-size:20px;line-height:1.45}.mode .next{font-size:42px}.mode.edit{border-color:#315d86;background:linear-gradient(135deg,#162538,#15202b)}.mode.edit .icon{border-color:#315d86}.mode.edit .next{color:#65a9ee}.mode.create{border-color:#27694f;background:linear-gradient(135deg,#123127,#15231f)}.mode.create .icon{border-color:#34775e;color:#73e2b0}.mode.create .next{color:#65a9ee}.mode.auto{border-color:#665127;background:linear-gradient(135deg,#2b2518,#191b1d)}.mode.auto .icon{border-color:#745d31;color:#e9b52e}.mode.auto .next{color:#65a9ee}.quick-title{font-size:29px;margin:38px 0 18px}.quick{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.quick button{min-height:154px;border:1px solid #2d3b49;border-radius:22px;background:#17212b;color:#f3f6fa;font-size:18px}.quick .qi{display:block;font-size:38px;margin-bottom:13px}.quick button:nth-child(5){grid-column:1}.bottom{position:fixed;left:0;right:0;bottom:0;height:88px;padding-bottom:env(safe-area-inset-bottom);display:grid;grid-template-columns:repeat(5,1fr);background:#0d141c;border-top:1px solid #283745;z-index:20}.bottom button{border:0;background:transparent;color:#70819a;font-size:14px}.bottom button b{display:block;font-size:27px;margin-bottom:4px}.bottom .active{color:#63a9f5;background:#111d2a}.toast{position:fixed;left:50%;bottom:108px;transform:translateX(-50%);padding:10px 15px;border:1px solid #594b2b;border-radius:12px;background:#1d1a12;color:#e7c86f;opacity:0;pointer-events:none;transition:.18s;white-space:nowrap}.toast.show{opacity:1}@media(max-width:600px){.topbar{height:86px;padding:14px 16px;gap:12px}.brand-icon{width:54px;height:54px;border-radius:14px;font-size:25px}.brand b{font-size:20px}.brand span{font-size:14px}.top-action{font-size:26px}.page{padding:28px 18px}.mode-card{padding:20px;border-radius:24px}.mode-title b{font-size:27px}.mode-title span{font-size:17px}.mode-list{gap:12px;margin-top:18px}.mode{min-height:124px;border-radius:21px;padding:18px;grid-template-columns:68px 1fr 22px;gap:16px}.mode .icon{width:68px;height:68px;border-radius:18px;font-size:34px}.mode b{font-size:21px}.mode small{font-size:15px;margin-top:5px}.mode .next{font-size:30px}.quick-title{font-size:22px;margin:30px 0 14px}.quick{gap:10px}.quick button{min-height:110px;border-radius:16px;font-size:14px}.quick .qi{font-size:28px;margin-bottom:8px}.bottom{height:76px}.bottom button{font-size:12px}.bottom button b{font-size:21px}}
</style>
</head>
<body>
<header class="topbar"><div class="brand-icon">⬡</div><div class="brand"><b>3D Viewer & Editor</b><span>AUTO • GLB • FBX • PNG</span></div><button class="top-action" type="button">💾</button><button class="top-action" type="button">＋</button><button class="top-action" type="button">⋮</button></header>
<main class="page"><section class="mode-card"><div class="mode-title"><b>Object Mode</b><span>Pilih workspace untuk model 3D</span></div><div class="mode-list"><button class="mode edit" id="autoToEdit"><span class="icon">✦</span><span><b>Edit</b><small>Workspace editor lengkap yang sudah dibuat sejauh ini.</small></span><span class="next">›</span></button><button class="mode create" id="autoToCreate"><span class="icon">＋</span><span><b>Create</b><small>Mulai dari mesh polos: Skeleton → Rig → Animation.</small></span><span class="next">›</span></button><button class="mode auto" id="autoCurrent"><span class="icon">⚡</span><span><b>Auto</b><small>Rigging dan animation otomatis.</small></span><span class="next">›</span></button></div></section><h2 class="quick-title">Quick Actions</h2><section class="quick"><button><span class="qi">📁</span>Import</button><button><span class="qi">⬡</span>New Scene</button><button><span class="qi">🖼️</span>Texture</button><button><span class="qi">⇧</span>Export</button><button><span class="qi">💾</span>Projects</button></section></main>
<nav class="bottom"><button class="active"><b>⌂</b>Home</button><button><b>✦</b>Toolkit</button><button><b>◌</b>Viewer</button><button><b>▦</b>Assets</button><button><b>⇧</b>Export</button></nav><div class="toast" id="toast">Auto UI preview — mesin belum diaktifkan</div>
<script>
// AUTO_UI_V34 — UI shell only. No Auto editor/rigging/animation engine is started here.
window.__OBJECT_MACHINE__='auto-ui';
window.__AUTO_ENGINE_ENABLED__=false;
const toast=document.getElementById('toast');
function uiOnly(){toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),1300)}
document.getElementById('autoToEdit').onclick=()=>location.href='index.html';
document.getElementById('autoToCreate').onclick=()=>location.href='create.html';
document.getElementById('autoCurrent').onclick=uiOnly;
document.querySelectorAll('.quick button,.bottom button,.top-action').forEach(b=>b.onclick=uiOnly);
</script>
</body></html>
'''
auto_path.write_text(auto,encoding='utf-8')
print('Auto UI v34 generated from supplied design; Auto engine remains disabled')
