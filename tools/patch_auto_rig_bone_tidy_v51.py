from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_BONE_TIDY_V51' in s:
    print('Auto Rig bone tidy v51 already applied'); raise SystemExit(0)
if 'AUTO_RIG_REPLACE_OLD_V50' not in s: raise SystemExit('v50 must run first')

# Penempatan sendi dirapikan mengikuti proporsi terukur dari rig referensi
# SK_NYX_nude_biped (biped 24 tulang yang sudah lulus tes). Struktur, nama dan
# hierarki tulang TIDAK berubah - hanya posisinya:
#   - garis tengah dihitung dari rata-rata marker kiri/kanan, seluruh rantai
#     Hips-Spine02-Spine01-Spine-neck-Head duduk lurus di garis itu
#   - fraksi torso terukur: Spine02 .345, Spine01 .545, Spine .745, neck .855,
#     Head tepat di ketinggian dagu (di referensi sendi Head = ketinggian dagu)
#   - Hips sedikit di atas pangkal paha (10% panjang kaki), pangkal paha
#     selebar 9% panjang kaki dari tengah - bukan selebar lutut
#   - klavikula (Shoulder) hanya 23% dari tengah dada ke marker bahu; Arm tepat
#     di marker bahu (di v46 keduanya salah tempat sehingga dada tampak V lebar)
#   - jari kaki maju 10% panjang kaki dari pergelangan
old_a='''    const groinW=m.groin.clone(),chinW=m.chin.clone();
    const torso=chinW.clone().sub(groinW), torsoLen=Math.max(torso.length(),h*.05);
    const torsoDir=torso.clone().normalize();
    const centerAt=t=>groinW.clone().lerp(chinW,t);
'''
new_a='''    // AUTO_RIG_BONE_TIDY_V51: proporsi sendi mengikuti rig referensi biped
    const cx=(m.shoulderL.x+m.shoulderR.x+m.kneeL.x+m.kneeR.x+m.ankleL.x+m.ankleR.x+m.chin.x+m.groin.x)/8;
    const groinW=new THREE.Vector3(cx,m.groin.y,m.groin.z),chinW=new THREE.Vector3(cx,m.chin.y,m.chin.z);
    const torso=chinW.clone().sub(groinW), torsoLen=Math.max(torso.length(),h*.05);
    const torsoDir=torso.clone().normalize();
    const centerAt=t=>groinW.clone().lerp(chinW,t);
    const ankleYV51=(m.ankleL.y+m.ankleR.y)/2;
    const legLenV51=Math.max(groinW.y-ankleYV51,h*.2);
    const hipsW=centerAt(0).add(new THREE.Vector3(0,legLenV51*.10,0));
'''
if old_a not in s: raise SystemExit('torso axis anchor missing')
s=s.replace(old_a,new_a,1)

old_b='''    const spine02W=centerAt(.24), spine01W=centerAt(.45), spineW=centerAt(.66);
    const neckW=centerAt(.84);'''
new_b='''    const spine02W=centerAt(.345), spine01W=centerAt(.545), spineW=centerAt(.745);
    const neckW=centerAt(.855);'''
if old_b not in s: raise SystemExit('spine fractions anchor missing')
s=s.replace(old_b,new_b,1)

old_c='''    const headW=chinW.clone().addScaledVector(torsoDir,torsoLen*.11);
    const headEndW=headW.clone().addScaledVector(torsoDir,torsoLen*.18);'''
new_c='''    const headW=chinW.clone();
    const headEndW=headW.clone().addScaledVector(torsoDir,torsoLen*.36);'''
if old_c not in s: raise SystemExit('head anchor missing')
s=s.replace(old_c,new_c,1)

old_d='''    const headFrontW=headW.clone().add(new THREE.Vector3(0,torsoLen*.03,torsoLen*.10));'''
new_d='''    const headFrontW=headW.clone().add(new THREE.Vector3(0,0,torsoLen*.18));'''
if old_d not in s: raise SystemExit('headfront anchor missing')
s=s.replace(old_d,new_d,1)

old_e='''    const hipLW=new THREE.Vector3(m.kneeL.x,groinW.y,groinW.z);
    const hipRW=new THREE.Vector3(m.kneeR.x,groinW.y,groinW.z);
    const toeLW=new THREE.Vector3(m.ankleL.x,b.min.y+h*.015,m.ankleL.z+h*.035);
    const toeRW=new THREE.Vector3(m.ankleR.x,b.min.y+h*.015,m.ankleR.z+h*.035);'''
new_e='''    const hipHalfV51=legLenV51*.09;
    const sideLV51=Math.sign(m.kneeL.x-cx)||1, sideRV51=Math.sign(m.kneeR.x-cx)||-1;
    const hipLW=new THREE.Vector3(cx+sideLV51*hipHalfV51,groinW.y,m.kneeL.z);
    const hipRW=new THREE.Vector3(cx+sideRV51*hipHalfV51,groinW.y,m.kneeR.z);
    const toeLW=new THREE.Vector3(m.ankleL.x,b.min.y+h*.015,m.ankleL.z+legLenV51*.10);
    const toeRW=new THREE.Vector3(m.ankleR.x,b.min.y+h*.015,m.ankleR.z+legLenV51*.10);'''
if old_e not in s: raise SystemExit('hip/toe anchor missing')
s=s.replace(old_e,new_e,1)

old_f="""    specs.hips=makeBone('Hips',groinW,null,null);"""
new_f="""    specs.hips=makeBone('Hips',hipsW,null,null);"""
if old_f not in s: raise SystemExit('hips anchor missing')
s=s.replace(old_f,new_f,1)

old_g='''      const sh=add(prefix+'Shoulder',prefix+'Shoulder',m['shoulder'+side],sp);
      // In the reference, the Shoulder joint is followed by Arm at the upper-arm
      // start. Estimate that point between shoulder and elbow; Elbow itself becomes
      // the ForeArm joint and Wrist becomes Hand.
      const armStart=m['shoulder'+side].clone().lerp(m['elbow'+side],.18);
      const arm=add(prefix+'Arm',prefix+'Arm',armStart,sh);'''
new_g='''      // Klavikula dekat tengah dada seperti di rig referensi; Arm tepat di
      // marker bahu, ForeArm di siku, Hand di pergelangan.
      const shW=centerAt(.82).lerp(m['shoulder'+side],.23);
      const sh=add(prefix+'Shoulder',prefix+'Shoulder',shW,sp);
      const arm=add(prefix+'Arm',prefix+'Arm',m['shoulder'+side].clone(),sh);'''
if old_g not in s: raise SystemExit('shoulder anchor missing')
s=s.replace(old_g,new_g,1)

p.write_text(s,encoding='utf-8')
print('Auto Rig bone tidy v51: penempatan sendi mengikuti proporsi rig referensi biped')
