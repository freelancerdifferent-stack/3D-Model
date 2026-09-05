from pathlib import Path

# PANGGANG IKUT KLIP ANIMASI - UPRIGHT_BAKE_CLIPS_V76
#
# Panggang v71 hanya memanggang REST POSE. Klip animasi tidak ikut, sehingga
# begitu mixer memutar klip ia MENIMPA transform lokal hasil panggang dengan
# nilai asli yang masih Z-up, dan seluruh rig kembali rebah.
#
# Terukur pada Anim_Warrior_Walk.FBX, kotak mesh:
#   dengan v71  diam 138.2 x 182.6 x 36.6   saat main 119 x  89.1 x 192.7  ambruk
#   tanpa v71   diam  95.0 x 173.7 x 116.6  saat main  79.1 x 177.4 x  60.4
# Tanpa v71 animasinya tegak tapi rest-nya rusak (kerusakan skinning CPU yang
# justru diperbaiki v71). Jadi keduanya harus dipenuhi sekaligus.
#
# Bukti sebabnya, membandingkan rest sesudah panggang dengan key pertama klip:
#   pelvis  posisi  rest (-0.6, 91.4, -0.1)  key (-0.6, 0.1, 91.4)   BEDA, Z-up
#   pelvis  rotasi  rest (0.538, 0.531, -0.457, -0.469)
#                   key  (-0.049, -0.699, -0.052, 0.712)             BEDA
#   spine_01, spine_02                                               IDENTIK
# Hanya tulang paling atas yang berbeda - tepat sesuai cara panggang bekerja,
# karena keturunannya mewarisi.
#
# Perbaikannya: panggang mencatat matriks yang dipakaikan ke tiap simpul, lalu
# nilai keyframe simpul itu ikut ditransformasi - posisi oleh matriksnya,
# kuaternion oleh bagian rotasinya, skala oleh bagian skalanya.
#
# Satu hal yang harus dijaga. Panggang menembus simpul perantara dan
# mengembalikannya ke identitas; itu wajib supaya THREE.Skeleton.pose() sah
# untuk tulang akar. Kalau simpul yang ditembus itu punya track, track tersebut
# akan melawan hasil panggang. Pada berkas ini Group 'root' - induk tulang
# 'pelvis' - memang punya track, TAPI track-nya identitas murni: posisi
# (0,0,0), rotasi identitas, skala (1,1,1), rentang perubahan 0 pada seluruh
# 41 key. Track semacam itu tidak melakukan apa-apa, jadi aman ditembus dan
# track-nya dibuang. Simpul perantara yang track-nya BENAR-BENAR bergerak
# tidak ditembus: panggang berhenti di situ dan track-nya yang dipanggang,
# sehingga animasinya tetap benar walau pose() kehilangan syaratnya - animasi
# yang benar lebih penting daripada kenyamanan pose().
#
# Hanya menyentuh animation.html.

p = Path('app/src/main/assets/animation.html')
if not p.exists(): raise SystemExit('animation.html must exist')
s = p.read_text(encoding='utf-8')

if 'UPRIGHT_BAKE_CLIPS_V76' in s:
    print('Upright bake clips v76 already applied'); raise SystemExit(0)
if 'FBX_UPRIGHT_BAKE_V71' not in s: raise SystemExit('FBX_UPRIGHT_BAKE_V71 must exist first')
if "window.__OBJECT_MACHINE__='animation';" not in s: raise SystemExit('bukan dokumen mesin Animation')

old = """      const bakeDownV71=node=>{
        node.updateMatrix();
        const M=node.matrix.clone();
        for(const c of node.children){
          c.updateMatrix();
          c.matrix.premultiply(M);
          c.matrix.decompose(c.position,c.quaternion,c.scale);
        }
        node.position.set(0,0,0);
        node.quaternion.set(0,0,0,1);
        node.scale.set(1,1,1);
        node.updateMatrix();
        for(const c of node.children){
          if(!c.isBone&&!c.isMesh&&!c.isSkinnedMesh)bakeDownV71(c);
        }
      };
      bakeDownV71(obj);
      obj.updateMatrixWorld(true);"""

