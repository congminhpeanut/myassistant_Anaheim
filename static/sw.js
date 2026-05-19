const CACHE_NAME = 'anaheim-guide-v2';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json'
];

const CACHE_API_ROUTES = [
  '/api/overview',
  '/api/airport',
  '/api/transport',
  '/api/hotels',
  '/api/schedule',
  '/api/food',
  '/api/emergency',
  '/api/activities',
  '/api/daily-plan',
  '/api/links'
];

const NETWORK_ONLY_ROUTES = [
  '/api/chat',
  '/api/navigate'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (NETWORK_ONLY_ROUTES.includes(url.pathname)) {
    event.respondWith(fetch(request));
    return;
  }

  if (CACHE_API_ROUTES.includes(url.pathname)) {
    event.respondWith(
      fetch(request)
        .then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
          return response;
        })
        .catch(() => caches.match(request).then(cached => cached || new Response(JSON.stringify({offline:true}), {headers:{'Content-Type':'application/json'}})))
    );
    return;
  }

  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached;
      return fetch(request).then(response => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
        return response;
      });
    })
  );
});
