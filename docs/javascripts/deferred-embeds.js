(() => {
  const initialize = () => {
    document.querySelectorAll("[data-deferred-embed]").forEach((wrapper) => {
      if (wrapper.dataset.initialized === "true") return;
      wrapper.dataset.initialized = "true";

      let frame = wrapper.querySelector("iframe[data-src]");
      if (!frame) return;

      let requestedSource = "";
      let onLoad;
      let timeout;
      const button = wrapper.querySelector("button");
      const load = (force = false) => {
        const source = new URL(frame.dataset.src, document.baseURI).href;
        if (!force && source === requestedSource && (wrapper.dataset.loading === "true" || wrapper.dataset.loaded === "true")) return;
        if (onLoad) frame.removeEventListener("load", onLoad);
        window.clearTimeout(timeout);
        if (requestedSource && (force || source !== requestedSource)) {
          // A fresh browsing context cancels an older in-flight navigation,
          // including a quick A → B → A switch before B has finished loading.
          const replacement = frame.cloneNode(false);
          replacement.src = "about:blank";
          frame.replaceWith(replacement);
          frame = replacement;
        }
        requestedSource = source;
        const activeFrame = frame;
        wrapper.dataset.loading = "true";
        wrapper.dataset.loaded = "false";
        wrapper.setAttribute("aria-busy", "true");
        onLoad = () => {
          if (frame !== activeFrame) return;
          // Ignore the initial about:blank event and superseded navigations.
          try {
            if (frame.contentWindow.location.href !== source) return;
          } catch (_) { /* Cross-origin embeds cannot expose their location. */ }
          frame.removeEventListener("load", onLoad);
          window.clearTimeout(timeout);
          wrapper.dataset.loaded = "true";
          wrapper.dataset.loading = "false";
          wrapper.setAttribute("aria-busy", "false");
        };
        frame.addEventListener("load", onLoad);
        timeout = window.setTimeout(() => {
          wrapper.dataset.loading = "false";
          wrapper.setAttribute("aria-busy", "false");
          if (button) button.textContent = "Retry loading viewer";
        }, 15000);
        frame.src = source;
      };

      wrapper.setAttribute("aria-busy", "true");
      button?.addEventListener("click", () => load(true));
      wrapper.addEventListener("cd:embed-load", () => load());

      const schedule = () => {
        if ("requestIdleCallback" in window) {
          window.requestIdleCallback(() => load(), { timeout: 900 });
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
