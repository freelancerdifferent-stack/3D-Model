from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist')
s=p.read_text(encoding='utf-8')
if 'ANIM_LIB_SMARTMAP_V56' in s:
    print('Anim lib smartmap v56 already applied'); raise SystemExit(0)
if 'ANIM_LIBRARY_V52' not in s or 'AUTO_RIG_ALIGN_V54' not in s:
    raise SystemExit('v52 dan v54 must run first')

# Library animasi (Walking/Running) kini bisa dipasang ke rig bernama lain
# (UE: pelvis/upperarm_l, mixamo, dll.):
#   - pemetaan pintar v54 diekspos dan dipakai untuk menerjemahkan nama tulang
#     referensi (Hips, LeftArm, ...) ke tulang rig target lewat PERAN-nya
#   - rest pose disimpan per-objek tulang (Map), bukan per-nama alias, sehingga
#     induk yang tidak terpetakan (mis. twist bone di tengah rantai) tetap
#     dihitung dengan rotasi rest yang benar
#   - nama track hasil retarget memakai nama tulang TARGET sehingga binding
#     mixer mengenai tulang yang benar

# 1) ekspos pemetaan pintar dari closure wizard
old_ex="window.__autoRigV50Debug={hasOldRig:hasOldRigV50,root:()=>root,meshList:()=>((typeof meshList!=='undefined')?meshList:null)};"
new_ex=old_ex+"\n  window.__mapCoreBonesV54=()=>mapCoreBonesV54(); // ANIM_LIB_SMARTMAP_V56"
if old_ex not in s: raise SystemExit('v50 debug anchor missing')
s=s.replace(old_ex,new_ex,1)

# 2) rest pose per-objek tulang
old_cr='''  function captureRest(bones){
    if(root.userData.animRestV52)return root.userData.animRestV52;
    root.updateMatrixWorld(true);
    const rest={};
    for(const k in bones){const b=bones[k];rest[k]={p:b.position.clone(),
      wq:b.getWorldQuaternion(new THREE.Quaternion()),wp:b.getWorldPosition(new THREE.Vector3())}}
    const bb=new THREE.Box3().setFromObject(root);
    root.userData.animRestV52={rest,groundY:bb.min.y,
      rootWQ:root.getWorldQuaternion(new THREE.Quaternion()),rootWS:root.getWorldScale(new THREE.Vector3())};
    return root.userData.animRestV52;
  }'''
new_cr='''  function captureRest(bones){
    if(root.userData.animRestV52)return root.userData.animRestV52;
    root.updateMatrixWorld(true);
    const restMap=new Map();
    root.traverse(o=>{if(o.isBone)restMap.set(o,{p:o.position.clone(),
      wq:o.getWorldQuaternion(new THREE.Quaternion()),wp:o.getWorldPosition(new THREE.Vector3())})});
    const bb=new THREE.Box3().setFromObject(root);
    root.userData.animRestV52={restMap,groundY:bb.min.y,
      rootWQ:root.getWorldQuaternion(new THREE.Quaternion()),rootWS:root.getWorldScale(new THREE.Vector3())};
    return root.userData.animRestV52;
  }'''
if old_cr not in s: raise SystemExit('captureRest anchor missing')
s=s.replace(old_cr,new_cr,1)

# 3) rumus retarget membaca restMap dan menamai track dengan nama tulang target
subs=[
("const tqp=(tb.parent&&tb.parent.isBone&&R.rest[tb.parent.name])?R.rest[tb.parent.name].wq:R.rootWQ;",
 "const tqp=(tb.parent&&tb.parent.isBone&&R.restMap.get(tb.parent))?R.restMap.get(tb.parent).wq:R.rootWQ;"),
("const post=QbI.clone().multiply(R.rest[nodeName].wq);",
 "const post=QbI.clone().multiply(R.restMap.get(tb).wq);"),
("tracks.push(new THREE.QuaternionKeyframeTrack(nodeName+'.quaternion',Array.from(tr.times),Array.from(vals)));",
 "tracks.push(new THREE.QuaternionKeyframeTrack(tb.name+'.quaternion',Array.from(tr.times),Array.from(vals)));"),
("const tgtH=Math.max(R.rest.Hips.wp.y-R.groundY,1e-4);",
 "const tgtH=Math.max(R.restMap.get(bones.Hips).wp.y-R.groundY,1e-4);"),
("v.applyQuaternion(rq).divide(R.rootWS).add(R.rest.Hips.p);",
 "v.applyQuaternion(rq).divide(R.rootWS).add(R.restMap.get(bones.Hips).p);"),
("tracks.push(new THREE.VectorKeyframeTrack('Hips.position',Array.from(tr.times),Array.from(vals)));",
 "tracks.push(new THREE.VectorKeyframeTrack(bones.Hips.name+'.position',Array.from(tr.times),Array.from(vals)));"),
]
for old,new in subs:
    if old not in s: raise SystemExit('retarget anchor missing: '+old[:50])
    s=s.replace(old,new,1)

# 4) guard: bila nama referensi tak ada, terjemahkan lewat peran tulang v54
old_g='''    const bones={};root.traverse(o=>{if(o.isBone)bones[o.name]=o});
    if(!bones.Hips||!bones.LeftArm||!bones.RightUpLeg){
      say('Model belum punya rig yang cocok — jalankan Auto Rig dulu');return false}'''
new_g='''    const bones={};root.traverse(o=>{if(o.isBone)bones[o.name]=o});
    if(!bones.Hips||!bones.LeftArm||!bones.RightUpLeg){
      // ANIM_LIB_SMARTMAP_V56: nama referensi tak ada - petakan lewat peran
      const m=(typeof window.__mapCoreBonesV54==='function')?window.__mapCoreBonesV54():null;
      if(!m||!m.ok){say('Model belum punya rig yang cocok — jalankan Auto Rig dulu');return false}
      const alias={};
      if(m.hips)alias.Hips=m.hips;
      const sp=m.spine||[];
      if(sp.length){
        alias.Spine02=sp[0];
        alias.Spine=sp[sp.length-1];
        if(sp.length>=3)alias.Spine01=sp[Math.floor((sp.length-1)/2)];
      }
      if(m.neck&&m.neck.length)alias.neck=m.neck[0];
      if(m.head)alias.Head=m.head;
      const rolesV56={Shoulder:'clav',Arm:'upperarm',ForeArm:'forearm',Hand:'hand',UpLeg:'thigh',Leg:'calf',Foot:'foot',ToeBase:'toe'};
      for(const [pre,sk] of [['Left','L'],['Right','R']]){
        for(const [suf,role] of Object.entries(rolesV56)){
          const b=m.sided&&m.sided[role]&&m.sided[role][sk];
          if(b)alias[pre+suf]=b;
        }
      }
      for(const [refName,b] of Object.entries(alias)){if(b&&!bones[refName])bones[refName]=b}
      if(!bones.Hips||!bones.LeftArm||!bones.RightUpLeg){
        say('Model belum punya rig yang cocok — jalankan Auto Rig dulu');return false}
      say('Rig dikenali — animasi dipetakan lewat peran tulang');
    }'''
if old_g not in s: raise SystemExit('guard anchor missing')
s=s.replace(old_g,new_g,1)

p.write_text(s,encoding='utf-8')
print('Anim lib smartmap v56: Walking/Running bisa dipasang ke rig bernama lain')
