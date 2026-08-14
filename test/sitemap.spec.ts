import { test, expect } from "@playwright/test";

test("XML sitemap", async ({ page, baseURL }) => {
  const response = await page.goto("/sitemap.xml");
  const xmlContent = await response?.text();
  await expect(xmlContent).toContain(`<loc>${baseURL}/</loc>`);
  await expect(xmlContent).toContain(`<loc>${baseURL}/about</loc>`);
  await expect(xmlContent).toContain(`<loc>${baseURL}/search</loc>`);
  await expect(xmlContent).toContain(`<loc>${baseURL}/releases</loc>`);
  await expect(xmlContent).toContain(`<loc>${baseURL}/releases/v124</loc>`);
  await expect(xmlContent).toContain(`<loc>${baseURL}/actor/1</loc>`);
  await expect(xmlContent).toContain(`<loc>${baseURL}/fmt/1</loc>`);
  await expect(xmlContent).toContain(`<loc>${baseURL}/signature-list</loc>`);
  await expect(xmlContent).toContain(
    `<loc>${baseURL}/accessibility-statement</loc>`,
  );
});
