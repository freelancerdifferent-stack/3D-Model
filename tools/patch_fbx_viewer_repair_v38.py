from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'FBX_VIEWER_REPAIR_V38' in s:
    print('FBX viewer repair v38 already applied'); raise SystemExit(0)
if 'loadFbxWithAssimp' not in s:
    raise SystemExit('FBX Assimp patch must run first')

# MainActivity used to inject this repair into index.html at load time, but its FBX
# anchor string disappeared when the Assimp patch rewrote the import flow, so the
# helper was injected without a single caller — and document-portal navigation loads
# assets directly, skipping the Java injection entirely. Bake the same repair into
# the build instead: every machine document (index/create/auto) then carries it
# itself, and the Java injection skips because the function already exists.
marker='function registerModel(obj,name,animations=[]){'
if marker not in s: raise SystemExit('registerModel marker missing')
helper=r'''// FBX_VIEWER_REPAIR_V38 — formerly injected by MainActivity.loadEditorHtml
function prepareFBXForViewer(obj){
  obj.updateMatrixWorld(true);
  obj.traverse(o=>{
    if(o.isSkinnedMesh){
      o.frustumCulled=false;
      try{o.normalizeSkinWeights?.();}catch(e){}
      if(o.skeleton){try{o.skeleton.pose();o.skeleton.update();o.bindMode='attached';if(o.bindMatrix)o.bind(o.skeleton,o.bindMatrix);}catch(e){console.warn('FBX skeleton repair',e);}}
      o.updateMatrixWorld(true);
    }
  });
  obj.updateMatrixWorld(true);
  return obj;
}

'''
s=s.replace(marker,helper+marker,1)

old_fallback='''        const obj=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));
        registerModel(obj,f.name,obj.animations||[]);
        msg('FBX dimuat via fallback');'''
if old_fallback not in s: raise SystemExit('FBXLoader fallback marker missing')
new_fallback='''        const obj=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));
        prepareFBXForViewer(obj);
        registerModel(obj,f.name,obj.animations||[]);
        requestAnimationFrame(()=>requestAnimationFrame(()=>{
          if(root===obj){prepareFBXForViewer(obj);centerAndFit(obj);updateTransformFields();}
        }));
        msg('FBX dimuat via fallback');'''
s=s.replace(old_fallback,new_fallback,1)

p.write_text(s,encoding='utf-8')
print('FBX viewer repair v38 baked into the build for every machine document')
