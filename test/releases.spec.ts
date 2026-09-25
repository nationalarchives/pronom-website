import { test, expect, describe } from "@playwright/test";
import { checkAccessibility, validateHtml } from "./lib.ts";
import { DOMParser } from "@xmldom/xmldom";
import xpath from "xpath";

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


describe("release notes page", () => {
  test("Full XML release notes", async ({page}) => {
    const response = await page.goto("/release-notes.xml");
    const xmlContent = await response?.text();

    const xml = new DOMParser().parseFromString(xmlContent!, "application/xml");
    
    expect(xpath.select1("//release_note[release_date='5th March 2010']/release_outline[@name='New Records']//format[puid[@type='fmt']='256']/name", xml).toString())
        .toContain(`<name>Microsoft Works Database for Windows 2000</name>`);
    expect(xpath.select1("//release_note[release_date='17th December 2015']/signature_filename", xml).toString())
        .toContain(`<signature_filename>DROID_SignatureFile_V83.xml</signature_filename>`);
    const formatElements = xpath.select("//release_note[release_date='11th March 2022']/release_outline[@name='Updated Records']//format", xml);
        expect(formatElements).toHaveLength(20);
    expect(xpath.select1("//release_note[release_date='30th March 2017']/release_outline[@name='Updated Records']//format[puid[@type='fmt']='145']/name", xml).toString())
        .toContain(`Acrobat PDF/X - Portable Document Format - Exchange 1:2001`);
    expect(xpath.select1("//release_note[release_date='30th March 2017']/release_outline[@name='Updated Records']//format[puid[@type='fmt']='145']/summary", xml).toString())
        .toContain(`Gave priority over all parent Acrobat PDF versions. Issue raised by Archives New Zealand and State Records New South Wales.`);
  });
});