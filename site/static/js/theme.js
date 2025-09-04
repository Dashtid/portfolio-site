document.addEventListener("DOMContentLoaded", () => {
  const saved = localStorage.getItem("theme");
  const prefersDark =
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;
  const theme = saved || (prefersDark ? "dark" : "light");
  setTheme(theme);

  const btn = document.getElementById("themeToggle");
  if (btn) {
    updateBtn(btn, theme);
    btn.addEventListener("click", () => {
      const next =
        document.documentElement.getAttribute("data-theme") === "dark"
          ? "light"
          : "dark";
      setTheme(next);
      updateBtn(btn, next);
    });
  }

  function setTheme(t) {
    document.documentElement.setAttribute("data-theme", t);
    localStorage.setItem("theme", t);
  }
  function updateBtn(button, t) {
    button.textContent = t === "dark" ? "Light" : "Dark";
    button.classList.toggle("btn-outline-light", t === "dark");
    button.classList.toggle("btn-outline-dark", t !== "dark");
  }

  // Back to Top (shared across all pages)
  const backToTopBtn = document.getElementById("backToTopBtn");
  if (backToTopBtn) {
    const toggleBackToTop = () => {
      const show =
        document.body.scrollTop > 300 ||
        document.documentElement.scrollTop > 300;
      backToTopBtn.style.display = show ? "block" : "none";
    };
    window.addEventListener("scroll", toggleBackToTop);
    toggleBackToTop();
    backToTopBtn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }
});
