from pathlib import Path

# BOBOT JARI, TWIST, DAN RAHANG - FINGER_WEIGHTS_V74
#
# Di mode "Ganti rig", rebuildRigKeepWeightsV57 memetakan bobot lama ke tulang
# baru lewat nameOf(), yang menelusuri ke ATAS sampai menemukan tulang yang
# punya padanan peran. Peran hanya dinilai untuk sendi inti - mapCoreBonesV54
# sengaja membuang jari, twist, dan rahang dari penilaian peran. Akibatnya
# bobot jari terlipat ke telapak, bobot twist ke tulang induknya, dan bobot
# rahang ke kepala.
#
# Terukur sebelum perbaikan pada SK_Mannequin: 22 tulang menerima bobot dari
# 61. Sisa 39 - 30 ruas jari, 8 twist, 1 rahang - ada di skeleton tapi tidak
# menggerakkan satu vertex pun. Tulang tanpa bobot hanya hiasan: bisa diputar,
# tapi mesh tidak ikut, sehingga jari tidak bisa dianimasikan.
#
# Perbaikannya menambah padanan langsung untuk ketiga kelompok itu, dipasang
# ke coreName sebelum nameOf dipakai. Karena nameOf berhenti pada padanan
# pertama yang ditemukan saat menelusuri ke atas, tulang jari kini berhenti
# pada dirinya sendiri, bukan terus naik ke telapak.
#
# Cara mencocokkan, mengikuti pola yang sudah dipakai di tempat lain:
#   - Jari dicari DI DALAM keturunan tulang telapak (bukan disapu global),
#     memakai jariDalamTanganV73 yang sudah membuang __dupV55 dan metacarpal.
#   - Sisi ditentukan dari posisi X sebenarnya, bukan huruf pada nama, sama
#     seperti pemasangan jangkar v70 dan deteksi marker v72.
#   - Twist dicari di dalam keturunan tulang anggota badan yang bersangkutan.
#   - Sasaran di rig baru dicari lewat pola nama pada struktur acuan, bukan
#     daftar nama mati, supaya berganti FBX acuan tidak memutus pemetaan.
# Padanan hanya dipasang bila tulang sasarannya memang ada di rig baru.
#
# Hanya menyentuh animation.html.

p = Path('app/src/main/assets/animation.html')
if not p.exists(): raise SystemExit('animation.html must exist')
s = p.read_text(encoding='utf-8')

if 'FINGER_WEIGHTS_V74' in s:
    print('Finger weights v74 already applied'); raise SystemExit(0)
if 'FINGER_DETECT_FIX_V73' not in s: raise SystemExit('finger detect fix v73 must run first')
if 'function refRolesV70' not in s: raise SystemExit('refRolesV70 tidak ada')
if "window.__OBJECT_MACHINE__='animation';" not in s: raise SystemExit('bukan dokumen mesin Animation')

anchor = "    const nameOf=b=>{let n=b;while(n&&n.isBone){if(coreName.has(n))return coreName.get(n);n=n.parent}return RR.hips};"
if anchor not in s: raise SystemExit('nameOf pada rebuildRigKeepWeightsV57 tidak ditemukan')

extra = r'''    // FINGER_WEIGHTS_V74
    (function(){
      const ref=S.refV70;
      if(!ref||!Array.isArray(ref.bones))return;
      const punya=new Set(ref.bones.map(b=>b.name));
      const unitX={}; for(const b of ref.bones) unitX[b.name]=b.unit?b.unit[0]:0;
      const W=b=>b.getWorldPosition(new THREE.Vector3());
      // Cari nama tulang acuan yang cocok pola DAN berada di sisi yang diminta.
      // sisi: +1 untuk X positif, -1 untuk X negatif.
      const cariRef=(pola,sisi)=>{
        let pilih=null;
        for(const nm of punya){
          if(!pola.test(nm))continue;
          if(sisi===0){pilih=nm;break}
          if(Math.sign(unitX[nm]||0)===sisi){pilih=nm;break}
        }
        return pilih;
      };
      const pasang=(tulangLama,namaBaru)=>{
        if(!tulangLama||!namaBaru||!punya.has(namaBaru))return 0;
        if(coreName.has(tulangLama))return 0;
        coreName.set(tulangLama,namaBaru);return 1;
      };
      let n=0;

      // JARI. Sisi ditentukan dari letak telapak, bukan huruf pada nama.
      const sdH=map.sided&&map.sided.hand;
      if(sdH&&sdH.L&&sdH.R){
        const a=W(sdH.L),b=W(sdH.R);
        const pasangan=[[(a.x<=b.x)?sdH.L:sdH.R,-1],[(a.x<=b.x)?sdH.R:sdH.L,+1]];
        for(const [hb,sisi] of pasangan){
          const per=jariDalamTanganV73(hb);
          for(const jari in per){
            per[jari].forEach((tulang,i)=>{
              const pola=new RegExp('^'+jari+'[^0-9]*0?'+(i+1)+'(?![0-9])','i');
              n+=pasang(tulang,cariRef(pola,sisi));
            });
          }
        }
      }

      // TWIST. Dicari di dalam keturunan tulang anggota badan yang bersangkutan.
      const twistPeran=[['upperarm','upperarm'],['forearm','lowerarm'],['thigh','thigh'],['calf','calf']];
      for(const [peran,akarNama] of twistPeran){
        const sd=map.sided&&map.sided[peran];
        if(!sd||!sd.L||!sd.R)continue;
        const a=W(sd.L),b=W(sd.R);
        const pasangan=[[(a.x<=b.x)?sd.L:sd.R,-1],[(a.x<=b.x)?sd.R:sd.L,+1]];
        for(const [limb,sisi] of pasangan){
          const kandidat=[];
          limb.traverse(x=>{ if(!x.isBone||x===limb)return;
            if(/dupv55/i.test(x.name))return;
            if(/twist/i.test(x.name))kandidat.push(x); });
          const dalam=x=>{let d=0,q=x;while(q&&q!==limb){d++;q=q.parent}return d};
          kandidat.sort((p2,q2)=>dalam(p2)-dalam(q2));
          kandidat.forEach((tulang,i)=>{
            const pola=new RegExp('^'+akarNama+'[_]?twist[^0-9]*0?'+(i+1)+'(?![0-9])','i');
            n+=pasang(tulang,cariRef(pola,sisi));
          });
        }
      }

      // RAHANG. Satu tulang, tanpa sisi.
      if(map.head){
        let rahang=null;
        map.head.traverse(x=>{ if(rahang||!x.isBone||x===map.head)return;
          if(/dupv55/i.test(x.name))return;
          if(/jaw/i.test(x.name))rahang=x; });
        n+=pasang(rahang,cariRef(/jaw/i,0));
      }

      if(n)console.log('FINGER_WEIGHTS_V74: '+n+' tulang tambahan dipetakan (jari, twist, rahang)');
    })();
'''

s = s.replace(anchor, extra + anchor, 1)
p.write_text(s, encoding='utf-8')
print('Finger weights v74 applied: jari, twist, dan rahang ikut menerima bobot')
