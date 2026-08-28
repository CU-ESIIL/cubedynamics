(() => {
  const initialize = () => {
    const select = document.getElementById("hero-cube-example");
    if (!select || select.dataset.initialized) return;
    const hero = select.closest(".cd-html-cube-hero");
    const wrapper = hero.querySelector("[data-deferred-embed]");
    const describe = () => {
      const frame = wrapper.querySelector("iframe");
      const option = select.selectedOptions[0];
      frame.dataset.src = option.value;
      frame.title = option.dataset.title;
      hero.querySelector("#hero-cube-description").textContent = option.dataset.description;
      hero.querySelector("#hero-cube-kind").textContent = option.dataset.kind === "hull"
        ? "Specialized fire hull · Plotly" : "Interactive raster cube";
      hero.querySelector("#hero-cube-open").href = option.value;
      hero.querySelector("#hero-cube-lesson").href = option.dataset.lesson;
      wrapper.querySelector(".cd-embed-loader strong").textContent = option.textContent;
    };
    select.dataset.initialized = "true";
    select.disabled = false;
    describe();
    select.addEventListener("change", () => {
      describe();
      // Replace the one active iframe document, never preload the full gallery.
      wrapper.dispatchEvent(new Event("cd:embed-load"));
    });
  };
  if (typeof document$ !== "undefined") document$.subscribe(initialize);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize);
  else initialize();
})();
