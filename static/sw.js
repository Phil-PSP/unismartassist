/**
 * KAAF AI Service Worker
 * Handles: offline caching, background sync, push notifications
 */

const CACHE_NAME = 'kaaf-v1';
const OFFLINE_URL = '/offline/';

// Resources to cache immediately on install
const PRECACHE = [
  '/',
  '/dashboard/',
  '/chatbot/',
  '/students/results/',
  '/students/timetable/',
  '/notifications/',
  '/planner/',
  '/offline/',
  '/static/manifest.json',
  '/static/my-logo.png',
  'https://cdn.tailwindcss.com',
  'https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap',
];

// ── Install ────────────────────────────────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      // Cache what we can, ignore failures for external resources
      return Promise.allSettled(
        PRECACHE.map(url => cache.add(url).catch(() => {}))
      );
    }).then(() => self.skipWaiting())
  );
});

// ── Activate ───────────────────────────────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// ── Fetch ──────────────────────────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET, WebSocket, and admin requests
  if (request.method !== 'GET') return;
  if (url.pathname.startsWith('/admin/')) return;
  if (url.protocol === 'ws:' || url.protocol === 'wss:') return;

  // API calls — network first, no cache
  if (url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/chatbot/send/') ||
      url.pathname.startsWith('/chatbot/feedback/')) {
    event.respondWith(
      fetch(request).catch(() =>
        new Response(JSON.stringify({ error: 'offline', response: 'You are offline. Please check your connection.' }),
          { headers: { 'Content-Type': 'application/json' } })
      )
    );
    return;
  }

  // HTML pages — network first, fall back to cache, then offline page
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          // Cache successful page responses
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
          }
          return response;
        })
        .catch(() =>
          caches.match(request)
            .then(cached => cached || caches.match(OFFLINE_URL))
        )
    );
    return;
  }

  // Static assets — cache first, then network
  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached;
      return fetch(request).then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
        }
        return response;
      }).catch(() => new Response('', { status: 408 }));
    })
  );
});

// ── Background Sync ────────────────────────────────────────────────────────────
self.addEventListener('sync', event => {
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncQueuedMessages());
  }
});

async function syncQueuedMessages() {
  const db = await openDB();
  const messages = await getAllFromDB(db, 'message-queue');
  for (const item of messages) {
    try {
      const response = await fetch('/chatbot/send/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': item.csrf,
        },
        body: JSON.stringify({ message: item.message, session_id: item.session_id }),
      });
      if (response.ok) {
        await deleteFromDB(db, 'message-queue', item.id);
        // Notify the page
        const clients = await self.clients.matchAll();
        clients.forEach(client => client.postMessage({
          type: 'sync-complete',
          message: item.message,
          response: response,
        }));
      }
    } catch (e) {
      // Will retry on next sync
    }
  }
}

// ── IndexedDB helpers ──────────────────────────────────────────────────────────
function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('kaaf-offline', 1);
    req.onupgradeneeded = e => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('message-queue')) {
        db.createObjectStore('message-queue', { keyPath: 'id', autoIncrement: true });
      }
    };
    req.onsuccess = e => resolve(e.target.result);
    req.onerror = () => reject(req.error);
  });
}

function getAllFromDB(db, store) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, 'readonly');
    const req = tx.objectStore(store).getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function deleteFromDB(db, store, id) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, 'readwrite');
    const req = tx.objectStore(store).delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

// ── Push Notifications ─────────────────────────────────────────────────────────
self.addEventListener('push', event => {
  const data = event.data?.json() || {};
  event.waitUntil(
    self.registration.showNotification(data.title || 'KAAF AI', {
      body: data.body || 'You have a new notification',
      icon: '/static/my-logo.png',
      badge: '/static/my-logo.png',
      data: { url: data.url || '/notifications/' },
      vibrate: [200, 100, 200],
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data?.url || '/dashboard/')
  );
});
