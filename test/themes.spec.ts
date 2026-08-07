import { test, expect } from "@playwright/test";

test("switching themes", async ({ page }) => {
  await page.goto("/");
  await expect(await page.locator("html")).toHaveClass(/tna-template--system-theme/);
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
  await expect(await page.locator("html")).toHaveClass(/tna-template--dark-theme/);

  await page
    .getByRole("button", { name: "Change to using the system theme" })
    .click();
  await expect(await page.locator("html")).toHaveClass(/tna-template--system-theme/);
  await expect(await page.locator("html")).not.toHaveClass(
    /tna-template--dark-theme/,
  );
});
