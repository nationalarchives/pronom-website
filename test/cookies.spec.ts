import { test, expect, describe } from "@playwright/test";
import { domainFromUrl } from "./lib";

test("cookie banner shows on all pages", async ({ page, context }) => {
  await context.clearCookies();
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

test("cookie banner can be dismissed", async ({ page, context }) => {
  await context.clearCookies();
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
  await expect(
    await page.locator(".tna-footer__theme-selector-notice"),
  ).toBeHidden();

  await page.goto("/about");
  await expect(await page.locator(".tna-cookie-banner")).not.toBeVisible();

  await page.goto("/search");
  await expect(await page.locator(".tna-cookie-banner")).not.toBeVisible();
});

test("cookie banner hidden if already set", async ({
  page,
  context,
  baseURL,
}) => {
  await context.clearCookies();
  await context.addCookies([
    {
      name: "cookie_preferences",
      value: JSON.stringify({
        settings: true,
        usage: true,
        marketing: true,
        essential: true,
      }),
      domain: domainFromUrl(baseURL || ""),
      path: "/",
    },
  ]);
  await context.addCookies([
    {
      name: "cookie_preferences_set",
      value: "true",
      domain: domainFromUrl(baseURL || ""),
      path: "/",
    },
  ]);
  await page.goto("/");
  await expect(await page.locator(".tna-cookie-banner")).not.toBeVisible();
  await expect(
    await page.locator(".tna-footer__theme-selector-notice"),
  ).not.toBeVisible();
});

describe("cookie banner shown if necessary", () => {
  test("invalid preferences set", async ({ page, context, baseURL }) => {
    await context.clearCookies();
    await context.addCookies([
      {
        name: "cookie_preferences",
        value: "foobar",
        domain: domainFromUrl(baseURL || ""),
        path: "/",
      },
    ]);
    await page.goto("/");
    await expect(await page.locator(".tna-cookie-banner")).toBeVisible();
  });

  test("invalid preferences set and declared", async ({
    page,
    context,
    baseURL,
  }) => {
    await context.clearCookies();
    await context.addCookies([
      {
        name: "cookie_preferences",
        value: "foobar",
        domain: domainFromUrl(baseURL || ""),
        path: "/",
      },
    ]);
    await context.addCookies([
      {
        name: "cookie_preferences_set",
        value: "true",
        domain: domainFromUrl(baseURL || ""),
        path: "/",
      },
    ]);
    await page.goto("/");
    await expect(await page.locator(".tna-cookie-banner")).not.toBeVisible();
    const cookies = await context.cookies();
    const cookiePreferences = JSON.parse(
      decodeURIComponent(
        cookies.find((cookie) => cookie.name === "cookie_preferences")?.value ||
          "{}",
      ),
    );
    expect(cookiePreferences).toBeDefined();
    expect(cookiePreferences).toHaveProperty("essential", true);
    expect(cookiePreferences).toHaveProperty("usage", false);
    expect(cookiePreferences).toHaveProperty("marketing", false);
    expect(cookiePreferences).toHaveProperty("settings", false);
  });

  test("incomplete preferences set", async ({ page, context, baseURL }) => {
    await context.clearCookies();
    await context.addCookies([
      {
        name: "cookie_preferences",
        value: JSON.stringify({
          settings: true,
        }),
        domain: domainFromUrl(baseURL || ""),
        path: "/",
      },
    ]);
    await context.addCookies([
      {
        name: "cookie_preferences_set",
        value: "true",
        domain: domainFromUrl(baseURL || ""),
        path: "/",
      },
    ]);
    await page.goto("/");
    await expect(await page.locator(".tna-cookie-banner")).not.toBeVisible();
    const cookies = await context.cookies();
    const cookiePreferences = JSON.parse(
      decodeURIComponent(
        cookies.find((cookie) => cookie.name === "cookie_preferences")?.value ||
          "{}",
      ),
    );
    expect(cookiePreferences).toBeDefined();
    expect(cookiePreferences).toHaveProperty("essential", true);
    expect(cookiePreferences).toHaveProperty("usage", false);
    expect(cookiePreferences).toHaveProperty("marketing", false);
    expect(cookiePreferences).toHaveProperty("settings", true);
  });

  test("set incorrectly declared", async ({ page, context, baseURL }) => {
    await context.clearCookies();
    await context.addCookies([
      {
        name: "cookie_preferences_set",
        value: "true",
        domain: domainFromUrl(baseURL || ""),
        path: "/",
      },
    ]);
    await page.goto("/");
    await expect(await page.locator(".tna-cookie-banner")).not.toBeVisible();
    const cookies = await context.cookies();
    const cookiePreferences = JSON.parse(
      decodeURIComponent(
        cookies.find((cookie) => cookie.name === "cookie_preferences")?.value ||
          "{}",
      ),
    );
    expect(cookiePreferences).toBeDefined();
    expect(cookiePreferences).toHaveProperty("essential", true);
    expect(cookiePreferences).toHaveProperty("usage", false);
    expect(cookiePreferences).toHaveProperty("marketing", false);
    expect(cookiePreferences).toHaveProperty("settings", false);
  });
});
