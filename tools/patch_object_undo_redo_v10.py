from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'OBJECT_UNDO_REDO_V10' in s:
    print('Object undo redo v10 already applied'); raise SystemExit(0)

# OBJECT_UNDO_REDO_V10 is retained only as a build-pipeline compatibility marker.
# The actual Object/Mesh history owner is V12. Keeping the old V10 runtime
# listeners active created a second history engine attached to the same buttons
# and Transform fields, which could re-disable/refresh Redo while Skeleton mode
# owned those controls.
marker=r'''
// OBJECT_UNDO_REDO_V10
// Legacy history runtime retired. OBJECT_UNDO_REDO_V12 is the sole Object/Mesh
// Undo/Redo engine; Skeleton history is owned separately by V21/V25.
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('script end missing')
s=s[:idx]+marker+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Object undo/redo v10 compatibility marker applied; legacy handlers disabled')
