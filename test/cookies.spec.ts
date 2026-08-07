import { test, expect } from "@playwright/test";

test("cookie banner shows on all pages", async ({ page }) => {
  await page.goto("/");
  expect(
    await page.getByRole("region", { name: "Cookies on PRONOM" }),
  ).toBeVisible();
  expect(
    await page.locator(".tna-footer__theme-selector-notice"),
  ).toBeVisible();

  await page.goto("/about");
  expect(
    await page.getByRole("region", { name: "Cookies on PRONOM" }),
  ).toBeVisible();

  await page.goto("/search");
  expect(
    await page.getByRole("region", { name: "Cookies on PRONOM" }),
  ).toBeVisible();
});

test("cookie banner can be dismissed", async ({ page }) => {
  await page.goto("/");
  expect(
    await page.getByRole("region", { name: "Cookies on PRONOM" }),
  ).toBeVisible();
  expect(
    await page.locator(".tna-footer__theme-selector-notice"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Accept cookies" }).click();
  expect(
    await page.getByRole("region", { name: "Cookies on PRONOM" }),
  ).not.toBeVisible();

  await page.goto("/");
  expect(
    await page.getByRole("region", { name: "Cookies on PRONOM" }),
  ).not.toBeVisible();
  expect(await page.locator(".tna-footer__theme-selector-notice")).toBeHidden();

  await page.goto("/about");
  expect(
    await page.getByRole("region", { name: "Cookies on PRONOM" }),
  ).not.toBeVisible();

  await page.goto("/search");
  expect(
    await page.getByRole("region", { name: "Cookies on PRONOM" }),
  ).not.toBeVisible();
});
