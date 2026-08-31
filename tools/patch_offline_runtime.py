from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

# Runtime must never depend on a network CDN. The build workflow copies these
# npm packages into app/src/main/assets/vendor before this patch runs.
s=s.replace('https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js','./vendor/three/build/three.module.js')
s=s.replace('https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/','./vendor/three/examples/jsm/')
s=s.replace('<script src="https://cdn.jsdelivr.net/npm/assimpjs@0.0.10/dist/assimpjs.js"></script>',
            '<script src="./vendor/assimpjs/dist/assimpjs.js"></script>')
s=s.replace("throw new Error('AssimpJS belum termuat. Periksa koneksi internet.');",
            "throw new Error('AssimpJS lokal gagal dimuat dari APK.');")

# AssimpJS resolves its WASM beside assimpjs.js, so keeping the complete dist/
# directory together makes WebView load assimpjs.wasm from the APK assets.
marker='OFFLINE_RUNTIME_V1'
if marker not in s:
    script_marker='<script type="importmap">'
    if script_marker not in s:
        raise SystemExit('importmap marker missing')
    s=s.replace(script_marker,'<!-- OFFLINE_RUNTIME_V1: Three.js + AssimpJS bundled in APK -->\n'+script_marker,1)

# Fail CI if any known runtime CDN remains.
for bad in ('cdn.jsdelivr.net/npm/three@','cdn.jsdelivr.net/npm/assimpjs@'):
    if bad in s:
        raise SystemExit('Runtime CDN still present: '+bad)

p.write_text(s,encoding='utf-8')
print('Offline runtime applied: Three.js and AssimpJS now load from APK assets')
