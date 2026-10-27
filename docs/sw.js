const CACHE = "math-tutor-web-v3";
const ASSETS = ["./", "./index.html", "./manifest.json", "./solver.py", "./icons/icon-192.png", "./icons/icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (url.origin === location.origin) {
    e.respondWith(
      caches.match(e.request).then((hit) => {
        const net = fetch(e.request).then((resp) => {
          if (resp && resp.status === 200) { const cl = resp.clone(); caches.open(CACHE).then((c) => c.put(e.request, cl)); }
          return resp;
        });
        return hit || net;
      })
    );
  }
  // 跨域（KaTeX/Pyodide/DeepSeek）不拦截
});
