from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist')
s=p.read_text(encoding='utf-8')
if 'ANIM_LIB_RESTOFFSET_V60' in s:
    print('Anim lib restoffset v60 already applied'); raise SystemExit(0)
if 'ANIM_LIB_BINDPOSE_V59' not in s: raise SystemExit('v59 must run first')

# Bahu/lengan ketarik mengikuti pose mannequin: mode salin-lokal v59 memindah
# rotasi ABSOLUT library sehingga selisih rest pose (~26 derajat di bahu)
# ikut terbawa. v60: untuk rig sekeluarga, yang disalin adalah DELTA lokal
# terhadap rest library, diterapkan di atas rest milik TARGET
# (q' = q_ref(t) * inv(q_ref_rest) * q_tgt_rest) - gerakan mengikuti klip,
# postur dasar tetap milik model.
old_cap='''    root.traverse(o=>{if(o.isBone)restMap.set(o,{p:o.position.clone(),
      wq:o.getWorldQuaternion(new THREE.Quaternion()),wp:o.getWorldPosition(new THREE.Vector3())})});'''
new_cap='''    root.traverse(o=>{if(o.isBone)restMap.set(o,{p:o.position.clone(),lq:o.quaternion.clone(),
      wq:o.getWorldQuaternion(new THREE.Quaternion()),wp:o.getWorldPosition(new THREE.Vector3())})});'''
if old_cap not in s: raise SystemExit('captureRest traverse anchor missing')
s=s.replace(old_cap,new_cap,1)

old_copy='''        if(familyV59&&chainOkV59){
          // rig sekeluarga: salin lokal apa adanya (transfer eksak)
          tracks.push(new THREE.QuaternionKeyframeTrack(tb.name+'.quaternion',Array.from(tr.times),Array.from(tr.values)));
        }else if(familyV59){'''
new_copy='''        if(familyV59&&chainOkV59){
          // ANIM_LIB_RESTOFFSET_V60: delta lokal thd rest library di atas rest target
          const postV60=rn.quaternion.clone().invert().multiply(R.restMap.get(tb).lq);
          const preV60=(nodeName==='LeftUpLeg')?spreadV60.L:((nodeName==='RightUpLeg')?spreadV60.R:null);
          const vals=new Float32Array(tr.values.length);
          for(let i=0;i<tr.values.length;i+=4){
            q.fromArray(tr.values,i);
            q.multiply(postV60);
            if(preV60)q.premultiply(preV60);
            q.normalize();
            q.toArray(vals,i);
          }
          tracks.push(new THREE.QuaternionKeyframeTrack(tb.name+'.quaternion',Array.from(tr.times),Array.from(vals)));
        }else if(familyV59){'''
if old_copy not in s: raise SystemExit('family copy anchor missing')
s=s.replace(old_copy,new_copy,1)

old_spread="""      if(!familyV59)KHV59.identity();
    }"""
new_spread="""      if(!familyV59)KHV59.identity();
    }
    // ANIM_LIB_RESTOFFSET_V60: pelebar sikap kaki - bukaan kaki sumber
    // diskalakan ke panjang kaki target agar tumit tidak saling sentuh
    const spreadV60={L:new THREE.Quaternion(),R:new THREE.Quaternion()};
    if(familyV59)try{
      const tfL=bones.LeftFoot,tfR=bones.RightFoot,ttL=bones.LeftUpLeg,ttR=bones.RightUpLeg;
      const rfL=refNodes.LeftFoot,rfR=refNodes.RightFoot,rtL=refNodes.LeftUpLeg,rtR=refNodes.RightUpLeg;
      if(tfL&&tfR&&ttL&&ttR&&rfL&&rfR&&rtL&&rtR){
        const P=o=>R.restMap.get(o).wp;
        const W=o=>o.getWorldPosition(new THREE.Vector3());
        const latT=P(ttL).clone().sub(P(ttR));const wT=latT.length();latT.normalize();
        const latR=W(rtL).clone().sub(W(rtR));const wR=latR.length();latR.normalize();
        const sepT=P(tfL).clone().sub(P(tfR)).dot(latT);
        const sepR=W(rfL).clone().sub(W(rfR)).dot(latR);
        const legT=P(tfL).distanceTo(P(ttL)),legR=Math.max(W(rfL).distanceTo(W(rtL)),1e-4);
        const desired=wT+(sepR-wR)*(legT/legR);
        const ang=Math.asin(Math.max(-0.5,Math.min(0.5,((desired-sepT)/2)/Math.max(legT,1e-4))));
        const fwdT=new THREE.Vector3().crossVectors(latT,new THREE.Vector3(0,1,0)).normalize();
        const mkV60=(sign,tb2)=>{
          const dq=new THREE.Quaternion().setFromAxisAngle(fwdT,sign*ang);
          const pq=(tb2.parent&&tb2.parent.isBone&&R.restMap.get(tb2.parent))?R.restMap.get(tb2.parent).wq:R.rootWQ;
          return pq.clone().invert().multiply(dq).multiply(pq);
        };
        spreadV60.L=mkV60(1,ttL);spreadV60.R=mkV60(-1,ttR);
      }
    }catch(_){ }"""
if old_spread not in s: raise SystemExit('family tail anchor missing')
s=s.replace(old_spread,new_spread,1)

p.write_text(s,encoding='utf-8')
print('Anim lib restoffset v60: delta lokal di atas rest target untuk rig sekeluarga')
