// Bump VERSION on every deploy (scripts/bump_version.py does it) so phones pick up the new app shell.
const VERSION = "7";
const SHELL_CACHE = `hskfc-shell-v${VERSION}`;
const DATA_CACHE = "hskfc-data"; // level files; kept across versions and refreshed in the background
const BANK_CACHE = "hskfc-bank"; // encrypted question bank (bank/…): clips cache-first, meta/index network-first; kept across versions
const HANZI_CACHE = "hskfc-hanzi"; // stroke data hanzi/{char}.json, cache-first, stored on first use; kept across versions
const SHELL = [
  "./",
  "index.html",
  "styles.css",
  "app.js",
  "js/storage.js",
  "js/check.js",
  "js/speech.js",
  "js/writing.js",
  "js/strokematch.js",
  "js/bank.js",
  "js/bankcore.js",
  "js/bankcrypto.js",
  "vendor/hanzi-writer.min.js",
  "manifest.webmanifest",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "icons/apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith("hskfc-shell-") && k !== SHELL_CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== self.location.origin) return;

  if (/\/data\/hsk\d\.json$/.test(url.pathname)) {
    // stale-while-revalidate: instant/offline from cache, fresh copy stored for next time
    event.respondWith(
      caches.open(DATA_CACHE).then(async (cache) => {
        const cached = await cache.match(req);
        const network = fetch(req).then((res) => {
          if (res.ok) cache.put(req, res.clone());
          return res;
        });
        if (cached) { network.catch(() => {}); return cached; }
        return network;
      })
    );
    return;
  }

  if (/\/bank\/.+/.test(url.pathname)) {
    const small = /\/(meta\.json|index\.bin)$/.test(url.pathname);
    event.respondWith(
      caches.open(BANK_CACHE).then(async (cache) => {
        if (small) { // fresh when online, the cached copy when offline
          try {
            const res = await fetch(req, { cache: "no-cache" });
            if (res.ok) cache.put(req, res.clone());
            return res;
          } catch (err) {
            const cached = await cache.match(req);
            if (cached) return cached;
            throw err;
          }
        }
        const cached = await cache.match(req);
        if (cached) return cached;
        const res = await fetch(req);
        if (res.ok) cache.put(req, res.clone());
        return res;
      })
    );
    return;
  }

  if (/\/hanzi\/[^/]+\.json$/.test(url.pathname)) {
    event.respondWith(
      caches.open(HANZI_CACHE).then(async (cache) => {
        const cached = await cache.match(req);
        if (cached) return cached;
        const res = await fetch(req);
        if (res.ok) cache.put(req, res.clone());
        return res;
      })
    );
    return;
  }

  event.respondWith(
    caches.match(req, { ignoreSearch: true }).then((hit) => {
      if (hit) return hit;
      return fetch(req).catch(() => (req.mode === "navigate" ? caches.match("index.html") : Response.error()));
    })
  );
});
