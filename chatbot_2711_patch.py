# -*- coding: utf-8 -*-
# chatbot_2711_patch.py · 27/11/2026 · «El Pirata»: asistente con preguntas prearmadas (árbol de opciones).
# Uso: python3 chatbot_2711_patch.py <index.html entrada> <index.html salida>
#   La imagen del pirata (versión sepia, webp 192 px) se lee de chat_pirata.webp.b64, en la misma carpeta.
# - Sin IA: responde con los datos que la web ya cargó después del login (DATA, REUNION, MI_NOMBRE, PERMS)
#   y con la tabla asistencia. Respeta los permisos: no ofrece ramas que el compañero no puede ver.
# - El CVU NO va en el HTML: se lee de fund_data.main.payload.cvu (SQL 24) -> window.CVU.
# - Solo visible con sesión iniciada. La portada y el login no cambian.
import sys, os

src, dst = sys.argv[1], sys.argv[2]
AV_B64 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_pirata.webp.b64')).read().strip()
s = open(src, encoding='utf-8').read()
assert 'chatbot-2711' not in s, 'el parche ya estaba aplicado'

# 1) auth: exponer el CVU que viene de la base (solo con permiso Fondo)
A = "window.ALIAS=p?(p.alias||''):'';"
assert s.count(A) == 1, 'cambió la asignación de ALIAS en auth'
s = s.replace(A, A + "window.CVU=p?(p.cvu||''):'';/* chatbot-2711 */")

AV = 'data:image/webp;base64,' + AV_B64

