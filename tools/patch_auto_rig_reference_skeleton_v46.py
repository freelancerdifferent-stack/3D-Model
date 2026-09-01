from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html missing')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_REFERENCE_SKELETON_V46' in s:
    print('Auto Rig reference skeleton v46 already applied'); raise SystemExit(0)
if 'AUTO_RIG_CENTERLINE_FIX_V45' not in s: raise SystemExit('Auto Rig centerline v45 must run first')

start=s.find('  // AUTO_RIG_CENTERLINE_FIX_V45\n  function generateSkeleton(){')
end=s.find('\n\n  async function skinGeometry(){',start)
if start<0 or end<0: raise SystemExit('generateSkeleton v45 block missing')

new_block=r'''  // AUTO_RIG_REFERENCE_SKELETON_V46
  // Humanoid hierarchy is intentionally matched to the supplied run.glb reference:
  // Hips -> (LeftUpLeg, RightUpLeg, Spine02)
  // Spine02 -> Spine01 -> Spine -> (LeftShoulder, RightShoulder, neck)
  // neck -> Head -> (head_end, headfront)
  // shoulders -> arm -> forearm -> hand; legs -> leg -> foot -> toe.
  function generateSkeleton(){
    if(S.helper){scene.remove(S.helper);S.helper=null}S.bones=[];
    const m=S.markers,b=S.box,h=S.size.y;
    const groinW=m.groin.clone(),chinW=m.chin.clone();
    const torso=chinW.clone().sub(groinW), torsoLen=Math.max(torso.length(),h*.05);
    const torsoDir=torso.clone().normalize();
    const centerAt=t=>groinW.clone().lerp(chinW,t);

    // Three spine joints distribute the user-defined Groin -> Chin axis. The final
    // Spine joint is the common branch point for shoulders and neck, as in run.glb.
    const spine02W=centerAt(.24), spine01W=centerAt(.45), spineW=centerAt(.66);
    const neckW=centerAt(.84);
    // Chin is a landmark, not a structural joint in the reference. Use it to solve
    // Head position while keeping the hierarchy compatible with the reference rig.
    const headW=chinW.clone().addScaledVector(torsoDir,torsoLen*.11);
    const headEndW=headW.clone().addScaledVector(torsoDir,torsoLen*.18);
    // headfront is a short forward helper/end joint. Forward is local +Z in the
    // normalized Auto Rig workspace; its exact animation role can be refined later.
    const headFrontW=headW.clone().add(new THREE.Vector3(0,torsoLen*.03,torsoLen*.10));

    const hipLW=new THREE.Vector3(m.kneeL.x,groinW.y,groinW.z);
    const hipRW=new THREE.Vector3(m.kneeR.x,groinW.y,groinW.z);
    const toeLW=new THREE.Vector3(m.ankleL.x,b.min.y+h*.015,m.ankleL.z+h*.035);
    const toeRW=new THREE.Vector3(m.ankleR.x,b.min.y+h*.015,m.ankleR.z+h*.035);

    const specs={};
    const add=(key,name,pos,parentSpec)=>{
      const x=makeBone(name,pos,parentSpec?.bone||null,parentSpec?.local||null);
      specs[key]=x;S.bones.push(x.bone);return x;
    };

    specs.hips=makeBone('Hips',groinW,null,null);root.add(specs.hips.bone);S.bones.push(specs.hips.bone);

    // Legs branch directly from Hips.
    const lUp=add('leftUpLeg','LeftUpLeg',hipLW,specs.hips);
    const lLeg=add('leftLeg','LeftLeg',m.kneeL,lUp);
    const lFoot=add('leftFoot','LeftFoot',m.ankleL,lLeg);
    add('leftToe','LeftToeBase',toeLW,lFoot);
    const rUp=add('rightUpLeg','RightUpLeg',hipRW,specs.hips);
    const rLeg=add('rightLeg','RightLeg',m.kneeR,rUp);
    const rFoot=add('rightFoot','RightFoot',m.ankleR,rLeg);
    add('rightToe','RightToeBase',toeRW,rFoot);

    // Reference torso hierarchy and branch point.
    const sp02=add('spine02','Spine02',spine02W,specs.hips);
    const sp01=add('spine01','Spine01',spine01W,sp02);
    const sp=add('spine','Spine',spineW,sp01);

    for(const side of ['L','R']){
      const prefix=side==='L'?'Left':'Right';
      const sh=add(prefix+'Shoulder',prefix+'Shoulder',m['shoulder'+side],sp);
      // In the reference, the Shoulder joint is followed by Arm at the upper-arm
      // start. Estimate that point between shoulder and elbow; Elbow itself becomes
      // the ForeArm joint and Wrist becomes Hand.
      const armStart=m['shoulder'+side].clone().lerp(m['elbow'+side],.18);
      const arm=add(prefix+'Arm',prefix+'Arm',armStart,sh);
      const fore=add(prefix+'ForeArm',prefix+'ForeArm',m['elbow'+side],arm);
      add(prefix+'Hand',prefix+'Hand',m['wrist'+side],fore);
    }

    const neck=add('neck','neck',neckW,sp);
    const head=add('head','Head',headW,neck);
    add('headEnd','head_end',headEndW,head);
    add('headFront','headfront',headFrontW,head);

    root.updateMatrixWorld(true);
    S.skeleton=new THREE.Skeleton(S.bones);S.skeleton.calculateInverses();
    S.helper=new THREE.SkeletonHelper(root);S.helper.material.depthTest=false;S.helper.material.transparent=true;S.helper.material.opacity=.95;scene.add(S.helper);
    return specs;
  }'''

s=s[:start]+new_block+s[end:]
p.write_text(s,encoding='utf-8')
print('Auto Rig reference skeleton v46 applied: 24-joint hierarchy matched to run.glb')
