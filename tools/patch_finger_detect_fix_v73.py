from pathlib import Path

# PERBAIKAN DETEKSI JARI - FINGER_DETECT_FIX_V73
#
# Pencarian ruas jari milik v72 salah memilih tulang. Terukur pada
# SK_NYX_Lingerie: di bawah satu telapak ada 38 tulang bernama jari, karena
# tiap jari punya metacarpal DAN tiga ruas bernomor, dan setiap tulang punya
# kembaran __dupV55. Penyaring v72 hanya membuang twist/roll/end/nub/tip/ik,
# lalu mengambil tiga teratas menurut kedalaman - sehingga yang terpilih:
#     middle01 -> middle_metacarpal_r
#     middle02 -> middle_metacarpal_r__dupV55
#     middle03 -> middle_01_r
# yaitu tulang telapak, tulang duplikat, lalu baru satu ruas jari asli.
# SK_Mannequin tidak memperlihatkan cacat ini karena rig-nya bersih: hanya
# 15 tulang, _01/_02/_03 per jari, tanpa metacarpal dan tanpa duplikat.
#
# Dua kekeliruan yang diperbaiki:
#   1. __dupV55 ikut terjaring. Penanda itu justru dipasang prepFbxV55 untuk
#      salinan skeleton non-kanonis yang sengaja dijauhkan dari binding.
#   2. Metacarpal dihitung sebagai ruas jari. Ruas jari sebenarnya bernomor;
#      metacarpal tidak. Urutan karena itu diambil dari NOMOR pada nama, bukan
#      dari kedalaman hierarki. Metacarpal hanya dipakai sebagai cadangan bila
#      jari itu sama sekali tidak punya ruas bernomor.
#
# Sekalian: marker jari kini boleh menjadi jangkar Auto Rig di mode Cepat,
# ASALKAN marker itu memang hasil deteksi dari rig model. Pembatasan di v70
# dibuat waktu marker jari masih tebakan kipas - memaku jari ke tebakan itu
# memang lebih buruk daripada memakai proporsi acuan. Sejak v72 marker jari
# bisa berupa deteksi sungguhan, jadi alasan itu tidak berlaku lagi untuk
# marker yang terdeteksi. Marker jari yang masih tebakan tetap tidak dipakai.
#
# Hanya menyentuh animation.html.

p = Path('app/src/main/assets/animation.html')
if not p.exists(): raise SystemExit('animation.html must exist')
s = p.read_text(encoding='utf-8')

if 'FINGER_DETECT_FIX_V73' in s:
    print('Finger detect fix v73 already applied'); raise SystemExit(0)
if 'MARKER_AUTODETECT_V72' not in s: raise SystemExit('marker autodetect v72 must run first')
if 'AUTO_RIG_REFERENCE_SKELETON_V70' not in s: raise SystemExit('reference skeleton v70 must run first')
if "window.__OBJECT_MACHINE__='animation';" not in s: raise SystemExit('bukan dokumen mesin Animation')

# 1. Ganti pencari ruas jari.
old_fn = """  function jariDalamTanganV72(handBone){
    const buruk=/twist|roll|end$|nub|tip$|ik|pole|target/i;
    const per={};
    handBone.traverse(b=>{
      if(!b.isBone||b===handBone)return;
      if(buruk.test(b.name))return;
      const m=/(thumb|index|middle|ring|pinky)/i.exec(b.name);
      if(!m)return;
      const k=m[1].toLowerCase();
      (per[k]=per[k]||[]).push(b);
    });
    const dalam=b=>{let d=0,n=b;while(n&&n!==handBone){d++;n=n.parent}return d};
    for(const k in per)per[k].sort((a,b)=>dalam(a)-dalam(b));
    return per;
  }"""