CSS = r'''
<style id="chatbot-2711-style">
#cb-fab{position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:900;width:66px;height:66px;border-radius:50%;border:3px solid #fff;padding:0;cursor:pointer;
  background:#efe2c6 var(--cb-av) center/cover no-repeat;box-shadow:0 6px 18px rgba(10,30,60,.35);transition:transform .15s}
#cb-fab:hover{transform:scale(1.06)}
#cb-fab .cb-bubble{position:absolute;right:58px;bottom:44px;white-space:nowrap;background:#143f6b;color:#fff;font:600 12.5px/1 Montserrat,system-ui,sans-serif;padding:8px 11px;border-radius:12px 12px 2px 12px;box-shadow:0 4px 12px rgba(0,0,0,.2);animation:cbIn .4s ease both}
body:has(#pwa-bar:not([hidden])) #cb-fab{bottom:calc(92px + env(safe-area-inset-bottom))}
body.locked #cb-fab,body.booting #cb-fab,body.gate-open #cb-fab,body.cb-open #cb-fab,body.locked #cb-panel,body.booting #cb-panel{display:none!important}
#cb-panel{position:fixed;z-index:950;right:20px;bottom:20px;width:380px;max-width:calc(100vw - 24px);height:min(600px,calc(100vh - 40px));display:none;flex-direction:column;
  background:var(--surface,#fff);color:var(--ink,#1b2a3a);border-radius:18px;box-shadow:0 18px 50px rgba(10,30,60,.35);overflow:hidden;font-family:Montserrat,system-ui,sans-serif}
body.cb-open #cb-panel{display:flex}
.cb-head{display:flex;align-items:center;gap:10px;padding:12px 12px 12px 14px;background:linear-gradient(135deg,#1f5c9e,#143f6b);color:#fff}
.cb-head .cb-av{width:44px;height:44px;border:2px solid #fff}
.cb-head b{display:block;font-size:15px}.cb-head small{font-size:11.5px;opacity:.85}
.cb-head .cb-x{margin-left:auto;background:rgba(255,255,255,.15);border:0;color:#fff;width:34px;height:34px;border-radius:50%;font-size:20px;cursor:pointer}
.cb-av{flex:none;width:32px;height:32px;border-radius:50%;background:#efe2c6 var(--cb-av) center/cover no-repeat}
.cb-log{flex:1;overflow-y:auto;padding:14px 12px 8px;display:flex;flex-direction:column;gap:10px;background:var(--bg,#f3f6fa)}
.cb-row{display:flex;gap:8px;align-items:flex-end;animation:cbIn .25s ease both}
.cb-row.me{justify-content:flex-end}
.cb-msg{max-width:82%;padding:10px 12px;border-radius:14px 14px 14px 3px;background:var(--surface,#fff);border:1px solid var(--line,#dde4ee);font-size:14px;line-height:1.45}
.cb-row.me .cb-msg{background:#1f5c9e;color:#fff;border-color:#1f5c9e;border-radius:14px 14px 3px 14px}
.cb-msg b{color:inherit}.cb-msg ul{margin:6px 0 0;padding-left:18px;max-height:220px;overflow:auto}.cb-msg li{margin:2px 0}
.cb-msg .cb-big{font-size:20px;font-weight:800;color:#1f5c9e;display:block;margin:2px 0}
.cb-pay{margin-top:8px;display:grid;gap:6px}
.cb-pay div{display:flex;align-items:center;gap:8px;background:var(--bg,#f3f6fa);border-radius:10px;padding:7px 9px}
.cb-pay span{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted,#6b7a8c);min-width:38px}
.cb-pay code{flex:1;font-size:13px;word-break:break-all;font-weight:700}
.cb-pay button,.cb-act{border:0;border-radius:8px;background:#1f5c9e;color:#fff;font:600 12px Montserrat,system-ui,sans-serif;padding:6px 9px;cursor:pointer}
.cb-typing{display:inline-flex;gap:4px}.cb-typing i{width:6px;height:6px;border-radius:50%;background:#8aa0b8;animation:cbDot 1s infinite}.cb-typing i:nth-child(2){animation-delay:.15s}.cb-typing i:nth-child(3){animation-delay:.3s}
.cb-opts{display:flex;flex-wrap:wrap;gap:7px;padding:10px 12px calc(12px + env(safe-area-inset-bottom));border-top:1px solid var(--line,#dde4ee);background:var(--surface,#fff);max-height:42%;overflow-y:auto}
.cb-opt{border:1.5px solid #1f5c9e;background:transparent;color:#1f5c9e;border-radius:999px;padding:8px 13px;font:600 13px Montserrat,system-ui,sans-serif;cursor:pointer;text-align:left}
.cb-opt:hover{background:#1f5c9e;color:#fff}
.cb-opt.sec{border-color:var(--line,#c9d3df);color:var(--muted,#6b7a8c)}
.cb-opt.go{background:#c9a227;border-color:#c9a227;color:#14233a}
@keyframes cbIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@keyframes cbDot{0%,80%,100%{opacity:.3}40%{opacity:1}}
@media(max-width:640px){#cb-panel{right:0;left:0;bottom:0;width:100%;max-width:100%;height:82vh;height:82dvh;border-radius:18px 18px 0 0}#cb-fab{width:60px;height:60px}}
@media(prefers-reduced-motion:reduce){.cb-row,#cb-fab .cb-bubble{animation:none}}
</style>
<button id="cb-fab" type="button" aria-label="Abrir el asistente de La XVII" title="¿En qué te ayudo?"><span class="cb-bubble" id="cb-hint" hidden>¿En qué te ayudo?</span></button>
<div id="cb-panel" role="dialog" aria-modal="false" aria-labelledby="cb-title">
  <div class="cb-head"><span class="cb-av" aria-hidden="true"></span><div><b id="cb-title">El Pirata de La XVII</b><small>Preguntas frecuentes</small></div><button class="cb-x" type="button" id="cb-x" aria-label="Cerrar">×</button></div>
  <div class="cb-log" id="cb-log" aria-live="polite"></div>
  <div class="cb-opts" id="cb-opts"></div>
</div>
'''.replace('--cb-av', '--cb-av')

