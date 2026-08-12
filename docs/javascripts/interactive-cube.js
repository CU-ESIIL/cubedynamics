(function () {
  "use strict";

  var cleanupCubes = function () {};

  function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
  }

  function initializeCube(root) {
    var scene = root.querySelector(".cd-cube-scene");
    var cube = root.querySelector("[data-cd-cube-object]");
    var reset = root.querySelector("[data-cd-cube-reset]");
    var status = root.querySelector("[data-cd-cube-status]");

    if (!scene || !cube || !reset) return function () {};

    var controller = new AbortController();
    var signal = controller.signal;
    var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    var rotationX = -18;
    var rotationY = 32;
    var scrollTurn = 0;
    var pointerId = null;
    var previousX = 0;
    var previousY = 0;
    var scrollFrame = 0;

    function render() {
      cube.style.setProperty("--cube-rx", rotationX.toFixed(2) + "deg");
      cube.style.setProperty("--cube-ry", rotationY.toFixed(2) + "deg");
      cube.style.setProperty("--cube-scroll", scrollTurn.toFixed(2) + "deg");
    }

    function announce() {
      if (!status) return;
      status.textContent =
        "Cube view: " + Math.round(rotationX) + " degrees vertical and " +
        Math.round(rotationY + scrollTurn) + " degrees horizontal.";
    }

    function updateFromScroll() {
      scrollFrame = 0;
      if (reducedMotion.matches) {
        scrollTurn = 0;
        render();
        return;
      }

      var hero = root.closest(".cd-hero-art");
      if (!hero) return;
      var bounds = hero.getBoundingClientRect();
      var travel = window.innerHeight + bounds.height;
      var progress = clamp((window.innerHeight - bounds.top) / travel, 0, 1);
      scrollTurn = (progress - 0.5) * 108;
      render();
    }

    function scheduleScrollUpdate() {
      if (!scrollFrame) scrollFrame = window.requestAnimationFrame(updateFromScroll);
    }

    function finishPointer(event) {
      if (event.pointerId !== pointerId) return;
      pointerId = null;
      root.classList.remove("is-dragging");
      announce();
    }

    scene.addEventListener("pointerdown", function (event) {
      if (event.button !== 0) return;
      pointerId = event.pointerId;
      previousX = event.clientX;
      previousY = event.clientY;
      scene.setPointerCapture(pointerId);
      root.classList.add("is-dragging");
    }, { signal: signal });

    scene.addEventListener("pointermove", function (event) {
      if (event.pointerId !== pointerId) return;
      var deltaX = event.clientX - previousX;
      var deltaY = event.clientY - previousY;
      previousX = event.clientX;
      previousY = event.clientY;
      rotationY += deltaX * 0.38;
      rotationX = clamp(rotationX - deltaY * 0.3, -72, 72);
      render();
    }, { signal: signal });

    scene.addEventListener("pointerup", finishPointer, { signal: signal });
    scene.addEventListener("pointercancel", finishPointer, { signal: signal });

    scene.addEventListener("keydown", function (event) {
      var handled = true;
      if (event.key === "ArrowLeft") rotationY -= 8;
      else if (event.key === "ArrowRight") rotationY += 8;
      else if (event.key === "ArrowUp") rotationX = clamp(rotationX - 8, -72, 72);
      else if (event.key === "ArrowDown") rotationX = clamp(rotationX + 8, -72, 72);
      else if (event.key === "Home") {
        rotationX = -18;
        rotationY = 32;
      } else handled = false;

      if (!handled) return;
      event.preventDefault();
      render();
      announce();
    }, { signal: signal });

    reset.addEventListener("click", function () {
      rotationX = -18;
      rotationY = 32;
      render();
      scene.focus();
      announce();
    }, { signal: signal });

    window.addEventListener("scroll", scheduleScrollUpdate, { passive: true, signal: signal });
    window.addEventListener("resize", scheduleScrollUpdate, { passive: true, signal: signal });
    reducedMotion.addEventListener("change", scheduleScrollUpdate, { signal: signal });

    root.dataset.cubeReady = "true";
    updateFromScroll();

    return function () {
      if (scrollFrame) window.cancelAnimationFrame(scrollFrame);
      controller.abort();
    };
  }

  function initializeAllCubes() {
    cleanupCubes();
    var cleanups = Array.from(document.querySelectorAll("[data-cd-cube]")).map(initializeCube);
    cleanupCubes = function () {
      cleanups.forEach(function (cleanup) { cleanup(); });
    };
  }

  if (typeof document$ !== "undefined") {
    document$.subscribe(initializeAllCubes);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeAllCubes, { once: true });
  } else {
    initializeAllCubes();
  }
}());
