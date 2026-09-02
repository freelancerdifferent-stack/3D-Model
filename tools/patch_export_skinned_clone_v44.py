from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'EXPORT_SKINNED_CLONE_V44' in s:
    print('Export skinned clone v44 already applied'); raise SystemExit(0)
if 'EXPORT_ALL_V13' not in s:
    raise SystemExit('Export All v13 must run first')

# Object3D.clone() copies a SkinnedMesh but leaves its skeleton pointing at the
# ORIGINAL bones, which are not part of the export scene. GLTFExporter then writes
# a skin whose joints reference nodes missing from the file, and any later import
# dies in GLTFLoader with "Cannot set properties of undefined (setting 'isBone')".
# SkeletonUtils.clone retargets skeletons onto the cloned bones, producing a
# self-contained skinned export.
imp="import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';"
if imp not in s: raise SystemExit('GLTFExporter import marker missing')
s=s.replace(imp,imp+"\nimport { clone as cloneWithSkeletonV44 } from 'three/addons/utils/SkeletonUtils.js'; // EXPORT_SKINNED_CLONE_V44",1)

old="   const c=src.clone(true);"
if old not in s: raise SystemExit('cloneForExport marker missing')
s=s.replace(old,"   const c=cloneWithSkeletonV44(src); // EXPORT_SKINNED_CLONE_V44: pertahankan ikatan skeleton",1)

p.write_text(s,encoding='utf-8')
print('Export skinned clone v44: SkeletonUtils.clone menggantikan Object3D.clone')
