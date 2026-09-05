from pathlib import Path

# MESIN MARKER AUTO RIG - AUTO_RIG_MARKER_MODES_V69
#
# Blok marker lama (initMarkers / markerDefs / projectMarkers / renderMarkerStep)
# DIGANTI UTUH oleh mesin marker baru. Bukan ditambal: potongan lama dipotong,
# kode baru yang berdiri sendiri dipasang di tempatnya.
#
# Dua mode, dipilih di Step 3:
#   cepat (15 titik) - 12 titik lama + puncak kepala + ujung kaki kiri/kanan
#   jari  (45 titik) - 15 di atas + 3 sendi x 5 jari x 2 tangan
#
# 12 kunci marker lama (chin, shoulderL/R, elbowL/R, wristL/R, groin, kneeL/R,
# ankleL/R) DIPERTAHANKAN apa adanya karena generateSkeleton() masih membacanya.
# Marker baru bersifat tambahan, sehingga Auto Rig yang ada tetap jalan.
#
# Hanya menyentuh animation.html.

p = Path('app/src/main/assets/animation.html')
if not p.exists(): raise SystemExit('animation.html must exist')
s = p.read_text(encoding='utf-8')

if 'AUTO_RIG_MARKER_MODES_V69' in s:
    print('Auto Rig marker modes v69 already applied'); raise SystemExit(0)
if 'AUTO_RIG_MACHINE_V42' not in s: raise SystemExit('Auto Rig machine v42 must run first')
if "window.__OBJECT_MACHINE__='animation';" not in s: raise SystemExit('bukan dokumen mesin Animation')

START = '  function initMarkers(){'
END = '  function localPoint(world){'
i = s.find(START)
j = s.find(END, i)
if i < 0 or j < 0: raise SystemExit('blok marker lama tidak ditemukan')
old = s[i:j]
for need in ['const markerDefs=', 'function projectMarkers()', 'function renderMarkerStep()']:
    if need not in old: raise SystemExit('blok marker lama tidak utuh: ' + need)

