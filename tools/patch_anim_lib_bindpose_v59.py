from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist')
s=p.read_text(encoding='utf-8')
if 'ANIM_LIB_BINDPOSE_V59' in s:
    print('Anim lib bindpose v59 already applied'); raise SystemExit(0)
if 'ANIM_LIB_SMARTMAP_V56' not in s: raise SystemExit('v56 must run first')

# Dua perbaikan untuk kaki menyilang saat klip library dipasang:
# 1. Rest pose acuan direkam dari BIND POSE murni (stopAllAction +
#    skeleton.pose()), bukan dari pose frame animasi yang kebetulan tampil.
# 2. Deteksi RIG SEKELUARGA: bila orientasi rest tulang target serupa dengan
#    tulang library (selisihnya seragam <25 derajat, mis. mannequin UE ->
#    NYX yang sama-sama skeleton Epic), quaternion lokal DISALIN LANGSUNG -
#    transfer eksak tanpa artefak sumbu. Rumus world-delta lama tetap dipakai
#    untuk rig beda keluarga (hasil Auto Rig yang rest-nya identitas, biped).
old_cr='''  function captureRest(bones){
    if(root.userData.animRestV52)return root.userData.animRestV52;
    root.updateMatrixWorld(true);
    const restMap=new Map();'''
new_cr='''  function captureRest(bones){
    if(root.userData.animRestV52)return root.userData.animRestV52;
    // ANIM_LIB_BINDPOSE_V59: acuan retarget HARUS bind pose murni
    try{
      if(typeof mixer!=='undefined'&&mixer){mixer.stopAllAction();mixer.timeScale=0}
      const skelsV59=new Set();
      root.traverse(o=>{if(o.isSkinnedMesh&&o.skeleton)skelsV59.add(o.skeleton)});
      for(const skV59 of skelsV59)skV59.pose();
    }catch(_){ }
    root.updateMatrixWorld(true);
    const restMap=new Map();'''
if old_cr not in s: raise SystemExit('captureRest anchor missing')
s=s.replace(old_cr,new_cr,1)

old_pre='''    const tracks=[];const q=new THREE.Quaternion();const v=new THREE.Vector3();'''
new_pre='''    const tracks=[];const q=new THREE.Quaternion();const v=new THREE.Vector3();
    // ANIM_LIB_BINDPOSE_V59: deteksi rig sekeluarga + rotasi penyelaras global
    const mappedSetV59=new Set(Object.values(bones));
    const KHV59=new THREE.Quaternion();let familyV59=false;
    {
      const rh=refNodes['Hips'],th=bones['Hips'];
      if(rh&&th&&R.restMap.get(th)){
        KHV59.copy(R.restMap.get(th).wq).multiply(rh.getWorldQuaternion(new THREE.Quaternion()).invert());
        let ok=0,tot=0;
        for(const nmV of ['LeftUpLeg','RightUpLeg','LeftArm','RightArm','Spine','LeftLeg','RightLeg','LeftForeArm','RightForeArm']){
          const rn2=refNodes[nmV],tb2=bones[nmV];
          if(!rn2||!tb2||!R.restMap.get(tb2))continue;
          const Kb=R.restMap.get(tb2).wq.clone().multiply(rn2.getWorldQuaternion(new THREE.Quaternion()).invert());
          tot++;if(KHV59.angleTo(Kb)<0.79)ok++;
        }
        familyV59=tot>=4&&ok===tot;
      }
      if(!familyV59)KHV59.identity();
    }'''
if old_pre not in s: raise SystemExit('tracks init anchor missing')
s=s.replace(old_pre,new_pre,1)

