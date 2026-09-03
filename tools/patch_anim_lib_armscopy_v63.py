from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist')
s=p.read_text(encoding='utf-8')
if 'ANIM_LIB_ARMSCOPY_V63' in s:
    print('Anim lib armscopy v63 already applied'); raise SystemExit(0)
if 'ANIM_LIB_LEGSCOPY_V61' not in s: raise SystemExit('v61 must run first')

# Screening 67 klip vs FBX bawaan: badan/kaki cocok 3-6 derajat, lengan
# melenceng 20-31 derajat. Perbaikan v63:
# 1. Lengan ikut jalur copy (delta-rest v60 membawa selisih pose istirahat).
# 2. Pemetaan peran tidak boleh memilih tulang duplikat sisa merge v55.
# 3. Hierarki referensi library: Hips->Spine02->Spine01->Spine(dada)->
#    bahu/leher - urutan smartmap v56 (Spine02=terbawah, Spine=terdalam)
#    sudah benar dan dipertahankan.
# 4. mappedSet v59 hanya berisi target nama referensi; tulang perantara tak
#    teranimasi (spine_02/04, neck_02 pada rig 5-spine) dijembatani
#    kompensasi konstan inv(E), E = perkalian rest lokal perantara.
# 5. Koreksi aim konstan per tulang rantai: orientasi copy diputar agar arah
#    ke anak tulang target sama dengan arah referensi (selisih geometri
#    rangka, mis. siku NYX), anak menerima kompensasi balik inv(C_parent).

old_bad='''    const bad=/twist|roll|helper|(^|[^a-z])ik|pole|target|nub|end$|tip$|top$|front|thumb|index|middle|ring|pinky|finger|eye|jaw|tongue|(^|[^a-z])ear|breast|weapon|prop|attach/;'''
new_bad='''    const bad=/twist|roll|helper|(^|[^a-z])ik|pole|target|nub|end$|tip$|top$|front|thumb|index|middle|ring|pinky|finger|eye|jaw|tongue|(^|[^a-z])ear|breast|weapon|prop|attach|dupv55/;'''
if old_bad not in s: raise SystemExit('bad regex anchor missing')
s=s.replace(old_bad,new_bad,1)

old_set='''    const mappedSetV59=new Set(Object.values(bones));'''
new_set='''    const mappedSetV59=new Set();
    for(const nmM in refNodes){if(bones[nmM])mappedSetV59.add(bones[nmM])}'''
if old_set not in s: raise SystemExit('mappedSet anchor missing')
s=s.replace(old_set,new_set,1)

old_cmap='''    }catch(_){ }
    for(const tr of clip.tracks){'''
new_cmap='''    }catch(_){ }
    /* koreksi aim: selaraskan arah tulang->anak dengan referensi */
    const cmapV63={};
    if(familyV59){
      const CCV63={Spine02:'Spine01',Spine01:'Spine',neck:'Head',
        LeftShoulder:'LeftArm',LeftArm:'LeftForeArm',LeftForeArm:'LeftHand',
        RightShoulder:'RightArm',RightArm:'RightForeArm',RightForeArm:'RightHand',
        LeftUpLeg:'LeftLeg',LeftLeg:'LeftFoot',LeftFoot:'LeftToeBase',
        RightUpLeg:'RightLeg',RightLeg:'RightFoot',RightFoot:'RightToeBase'};
      for(const nmC in CCV63){
        const rnB=refNodes[nmC],rnC=refNodes[CCV63[nmC]];
        const tbB=bones[nmC],tbC=bones[CCV63[nmC]];
        if(!rnB||!rnC||!tbB||!tbC)continue;
        const rmB=R.restMap.get(tbB),rmC=R.restMap.get(tbC);
        if(!rmB||!rmC)continue;
        const dT=rmC.wp.clone().sub(rmB.wp);
        if(dT.lengthSq()<1e-8)continue;
        dT.applyQuaternion(rmB.wq.clone().invert()).normalize();
        const dRf=rnC.getWorldPosition(new THREE.Vector3()).sub(rnB.getWorldPosition(new THREE.Vector3()));
        if(dRf.lengthSq()<1e-8)continue;
        dRf.applyQuaternion(rnB.getWorldQuaternion(new THREE.Quaternion()).invert()).normalize();
        cmapV63[nmC]=new THREE.Quaternion().setFromUnitVectors(dT,dRf);
      }
    }
    for(const tr of clip.tracks){'''
if old_cmap not in s: raise SystemExit('cmap anchor missing')
s=s.replace(old_cmap,new_cmap,1)

old_chain='''        const chainOkV59=tb.parent&&tb.parent.isBone&&mappedSetV59.has(tb.parent);
        if(familyV59&&chainOkV59){'''
new_chain='''        let chainOkV59=tb.parent&&tb.parent.isBone&&mappedSetV59.has(tb.parent);
        let gapEV63=null;
        if(familyV59&&!chainOkV59&&tb.parent&&tb.parent.isBone){
          const eq=new THREE.Quaternion();const chain=[];let anc=tb.parent;
          while(anc&&anc.isBone&&!mappedSetV59.has(anc)){chain.unshift(anc);anc=anc.parent}
          const refPar=rn.parent&&bones[rn.parent.name];
          if(anc&&anc.isBone&&refPar===anc&&chain.length){
            let full=true;
            for(const c of chain){const rm=R.restMap.get(c);if(rm)eq.multiply(rm.lq);else full=false}
            if(full){gapEV63=eq.invert();chainOkV59=true;}
          }
        }
        if(familyV59&&chainOkV59){'''
if old_chain not in s: raise SystemExit('chainOk anchor missing')
s=s.replace(old_chain,new_chain,1)

old_block='''          const legV61=/^((Left|Right)(UpLeg|Leg|Foot|ToeBase)|Spine02|Spine01|Spine|neck|Head)$/.test(nodeName);
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
new_block='''          const legV61=/^((Left|Right)(UpLeg|Leg|Foot|ToeBase|Shoulder|Arm|ForeArm|Hand)|Spine02|Spine01|Spine|neck|Head)$/.test(nodeName);
          const postV60=legV61?null:rn.quaternion.clone().invert().multiply(R.restMap.get(tb).lq);
          const preV60=(nodeName==='LeftUpLeg')?spreadV60.L:((nodeName==='RightUpLeg')?spreadV60.R:null);
          const cSelfV63=(legV61&&cmapV63[nodeName])?cmapV63[nodeName]:null;
          const cParV63=(legV61&&rn.parent&&cmapV63[rn.parent.name])?cmapV63[rn.parent.name].clone().invert():null;
          const vals=new Float32Array(tr.values.length);
          for(let i=0;i<tr.values.length;i+=4){
            q.fromArray(tr.values,i);
            if(postV60)q.multiply(postV60);
            if(cSelfV63)q.multiply(cSelfV63);
            if(cParV63)q.premultiply(cParV63);
            if(gapEV63)q.premultiply(gapEV63);
            if(preV60)q.premultiply(preV60);
            q.normalize();
            q.toArray(vals,i);
          }'''
if old_block not in s: raise SystemExit('family block anchor missing')
s=s.replace(old_block,new_block,1)

p.write_text(s,encoding='utf-8')
print('Anim lib armscopy v63: copy + peta dada + jembatan perantara + koreksi aim')
