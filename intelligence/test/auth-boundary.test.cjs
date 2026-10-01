'use strict';
// Execute real main-process source with synthetic Electron/FS dependencies only.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');
const sourceRoot = process.env.JARVIS_AUDIT_SOURCE || path.resolve(__dirname, '../..');
const source = fs.readFileSync(path.join(sourceRoot, 'intelligence/main.cjs'), 'utf8');
const origin = 'http://127.0.0.1:4321';
const token = 'SYNTHETIC-OFFLINE-TOKEN';

function host(link = {origin, token}, stage4 = false) {
  let headersHook, start, window;
  const loads = [], stage4Calls = [];
  const session = {webRequest: {onBeforeSendHeaders(callback) {headersHook = callback;}}};
  class Window {
    constructor(options) {this.options = options; this.listeners = {}; this.webContents = {on: (name, callback) => {this.listeners[name] = callback;}}; window = this;}
    removeMenu() {}
    once() {}
    show() {}
    isDestroyed() {return false;}
    loadURL(url) {loads.push(['url', url]); return Promise.resolve();}
    loadFile(file) {loads.push(['file', file]); return Promise.resolve();}
  }
  const electron = {
    app: {commandLine: {appendSwitch() {}}, whenReady: () => ({then(callback) {start = callback;}}), on() {}, quit() {}},
    BrowserWindow: Window,
    session: {fromPartition(name) {assert.equal(name, 'jarvis-intelligence'); return session;}}
  };
  const context = {URL, __dirname: path.join(sourceRoot, 'intelligence'), process: {argv: stage4 ? ['node', '--stage4-test'] : ['node'], platform: 'win32'},
    require(name) {
      if (name === 'electron') return electron;
      if (name === 'node:path') return path;
      if (name === 'node:fs') return {readFileSync(file) {
        assert.equal(path.basename(file), '.jarvis-session.json');
        if (link === null) throw new Error('synthetic missing session');
        return JSON.stringify(link);
      }};
      if (name === '../desktop/policy.cjs') return require(path.join(sourceRoot, 'desktop/policy.cjs'));
      if (name === '../stage4_client.cjs') return {launchTestClient: role => stage4Calls.push(role)};
      throw new Error('Unexpected dependency: ' + name);
    }
  };
  vm.runInNewContext(source, context, {filename: 'intelligence/main.cjs'});
  if (start) start();
  function headers(url, requestHeaders = {}) {
    assert.ok(headersHook, 'actual onBeforeSendHeaders callback registered');
    let response;
    headersHook({url, requestHeaders}, value => {response = value.requestHeaders;});
    return response;
  }
  return {headers, hasHook: !!headersHook, loads, window, stage4Calls};
}

function credentials(headers) {
  return Object.entries(headers).filter(([name]) => name.toLowerCase() === 'x-jarvis-desktop');
}

test('same-origin document, API, assets and query paths retain normal token flow', () => {
  const app = host();
  assert.equal(app.loads[0][1], origin + '/intelligence.html');
  for (const suffix of ['/intelligence.html', '/api/state', '/app.js', '/api/events?id=1', '/path?next=https://untrusted.invalid/']) {
    const result = app.headers(origin + suffix, {Accept: 'application/json'});
    assert.equal(result['X-Jarvis-Desktop'], token);
    assert.equal(result.Accept, 'application/json');
  }
});

const denied = ['http://127.0.0.1:43210/api/state', 'http://127.0.0.1:4321@untrusted.invalid/collect',
    'http://localhost:4321/api/state', 'https://127.0.0.1:4321/api/state', 'http://127.0.0.2:4321/api/state',
    'https://untrusted.invalid/', 'file:///fixture.html', 'data:text/html,fixture', 'not a URL'];
for (const url of denied) {
  test('no token for ' + url, () => {
    const app = host();
    const normalized = url === 'not a URL' ? url : new URL(url).href;
    assert.equal(credentials(app.headers(normalized)).length, 0, url);
  });
}

test('cross-origin redirect drops inherited token regardless of header casing', () => {
  const app = host();
  const first = app.headers(origin + '/api/state');
  assert.equal(first['X-Jarvis-Desktop'], token);
  for (const spelling of ['X-Jarvis-Desktop', 'x-jarvis-desktop', 'X-JARVIS-DESKTOP']) {
    const next = app.headers('https://untrusted.invalid/redirect-target', {[spelling]: token, Accept: '*/*'});
    assert.equal(credentials(next).length, 0, spelling);
    assert.equal(next.Accept, '*/*');
  }
});

test('trusted requests replace supplied credential variants with one canonical token', () => {
  const app = host();
  const input = {'x-jarvis-desktop': 'SYNTHETIC-STALE', 'X-JARVIS-DESKTOP': 'SYNTHETIC-OTHER'};
  const result = app.headers(origin + '/api/state', input);
  assert.equal(credentials(result).length, 1);
  assert.equal(result['X-Jarvis-Desktop'], token);
  assert.equal(input['x-jarvis-desktop'], 'SYNTHETIC-STALE');
});

test('missing session still opens local prototype without credential hook', () => {
  const app = host(null);
  assert.equal(app.hasHook, false);
  assert.equal(app.loads[0][0], 'file');
  assert.equal(path.basename(app.loads[0][1]), 'index.html');
});

test('failed local Core load retains existing local-file fallback', () => {
  const app = host();
  app.window.listeners['did-fail-load']({}, -1, 'synthetic failure');
  assert.equal(app.loads[1][0], 'file');
  assert.equal(path.basename(app.loads[1][1]), 'index.html');
});

test('explicit Stage4 TEST branch bypasses ordinary client setup', () => {
  const app = host({origin, token}, true);
  assert.deepEqual(app.stage4Calls, ['intelligence']);
  assert.equal(app.hasHook, false);
  assert.equal(app.loads.length, 0);
});
