/**
 * Record silent Playwright clips per demo scene.
 * Usage: CONTROL_PLANE_URL and CONSOLE_URL must be running.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const CONSOLE = process.env.CONSOLE_URL || "http://localhost:3000";
const outDir = path.join(__dirname, "output", "clips");
fs.mkdirSync(outDir, { recursive: true });

async function scene(name, fn) {
  const browser = await chromium.launch();
  const context = await browser.newContext({ recordVideo: { dir: outDir, size: { width: 1280, height: 720 } } });
  const page = await context.newPage();
  await fn(page);
  await page.waitForTimeout(800);
  await context.close();
  await browser.close();
  const files = fs.readdirSync(outDir).filter((f) => f.endsWith(".webm"));
  const latest = files.map((f) => ({ f, t: fs.statSync(path.join(outDir, f)).mtimeMs })).sort((a, b) => b.t - a.t)[0];
  fs.renameSync(path.join(outDir, latest.f), path.join(outDir, `${name}.webm`));
}

(async () => {
  await scene("scene-01-problem", async (page) => {
    await page.goto(CONSOLE);
    await page.waitForTimeout(1500);
  });
  await scene("scene-02-target", async (page) => {
    await page.goto(`${CONSOLE}/cells`);
    await page.waitForTimeout(1500);
  });
  await scene("scene-03-create", async (page) => {
    await page.goto(`${CONSOLE}/tenants/new`);
    await page.getByRole("button", { name: "Create" }).click();
    await page.waitForTimeout(2000);
  });
  await scene("scene-04-scale", async (page) => {
    await page.goto(`${CONSOLE}/operations`);
    await page.getByRole("button", { name: "Seed 20 tenants" }).click();
    await page.waitForTimeout(2500);
    await page.goto(`${CONSOLE}/cells`);
  });
  await scene("scene-05-move", async (page) => {
    await page.goto(CONSOLE);
    const link = page.locator("table a").first();
    await link.click();
    await page.getByRole("link", { name: "Move tenant" }).click();
    await page.getByRole("button", { name: "Start move" }).click();
    await page.waitForTimeout(2000);
  });
  await scene("scene-06-release", async (page) => {
    await page.goto(`${CONSOLE}/releases`);
    await page.getByRole("button", { name: "Start V8" }).click();
    await page.waitForTimeout(800);
    await page.getByRole("button", { name: "Continue wave" }).click();
    await page.waitForTimeout(800);
    await page.getByRole("button", { name: "Continue wave" }).click();
    await page.waitForTimeout(1500);
  });
  await scene("scene-07-break", async (page) => {
    await page.goto(`${CONSOLE}/operations`);
    await page.getByRole("button", { name: "Break one tenant DB" }).click();
    await page.waitForTimeout(2000);
  });
  console.log("clips written to", outDir);
})();
