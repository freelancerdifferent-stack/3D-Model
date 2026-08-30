from pathlib import Path

src_path = Path(__file__).with_name('patch_layers.py')
src = src_path.read_text(encoding='utf-8')
lines = src.splitlines()

try:
    start = next(i for i, line in enumerate(lines) if line.startswith("reg_marker="))
    end = next(i for i in range(start, len(lines)) if "s=s.replace(reg_marker,reg_repl,1)" in lines[i]) + 1
except StopIteration:
    raise SystemExit('Unable to locate legacy registerModel marker block in patch_layers.py')

# The old patch expected registerModel() to be immediately followed by the
# injected layer helper functions. That assumption is brittle after other
# build-time patches (Assimp, etc.). Instead, register the primary layer at the
# common successful-import point. This is independent of GLB/FBX parser layout.
replacement = [
    "primary_marker=\"    $('importStatus').textContent=`Berhasil import ${f.name}.`;\"",
    "if primary_marker not in s: raise SystemExit('primary import success marker missing')",
    "s=s.replace(primary_marker,\"    if(!suppressLayerSync) registerPrimaryLayer();\\n\"+primary_marker,1)",
]

patched = '\n'.join(lines[:start] + replacement + lines[end:]) + '\n'
exec(compile(patched, str(src_path), 'exec'), {'__name__': '__main__', '__file__': str(src_path)})
