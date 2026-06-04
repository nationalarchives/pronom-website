document.addEventListener("DOMContentLoaded", () => {
  window.TNAFrontend.initAll();

  const cookies = new window.TNAFrontend.Cookies();

  const setTheme = (theme) => {
    document.documentElement.classList.remove("tna-template--dark-theme");
    document.documentElement.classList.remove("tna-template--system-theme");
    if (["dark", "system"].includes(theme)) {
      document.documentElement.classList.add(`tna-template--${theme}-theme`);
    }
  };
  let theme = "system";
  if (cookies.exists("theme")) {
    theme = cookies.get("theme");
  }
  setTheme(theme);
});
