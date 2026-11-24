#!/usr/bin/env python3
"""servidor_patch.py · 24/11/2026 · La base manda: lo borrado no vuelve a aparecer.

Uso:  python3 -I servidor_patch.py entrada.html salida.html

Problema (reportado por Seba): un texto de prueba en Recuerdos reaparecía cada vez que se recargaba
la página. No está en la base: vive en la copia local del navegador (IndexedDB). Al sincronizar,
la web MEZCLABA lo local con lo de la base (se quedaba con todo), así que algo que existía solo en
un navegador, o que otra pestaña/la app instalada tenía en memoria, volvía siempre.

Arreglo: cuando la consulta a la base sale bien, para historias, firmas, homenajes, fotos y álbumes
manda la base (se descarta lo que solo está en el navegador). Si la consulta falla, se conserva lo
local, como antes. No toca la base ni borra nada en ella.
Además:
- Al abrir la página ya no se reenvía toda la copia local a la base (eso deshacía cambios: el 24/11
  una pestaña con copia vieja volvió 76 fotos a «Históricas»).
- Al sincronizar, a la base solo van los campos que cambiaron en esta sesión (PATCH); filas nuevas completas.
- Mover fotos usa la función admin_move_photos (SQL 22); la base ignora cualquier otro cambio de álbum.
- La consulta de permisos pide solo la fila del propio usuario (el admin puede leerlas todas).
El parche falla si ya estaba aplicado o si cambió el texto de base.
"""
import sys

MARK = "servidor-2411"


def rep(s, old, new, what=""):
    n = s.count(old)
    assert n == 1, f"[servidor_patch] esperaba 1 ocurrencia de {what or old[:70]!r}, hay {n}"
    return s.replace(old, new)


SYNC_OLD = ("async function syncUp(){if(!remoteOn())return;\n for(const t of ['stories','signatures','tributes','photos','albums']){const cur=snapArr(state[t]),prev=syncSnap[t]||{};"
            "for(const id in cur){if(JSON.stringify(prev[id])!==JSON.stringify(cur[id]))pushRow(t,t==='stories'?rowStory(cur[id]):t==='tributes'?rowTrib(cur[id]):t==='photos'?rowPhoto(cur[id]):t==='albums'?rowAlbum(cur[id]):rowSign(cur[id]));}"
            "for(const id in prev){if(!cur[id])delRow(t,id);}syncSnap[t]=cur;}\n const cur=snapObj(state.profiles),prev=syncSnap.profiles;"
            "for(const k in cur){if(JSON.stringify(prev[k])!==JSON.stringify(cur[k]))pushRow('profiles',rowProf(k,cur[k]));}syncSnap.profiles=cur;\n}")
SYNC_NEW = ("/* servidor-2411: a la base solo va lo que cambió en esta sesión (campo por campo); las filas nuevas van completas */\n"
            "async function patchRow(table,col,id,diff){try{await sreq(table+'?'+col+'=eq.'+encodeURIComponent(id),{method:'PATCH',body:JSON.stringify(diff)});}catch(e){console.warn('patch',table,e);}}\n"
            "const rowDiff=(a,b)=>{const d={};for(const k in b){if(JSON.stringify(a[k])!==JSON.stringify(b[k]))d[k]=b[k]}return d};\n"
            "async function syncUp(){if(!remoteOn())return;\n const RF={stories:rowStory,tributes:rowTrib,photos:rowPhoto,albums:rowAlbum,signatures:rowSign};\n"
            " for(const t of ['stories','signatures','tributes','photos','albums']){const cur=snapArr(state[t]),prev=syncSnap[t]||{};"
            "for(const id in cur){if(JSON.stringify(prev[id])===JSON.stringify(cur[id]))continue;if(!prev[id]){pushRow(t,RF[t](cur[id]));continue}"
            "const d=rowDiff(RF[t](prev[id]),RF[t](cur[id]));delete d.id;if(Object.keys(d).length)patchRow(t,'id',id,d);}"
            "for(const id in prev){if(!cur[id])delRow(t,id);}syncSnap[t]=cur;}\n const cur=snapObj(state.profiles),prev=syncSnap.profiles||{};"
            "for(const k in cur){if(JSON.stringify(prev[k])===JSON.stringify(cur[k]))continue;if(!prev[k]){pushRow('profiles',rowProf(k,cur[k]));continue}"
            "const d=rowDiff(rowProf(k,prev[k]),rowProf(k,cur[k]));delete d.pkey;if(Object.keys(d).length)patchRow('profiles','pkey',k,d);}syncSnap.profiles=cur;\n}")


