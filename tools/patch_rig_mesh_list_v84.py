#!/usr/bin/env python3
# RIG_MESH_LIST_V84 - mesh dipilih dari daftar, bukan dengan membidik sentuhan.
#
# Gejalanya: alur "sentuh senjata, sentuh tulang, Bind" tidak pernah bisa
# dijalankan dengan jari, sehingga Apply Weight dan Bind tidak punya sasaran.
#
# Diuji di Chromium dengan sentuhan sungguhan pada SK_NYX_bonus_animation.glb:
#
#   sentuh ujung bilah (titik terjauh dari tulang, 24.3 satuan)
#     -> terpilih tulang breast_l, mesh tetap null
#   sentuh tengah bilah, sesudah prioritas dibalik ke mesh
#     -> sinar mengenai SK_NYX_SUIT (badan) di jarak 534; bilah tertutup badan
#        dari sudut itu, dan tulang thigh_r hanya 5 piksel dari titik sentuh
#
# Tiga sebab bertumpuk: bilahnya tipis, sebagian tertutup badan, dan rig ini
# punya 125 tulang sehingga selalu ada sendi yang lebih dekat daripada mesh mana
# pun. Mengutak-atik prioritas sentuhan tidak menyelesaikannya - percobaan itu
# sudah dibuat, diukur gagal, dan dibuang.
#
# Perbaikannya menghapus penyebabnya, bukan menutupinya: mesh dipilih dari
# DAFTAR NAMA. Tidak ada sinar yang bisa meleset, tidak ada badan yang
# menghalangi, tidak ada tulang yang menyerobot. Mesh tanpa skin diberi tanda
# "perlu rig" dan dikonversi saat dipilih, memakai jalur yang sama dengan
# RIG_PROP_SKIN_V82.
#
# Sentuhan di viewport tidak diubah sama sekali - memilih tulang tetap seperti
# sebelumnya. Daftar ini menambah jalan, tidak mengganti yang sudah ada.
#
# Hanya animation.html yang disentuh.

from pathlib import Path

p = Path('app/src/main/assets/animation.html')
s = p.read_text(encoding='utf-8')

if 'RIG_MESH_LIST_V84' in s:
    raise SystemExit('RIG_MESH_LIST_V84 sudah ada - patch dijalankan dua kali')
if 'RIG_PROP_SKIN_V82' not in s:
    raise SystemExit('mesin v82 tidak ditemukan - urutan pipeline salah')

# ---------------------------------------------------------------- CSS
anchor_css = "#rigWorkspaceV26 #rigBindV26{background:#1b553c;border-color:#33795b}\n"
if anchor_css not in s:
    raise SystemExit('blok CSS tombol Bind tidak ditemukan')
css = """/* RIG_MESH_LIST_V84 */
#rigWorkspaceV26 #rigMeshPickV84{width:100%;min-height:44px;margin-top:9px;border-radius:10px;background:#152b40;display:flex;align-items:center;justify-content:space-between;padding:0 12px;gap:8px}
#rigWorkspaceV26 #rigMeshPickV84 .rig-pick-label{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:700}
#rigWorkspaceV26 #rigMeshListV84{margin-top:8px;max-height:34vh;overflow:auto;border:1px solid #315e87;border-radius:10px;background:#0e1826}
#rigWorkspaceV26 #rigMeshListV84 button{display:flex;align-items:center;gap:8px;width:100%;min-height:44px;padding:0 12px;border:0;border-bottom:1px solid #1c3350;background:transparent;color:#dcecff;font-size:14px;font-weight:600;text-align:left}
#rigWorkspaceV26 #rigMeshListV84 button:last-child{border-bottom:0}
#rigWorkspaceV26 #rigMeshListV84 button:active{background:#16283c}
#rigWorkspaceV26 #rigMeshListV84 button.sel{background:#173f62}
#rigWorkspaceV26 #rigMeshListV84 .rig-item-name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#rigWorkspaceV26 #rigMeshListV84 .rig-item-tag{flex:none;font-size:11px;font-weight:700;padding:2px 7px;border-radius:999px;background:#4a3410;color:#ffce7a}
"""
s = s.replace(anchor_css, anchor_css + css, 1)

# ---------------------------------------------------------------- markup
anchor_html = ('     <div class="rig-actions"><button id="rigApplyV26" type="button">Apply Weight</button>'
               '<button id="rigBindV26" type="button">Bind</button></div>')
if anchor_html not in s:
    raise SystemExit('baris tombol aksi Rig tidak ditemukan')
