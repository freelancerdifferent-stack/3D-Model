from pathlib import Path

p=Path('app/src/main/assets/auto.html')
if not p.exists(): raise SystemExit('auto.html must exist')
s=p.read_text(encoding='utf-8')
if 'ANIM_LIB_GROUPS_V58' in s:
    print('Anim lib groups v58 already applied'); raise SystemExit(0)
if 'ANIM_LIB_SMARTMAP_V56' not in s: raise SystemExit('v56 must run first')

# Library kini berisi 67 klip warrior; panel diubah dari daftar datar menjadi
# daftar terkelompok (Dengan Senjata / Tanpa Senjata) yang bisa di-scroll.
# Nama klip menyimpan prefix kategori 'WW|'/'NW|' di dalam file; UI selalu
# menampilkannya tanpa prefix.
css=r'''
/* ANIM_LIB_GROUPS_V58 */
.anim-lib-list-v52{max-height:46vh;overflow-y:auto;padding-right:2px}
.anim-lib-group-v58{margin:10px 0 4px;font-size:12px;font-weight:700;color:#ffb84d;letter-spacing:.4px}
.anim-lib-group-v58:first-child{margin-top:0}
'''
if '</style>' not in s: raise SystemExit('style end missing')
s=s.replace('</style>',css+'\n</style>',1)

old_list='''      const list=panel.querySelector('#animLibListV52');list.innerHTML='';
      if(!lib.clips.length){list.textContent='Library kosong';return}
      for(const c of lib.clips){
        const it=document.createElement('button');it.type='button';it.className='anim-lib-item-v52';
        it.innerHTML='<b>🏃</b>'+(c.name||'Animation')+' • '+c.duration.toFixed(2)+'s';
        it.addEventListener('click',()=>{if(applyClip(lib,c))closePanel()});
        list.appendChild(it);
      }'''
new_list='''      const list=panel.querySelector('#animLibListV52');list.innerHTML='';
      if(!lib.clips.length){list.textContent='Library kosong';return}
      // ANIM_LIB_GROUPS_V58
      const groupsV58={WW:{t:'⚔ Dengan Senjata',items:[]},NW:{t:'🥋 Tanpa Senjata',items:[]},XX:{t:'Lainnya',items:[]}};
      for(const c of lib.clips){
        const i=(c.name||'').indexOf('|');
        const k=(i>0&&groupsV58[c.name.slice(0,i)])?c.name.slice(0,i):'XX';
        groupsV58[k].items.push(c);
      }
      for(const k of ['WW','NW','XX']){
        const g=groupsV58[k];if(!g.items.length)continue;
        const h=document.createElement('div');h.className='anim-lib-group-v58';h.textContent=g.t+' ('+g.items.length+')';list.appendChild(h);
        for(const c of g.items){
          const nm=(c.name||'Animation').replace(/^\w\w\|/,'');
          const it=document.createElement('button');it.type='button';it.className='anim-lib-item-v52';
          it.dataset.clip=c.name||'';
          it.innerHTML='<b>🏃</b>'+nm+' • '+c.duration.toFixed(2)+'s';
          it.addEventListener('click',()=>{if(applyClip(lib,c))closePanel()});
          list.appendChild(it);
        }
      }'''
if old_list not in s: raise SystemExit('list render anchor missing')
s=s.replace(old_list,new_list,1)

subs=[
("opt.textContent=(idx+1)+'. '+(nc.name||'Animation');sel.appendChild(opt);",
 "opt.textContent=(idx+1)+'. '+((nc.name||'Animation').replace(/^\\w\\w\\|/,''));sel.appendChild(opt);"),
("say('Animasi \"'+(nc.name||'?')+'\" diterapkan');",
 "say('Animasi \"'+((nc.name||'?').replace(/^\\w\\w\\|/,''))+'\" diterapkan');"),
]
for old,new in subs:
    if old not in s: raise SystemExit('anchor missing: '+old[:40])
    s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('Anim lib groups v58: panel terkelompok Dengan/Tanpa Senjata, scrollable')
