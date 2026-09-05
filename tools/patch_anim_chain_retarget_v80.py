#!/usr/bin/env python3
# ANIM_CHAIN_RETARGET_V80 - animasi dari library juga benar pada rig bawaan model.
#
# Gejalanya: animasi diterapkan ke model yang belum di-Auto Rig membuat punggung
# dan kepala terlalu menunduk. Terukur pada SK_NYX_Lingerie: condong batang tubuh
# +36.9 derajat, sedangkan animasi aslinya hanya +22.5 derajat.
#
# Sebabnya bukan matematika retargetnya, melainkan pencocokan nama satu-satu saat
# jumlah ruas rantai tulang belakang berbeda. Rig sumber animasi punya spine_01..03
# dan neck_01; rig bawaan NYX punya spine_01..05 dan neck_01, neck_02. Ruas yang
# tidak punya padanan tetap di pose bind, jadi seluruh tekukan badan - yang di
# sumber tersebar dari pinggul sampai bahu - termampat ke punggung bawah, lalu
# punggung atas membawanya kaku di atasnya. Tekukan menumpuk.
#
# Perbaikannya: tekukan dibagi menurut POSISI RELATIF sendi sepanjang rantai,
# bukan menurut nama. Selisih rotasi sumber dibaca sebagai fungsi ketinggian
# relatif 0..1 di sepanjang rantai, lalu tiap sendi rig tujuan mengambil nilai
# pada ketinggian relatifnya sendiri lewat slerp. Panjang rantai boleh berbeda;
# bentuk lengkung punggungnya tetap sama.
#
# Satu hal yang menentukan: rantai HARUS bermula di sendi yang sama di kedua rig.
# Beberapa rig menaruh tulang tambahan di bawah pinggul - NYX punya 'root' di
# lantai - dan kalau ruas itu ikut terhitung, pinggul bergeser ke tengah rantai
# sehingga seluruh tulang belakang menerima tekukan bagian atas. Terukur: tanpa
# penyelarasan pangkal hasilnya masih +28.8 derajat; dengan penyelarasan +22.6
# derajat, yaitu 0.2 derajat dari animasi aslinya.
#
# Pembagian hanya dinyalakan kalau memang ada ruas rantai rig tujuan yang tidak
# dianimasikan sumber. Kalau seluruh rantai berpadanan - misalnya rig hasil Auto
# Rig, yang strukturnya acuan itu sendiri - jalur nama langsung tetap dipakai apa
# adanya, jadi hasil yang sudah terverifikasi tidak berubah sedikit pun.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'ANIM_CHAIN_RETARGET_V80' in s:
    raise SystemExit('ANIM_CHAIN_RETARGET_V80 sudah ada - patch dijalankan dua kali')
if 'ANIM_PORTAL_V79' not in s:
    raise SystemExit('portal Anim v79 tidak ditemukan - urutan pipeline salah')

awal = '  function retargetV79(akar,lib,klip){'
akhir = ('    return{clip:new THREE.AnimationClip(klip.name,dur,tracks),cocok:cocok.length,'
         'total:total,skala:skala};\n  }\n')
i = s.find(awal)
if i < 0:
    raise SystemExit('fungsi retargetV79 tidak ditemukan')
j = s.find(akhir, i)
if j < 0:
    raise SystemExit('akhir fungsi retargetV79 tidak ditemukan')
j += len(akhir)

