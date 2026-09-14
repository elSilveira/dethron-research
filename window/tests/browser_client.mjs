// Optional local Chrome QA helper; no browser dependency in the application.
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

export async function connect(profile) {
  const [port, route] = (await readFile(path.join(profile, 'DevToolsActivePort'), 'utf8')).trim().split(/\r?\n/);
  const socket = new WebSocket(`ws://127.0.0.1:${port}${route}`);
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once:true });
    socket.addEventListener('error', reject, { once:true });
  });
  let counter = 0;
  const pending = new Map(), errors = [];
  socket.addEventListener('message', ({ data }) => {
    const message = JSON.parse(data);
    if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails);
    if (!message.id) return;
    const waiter = pending.get(message.id);
    if (!waiter) return;
    pending.delete(message.id);
    clearTimeout(waiter.timer);
    if (message.error) waiter.reject(new Error(JSON.stringify(message.error)));
    else waiter.resolve(message.result);
  });
  function send(method, params = {}, sessionId) {
    return new Promise((resolve, reject) => {
      const id = ++counter;
      const timer = setTimeout(() => { pending.delete(id); reject(new Error(`Timed out: ${method}`)); }, 10000);
      pending.set(id, { resolve, reject, timer });
      socket.send(JSON.stringify({ id, method, params, sessionId }));
    });
  }
  const { targetId } = await send('Target.createTarget', { url:'about:blank' });
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten:true });
  const call = (method, params) => send(method, params, sessionId);
  await call('Runtime.enable');
  await call('Page.enable');
  async function evaluate(expression) {
    const result = await call('Runtime.evaluate', { expression, returnByValue:true, awaitPromise:true });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  }
  async function wait(expression, timeout = 15000) {
    const end = Date.now() + timeout;
    while (Date.now() < end) {
      if (await evaluate(expression)) return;
      await new Promise(resolve => setTimeout(resolve, 75));
    }
    throw new Error(`UI condition timed out: ${expression}`);
  }
  async function screenshot(file) {
    const { data } = await call('Page.captureScreenshot', { format:'png', captureBeyondViewport:true });
    await writeFile(file, Buffer.from(data, 'base64'));
  }
  return { call, send, evaluate, wait, screenshot, errors,
    close:async () => { await send('Target.closeTarget', { targetId }); socket.close(); } };
}
