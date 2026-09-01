from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

if 'OBJECT_PORTALS_V30' in s:
    print('Object portals v30 already applied')
    raise SystemExit(0)
if 'OBJECT_UI_V9' not in s:
    raise SystemExit('Object UI v9 must run first')

old='<button class="nav" data-go="editorScreen"><b>⬡</b>Object</button>'
new='<button class="nav" id="objectPortalNavV30"><b>⬡</b>Object</button>'
if old not in s:
    raise SystemExit('Object bottom navigation anchor missing')
s=s.replace(old,new,1)

css=r'''
/* OBJECT_PORTALS_V30 */
#objectPortalOverlayV30{position:fixed;inset:0;z-index:1400;display:none;align-items:flex-end;justify-content:center;background:rgba(3,7,12,.72);backdrop-filter:blur(7px);-webkit-backdrop-filter:blur(7px);padding:18px 14px 78px}
#objectPortalOverlayV30.open{display:flex}
#objectPortalSheetV30{width:min(560px,100%);background:linear-gradient(180deg,#151e29,#0d131b);border:1px solid #2d3e51;border-radius:22px;padding:16px;box-shadow:0 20px 70px #000b;animation:objectPortalInV30 .18s ease-out}
@keyframes objectPortalInV30{from{opacity:0;transform:translateY(22px) scale(.98)}to{opacity:1;transform:none}}
#objectPortalSheetV30 .op-head{display:flex;align-items:center;justify-content:space-between;padding:2px 2px 14px}
#objectPortalSheetV30 .op-title b{display:block;font-size:18px;letter-spacing:.02em}
#objectPortalSheetV30 .op-title span{display:block;margin-top:3px;color:#8fa0b4;font-size:11px}
#objectPortalCloseV30{width:36px;height:36px;border:1px solid #314154;border-radius:10px;background:#18222d;color:#cbd7e4;font-size:21px;line-height:1}
#objectPortalSheetV30 .op-list{display:grid;gap:10px}
#objectPortalSheetV30 .op-card{position:relative;width:100%;min-height:92px;border:1px solid #2d3a49;border-radius:16px;background:#151e28;color:#eef5ff;text-align:left;padding:13px 14px;display:grid;grid-template-columns:52px 1fr 24px;align-items:center;gap:12px;overflow:hidden}
#objectPortalSheetV30 .op-card:active{transform:scale(.99)}
#objectPortalSheetV30 .op-card.edit{border-color:#315d86;background:linear-gradient(135deg,#162538,#15202b)}
#objectPortalSheetV30 .op-card.create{border-color:#27694f;background:linear-gradient(135deg,#122d25,#15221f)}
#objectPortalSheetV30 .op-card.auto{opacity:.72;border-color:#604c28;background:linear-gradient(135deg,#2a2214,#191b1d)}
#objectPortalSheetV30 .op-icon{width:50px;height:50px;border-radius:13px;display:grid;place-items:center;border:1px solid #36506a;background:#101820;font-size:25px}
#objectPortalSheetV30 .create .op-icon{border-color:#34775e;color:#73e2b0}
#objectPortalSheetV30 .auto .op-icon{border-color:#745d31;color:#f2c66f}
#objectPortalSheetV30 .op-copy b{display:block;font-size:15px;margin-bottom:4px}
#objectPortalSheetV30 .op-copy small{display:block;color:#9baaba;font-size:11px;line-height:1.4}
#objectPortalSheetV30 .op-next{font-size:22px;color:#78aee7;text-align:right}
#objectPortalSheetV30 .op-badge{position:absolute;right:10px;top:8px;border:1px solid #7a6237;background:#322711;color:#ffd687;border-radius:20px;padding:3px 7px;font-size:8px;font-weight:800;letter-spacing:.08em}
#objectPortalSheetV30 .auto .op-next{color:#756b59;font-size:18px}
#objectPortalNavV30.active{color:#61a6ff;background:#141d28}
body.object-portal-entry-v30 #objectPortalOverlayV30{padding-bottom:18px}
body.object-portal-entry-v30 #objectPortalCloseV30{visibility:hidden;pointer-events:none}
@media (min-width:700px){#objectPortalOverlayV30{align-items:center;padding-bottom:18px}}
'''
if '</style>' not in s:
    raise SystemExit('Style closing tag missing')
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// OBJECT_PORTALS_V30
const objectPortalOverlayV30=document.createElement('div');
objectPortalOverlayV30.id='objectPortalOverlayV30';
objectPortalOverlayV30.innerHTML=`
  <div id="objectPortalSheetV30" role="dialog" aria-modal="true" aria-label="Object Mode">
    <div class="op-head">
      <div class="op-title"><b>Object Mode</b><span>Pilih workspace untuk model 3D</span></div>
      <button id="objectPortalCloseV30" type="button" aria-label="Tutup">×</button>
    </div>
    <div class="op-list">
      <button class="op-card edit" id="objectPortalEditV30" type="button">
        <span class="op-icon">✦</span>
        <span class="op-copy"><b>Edit</b><small>Workspace lengkap yang sudah dibangun sejauh ini.</small></span>
        <span class="op-next">›</span>
      </button>
      <button class="op-card create" id="objectPortalCreateV30" type="button">
        <span class="op-icon">＋</span>
        <span class="op-copy"><b>Create</b><small>Mulai dari mesh polos: Skeleton → Rig → Animation.</small></span>
        <span class="op-next">›</span>
      </button>
      <button class="op-card auto" id="objectPortalAutoV30" type="button" aria-disabled="true">
        <span class="op-badge">EXCLUSIVE · COMING SOON</span>
        <span class="op-icon">⚡</span>
        <span class="op-copy"><b>Auto</b><small>Rigging dan animation otomatis.</small></span>
        <span class="op-next">🔒</span>
      </button>
    </div>
  </div>`;