JS = r'''
<script id="chatbot-2711">
/* chatbot-2711 · «El Pirata»: árbol de preguntas prearmadas. Lee datos ya cargados tras el login; sin IA. */
(function(){
  'use strict';
  const $=id=>document.getElementById(id);
  const B=document.body;
  const esc=x=>String(x==null?'':x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const disp=n=>String(n||'').replace(/\s*\(\d+\)$/,'');
  const fold=x=>disp(x).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const nf=new Intl.NumberFormat('es-AR',{maximumFractionDigits:0});
  const money=x=>'$'+nf.format(Math.round(Number(x)||0));
  const pct=x=>new Intl.NumberFormat('es-AR',{maximumFractionDigits:1}).format((Number(x)||0)*100)+'%';
  const SUPA='https://tfibvqaohjdbxjjatfnd.supabase.co',KEY='sb_publishable_i-idZRBYTiKgluFEWvSdFA_K9em3MkU';
  const TARGET=new Date('2027-11-19T11:00:00-03:00'), FECHA='del viernes 19 al lunes 22 de noviembre de 2027';
  const ok=k=>!B.classList.contains('no-'+k);
  const D=()=>window.DATA||null, KP=()=>(D()&&D().kpi)||{};
  const me=()=>window.MI_NOMBRE||'';
  const nombre=()=>{try{const n=(window.AUTH&&AUTH.user()&&AUTH.user().user_metadata&&AUTH.user().user_metadata.name)||disp(me());const w=n?n.trim().split(/\s+/):[];return w[1]||w[0]||''}catch(e){return ''}};
  const yo=()=>{const m=fold(me());return m?((D()&&D().part)||[]).find(p=>fold(p.n)===m)||null:null};
  const fdate=x=>{const p=String(x||'').slice(0,10).split('-');return p.length===3?p[2]+'/'+p[1]+'/'+p[0]:String(x||'')};
  const gestion=()=>window.GESTION_ACTUAL||((KP().inicio||'').slice(0,4))||'';
  let asisCache=null,asisT=0;
  async function asistencia(){
    if(asisCache&&Date.now()-asisT<60000)return asisCache;
    const r=await fetch(SUPA+'/rest/v1/asistencia?select=pkey',{headers:{apikey:KEY,Authorization:'Bearer '+((window.AUTH&&AUTH.token())||KEY)}});
    if(!r.ok)throw Error('HTTP '+r.status);asisCache=(await r.json())||[];asisT=Date.now();return asisCache;
  }
  /* ---- acciones (salen del chat y llevan a la sección) ---- */
  const later=f=>{close();setTimeout(f,250)};
  const goHash=(h,then)=>later(()=>{if(location.hash!==h)location.hash=h;const e=document.querySelector(h);if(e)e.scrollIntoView({block:'start'});if(then)setTimeout(then,350)});
  const ACT={
    rsvp:()=>later(()=>{const b=$('rsvp-open');if(b){(location.hash==='#companeros'||location.hash==='#ficha-box')&&(location.hash='#inicio');b.click()}}),
    maps:()=>{const u=(window.REUNION||{}).maps_url;if(u&&/^https:\/\//.test(u))window.open(u,'_blank','noopener')},
    deuda:()=>later(()=>{if(location.hash==='#companeros'||location.hash==='#ficha-box')location.hash='#fondo';const b=$('btn-deuda');if(b)b.click();
      const p=yo(),sel=$('dz-who');if(p&&sel){const o=[...sel.options].find(o=>fold(o.textContent)===fold(p.n));if(o){sel.value=o.value;sel.dispatchEvent(new Event('change'))}}}),
    fondo:()=>goHash('#fondo'),
    rendicion:()=>goHash('#fondo',()=>{const e=document.querySelector('#fondo ~ * .gastos, #gastos, [id*="rendic"]');if(e)e.scrollIntoView({block:'start'})}),
    buscar:()=>goHash('#companeros',()=>{const i=$('people-search');if(i)i.focus()}),
    ficha:()=>later(()=>{const l=$('ficha-link');if(l)l.click();else location.hash='#ficha-box'}),
    fotos:()=>goHash('#fotos'),
    subir:()=>goHash('#fotos',()=>{const b=$('show-upload');if(b)b.click()}),
    historia:()=>goHash('#historias',()=>{const i=$('story-title');if(i)i.focus()}),
    cumples:()=>goHash('#cumples'),
    clave:()=>later(()=>{if(window.AUTH&&AUTH.openAccount)AUTH.openAccount()}),
    instalar:()=>later(()=>{const g=$('pwa-go');if(g)g.click()})
  };
  /* ---- árbol: cada nodo devuelve {t: html, o: [[etiqueta, destino], …]} ---- */
  const BACK=(n)=>[['⟵ Volver',n,'sec'],['🏠 Inicio','root','sec']];
  const N={
    root:()=>{const o=[];
      if(ok('reunion'))o.push(['📅 La reunión','reunion']);
      if(D())o.push(['💰 Mi cuenta en el fondo','cuenta'],['📊 El fondo','fondo']);
      if(ok('companeros')||ok('cumples'))o.push(['👥 Compañeros','comp']);
      if(ok('fotos')||ok('historias'))o.push(['📷 Fotos y recuerdos','fotos']);
      o.push(['🛟 Ayuda con la página','ayuda']);
      const n=nombre();return{t:'¡Ahoy'+(n?', <b>'+esc(n)+'</b>':'')+'! Soy el Pirata de La XVII. ¿En qué te ayudo?',o}},
    reunion:()=>({t:'¿Qué querés saber de la reunión?',o:[['¿Cuándo es?','cuando'],['¿Dónde es?','donde'],['¿Quiénes van?','quienes'],['¿Estoy confirmado?','voy'],...BACK('root')]}),
    cuando:()=>{const ms=TARGET-new Date(),d=Math.floor(ms/86400000);
      return{t:'La juntada es '+FECHA+'.'+(ms>0?'<span class="cb-big">'+(d>0?'Faltan '+nf.format(d)+(d===1?' día':' días'):'¡Falta menos de un día!')+'</span>':'<span class="cb-big">¡Es ahora!</span>'),o:[['¿Dónde es?','donde'],['¿Quiénes van?','quienes'],...BACK('reunion')]}},
    donde:()=>{const r=window.REUNION||{},hay=r.lugar&&r.lugar!=='Lugar a confirmar',map=r.maps_url&&/^https:\/\//.test(r.maps_url);
      const o=[];if(hay&&map)o.push(['📍 Cómo llegar','@maps','go']);o.push(['¿Cuándo es?','cuando'],...BACK('reunion'));
      return{t:hay?'Es en <b>'+esc(r.lugar)+'</b>.'+(r.detalle?'<br>'+esc(r.detalle):''):'El lugar todavía no está confirmado. Apenas esté, lo vas a ver acá y en el Inicio.',o}},
    quienes:async()=>{try{const L=(await asistencia()).map(r=>disp(r.pkey)).sort((a,b)=>a.localeCompare(b,'es'));
        return{t:L.length?(L.length===1?'Confirmó <b>1</b> compañero:':'Confirmaron <b>'+L.length+'</b> compañeros:')+'<ul>'+L.map(n=>'<li>'+esc(n)+'</li>').join('')+'</ul>':'Todavía no confirmó nadie. ¡Podés ser el primero!',o:[['¿Estoy confirmado?','voy'],...BACK('reunion')]}}
      catch(e){return{t:'No pude traer la lista ahora. Probá de nuevo en un rato.',o:BACK('reunion')}}},
    voy:async()=>{const m=me();if(!m)return{t:'No encuentro tu nombre vinculado a tu usuario. Avisale a Seba.',o:BACK('reunion')};
      try{const si=(await asistencia()).some(r=>fold(r.pkey)===fold(m));
        return si?{t:'Sí, <b>ya estás confirmado</b> ✋. Si no podés ir, entrá a la confirmación y tocá tu nombre.',o:[['Ver confirmación','@rsvp'],...BACK('reunion')]}
          :{t:'Todavía <b>no confirmaste</b>. Confirmar te suma como aportante del fondo '+esc((window.REUNION||{}).gestion_fondo||'2027')+'.',o:[['✋ Confirmar ahora','@rsvp','go'],...BACK('reunion')]}}
      catch(e){return{t:'No pude consultar la asistencia ahora. Probá de nuevo en un rato.',o:BACK('reunion')}}},
    cuenta:()=>({t:'Tu cuenta en el fondo:',o:[['¿Cuánto debo?','debo'],['¿Cuánto es la cuota?','cuota'],['¿Cómo pago?','pago'],['¿Cómo me fue?','mefue'],...BACK('root')]}),
    debo:()=>{const p=yo(),k=KP(),ini=String(k.inicio||''),pre=ini&&new Date(ini+'T00:00:00-03:00')>new Date();
      if(!me())return{t:'No encuentro tu nombre vinculado a tu usuario. Avisale a Seba.',o:BACK('cuenta')};
      if(!p){const o=[];if(ok('reunion'))o.push(['✋ Confirmar asistencia','@rsvp','go']);o.push(...BACK('cuenta'));
        return{t:'No figurás como aportante de la gestión '+esc(gestion())+', así que no tenés deuda.'+(ok('reunion')?' Si confirmás tu asistencia a la reunión, te sumás al fondo.':''),o}}
      if(!(p.mora>0))return{t:(pre?'La gestión '+esc(gestion())+' arranca el '+fdate(ini)+' y la primera cuota vence el '+(k.vto||'')+' de ese mes. ':'')+'<span class="cb-big">Estás al día ⭐</span>Sos un cadete ejemplar, un orgullo para la promoción.',o:[['¿Cuánto es la cuota?','cuota'],['¿Cómo pago?','pago'],...BACK('cuenta')]};
      return{t:'Debés <b>'+p.mora+' '+(p.mora===1?'cuota':'cuotas')+'</b>:<span class="cb-big">'+money(p.mora*(Number(k.cuota)||0))+'</span>más el interés por atraso. Cálculo al '+esc(k.corte||'')+'.',o:[['🧾 Ver detalle con interés','@deuda','go'],['¿Cómo pago?','pago'],...BACK('cuenta')]}},
    cuota:()=>{const k=KP();return{t:'La cuota es de <b>'+money(k.cuota)+'</b> por mes y vence el <b>día '+esc(k.vto)+'</b> de cada mes.'+(k.inicio?' La gestión '+esc(gestion())+' arrancó el '+fdate(k.inicio)+'.':''),o:[['¿Cuánto debo?','debo'],['¿Cómo pago?','pago'],...BACK('cuenta')]}},
    pago:()=>{const cvu=String(window.CVU||''),al=String(window.ALIAS||'');
      const row=(lab,v)=>v?'<div><span>'+lab+'</span><code>'+esc(v)+'</code><button type="button" data-copy="'+esc(v)+'">Copiar</button></div>':'';
      return{t:(cvu||al)?'Transferí desde cualquier banco o billetera a la cuenta del fondo (BullPay):<div class="cb-pay">'+row('CVU',cvu)+row('Alias',al)+'</div><div style="margin-top:8px">Después avisale al tesorero. 🙏</div>':'Todavía no está cargada la cuenta para transferir. Consultale a Seba.',o:[['¿Cuánto debo?','debo'],...BACK('cuenta')]}},
    mefue:()=>{const p=yo();if(!p)return{t:'No figurás como aportante de la gestión '+esc(gestion())+'.',o:BACK('cuenta')};
      return{t:'Aportaste <b>'+money(p.ap)+'</b>. Hoy tu parte vale <b>'+money(p.val)+'</b>, con una ganancia de <b>'+money(p.gan)+'</b>.<br>Puntaje '+esc(p.score)+' · categoría '+esc(p.cat)+'.',o:[['📊 Ver el fondo completo','@fondo','go'],...BACK('cuenta')]}},
    fondo:()=>({t:'¿Qué querés ver del fondo?',o:[['¿Cuánto hay?','hay'],['¿En qué está invertido?','cartera'],['¿En qué se gastó?','gastos'],...BACK('root')]}),
    hay:()=>{const k=KP(),n=((D()&&D().part)||[]).length;return{t:'Al '+esc(k.corte||'')+' el fondo vale:<span class="cb-big">'+money(k.valor)+'</span>Capital '+money(k.capital)+' · ganancia '+money(k.ganancia)+' (rend. '+pct(k.rend)+').'+(n?' Aportantes: '+n+'.':''),o:[['¿En qué está invertido?','cartera'],...BACK('fondo')]}},
    cartera:()=>{const I=((D()&&D().inst)||[]).filter(i=>Number(i.val)>0);
      return{t:I.length?'La cartera hoy:<ul>'+I.map(i=>'<li><b>'+esc(i.n)+'</b>: '+money(i.val)+(i.tna!=null?' · TNA '+pct(i.tna):'')+'</li>').join('')+'</ul>':'Por ahora no hay inversiones cargadas en esta gestión.',o:[['📊 Ver el detalle','@fondo','go'],...BACK('fondo')]}},
    gastos:()=>({t:'La rendición completa de aportes, inversiones y gastos está en <b>Cuentas Claras</b>. Te llevo.',o:[['🧾 Ir a Cuentas Claras','@rendicion','go'],...BACK('fondo')]}),
    comp:()=>{const o=[];if(ok('cumples'))o.push(['🎂 Próximos cumpleaños','cumple']);if(ok('companeros'))o.push(['🔎 Buscar a un compañero','@buscar'],['✏️ Editar mi ficha','@ficha']);o.push(...BACK('root'));return{t:'¿Qué buscás?',o}},
    cumple:()=>{const R=[...document.querySelectorAll('#birthday-list .birthday-row')].slice(0,4).map(r=>{const b=r.querySelector('b'),s=r.querySelector('span');return '<li><b>'+esc(b&&b.textContent)+'</b> · '+esc(s&&s.textContent)+'</li>'});
      return{t:R.length?'Los que vienen:<ul>'+R.join('')+'</ul>':'Todavía nadie cargó su cumpleaños. Cada uno lo agrega en «Editar mi ficha».',o:[['Ver todos','@cumples'],...BACK('comp')]}},
    fotos:()=>{const o=[];if(ok('fotos'))o.push(['🖼️ Ver álbumes','@fotos'],['⬆️ Subir fotos o videos','@subir']);if(ok('historias'))o.push(['📝 Dejar una historia','@historia']);o.push(...BACK('root'));return{t:'Fotos, videos y recuerdos:',o}},
    ayuda:()=>{const o=[['📲 Instalar en el celular','instalar']];if(ok('companeros'))o.push(['🙂 Cambiar mi foto','@ficha']);o.push(['🔑 Cambiar mi clave','@clave'],['😵 Algo no funciona','nofunca'],...BACK('root'));return{t:'¿Con qué te ayudo?',o}},
    instalar:()=>{const g=$('pwa-go'),bar=$('pwa-bar'),puede=g&&bar&&!bar.hidden;const o=[];if(puede)o.push(['📲 Instalar ahora','@instalar','go']);o.push(...BACK('ayuda'));
      return{t:'Así queda como una app en tu pantalla:<ul><li><b>Android (Chrome):</b> menú ⋮ → «Instalar app» o «Agregar a la pantalla principal».</li><li><b>iPhone (Safari):</b> botón Compartir ⬆️ → «Agregar a inicio».</li></ul>',o}},
    nofunca:()=>({t:'Probá esto:<ul><li>Recargá la página (deslizá hacia abajo en el celular).</li><li>Revisá que tengas conexión.</li><li>Si sigue, escribile a Seba por WhatsApp contando qué pasó, con una captura si podés.</li></ul>',o:BACK('ayuda')})
  };
  /* ---- motor del chat ---- */
  let started=false,busy=false;
  const log=()=>$('cb-log');
  function add(html,mine){const r=document.createElement('div');r.className='cb-row'+(mine?' me':'');r.innerHTML=(mine?'':'<span class="cb-av" aria-hidden="true"></span>')+'<div class="cb-msg">'+html+'</div>';log().appendChild(r);log().scrollTop=log().scrollHeight;return r}
  function opts(L){const box=$('cb-opts');box.innerHTML='';L.forEach(([lab,to,cls])=>{const b=document.createElement('button');b.type='button';b.className='cb-opt'+(cls?' '+cls:'');b.textContent=lab;b.onclick=()=>pick(lab,to);box.appendChild(b)})}
  async function show(id){busy=true;$('cb-opts').innerHTML='';const t=add('<span class="cb-typing"><i></i><i></i><i></i></span>');
    let n;try{n=await Promise.all([N[id](),new Promise(r=>setTimeout(r,380))]).then(a=>a[0])}catch(e){console.warn('chatbot',e);n={t:'Uy, algo falló. Probá de nuevo.',o:BACK('root')}}
    t.querySelector('.cb-msg').innerHTML=n.t;log().scrollTop=log().scrollHeight;opts(n.o);busy=false}
  function pick(lab,to){if(busy)return;add(esc(lab),true);if(to.charAt(0)==='@'){const f=ACT[to.slice(1)];if(f)f();return}show(to)}
  function open(){B.classList.add('cb-open');const h=$('cb-hint');if(h)h.hidden=true;try{localStorage.setItem('laxvii-cb-visto','1')}catch(e){}
    if(!started){started=true;show('root')}else if(!$('cb-opts').children.length)opts(BACK('root').slice(1))}
  function close(){B.classList.remove('cb-open')}
  function init(){const f=$('cb-fab'),p=$('cb-panel');if(!f||!p)return;
    f.onclick=open;$('cb-x').onclick=close;
    document.addEventListener('keydown',e=>{if(e.key==='Escape'&&B.classList.contains('cb-open'))close()});
    log().addEventListener('click',e=>{const b=e.target.closest('[data-copy]');if(!b)return;const v=b.getAttribute('data-copy');
      const done=()=>{b.textContent='¡Copiado!';setTimeout(()=>b.textContent='Copiar',1500)};
      if(navigator.clipboard)navigator.clipboard.writeText(v).then(done,done);else done()});
    try{if(!localStorage.getItem('laxvii-cb-visto')){const h=$('cb-hint');if(h){h.hidden=false;setTimeout(()=>{h.hidden=true},9000)}}}catch(e){}
  }
  window.CHATBOT={open,close,show,nodes:N};
  if(document.readyState!=='loading')init();else document.addEventListener('DOMContentLoaded',init);
})();
</script>
'''

block = CSS.replace('</style>', '#cb-fab,.cb-av{--cb-av:url("' + AV + '")}\n</style>', 1) + JS
assert s.count('</body>') == 1, 'falta o se repite </body>'
s = s.replace('</body>', block + '</body>')
open(dst, 'w', encoding='utf-8').write(s)
print('OK chatbot-2711 ·', len(s), 'bytes')