new_fn = r"""  // FINGER_DETECT_FIX_V73
  // Ruas jari diurutkan dari NOMOR pada namanya, bukan dari kedalaman
  // hierarki. Metacarpal tidak bernomor sehingga tidak ikut mengisi ketiga
  // ruas; ia hanya dipakai bila jari itu tak punya ruas bernomor sama sekali.
  // Kembaran __dupV55 dibuang - penanda itu dipasang prepFbxV55 untuk salinan
  // skeleton non-kanonis yang sengaja dijauhkan dari binding.
  function jariDalamTanganV73(handBone){
    const buruk=/twist|roll|end$|nub|tip$|ik|pole|target|dupv55/i;
    const per={};
    handBone.traverse(b=>{
      if(!b.isBone||b===handBone)return;
      if(buruk.test(b.name))return;
      const m=/(thumb|index|middle|ring|pinky)/i.exec(b.name);
      if(!m)return;
      const k=m[1].toLowerCase();
      // nomor dicari SESUDAH nama jari, supaya angka lain pada awalan nama
      // (mis. awalan berkas atau nomor rig) tidak salah terbaca.
      const ekor=b.name.slice(m.index+m[1].length);
      const num=/(\d+)/.exec(ekor);
      (per[k]=per[k]||[]).push({bone:b,nomor:num?parseInt(num[1],10):null});
    });
    const dalam=b=>{let d=0,n=b;while(n&&n!==handBone){d++;n=n.parent}return d};
    const out={};
    for(const k in per){
      const bernomor=per[k].filter(x=>x.nomor!==null).sort((a,b)=>a.nomor-b.nomor);
      const tanpa=per[k].filter(x=>x.nomor===null).sort((a,b)=>dalam(a.bone)-dalam(b.bone));
      const dipakai=bernomor.length?bernomor:tanpa;
      out[k]=dipakai.slice(0,3).map(x=>x.bone);
    }
    return out;
  }"""
if old_fn not in s: raise SystemExit('pencari ruas jari v72 tidak ditemukan')
s = s.replace(old_fn, new_fn, 1)

old_call = "        const per=jariDalamTanganV72(hb);"
new_call = "        const per=jariDalamTanganV73(hb);"
if old_call not in s: raise SystemExit('pemanggil pencari jari tidak ditemukan')
s = s.replace(old_call, new_call, 1)

# 2. Catat marker mana yang berasal dari rig, bukan dari tebakan.
old_rec = """    let terdeteksi=0;
    const dariRig=markerDariRigV72();
    if(dariRig){
      for(const k in dariRig){
        if(!m[k]||!dariRig[k])continue;
        m[k].copy(dariRig[k]); terdeteksi++;
      }
    }
    S.markerAutoV72=terdeteksi;"""
new_rec = """    let terdeteksi=0;
    const dariRig=markerDariRigV72();
    const dariRigSetV73=new Set();
    if(dariRig){
      for(const k in dariRig){
        if(!m[k]||!dariRig[k])continue;
        m[k].copy(dariRig[k]); terdeteksi++; dariRigSetV73.add(k);
      }
    }
    // Dipakai buildAnchorMapV70 untuk membedakan marker hasil deteksi dari
    // marker yang masih tebakan.
    S.markerFromRigV73=dariRigSetV73;
    S.markerAutoV72=terdeteksi;"""
if old_rec not in s: raise SystemExit('pencatat marker otomatis tidak ditemukan')
s = s.replace(old_rec, new_rec, 1)

# 3. Marker jari boleh jadi jangkar di mode Cepat bila memang hasil deteksi.
old_pairs = """    const pairs=ANCHOR_PAIRS_V70.concat(
      S.markerModeV69==='jari' ? fingerPairsV70(ref.bones) : []);"""
new_pairs = """    // Marker jari dipakai sebagai jangkar bila pengguna memang memakai mode
    // per sendi jari, ATAU bila marker itu hasil deteksi dari rig model.
    // Marker jari yang masih tebakan kipas tetap tidak dipakai - untuk itu
    // proporsi acuan lebih dipercaya daripada tebakan.
    const dariRigV73=S.markerFromRigV73;
    const bolehJariV73=k=>S.markerModeV69==='jari'||(dariRigV73&&dariRigV73.has(k));
    const pairs=ANCHOR_PAIRS_V70.concat(
      fingerPairsV70(ref.bones).filter(([bL,bR,base])=>bolehJariV73(base+'L')&&bolehJariV73(base+'R')));"""
if old_pairs not in s: raise SystemExit('gerbang jangkar jari v70 tidak ditemukan')
s = s.replace(old_pairs, new_pairs, 1)

p.write_text(s, encoding='utf-8')
print('Finger detect fix v73 applied: ruas jari diurut dari nomor, duplikat dibuang, marker jari terdeteksi jadi jangkar')