html = ('     <button id="rigMeshPickV84" type="button"><span class="rig-pick-label">Pilih Mesh dari daftar</span>'
        '<span id="rigMeshPickCaretV84">▾</span></button>\n'
        '     <div id="rigMeshListV84" hidden></div>\n')
s = s.replace(anchor_html, html + anchor_html, 1)

# ---------------------------------------------------------------- JS
anchor_js = " window.openRigWorkspaceV26=()=>setRigModeV26(true);\n"
if anchor_js not in s:
    raise SystemExit('titik ekspor workspace Rig tidak ditemukan')

js = r""" // RIG_MESH_LIST_V84 - pilih mesh dari daftar nama.
 //
 // Membidik dengan sentuhan tidak bisa diandalkan pada model padat: mesh tipis
 // tertutup mesh lain, dan pemilihan tulang selalu menang karena sendi hampir
 // selalu lebih dekat di layar. Daftar nama menghapus ketiga sumber itu.
 const rigMeshPickV84=$('rigMeshPickV84'),rigMeshListV84=$('rigMeshListV84');
 function labelMeshV84(o,i){return o.name||('(tanpa nama '+(i+1)+')')}
 function pilihDariDaftarV84(o){
   if(!o)return false;
   let m=o;
   if(!m.isSkinnedMesh){
     const c=jadikanSkinV82(m);
     if(!c)return false;
     m=c;refreshHelper();setSkeletonVisible(true);
   }
   rigMeshV26=m;
   // Apply Weight butuh titik pusat kuas; tanpa sentuhan, pusat mesh dipakai.
   m.updateMatrixWorld(true);
   rigHitWorldV26=new THREE.Box3().setFromObject(m).getCenter(new THREE.Vector3());
   rigStatusV26.textContent=(m.userData&&m.userData.propSkinV82)
     ?'Benda siap dirig - pilih bone lalu Bind'
     :('Mesh dipilih: '+(m.name||'SkinnedMesh'));
   syncRigUiV26();
   return true;
 }
 function isiDaftarMeshV84(){
   // Yang belum punya skin diletakkan di atas: justru itulah yang dicari orang
   // saat membuka daftar ini, dan pada model padat ia bisa terkubur jauh di
   // bawah (senjata di berkas SK_NYX ada di baris 31 dari 32).
   const daftar=sasaranRigV82().slice().sort((a,b)=>(a.isSkinnedMesh?1:0)-(b.isSkinnedMesh?1:0));
   rigMeshListV84.innerHTML='';
   if(!daftar.length){
     const kosong=document.createElement('button');kosong.type='button';kosong.disabled=true;
     kosong.innerHTML='<span class="rig-item-name">Tidak ada mesh pada model ini</span>';
     rigMeshListV84.appendChild(kosong);return;
   }
   daftar.forEach((o,i)=>{
     const b=document.createElement('button');b.type='button';
     if(o===rigMeshV26)b.className='sel';
     const nm=document.createElement('span');nm.className='rig-item-name';nm.textContent=labelMeshV84(o,i);
     b.appendChild(nm);
     if(!o.isSkinnedMesh){
       const tag=document.createElement('span');tag.className='rig-item-tag';tag.textContent='perlu rig';
       b.appendChild(tag);
     }
     b.onclick=()=>{if(pilihDariDaftarV84(o)){tutupDaftarV84();}};
     rigMeshListV84.appendChild(b);
   });
 }
 function bukaDaftarV84(){isiDaftarMeshV84();rigMeshListV84.hidden=false;$('rigMeshPickCaretV84').textContent='▴'}
 function tutupDaftarV84(){rigMeshListV84.hidden=true;$('rigMeshPickCaretV84').textContent='▾'}
 rigMeshPickV84.onclick=()=>{if(rigMeshListV84.hidden)bukaDaftarV84();else tutupDaftarV84()};
 window.openRigWorkspaceV26=()=>{setRigModeV26(true);tutupDaftarV84()};
"""
s = s.replace(anchor_js, js, 1)

# Daftar ditutup saat workspace ditutup, supaya tidak menggantung terbuka.
lama_tutup = " window.closeRigWorkspaceV26=()=>setRigModeV26(false);\n"
if lama_tutup not in s:
    raise SystemExit('titik penutup workspace Rig tidak ditemukan')
s = s.replace(lama_tutup, " window.closeRigWorkspaceV26=()=>{setRigModeV26(false);tutupDaftarV84()};\n", 1)

p.write_text(s, encoding='utf-8')
print('RIG_MESH_LIST_V84 applied: daftar mesh di panel Rig, mesh tanpa skin ditandai dan dikonversi saat dipilih')
