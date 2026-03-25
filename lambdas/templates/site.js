document.addEventListener("DOMContentLoaded", function () {
  window.TNAFrontend.initAll();

  const cookies = new window.TNAFrontend.Cookies();

  const setTheme = (theme) => {
    document.documentElement.classList.remove("tna-template--dark-theme");
    document.documentElement.classList.remove("tna-template--system-theme");
    if (["dark", "system"].includes(theme)) {
      document.documentElement.classList.add(`tna-template--${theme}-theme`);
    }
  };

  setTheme(cookies.exists("theme") ? cookies.get("theme") : "system");
});
