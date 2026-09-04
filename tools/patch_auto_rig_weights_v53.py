from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_WEIGHTS_V53' in s:
    print('Auto Rig weights v53 already applied'); raise SystemExit(0)
if 'AUTO_RIG_BONE_TIDY_V51' not in s: raise SystemExit('v51 must run first')

# Kualitas skin weights: metode lama mengikat tiap vertex ke 4 TITIK sendi
# terdekat dengan jarak lurus - vertex paha kiri bisa terikat tulang paha
# kanan (jarak menembus tubuh), dan vertex tengah betis jauh dari kedua
# sendinya sehingga bobotnya kabur. Deformasi jadi sobek di selangkangan,
# ketiak dan pinggul. v53:
#   - jarak dihitung ke RUAS tulang (segmen sendi->anak, seperti kapsul)
#   - pagar kiri/kanan: tulang Left*/Right* tidak menerima vertex dari sisi
#     tubuh yang berlawanan (di luar pita toleransi 6% lebar model);
#     sisi ditentukan dari posisi tulangnya sendiri, bukan asumsi arah hadap
#   - falloff 1/d^2 sehingga tiap vertex didominasi tulang yang benar
old_a='''    const bonePts=S.bones.map(b=>b.getWorldPosition(new THREE.Vector3()));
    let done=0;'''
new_a='''    // AUTO_RIG_WEIGHTS_V53: bobot kapsul per ruas tulang + pagar kiri/kanan
    const bonePts=S.bones.map(b=>b.getWorldPosition(new THREE.Vector3()));
    const boneSegs=S.bones.map((b,bi)=>{
      const segs=[];const a=bonePts[bi];
      for(const c of b.children){if(!c.isBone)continue;const ci=S.bones.indexOf(c);if(ci>=0)segs.push([a,bonePts[ci]])}
      if(!segs.length)segs.push([a,a]);
      return segs;
    });
    const isSideV53=S.bones.map(b=>b.name.startsWith('Left')||b.name.startsWith('Right'));
    const cxV53=bonePts[0].x;
    const bbV53=new THREE.Box3().setFromObject(root);
    const tolV53=Math.max((bbV53.max.x-bbV53.min.x)*.06,1e-4);
    const segTV53=new THREE.Vector3();
    const distSegV53=(pv,a,b2)=>{segTV53.subVectors(b2,a);const L2=segTV53.lengthSq();
      if(L2<1e-12)return pv.distanceTo(a);
      let t=(pv.x-a.x)*segTV53.x+(pv.y-a.y)*segTV53.y+(pv.z-a.z)*segTV53.z;t=Math.max(0,Math.min(1,t/L2));
      const dx=a.x+segTV53.x*t-pv.x,dy=a.y+segTV53.y*t-pv.y,dz=a.z+segTV53.z*t-pv.z;
      return Math.sqrt(dx*dx+dy*dy+dz*dz)};
    let done=0;'''
if old_a not in s: raise SystemExit('bonePts anchor missing')
s=s.replace(old_a,new_a,1)

old_b='''        const cand=bonePts.map((p,bi)=>({bi,d:v.distanceToSquared(p)})).sort((a,b)=>a.d-b.d).slice(0,4);
        let sum=0;
        for(let j=0;j<4;j++){const w=1/(Math.sqrt(cand[j].d)+1e-4);wei[i*4+j]=w;idx[i*4+j]=cand[j].bi;sum+=w}
        for(let j=0;j<4;j++)wei[i*4+j]/=sum;'''
new_b='''        const vsV53=v.x-cxV53;
        const cand=[];
        for(let bi=0;bi<S.bones.length;bi++){
          if(isSideV53[bi]){
            const bx=bonePts[bi].x-cxV53;
            if(Math.abs(vsV53)>tolV53&&Math.abs(bx)>tolV53&&((vsV53>0)!==(bx>0)))continue;
          }
          let d=Infinity;const ss=boneSegs[bi];
          for(let k=0;k<ss.length;k++){const dd=distSegV53(v,ss[k][0],ss[k][1]);if(dd<d)d=dd}
          cand.push({bi,d});
        }
        cand.sort((a,b)=>a.d-b.d);
        const nV53=Math.min(4,cand.length);
        let sum=0;
        for(let j=0;j<nV53;j++){const w=1/((cand[j].d+1e-4)*(cand[j].d+1e-4));wei[i*4+j]=w;idx[i*4+j]=cand[j].bi;sum+=w}
        for(let j=0;j<nV53;j++)wei[i*4+j]/=sum;'''
if old_b not in s: raise SystemExit('weight loop anchor missing')
s=s.replace(old_b,new_b,1)

p.write_text(s,encoding='utf-8')
print('Auto Rig weights v53: bobot kapsul ruas tulang + pagar kiri/kanan + falloff 1/d^2')
