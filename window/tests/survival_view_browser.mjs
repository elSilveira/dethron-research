import assert from 'node:assert/strict';
import {connect} from './browser_client.mjs';
const [profile,base,output]=process.argv.slice(2);
const browser=await connect(profile);
try {
  await browser.call('Emulation.setDeviceMetricsOverride',{width:1440,height:1200,deviceScaleFactor:1,mobile:false});
  await browser.call('Page.navigate',{url:`${base}/survival`});
  await browser.wait("document.querySelector('#passed')?.textContent==='3 / 3'");
  await browser.evaluate("document.querySelectorAll('#steps button')[4].click()");
  assert.equal(await browser.evaluate("document.querySelectorAll('#nodes .node').length"),20);
  assert.equal(await browser.evaluate("document.querySelectorAll('#nodes .dead').length"),0);
  await browser.screenshot(`${output}/completed.png`);
  await browser.evaluate("document.querySelector('#node-phase').value='before';document.querySelector('#node-phase').dispatchEvent(new Event('change'))");
  assert.equal(await browser.evaluate("document.querySelectorAll('#nodes .dead').length"),19);
  await browser.evaluate("document.querySelector('#node-phase').value='after';document.querySelector('#node-phase').dispatchEvent(new Event('change'))");
  await browser.call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  assert.equal(await browser.evaluate('document.documentElement.scrollWidth <= innerWidth'),true);
  await browser.screenshot(`${output}/mobile.png`);
  // View-only fixture: a new run with no evidence must clear the previous object.
  await browser.evaluate("window.fetch=async()=>new Response(JSON.stringify({status:'running',run_id:'fixture-empty',events:[],report:null,token:'unused'}),{headers:{'Content-Type':'application/json'}})");
  await browser.wait("document.querySelector('#status').textContent.includes('fixture-empty')");
  assert.equal(await browser.evaluate("document.querySelector('#object-panel').hidden"),true);
  assert.equal(browser.errors.length,0,JSON.stringify(browser.errors));
  console.log('Before/after repair views, desktop and mobile passed.');
} finally {await browser.close();}
