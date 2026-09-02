from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_ALIGN_V54' in s:
    print('Auto Rig align v54 already applied'); raise SystemExit(0)
if 'AUTO_RIG_WEIGHTS_V53' not in s: raise SystemExit('v53 must run first')

# Konsep baru untuk model yang SUDAH ber-rig: rig lama tidak dihapus.
# Tulang inti (hips, rantai spine, leher, kepala, klavikula-lengan-tangan,
# paha-betis-kaki-jari kaki) dipetakan lewat pola nama + analisis hierarki
# (mendukung mixamorig:Hips, Bip01_Pelvis, pelvis, dst.), lalu DISEJAJARKAN
# ke posisi marker memakai rumus proporsi v51. Tulang non-inti (jari tangan,
# twist, wajah) tetap menempel dan ikut induknya. Setelah digeser, boneInverses
# dihitung ulang sehingga pose sekarang menjadi bind pose baru - mesh tidak
# bergeser dan SKIN WEIGHTS ASLI TETAP DIPAKAI. Jalur hapus+ganti (v50)
# menjadi cadangan bila pemetaan gagal mengenali rig.
funcs=r'''  // AUTO_RIG_ALIGN_V54
  function mapCoreBonesV54(){
    if(!root)return {ok:false};
    const all=[];root.traverse(o=>{if(o.isBone)all.push(o)});
    if(!all.length)return {ok:false};
    root.updateMatrixWorld(true);
    const depth=b=>{let d=0,n=b;while(n.parent&&n.parent.isBone){d++;n=n.parent}return d};
    const norm=n=>String(n||'').toLowerCase().replace(/^.*[:]/,'').replace(/[\s_\-\.]/g,'');
    const bad=/twist|roll|helper|(^|[^a-z])ik|pole|target|nub|end$|tip$|top$|front|thumb|index|middle|ring|pinky|finger|eye|jaw|tongue|(^|[^a-z])ear|breast|weapon|prop|attach/;
    const sideTok=b=>{const t=String(b.name).toLowerCase();
      if(t.includes('left'))return 1; if(t.includes('right'))return -1;
      if(/(^|[^a-z0-9])l([^a-z0-9]|$)/.test(t)||/[\._-]l$|^l[\._-]/.test(t))return 1;
      if(/(^|[^a-z0-9])r([^a-z0-9]|$)/.test(t)||/[\._-]r$|^r[\._-]/.test(t))return -1;
      return 0};
    const roleOf=n=>{
      if(bad.test(n))return null;
      if(/hip|pelvis/.test(n))return 'hips';
      if(/spine|chest|torso/.test(n))return 'spine';
      if(/neck/.test(n))return 'neck';
      if(/head/.test(n))return 'head';
      if(/clavicle|collar|shoulder/.test(n))return 'clav';
      if(/forearm|lowerarm|elbow|ulna/.test(n))return 'forearm';
      if(/upperarm|uparm|arm/.test(n))return 'upperarm';
      if(/hand|wrist|carpal/.test(n))return 'hand';
      if(/upleg|upperleg|thigh|femur/.test(n))return 'thigh';
      if(/foot|ankle|tarsal/.test(n))return 'foot';
      if(/toe|ball/.test(n))return 'toe';
      if(/leg|calf|shin|knee|tibia/.test(n))return 'calf';
      return null};
    const hipsCand=all.find(x=>/hip|pelvis/.test(norm(x.name)));
    const hipsX=hipsCand?hipsCand.getWorldPosition(new THREE.Vector3()).x:0;
    const groups={spine:[],neck:[]};const single={};
    const sided={clav:{},upperarm:{},forearm:{},hand:{},thigh:{},calf:{},foot:{},toe:{}};
    for(const bn of all){
      const r=roleOf(norm(bn.name));if(!r)continue;
      if(r==='spine'||r==='neck'){groups[r].push(bn);continue}
      if(r==='hips'||r==='head'){
        if(!single[r]||depth(bn)<depth(single[r]))single[r]=bn;continue}
      let sd=sideTok(bn);
      if(sd===0){sd=bn.getWorldPosition(new THREE.Vector3()).x>=hipsX?1:-1}
      const key=sd>0?'L':'R';
      if(!sided[r][key]||depth(bn)<depth(sided[r][key]))sided[r][key]=bn;
    }
    groups.spine.sort((a,c)=>depth(a)-depth(c));groups.neck.sort((a,c)=>depth(a)-depth(c));
    const need=['upperarm','forearm','hand','thigh','calf','foot'];
    const ok=!!single.hips&&need.every(r=>sided[r].L&&sided[r].R);
    return {ok,all,hips:single.hips,head:single.head,spine:groups.spine,neck:groups.neck,sided,depth};
  }

  function alignExistingRigV54(map){
    const m=S.markers,b=S.box,h=S.size.y;
    root.updateMatrixWorld(true);
    // rumus target identik dengan generateSkeleton v51
    const cx=(m.shoulderL.x+m.shoulderR.x+m.kneeL.x+m.kneeR.x+m.ankleL.x+m.ankleR.x+m.chin.x+m.groin.x)/8;
    const groinW=new THREE.Vector3(cx,m.groin.y,m.groin.z),chinW=new THREE.Vector3(cx,m.chin.y,m.chin.z);
    const centerAt=t=>groinW.clone().lerp(chinW,t);
    const ankleY=(m.ankleL.y+m.ankleR.y)/2;
    const legLen=Math.max(groinW.y-ankleY,h*.2);
    const hipsW=centerAt(0).add(new THREE.Vector3(0,legLen*.10,0));
    const hipHalf=legLen*.09;
    const sL=Math.sign(m.kneeL.x-cx)||1,sR=Math.sign(m.kneeR.x-cx)||-1;
    const sideT={
      L:{clav:centerAt(.82).lerp(m.shoulderL,.23),upperarm:m.shoulderL.clone(),forearm:m.elbowL.clone(),hand:m.wristL.clone(),
         thigh:new THREE.Vector3(cx+sL*hipHalf,groinW.y,m.kneeL.z),calf:m.kneeL.clone(),foot:m.ankleL.clone(),
         toe:new THREE.Vector3(m.ankleL.x,b.min.y+h*.015,m.ankleL.z+legLen*.10)},
      R:{clav:centerAt(.82).lerp(m.shoulderR,.23),upperarm:m.shoulderR.clone(),forearm:m.elbowR.clone(),hand:m.wristR.clone(),
         thigh:new THREE.Vector3(cx+sR*hipHalf,groinW.y,m.kneeR.z),calf:m.kneeR.clone(),foot:m.ankleR.clone(),
         toe:new THREE.Vector3(m.ankleR.x,b.min.y+h*.015,m.ankleR.z+legLen*.10)}};
    // cocokkan sisi dengan posisi fisik (model bisa menghadap membelakangi kamera)
    let flip=false;
    const tl=map.sided.thigh.L,tr=map.sided.thigh.R;
    if(tl&&tr){
      const xl=tl.getWorldPosition(new THREE.Vector3()).x,xr=tr.getWorldPosition(new THREE.Vector3()).x;
      if((xl>=xr)!==(sideT.L.thigh.x>=sideT.R.thigh.x))flip=true;
    }
    const jobs=[];
    if(map.hips)jobs.push([map.hips,hipsW]);
    const ns=map.spine.length;
    map.spine.forEach((sb,i)=>{const t=ns===1?.55:(.345+(.745-.345)*(i/(ns-1)));jobs.push([sb,centerAt(t)])});
    const nn=map.neck.length;
    map.neck.forEach((nb,i)=>{const t=nn===1?.855:(.8+(.91-.8)*(i/(nn-1)));jobs.push([nb,centerAt(t)])});
    if(map.head)jobs.push([map.head,chinW.clone()]);
    for(const key of ['L','R']){
      const src=flip?(key==='L'?'R':'L'):key;
      for(const role of ['clav','upperarm','forearm','hand','thigh','calf','foot','toe']){
        const bn=map.sided[role]&&map.sided[role][key];if(!bn)continue;
        jobs.push([bn,sideT[src][role]]);
      }
    }
    jobs.sort((a,c)=>map.depth(a[0])-map.depth(c[0]));
    if(typeof mixer!=='undefined'&&mixer){try{mixer.stopAllAction()}catch(_){ }playing=false;mixer.timeScale=0;
      const pbA=document.getElementById('playBtn');if(pbA)pbA.textContent='▶'}
    const lp=new THREE.Vector3();
    for(const [bn,tw] of jobs){
      if(!bn.parent)continue;
      bn.parent.updateMatrixWorld(true);
      lp.copy(tw);bn.parent.worldToLocal(lp);
      bn.position.copy(lp);bn.updateMatrixWorld(true);
    }
    root.updateMatrixWorld(true);
    // pose sekarang menjadi bind pose baru: mesh diam, weights asli tetap dipakai
    let skinned=0;const skels=new Set();
    root.traverse(o=>{if(o.isSkinnedMesh&&o.skeleton){skels.add(o.skeleton);skinned++}});
    for(const sk of skels)sk.calculateInverses();
    if(S.helper){scene.remove(S.helper);S.helper=null}
    S.bones=map.all.slice();
    S.skeleton=null;
    S.skinned=skinned;
    S.alignedV54=true;
    S.helper=new THREE.SkeletonHelper(root);S.helper.material.depthTest=false;S.helper.material.transparent=true;S.helper.material.opacity=.95;scene.add(S.helper);
    window.__autoRigAlignV54={bones:map.all.length,aligned:jobs.length,skinned,flip};
    return jobs.length;
  }

'''
old_open='''    if(!root){notify('Import model terlebih dahulu sebelum Auto Rig.');return}
    S.box=modelBox();'''
