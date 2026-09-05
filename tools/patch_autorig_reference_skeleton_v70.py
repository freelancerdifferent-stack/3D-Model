from pathlib import Path

# SKELETON ACUAN DARI FBX - AUTO_RIG_REFERENCE_SKELETON_V70
#
# generateSkeleton() lama membangun 24 tulang dengan proporsi yang ditulis mati
# di dalam kode. Badan fungsi itu DIGANTI UTUH: struktur tulang kini dibaca dari
# rig_reference.json - hasil mesin ekstrak v68 atas FBX di asset/fbx-loader/.
# Ganti FBX acuan = ganti struktur rig, tanpa menyentuh kode.
#
# Cara memetakan acuan ke model pengguna:
#   Acuan menyimpan posisi 'unit' (titik nol di telapak kaki, dibagi tinggi),
#   jadi bebas skala. Marker yang dipasang pengguna menjadi JANGKAR: tiap tulang
#   acuan yang punya padanan marker ditempelkan tepat di marker itu. Tulang di
#   antara dua jangkar diinterpolasi sepanjang rantai, lengkap dengan simpangan
#   tegak lurusnya supaya bentuk acuan tidak hilang. Tulang di luar jangkar
#   terakhir (mis. B_Jaw, twist, atau jari saat mode Cepat) digantung pada
#   induknya memakai skala rantai induk.
#
#   Saat satu tulang punya lebih dari satu jangkar keturunan (mis. spine_03
#   bercabang ke kepala dan ke kedua lengan), yang dipilih adalah cabang yang
#   arahnya paling melanjutkan arah datang dari jangkar leluhur - bukan yang
#   kebetulan pertama ditemukan.
#
# Rotasi rest tulang sengaja dibiarkan identitas, sama seperti generateSkeleton
# lama, karena jalur retarget di mesin ini bertumpu pada anggapan itu.
#
# Kalau rig_reference.json tidak ada atau tidak sah, Auto Rig BERHENTI dengan
# pesan jelas. Tidak ada diam-diam kembali ke 24 tulang lama.
#
# Hanya menyentuh animation.html.

p = Path('app/src/main/assets/animation.html')
if not p.exists(): raise SystemExit('animation.html must exist')
s = p.read_text(encoding='utf-8')

if 'AUTO_RIG_REFERENCE_SKELETON_V70' in s:
    print('Auto Rig reference skeleton v70 already applied'); raise SystemExit(0)
if 'AUTO_RIG_MARKER_MODES_V69' not in s: raise SystemExit('marker modes v69 must run first')
if "window.__OBJECT_MACHINE__='animation';" not in s: raise SystemExit('bukan dokumen mesin Animation')

START = '  function generateSkeleton(){'
END = '  async function skinGeometry(){'
i = s.find(START); j = s.find(END, i)
if i < 0 or j < 0: raise SystemExit('generateSkeleton lama tidak ditemukan')
old = s[i:j]
if 'Spine02' not in old or 'LeftUpLeg' not in old:
    raise SystemExit('blok generateSkeleton lama tidak seperti yang diharapkan')

