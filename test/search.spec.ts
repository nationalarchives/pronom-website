import { test, expect, describe } from "@playwright/test";
import { checkAccessibility, validateHtml } from "./lib.ts";

describe("landing page", () => {
  test("page has no accessibility issues", async ({ page }) => {
    await page.goto("/search");
    await checkAccessibility(page);
  });

  test("page has valid HTML", async ({ page }) => {
    await page.goto("/search");
    await validateHtml(page);
  });

  test("header has the correct accessibility tree", async ({ page }) => {
    await page.goto("/search");
    await expect(page.locator(".tna-header")).toMatchAriaSnapshot(`- banner:
  - strong: "Service phase: Beta"
  - paragraph:
    - text: This service is still in development.
    - link "Give us your feedback":
      - /url: https://www.smartsurvey.co.uk/s/pronom/
    - text: .
  - link "The National Archives - PRONOM":
    - /url: /
    - text: PRONOM
  - navigation "Primary":
    - list:
      - listitem:
        - link "About":
          - /url: /about
      - listitem:
        - link "Search":
          - /url: /search
      - listitem:
        - link "Releases":
          - /url: /releases
    - list:
      - listitem:
        - link "DROID Signature Files":
          - /url: /signature-list
      - listitem:
        - link "PRONOM on GitHub":
          - /url: https://github.com/nationalarchives/pronom`);
  });

  test("main has the correct accessibility tree", async ({ page }) => {
    await page.goto("/search");
    await expect(page.getByRole("main")).toMatchAriaSnapshot(`- main:
  - heading "Search PRONOM" [level=1]
  - paragraph: Enter a file format name or file extension
  - searchbox "Search PRONOM"
  - button "Search"`);
  });

  test("footer has the correct accessibility tree", async ({ page }) => {
    await page.goto("/search");
    await expect(page.locator(".tna-footer"))
      .toMatchAriaSnapshot(`- contentinfo:
  - heading "Change the site theme" [level=2]
  - button "Change to using the system theme"
  - button "Change to using the light theme"
  - button "Change to using the dark theme"
  - paragraph:
    - text: To save your preference,
    - button "enable settings cookies"
    - text: . Review your
    - link "cookie preferences":
      - /url: https://www.nationalarchives.gov.uk/cookies/
    - text: .
  - heading "The National Archives" [level=2]
  - text: Kew, Richmond TW9 4DU
  - heading "Follow us on social media" [level=3]
  - navigation "Social":
    - list:
      - listitem:
        - link "The National Archives X feed (formerly known as Twitter)":
          - /url: https://twitter.com/UKNatArchives
          - text: X (formerly Twitter)
      - listitem:
        - link "The National Archives YouTube channel":
          - /url: https://www.youtube.com/c/TheNationalArchivesUK
          - text: ""
      - listitem:
        - link "The National Archives Facebook page":
          - /url: https://www.facebook.com/TheNationalArchives
          - text: ""
      - listitem:
        - link "The National Archives Flickr feed":
          - /url: https://www.flickr.com/photos/nationalarchives
          - text: ""
      - listitem:
        - link "The National Archives Instagram feed":
          - /url: https://www.instagram.com/nationalarchivesuk/
          - text: ""
  - heading "Legal information" [level=3]
  - navigation "Legal":
    - list:
      - listitem:
        - link "Accessibility statement":
          - /url: /accessibility-statement
      - listitem:
        - link "Terms and conditions":
          - /url: https://www.nationalarchives.gov.uk/legal/
      - listitem:
        - link "Cookies":
          - /url: https://www.nationalarchives.gov.uk/cookies/
    - separator
  - paragraph:
    - text: All content is available under the
    - link "Open Government Licence v3.0":
      - /url: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
    - text: ", except where otherwise stated"
  - link "GOV.UK":
    - /url: https://www.gov.uk/`);
  });
});

describe("searching", () => {
  test("empty search", async ({ page }) => {
    await page.goto("/search");
    await expect(page.locator(".tna-skip-link")).toHaveCount(1);
    await expect(page.locator("#search-results")).toHaveCount(0);

    await page.getByRole("button", { name: "Search" }).click();
    await expect(page.locator(".tna-skip-link")).toHaveCount(2);
    await expect(page.locator("#search-results")).toBeVisible();
    const searchResults = page.locator("#search-results");
    await expect(searchResults).toHaveText(/Showing ([\d,]+) results/);
    const searchResultList = searchResults.getByRole("list");
    await expect(searchResultList).toBeVisible();
    await expect(await searchResultList.locator("li").count()).toBeGreaterThan(
      0,
    );
    // await checkAccessibility(page);  // TODO: Takes a long time to run, so disabled for now
    await validateHtml(page);

    await searchResultList.locator("li").first().getByRole("link").click();
    await expect(page).toHaveURL(/\/fmt\/(\d+)$/);
  });

  test("search for 'mp4'", async ({ page }) => {
    await page.goto("/search");
    await expect(page.locator(".tna-skip-link")).toHaveCount(1);
    await expect(page.locator("#search-results")).toHaveCount(0);

    await page.getByRole("searchbox").fill("mp4");
    await page.getByRole("button", { name: "Search" }).click();
    await expect(page.locator(".tna-skip-link")).toHaveCount(2);
    await expect(page.locator("#search-results")).toBeVisible();
    const searchResults = page.locator("#search-results");
    await expect(searchResults).toHaveText(
      /Showing ([\d,]+) results for "mp4"/,
    );
    const searchResultList = searchResults.getByRole("list");
    await expect(searchResultList).toBeVisible();
    await expect(await searchResultList.locator("li").count()).toBeGreaterThan(
      0,
    );
    await checkAccessibility(page);
    await validateHtml(page);

    await searchResultList.locator("li").first().getByRole("link").click();
    await expect(page).toHaveURL(/\/fmt\/(\d+)$/);
  });

  test("search for non-existant", async ({ page }) => {
    await page.goto("/search");
    await expect(page.locator(".tna-skip-link")).toHaveCount(1);
    await expect(page.locator("#search-results")).toHaveCount(0);

    await page.getByRole("searchbox").fill("foobar");
    await page.getByRole("button", { name: "Search" }).click();
    await expect(page.locator(".tna-skip-link")).toHaveCount(1);
    await expect(page.locator("#search-results")).toBeVisible();
    const searchResults = page.locator("#search-results");
    await expect(searchResults).toHaveText(/No results found/);
    await expect(searchResults)
      .toMatchAriaSnapshot(`- heading "No results found" [level=2]
- paragraph: "You can improve your search results by:"
- list:
  - listitem: Double checking your spelling
  - listitem: Using fewer keywords`);
    await checkAccessibility(page);
    await validateHtml(page);
  });
});
