/**
 * Print the learning guide to PDF (A4).
 * Usage: node print_guide.js
 */
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");

(async () => {
  const html = path.join(__dirname, "..", "..", "docs", "learn", "guide.html");
  const out = path.join(__dirname, "..", "..", "docs", "learn", "cell-platform-end-to-end.pdf");
  const fileUrl = "file:///" + html.replace(/\\/g, "/");
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(fileUrl, { waitUntil: "load" });
  await page.pdf({
    path: out,
    format: "A4",
    printBackground: true,
    margin: { top: "14mm", bottom: "16mm", left: "14mm", right: "14mm" },
  });
  await browser.close();
  const size = fs.statSync(out).size;
  console.log("wrote", out, size, "bytes");
})();