new = r'''  // AUTO_RIG_REFERENCE_SKELETON_V70
  let refPromiseV70=null;
  function loadRigReferenceV70(){
    if(refPromiseV70)return refPromiseV70;
    refPromiseV70=fetch('rig_reference.json')
      .then(r=>{if(!r.ok)throw new Error('rig_reference.json tidak terbaca ('+r.status+')');return r.json()})
      .then(d=>{
        if(!d||d.marker!=='RIG_REFERENCE_V68')throw new Error('rig_reference.json bukan RIG_REFERENCE_V68');
        if(!Array.isArray(d.bones)||!d.bones.length)throw new Error('rig_reference.json tidak memuat tulang');
        const seen=new Set();
        for(const b of d.bones){
          if(!b.name||!Array.isArray(b.unit)||b.unit.length!==3)throw new Error('tulang acuan cacat: '+(b&&b.name));
          if(seen.has(b.name))throw new Error('nama tulang acuan kembar: '+b.name);
          seen.add(b.name);
        }
        for(const b of d.bones){
          if(b.parent&&!seen.has(b.parent))throw new Error('induk acuan menggantung: '+b.name+' -> '+b.parent);
        }
        return d;
      })
      .catch(e=>{refPromiseV70=null;throw e});
    return refPromiseV70;
  }

  // Peran anatomi -> nama tulang DI DALAM ACUAN. Diturunkan dari isi acuan,
  // bukan daftar nama mati, supaya berganti FBX acuan tidak memutus apa pun.
  // Kosakata regexnya sengaja sama dengan mapCoreBonesV54 agar penilaian peran
  // di kedua tempat konsisten.
  let rolesMemoV70=null;
  function refRolesV70(ref){
    if(rolesMemoV70&&rolesMemoV70.__ref===ref)return rolesMemoV70;
    const bad=/twist|roll|helper|(^|[^a-z])ik|pole|target|nub|end$|tip$|top$|front|thumb|index|middle|ring|pinky|finger|eye|jaw|tongue|(^|[^a-z])ear|breast|weapon|prop|attach|dupv55/;
    const norm=n=>String(n||'').toLowerCase().replace(/^.*[:]/,'').replace(/[\s_\-\.]/g,'');
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
      return null;
    };
    const sideOf=b=>{
      const t=String(b.name).toLowerCase();
      if(/left/.test(t)||/[._-]l$/.test(t))return 'L';
      if(/right/.test(t)||/[._-]r$/.test(t))return 'R';
      return (b.unit&&b.unit[0]>0)?'L':'R';
    };
    const out={hips:null,head:null,neck:null,spine:[],L:{},R:{},__ref:ref};
    const spine=[];
    for(const b of ref.bones){
      const r=roleOf(norm(b.name));
      if(!r)continue;
      const d=b.depth|0;
      if(r==='spine'){spine.push(b);continue}
      if(r==='hips'||r==='head'||r==='neck'){
        const cur=out[r];
        if(!cur||d<cur.depth)out[r]=b;
        continue;
      }
      const sd=sideOf(b),slot=out[sd];
      if(!slot[r]||d<slot[r].depth)slot[r]=b;
    }
    spine.sort((a,b)=>(a.depth|0)-(b.depth|0));
    out.spine=spine.map(b=>b.name);
    out.hips=out.hips?out.hips.name:null;
    out.head=out.head?out.head.name:null;
    out.neck=out.neck?out.neck.name:null;
    for(const sd of ['L','R']){const o={};for(const k in out[sd])o[k]=out[sd][k].name;out[sd]=o}
    if(!out.hips)throw new Error('Acuan tidak punya tulang panggul yang dikenali.');
    if(!out.spine.length)out.spine=[out.hips];
    rolesMemoV70=out;return out;
  }

  // Padanan tulang acuan -> marker, ditulis sebagai PASANGAN SISI, bukan nama
  // mati. Sisi mana yang dipakai ditentukan dari geometri, karena kedua sistem
  // tidak sepakat soal arti "kiri": acuan UE4 memakai kiri ANATOMIS (tulang _l
  // ada di +X, mis. hand_l unit x = +0.292), sedangkan marker aplikasi memakai
  // kiri dari SUDUT PANDANG PENONTON (wristL bawaan ada di -X). Memasangkan
  // lewat huruf L/R begitu saja membuat tulang kiri menempel di sisi kanan
  // model - rig tercermin. Yang menentukan adalah letak sebenarnya, sehingga
  // acuan dengan konvensi mana pun tetap mendarat di sisi yang benar, termasuk
  // kalau pengguna menggeser marker melewati garis tengah.
  const ANCHOR_SOLO_V70={pelvis:'groin', head:'chin'};
  const ANCHOR_PAIRS_V70=[
    ['upperarm_l','upperarm_r','shoulder'],
    ['lowerarm_l','lowerarm_r','elbow'],
    ['hand_l','hand_r','wrist'],
    ['calf_l','calf_r','knee'],
    ['foot_l','foot_r','ankle'],
    ['ball_l','ball_r','toe'],
  ];
  function fingerPairsV70(refBones){
    const out=[];
    for(const b of refBones){
      const m=/^(thumb|index|middle|ring|pinky)_(\d{2})_l$/.exec(b.name);
      if(m)out.push([m[0], m[1]+'_'+m[2]+'_r', m[1]+m[2]]);
    }
    return out;
  }
  // Peta jangkar dibangun ulang tiap kali skeleton dibuat, karena posisi marker
  // bisa berubah di antara dua percobaan.
  function buildAnchorMapV70(ref,refPos){
    const map={};
    for(const bn in ANCHOR_SOLO_V70){
      if(refPos[bn]&&S.markers[ANCHOR_SOLO_V70[bn]])map[bn]=ANCHOR_SOLO_V70[bn];
    }
    const pairs=ANCHOR_PAIRS_V70.concat(
      S.markerModeV69==='jari' ? fingerPairsV70(ref.bones) : []);
    for(const [bL,bR,base] of pairs){
      const mL=S.markers[base+'L'], mR=S.markers[base+'R'];
      if(!refPos[bL]||!refPos[bR]||!mL||!mR)continue;
      const dBone=refPos[bL].x-refPos[bR].x;              // + bila _l di sisi X positif
      const dMk=(mL.x-S.center.x)-(mR.x-S.center.x);      // + bila markerL di sisi X positif
      const searah=(Math.abs(dBone)<1e-9||Math.abs(dMk)<1e-9)?1:Math.sign(dBone*dMk);
      map[bL]=searah>=0?base+'L':base+'R';
      map[bR]=searah>=0?base+'R':base+'L';
    }
    return map;
  }

  function generateSkeleton(){
    const ref=S.refV70;
    if(!ref)throw new Error('Struktur acuan belum dimuat (rig_reference.json).');
    if(S.helper){scene.remove(S.helper);S.helper=null}
    S.bones=[];

    const rows=ref.bones.slice().sort((a,b)=>(a.depth|0)-(b.depth|0));
    const byName={}; for(const r of rows) byName[r.name]=r;
    const kids={}; for(const r of rows){ if(r.parent)(kids[r.parent]=kids[r.parent]||[]).push(r.name); }
    const refPos={}; for(const r of rows) refPos[r.name]=new THREE.Vector3(r.unit[0],r.unit[1],r.unit[2]);

    // Jangkar: tulang acuan yang punya marker terpasang. Marker jari hanya ada
    // di mode "jari"; kalau tidak ada, tulang itu bukan jangkar.
    const anchorMap=buildAnchorMapV70(ref,refPos);
    const anchor={};
    for(const r of rows){
      const key=anchorMap[r.name];
      if(key&&S.markers[key])anchor[r.name]=S.markers[key].clone();
    }
    if(!Object.keys(anchor).length)throw new Error('Tidak ada marker yang cocok dengan struktur acuan.');

    // Skala menyeluruh dipakai hanya bila sebuah tulang tidak punya jangkar
    // leluhur maupun induk yang sudah ditempatkan.
    const H=Math.max(S.size.y,1e-6);
    const originW=new THREE.Vector3(S.center.x,S.box.min.y,S.center.z);
    const unitToWorld=u=>originW.clone().addScaledVector(u,H);

    // Jangkar terdekat di dalam subtree (tidak termasuk simpul itu sendiri
    // saat dipanggil dari induknya). Dihitung sekali, kedalaman terkecil menang.
    const nearestAnchorMemo={};
    function nearestAnchorIn(name){
      if(name in nearestAnchorMemo)return nearestAnchorMemo[name];
      let out=null;
      if(anchor[name])out=name;
      else{
        let best=null,bestDepth=Infinity;
        for(const c of (kids[name]||[])){
          const got=nearestAnchorIn(c);
          if(got&&(byName[got].depth|0)<bestDepth){best=got;bestDepth=byName[got].depth|0}
        }
        out=best;
      }
      nearestAnchorMemo[name]=out;return out;
    }
    const ancestorAnchorOf=name=>{
      let n=byName[name]?byName[name].parent:null;
      while(n){ if(anchor[n])return n; n=byName[n]?byName[n].parent:null; }
      return null;
    };

    const target={},chainScale={};
    for(const r of rows){
      const name=r.name;
      if(anchor[name]){
        target[name]=anchor[name].clone();
        const A=ancestorAnchorOf(name);
        if(A){
          const dRef=refPos[name].distanceTo(refPos[A]);
          chainScale[name]=dRef>1e-9?(target[name].distanceTo(target[A])/dRef):(chainScale[A]||H);
        }else chainScale[name]=H;
        continue;
      }
      const A=ancestorAnchorOf(name);
      // Jangkar keturunan per cabang; pilih cabang yang paling melanjutkan
      // arah datang, supaya tulang belakang tidak tertarik ke arah lengan.
      let D=null;
      const cands=[];
      for(const c of (kids[name]||[])){ const got=nearestAnchorIn(c); if(got)cands.push(got); }
      if(cands.length===1)D=cands[0];
      else if(cands.length>1){
        const inDir=A?refPos[name].clone().sub(refPos[A]):null;
        if(inDir&&inDir.lengthSq()>1e-12){
          inDir.normalize();
          let best=null,bestDot=-Infinity;
          for(const c of cands){
            const v=refPos[c].clone().sub(refPos[name]);
            if(v.lengthSq()<1e-12)continue;
            const d=v.normalize().dot(inDir);
            if(d>bestDot){bestDot=d;best=c}
          }
          D=best||cands[0];
        }else D=cands[0];
      }

      if(A&&D&&A!==D){
        const u=refPos[D].clone().sub(refPos[A]);
        const len2=u.lengthSq();
        if(len2>1e-12){
          const rel=refPos[name].clone().sub(refPos[A]);
          const t=rel.dot(u)/len2;
          const residual=rel.clone().addScaledVector(u,-t);
          // D belum tentu sudah ditempatkan, jadi pakai posisi jangkarnya langsung.
          const tgtA=target[A]||anchor[A],tgtD=anchor[D];
          const s=tgtD.distanceTo(tgtA)/Math.sqrt(len2);
          target[name]=tgtA.clone().addScaledVector(tgtD.clone().sub(tgtA),t).addScaledVector(residual,s);
          chainScale[name]=s;
          continue;
        }
      }
      const par=r.parent;
      if(par&&target[par]){
        const s=chainScale[par]||H;
        target[name]=target[par].clone().addScaledVector(refPos[name].clone().sub(refPos[par]),s);
        chainScale[name]=s;
      }else{
        target[name]=unitToWorld(refPos[name]);
        chainScale[name]=H;
      }
    }

    // Bangun pohon tulang persis seperti acuan.
    const nodes={};
    for(const r of rows){
      const b=new THREE.Bone();b.name=r.name;nodes[r.name]=b;
      if(r.parent&&nodes[r.parent])nodes[r.parent].add(b);else root.add(b);
    }
    // Rotasi rest dibiarkan identitas; posisi lokal = selisih posisi dunia
    // dalam ruang lokal root, sama seperti makeBone lama.
    for(const r of rows){
      const lp=localPoint(target[r.name]);
      nodes[r.name].position.copy(r.parent&&nodes[r.parent]?lp.clone().sub(localPoint(target[r.parent])):lp);
    }
    S.bones=rows.map(r=>nodes[r.name]);

    root.updateMatrixWorld(true);
    S.skeleton=new THREE.Skeleton(S.bones);S.skeleton.calculateInverses();
    S.helper=new THREE.SkeletonHelper(root);S.helper.material.depthTest=false;S.helper.material.transparent=true;S.helper.material.opacity=.95;scene.add(S.helper);
    S.anchorCountV70=Object.keys(anchor).length;
    console.log('AUTO_RIG_REFERENCE_SKELETON_V70: '+S.bones.length+' tulang dari acuan '+(ref.source||'?')+', '+S.anchorCountV70+' jangkar marker');
    const specs={};for(const r of rows)specs[r.name]={bone:nodes[r.name]};
    return specs;
  }

'''

