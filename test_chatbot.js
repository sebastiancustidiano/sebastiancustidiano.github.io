// test_chatbot.js · «El Pirata» (chatbot-2711) con Supabase simulado (mismas reglas que test_perfiles.js).
// Uso: node test_chatbot.js <index.html> [carpeta_capturas]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs');
const FILE = process.argv[2], SHOTS = process.argv[3] || '/tmp/shots_cb';
fs.mkdirSync(SHOTS, { recursive: true });
const SUPA = 'https://tfibvqaohjdbxjjatfnd.supabase.co';
const USERS = {
  '117': { id: 'u-117', name: 'Custidiano Sebastián', role: 'admin' },
  '1': { id: 'u-1', name: 'Figueredo Carlos Eduardo', role: 'member' },
  '2': { id: 'u-2', name: 'Aquino Luis Froilán', role: 'member' },
};
const PERMISOS = { 'u-2': { perfil: 'restringido', perms: ['fotos:Históricas'] } };
const DATA = { kpi: { capital: 1000, valor: 900, ganancia: 50, rend: 0.05, tna: 0.3, aportantes: 2, total: 2, aportes: 1000, comun: 0, corte: '20/11/2026', gastos: 100, cuota: 20000, vto: 5, inicio: '2026-01-01', meses: 11 },
  part: [{ n: 'Figueredo Carlos Eduardo', ap: 1000, val: 900, gan: 50, pct: 1, cob: 1, mora: 2, adel: 0, punt: 0, score: 900, cat: 'A', gasto: 100, saldo: 800 },
         { n: 'Custidiano Sebastián', ap: 1000, val: 900, gan: 50, pct: 1, cob: 1, mora: 0, adel: 0, punt: 0, score: 950, cat: 'A+', gasto: 100, saldo: 800 }],
  inst: [{ n: 'Caución', t: 'Renta fija', val: 900, rend: 0, tna: 0.3, src: null }],
  evol: [{ m: 'Oct', cap: 500, ap: 500, ret: 0 }, { m: 'Nov', cap: 1000, ap: 500, ret: 0 }],
  ultimo: null, gastos: [], movs: [] };
