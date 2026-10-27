// 网络优先的 Service Worker：保证拿到最新版，同时支持离线回退和 PWA 安装。
const CACHE = "math-tutor-v2";
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== location.origin) return; // 跨域不拦截
  event.respondWith(
    fetch(event.request)
      .then((resp) => {
        if (resp && resp.status === 200) {
          const cl = resp.clone();
          caches.open(CACHE).then((c) => c.put(event.request, cl));
        }
        return resp;
      })
      .catch(() => caches.match(event.request))
  );
});
