// 自毁式 Service Worker：安装后立即清空所有缓存并注销自己，
// 让网站永远从网络取最新版，避免旧缓存导致页面停留在旧版本。
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.map((k) => caches.delete(k))))
      .then(() => self.registration.unregister())
  );
});
