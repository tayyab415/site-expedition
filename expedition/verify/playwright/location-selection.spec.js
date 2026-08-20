const { test, expect } = require("@playwright/test");

test("Discover moves through location selection before Examine", async ({ page }) => {
  await page.route("**/api/discover", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        candidates: [
          { id: "san_marcos_tx", name: "San Marcos I-35 / rail pin", lat: 29.883, lng: -97.941, label: "POTENTIAL", site_form: "existing_asset", source: "openstreetmap", captured_at: "2026-08-20T00:00:00Z" },
          { id: "san_leon", name: "San Leon coastal pin", lat: 29.475732, lng: -94.966533, label: "POTENTIAL", site_form: "existing_asset", source: "openstreetmap", captured_at: "2026-08-20T00:00:00Z" },
          { id: "port_houston", name: "Port Houston logistics pin", lat: 29.73, lng: -95.12, label: "POTENTIAL", site_form: "existing_asset", source: "openstreetmap", captured_at: "2026-08-20T00:00:00Z" },
          { id: "alliance_tx", name: "Alliance / Fort Worth logistics pin", lat: 32.976, lng: -97.319, label: "POTENTIAL", site_form: "existing_asset", source: "openstreetmap", captured_at: "2026-08-20T00:00:00Z" },
        ],
        note: "Curated replay candidates.",
      }),
    });
  });

  await page.goto("/");
  await expect(page.getByRole("button", { name: /Warehouse/ })).toBeVisible();
  await page.getByRole("button", { name: /Warehouse/ }).click();
  await expect(page.locator("#confirm")).toBeEnabled();
  await page.locator("#confirm").click();

  await expect(page.locator("#app")).not.toHaveClass(/hidden/);
  await expect(page.locator('#locate-cards .locate-card[data-region="austin_san_antonio"]')).toBeVisible();
  await page.locator('#locate-cards .locate-card[data-region="austin_san_antonio"]').click();

  await expect(page.locator("#app")).toHaveAttribute("data-beat", "scout");
  await expect(page.locator("#selection-heading")).toHaveText("Select a location");
  await expect(page.locator("#selection-image")).toBeVisible();
  await expect(page.locator("#cards .card")).toHaveCount(4);
  await expect(page.locator("#examine-location")).toBeVisible();
  await expect(page.locator("#selection-image")).toHaveAttribute("data-source", "street-view");
  await expect(page.locator('#cards .card-thumb[data-source="street-view"]').first()).toBeVisible();
  await page.screenshot({ path: "expedition/var/playwright-location-selection.png" });

  await page.locator('#cards .card[data-id="san_marcos_tx"]').click();
  await expect(page.locator("#selection-name")).toContainText("San Marcos");
  await page.locator("#examine-location").click();

  await expect(page.locator("#app")).toHaveAttribute("data-beat", "screen");
  await expect(page.locator("#selection-stage")).toBeHidden();
  await expect(page.locator("#pin-name")).toContainText("San Marcos");
  await expect(page.locator("#run-one")).toBeVisible();
  await page.screenshot({ path: "expedition/var/playwright-location-examine.png" });
});
