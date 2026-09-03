from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist')
s=p.read_text(encoding='utf-8')
if 'ANIM_LIB_GROUNDFACE_V62' in s:
    print('Anim lib groundface v62 already applied'); raise SystemExit(0)
if 'ANIM_LIB_LEGSCOPY_V61' not in s: raise SystemExit('v61 must run first')

# Dua polesan otomatis per klip saat dipasang:
# 1. ARAH HADAP: orientasi hips frame-0 hasil retarget dibandingkan dengan
#    arah hadap rest model; seluruh klip diputar yaw sebesar selisihnya
#    sehingga karakter menghadap arah yang sama dengan sebelum animasi
#    (lurus ke kamera), bukan arah rekaman klip sumber.
# 2. INJAK LANTAI: klip disimulasikan senyap 21 fase, titik terendah
#    telapak/jari kaki diukur, lalu track posisi Hips digeser vertikal agar
#    titik terendah siklus tepat di lantai model.
funcs=r'''  // ANIM_LIB_GROUNDFACE_V62
  function groundFaceV62(nc,bones,R){
    try{
      const hips=bones.Hips;if(!hips)return;
      const posName=hips.name+'.position';
      const posTrack=nc.tracks.find(t=>t.name===posName);
      const mixer2=new THREE.AnimationMixer(root);
      const act=mixer2.clipAction(nc);act.reset();act.play();
      const v=new THREE.Vector3();
      const yawOf=q=>{const f=new THREE.Vector3(0,0,1).applyQuaternion(q);return Math.atan2(f.x,f.z)};
      // 1) arah hadap: RATA-RATA yaw hips satu siklus vs yaw rest model
      // (pelvis berayun yaw saat jalan/lari, jadi frame tunggal menyesatkan)
      let sx=0,sz=0;
      for(let i=0;i<8;i++){
        mixer2.setTime(nc.duration*i/8);root.updateMatrixWorld(true);
        const fq=new THREE.Vector3(0,0,1).applyQuaternion(hips.getWorldQuaternion(new THREE.Quaternion()));
        sx+=fq.x;sz+=fq.z;
      }
      const yaw0=Math.atan2(sx,sz);
      const yawRest=yawOf(R.restMap.get(hips).wq);
      let dy=yawRest-yaw0;
      while(dy>Math.PI)dy-=2*Math.PI;while(dy<-Math.PI)dy+=2*Math.PI;
      if(Math.abs(dy)>0.02){
        const Yq=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),dy);
        const tqp=(hips.parent&&hips.parent.isBone&&R.restMap.get(hips.parent))?R.restMap.get(hips.parent).wq:R.rootWQ;
        const pre=tqp.clone().invert().multiply(Yq).multiply(tqp);
        const quatTrack=nc.tracks.find(t=>t.name===hips.name+'.quaternion');
        if(quatTrack){
          const q2=new THREE.Quaternion();
          for(let i=0;i<quatTrack.values.length;i+=4){
            q2.fromArray(quatTrack.values,i);
            q2.premultiply(pre).normalize();
            q2.toArray(quatTrack.values,i);
          }
        }
        if(posTrack){
          const rp=R.restMap.get(hips).p;
          for(let i=0;i<posTrack.values.length;i+=3){
            v.set(posTrack.values[i]-rp.x,posTrack.values[i+1]-rp.y,posTrack.values[i+2]-rp.z);
            v.applyQuaternion(Yq);
            posTrack.values[i]=rp.x+v.x;posTrack.values[i+1]=rp.y+v.y;posTrack.values[i+2]=rp.z+v.z;
          }
        }
      }
      // 1b) tegakkan kemiringan samping (roll): rata-rata vektor atas hips
      // satu siklus dibandingkan rest, dikoreksi pada sumbu depan horizontal -
      // condong ke depan (pitch) khas lari TIDAK disentuh
      {
        const U=new THREE.Vector3(0,1,0);
        const fh=new THREE.Vector3(0,0,1).applyQuaternion(R.restMap.get(hips).wq);fh.y=0;
        if(fh.lengthSq()>1e-6){
          const F=fh.normalize();
          const S=new THREE.Vector3().crossVectors(U,F).normalize();
          const ur=new THREE.Vector3(0,1,0).applyQuaternion(R.restMap.get(hips).wq);
          for(let iterV62=0;iterV62<3;iterV62++){
          const mu=new THREE.Vector3();
          for(let i=0;i<8;i++){
            mixer2.setTime(nc.duration*(i+0.5)/8);root.updateMatrixWorld(true);
            mu.add(new THREE.Vector3(0,1,0).applyQuaternion(hips.getWorldQuaternion(new THREE.Quaternion())));
          }
          mu.normalize();
          const roll=Math.atan2(mu.dot(S),mu.dot(U))-Math.atan2(ur.dot(S),ur.dot(U));
          if(Math.abs(roll)<=0.017)break;
          if(Math.abs(roll)>0.01){
            const Rq=new THREE.Quaternion().setFromAxisAngle(F,roll);
            const tqp2=(hips.parent&&hips.parent.isBone&&R.restMap.get(hips.parent))?R.restMap.get(hips.parent).wq:R.rootWQ;
            const pre2=tqp2.clone().invert().multiply(Rq).multiply(tqp2);
            const quatTrack2=nc.tracks.find(t2=>t2.name===hips.name+'.quaternion');
            if(quatTrack2){
              const q3=new THREE.Quaternion();
              for(let i=0;i<quatTrack2.values.length;i+=4){
                q3.fromArray(quatTrack2.values,i);
                q3.premultiply(pre2).normalize();
                q3.toArray(quatTrack2.values,i);
              }
            }
            if(posTrack){
              const rp2=R.restMap.get(hips).p;const v2=new THREE.Vector3();
              for(let i=0;i<posTrack.values.length;i+=3){
                v2.set(posTrack.values[i]-rp2.x,posTrack.values[i+1]-rp2.y,posTrack.values[i+2]-rp2.z);
                v2.applyQuaternion(Rq);
                posTrack.values[i]=rp2.x+v2.x;posTrack.values[i+1]=rp2.y+v2.y;posTrack.values[i+2]=rp2.z+v2.z;
              }
            }
          }
          }
        }
      }
      // 2) injak lantai: geser Y hips agar kaki terendah siklus di lantai
      if(posTrack){
        let minY=Infinity;
        const feet=['LeftFoot','RightFoot','LeftToeBase','RightToeBase'].map(n=>bones[n]).filter(Boolean);
        for(let i=0;i<=40;i++){
          mixer2.setTime(nc.duration*i/40);root.updateMatrixWorld(true);
          for(const f of feet)minY=Math.min(minY,f.getWorldPosition(v).y);
        }
        if(feet.length&&isFinite(minY)){
          const drop=(minY-R.groundY)/Math.max(R.rootWS.y,1e-6);
          if(Math.abs(drop)>0.001){
            for(let i=1;i<posTrack.values.length;i+=3)posTrack.values[i]-=drop;
          }
        }
      }
      mixer2.stopAllAction();mixer2.uncacheRoot(root);
      // kembalikan bind pose; selectAnimation akan memutar klip final
      const skels=new Set();root.traverse(o=>{if(o.isSkinnedMesh&&o.skeleton)skels.add(o.skeleton)});
      for(const sk of skels)sk.pose();
      root.updateMatrixWorld(true);
    }catch(e){console.warn('ANIM_LIB_GROUNDFACE_V62',e)}
  }

'''
anchor='  function applyClip(lib,srcClip){'
if anchor not in s: raise SystemExit('applyClip anchor missing')
s=s.replace(anchor,funcs+anchor,1)

old_call='''    const nc=retargetClip(lib,srcClip,bones,R);
    if(!nc){say('Tidak ada tulang yang cocok untuk animasi ini');return false}'''
new_call='''    const nc=retargetClip(lib,srcClip,bones,R);
    if(!nc){say('Tidak ada tulang yang cocok untuk animasi ini');return false}
    groundFaceV62(nc,bones,R);'''
if old_call not in s: raise SystemExit('retargetClip call anchor missing')
s=s.replace(old_call,new_call,1)

p.write_text(s,encoding='utf-8')
print('Anim lib groundface v62: hadap kamera + injak lantai otomatis per klip')