new = r'''  // AUTO_RIG_MARKER_MODES_V69 - mesin marker dua mode
  // Titik awal tiap marker hanyalah tebakan proporsi dari kotak batas model;
  // pengguna yang menentukan posisi sebenarnya dengan menggeser.
  const MK_FINGERS_V69 = [['thumb','Ib'],['index','Tj'],['middle','Tg'],['ring','Mn'],['pinky','Kl']];
  const MK_BODY_V69 = [
    ['headTop','HT','center','Tubuh'],
    ['chin','C','center','Tubuh'],
    ['shoulderL','SL','lr','Tubuh'],['shoulderR','SR','lr','Tubuh'],
    ['elbowL','EL','lr','Tubuh'],['elbowR','ER','lr','Tubuh'],
    ['wristL','WL','lr','Tubuh'],['wristR','WR','lr','Tubuh'],
    ['groin','G','center','Tubuh'],
    ['kneeL','KL','lr','Tubuh'],['kneeR','KR','lr','Tubuh'],
    ['ankleL','AL','lr','Tubuh'],['ankleR','AR','lr','Tubuh'],
    ['toeL','TL','lr','Tubuh'],['toeR','TR','lr','Tubuh'],
  ];
  function mkFingerDefsV69(){
    const out=[];
    for(const side of ['L','R']){
      const grp = side==='L' ? 'Tangan Kiri' : 'Tangan Kanan';
      for(const [f,tag] of MK_FINGERS_V69){
        for(let j=1;j<=3;j++) out.push([f+'0'+j+side, tag+j, 'fingerv69', grp]);
      }
    }
    return out;
  }
  const MK_FINGER_V69 = mkFingerDefsV69();
  function mkDefsV69(){
    return S.markerModeV69==='jari' ? MK_BODY_V69.concat(MK_FINGER_V69) : MK_BODY_V69;
  }
  function mkGroupsV69(){
    const seen=[]; for(const d of mkDefsV69()) if(!seen.includes(d[3])) seen.push(d[3]);
    return seen;
  }
  function mkActiveDefsV69(){
    const g=S.markerGroupV69;
    return mkDefsV69().filter(d=>!g||d[3]===g);
  }
  // Dekatkan kamera ke kelompok marker yang sedang dipilih.
  // Ini syarat pakai, bukan hiasan: pada jarak kamera bawaan, dua marker jari
  // bersebelahan hanya terpisah ~3.6 px sementara titiknya sendiri 17 px, jadi
  // saling menimpa dan tidak bisa digeser. Jarak dunianya sudah benar (3.1 unit
  // pada model setinggi 182.6 = 1.7% tinggi badan, seukuran jari sungguhan),
  // jadi yang perlu didekatkan kameranya - bukan jarinya yang direnggangkan.
  function mkFocusGroupV69(){
    const box=new THREE.Box3();
    for(const [k] of mkActiveDefsV69()){ if(S.markers[k]) box.expandByPoint(S.markers[k]); }
    if(box.isEmpty())return;
    const c=box.getCenter(new THREE.Vector3());
    const radius=Math.max(box.getSize(new THREE.Vector3()).length()*.5, S.size.y*.015);
    const dist=(radius/Math.tan(THREE.MathUtils.degToRad(camera.fov*.5)))*2.2;
    let dir=new THREE.Vector3().subVectors(camera.position,controls.target);
    if(dir.lengthSq()<1e-9)dir.set(0,0,1);
    dir.normalize();
    controls.target.copy(c);
    camera.position.copy(c).addScaledVector(dir,dist);
    camera.near=Math.max(.01,dist*.01);
    camera.far=Math.max(1000,dist*20);
    camera.updateProjectionMatrix();
    controls.update();
  }

  function initMarkers(){
    S.box=modelBox();S.size=S.box.getSize(new THREE.Vector3());S.center=S.box.getCenter(new THREE.Vector3());
    const b=S.box,c=S.center,w=S.size.x,h=S.size.y,z=c.z;
    const P=(x,y,zz)=>new THREE.Vector3(x,y,zz===undefined?z:zz);
    if(!S.markerModeV69)S.markerModeV69='cepat';
    S.markerGroupV69=S.markerGroupV69||'Tubuh';
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
    // Jari dijajarkan dari pergelangan mengikuti arah siku->pergelangan, lalu
    // dikipaskan TEGAK LURUS terhadap arah itu. Kipas tegak lurus dipilih bukan
    // sekadar rapi: mengipas pada sumbu depan-belakang membuat kelima jari
    // saling menimpa saat dilihat dari kamera depan sehingga tidak bisa digeser.
    // Murni titik awal; pengguna yang menentukan posisi sebenarnya.
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
          const q=wr.clone().addScaledVector(dir,seg*j).addScaledVector(perp,lateral);
          m[f+'0'+j+side]=q;
        }
      });
    }
    S.markers=m;
  }

  function projectMarkers(){
    if(!S.open||S.step!==3)return;
    const r=viewport.getBoundingClientRect();
    mkActiveDefsV69().forEach(([k])=>{
      const el=markerLayer.querySelector('[data-m="'+k+'"]');
      const p=S.markers[k]?.clone();
      if(!el||!p)return;
      p.project(camera);
      el.style.left=((p.x*.5+.5)*r.width)+'px';
      el.style.top=((-p.y*.5+.5)*r.height)+'px';
      el.style.display=(p.z<-1||p.z>1)?'none':'block';
    });
    requestAnimationFrame(projectMarkers);
  }

  function renderMarkerStep(){
    const defs=mkActiveDefsV69();
    const groups=mkGroupsV69();
    const modeBtn=(id,md,title,sub)=>'<button type="button" id="'+id+'" class="armk69-mode'+(S.markerModeV69===md?' sel':'')+'"><b>'+title+'</b><span>'+sub+'</span></button>';
    const chips=S.markerModeV69==='jari'
      ? '<div class="armk69-groups">'+groups.map(g=>'<button type="button" class="armk69-chip'+(S.markerGroupV69===g?' sel':'')+'" data-g="'+g+'">'+g+'</button>').join('')+'</div>'
      : '';
    panel.innerHTML='<h3>Place Markers</h3>'
      +'<div class="armk69-modes">'
      +modeBtn('armk69Cepat','cepat','Cepat','15 titik - tubuh saja')
      +modeBtn('armk69Jari','jari','Per Sendi Jari','45 titik - tubuh + 3 sendi tiap jari')
      +'</div>'
      +chips
      +'<p>Geser marker ke titik anatomi yang sesuai. Marker ini menjadi sumber utama pembentukan skeleton.</p>'
      +'<div class="arv42-marker-list">'+defs.map(([k])=>'<span>'+k+'</span>').join('')+'</div>'
      +'<div class="arv42-toggle"><span>Symmetry</span><button id="arv42Sym" class="'+(S.symmetry?'on':'')+'"></button></div>'
      +btns(true,true,'Confirm');
    markerLayer.innerHTML=defs.map(([k,t,c])=>'<div class="arv42-marker '+c+'" data-m="'+k+'">'+t+'</div>').join('');

    panel.querySelector('#arv42Sym').onclick=e=>{S.symmetry=!S.symmetry;e.currentTarget.classList.toggle('on',S.symmetry)};
    const setMode=md=>{S.markerModeV69=md;S.markerGroupV69='Tubuh';renderMarkerStep();mkFocusGroupV69()};
    panel.querySelector('#armk69Cepat').onclick=()=>setMode('cepat');
    panel.querySelector('#armk69Jari').onclick=()=>setMode('jari');
    panel.querySelectorAll('.armk69-chip').forEach(b=>b.onclick=()=>{S.markerGroupV69=b.dataset.g;renderMarkerStep();mkFocusGroupV69()});

    const plane=new THREE.Plane(),raycaster=new THREE.Raycaster(),pt=new THREE.Vector3(),ndc=new THREE.Vector2();
    function dragMarker(ev,key){
      const r=viewport.getBoundingClientRect();
      ndc.x=((ev.clientX-r.left)/r.width)*2-1;ndc.y=-((ev.clientY-r.top)/r.height)*2+1;
      raycaster.setFromCamera(ndc,camera);
      const n=new THREE.Vector3();camera.getWorldDirection(n);
      plane.setFromNormalAndCoplanarPoint(n,S.markers[key]);
      if(raycaster.ray.intersectPlane(plane,pt)){
        S.markers[key].copy(pt);
        if(S.symmetry&&/[LR]$/.test(key)){
          const other=key.slice(0,-1)+(key.endsWith('L')?'R':'L');
          if(S.markers[other]){S.markers[other].copy(pt);S.markers[other].x=2*S.center.x-pt.x}
        }
      }
    }
    markerLayer.querySelectorAll('.arv42-marker').forEach(el=>{
      let down=false;
      el.onpointerdown=e=>{down=true;controls.enabled=false;el.setPointerCapture?.(e.pointerId);e.preventDefault()};
      el.onpointermove=e=>{if(down)dragMarker(e,el.dataset.m)};
      const up=()=>{down=false;controls.enabled=true};
      el.onpointerup=up;el.onpointercancel=up;
    });
    requestAnimationFrame(projectMarkers);
    wireNav(()=>step(2),()=>step(4));
  }

'''

