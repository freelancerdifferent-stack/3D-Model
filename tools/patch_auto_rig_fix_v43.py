from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html missing')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_FIX_V43' in s:
    print('Auto Rig fix v43 already applied'); raise SystemExit(0)
if 'AUTO_RIG_MACHINE_V42' not in s: raise SystemExit('Auto Rig v42 must run first')

# Keep the character visible throughout the wizard, even if Object/Skeleton UI had hidden meshes.
anchor="  function captureOriginal(){if(!root)return;S.original={position:root.position.clone(),quaternion:root.quaternion.clone(),scale:root.scale.clone()}}\n"
if anchor not in s: raise SystemExit('captureOriginal anchor missing')
replacement=anchor+"""  // AUTO_RIG_FIX_V43\n  function forceRigModelVisible(){\n    if(!root)return;\n    root.visible=true;\n    root.traverse(o=>{if(o.isMesh&&!o.isSkeletonHelper)o.visible=true});\n    root.updateMatrixWorld(true);\n  }\n"""
s=s.replace(anchor,replacement,1)

open_old="    S.open=true;S.step=1;document.body.classList.add('auto-rig-v42');shell.style.display='block';go('editorScreen');renderStep();\n"
open_new="    S.open=true;S.step=1;forceRigModelVisible();document.body.classList.add('auto-rig-v42');shell.style.display='block';go('editorScreen');renderStep();\n"
if open_old not in s: raise SystemExit('openRig anchor missing')
s=s.replace(open_old,open_new,1)

# Reassert visibility whenever a wizard step renders, especially marker placement (Step 3).
step_old="  function renderStep(){\n    stepChip.textContent='Auto Rig • Step '+S.step+'/5';markerLayer.style.display=S.step===3?'block':'none';\n"
step_new="  function renderStep(){\n    forceRigModelVisible();\n    stepChip.textContent='Auto Rig • Step '+S.step+'/5';markerLayer.style.display=S.step===3?'block':'none';\n"
if step_old not in s: raise SystemExit('renderStep anchor missing')
s=s.replace(step_old,step_new,1)

# Replace skin conversion with a safer bind path that preserves world transforms.
start=s.find('  async function skinGeometry(){')
end=s.find('\n\n  async function renderProcessingStep(){',start)
if start<0 or end<0: raise SystemExit('skinGeometry block missing')
new_skin=r'''  async function skinGeometry(){
    if(!S.skeleton)return 0;
    forceRigModelVisible();
    root.updateMatrixWorld(true);
    S.skeleton.calculateInverses();
    const bonePts=S.bones.map(b=>b.getWorldPosition(new THREE.Vector3()));
    let done=0;
    const targets=[];
    root.traverse(o=>{if(o.isMesh&&!o.isSkinnedMesh&&!o.isSkeletonHelper&&o.geometry?.attributes?.position)targets.push(o)});
    for(const mesh of targets){
      mesh.updateMatrixWorld(true);
      const oldWorld=mesh.matrixWorld.clone();
      const g=mesh.geometry.clone(),pos=g.attributes.position,count=pos.count;
      const idx=new Uint16Array(count*4),wei=new Float32Array(count*4),v=new THREE.Vector3();
      for(let i=0;i<count;i++){
        v.fromBufferAttribute(pos,i).applyMatrix4(oldWorld);
        const cand=bonePts.map((p,bi)=>({bi,d:v.distanceToSquared(p)})).sort((a,b)=>a.d-b.d).slice(0,4);
        let sum=0;
        for(let j=0;j<4;j++){const w=1/(Math.sqrt(cand[j].d)+1e-4);wei[i*4+j]=w;idx[i*4+j]=cand[j].bi;sum+=w}
        for(let j=0;j<4;j++)wei[i*4+j]/=sum;
        if((i%20000)===0)await new Promise(requestAnimationFrame);
      }
      g.setAttribute('skinIndex',new THREE.Uint16BufferAttribute(idx,4));
      g.setAttribute('skinWeight',new THREE.Float32BufferAttribute(wei,4));
      const sk=new THREE.SkinnedMesh(g,mesh.material);
      sk.name=mesh.name;sk.position.copy(mesh.position);sk.quaternion.copy(mesh.quaternion);sk.scale.copy(mesh.scale);
      sk.visible=true;sk.castShadow=mesh.castShadow;sk.receiveShadow=mesh.receiveShadow;
      const parent=mesh.parent,at=parent.children.indexOf(mesh);
      parent.add(sk);
      if(at>=0){parent.children.splice(parent.children.indexOf(sk),1);parent.children.splice(at+1,0,sk)}
      sk.updateMatrixWorld(true);
      sk.bind(S.skeleton,oldWorld);
      sk.normalizeSkinWeights();
      // Only remove the source mesh after the skinned replacement is fully bound.
      parent.remove(mesh);
      sk.visible=true;
      done++;
    }
    S.skinned=done;
    forceRigModelVisible();
    return done;
  }'''
s=s[:start]+new_skin+s[end:]

# Three r180 SkeletonHelper has no .update(); updateMatrixWorld is the supported refresh path.
s=s.replace("if(S.helper)S.helper.update();","if(S.helper)S.helper.updateMatrixWorld(true);",1)

# Final safety: force model visible after processing before showing the result screen.
proc_old="set(100);await new Promise(r=>setTimeout(r,180));step(5)"
proc_new="forceRigModelVisible();set(100);await new Promise(r=>setTimeout(r,180));step(5)"
if proc_old not in s: raise SystemExit('processing completion anchor missing')
s=s.replace(proc_old,proc_new,1)

p.write_text(s,encoding='utf-8')
print('Auto Rig fix v43 applied: model remains visible, safe bind path, SkeletonHelper refresh fixed')