baru = r"""  // ANIM_CHAIN_RETARGET_V80 - rantai aksial (pinggul -> kepala)
  //
  // Dipakai saat jumlah ruas rantai rig tujuan berbeda dari rig sumber.
  // Mencocokkan nama satu-satu di situ memampatkan seluruh tekukan badan ke ruas
  // yang lebih pendek, lalu ruas sisanya membawanya kaku - badan jadi menunduk
  // berlebihan.
  const NAMA_ATAS_V80=/^head(_?\d+)?$/i;
  function puncakRantaiV80(nama){
    for(const n of nama)if(NAMA_ATAS_V80.test(n))return n;
    return null;
  }
  function rantaiTujuanV80(bindTgt,atas){
    const jalur=[];let d=bindTgt.get(atas);
    while(d){jalur.push(d.bone.name);
      const pr=d.bone.parent;
      d=(pr&&pr.isBone&&bindTgt.has(pr.name))?bindTgt.get(pr.name):null}
    return jalur.reverse();
  }
  function rantaiSumberV80(bindSrc,atas,pangkal){
    const jalur=[];let n=atas;
    while(n&&bindSrc[n]){jalur.push(n);if(n===pangkal)break;n=bindSrc[n].parent}
    return jalur.reverse();
  }
  // Rantai HARUS bermula di sendi yang sama di kedua rig. Beberapa rig menaruh
  // tulang tambahan di bawah pinggul - misalnya 'root' di lantai - dan kalau ruas
  // itu ikut terhitung, pinggul bergeser jauh dari pangkal sehingga seluruh
  // tulang belakang menerima tekukan bagian atas.
  function potongPangkalV80(jalur,adaDiSumber){
    let i=0;while(i<jalur.length-1&&!adaDiSumber(jalur[i]))i++;
    return jalur.slice(i);
  }
  // Posisi relatif tiap sendi sepanjang rantai, 0 di pangkal sampai 1 di puncak,
  // diukur dari jarak pose bind - itulah yang membuat pembagian tetap sepadan
  // meski panjang ruasnya berbeda.
  function ukuranRantaiV80(titik){
    const n=titik.length,jarak=new Array(n).fill(0);
    for(let i=1;i<n;i++)jarak[i]=jarak[i-1]+titik[i].distanceTo(titik[i-1]);
    const total=jarak[n-1];
    return total>1e-6?jarak.map(d=>d/total):jarak.map((_,i)=>i/Math.max(1,n-1));
  }

  function retargetV80(akar,lib,klip){
    const sumber=(lib.sources||[])[klip.source]||{};
    const bindSrc=sumber.bind||{};
    const bindTgt=bindDuniaTujuan(akar);
    const total=Object.keys(klip.world||{}).length;
    if(!bindTgt.size)return{clip:null,cocok:0,total:total,alasan:'model belum punya tulang'};
    const cocok=Object.keys(klip.world).filter(n=>bindTgt.has(n)&&bindSrc[n]);
    if(!cocok.length)return{clip:null,cocok:0,total:total,alasan:'tidak ada nama tulang yang cocok'};

    // Pembagian rantai hanya dinyalakan kalau ada ruas rantai rig tujuan yang
    // tidak dianimasikan sumber. Rantai yang sudah sepadan dibiarkan lewat jalur
    // nama langsung, supaya hasil yang sudah benar tidak berubah.
    let bagi=null;
    const atasTgt=puncakRantaiV80([...bindTgt.keys()]);
    const atasSrc=puncakRantaiV80(Object.keys(klip.world));
    if(atasTgt&&atasSrc){
      const rT=potongPangkalV80(rantaiTujuanV80(bindTgt,atasTgt),n=>!!klip.world[n]);
      const rS=rantaiSumberV80(bindSrc,atasSrc,rT[0]);
      if(rT.length>1&&rS.length>1&&rS[0]===rT[0]&&rT.some(n=>!klip.world[n])){
        bagi={tujuan:rT,sumber:rS,
              uT:ukuranRantaiV80(rT.map(n=>bindTgt.get(n).pos)),
              uS:ukuranRantaiV80(rS.map(n=>new THREE.Vector3().fromArray(bindSrc[n].pos))),
              set:new Set(rT)};
      }
    }

    const urut=urutIndukDulu(bindTgt),F=klip.frames,dur=klip.duration;
    const waktu=new Float32Array(F);
    for(let f=0;f<F;f++)waktu[f]=(f/(F-1))*dur;
    const ditulis=bagi?[...new Set(cocok.concat(bagi.tujuan))]:cocok;
    const nilai={};for(const n of ditulis)nilai[n]=new Float32Array(F*4);
    const duniaTgt=new Map(),setCocok=new Set(cocok);
    const qs=new THREE.Quaternion(),qb=new THREE.Quaternion(),qd=new THREE.Quaternion(),ql=new THREE.Quaternion();
    const selisihSumber=(n,f)=>{
      const w=klip.world[n];
      qs.set(w[f*4],w[f*4+1],w[f*4+2],w[f*4+3]);
      const bq=bindSrc[n].quat;qb.set(bq[0],bq[1],bq[2],bq[3]);
      return qs.clone().multiply(qb.invert());
    };

    for(let f=0;f<F;f++){
      let seri=null;
      if(bagi)seri=bagi.sumber.map(n=>selisihSumber(n,f));
      const padaU=u=>{
        const uS=bagi.uS;
        let i=0;while(i<uS.length-2&&uS[i+1]<u)i++;
        const a=uS[i],b=uS[i+1];
        const t=(b-a)>1e-6?Math.max(0,Math.min(1,(u-a)/(b-a))):0;
        return seri[i].clone().slerp(seri[i+1],t);
      };
      for(const n of urut){
        const bt=bindTgt.get(n);
        if(bagi&&bagi.set.has(n))duniaTgt.set(n,padaU(bagi.uT[bagi.tujuan.indexOf(n)]).multiply(bt.quat));
        else if(setCocok.has(n)){qd.copy(selisihSumber(n,f));duniaTgt.set(n,qd.clone().multiply(bt.quat))}
        else duniaTgt.set(n,bt.quat.clone());
      }
      for(const n of ditulis){
        const bone=bindTgt.get(n).bone,pr=bone.parent;
        const wp=(pr&&pr.isBone&&duniaTgt.has(pr.name))?duniaTgt.get(pr.name):null;
        ql.copy(duniaTgt.get(n));
        if(wp)ql.premultiply(wp.clone().invert());
        const a=nilai[n];a[f*4]=ql.x;a[f*4+1]=ql.y;a[f*4+2]=ql.z;a[f*4+3]=ql.w;
      }
    }
    const tracks=[];
    for(const n of ditulis)tracks.push(new THREE.QuaternionKeyframeTrack(n+'.quaternion',waktu,nilai[n]));

    // Gerak badan: hanya tulang akar yang diberi posisi, diskalakan menurut
    // tinggi model tujuan supaya langkahnya sepadan dengan ukuran badannya.
    let skala=1;
    if(klip.root&&bindTgt.has(klip.root)&&bindSrc[klip.root]&&klip.rootPos&&klip.rootPos.length===F*3){
      const hSrc=sumber.height||0,hTgt=tinggiObjek(akar);
      if(hSrc>1e-3&&hTgt>1e-3)skala=hTgt/hSrc;
      const bt=bindTgt.get(klip.root),bone=bt.bone,bp=bindSrc[klip.root].pos;
      // Posisi bind LOKAL dihitung dari posisi bind dunia lewat induknya, bukan
      // dibaca dari bone.position - pada model beranimasi nilai itu adalah
      // bingkai gerak yang sedang tampil, bukan pose bind.
      const indukM=new THREE.Matrix4();
      if(bone.parent){bone.parent.updateMatrixWorld(true);indukM.copy(bone.parent.matrixWorld).invert()}
      const lokalBind=bt.pos.clone().applyMatrix4(indukM);
      const indukQ=new THREE.Quaternion();
      if(bone.parent)bone.parent.getWorldQuaternion(indukQ).invert();
      const geser=new THREE.Vector3(),pos=new Float32Array(F*3);
      for(let f=0;f<F;f++){
        geser.set(klip.rootPos[f*3]-bp[0],klip.rootPos[f*3+1]-bp[1],klip.rootPos[f*3+2]-bp[2])
             .multiplyScalar(skala).applyQuaternion(indukQ);
        pos[f*3]=lokalBind.x+geser.x;pos[f*3+1]=lokalBind.y+geser.y;pos[f*3+2]=lokalBind.z+geser.z;
      }
      tracks.push(new THREE.VectorKeyframeTrack(klip.root+'.position',waktu,pos));
    }
    return{clip:new THREE.AnimationClip(klip.name,dur,tracks),cocok:cocok.length,total:total,skala:skala,
           rantai:bagi?{sumber:bagi.sumber.length,tujuan:bagi.tujuan.length,pangkal:bagi.tujuan[0]}:null};
  }
"""

