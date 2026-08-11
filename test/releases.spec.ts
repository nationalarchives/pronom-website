import { test, expect, describe } from "@playwright/test";
import { checkAccessibility, validateHtml } from "./lib.ts";

describe("landing page", () => {
  // TODO: This takes a long time to run and is not currently working due to the length of the page
  // test("page has no accessibility issues", async ({ page }) => {
  //   await page.goto("/releases");
  //   await checkAccessibility(page);
  // });

  test("page has valid HTML", async ({ page }) => {
    await page.goto("/releases");
    await validateHtml(page);
  });
});

describe("release details page", () => {
  const goToReleaseDetailsPage = async (page: any) => {
    await page.goto("/releases");
    await page
      .locator("#releases")
      .locator("li")
      .first()
      .getByRole("link")
      .click();
    await expect(page).toHaveURL(/\/releases\/v(\d+)$/);
  };

  test("page has no accessibility issues", async ({ page }) => {
    await goToReleaseDetailsPage(page);
    await checkAccessibility(page);
  });

  test("page has valid HTML", async ({ page }) => {
    await goToReleaseDetailsPage(page);
    await validateHtml(page);
  });
});
