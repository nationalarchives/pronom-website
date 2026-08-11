import { test, expect } from "@playwright/test";
import { checkAccessibility, validateHtml } from "./lib.ts";

test("page has no accessibility issues", async ({ page }) => {
  await page.goto("/signature-list");
  await checkAccessibility(page);
});

test("page has valid HTML", async ({ page }) => {
  await page.goto("/signature-list");
  await validateHtml(page);
});

test("binary signature XML", { tag: ["@aws"] }, async ({ page }) => {
  await page.goto("/signature-list");
  await validateHtml(page);
  const firstBinarySignatureFile = await page
    .locator("ul:near(:text('Binary signature files'))")
    .locator("li")
    .first()
    .getByRole("link");
  const href = (await firstBinarySignatureFile.getAttribute("href")) || "";
  await expect(href).toMatch(/\/signatures\/DROID_SignatureFile_V(\d+)\.xml$/);

  const response = await page.goto(href);
  const xmlContent = await response?.text();
  await expect(xmlContent).toContain(
    '<FFSignatureFile xmlns="http://www.nationalarchives.gov.uk/pronom/SignatureFile"',
  );
});

test("container signature XML", { tag: ["@aws"] }, async ({ page }) => {
  await page.goto("/signature-list");
  await validateHtml(page);
  const firstContainerSignatureFile = await page
    .locator("ul:near(:text('Container signature files'))")
    .locator("li")
    .first()
    .getByRole("link");
  const href = (await firstContainerSignatureFile.getAttribute("href")) || "";
  await expect(href).toMatch(
    /\/container-signatures\/container-signature-(\d{8})\.xml$/,
  );

  const response = await page.goto(href);
  const xmlContent = await response?.text();
  await expect(xmlContent).toContain(
    '<ContainerSignature Id="2110" ContainerType="OLE2">',
  );
  await expect(xmlContent).toContain(
    "<Description>Microsoft Excel 97-2003 Template OLE2</Description>",
  );
});
