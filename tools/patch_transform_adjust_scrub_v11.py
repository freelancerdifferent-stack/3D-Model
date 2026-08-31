from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'TRANSFORM_ADJUST_SCRUB_V11' in s:
    print('Transform adjust scrub v11 already applied'); raise SystemExit(0)
css=r'''
/* TRANSFORM_ADJUST_SCRUB_V11 */
#editorScreen .adjust-field-wrap{position:relative;min-width:0}
#editorScreen .adjust-field-wrap .field{padding-right:35px}
#editorScreen .adjust-scrub{position:absolute;right:3px;top:3px;bottom:3px;width:29px;border:0;border-left:1px solid #334150;border-radius:0 6px 6px 0;background:#1b2632;color:#8dbdff;font-size:15px;font-weight:700;touch-action:none;cursor:ew-resize;display:grid;place-items:center;padding:0}
#editorScreen .adjust-scrub.active{background:#25486e;color:#fff}
#editorScreen .adjust-scrub:after{content:'↔';line-height:1}
'''
s=s.replace('</style>',css+'\n</style>',1)
js=r'''
// TRANSFORM_ADJUST_SCRUB_V11
(function(){
 const config={
   px:{step:.005,dec:3},py:{step:.005,dec:3},pz:{step:.005,dec:3},
   rx:{step:.25,dec:1},ry:{step:.25,dec:1},rz:{step:.25,dec:1},
   sx:{step:.005,dec:3,min:.001},sy:{step:.005,dec:3,min:.001},sz:{step:.005,dec:3,min:.001}
 };
 Object.entries(config).forEach(([id,cfg])=>{
   const el=$(id); if(!el||el.parentElement?.classList.contains('adjust-field-wrap'))return;
   const wrap=document.createElement('div');wrap.className='adjust-field-wrap';
   el.parentNode.insertBefore(wrap,el);wrap.appendChild(el);
   const h=document.createElement('button');h.type='button';h.className='adjust-scrub';h.setAttribute('aria-label','Adjust '+id+' dengan geser kiri kanan');h.title='Geser kiri / kanan untuk adjust';wrap.appendChild(h);
   let pid=null,startX=0,startVal=0,moved=false;
   const clamp=v=>cfg.min!=null?Math.max(cfg.min,v):v;
   const emitInput=()=>el.dispatchEvent(new Event('input',{bubbles:true}));
   h.addEventListener('pointerdown',e=>{
     e.preventDefault();e.stopPropagation();pid=e.pointerId;startX=e.clientX;startVal=parseFloat(el.value)||0;moved=false;h.classList.add('active');
     try{h.setPointerCapture(pid)}catch(_){}
     // Tell the real undo/redo history this adjustment has started, without opening the keyboard.
     el.dispatchEvent(new Event('focus',{bubbles:false}));
   });
   h.addEventListener('pointermove',e=>{
     if(pid!==e.pointerId)return;e.preventDefault();e.stopPropagation();
     const dx=e.clientX-startX;if(Math.abs(dx)>1)moved=true;
     const v=clamp(startVal+dx*cfg.step);el.value=v.toFixed(cfg.dec);emitInput();
   });
   const finish=e=>{
     if(pid===null||(e.pointerId!=null&&e.pointerId!==pid))return;
     try{h.releasePointerCapture(pid)}catch(_){}pid=null;h.classList.remove('active');
     if(moved)el.dispatchEvent(new Event('change',{bubbles:true}));
   };
   h.addEventListener('pointerup',finish);h.addEventListener('pointercancel',finish);
 });
})();
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('script end missing')
s=s[:idx]+js+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Transform adjust scrub v11 applied')
