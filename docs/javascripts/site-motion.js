(() => {
  let ticking = false;

  const update = () => {
    document.querySelectorAll("[data-parallax]").forEach((element) => {
      const rect = element.getBoundingClientRect();
      const offset = Math.max(-60, Math.min(60, (window.innerHeight / 2 - rect.top) * 0.07));
      element.style.setProperty("--cd-parallax", `${offset}px`);
    });
    ticking = false;
  };

  const requestUpdate = () => {
    if (!ticking) {
      window.requestAnimationFrame(update);
      ticking = true;
    }
  };

  const initialize = () => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    requestUpdate();
  };

  window.addEventListener("scroll", requestUpdate, { passive: true });
  window.addEventListener("resize", requestUpdate, { passive: true });
  if (typeof document$ !== "undefined") document$.subscribe(initialize);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize);
  else initialize();
})();