s = s[:i] + baru + s[j:]

# Titik panggil dan catatan konsol mengikuti fungsi baru.
lama_panggil = "    try{hasil=retargetV79(root,S.lib,klip)}"
if lama_panggil not in s:
    raise SystemExit('titik panggil retargetV79 tidak ditemukan')
s = s.replace(lama_panggil, "    try{hasil=retargetV80(root,S.lib,klip)}", 1)

lama_log = ("    console.log('ANIM_PORTAL_V79: \"'+hasil.clip.name+'\" diterapkan, '+hasil.cocok+'/'"
            "+hasil.total+' tulang cocok, skala '+hasil.skala.toFixed(3));")
if lama_log not in s:
    raise SystemExit('baris catatan konsol v79 tidak ditemukan')
baru_log = ("    console.log('ANIM_PORTAL_V79: \"'+hasil.clip.name+'\" diterapkan, '+hasil.cocok+'/'"
            "+hasil.total+' tulang cocok, skala '+hasil.skala.toFixed(3)+"
            "(hasil.rantai?', ANIM_CHAIN_RETARGET_V80 membagi rantai '+hasil.rantai.sumber+' sendi -> '"
            "+hasil.rantai.tujuan+' sendi dari '+hasil.rantai.pangkal:', rantai aksial sepadan'));")
s = s.replace(lama_log, baru_log, 1)

lama_simpan = "S.terakhir={nama:hasil.clip.name,cocok:hasil.cocok,total:hasil.total,skala:+hasil.skala.toFixed(4)};"
if lama_simpan not in s:
    raise SystemExit('penyimpanan hasil terakhir tidak ditemukan')
s = s.replace(lama_simpan,
              "S.terakhir={nama:hasil.clip.name,cocok:hasil.cocok,total:hasil.total,"
              "skala:+hasil.skala.toFixed(4),rantai:hasil.rantai||null};", 1)

if 'retargetV79' in s:
    raise SystemExit('masih ada sisa retargetV79 - penggantian tidak utuh')

p.write_text(s, encoding='utf-8')
print('ANIM_CHAIN_RETARGET_V80 applied: tekukan dibagi menurut posisi relatif sendi di rantai aksial')