s = s[:i] + new + s[j:]

css = r'''
/* AUTO_RIG_MARKER_MODES_V69 */
.armk69-modes{display:grid;gap:7px;margin:0 0 10px}
.armk69-mode{text-align:left;border:1px solid #46552b;border-radius:11px;background:#171c15;color:#e9f0e2;padding:9px 11px}
.armk69-mode b{display:block;font-size:13px;margin-bottom:2px}
.armk69-mode span{display:block;font-size:11px;color:#a9b69c;line-height:1.35}
.armk69-mode.sel{border-color:#baff31;box-shadow:0 0 0 1px #baff3155 inset}
.armk69-mode.sel b{color:#baff31}
.armk69-groups{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 10px}
.armk69-chip{border:1px solid #35402b;border-radius:9px;background:#161a14;color:#c6cfbe;font-size:11px;padding:6px 10px}
.armk69-chip.sel{border-color:#baff31;color:#baff31;background:#1d2616}
.arv42-marker.fingerv69{width:17px;height:17px;margin:-8.5px 0 0 -8.5px;border-color:#7fd4ff;font-size:8px;line-height:13px}
'''
if '</style>' not in s: raise SystemExit('style end missing')
s = s.replace('</style>', css + '\n</style>', 1)

p.write_text(s, encoding='utf-8')
print('Auto Rig marker modes v69 applied: blok marker lama diganti mesin dua mode (15 / 45 titik)')
