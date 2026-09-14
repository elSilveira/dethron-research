import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {connect} from './browser_client.mjs';
const [profile,base,output]=process.argv.slice(2);
await mkdir(output,{recursive:true});
const browser=await connect(profile);
try{
  await browser.call('Emulation.setDeviceMetricsOverride',{width:1440,height:1200,deviceScaleFactor:1,mobile:false});
  await browser.call('Page.navigate',{url:`${base}/reconstruction`});
  await browser.wait("document.querySelector('#start') && !document.querySelector('#start').disabled");
  assert.equal(await browser.evaluate("document.querySelector('#experiment').value"),'document');
  await browser.evaluate("document.querySelector('#start').click()");
  await browser.wait("document.querySelector('#status').textContent.includes('Executando')");
  await browser.screenshot(`${output}/running.png`);
  await browser.wait("document.querySelector('#status').textContent.includes('concluída') || document.querySelector('#status').textContent.includes('falhou')",480000);
  console.log(await browser.evaluate("document.querySelector('#status').textContent"));
  assert.match(await browser.evaluate("document.querySelector('#status').textContent"),/concluída/);
  assert.equal(await browser.evaluate("document.querySelector('#progress').textContent"),'8 / 8');
  assert.equal(await browser.evaluate("document.querySelectorAll('.case').length"),8);
  assert.equal(await browser.evaluate("document.querySelector('#document-panel').hidden"),false);
  await browser.screenshot(`${output}/completed.png`);
  const report=await browser.evaluate("fetch('/api/reconstruction/report').then(r=>r.json())");
  await writeFile(`${output}/report.json`,JSON.stringify(report,null,2));
  console.log(JSON.stringify(report.summary));
  await browser.call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  assert.equal(await browser.evaluate('document.documentElement.scrollWidth<=innerWidth'),true);
  await browser.screenshot(`${output}/mobile.png`);
  assert.equal(browser.errors.length,0,JSON.stringify(browser.errors));
}finally{await browser.close();}
