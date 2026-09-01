from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
if 'MODE_STORAGE_SPLIT_V40' in s:
    print('Mode storage split v40 already applied'); raise SystemExit(0)
if 'OFFLINE_RUNTIME_V1' not in s:
    raise SystemExit('Offline runtime must run first')

# One WebView origin means every machine document would otherwise share the same
# IndexedDB and the same SAF file names. Split both per machine at runtime: the machine
# id comes from window.__OBJECT_MACHINE__, which each copied document overrides.
# Edit keeps the original, unsuffixed names so existing projects stay visible in Edit.
old_open="indexedDB.open(PROJECT_DB_NAME,PROJECT_DB_VERSION)"
if old_open not in s: raise SystemExit('project IndexedDB open marker missing')
s=s.replace(old_open,"indexedDB.open(PROJECT_DB_NAME+modeStorageSuffixV40(),PROJECT_DB_VERSION)",1)

js=r'''
// MODE_STORAGE_SPLIT_V40
// Function declarations hoist across the module, so the projectDb open call above
// can already see these even though they are appended at the end.
function modeStorageSuffixV40(){const m=window.__OBJECT_MACHINE__||'edit';return m==='edit'?'':'_'+m}
function modeFileTagV40(){const m=window.__OBJECT_MACHINE__||'edit';return m==='edit'?'':'['+m+'] '}
(function(){
 const raw=window.Android;
 if(!raw)return;
 const pfx=n=>{const t=modeFileTagV40();return t&&typeof n==='string'&&!n.startsWith(t)?t+n:n};
 const wrap={};
 for(const k of ['chooseProjectFolder','appendProjectWriteChunk','finishProjectWrite','cancelProjectWrite']){
   if(typeof raw[k]==='function')wrap[k]=function(){return raw[k].apply(raw,arguments)};
 }
 if(typeof raw.saveProjectFile==='function')wrap.saveProjectFile=function(name,json){return raw.saveProjectFile(pfx(name),json)};
 if(typeof raw.saveBase64File==='function')wrap.saveBase64File=function(b64,fileName,mime){return raw.saveBase64File(b64,pfx(fileName),mime)};
 if(typeof raw.beginProjectWrite==='function')wrap.beginProjectWrite=function(mode,name,fileName){return raw.beginProjectWrite(mode,pfx(name),pfx(fileName))};
 window.__AndroidRawV40=raw;
 window.Android=wrap;
})();
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('module script end missing')
s=s[:idx]+js+'\n'+s[idx:]
p.write_text(s,encoding='utf-8')
print('Mode storage split v40 applied: per-machine IndexedDB and per-machine file tags')
