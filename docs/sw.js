// Bump VERSION on every deploy (scripts/bump_version.py does it) so phones pick up the new app shell.
const VERSION = "2";
const SHELL_CACHE = `hskfc-shell-v${VERSION}`;
const DATA_CACHE = "hskfc-data"; // level files; kept across versions and refreshed in the background
const SHELL = [
  "./",
  "index.html",
  "styles.css",
  "app.js",
  "js/storage.js",
  "js/check.js",
  "js/speech.js",
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

  event.respondWith(
    caches.match(req, { ignoreSearch: true }).then((hit) => {
      if (hit) return hit;
      return fetch(req).catch(() => (req.mode === "navigate" ? caches.match("index.html") : Response.error()));
    })
  );
});
