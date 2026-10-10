// Screenshot helper. usage: node screenshots.mjs <cookie-file> <outdir> <execId> [reportHtml] [slackCardHtml]
// Logs in via an existing session cookie (never prints it) and hides the sidebar/user menu so no account info is shown.
import puppeteer from 'puppeteer-core';
import fs from 'fs';
const [cookieFile, outDir, execId, reportHtml, cardHtml] = process.argv.slice(2);
const BASE = 'http://127.0.0.1:5678', WF = 'csvDailyReport01';
const cookie = fs.readFileSync(cookieFile, 'utf8').split('\n').filter(l => l.includes('n8n-auth')).map(l => l.split('\t'))[0];
const browser = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.setViewport({ width: 1600, height: 760, deviceScaleFactor: 2 });
await page.setCookie({ name: 'n8n-auth', value: cookie[6].trim(), domain: '127.0.0.1', path: '/' });
const HIDE = `[class*="sidebar"], [class*="_sideMenu"], #side-menu, [data-test-id="main-sidebar"], [data-test-id="user-menu"], [class*="userMenu"], [data-test-id*="user"] {display:none !important}`;
async function shot(url, file, opts = {}) {
  await page.goto(url, { waitUntil: 'networkidle2' });
  await page.addStyleTag({ content: HIDE });
  await new Promise(r => setTimeout(r, opts.wait || 3000));
  if (opts.fit) { await page.keyboard.press('1'); await new Promise(r => setTimeout(r, 1200)); }
  await page.screenshot({ path: `${outDir}/${file}` });
  console.log('wrote', file);
}
await shot(`${BASE}/workflow/${WF}`, '01-workflow-canvas.png', { fit: true });
if (execId) await shot(`${BASE}/workflow/${WF}/executions/${execId}`, '02-execution-success.png', { fit: true, wait: 4000 });
if (reportHtml) { await page.setViewport({ width: 1100, height: 900, deviceScaleFactor: 2 });
  await page.goto('file://' + reportHtml); await page.screenshot({ path: `${outDir}/03-report.png`, fullPage: true }); console.log('wrote report'); }
if (cardHtml) { await page.setViewport({ width: 900, height: 900, deviceScaleFactor: 2 });
  await page.goto('file://' + cardHtml); await page.screenshot({ path: `${outDir}/04-slack-alert-card.png`, fullPage: true }); console.log('wrote card'); }
await browser.close();
