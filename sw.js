const CACHE_NAME = "typing-test-shell-v3";
const SHELL_URLS = [
  "/",
  "/manifest.json",
  "/static/app.js?v=20261102-linebyline",
  "/static/pwa.js",
  "/static/style.css?v=20261102-linebyline",
  "/static/brand.svg",
  "/apple-touch-icon.png",
  "/icon-192.png",
  "/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(SHELL_URLS))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith("typing-test-shell-") && key !== CACHE_NAME)
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin) return;

  // Account, message, challenge, and uploaded-media responses are always network-only.
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/media/")) return;

  if (request.mode === "navigate") {
    event.respondWith(
      (async () => {
        try {
          const response = await fetch(request);
          if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            await cache.put("/", response.clone());
          }
          return response;
        } catch {
          return (await caches.match("/")) || Response.error();
        }
      })(),
    );
    return;
  }

  const isShellAsset =
    url.pathname.startsWith("/static/") ||
    ["/manifest.json", "/apple-touch-icon.png", "/icon-192.png", "/icon-512.png"].includes(
      url.pathname,
    );
  if (!isShellAsset) return;

  event.respondWith(
    (async () => {
      try {
        const response = await fetch(request);
        if (response.ok) {
          const cache = await caches.open(CACHE_NAME);
          await cache.put(request, response.clone());
        }
        return response;
      } catch {
        return (await caches.match(request)) || Response.error();
      }
    })(),
  );
});
