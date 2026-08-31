from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

if 'PART_LONGPRESS_FIX_V2' in s:
    print('Long-press fix already applied')
    raise SystemExit(0)

marker='const PART_LONGPRESS_MOVE_TOLERANCE=14;'
if marker not in s:
    raise SystemExit('Long-press state marker missing')
s=s.replace(marker, marker+"\nconst PART_LONGPRESS_FIX_V2=true;\nlet partLongPressHolding=false;\nlet partLongPressPrevControlsEnabled=true;",1)

# Keep OrbitControls from consuming the hold before the 3s timer fires.
start=s.find('function beginPartLongPress(ev){')
end=s.find('\nfunction trackPartLongPress(ev){',start)
if start<0 or end<0: raise SystemExit('beginPartLongPress block missing')
new_begin=r'''function beginPartLongPress(ev){
  if(ev.pointerType==='mouse'&&ev.button!==0)return;
  closePartContextMenu();
  cancelPartLongPress();
  partLongPressPointerId=ev.pointerId;
  partLongPressStartX=partLongPressLastX=ev.clientX;
  partLongPressStartY=partLongPressLastY=ev.clientY;
  partLongPressTriggered=false;
  partLongPressHolding=true;

  // Temporarily freeze camera orbit while the finger is being held. Without
  // this, OrbitControls consumes the same Android pointer gesture and the hold
  // is cancelled before the 3 second timer can fire.
  partLongPressPrevControlsEnabled=controls.enabled;
  controls.enabled=false;

  const vr=canvas.parentElement.getBoundingClientRect();
  const ring=$('partHoldRing');
  if(ring){
    ring.style.left=(ev.clientX-vr.left)+'px';
    ring.style.top=(ev.clientY-vr.top)+'px';
    ring.classList.add('on');
  }
  partLongPressTimer=setTimeout(triggerPartLongPress,PART_LONGPRESS_MS);
}'''
s=s[:start]+new_begin+s[end:]

start=s.find('function trackPartLongPress(ev){')
end=s.find('\nfunction endPartLongPress(ev){',start)
if start<0 or end<0: raise SystemExit('trackPartLongPress block missing')
new_track=r'''function trackPartLongPress(ev){
  if(ev.pointerId!==partLongPressPointerId)return;
  partLongPressLastX=ev.clientX;partLongPressLastY=ev.clientY;
  if(Math.hypot(ev.clientX-partLongPressStartX,ev.clientY-partLongPressStartY)>PART_LONGPRESS_MOVE_TOLERANCE){
    const wasHolding=partLongPressHolding;
    cancelPartLongPress();
    partLongPressHolding=false;
    if(wasHolding)controls.enabled=partLongPressPrevControlsEnabled;
  }
}'''
s=s[:start]+new_track+s[end:]

start=s.find('function endPartLongPress(ev){')
end=s.find('\nfunction choosePartContextMode(mode){',start)
if start<0 or end<0: raise SystemExit('endPartLongPress block missing')
new_end=r'''function endPartLongPress(ev){
  if(ev.pointerId!==partLongPressPointerId)return;
  const triggered=partLongPressTriggered;
  cancelPartLongPress();
  partLongPressHolding=false;
  // If popup did not open, restore the camera immediately. If it did open,
  // keep controls disabled until a mode is chosen or the popup is dismissed.
  if(!triggered)controls.enabled=partLongPressPrevControlsEnabled;
  if(triggered){
    ev.preventDefault();ev.stopPropagation();
    if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();
  }
}'''
s=s[:start]+new_end+s[end:]

# Ensure successful trigger does not call cancelPartLongPress() after setting the
# trigger flag; that helper clears pointer state and could race with pointerup.
old=r'''function triggerPartLongPress(){
  partLongPressTimer=null;
  const hit=partPickAt(partLongPressLastX,partLongPressLastY);
  if(!hit){cancelPartLongPress();return}
  partLongPressTriggered=true;
  if(navigator.vibrate)try{navigator.vibrate(35)}catch(_){ }
  openPartContextMenu(hit.object,partLongPressLastX,partLongPressLastY);
  const r=$('partHoldRing');if(r)r.classList.remove('on');
}'''
new=r'''function triggerPartLongPress(){
  partLongPressTimer=null;
  const hit=partPickAt(partLongPressLastX,partLongPressLastY);
  if(!hit){
    const prev=partLongPressPrevControlsEnabled;
    cancelPartLongPress();
    partLongPressHolding=false;
    controls.enabled=prev;
    msg('Part tidak terdeteksi — tahan tepat di permukaan model');
    return;
  }
  partLongPressTriggered=true;
  partLongPressHolding=false;
  if(navigator.vibrate)try{navigator.vibrate(35)}catch(_){ }
  openPartContextMenu(hit.object,partLongPressLastX,partLongPressLastY);
  const r=$('partHoldRing');if(r)r.classList.remove('on');
}'''
if old not in s: raise SystemExit('triggerPartLongPress block missing')
s=s.replace(old,new,1)

# Tapping outside the popup closes it and restores orbit controls.
handler="$('partContextMenu').addEventListener('pointerdown',ev=>ev.stopPropagation());"
if handler not in s: raise SystemExit('context menu handler missing')
extra=handler+r'''
partGestureSurface.addEventListener('pointerdown',ev=>{
  const menu=$('partContextMenu');
  if(menu?.classList.contains('on') && !menu.contains(ev.target)){
    closePartContextMenu();
    controls.enabled=true;
  }
},{capture:true});'''
s=s.replace(handler,extra,1)

p.write_text(s,encoding='utf-8')
print('Long-press popup Android gesture fix applied')
