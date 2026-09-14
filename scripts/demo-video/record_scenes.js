/**
 * Record silent Playwright clips per demo scene.
 * Voice is muxed later and must not overlap these clips.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const CONSOLE = process.env.CONSOLE_URL || "http://localhost:3000";
const outDir = path.join(__dirname, "output", "clips");
fs.mkdirSync(outDir, { recursive: true });

async function scene(name, fn) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    recordVideo: { dir: outDir, size: { width: 1280, height: 720 } },
    viewport: { width: 1280, height: 720 },
  });
  const page = await context.newPage();
  page.setDefaultTimeout(25000);
  await fn(page);
  await page.waitForTimeout(900);
  await context.close();
  await browser.close();
  const files = fs.readdirSync(outDir).filter((f) => f.endsWith(".webm"));
  const latest = files
    .map((f) => ({ f, t: fs.statSync(path.join(outDir, f)).mtimeMs }))
    .sort((a, b) => b.t - a.t)[0];
  fs.renameSync(path.join(outDir, latest.f), path.join(outDir, `${name}.webm`));
}

(async () => {
  await scene("scene-01-problem", async (page) => {
    await page.goto(CONSOLE, { waitUntil: "networkidle" });
    await page.getByRole("heading", { name: "Fleet" }).waitFor();
    await page.waitForTimeout(2200);
  });

  await scene("scene-02-hosting", async (page) => {
    await page.setContent(`<!doctype html>
<html><head><meta charset="utf-8"/>
<style>
  body{margin:0;background:#f8f8f8;color:#222;font-family:Inter Tight,Segoe UI,sans-serif;height:100vh;display:flex;flex-direction:column;justify-content:center;padding:80px}
  .k{letter-spacing:.16em;text-transform:uppercase;font-size:13px;color:#6a6a6a;margin-bottom:18px}
  h1{font-size:64px;font-weight:500;letter-spacing:-.04em;line-height:.95;margin:0 0 28px}
  .row{display:flex;gap:48px;font-size:18px;line-height:1.5}
  .row b{display:block;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#6a6a6a;margin-bottom:6px}
</style></head>
<body>
  <div class="k">03 systems · one repository</div>
  <h1>GitHub. Render. Vercel.</h1>
  <div class="row">
    <div><b>Source</b>main branch</div>
    <div><b>API</b>FastAPI on Render</div>
    <div><b>Console</b>Next.js on Vercel</div>
  </div>
</body></html>`);
    await page.waitForTimeout(2800);
  });

  await scene("scene-03-target", async (page) => {
    await page.goto(`${CONSOLE}/cells`, { waitUntil: "networkidle" });
    await page.getByRole("heading", { name: "Cells" }).waitFor();
    await page.waitForTimeout(2200);
  });

  await scene("scene-04-create", async (page) => {
    await page.goto(`${CONSOLE}/tenants/new`, { waitUntil: "networkidle" });
    await page.getByLabel(/company/i).fill("Northwind Freight");
    await page.getByRole("button", { name: /create/i }).click();
    await page.getByText(/database_ready/i).waitFor({ timeout: 20000 }).catch(() => {});
    await page.waitForTimeout(2200);
  });

  await scene("scene-05-scale", async (page) => {
    await page.goto(`${CONSOLE}/operations`, { waitUntil: "networkidle" });
    await page.getByRole("button", { name: /seed 20 tenants/i }).click();
    await page.waitForTimeout(2800);
    await page.goto(`${CONSOLE}/cells`, { waitUntil: "networkidle" });
    await page.waitForTimeout(1800);
    await page.goto(CONSOLE, { waitUntil: "networkidle" });
    await page.waitForTimeout(1600);
  });

  await scene("scene-06-move", async (page) => {
    await page.goto(CONSOLE, { waitUntil: "networkidle" });
    const link = page.locator("table a").first();
    await link.waitFor();
    await link.click();
    await page.getByRole("link", { name: /move tenant/i }).click();
    await page.getByRole("button", { name: /start move/i }).click();
    await page.getByText(/cutover complete/i).waitFor({ timeout: 20000 }).catch(() => {});
    await page.waitForTimeout(1800);
  });

  await scene("scene-07-release", async (page) => {
    await page.goto(`${CONSOLE}/releases`, { waitUntil: "networkidle" });
    await page.getByRole("button", { name: /start v8/i }).click();
    await page.getByText(/canary/i).waitFor({ timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(900);
    await page.getByRole("button", { name: /continue wave/i }).click();
    await page.waitForTimeout(1800);
  });

  await scene("scene-08-break", async (page) => {
    await page.goto(`${CONSOLE}/operations`, { waitUntil: "networkidle" });
    await page.getByRole("button", { name: /run i1/i }).click();
    await page.getByText(/I1/i).waitFor({ timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(1200);
    await page.getByRole("button", { name: /break one tenant db/i }).click();
    await page.getByText(/degraded/i).waitFor({ timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(1800);
  });

  console.log("clips written to", outDir);
})();