old_q='''      if(prop==='quaternion'){
        const Qp=rn.parent.getWorldQuaternion(new THREE.Quaternion());
        const QbI=rn.getWorldQuaternion(new THREE.Quaternion()).invert();
        const tqp=(tb.parent&&tb.parent.isBone&&R.restMap.get(tb.parent))?R.restMap.get(tb.parent).wq:R.rootWQ;
        const pre=tqp.clone().invert().multiply(Qp);
        const post=QbI.clone().multiply(R.restMap.get(tb).wq);
        const vals=new Float32Array(tr.values.length);
        for(let i=0;i<tr.values.length;i+=4){
          q.fromArray(tr.values,i);
          q.copy(pre.clone().multiply(q).multiply(post)).normalize();
          q.toArray(vals,i);
        }
        tracks.push(new THREE.QuaternionKeyframeTrack(tb.name+'.quaternion',Array.from(tr.times),Array.from(vals)));
      }else if(prop==='position'&&nodeName==='Hips'){'''
new_q='''      if(prop==='quaternion'){
        const chainOkV59=tb.parent&&tb.parent.isBone&&mappedSetV59.has(tb.parent);
        if(familyV59&&chainOkV59){
          // rig sekeluarga: salin lokal apa adanya (transfer eksak)
          tracks.push(new THREE.QuaternionKeyframeTrack(tb.name+'.quaternion',Array.from(tr.times),Array.from(tr.values)));
        }else if(familyV59){
          // akar rantai (Hips): selaraskan dengan rotasi global K
          const Qp=rn.parent.getWorldQuaternion(new THREE.Quaternion());
          const tqp=(tb.parent&&tb.parent.isBone&&R.restMap.get(tb.parent))?R.restMap.get(tb.parent).wq:R.rootWQ;
          const pre=tqp.clone().invert().multiply(KHV59).multiply(Qp);
          const vals=new Float32Array(tr.values.length);
          for(let i=0;i<tr.values.length;i+=4){
            q.fromArray(tr.values,i);
            q.copy(pre.clone().multiply(q)).normalize();
            q.toArray(vals,i);
          }
          tracks.push(new THREE.QuaternionKeyframeTrack(tb.name+'.quaternion',Array.from(tr.times),Array.from(vals)));
        }else{
          const Qp=rn.parent.getWorldQuaternion(new THREE.Quaternion());
          const QbI=rn.getWorldQuaternion(new THREE.Quaternion()).invert();
          const tqp=(tb.parent&&tb.parent.isBone&&R.restMap.get(tb.parent))?R.restMap.get(tb.parent).wq:R.rootWQ;
          const pre=tqp.clone().invert().multiply(Qp);
          const post=QbI.clone().multiply(R.restMap.get(tb).wq);
          const vals=new Float32Array(tr.values.length);
          for(let i=0;i<tr.values.length;i+=4){
            q.fromArray(tr.values,i);
            q.copy(pre.clone().multiply(q).multiply(post)).normalize();
            q.toArray(vals,i);
          }
          tracks.push(new THREE.QuaternionKeyframeTrack(tb.name+'.quaternion',Array.from(tr.times),Array.from(vals)));
        }
      }else if(prop==='position'&&nodeName==='Hips'){'''
if old_q not in s: raise SystemExit('quaternion branch anchor missing')
s=s.replace(old_q,new_q,1)

old_p='''          v.fromArray(tr.values,i).applyMatrix4(pm).sub(refRestW).multiplyScalar(ratio);
          v.applyQuaternion(rq).divide(R.rootWS).add(R.restMap.get(bones.Hips).p);'''
new_p='''          v.fromArray(tr.values,i).applyMatrix4(pm).sub(refRestW).multiplyScalar(ratio);
          v.applyQuaternion(KHV59).applyQuaternion(rq).divide(R.rootWS).add(R.restMap.get(bones.Hips).p);'''
if old_p not in s: raise SystemExit('hips position anchor missing')
s=s.replace(old_p,new_p,1)

p.write_text(s,encoding='utf-8')
print('Anim lib bindpose+family v59: bind pose murni + salin-lokal untuk rig sekeluarga')
