// Run against a dedicated test server, with a separate headless Chrome profile.
import assert from 'node:assert/strict';
import { mkdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { connect } from './browser_client.mjs';

const profile = process.argv[2];
if (!profile) throw new Error('Usage: node tests/browser_smoke.mjs <Chrome-profile> [http://127.0.0.1:8765]');
const url = process.argv[3] || 'http://127.0.0.1:8765';
const output = path.resolve('results/browser-check');
await mkdir(output, { recursive:true });
const browser = await connect(profile);
try {
  await browser.send('Browser.setDownloadBehavior', { behavior:'allow', downloadPath:output });
  await browser.call('Emulation.setDeviceMetricsOverride', { width:1440, height:1200, deviceScaleFactor:1, mobile:false });
  await browser.call('Page.navigate', { url });
  await browser.wait("document.querySelector('#start') && !document.querySelector('#start').disabled");
  assert.equal(await browser.evaluate("document.querySelector('h1').textContent"), 'Watch a TRON take shape.');
  await browser.screenshot(path.join(output, 'desktop-idle.png'));
  await browser.evaluate("document.querySelector('#cycles').value = '3'; document.querySelector('#pace').value = '350'; document.querySelector('#controls').requestSubmit()");
  await browser.wait("document.querySelector('#run-status').textContent === 'Running' && Number(document.querySelector('#event-count').textContent) >= 3");
  assert.equal(await browser.evaluate("document.querySelector('#export-report').disabled"), true);
  await browser.screenshot(path.join(output, 'desktop-live.png'));
  await browser.wait("document.querySelector('#run-status').textContent === 'Completed · verified'");
  assert.equal(await browser.evaluate("document.querySelector('#baseline').textContent.replace(/[^0-9]/g, '')"), '4103');
  assert.equal(await browser.evaluate("document.querySelector('#evolved').textContent"), '95');
  assert.equal(await browser.evaluate("document.querySelectorAll('.chart-row').length"), 8);
  assert.equal(await browser.evaluate("document.querySelectorAll('#evolution-body tr').length"), 3);
  await browser.evaluate("const filter = document.querySelector('#event-filter'); filter.value = 'evolution'; filter.dispatchEvent(new Event('change'))");
  assert.equal(await browser.evaluate("document.querySelectorAll('.event-row').length"), 3);
  await browser.evaluate("document.querySelector('.event-row').click()");
  assert.equal(await browser.evaluate("document.querySelector('#inspect-title').textContent"), 'Strategy evaluated');
  await browser.screenshot(path.join(output, 'desktop-complete.png'));
  await browser.evaluate("document.querySelector('#export-report').click()");
  let downloaded;
  for (let i = 0; i < 50; i++) {
    try { downloaded = JSON.parse(await readFile(path.join(output, 'tron-report.json'), 'utf8')); break; }
    catch { await new Promise(resolve => setTimeout(resolve, 100)); }
  }
  assert.equal(downloaded?.correct, true, 'Report download must contain the real successful report');
  await browser.call('Emulation.setDeviceMetricsOverride', { width:390, height:844, deviceScaleFactor:1, mobile:true });
  assert.equal(await browser.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), true, 'Mobile must not overflow');
  await browser.screenshot(path.join(output, 'mobile-complete.png'));
  await browser.evaluate("document.querySelector('#cycles').value = '100'; document.querySelector('#pace').value = '750'; document.querySelector('#controls').requestSubmit()");
  await browser.wait("document.querySelector('#run-status').textContent === 'Running' && !document.querySelector('#stop').disabled");
  await browser.evaluate("document.querySelector('#stop').click()");
  await browser.wait("document.querySelector('#run-status').textContent.startsWith('Stopped')", 5000);
  assert.equal(await browser.evaluate("document.querySelector('#export-report').disabled"), true);
  assert.equal(await browser.evaluate("document.querySelector('#start').disabled"), false);
  assert.equal(browser.errors.length, 0, JSON.stringify(browser.errors));
  console.log('Browser QA passed: live progress, completion, counters, filter, inspector, download, mobile layout, stop, restart controls.');
  console.log(`Screenshots: ${output}`);
} finally {
  await browser.close();
}