new = r"""      // UPRIGHT_BAKE_CLIPS_V76
      const klipV76=Array.isArray(obj.animations)?obj.animations:[];
      const trackMilikV76=nm=>{
        const out=[];
        for(const k of klipV76) for(const tr of (k.tracks||[])){
          const t=String(tr.name).split('.');
          if(t[0]===nm)out.push({klip:k,tr,jenis:t[1]});
        }
        return out;
      };
      // Track yang isinya identitas murni tidak melakukan apa-apa, jadi aman
      // ditembus panggang dan dibuang. Yang benar-benar bergerak tidak.
      const trackIdentitasV76=nm=>{
        const daftar=trackMilikV76(nm);
        if(!daftar.length)return false;
        const E=1e-6;
        for(const {tr,jenis} of daftar){
          const v=tr.values;
          if(jenis==='position'){ for(let i=0;i<v.length;i++) if(Math.abs(v[i])>E)return false; }
          else if(jenis==='scale'){ for(let i=0;i<v.length;i++) if(Math.abs(v[i]-1)>E)return false; }
          else if(jenis==='quaternion'){
            for(let i=0;i<v.length;i+=4){
              if(Math.abs(v[i])>E||Math.abs(v[i+1])>E||Math.abs(v[i+2])>E||Math.abs(Math.abs(v[i+3])-1)>E)return false;
            }
          } else return false;
        }
        return true;
      };
      const buangTrackV76=nm=>{
        for(const k of klipV76) k.tracks=(k.tracks||[]).filter(tr=>String(tr.name).split('.')[0]!==nm);
      };
      // Transformasi keyframe simpul dengan matriks yang dipakaikan padanya.
      const _mR=new THREE.Matrix4(), _q=new THREE.Quaternion(), _qM=new THREE.Quaternion(), _v=new THREE.Vector3(), _sM=new THREE.Vector3();
      const panggangTrackV76=(nm,M)=>{
        const daftar=trackMilikV76(nm);
        if(!daftar.length)return 0;
        _mR.extractRotation(M); _qM.setFromRotationMatrix(_mR); _sM.setFromMatrixScale(M);
        for(const {tr,jenis} of daftar){
          const v=tr.values;
          if(jenis==='position'){
            for(let i=0;i<v.length;i+=3){ _v.set(v[i],v[i+1],v[i+2]).applyMatrix4(M); v[i]=_v.x;v[i+1]=_v.y;v[i+2]=_v.z; }
          }else if(jenis==='quaternion'){
            for(let i=0;i<v.length;i+=4){ _q.set(v[i],v[i+1],v[i+2],v[i+3]).premultiply(_qM); v[i]=_q.x;v[i+1]=_q.y;v[i+2]=_q.z;v[i+3]=_q.w; }
          }else if(jenis==='scale'){
            for(let i=0;i<v.length;i+=3){ v[i]*=_sM.x;v[i+1]*=_sM.y;v[i+2]*=_sM.z; }
          }
        }
        return daftar.length;
      };

      let trackDipanggangV76=0, trackDibuangV76=0, berhentiV76=0;
      const bakeDownV76=node=>{
        node.updateMatrix();
        const M=node.matrix.clone();
        const anak=node.children.slice();
        for(const c of anak){
          c.updateMatrix();
          c.matrix.premultiply(M);
          c.matrix.decompose(c.position,c.quaternion,c.scale);
        }
        node.position.set(0,0,0);
        node.quaternion.set(0,0,0,1);
        node.scale.set(1,1,1);
        node.updateMatrix();
        for(const c of anak){
          const punyaTrack=trackMilikV76(c.name).length>0;
          const perantara=!c.isBone&&!c.isMesh&&!c.isSkinnedMesh;
          if(perantara&&(!punyaTrack||trackIdentitasV76(c.name))){
            // Aman ditembus. Track identitas dibuang supaya tidak melawan panggang.
            if(punyaTrack){buangTrackV76(c.name);trackDibuangV76++}
            bakeDownV76(c);
          }else if(punyaTrack){
            // Simpul ini memikul transformnya sendiri saat animasi berjalan,
            // jadi keyframe-nya yang dipanggang - bukan diteruskan ke bawah.
            trackDipanggangV76+=panggangTrackV76(c.name,M);
            if(perantara)berhentiV76++;
          }
        }
      };
      bakeDownV76(obj);
      obj.updateMatrixWorld(true);"""

if old not in s: raise SystemExit('blok bakeDownV71 tidak ditemukan')
s = s.replace(old, new, 1)

old_log = "      console.log('FBX_UPRIGHT_BAKE_V71: rotasi dipanggangkan sampai tulang & mesh, simpul perantara identitas, '+skelsV71.size+' skeleton diikat ulang');"
new_log = ("      console.log('FBX_UPRIGHT_BAKE_V71: rotasi dipanggangkan sampai tulang & mesh, simpul perantara identitas, '+skelsV71.size+' skeleton diikat ulang');\n"
           "      console.log('UPRIGHT_BAKE_CLIPS_V76: '+trackDipanggangV76+' track dipanggang, '+trackDibuangV76+' track identitas dibuang, '+berhentiV76+' simpul perantara tidak ditembus');")
if old_log not in s: raise SystemExit('baris log v71 tidak ditemukan')
s = s.replace(old_log, new_log, 1)

if 'bakeDownV71' in s: raise SystemExit('masih ada sisa bakeDownV71')

p.write_text(s, encoding='utf-8')
print('Upright bake clips v76 applied: klip animasi ikut dipanggang bersama rest pose')