const FUND = [
  { id: 'main', payload: { DATA, PHOTOS: {}, alias: 'ALIAS.PRUEBA.XVII', cvu: '0000099900000000000001', COLECTA: null } },
  { id: 'comun', payload: { PHOTOS: {} } },
  { id: 'reunion', payload: { lugar: 'Lugar de prueba', detalle: 'Viernes 19 · 11:00 h', fotos_url: '', maps_url: 'https://maps.example.com/x', gestion_fondo: '2027' } },
  { id: 'padron', payload: { names: ['Figueredo Carlos Eduardo', 'Custidiano Sebastián', 'Aquino Luis Froilán'] } },
];
const tokUser = {};
const permsOf = u => (u.role === 'admin' || !PERMISOS[u.id]) ? ['*'] : PERMISOS[u.id].perms;
const has = (u, k) => { const p = permsOf(u); return p.includes('*') || p.includes(k) || (k.startsWith('fotos:') && p.includes('fotos:*')); };
async function supa(route) {
  const req = route.request(), url = new URL(req.url()), p = url.pathname, m = req.method();
  const json = (b, s = 200) => route.fulfill({ status: s, contentType: 'application/json', body: JSON.stringify(b) });
  if (p === '/auth/v1/token') {
    const b = JSON.parse(req.postData() || '{}');
    let mat = b.email ? b.email.split('@')[0] : null; if (b.refresh_token) mat = b.refresh_token.split('-')[1];
    const u = USERS[mat]; if (!u || (b.password && b.password !== 'Clave.123')) return json({ msg: 'Invalid login credentials' }, 400);
    const tok = 'tok-' + mat; tokUser[tok] = u;
    return json({ access_token: tok, refresh_token: 'ref-' + mat, expires_in: 3600, user: { id: u.id, email: mat + '@laxvii.com.ar', app_metadata: { member: true, role: u.role }, user_metadata: { name: u.name, matricula: mat } } });
  }
  const tok = (req.headers()['authorization'] || '').replace('Bearer ', ''), u = tokUser[tok] || (tok.startsWith('tok-') ? USERS[tok.slice(4)] : null);
  if (!u) return json({ message: 'no auth' }, 401);
  if (p.startsWith('/storage/v1/')) return json([]);
  if (p.startsWith('/rest/v1/rpc/')) { const fn = p.split('/').pop(); if (fn === 'mi_nombre') return json(u.name); if (fn.startsWith('admin_list')) return json([]); return json(null); }
  if (p.startsWith('/rest/v1/')) {
    const t = p.slice('/rest/v1/'.length); if (m !== 'GET') return route.fulfill({ status: 201, body: '' });
    const idq = url.searchParams.get('id');
    if (t === 'fund_data') return json(FUND.filter(r => (!idq || idq === 'eq.' + r.id) && (r.id === 'main' ? has(u, 'fondo') : r.id === 'reunion' ? has(u, 'reunion') : r.id === 'padron' ? true : has(u, 'companeros'))).map(r => Object.assign({ updated_at: '2026-11-20T10:00:00Z' }, r)));
    if (t === 'padron_user') return json([{ nombre: u.name }]);
    if (t === 'permisos') return json(PERMISOS[u.id] ? [PERMISOS[u.id]] : []);
    if (t === 'asistencia') return has(u, 'reunion') ? json([{ pkey: 'Figueredo Carlos Eduardo', created: '2026-11-01' }]) : json({ message: 'rls' }, 403);
    return json([]);
  }
  return json({}, 404);
}
const srv = http.createServer((q, r) => { if (q.url.split('?')[0] === '/') { r.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); r.end(fs.readFileSync(FILE)); } else { r.writeHead(404); r.end(); } });
let fails = 0; const errs = [];
const ok = (c, t) => { console.log((c ? 'OK   ' : 'FALLA') + ' · ' + t); if (!c) fails++; };
(async () => {
  await new Promise(r => srv.listen(8098, r));
  const browser = await chromium.launch();
  const newCtx = async vp => { const ctx = await browser.newContext({ viewport: vp || { width: 1280, height: 900 }, serviceWorkers: 'block' });
    await ctx.route('**/*', r => { const u = r.request().url(); if (u.startsWith('http://localhost:8098')) return r.continue(); if (u.startsWith(SUPA)) return supa(r); return r.abort(); }); return ctx; };
  const watch = (pg, tag) => pg.on('pageerror', e => errs.push(tag + ': ' + e.message));
  const login = async (pg, mat) => { await pg.click('#btn-acceder'); await pg.fill('#login-leg', mat); await pg.fill('#login-pass', 'Clave.123'); await pg.click('#login-btn');
    await pg.waitForFunction(() => !document.body.classList.contains('locked') && !document.body.classList.contains('booting'), null, { timeout: 45000 }); await pg.waitForTimeout(1500); };
  const vis = (pg, sel) => pg.evaluate(s => { const e = document.querySelector(s); if (!e) return false; const r = e.getBoundingClientRect(); return getComputedStyle(e).display !== 'none' && r.height > 0; }, sel);
  const opts = pg => pg.$$eval('#cb-opts .cb-opt', b => b.map(x => x.textContent));
  const say = async (pg, lab) => { await pg.click('#cb-opts .cb-opt >> text="' + lab + '"'); await pg.waitForTimeout(700); };
  const last = pg => pg.$$eval('#cb-log .cb-row:not(.me) .cb-msg', b => b[b.length - 1].innerText);

  const html = fs.readFileSync(FILE, 'utf8');
  ok(/chatbot-2711/.test(html), 'parche presente');
  ok(!/0000060400|LaXVIIenObera/i.test(html), 'HTML público: sin CVU ni alias');

  let ctx = await newCtx(), pg = await ctx.newPage(); watch(pg, 'portada');
  await pg.goto('http://localhost:8098/'); await pg.waitForTimeout(1200);
  ok(!(await vis(pg, '#cb-fab')), 'portada: sin botón del chat');
  await ctx.close();

  // compañero full con deuda
  ctx = await newCtx(); pg = await ctx.newPage(); watch(pg, 'full');
  await pg.goto('http://localhost:8098/'); await login(pg, '1');
  ok(await vis(pg, '#cb-fab'), 'full: botón del pirata visible');
  await pg.click('#cb-fab'); await pg.waitForTimeout(700);
  ok(await vis(pg, '#cb-panel'), 'full: abre el panel');
  const o1 = await opts(pg);
  ok(['📅 La reunión', '💰 Mi cuenta en el fondo', '📊 El fondo', '👥 Compañeros', '📷 Fotos y recuerdos', '🛟 Ayuda con la página'].every(x => o1.includes(x)), 'full: menú completo (' + o1.join(' | ') + ')');
  ok((await last(pg)).includes('Carlos'), 'full: saluda por el nombre');
  await pg.screenshot({ path: SHOTS + '/1_menu.png' });
  await say(pg, '📅 La reunión'); await say(pg, '¿Cuándo es?');
  ok(/19 al lunes 22 de noviembre de 2027/.test(await last(pg)) && /Faltan/.test(await last(pg)), 'reunión: fecha y días que faltan');
  await say(pg, '¿Dónde es?'); ok((await last(pg)).includes('Lugar de prueba') && (await opts(pg)).includes('📍 Cómo llegar'), 'reunión: lugar y mapa desde la base');
  await say(pg, '⟵ Volver'); await say(pg, '¿Quiénes van?'); ok(/Confirmó 1 compañero:/.test(await last(pg)), 'reunión: confirmados desde asistencia');
  await pg.screenshot({ path: SHOTS + '/2_reunion.png' });
  await say(pg, '¿Estoy confirmado?'); ok(/ya estás confirmado/.test(await last(pg)), 'reunión: «¿estoy confirmado?» lo reconoce');
  await say(pg, '🏠 Inicio'); await say(pg, '💰 Mi cuenta en el fondo'); await say(pg, '¿Cuánto debo?');
  ok(/2 cuotas/.test(await last(pg)) && /\$40\.000/.test(await last(pg)), 'cuenta: deuda 2 cuotas = $40.000');
  await say(pg, '¿Cómo pago?');
  const pago = await last(pg);
  ok(pago.includes('0000099900000000000001') && pago.includes('ALIAS.PRUEBA.XVII'), 'cuenta: CVU y alias llegan de la base');
  await pg.screenshot({ path: SHOTS + '/3_pago.png' });
  await say(pg, '⟵ Volver'); await say(pg, '¿Cuánto debo?'); await say(pg, '🧾 Ver detalle con interés'); await pg.waitForTimeout(800);
  ok(!(await vis(pg, '#cb-panel')) && await vis(pg, '#view-deuda') && (await pg.textContent('#dz-res')).includes('turnos'), 'cuenta: «ver detalle» abre Consultá tu deuda con su nombre');
  await pg.click('#cb-fab'); await pg.waitForTimeout(300);
  await say(pg, '🏠 Inicio'); await say(pg, '📊 El fondo'); await say(pg, '¿Cuánto hay?'); ok(/\$900/.test(await last(pg)), 'fondo: valor actual');
  await say(pg, '⟵ Volver'); await say(pg, '¿En qué está invertido?'); ok((await last(pg)).includes('Caución'), 'fondo: cartera');
  await say(pg, '🏠 Inicio'); await say(pg, '🛟 Ayuda con la página'); await say(pg, '📲 Instalar en el celular'); ok(/Agregar a inicio/.test(await last(pg)), 'ayuda: instalar');
  await ctx.close();

  // restringido: sin fondo ni reunión
  ctx = await newCtx({ width: 390, height: 844 }); pg = await ctx.newPage(); watch(pg, 'restringido');
  await pg.goto('http://localhost:8098/'); await login(pg, '2');
  await pg.click('#cb-fab'); await pg.waitForTimeout(700);
  const o2 = await opts(pg);
  ok(!o2.some(x => /reunión|fondo|Compañeros/.test(x)) && o2.includes('📷 Fotos y recuerdos'), 'restringido: sin Reunión, Fondo ni Compañeros (' + o2.join(' | ') + ')');
  ok(await pg.evaluate(() => !window.CVU), 'restringido: sin CVU en memoria');
  await say(pg, '📷 Fotos y recuerdos'); ok(!(await opts(pg)).includes('📝 Dejar una historia'), 'restringido: sin historias');
  await pg.screenshot({ path: SHOTS + '/4_restringido_celular.png' });
  await ctx.close();

  // admin al día, en celular
  ctx = await newCtx({ width: 390, height: 844 }); pg = await ctx.newPage(); watch(pg, 'admin');
  await pg.goto('http://localhost:8098/'); await login(pg, '117');
  await pg.screenshot({ path: SHOTS + '/5_boton_celular.png' });
  await pg.click('#cb-fab'); await pg.waitForTimeout(700);
  await say(pg, '💰 Mi cuenta en el fondo'); await say(pg, '¿Cuánto debo?');
  ok(/Estás al día/.test(await last(pg)), 'admin: al día');
  await say(pg, '¿Cómo pago?');
  await pg.screenshot({ path: SHOTS + '/6_admin_celular.png' });
  await say(pg, '🏠 Inicio'); await say(pg, '📅 La reunión'); await say(pg, '¿Estoy confirmado?');
  ok(/no confirmaste/.test(await last(pg)), 'admin: no confirmado → ofrece confirmar');
  await say(pg, '✋ Confirmar ahora'); await pg.waitForTimeout(700);
  ok(await pg.evaluate(() => document.getElementById('rsvp-modal').classList.contains('open')), 'admin: «Confirmar ahora» abre ¿Venís?');
  await ctx.close();

  await browser.close(); srv.close();
  console.log('Errores de pagina: ' + (errs.length ? errs.join(' | ') : 'ninguno'));
  console.log(fails ? fails + ' FALLAS' : 'TODO OK');
  process.exit(fails || errs.length ? 1 : 0);
})().catch(e => { console.error(e); srv.close(); process.exit(2); });
