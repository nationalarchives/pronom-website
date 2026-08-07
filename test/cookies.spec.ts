import { test, expect } from "@playwright/test";

test("cookie banner shows on all pages", async ({ page }) => {
  await page.goto("/");
  await expect(await page.locator(".tna-cookie-banner")).toBeVisible();
  await expect(
    await page.locator(".tna-footer__theme-selector-notice"),
  ).toBeVisible();

  await page.goto("/about");
  await expect(await page.locator(".tna-cookie-banner")).toBeVisible();

  await page.goto("/search");
  await expect(await page.locator(".tna-cookie-banner")).toBeVisible();
});

test("cookie banner can be dismissed", async ({ page }) => {
  await page.goto("/");
  await expect(await page.locator(".tna-cookie-banner")).toBeVisible();
  await expect(
    await page.locator(".tna-footer__theme-selector-notice"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Accept cookies" }).click();
  await page.getByRole("button", { name: "Hide cookies message" }).click();
  await expect(await page.locator(".tna-cookie-banner")).not.toBeVisible();

  await page.goto("/");
  await expect(await page.locator(".tna-cookie-banner")).not.toBeVisible();
  await expect(await page.locator(".tna-footer__theme-selector-notice")).toBeHidden();

  await page.goto("/about");
  await expect(await page.locator(".tna-cookie-banner")).not.toBeVisible();

  await page.goto("/search");
  await expect(await page.locator(".tna-cookie-banner")).not.toBeVisible();
});