s = s[:i] + new + s[j:]

# Acuan dimuat sebelum percabangan Step 4 (renderProcessingStep sudah async).
old_try = "try{set(12);await new Promise(r=>setTimeout(r,80));S.alignedV54=false;"
new_try = "try{set(12);S.refV70=await loadRigReferenceV70();await new Promise(r=>setTimeout(r,80));S.alignedV54=false;"
if old_try not in s: raise SystemExit('titik muat acuan di Step 4 tidak ditemukan')
s = s.replace(old_try, new_try, 1)

# Teks UI: tidak lagi "24 tulang".
old_mode = '<b>\U0001f9b4 Ganti rig standar 24 tulang</b><span>Semua tulang lama dihapus dan diganti skeleton standar &mdash; skin weights asli DIPETAKAN ke tulang baru. Cocok untuk library animasi dan export ringan.</span>'
old_mode = old_mode.replace('&mdash;', '—')
if old_mode not in s: raise SystemExit('teks mode rebuild tidak ditemukan')
s = s.replace(old_mode, '<b>\U0001f9b4 Ganti rig dari FBX acuan</b><span>Semua tulang lama dihapus dan diganti struktur dari rig_reference.json — skin weights asli DIPETAKAN ke tulang baru.</span>', 1)

old_res = 'Rig lama diganti skeleton standar 24 tulang — skin weights asli dipetakan ke tulang baru.'
if old_res not in s: raise SystemExit('teks hasil rebuild tidak ditemukan')
s = s.replace(old_res, 'Rig lama diganti struktur dari FBX acuan — skin weights asli dipetakan ke tulang baru.', 1)

