// The new header looked at in a real desktop window: the same Electron and the same window options as
// desktop/main.cjs (hidden title bar with the Windows buttons laid over the page), the interface served by a
// sandbox Core on this PC. Its own name and profile folder, so nothing of the installed JARVIS is read, written or
// signalled; nothing but 127.0.0.1 is reachable. Saves a picture and measurements per window size and quits.
const { app, BrowserWindow } = require('electron');
const fs = require('fs');
const path = require('path');

const out = process.env.HEADER_CHECK_OUT;
if (!out) { console.error('HEADER_CHECK_OUT not set'); process.exit(2); }
app.setName('jarvis-header-check');
app.setPath('userData', path.join(out, 'profile'));
app.commandLine.appendSwitch('host-resolver-rules', 'MAP * ~NOTFOUND, EXCLUDE 127.0.0.1');

function measure() {
  const box = e => { const b = e.getBoundingClientRect(); return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height) }; };
  const region = e => getComputedStyle(e).getPropertyValue('-webkit-app-region') || getComputedStyle(e).webkitAppRegion || '';
  const top = document.querySelector('.topbar'), nav = top.querySelector('nav'), actions = top.querySelector('.top-actions'), brand = top.querySelector('.brand');
  const shown = [...nav.children].filter(e => e.getBoundingClientRect().width > 0 && getComputedStyle(e).visibility !== 'hidden');
  const overlay = navigator.windowControlsOverlay;
  const area = overlay && overlay.visible ? overlay.getTitlebarAreaRect() : null;
  return {
    htmlClass: document.documentElement.className, innerWidth, innerHeight, pageScrollWidth: document.documentElement.scrollWidth,
    topbar: { ...box(top), region: region(top), paddingRight: getComputedStyle(top).paddingRight },
    brand: { ...box(brand), region: region(brand) }, actions: { ...box(actions), region: region(actions), parts: [...actions.children].filter(e => e.getBoundingClientRect().width > 0).map(e => ({ tag: e.tagName, ...box(e), region: region(e) })) },
    nav: { ...box(nav), region: region(nav), scrollWidth: nav.scrollWidth, clientWidth: nav.clientWidth },
    items: shown.map(e => ({ text: (e.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 16), ...box(e), region: region(e) })),
    windowButtonsArea: area && { x: area.x, y: area.y, w: area.width, h: area.height }, overlayVisible: overlay ? overlay.visible : null,
  };
}

app.whenReady().then(async () => {
  const results = [];
  for (const [width, height] of [[1280, 900], [1501, 900], [1600, 900], [1650, 900], [1651, 900], [1700, 900], [1920, 1040], [1024, 768], [720, 540]]) {
    const win = new BrowserWindow({ width, height, minWidth: 720, minHeight: 540, show: false,
      titleBarStyle: 'hidden', titleBarOverlay: { color: '#03111b', symbolColor: '#bcefff', height: 36 }, backgroundColor: '#101820',
      webPreferences: { preload: path.join(__dirname, 'preload.cjs'), nodeIntegration: false, contextIsolation: true, sandbox: true, backgroundThrottling: false } });
    win.removeMenu();
    try {
      await win.loadURL('http://127.0.0.1:8799/');
      await new Promise(resolve => setTimeout(resolve, 4500));
      const measured = await win.webContents.executeJavaScript(`(${measure.toString()})()`);
      const image = await win.webContents.capturePage();
      const size = image.getSize();
      fs.writeFileSync(path.join(out, `header-${width}x${height}.png`), image.toPNG());
      results.push({ window: [width, height], picture: size, ...measured });
    } catch (error) {
      results.push({ window: [width, height], error: String(error) });
    }
    win.destroy();
  }
  fs.writeFileSync(path.join(out, 'header-check.json'), JSON.stringify(results, null, 1));
  app.quit();
});
app.on('window-all-closed', () => {});
