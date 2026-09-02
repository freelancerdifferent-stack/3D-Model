from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html missing')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_CENTERLINE_FIX_V45' in s:
    print('Auto Rig centerline fix v45 already applied'); raise SystemExit(0)
if 'AUTO_RIG_HEIGHT_FIX_V44' not in s: raise SystemExit('Auto Rig height fix v44 must run first')

start=s.find('  function generateSkeleton(){')
end=s.find('\n\n  async function skinGeometry(){',start)
if start<0 or end<0: raise SystemExit('generateSkeleton block missing')

new_block=r'''  // AUTO_RIG_CENTERLINE_FIX_V45
  function generateSkeleton(){
    if(S.helper){scene.remove(S.helper);S.helper=null}S.bones=[];
    const m=S.markers,b=S.box,h=S.size.y,c=S.center;

    // The torso is now derived from the two user landmarks that define the body's
    // centre line: Groin -> Chin. V42 ignored the Chin marker and rebuilt Spine/Chest/
    // Neck from bounding-box percentages, which could create a crooked/disconnected
    // visual chain. Every centre bone below lies on this exact landmark axis.
    const groinW=m.groin.clone();
    const chinW=m.chin.clone();
    const axis=chinW.clone().sub(groinW);
    const axisLen=Math.max(axis.length(),h*.05);
    const axisDir=axis.clone().normalize();
    const centerAt=t=>groinW.clone().lerp(chinW,t);
    const spineW=centerAt(.32);
    const chestW=centerAt(.58);
    const neckW=centerAt(.84);
    const headW=chinW.clone().addScaledVector(axisDir,axisLen*.18);

    // Leg roots retain the user's left/right knee alignment while sharing the exact
    // groin Y/Z plane, so both legs branch cleanly from Hips.
    const hipLW=new THREE.Vector3(m.kneeL.x,groinW.y,groinW.z);
    const hipRW=new THREE.Vector3(m.kneeR.x,groinW.y,groinW.z);
    const footLW=new THREE.Vector3(m.ankleL.x,b.min.y+h*.015,m.ankleL.z+h*.025);
    const footRW=new THREE.Vector3(m.ankleR.x,b.min.y+h*.015,m.ankleR.z+h*.025);

    const specs={};
    specs.hips=makeBone('Hips',groinW,null,null);root.add(specs.hips.bone);S.bones.push(specs.hips.bone);
    specs.spine=makeBone('Spine',spineW,specs.hips.bone,specs.hips.local);S.bones.push(specs.spine.bone);
    specs.chest=makeBone('Chest',chestW,specs.spine.bone,specs.spine.local);S.bones.push(specs.chest.bone);
    specs.neck=makeBone('Neck',neckW,specs.chest.bone,specs.chest.local);S.bones.push(specs.neck.bone);
    // Keep a real bone exactly on the Chin marker so the helper line visibly reaches
    // the landmark selected by the user instead of stopping at an estimated neck.
    specs.chin=makeBone('Chin',chinW,specs.neck.bone,specs.neck.local);S.bones.push(specs.chin.bone);
    specs.head=makeBone('Head',headW,specs.chin.bone,specs.chin.local);S.bones.push(specs.head.bone);

    for(const side of ['L','R']){
      const sh=makeBone('Shoulder_'+side,m['shoulder'+side],specs.chest.bone,specs.chest.local);S.bones.push(sh.bone);
      const ua=makeBone('UpperArm_'+side,m['elbow'+side],sh.bone,sh.local);S.bones.push(ua.bone);
      const la=makeBone('LowerArm_'+side,m['wrist'+side],ua.bone,ua.local);S.bones.push(la.bone);
      const handPos=m['wrist'+side].clone();handPos.x+=(side==='L'?-1:1)*S.size.x*.07;
      const hand=makeBone('Hand_'+side,handPos,la.bone,la.local);S.bones.push(hand.bone);
      const hip=makeBone('UpperLeg_'+side,side==='L'?hipLW:hipRW,specs.hips.bone,specs.hips.local);S.bones.push(hip.bone);
      const knee=makeBone('LowerLeg_'+side,m['knee'+side],hip.bone,hip.local);S.bones.push(knee.bone);
      const ankle=makeBone('Foot_'+side,m['ankle'+side],knee.bone,knee.local);S.bones.push(ankle.bone);
      const toe=makeBone('Toe_'+side,side==='L'?footLW:footRW,ankle.bone,ankle.local);S.bones.push(toe.bone);
    }
    root.updateMatrixWorld(true);
    S.skeleton=new THREE.Skeleton(S.bones);S.skeleton.calculateInverses();
    S.helper=new THREE.SkeletonHelper(root);S.helper.material.depthTest=false;S.helper.material.transparent=true;S.helper.material.opacity=.95;scene.add(S.helper);
    return specs;
  }'''

s=s[:start]+new_block+s[end:]
p.write_text(s,encoding='utf-8')
print('Auto Rig centerline fix v45 applied: Groin -> Spine -> Chest -> Neck -> Chin -> Head is one landmark-driven line')