document.body.appendChild(objectPortalOverlayV30);

const objectPortalNavV30=document.getElementById('objectPortalNavV30');
let objectPortalEntryV30=true;
const openObjectPortalV30=(entry=false)=>{
  objectPortalEntryV30=!!entry;
  document.body.classList.toggle('object-portal-entry-v30',objectPortalEntryV30);
  objectPortalOverlayV30.classList.add('open');
  objectPortalNavV30?.classList.add('active');
};
const closeObjectPortalV30=()=>{
  objectPortalEntryV30=false;
  document.body.classList.remove('object-portal-entry-v30');
  objectPortalOverlayV30.classList.remove('open');
  objectPortalNavV30?.classList.remove('active');
};
objectPortalNavV30?.addEventListener('click',()=>openObjectPortalV30(false));
document.getElementById('objectPortalCloseV30').onclick=closeObjectPortalV30;
objectPortalOverlayV30.addEventListener('click',e=>{if(e.target===objectPortalOverlayV30&&!objectPortalEntryV30)closeObjectPortalV30()});

// EDIT is the complete application/workspace already built in this repository.
// Nothing is duplicated or stripped: all existing import, project, layers, mesh edit,
// materials, Skeleton/Rig, export, offline runtime and Android bridge stay on the same
// infrastructure and become reachable through this portal.
document.getElementById('objectPortalEditV30').onclick=()=>{closeObjectPortalV30();go('editorScreen')};
document.getElementById('objectPortalCreateV30').onclick=()=>{closeObjectPortalV30();msg('Create workspace dipilih — Skeleton → Rig → Animation')};
document.getElementById('objectPortalAutoV30').onclick=()=>msg('Auto adalah fitur Exclusive — Coming Soon');

// First app entry: portal is the gate before entering the existing application workspace.
requestAnimationFrame(()=>openObjectPortalV30(true));
'''
if '</script>' not in s:
    raise SystemExit('Script closing tag missing')
s=s.replace('</script>',js+'\n</script>',1)

p.write_text(s,encoding='utf-8')
print('Object portals v30 applied: startup gate + complete existing workspace under Edit')
