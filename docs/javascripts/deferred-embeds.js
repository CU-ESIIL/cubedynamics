(() => {
  const initialize = () => {
    document.querySelectorAll("[data-deferred-embed]").forEach((wrapper) => {
      if (wrapper.dataset.initialized === "true") return;
      wrapper.dataset.initialized = "true";

      const frame = wrapper.querySelector("iframe[data-src]");
      if (!frame) return;

      const load = () => {
        if (wrapper.dataset.loading === "true" || wrapper.dataset.loaded === "true") return;
        wrapper.dataset.loading = "true";
        frame.addEventListener("load", () => {
          wrapper.dataset.loaded = "true";
          wrapper.setAttribute("aria-busy", "false");
        }, { once: true });
        frame.src = frame.dataset.src;
      };

      wrapper.setAttribute("aria-busy", "true");
      wrapper.querySelector("button")?.addEventListener("click", load);

      const schedule = () => {
        if ("requestIdleCallback" in window) {
          window.requestIdleCallback(load, { timeout: 900 });
        } else {
          window.setTimeout(load, 300);
        }
      };

      if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver((entries) => {
          if (entries.some((entry) => entry.isIntersecting)) {
            observer.disconnect();
            schedule();
          }
        }, { rootMargin: "220px" });
        observer.observe(wrapper);
      } else {
        schedule();
      }
    });
  };

  if (typeof document$ !== "undefined") document$.subscribe(initialize);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize);
  else initialize();
})();
