import Cookies from "@nationalarchives/cookies";
import { initAll } from "@nationalarchives/frontend/nationalarchives/all.mjs";

const cookies = new Cookies();

const setTheme = (theme) => {
  document.documentElement.classList.remove("tna-template--dark-theme");
  document.documentElement.classList.remove("tna-template--system-theme");
  if (["dark", "system"].includes(theme)) {
    document.documentElement.classList.add(`tna-template--${theme}-theme`);
  }
};

const appendDateToLogoAdornments = () => {
  const now = new Date();
  /* eslint-disable no-magic-numbers */
  const iso8601DateString = `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}-${String(now.getUTCDate()).padStart(2, "0")}`;
  const logoAdornmentsCss = document.getElementById("logo-adornments-css");
  if (logoAdornmentsCss) {
    logoAdornmentsCss.setAttribute(
      "href",
      `${logoAdornmentsCss.getAttribute("href")}?date=${iso8601DateString}`,
    );
  }
  const logoAdornmentsJs = document.getElementById("logo-adornments-js");
  if (logoAdornmentsJs) {
    logoAdornmentsJs.setAttribute(
      "src",
      `${logoAdornmentsJs.getAttribute("src")}?date=${iso8601DateString}`,
    );
  }
};

document.addEventListener("DOMContentLoaded", () => {
  initAll();

  if (cookies.exists("theme")) {
    setTheme(cookies.get("theme"));
  } else {
    setTheme("system");
  }

  appendDateToLogoAdornments();
});