def apply(h):
    assert MARK not in h, "[servidor_patch] ya estaba aplicado"
    h = rep(h, "sreq('tributes?select=*').catch(()=>[]),sreq('photos?select=*').catch(()=>[]),sreq('albums?select=*').catch(()=>[])",
            "sreq('tributes?select=*').catch(()=>null),sreq('photos?select=*').catch(()=>null),sreq('albums?select=*').catch(()=>null)",
            "pull: falla = null")
    h = rep(h, "const st=res[0]||[],sg=res[1]||[],pr=res[2]||[],tr=res[3]||[],ph=res[4]||[],al=res[5]||[];",
            "const st=res[0]||[],sg=res[1]||[],pr=res[2]||[],tr=res[3],ph=res[4],al=res[5];",
            "pull: resultados")
    h = rep(h, "const mergeArr=(local,rem)=>{const by={};(local||[]).concat(rem||[]).forEach(x=>{if(x&&x.id)by[x.id]=x});return Object.values(by).sort((a,b)=>Date.parse(b.created)-Date.parse(a.created));};",
            "/* servidor-2411: si la base respondió, manda la base; si falló, queda lo local */\n"
            " const mergeArr=(local,rem)=>{if(rem==null)return (local||[]).slice();const by={};(rem||[]).forEach(x=>{if(x&&x.id)by[x.id]=x});return Object.values(by).sort((a,b)=>Date.parse(b.created)-Date.parse(a.created));};",
            "pull: mergeArr")
    # al abrir la página: NO reenviar toda la copia local; la referencia es lo que había guardado
    h = rep(h, "syncUp();pullRemote();setInterval(pullRemote,45000);",
            "syncSnap={stories:snapArr(state.stories),signatures:snapArr(state.signatures),tributes:snapArr(state.tributes||[]),photos:snapArr(state.photos||[]),albums:snapArr(state.albums||[]),profiles:snapObj(state.profiles)};"
            "pullRemote();setInterval(pullRemote,45000);   /* servidor-2411: sin envío masivo al abrir */",
            "arranque sin envío masivo")
    # sincronizar: a la base solo van los CAMPOS que cambiaron en esta sesión (las filas nuevas, completas)
    h = rep(h, SYNC_OLD, SYNC_NEW, "syncUp por diferencias")
    # mover fotos: por la función del admin (la base ignora cualquier otro cambio de álbum)
    h = rep(h, "  await mutate(s=>{s.photos.forEach(x=>{if(ids.includes(x.id))x.category=dest})});return ids.length}",
            "  await sreq('rpc/admin_move_photos',{method:'POST',body:JSON.stringify({p_ids:ids,p_dest:dest})});\n"
            "  await mutate(s=>{s.photos.forEach(x=>{if(ids.includes(x.id))x.category=dest})});return ids.length}",
            "mover por RPC")
    # el admin puede leer todas las filas de permisos: pedir solo la propia
    h = rep(h, "fetch(URL_+'/rest/v1/permisos?select=perfil,perms',{headers:h}).catch(()=>null),",
            "fetch(URL_+'/rest/v1/permisos?select=perfil,perms&user_id=eq.'+uidq,{headers:h}).catch(()=>null),",
            "auth: permisos propios")
    return h


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    h = open(src, encoding="utf-8").read()
    out = apply(h)
    open(dst, "w", encoding="utf-8").write(out)
    print(f"OK · {len(h):,} → {len(out):,} bytes")
