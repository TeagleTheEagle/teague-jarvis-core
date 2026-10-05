// Horizon shell (1.0.15): the owner's new look for the whole interface (docs/design/NEW-LOOK.md).
// Presentation only: the navigation buttons, the command palette and every handler are the existing ones, moved and
// relabelled. Nothing here invents a value: the version comes from /api/state, the sky is a drawing.
(() => {
  const q = s => document.querySelector(s);
  const topbar = q('.topbar'), nav = q('.topbar nav'), shell = q('.shell');
  if (!topbar || !nav || !shell || q('.hz-strip')) return;
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  document.documentElement.classList.add('hz');

  // ---- brand: the JARVIS mark (Teague T in a ring) ----
  const mark = q('.brand > img'); if (mark) mark.src = '/assets/branding/teague/jarvis-mark.svg';
  const productLine = q('.brand-product small'); if (productLine) productLine.textContent = 'AI COMMAND CENTER';

  // ---- navigation: eight everyday sections, the rest under MORE, Settings last ----
  const PRIMARY = [['command', 'DASHBOARD'], ['communications', 'CHAT'], ['focus', 'TASKS'], ['projects', 'PROJECTS'], ['memory', 'MEMORY'],
    ['files', 'FILES'], ['web', 'WEB'], ['maps', 'MAPS']];
  const SECONDARY = [['system', 'SYSTEM STATUS'], ['mission', 'ACTIVITY LOG'], ['diagrams', 'DIAGRAMS'], ['changes', 'RELEASE HISTORY']];
  const button = name => document.querySelector(`.nav[data-view="${name}"]`);
  const more = el('div', 'hz-more'); const toggle = el('button', 'hz-more-toggle', 'MORE'); toggle.type = 'button';
  toggle.setAttribute('aria-haspopup', 'true'); toggle.setAttribute('aria-expanded', 'false');
  const menu = el('div', 'hz-menu'); menu.hidden = true; more.append(toggle, menu);
  const primary = [];
  for (const [name, label] of PRIMARY) { const b = button(name); if (b) { b.textContent = label; nav.append(b); primary.push(b); } }
  for (const [name, label] of SECONDARY) { const b = button(name); if (b) { b.textContent = label; menu.append(b); } }
  const settings = button('settings');
  for (const b of [...document.querySelectorAll('.topbar .nav')]) if (!primary.includes(b) && b !== settings && !menu.contains(b)) menu.append(b);
  const suite = q('#suiteButton'); if (suite) { suite.textContent = 'APPLICATIONS'; menu.append(suite); }
  nav.append(more); if (settings) { settings.textContent = 'SETTINGS'; nav.append(settings); }
  const openMenu = open => { menu.hidden = !open; toggle.setAttribute('aria-expanded', String(open)); };
  toggle.addEventListener('click', e => { e.stopPropagation(); openMenu(menu.hidden); });
  menu.addEventListener('click', () => openMenu(false));
  document.addEventListener('click', e => { if (!more.contains(e.target)) openMenu(false); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !menu.hidden) { openMenu(false); toggle.focus(); } });
  const syncMore = () => toggle.classList.toggle('active', !!menu.querySelector('.nav.active'));
  new MutationObserver(syncMore).observe(nav, {subtree: true, attributes: true, attributeFilter: ['class']});
  // A narrow window keeps one row: sections that do not fit move under MORE, and come back when there is room.
  function fit() {
    for (const b of primary) nav.insertBefore(b, more);
    let last = primary.length - 1;
    while (last > 1 && nav.scrollWidth > nav.clientWidth + 1) { menu.prepend(primary[last]); last -= 1; }
    syncMore();
  }
  new ResizeObserver(fit).observe(topbar);

  // ---- right side: command search, connection, clock ----
  const actions = q('.top-actions'), palette = q('.ti-palette-trigger');
  if (palette) {
    palette.replaceChildren(el('span', 'hz-search-icon'), el('span', 'hz-search-text', 'Search commands'), el('kbd', '', 'Ctrl K'));
    palette.setAttribute('aria-label', 'Search commands (Ctrl K)');
    if (actions) actions.prepend(palette);
  }

  // The connection light follows the text app.js writes (green only while the Core answers).
  const connection = q('#connection');
  if (connection && connection.parentElement) {
    const syncConnection = () => connection.parentElement.classList.toggle('lost', /lost|offline/i.test(connection.textContent));
    new MutationObserver(syncConnection).observe(connection, {childList: true, characterData: true, subtree: true}); syncConnection();
  }

  // ---- strip under the header: what JARVIS is, and the running version ----
  const strip = el('div', 'hz-strip'); const line = el('p');
  ['ONE CORE', 'MANY CAPABILITIES', 'LOCAL AND PRIVATE'].forEach((text, i) => { if (i) line.append(el('b', 'hz-sep', '//')); line.append(el('span', '', text)); });
  const version = el('span', 'hz-version'); const owner = el('span', 'hz-owner', 'TEAGUE INDUSTRIES');
  const stripRight = el('span', 'hz-strip-right'); stripRight.append(version, owner);
  strip.append(el('span', 'hz-strip-edge'), line, stripRight); topbar.append(strip);
  function versionText() {
    const updates = typeof state !== 'undefined' && state.data && state.data.updates;
    if (!updates) return '';
    if (updates.installed_release) return 'v' + String(updates.installed_release).split('-')[0];
    return updates.source_revision ? 'DEV ' + String(updates.source_revision).slice(0, 7) : 'DEV';
  }
  const tick = () => { const text = versionText(); if (version.textContent !== text) version.textContent = text;
    if (version.title !== (text ? 'Running release' : '')) version.title = text ? 'Running release' : ''; };
  tick(); setInterval(tick, 3000);

  // ---- footer wording ----
  const footerFirst = q('footer span:first-child'); if (footerFirst) footerFirst.lastChild.textContent = ' TEAGUE INDUSTRIES · A BRIGHTER TOMORROW';
  const footerSecond = q('footer span:nth-child(2)'); if (footerSecond) footerSecond.textContent = 'ONE CORE · LOCAL NODE';

  // ---- the sky: stars and the Earth's horizon, drawn once per window size (a drawing, not data) ----
  const sky = el('canvas', 'hz-sky'); sky.setAttribute('aria-hidden', 'true'); document.body.prepend(sky);
  function drawSky() {
    const w = innerWidth, h = innerHeight, dpr = Math.min(devicePixelRatio || 1, 2);
    if (!w || !h) return;
    sky.width = Math.round(w * dpr); sky.height = Math.round(h * dpr);
    const g = sky.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0);
    let seed = 20261005; const rnd = () => (seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296;
    const space = g.createLinearGradient(0, 0, 0, h);
    space.addColorStop(0, '#01050b'); space.addColorStop(.6, '#020a15'); space.addColorStop(1, '#041428');
    g.fillStyle = space; g.fillRect(0, 0, w, h);
    for (const [x, y, r, c] of [[.86, .2, .5, 'rgba(24,74,150,.20)'], [.1, .12, .42, 'rgba(18,58,120,.14)'], [.5, .45, .5, 'rgba(14,70,130,.16)']]) {
      const haze = g.createRadialGradient(x * w, y * h, 0, x * w, y * h, r * w); haze.addColorStop(0, c); haze.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = haze; g.fillRect(0, 0, w, h);
    }
    const stars = Math.round(w * h / 4200);
    for (let i = 0; i < stars; i++) {
      const x = rnd() * w, y = rnd() * h * .86, big = rnd() > .97;
      g.fillStyle = `rgba(${170 + Math.round(rnd() * 60)},${205 + Math.round(rnd() * 40)},255,${(big ? .75 : .12 + rnd() * .5).toFixed(2)})`;
      g.beginPath(); g.arc(x, y, big ? 1.1 + rnd() * .5 : .25 + rnd() * .7, 0, 7); g.fill();
    }
    // Earth: a circle whose top edge crosses the bottom of the window.
    const apex = h - Math.max(100, Math.min(176, h * .18)), drop = Math.max(90, w * .092);
    const R = ((w / 2) ** 2 + drop ** 2) / (2 * drop), cx = w / 2, cy = apex + R;
    const limb = x => cy - Math.sqrt(Math.max(0, R * R - (x - cx) ** 2));
    const air = g.createRadialGradient(cx, cy, R - 4, cx, cy, R + 90);
    air.addColorStop(0, 'rgba(110,195,255,.60)'); air.addColorStop(.12, 'rgba(50,140,255,.30)'); air.addColorStop(.45, 'rgba(24,96,220,.10)'); air.addColorStop(1, 'rgba(10,60,180,0)');
    g.fillStyle = air; g.beginPath(); g.arc(cx, cy, R + 90, 0, 7); g.fill();
    const body = g.createRadialGradient(cx, apex - 30, 20, cx, apex + 60, Math.max(w * .62, 500));
    body.addColorStop(0, '#12406f'); body.addColorStop(.28, '#0a2748'); body.addColorStop(.7, '#05152a'); body.addColorStop(1, '#030c18');
    g.fillStyle = body; g.beginPath(); g.arc(cx, cy, R, 0, 7); g.fill();
    g.save(); g.beginPath(); g.arc(cx, cy, R, 0, 7); g.clip();
    for (let i = 0; i < 26; i++) {  // soft cloud and land mottling
      const x = rnd() * w, y = limb(x) + 18 + rnd() * (h - apex), r = 60 + rnd() * 170;
      const blot = g.createRadialGradient(x, y, 0, x, y, r); blot.addColorStop(0, `rgba(${rnd() > .5 ? '70,130,200' : '3,10,22'},${(.05 + rnd() * .09).toFixed(2)})`); blot.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = blot; g.beginPath(); g.ellipse(x, y, r, r * .32, 0, 0, 7); g.fill();
    }
    const light = (x, y, a, r) => { g.fillStyle = `rgba(255,${190 + Math.round(rnd() * 40)},${110 + Math.round(rnd() * 50)},${a.toFixed(2)})`; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); };
    g.shadowColor = 'rgba(255,170,70,.9)'; g.shadowBlur = 5;
    const clusters = Math.max(7, Math.round(w / 190));
    for (let c = 0; c < clusters; c++) {  // city lights, gathered the way coasts and cities gather them
      const x0 = rnd() * w, y0 = limb(x0) + 26 + rnd() * Math.max(30, h - limb(x0) - 40), spread = 26 + rnd() * 80, count = 26 + Math.round(rnd() * 60);
      for (let i = 0; i < count; i++) {
        const x = x0 + (rnd() + rnd() + rnd() - 1.5) * spread * 2.2, y = y0 + (rnd() + rnd() + rnd() - 1.5) * spread * .5;
        if (y > limb(x) + 10) light(x, y, .25 + rnd() * .6, .4 + rnd() * .9);
      }
      let x = x0, y = y0; const dx = (rnd() - .5) * 14, dy = (rnd() - .5) * 3;
      for (let i = 0; i < 22; i++) { x += dx + (rnd() - .5) * 6; y += dy + (rnd() - .5) * 3; if (y > limb(x) + 10) light(x, y, .3 + rnd() * .4, .5); }
    }
    g.restore(); g.shadowBlur = 0;
    g.strokeStyle = 'rgba(170,225,255,.95)'; g.lineWidth = 1.4; g.shadowColor = '#4db8ff'; g.shadowBlur = 16;
    g.beginPath(); g.arc(cx, cy, R, Math.PI * 1.2, Math.PI * 1.8); g.stroke(); g.shadowBlur = 0;
    g.save(); g.globalCompositeOperation = 'lighter'; g.translate(cx, apex); g.scale(1, .26);
    const flare = g.createRadialGradient(0, 0, 0, 0, 0, Math.min(w * .3, 460));
    flare.addColorStop(0, 'rgba(215,240,255,.62)'); flare.addColorStop(.07, 'rgba(120,200,255,.34)'); flare.addColorStop(.4, 'rgba(50,140,255,.10)'); flare.addColorStop(1, 'rgba(20,90,220,0)');
    g.fillStyle = flare; g.beginPath(); g.arc(0, 0, Math.min(w * .3, 460), 0, 7); g.fill(); g.restore();
  }
  let skyTimer = 0; const redraw = () => { clearTimeout(skyTimer); skyTimer = setTimeout(drawSky, 120); };
  drawSky(); addEventListener('resize', redraw); fit();
})();
