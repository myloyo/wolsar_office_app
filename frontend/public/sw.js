// Cache public interface assets only. API responses and personal data stay on the network.
const CACHE = 'wolsar-shell-v2';
self.addEventListener('install', event => {
  event.waitUntil(Promise.all([self.skipWaiting(), caches.open(CACHE).then(cache => cache.addAll(['/','/icon-192.png']))]));
});
self.addEventListener('activate', event => {
  event.waitUntil(Promise.all([self.clients.claim(), caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('wolsar-shell-') && key !== CACHE).map(key => caches.delete(key))))]));
});
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return;
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match('/').then(response => response || Response.error())));
  } else if (/^\/assets\/.*\.(js|css)$/.test(url.pathname)) {
    event.respondWith(caches.open(CACHE).then(async cache => {
      const cached = await cache.match(request);
      if (cached) return cached;
      const response = await fetch(request);
      if (response.ok) await cache.put(request, response.clone());
      return response;
    }));
  }
});

self.addEventListener('push', event => {
  let data = {title: 'СЖ Саратов', href: '/notifications'};
  try { data = {...data, ...event.data.json()}; } catch { /* use generic message */ }
  const target = new URL(data.href, self.location.origin);
  event.waitUntil(self.registration.showNotification(data.title, {
    body: 'Откройте приложение, чтобы посмотреть обновление.',
    icon: '/icon-192.png', tag: String(data.id || data.href), data: {href: target.origin === self.location.origin ? target.href : '/notifications'}
  }));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = new URL(event.notification.data?.href || '/notifications', self.location.origin);
  if (target.origin !== self.location.origin) return;
  event.waitUntil(clients.matchAll({type: 'window', includeUncontrolled: true}).then(async windows => {
    const existing = windows.find(client => new URL(client.url).origin === self.location.origin);
    if (existing) { await existing.navigate(target.href); await existing.focus(); }
    else await clients.openWindow(target.href);
  }));
});
