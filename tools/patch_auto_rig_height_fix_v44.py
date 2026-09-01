from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html missing')
s=p.read_text(encoding='utf-8')
if 'AUTO_RIG_HEIGHT_FIX_V44' in s:
    print('Auto Rig height fix v44 already applied'); raise SystemExit(0)
if 'AUTO_RIG_FIX_V43' not in s: raise SystemExit('Auto Rig fix v43 must run first')

# V42 recalculated the current bounding-box height on every slider event and then
# multiplied the already-scaled root again. On Android this compounds scale rapidly.
# V44 uses one fixed baseline for the whole Step 2 interaction.
old="""    const deg=[THREE.MathUtils.radToDeg(root.rotation.x),THREE.MathUtils.radToDeg(root.rotation.y),THREE.MathUtils.radToDeg(root.rotation.z)];
    const currentBox=modelBox(), h=Math.max(.001,currentBox.max.y-currentBox.min.y);
    panel.innerHTML="""
new="""    // AUTO_RIG_HEIGHT_FIX_V44
    const deg=[THREE.MathUtils.radToDeg(root.rotation.x),THREE.MathUtils.radToDeg(root.rotation.y),THREE.MathUtils.radToDeg(root.rotation.z)];
    const currentBox=modelBox(), h=Math.max(.001,currentBox.max.y-currentBox.min.y);
    // Capture a stable reference once per Step 2 render. Height becomes an absolute
    // target relative to this baseline instead of multiplying the previous scale.
    const heightBase={height:h,scale:root.scale.clone()};
    panel.innerHTML="""
if old not in s: raise SystemExit('height baseline anchor missing')
s=s.replace(old,new,1)

old_handler="""    const hr=panel.querySelector('#arv42Height'),hn=panel.querySelector('#arv42HeightNum');hr.oninput=()=>{const b=modelBox(),ch=Math.max(.001,b.max.y-b.min.y),f=(+hr.value)/ch;root.scale.multiplyScalar(f);root.updateMatrixWorld(true);hn.value=(+hr.value).toFixed(2)};
"""
new_handler="""    const hr=panel.querySelector('#arv42Height'),hn=panel.querySelector('#arv42HeightNum');
    const applyHeight=raw=>{
      const target=Math.max(.05,Number(raw)||heightBase.height);
      const f=target/heightBase.height;
      root.scale.copy(heightBase.scale).multiplyScalar(f);
      root.updateMatrixWorld(true);
      hn.value=target.toFixed(2);
    };
    hr.oninput=()=>applyHeight(hr.value);
    // Numeric field is now a real input too; commit on change/blur without compounding.
    hn.onchange=()=>{let v=Math.max(.05,Number(hn.value)||heightBase.height);v=Math.min(20,v);hn.value=v.toFixed(2);hr.value=String(Math.min(Number(hr.max),Math.max(Number(hr.min),v)));applyHeight(v)};
"""
if old_handler not in s: raise SystemExit('height handler anchor missing')
s=s.replace(old_handler,new_handler,1)

p.write_text(s,encoding='utf-8')
print('Auto Rig height fix v44 applied: absolute baseline scaling, stable slider and numeric input')
