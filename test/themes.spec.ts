import { test, expect, describe } from "@playwright/test";
import { domainFromUrl } from "./lib";

test("switching themes", async ({ page }) => {
  await page.goto("/");
  await expect(await page.locator("html")).toHaveClass(
    /tna-template--system-theme/,
  );
  await expect(await page.locator("html")).not.toHaveClass(
    /tna-template--dark-theme/,
  );

  await page
    .getByRole("button", { name: "Change to using the light theme" })
    .click();
  await expect(await page.locator("html")).not.toHaveClass(
    /tna-template--system-theme/,
  );
  await expect(await page.locator("html")).not.toHaveClass(
    /tna-template--dark-theme/,
  );

  await page
    .getByRole("button", { name: "Change to using the dark theme" })
    .click();
  await expect(await page.locator("html")).not.toHaveClass(
    /tna-template--system-theme/,
  );
  await expect(await page.locator("html")).toHaveClass(
    /tna-template--dark-theme/,
  );

  await page
    .getByRole("button", { name: "Change to using the system theme" })
    .click();
  await expect(await page.locator("html")).toHaveClass(
    /tna-template--system-theme/,
  );
  await expect(await page.locator("html")).not.toHaveClass(
    /tna-template--dark-theme/,
  );
});

describe("setting themes from cookies", () => {
  test("none", async ({ context, page, baseURL }) => {
    await context.clearCookies();
    await page.goto("/");
    await expect(await page.locator("html")).toHaveClass(
      /tna-template--system-theme/,
    );
    await expect(await page.locator("html")).not.toHaveClass(
      /tna-template--dark-theme/,
    );
    await page.goto("/search");
    await expect(await page.locator("html")).toHaveClass(
      /tna-template--system-theme/,
    );
    await expect(await page.locator("html")).not.toHaveClass(
      /tna-template--dark-theme/,
    );
  });

  test("system", async ({ context, page, baseURL }) => {
    await context.clearCookies();
    await context.addCookies([
      {
        name: "theme",
        value: "system",
        domain: domainFromUrl(baseURL || ""),
        path: "/",
      },
    ]);
    await page.goto("/");
    await expect(await page.locator("html")).toHaveClass(
      /tna-template--system-theme/,
    );
    await expect(await page.locator("html")).not.toHaveClass(
      /tna-template--dark-theme/,
    );
    await page.goto("/search");
    await expect(await page.locator("html")).toHaveClass(
      /tna-template--system-theme/,
    );
    await expect(await page.locator("html")).not.toHaveClass(
      /tna-template--dark-theme/,
    );
  });

  test("light", async ({ context, page, baseURL }) => {
    await context.clearCookies();
    await context.addCookies([
      {
        name: "theme",
        value: "light",
        domain: domainFromUrl(baseURL || ""),
        path: "/",
      },
    ]);
    await page.goto("/");
    await expect(await page.locator("html")).not.toHaveClass(
      /tna-template--system-theme/,
    );
    await expect(await page.locator("html")).not.toHaveClass(
      /tna-template--dark-theme/,
    );
    await page.goto("/search");
    await expect(await page.locator("html")).not.toHaveClass(
      /tna-template--system-theme/,
    );
    await expect(await page.locator("html")).not.toHaveClass(
      /tna-template--dark-theme/,
    );
  });

  test("dark", async ({ context, page, baseURL }) => {
    await context.clearCookies();
    await context.addCookies([
      {
        name: "theme",
        value: "dark",
        domain: domainFromUrl(baseURL || ""),
        path: "/",
      },
    ]);
    await page.goto("/");
    await expect(await page.locator("html")).not.toHaveClass(
      /tna-template--system-theme/,
    );
    await expect(await page.locator("html")).toHaveClass(
      /tna-template--dark-theme/,
    );
    await page.goto("/search");
    await expect(await page.locator("html")).not.toHaveClass(
      /tna-template--system-theme/,
    );
    await expect(await page.locator("html")).toHaveClass(
      /tna-template--dark-theme/,
    );
  });
});
