from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'SKELETON_TOOL_ROUTES_V21' in s:
    print('Skeleton tool routes v21 already applied'); raise SystemExit(0)
if 'SKELETON_LIVE_EDIT_V20' not in s:
    raise SystemExit('Skeleton Live Edit v20 must run first')

# This patch owns bone selection, the Transform panel and rail tool routing only.
# Skeleton history is owned solely by SKELETON_UNDO_REDO_V29.
s=s.replace('</style>',r'''
/* SKELETON_TOOL_ROUTES_V21 — bone selection, Transform panel and tool routing */
</style>''',1)

s=s.replace("let selectedBone=null;\n let skeletonTransformMode='rotate';","let selectedBone=null; window.skeletonSelectedBone=null;\n let skeletonTransformMode='rotate';",1)
old="function chooseBone(x,y){const b=projectedBoneAt(x,y);if(b){selectedBone=b;return true}return false}"
new="""function setSkeletonSelectedBoneV21(b){selectedBone=b||null;window.skeletonSelectedBone=selectedBone;syncSkeletonTransformFieldsV21();return selectedBone}\n function chooseBone(x,y){const b=projectedBoneAt(x,y);if(b){setSkeletonSelectedBoneV21(b);return true}return false}"""
if old not in s: raise SystemExit('chooseBone marker missing')
s=s.replace(old,new,1)
s=s.replace("controls.enabled=true;selectedBone=null;touchId=null;","controls.enabled=true;setSkeletonSelectedBoneV21(null);touchId=null;",1)
s=s.replace("parent.add(b);selectedBone=b;refreshHelper();setSkeletonVisible(true);","parent.add(b);setSkeletonSelectedBoneV21(b);refreshHelper();setSkeletonVisible(true);",1)
s=s.replace("parent.add(b);selectedBone=b;refreshHelper();setSkeletonVisible(true);","parent.add(b);setSkeletonSelectedBoneV21(b);refreshHelper();setSkeletonVisible(true);",1)

old_end="const endTouch=e=>{if(!skeletonLiveEditMode)return;touchId=null;startPos=startQuat=startScale=null};"
new_end="""const endTouch=e=>{if(!skeletonLiveEditMode)return;\n   touchId=null;startPos=startQuat=startScale=null;syncSkeletonTransformFieldsV21();\n };"""
if old_end not in s: raise SystemExit('touch end marker missing')
s=s.replace(old_end,new_end,1)

anchor=" setInterval(()=>{syncHelper();if(skeletonLiveEditMode){controls.enabled=false;const badge=$('liveEditBadge');if(badge){badge.textContent='LIVE EDIT Skeleton';badge.classList.add('on')}}},300);"
if anchor not in s: raise SystemExit('Skeleton interval anchor missing')
route=r'''
 // SKELETON_TOOL_ROUTES_V21
 const transformBtnV21=$('objectTransformToggle');
 const propsV21=editor.querySelector('.props');
 const boneFieldIdsV21=['px','py','pz','rx','ry','rz','sx','sy','sz'];
 function syncSkeletonTransformFieldsV21(){if(!skeletonLiveEditMode||!selectedBone)return;const deg=THREE.MathUtils.radToDeg;const vals={px:selectedBone.position.x,py:selectedBone.position.y,pz:selectedBone.position.z,rx:deg(selectedBone.rotation.x),ry:deg(selectedBone.rotation.y),rz:deg(selectedBone.rotation.z),sx:selectedBone.scale.x,sy:selectedBone.scale.y,sz:selectedBone.scale.z};for(const id of boneFieldIdsV21){const el=$(id);if(el)el.value=Number(vals[id]).toFixed(4).replace(/0+$/,'').replace(/\.$/,'')}}
 function openSkeletonTransformV21(){if(!selectedBone){msg('Pilih bone dulu');return}if(!propsV21)return;const open=propsV21.style.display!=='block';propsV21.style.display=open?'block':'none';if(open){propsV21.style.position='absolute';propsV21.style.left='58px';propsV21.style.right='0';propsV21.style.bottom='0';propsV21.style.zIndex='20';propsV21.style.maxHeight='245px';syncSkeletonTransformFieldsV21()}transformBtnV21?.classList.toggle('active',open)}
 function applySkeletonFieldV21(id,value){if(!selectedBone)return;const n=Number(value);if(!Number.isFinite(n))return;if(id==='px')selectedBone.position.x=n;else if(id==='py')selectedBone.position.y=n;else if(id==='pz')selectedBone.position.z=n;else if(id==='rx')selectedBone.rotation.x=THREE.MathUtils.degToRad(n);else if(id==='ry')selectedBone.rotation.y=THREE.MathUtils.degToRad(n);else if(id==='rz')selectedBone.rotation.z=THREE.MathUtils.degToRad(n);else if(id==='sx')selectedBone.scale.x=n;else if(id==='sy')selectedBone.scale.y=n;else if(id==='sz')selectedBone.scale.z=n;selectedBone.updateMatrixWorld(true);if(typeof skeletonHelper?.update==='function')skeletonHelper.update();syncSkeletonTransformFieldsV21()}
 document.addEventListener('click',ev=>{if(!skeletonLiveEditMode)return;const b=ev.target.closest('button');if(!b)return;if(b===transformBtnV21){ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();openSkeletonTransformV21();return}if(b.classList.contains('tool')){const t=(b.textContent||'').toLowerCase();if(t.includes('move')||t.includes('rotate')||t.includes('scale')){ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();skeletonTransformMode=t.includes('move')?'move':(t.includes('scale')?'scale':'rotate');rail.querySelectorAll('.tool').forEach(x=>x.classList.remove('active'));b.classList.add('active');const badge=$('liveEditBadge');if(badge)badge.textContent='LIVE EDIT Skeleton • '+skeletonTransformMode.toUpperCase();return}}},true);
 for(const id of boneFieldIdsV21){const el=$(id);if(!el)continue;const handler=ev=>{if(!skeletonLiveEditMode||!selectedBone)return;ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();applySkeletonFieldV21(id,el.value)};el.addEventListener('change',handler,true)}
 const oldSkeletonModeClickV21=skeletonModeBtn.onclick;
 skeletonModeBtn.onclick=()=>{
   oldSkeletonModeClickV21?.();
   if(skeletonLiveEditMode)syncSkeletonTransformFieldsV21();
 };
'''
s=s.replace(anchor,route+'\n'+anchor,1)
p.write_text(s,encoding='utf-8')
print('Skeleton tool routes v21 applied: selection, Transform panel and tool routing (no history)')
