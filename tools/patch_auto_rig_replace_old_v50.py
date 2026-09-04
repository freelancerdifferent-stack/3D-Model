from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_REPLACE_OLD_V50' in s:
    print('Auto Rig replace-old v50 already applied'); raise SystemExit(0)
if 'AUTO_RIG_MACHINE_V42' not in s: raise SystemExit('Auto Rig machine v42 must run first')

# Model yang sudah ter-rig: rig lamanya DIHAPUS dan digantikan hasil Auto Rig.
# Kuncinya pose-baking — geometry mentah SkinnedMesh sering berada di skala/posisi
# berbeda dari yang tampil (penempatan dibawa tulang+bindMatrix, khas FBX cm).
# Setiap vertex dibaca lewat getVertexPosition (pose tampil, termasuk frame animasi),
# dikonversi ke lokal root, ditulis ke mesh polos ber-transform identitas; tanpa ini
# mesh akan "berpisah" dari kerangka barunya.
css=r'''
/* AUTO_RIG_REPLACE_OLD_V50 */
.arv42-warn50{margin:8px 0;padding:8px 10px;border:1px solid #7a6237;background:#332711;color:#ffd57a;border-radius:9px;font-size:12px;line-height:1.45}
'''
if '</style>' not in s: raise SystemExit('style end missing')
s=s.replace('</style>',css+'\n</style>',1)

# 1) fungsi pelepas rig lama, ditanam di dalam closure wizard
anchor='  async function renderProcessingStep(){'
if anchor not in s: raise SystemExit('renderProcessingStep anchor missing')
strip_js=r'''  // AUTO_RIG_REPLACE_OLD_V50
  function hasOldRigV50(){let n=0;if(root)root.traverse(o=>{if(o.isBone)n++});return n>0}
  function stripOldRigV50(){
    if(!root||!hasOldRigV50())return 0;
    root.updateMatrixWorld(true);
    const boneRoots=[];root.traverse(o=>{if(o.isBone&&(!o.parent||!o.parent.isBone))boneRoots.push(o)});
    const skinned=[];root.traverse(o=>{if(o.isSkinnedMesh)skinned.push(o)});
    for(const m of skinned){
      m.updateMatrixWorld(true);
      const g=m.geometry.clone();
      g.deleteAttribute('skinIndex');g.deleteAttribute('skinWeight');
      const pos=g.getAttribute('position'),v=new THREE.Vector3();
      for(let i=0;i<pos.count;i++){
        m.getVertexPosition(i,v);v.applyMatrix4(m.matrixWorld);root.worldToLocal(v);
        pos.setXYZ(i,v.x,v.y,v.z);
      }
      pos.needsUpdate=true;g.computeVertexNormals();g.computeBoundingBox();g.computeBoundingSphere();
      const nm=new THREE.Mesh(g,m.material);
      nm.name=m.name;nm.castShadow=m.castShadow;nm.receiveShadow=m.receiveShadow;nm.visible=true;
      root.add(nm);
      const mi=(typeof meshList!=='undefined')?meshList.indexOf(m):-1;
      if(mi>=0)meshList[mi]=nm;
      if(m.parent)m.parent.remove(m);
    }
    for(const b of boneRoots){if(b.parent)b.parent.remove(b)}
    // Pemutar animasi lama ikut dibersihkan: klip lama menarget tulang yang
    // baru saja dihapus, dan cache binding mixer akan mengarahkan track baru
    // bernama sama ke tulang mati itu (animasi jalan di "tulang hantu").
    try{if(typeof mixer!=='undefined'&&mixer){mixer.stopAllAction();mixer.uncacheRoot(mixer.getRoot())}}catch(_){ }
    mixer=null;clips=[];activeAction=null;playing=false;activeClipIndex=0;
    const selV50=document.getElementById('animSelect');
    if(selV50)selV50.innerHTML='<option value="">No Animation</option>';
    const cntV50=document.getElementById('animClipCount');if(cntV50)cntV50.textContent='0';
    const durV50=document.getElementById('durationText');if(durV50)durV50.textContent='0s';
    const pbV50=document.getElementById('playBtn');if(pbV50)pbV50.textContent='▶';
    root.updateMatrixWorld(true);
    window.__autoRigReplaceV50={stripped:skinned.length,bonesRootsRemoved:boneRoots.length};
    return skinned.length;
  }
  window.__autoRigV50Debug={hasOldRig:hasOldRigV50,root:()=>root,meshList:()=>((typeof meshList!=='undefined')?meshList:null)};
'''
s=s.replace(anchor,strip_js+anchor,1)

# 2) panggil pelepas sebelum skeleton baru dibangun
old_run='try{set(12);await new Promise(r=>setTimeout(r,80));generateSkeleton();'
if old_run not in s: raise SystemExit('processing chain anchor missing')
s=s.replace(old_run,'try{set(12);await new Promise(r=>setTimeout(r,80));stripOldRigV50();set(24);generateSkeleton();',1)

# 3) peringatan di layar 1 saat model sudah ber-rig
old_p1="panel.innerHTML='<h3>Rig Model</h3><p>Posisikan"
if old_p1 not in s: raise SystemExit('step1 panel anchor missing')
s=s.replace(old_p1,"panel.innerHTML='<h3>Rig Model</h3>'+(hasOldRigV50()?'<div class=\"arv42-warn50\">⚠ Model ini sudah punya rig. Rig lama akan DIHAPUS dan digantikan hasil Auto Rig.</div>':'')+'<p>Posisikan",1)

# 4) meshList ikut diperbarui saat mesh polos diganti SkinnedMesh baru (stale-ref fix)
old_swap='''      parent.add(sk);
      if(at>=0){parent.children.splice(parent.children.indexOf(sk),1);parent.children.splice(at+1,0,sk)}'''
if old_swap not in s: raise SystemExit('skinGeometry swap anchor missing')
s=s.replace(old_swap,old_swap+'''
      const li50=(typeof meshList!=='undefined')?meshList.indexOf(mesh):-1;if(li50>=0)meshList[li50]=sk;''',1)

p.write_text(s,encoding='utf-8')
print('Auto Rig replace-old v50: rig lama dilepas (pose-baked) lalu digantikan rig baru')
