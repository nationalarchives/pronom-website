import { test } from "@playwright/test";
import { checkAccessibility, validateHtml } from "./lib.ts";

test("page has no accessibility issues", async ({ page }) => {
  await page.goto("/about");
  await checkAccessibility(page);
});

test("page has valid HTML", async ({ page }) => {
  await page.goto("/about");
  await validateHtml(page);
});
