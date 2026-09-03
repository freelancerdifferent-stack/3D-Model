from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist')
s=p.read_text(encoding='utf-8')
if 'ANIM_LIB_LEGSCOPY_V61' in s:
    print('Anim lib legscopy v61 already applied'); raise SystemExit(0)
if 'ANIM_LIB_RESTOFFSET_V60' not in s: raise SystemExit('v60 must run first')

# Gerakan kaki tidak natural: pelebar konstan v60 memiringkan bidang ayunan
# kaki keluar (jalan "di atas rel"). v61: rantai KAKI menyalin orientasi
# library apa adanya - gait alami sumber dipertahankan penuh - dan pelebar
# hanya mengompensasi selisih lebar pinggul target vs sumber (sudut kecil),
# bukan seluruh bukaan langkah. Lengan/torso tetap delta di atas rest target.
old_ang='''        const desired=wT+(sepR-wR)*(legT/legR);
        const ang=Math.asin(Math.max(-0.5,Math.min(0.5,((desired-sepT)/2)/Math.max(legT,1e-4))));'''
new_ang='''        // ANIM_LIB_LEGSCOPY_V61: kompensasi selisih lebar pinggul saja
        const dW=Math.max(0,wR*(legT/legR)-wT);
        const ang=Math.asin(Math.min(0.5,(dW/2)/Math.max(legT,1e-4)));'''
if old_ang not in s: raise SystemExit('spread angle anchor missing')
s=s.replace(old_ang,new_ang,1)

old_post='''          const postV60=rn.quaternion.clone().invert().multiply(R.restMap.get(tb).lq);
          const preV60=(nodeName==='LeftUpLeg')?spreadV60.L:((nodeName==='RightUpLeg')?spreadV60.R:null);
          const vals=new Float32Array(tr.values.length);
          for(let i=0;i<tr.values.length;i+=4){
            q.fromArray(tr.values,i);
            q.multiply(postV60);
            if(preV60)q.premultiply(preV60);
            q.normalize();
            q.toArray(vals,i);
          }'''
new_post='''          const legV61=/^(Left|Right)(UpLeg|Leg|Foot|ToeBase)$/.test(nodeName);
          const postV60=legV61?null:rn.quaternion.clone().invert().multiply(R.restMap.get(tb).lq);
          const preV60=(nodeName==='LeftUpLeg')?spreadV60.L:((nodeName==='RightUpLeg')?spreadV60.R:null);
          const vals=new Float32Array(tr.values.length);
          for(let i=0;i<tr.values.length;i+=4){
            q.fromArray(tr.values,i);
            if(postV60)q.multiply(postV60);
            if(preV60)q.premultiply(preV60);
            q.normalize();
            q.toArray(vals,i);
          }'''
if old_post not in s: raise SystemExit('family loop anchor missing')
s=s.replace(old_post,new_post,1)

p.write_text(s,encoding='utf-8')
print('Anim lib legscopy v61: kaki menyalin gait sumber + kompensasi lebar pinggul')
