// Screenshots via puppeteer-core + the system Chrome. Logs in through the REST API from inside the page
// (credentials come from the environment, are never printed, and no login form is ever rendered).
// usage: NODE_PATH=<dir with puppeteer-core> secret run N8N_OWNER_EMAIL N8N_OWNER_PASSWORD -- node screenshot.js <execId> <outDir> <resultsHtml>
const puppeteer = require('puppeteer-core');
const [execId, outDir, resultsHtml] = process.argv.slice(2);
const BASE = 'http://127.0.0.1:5678';
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', args: ['--no-sandbox'],
                                           defaultViewport: { width: 1600, height: 900 } });
  const page = await browser.newPage();
  await page.goto(BASE + '/signin', { waitUntil: 'domcontentloaded' });
  const status = await page.evaluate(async (e, p) => {
    const r = await fetch('/rest/login', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ emailOrLdapLoginId: e, password: p }) });
    return r.status;
  }, process.env.N8N_OWNER_EMAIL, process.env.N8N_OWNER_PASSWORD);
  if (status !== 200) throw new Error('login failed ' + status);
  // hide anything that could show account details, keep canvas clean
  const css = `[data-test-id="main-sidebar"], #side-menu, [class*="sidebar" i] [data-test-id="user-menu"], [data-test-id="main-sidebar-user-menu"],
               [class*="mainSidebar"], [class*="MainSidebar"], [class*="askAssistant"], [data-test-id="ask-assistant-floating-button"],
               [data-test-id="canvas-chat-button"], [data-test-id="ask-assistant-button"] { display: none !important; }`;
  async function open(path, file, wait = 2500, extra) {
    await page.goto(BASE + path, { waitUntil: 'networkidle2' });
    await page.addStyleTag({ content: css });
    await new Promise(r => setTimeout(r, wait));
    if (extra) await extra();
    await page.screenshot({ path: `${outDir}/${file}` });
  }
  await open('/workflow/invPdfToCsv01', '01-canvas.png', 2500, async () => {
    await page.mouse.move(800, 450); await page.keyboard.press('1'); await page.mouse.move(1500, 780); await new Promise(r => setTimeout(r, 1200));
  });
  await open(`/workflow/invPdfToCsv01/executions/${execId}`, '02-execution.png', 3500, async () => {
    await page.mouse.move(800, 450); await page.keyboard.press('1'); await page.mouse.move(1500, 780); await new Promise(r => setTimeout(r, 1200));
  });
  const p2 = await browser.newPage();
  await p2.setViewport({ width: 1440, height: 900 });
  await p2.goto('file://' + resultsHtml);
  await p2.screenshot({ path: `${outDir}/03-results.png`, fullPage: false });
  await browser.close();
})().catch(e => { console.error(String(e.message).replace(/\S+@\S+/g, '<redacted>')); process.exit(1); });
