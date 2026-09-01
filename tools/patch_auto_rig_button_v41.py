from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists():
    raise SystemExit('auto.html must be built by patch_auto_machine_v39 first')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_BUTTON_V41' in s:
    print('Auto Rig button v41 already applied'); raise SystemExit(0)
if 'AUTO_MACHINE_V39' not in s:
    raise SystemExit('Auto machine v39 marker missing in auto.html')

# Auto machine only: a portal button in the Object tool rail. It will route to the
# dedicated Auto Rig machine once that machine exists; today it only announces itself.
css=r'''
/* AUTO_RIG_BUTTON_V41 */
#editorScreen .auto-rig-portal-v41{color:#39e75f}
#editorScreen .auto-rig-portal-v41 b{color:#39e75f}
#editorScreen .auto-rig-portal-v41:active{background:#12351c;box-shadow:inset 0 0 0 1px #2f9950}
'''
if '</style>' not in s: raise SystemExit('style end missing')
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
// AUTO_RIG_BUTTON_V41 — portal to the future Auto Rig machine (UI only for now).
(function(){
 const editor=$('editorScreen'), rail=editor?.querySelector('.toolrail');
 if(!editor||!rail)return;
 const b=document.createElement('button');
 b.type='button';
 b.id='autoRigPortalBtnV41';
 b.className='object-extra-tool auto-rig-portal-v41';
 b.innerHTML='<b>☠</b>Auto Rig';
 const anchor=$('liveEditSelectBtn');
 if(anchor&&anchor.parentElement===rail)rail.insertBefore(b,anchor);
 else rail.appendChild(b);
 // Placeholder route: replaced by real navigation once the Auto Rig machine is built.
 b.onclick=()=>msg('Auto Rig — mesin khususnya akan dibangun berikutnya');
})();
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('module script end missing')
s=s[:idx]+js+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Auto Rig portal button v41 added to the Auto machine tool rail')