old_gen = 'Skeleton humanoid dibuat dari marker dan skin weights sudah dihitung untuk mesh yang belum memiliki skin.'
if old_gen not in s: raise SystemExit('teks hasil generate tidak ditemukan')
s = s.replace(old_gen, 'Skeleton dibangun dari struktur FBX acuan, ditempelkan ke marker, dan skin weights sudah dihitung.', 1)

# Pemetaan bobot pada rebuildRigKeepWeightsV57 memakai NAMA TULANG LAMA
# (Hips, LeftUpLeg, ...). Setelah v70 tulang bernama mengikuti acuan, sehingga
# setiap pencarian meleset dan seluruh vertex jatuh ke cadangan idxOf.Hips||0
# alias indeks 0. Diukur sebelum perbaikan: 123.012 vertex, 1 tulang terpakai
# dari 61 - mesh jadi satu balok kaku. Nama sasarannya karena itu diambil dari
# peran acuan. Ini bukan tambalan atas kode yang sudah rusak, melainkan
# menyambungkan pemakai ke penamaan baru yang v70 perkenalkan.
pairs = [
    ("    if(map.hips)coreName.set(map.hips,'Hips');\n    const spN=['Spine02','Spine01','Spine'];",
     "    const RR=refRolesV70(S.refV70);\n    if(map.hips)coreName.set(map.hips,RR.hips);\n    const spN=RR.spine;"),
    ("    map.neck.forEach(b=>coreName.set(b,'neck'));",
     "    map.neck.forEach(b=>coreName.set(b,RR.neck||RR.spine[RR.spine.length-1]||RR.hips));"),
    ("    if(map.head)coreName.set(map.head,'Head');",
     "    if(map.head)coreName.set(map.head,RR.head||RR.neck||RR.hips);"),
    ("""    const sideNames={L:{clav:'LeftShoulder',upperarm:'LeftArm',forearm:'LeftForeArm',hand:'LeftHand',thigh:'LeftUpLeg',calf:'LeftLeg',foot:'LeftFoot',toe:'LeftToeBase'},
                     R:{clav:'RightShoulder',upperarm:'RightArm',forearm:'RightForeArm',hand:'RightHand',thigh:'RightUpLeg',calf:'RightLeg',foot:'RightFoot',toe:'RightToeBase'}};""",
     "    const sideNames={L:RR.L,R:RR.R};"),
    ("    const nameOf=b=>{let n=b;while(n&&n.isBone){if(coreName.has(n))return coreName.get(n);n=n.parent}return 'Hips'};",
     "    const nameOf=b=>{let n=b;while(n&&n.isBone){if(coreName.has(n))return coreName.get(n);n=n.parent}return RR.hips};"),
    ("            const bi=idxOf[j.table[oldIdx.getComponent(i,k)]||'Hips'];",
     "            const bi=idxOf[j.table[oldIdx.getComponent(i,k)]||RR.hips];"),
    ("          if(sum<=0){ni[i*4]=idxOf.Hips||0;nw[i*4]=1;continue}",
     "          if(sum<=0){ni[i*4]=idxOf[RR.hips]||0;nw[i*4]=1;continue}"),
    ("      }else{for(let i=0;i<n;i++){ni[i*4]=idxOf.Hips||0;nw[i*4]=1}}",
     "      }else{for(let i=0;i<n;i++){ni[i*4]=idxOf[RR.hips]||0;nw[i*4]=1}}"),
]
for a, b in pairs:
    if a not in s:
        raise SystemExit('titik sambung bobot tidak ditemukan: ' + a.strip()[:70])
    s = s.replace(a, b, 1)

# Komentar hierarki lama di atas generateSkeleton sudah tidak menggambarkan
# kode yang ada; dibuang supaya tidak menyesatkan.
stale = """  // Humanoid hierarchy is intentionally matched to the supplied run.glb reference:
  // Hips -> (LeftUpLeg, RightUpLeg, Spine02)
  // Spine02 -> Spine01 -> Spine -> (LeftShoulder, RightShoulder, neck)
  // neck -> Head -> (head_end, headfront)
  // shoulders -> arm -> forearm -> hand; legs -> leg -> foot -> toe.
"""
if stale in s:
    s = s.replace(stale, '', 1)

p.write_text(s, encoding='utf-8')
print('Auto Rig reference skeleton v70 applied: generateSkeleton kini membangun tulang dari rig_reference.json')
