// usage: N8N_OWNER_EMAIL=.. N8N_OWNER_PASSWORD=.. node screenshots.mjs <outdir> <askExecId> <ingestExecId> <answersHtml>
// Needs puppeteer-core. Logs in with env credentials inside the page (never printed) and hides the sidebar / user menu.
import puppeteer from 'puppeteer-core';
const [outDir, askExec, ingestExec, answersHtml] = process.argv.slice(2);
const BASE = 'http://127.0.0.1:5678';
const browser = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1.5 });
await page.goto(BASE + '/signin', { waitUntil: 'networkidle2' });
await page.evaluate(async (e, p) => {
  await fetch('/rest/login', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ emailOrLdapLoginId: e, password: p }) });
}, process.env.N8N_OWNER_EMAIL, process.env.N8N_OWNER_PASSWORD);
const HIDE = `[class*="sidebar"], [class*="_sideMenu"], #side-menu, [data-test-id="main-sidebar"], [data-test-id="user-menu"], [class*="userMenu"], [data-test-id*="user"] {display:none !important}`;
async function shot(url, file, wait = 3500) {
  await page.goto(url, { waitUntil: 'networkidle2' });
  await page.addStyleTag({ content: HIDE });
  await new Promise(r => setTimeout(r, wait));
  // dismiss the "Production Checklist" popover if shown (close X at top-right of the card)
  if (await page.evaluate(() => document.body.innerText.includes('Production Checklist'))) {
    await page.mouse.click(394, 105); await new Promise(r => setTimeout(r, 800));
  }
  await page.keyboard.press('1');
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: `${outDir}/${file}` });
  console.log('wrote', file);
}
await shot(`${BASE}/workflow/ragKbIngest0001`, '01-ingest-canvas.png');
await shot(`${BASE}/workflow/ragKbAsk000002`, '02-ask-canvas.png');
await shot(`${BASE}/workflow/ragKbAsk000002/executions/${askExec}`, '03-ask-execution-success.png', 4500);
await page.setViewport({ width: 1100, height: 900, deviceScaleFactor: 1.5 });
await page.goto('file://' + answersHtml);
await page.screenshot({ path: `${outDir}/04-answers-with-citations.png`, fullPage: true });
console.log('wrote 04');
await browser.close();
