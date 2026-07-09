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

// document
//   .querySelectorAll('[data-module="filter-container"]')
//   /* eslint-disable max-statements */
//   .forEach((filterContainer) => {
//     const filterInput = filterContainer.querySelector(".filter-input");
//     const filteredCount = filterContainer.querySelector(".filtered-count");
//     const filterTarget = filterContainer.dataset.filterTarget
//       ? document.getElementById(filterContainer.dataset.filterTarget)
//       : null;
//     const filterAttribute = filterContainer.dataset.filterAttribute || "";
//     if (!filterInput || !filteredCount || !filterTarget || !filterAttribute) {
//       return;
//     }
//     const filterTargetChildren = (
//       filterTarget ? Array.from(filterTarget.children) : []
//     ).map((child) => ({
//       $el: child,
//       attributeValues: (child.getAttribute(filterAttribute) || "")
//         .split(",")
//         .map((value) => value.trim().toLowerCase()),
//     }));
//     if (filterTargetChildren.length === 0) {
//       return;
//     }
//     filterInput.addEventListener("keyup", () => {
//       const filterValue = filterInput.value.toLowerCase();
//       let visibleCount = 0;
//       filterTargetChildren.forEach((child) => {
//         if (
//           child.attributeValues.some((value) => value.includes(filterValue))
//         ) {
//           child.$el.removeAttribute("hidden");
//           visibleCount += 1;
//         } else {
//           child.$el.setAttribute("hidden", "true");
//         }
//       });
//       filteredCount.textContent = `Showing ${visibleCount} of ${filterTargetChildren.length} items.`;
//     });
//     filteredCount.textContent = `Showing ${filterTargetChildren.length} of ${filterTargetChildren.length} items.`;
//     filterContainer.removeAttribute("hidden");
//   });
