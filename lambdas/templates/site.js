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
  if (cookies.exists("theme")) {
    setTheme(cookies.get("theme"));
  } else {
    setTheme("system");
  }
});

const now = new Date();
/* eslint-disable no-magic-numbers */
const iso8601DateString = `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}-${String(now.getUTCDate()).padStart(2, "0")}`;
const logoAdornmentsCss = document.getElementById("logo-adornments-css");
if (logoAdornmentsCss) {
  const url = logoAdornmentsCss.getAttribute("href");
  logoAdornmentsCss.setAttribute("href", `${url}?date=${iso8601DateString}`);
}
const logoAdornmentsJs = document.getElementById("logo-adornments-js");
if (logoAdornmentsJs) {
  const url = logoAdornmentsJs.getAttribute("src");
  logoAdornmentsJs.setAttribute("src", `${url}?date=${iso8601DateString}`);
}
