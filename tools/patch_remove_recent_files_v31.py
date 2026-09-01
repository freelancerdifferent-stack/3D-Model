from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

if 'REMOVE_RECENT_FILES_V31' in s:
    print('Recent Files v31 already removed')
    raise SystemExit(0)

block='''      <div class="titleline"><h2>Recent Files</h2><span style="color:#61a6ff;font-size:12px">Local</span></div>\n      <div class="file-card"><div class="thumb">🪑</div><div><b>Model.glb</b><small>Import GLB dari perangkat</small></div><div>⋮</div></div>\n      <div class="file-card"><div class="thumb">🚙</div><div><b>Model.fbx</b><small>Import FBX dari perangkat</small></div><div>⋮</div></div>\n      <div class="file-card"><div class="thumb">🖼️</div><div><b>Texture.png</b><small>Pasang PNG ke material model</small></div><div>⋮</div></div>\n'''
if block not in s:
    raise SystemExit('Recent Files placeholder block not found')

s=s.replace(block,'      <!-- REMOVE_RECENT_FILES_V31: placeholder Recent Files UI removed -->\n',1)
p.write_text(s,encoding='utf-8')
print('Removed placeholder Recent Files UI from Home')
