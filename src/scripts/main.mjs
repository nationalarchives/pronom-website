import Cookies from "@nationalarchives/cookies";
import { initAll } from "@nationalarchives/frontend/nationalarchives/all.mjs";

const cookies = new Cookies();

const setTheme = (theme) => {
  document.documentElement.classList.remove(
    "tna-template--dark-theme",
    "tna-template--system-theme",
  );
  if (["dark", "system"].includes(theme)) {
    document.documentElement.classList.add(`tna-template--${theme}-theme`);
  }
};

document.addEventListener("DOMContentLoaded", () => {
  initAll();

  if (cookies.exists("theme")) {
    setTheme(cookies.get("theme"));
  } else {
    setTheme("system");
  }
});
