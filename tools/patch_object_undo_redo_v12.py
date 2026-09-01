from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'OBJECT_UNDO_REDO_V12' in s:
    print('Object undo redo v12 already applied'); raise SystemExit(0)
marker=r'''
// OBJECT_UNDO_REDO_V12
// Compatibility marker only. Live Edit Object/Mesh Undo/Redo is owned solely by
// OBJECT_UNDO_REDO_V10. Keeping a second runtime here caused duplicate listeners,
// competing button state, and broken history on Android WebView.
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('script end missing')
s=s[:idx]+marker+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Object undo/redo v12 compatibility marker applied; runtime disabled')
