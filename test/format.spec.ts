import { test, expect, describe } from "@playwright/test";
import { checkAccessibility, validateHtml } from "./lib.ts";

const goToFormatPage = async (page: any, format: number = 0) => {
  if (format === 0) {
    await page.goto("/search?q=mp4");
    await page
      .locator("#search-results")
      .getByRole("list")
      .locator("li")
      .first()
      .getByRole("link")
      .click();
    await expect(page).toHaveURL(/\/fmt\/(\d+)$/);
  } else {
    await page.goto(`/fmt/${format}`);
  }
};

test("page has no accessibility issues", async ({ page }) => {
  await goToFormatPage(page, 199);
  await checkAccessibility(page);
});

test("page has valid HTML", async ({ page }) => {
  await goToFormatPage(page, 199);
  await validateHtml(page);
});

test("page has an XML download button", async ({ page }) => {
  await goToFormatPage(page, 199);
  const downloadButton = await page.getByRole("link", { name: "Download XML" });
  await expect(downloadButton).toBeVisible();
  const href = (await downloadButton.getAttribute("href")) || "";
  await expect(href).toMatch(/\/fmt\/(\d+)\.xml$/);

  const response = await page.goto(href);
  const xmlContent = await response?.text();
  await expect(xmlContent).toContain(
    '<PRONOM-Report xmlns="http://pronom.nationalarchives.gov.uk">',
  );
  await expect(xmlContent).toContain("<FormatID>924</FormatID>");
  await expect(xmlContent).toContain(
    "<FormatName>MPEG-4 Media File</FormatName>",
  );
});

describe("page shows the correct details", () => {
  test("summary", async ({ page }) => {
    await goToFormatPage(page, 199);
    const summary = await page.locator("dl:near(:text('Summary'))");

    const name = await summary.locator("dt:has-text('Name') + dd");
    await expect(name).toHaveText("MPEG-4 Media File");

    const identifiers = await summary
      .locator("dt:has-text('Identifiers') + dd > ul > li")
      .all();
    await expect(identifiers[0]).toHaveText("MIME: video/mp4");
    await expect(identifiers[1]).toHaveText("PUID: fmt/199");

    const formatType = await summary
      .locator("dt:has-text('Format type') + dd > ul > li")
      .all();
    await expect(formatType[0]).toHaveText("Audio");
    await expect(formatType[1]).toHaveText("Video");

    const description = await summary.locator(
      "dt:has-text('Description') + dd",
    );
    await expect(await description.textContent()).not.toBeNull();

    const fileExtensions = await summary
      .locator("dt:has-text('File extensions') + dd > code")
      .all();
    await expect(fileExtensions[0]).toHaveText("mp4");
    await expect(fileExtensions[1]).toHaveText("m4v");
    await expect(fileExtensions[2]).toHaveText("m4a");
    await expect(fileExtensions[3]).toHaveText("f4v");
    await expect(fileExtensions[4]).toHaveText("f4a");
    await expect(fileExtensions[5]).toHaveText("m4b");

    const source = await summary.locator("dt:has-text('Source') + dd");
    await expect(await source.textContent()).not.toBeNull();
    await expect(source.locator("a")).toHaveCount(1);
    await expect(source.locator("a")).toHaveAttribute("href", /actor\/(\d+)/);

    await goToFormatPage(page, 1509);

    const version = await summary.locator("dt:has-text('Version') + dd");
    await expect(version).toHaveText("3");

    const formatType2 = await summary.locator(
      "dt:has-text('Format type') + dd",
    );
    await expect(formatType2).toHaveText("Image (Vector)");

    const developedBy = await summary.locator(
      "dt:has-text('Developed by') + dd",
    );
    await expect(await developedBy.textContent()).not.toBeNull();
    await expect(developedBy.locator("a")).toHaveCount(1);
    await expect(developedBy.locator("a")).toHaveAttribute(
      "href",
      /actor\/(\d+)/,
    );

    const supportedBy = await summary.locator(
      "dt:has-text('Supported by') + dd",
    );
    await expect(await supportedBy.textContent()).not.toBeNull();
    await expect(supportedBy.locator("a")).toHaveCount(1);
    await expect(supportedBy.locator("a")).toHaveAttribute(
      "href",
      /actor\/(\d+)/,
    );

    await goToFormatPage(page, 61);

    const identifiers2 = await summary
      .locator("dt:has-text('Identifiers') + dd > ul > li")
      .all();
    await expect(identifiers2[0]).toHaveText("MIME: application/vnd.ms-excel");
    await expect(identifiers2[1]).toHaveText(
      "Apple Uniform Type Identifier: com.microsoft.excel.xls",
    );
    await expect(identifiers2[2]).toHaveText("PUID: fmt/61");
  });

  test("relationships", async ({ page }) => {
    await goToFormatPage(page, 199);
    const summary = await page.locator("dl:near(:text('Relationships'))");

    const hasLowerPriorityThan = await summary
      .locator("dt:has-text('Has lower priority than') + dd > ul > li")
      .all();
    await expect(hasLowerPriorityThan.length).toBeGreaterThan(0);
    await expect(hasLowerPriorityThan[0].locator("a")).toHaveCount(1);
    await expect(hasLowerPriorityThan[0].locator("a")).toHaveAttribute(
      "href",
      /fmt\/(\d+)/,
    );

    const hasPriorityOver = await summary
      .locator("dt:has-text('Has priority over') + dd > ul > li")
      .all();
    await expect(hasPriorityOver.length).toBeGreaterThan(0);
    await expect(hasPriorityOver[0].locator("a")).toHaveCount(1);
    await expect(hasPriorityOver[0].locator("a")).toHaveAttribute(
      "href",
      /fmt\/(\d+)/,
    );
  });

  test("internal signatures", async ({ page }) => {
    await goToFormatPage(page, 199);
    await expect(page.locator(".tna-aside:near(:text('Internal signatures'))"))
      .toMatchAriaSnapshot(`- heading "MP4 Media File" [level=3]
- term: Note
- definition: "Represents the following character sequence: \{4\}ftyp\{0-64\}\(mp42\|mp41\|isom\|iso2\)\*moov"
- heading "Byte sequences" [level=4]
- term: Min Frag Length
- definition: Absolute from BOF
- term: Offset
- definition: "4"
- term: Max offset
- definition: None
- term: Byte Sequence
- definition:
  - code: "66747970\{0-64\}\(6D703432\|6D703431\|69736F6D\|69736F32\)\*6D6F6F76"
- term: Endianness
- definition: Little-endian`);
  });

  test("container signatures", async ({ page }) => {
    await goToFormatPage(page, 1509);
    await expect(page.locator(".tna-aside:near(:text('Container signatures'))"))
      .toMatchAriaSnapshot(`- paragraph: "Type: OLE2"
- heading "13090 - Microsoft Visio Document 3" [level=3]
- term: File path
- definition: VisioDocument
- heading "Byte sequence reference" [level=4]
- paragraph: BOFoffset
- heading "Sub sequences" [level=5]
- term: Min Frag Length
- definition: "0"
- term: Position
- definition: "1"
- term: Sub sequence min offset
- definition: "0"
- term: Sub sequence max offset
- definition: "0"
- term: Sequence
- definition:
  - code: "'Visio (TM) Drawing'0D0A"
- term: Right fragment
- definition: Max offset 6 Min offset 6 Position 1`);
  });
});