new_open='''    if(!root){notify('Import model terlebih dahulu sebelum Auto Rig.');return}
    // AUTO_RIG_ALIGN_V54: kembalikan pose ke bind pose sebelum box dan marker
    // dihitung - frame animasi yang sedang tampil bukan acuan penyejajaran.
    try{
      if(typeof mixer!=='undefined'&&mixer){mixer.stopAllAction();mixer.timeScale=0;playing=false;
        const pbO=document.getElementById('playBtn');if(pbO)pbO.textContent='▶'}
      const skelsO=new Set();root.traverse(o=>{if(o.isSkinnedMesh&&o.skeleton)skelsO.add(o.skeleton)});
      for(const skO of skelsO)skO.pose();
      root.updateMatrixWorld(true);
    }catch(eO){console.warn('AUTO_RIG_ALIGN_V54 pose reset',eO)}
    S.box=modelBox();'''
if old_open not in s: raise SystemExit('openRig anchor missing')
s=s.replace(old_open,new_open,1)

anchor='  async function renderProcessingStep(){'
if anchor not in s: raise SystemExit('renderProcessingStep anchor missing')
s=s.replace(anchor,funcs+anchor,1)

old_run='try{set(12);await new Promise(r=>setTimeout(r,80));stripOldRigV50();set(24);generateSkeleton();set(38);await new Promise(r=>setTimeout(r,80));await skinGeometry();set(84);'
new_run='try{set(12);await new Promise(r=>setTimeout(r,80));S.alignedV54=false;const mapV54=hasOldRigV50()?mapCoreBonesV54():null;if(mapV54&&mapV54.ok){set(30);alignExistingRigV54(mapV54);set(70);await new Promise(r=>setTimeout(r,80))}else{stripOldRigV50();set(24);generateSkeleton();set(38);await new Promise(r=>setTimeout(r,80));await skinGeometry()}set(84);'
if old_run not in s: raise SystemExit('processing chain anchor missing')
s=s.replace(old_run,new_run,1)

