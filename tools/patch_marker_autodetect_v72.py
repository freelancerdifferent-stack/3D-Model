from pathlib import Path

# MARKER MENGIKUTI RIG MODEL - MARKER_AUTODETECT_V72
#
# initMarkers milik v69 diganti utuh. Sebelumnya semua marker ditaruh dari
# pecahan kotak batas model - tebakan kasar yang harus digeser satu per satu.
# Sekarang, kalau model yang diimpor sudah punya rig yang dikenali, marker
# dipasang tepat di sendi aslinya; pengguna tinggal membetulkan yang meleset.
#
# Sumber deteksinya mapCoreBonesV54, yang sudah dipakai Auto Rig untuk menilai
# peran tulang. Diuji pada dua model: SK_Mannequin (64 tulang) dan
# SK_NYX_Lingerie (451 tulang) - keduanya mengenali panggul, kepala, tulang
# belakang, leher, serta bahu/siku/pergelangan dan paha/lutut/telapak/ujung
# kaki di kedua sisi. Jadi 14 dari 15 marker mode Cepat bisa langsung tepat.
# headTop tidak punya tulang, jadi tetap dari puncak kotak model.
#
# JARI DICARI DI DALAM KETURUNAN TULANG hand, BUKAN DISAPU DARI SELURUH RIG.
# Ini bukan kerapian: di NYX, pencarian nama 'ring' secara global cocok dengan
# 84 tulang - jelas bukan jari, kemungkinan tulang rambut atau kain. Kalau
# disapu global, marker jari akan menempel ke tulang rambut.
#
# Sisi kiri/kanan ditentukan dari posisi X sebenarnya, bukan huruf pada nama,
# sama seperti pemasangan jangkar v70. Marker '...L' milik aplikasi berada di
# sisi X negatif, jadi tulang dengan X lebih kecil yang mengisinya - dengan
# begitu marker mendarat di sisi yang benar secara fisik apa pun konvensi
# penamaan berkas sumbernya.
#
# Model tanpa rig, atau rig yang tidak dikenali, tetap memakai tebakan
# proporsi seperti sebelumnya - tidak ada yang dibiarkan kosong.
#
# Hanya menyentuh animation.html.

p = Path('app/src/main/assets/animation.html')
if not p.exists(): raise SystemExit('animation.html must exist')
s = p.read_text(encoding='utf-8')

if 'MARKER_AUTODETECT_V72' in s:
    print('Marker autodetect v72 already applied'); raise SystemExit(0)
if 'AUTO_RIG_MARKER_MODES_V69' not in s: raise SystemExit('marker modes v69 must run first')
if 'function mapCoreBonesV54()' not in s: raise SystemExit('mapCoreBonesV54 tidak ada')
if "window.__OBJECT_MACHINE__='animation';" not in s: raise SystemExit('bukan dokumen mesin Animation')

START = '  function initMarkers(){'
END = '\n  function projectMarkers(){'
i = s.find(START); j = s.find(END, i)
if i < 0 or j < 0: raise SystemExit('initMarkers v69 tidak ditemukan')
old = s[i:j]
if 'MK_FINGERS_V69' not in old: raise SystemExit('initMarkers bukan versi v69')

