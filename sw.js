/* La XVII · service worker
   - Solo maneja archivos del propio sitio (laxvii.com.ar).
   - NUNCA intercepta ni guarda respuestas de Supabase ni de otros dominios:
     las cifras del fondo, fotos y datos de compañeros siempre van por red y con login.
   - La página (index.html, sin cifras) se pide primero a la red; la copia guardada
     solo se usa si no hay conexión. */
const VERSION = 'laxvii-v3';
const SHELL = ['/', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png',
               '/icon-maskable-512.png', '/apple-touch-icon.png', '/favicon-32.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

const OFFLINE = '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
  + '<title>La XVII · sin conexión</title><body style="margin:0;min-height:100vh;display:flex;align-items:center;'
  + 'justify-content:center;background:#e7d9b6;font-family:system-ui,sans-serif;text-align:center;color:#1d1d1b">'
  + '<div><img src="/icon-192.png" width="120" height="120" alt=""><h1 style="margin:12px 0 6px">Sin conexión</h1>'
  + '<p>La XVII necesita internet. Probá de nuevo en un rato.</p>'
  + '<button onclick="location.reload()" style="font:600 16px system-ui;padding:12px 28px;border:0;border-radius:99px;'
  + 'background:#b4342f;color:#fff">Reintentar</button></div>';

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;          // Supabase, fuentes, etc.: no se tocan

  if (req.mode === 'navigate') {                            // la página: red primero
    e.respondWith(
      fetch(req).then(res => {
        if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put('/', copy)); }
        return res;
      }).catch(() => caches.match('/').then(r => r || new Response(OFFLINE,
        { headers: { 'Content-Type': 'text/html; charset=utf-8' } })))
    );
    return;
  }
  if (SHELL.includes(url.pathname)) {                       // íconos y manifest: copia guardada
    e.respondWith(caches.match(req).then(r => r || fetch(req)));
  }
});