old_warn="""(hasOldRigV50()?'<div class="arv42-warn50">⚠ Model ini sudah punya rig. Rig lama akan DIHAPUS dan digantikan hasil Auto Rig.</div>':'')"""
new_warn="""(hasOldRigV50()?(mapCoreBonesV54().ok?'<div class="arv42-warn50" style="border-color:#3f7a37;background:#12290f;color:#a8e78f">✔ Rig terdeteksi dan dikenali. Tulang inti akan DISEJAJARKAN ke marker — tulang lain (jari, twist, dll.) dan skin weights asli DIPERTAHANKAN.</div>':'<div class="arv42-warn50">⚠ Model punya rig yang tidak dikenali. Rig lama akan DIHAPUS dan digantikan hasil Auto Rig.</div>'):'')"""
if old_warn not in s: raise SystemExit('step1 warning anchor missing')
s=s.replace(old_warn,new_warn,1)

old_res="'<h3>Rig Complete</h3><p>Skeleton humanoid dibuat dari marker dan skin weights sudah dihitung untuk mesh yang belum memiliki skin.</p><div"
new_res="'<h3>Rig Complete</h3><p>'+(S.alignedV54?'Tulang inti disejajarkan ke marker. Struktur rig, tulang tambahan, dan skin weights asli dipertahankan.':'Skeleton humanoid dibuat dari marker dan skin weights sudah dihitung untuk mesh yang belum memiliki skin.')+'</p><div"
if old_res not in s: raise SystemExit('result text anchor missing')
s=s.replace(old_res,new_res,1)

p.write_text(s,encoding='utf-8')
print('Auto Rig align v54: rig lama dipertahankan, tulang inti disejajarkan ke marker')