new = r'''  // MARKER_AUTODETECT_V72
  // Kumpulkan ruas jari DI DALAM keturunan satu tulang telapak. Pencarian nama
  // secara global tidak aman: di NYX kata 'ring' cocok dengan 84 tulang.
  function jariDalamTanganV72(handBone){
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
  }

  // Baca posisi sendi dari rig yang sudah ada pada model. Balikan null kalau
  // model tidak punya rig yang dikenali.
  function markerDariRigV72(){
    if(typeof hasOldRigV50!=='function'||!hasOldRigV50())return null;
    let map=null;
    try{map=mapCoreBonesV54()}catch(e){console.warn('MARKER_AUTODETECT_V72 deteksi',e);return null}
    if(!map||!map.ok)return null;
    root.updateMatrixWorld(true);
    const W=b=>b?b.getWorldPosition(new THREE.Vector3()):null;
    const out={};
    if(map.hips)out.groin=W(map.hips);
    if(map.head)out.chin=W(map.head);
    // Pasangan bersisi: yang X-nya lebih kecil mengisi marker '...L',
    // mengikuti konvensi marker aplikasi.
    const pasang=(peran,base)=>{
      const sd=map.sided&&map.sided[peran];
      if(!sd||!sd.L||!sd.R)return null;
      const a=W(sd.L),b=W(sd.R);
      if(!a||!b)return null;
      const kiri=(a.x<=b.x)?a:b, kanan=(a.x<=b.x)?b:a;
      const tulangKiri=(a.x<=b.x)?sd.L:sd.R, tulangKanan=(a.x<=b.x)?sd.R:sd.L;
      out[base+'L']=kiri; out[base+'R']=kanan;
      return {L:tulangKiri,R:tulangKanan};
    };
    pasang('upperarm','shoulder');
    pasang('forearm','elbow');
    const tangan=pasang('hand','wrist');
    pasang('calf','knee');
    pasang('foot','ankle');
    pasang('toe','toe');
    // Jari mengikuti tulang telapak sisi yang sama.
    if(tangan){
      for(const sisi of ['L','R']){
        const hb=tangan[sisi]; if(!hb)continue;
        const per=jariDalamTanganV72(hb);
        for(const nama in per){
          const ruas=per[nama];
          for(let j=0;j<Math.min(3,ruas.length);j++){
            out[nama+'0'+(j+1)+sisi]=W(ruas[j]);
          }
        }
      }
    }
    return out;
  }

  function initMarkers(){
    S.box=modelBox();S.size=S.box.getSize(new THREE.Vector3());S.center=S.box.getCenter(new THREE.Vector3());
    const b=S.box,c=S.center,w=S.size.x,h=S.size.y,z=c.z;
    const P=(x,y,zz)=>new THREE.Vector3(x,y,zz===undefined?z:zz);
    if(!S.markerModeV69)S.markerModeV69='cepat';
    S.markerGroupV69=S.markerGroupV69||'Tubuh';
    // Lapis pertama: tebakan proporsi, supaya tidak ada marker yang kosong.
    const m={
      headTop:P(c.x,b.min.y+h*.97),
      chin:P(c.x,b.min.y+h*.88),
      shoulderL:P(c.x-w*.22,b.min.y+h*.77),shoulderR:P(c.x+w*.22,b.min.y+h*.77),
      elbowL:P(c.x-w*.36,b.min.y+h*.61),elbowR:P(c.x+w*.36,b.min.y+h*.61),
      wristL:P(c.x-w*.46,b.min.y+h*.48),wristR:P(c.x+w*.46,b.min.y+h*.48),
      groin:P(c.x,b.min.y+h*.48),
      kneeL:P(c.x-w*.12,b.min.y+h*.27),kneeR:P(c.x+w*.12,b.min.y+h*.27),
      ankleL:P(c.x-w*.12,b.min.y+h*.055),ankleR:P(c.x+w*.12,b.min.y+h*.055),
      toeL:P(c.x-w*.12,b.min.y+h*.015,z+h*.08),toeR:P(c.x+w*.12,b.min.y+h*.015,z+h*.08),
    };
    const seg=h*.020, fan=h*.017;
    const upV69=new THREE.Vector3(0,1,0);
    for(const side of ['L','R']){
      const wr=m['wrist'+side], el=m['elbow'+side];
      let dir=wr.clone().sub(el);
      if(dir.lengthSq()<1e-9)dir=new THREE.Vector3(side==='L'?-1:1,0,0);
      dir.normalize();
      let perp=new THREE.Vector3().crossVectors(dir,upV69);
      if(perp.lengthSq()<1e-6)perp=new THREE.Vector3().crossVectors(dir,new THREE.Vector3(0,0,1));
      perp.normalize();
      MK_FINGERS_V69.forEach(([f],fi)=>{
        const lateral=(fi-2)*fan;
        for(let j=1;j<=3;j++){
          m[f+'0'+j+side]=wr.clone().addScaledVector(dir,seg*j).addScaledVector(perp,lateral);
        }
      });
    }
    // Lapis kedua: kalau model punya rig yang dikenali, timpa dengan sendi asli.
    let terdeteksi=0;
    const dariRig=markerDariRigV72();
    if(dariRig){
      for(const k in dariRig){
        if(!m[k]||!dariRig[k])continue;
        m[k].copy(dariRig[k]); terdeteksi++;
      }
    }
    S.markerAutoV72=terdeteksi;
    S.markerTotalV72=Object.keys(m).length;
    if(terdeteksi)console.log('MARKER_AUTODETECT_V72: '+terdeteksi+' dari '+S.markerTotalV72+' marker dipasang dari rig model');
    S.markers=m;
  }
'''

s = s[:i] + new + s[j:]

# Beri tahu pengguna berapa marker yang sudah otomatis, supaya jelas mana yang
# tinggal dibetulkan.
old_p = "      +'<p>Geser marker ke titik anatomi yang sesuai. Marker ini menjadi sumber utama pembentukan skeleton.</p>'"
new_p = ("      +(S.markerAutoV72\n"
         "        ? '<p>'+S.markerAutoV72+' dari '+S.markerTotalV72+' marker sudah dipasang otomatis dari rig model. Betulkan yang meleset saja.</p>'\n"
         "        : '<p>Geser marker ke titik anatomi yang sesuai. Marker ini menjadi sumber utama pembentukan skeleton.</p>')")
if old_p not in s: raise SystemExit('paragraf Step 3 tidak ditemukan')
s = s.replace(old_p, new_p, 1)

p.write_text(s, encoding='utf-8')
print('Marker autodetect v72 applied: marker mengikuti rig model bila dikenali')
