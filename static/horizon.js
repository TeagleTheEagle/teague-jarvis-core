// Horizon shell (1.0.15): the owner's new look for the whole interface (docs/design/NEW-LOOK.md).
// Presentation only: the navigation buttons, the command palette and every handler are the existing ones, moved and
// relabelled. Nothing here invents a value: the version comes from /api/state, the connection light follows what
// static/dashboard-model.js makes of the last answer from the Core, and the sky is a drawing.
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
  // Escape closes the open menu and stops there: app.js treats Escape as "stop JARVIS", which is not what a
  // person closing a menu means. Capture phase, so this runs before that handler.
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !menu.hidden) { e.stopPropagation(); e.preventDefault(); openMenu(false); toggle.focus(); } }, true);
  const syncMore = () => toggle.classList.toggle('active', !!menu.querySelector('.nav.active'));
  new MutationObserver(syncMore).observe(nav, {subtree: true, attributes: true, attributeFilter: ['class']});
  // A narrow window keeps one row: sections that do not fit move under MORE, and come back when there is room.
  // Only a section whose place changes is moved, so a button that stays keeps the keyboard focus.
  let shown = primary.length;  // how many everyday sections sit in the row
  const overflows = () => nav.scrollWidth > nav.clientWidth + 1;
  function fit() {
    if (!menu.hidden) openMenu(false);  // an open menu would be measured as part of the row
    const focused = document.activeElement, before = shown;
    while (shown > 2 && overflows()) { shown -= 1; menu.prepend(primary[shown]); }
    // Room again: bring sections back one at a time, as many as fit.
    while (shown >= before && shown < primary.length) { nav.insertBefore(primary[shown], more); if (overflows()) { menu.prepend(primary[shown]); break; } shown += 1; }
    if (focused && focused !== document.activeElement && menu.contains(focused)) toggle.focus();  // its button went under MORE
    syncMore();
  }
  const sizes = new ResizeObserver(fit); sizes.observe(topbar); sizes.observe(nav);  // nav: the right side can grow without the header changing size

  // ---- right side: command search, connection, clock ----
  const actions = q('.top-actions'), palette = q('.ti-palette-trigger');
  if (palette) {
    palette.replaceChildren(el('span', 'hz-search-icon'), el('span', 'hz-search-text', 'Search commands'), el('kbd', '', 'Ctrl K'));
    palette.setAttribute('aria-label', 'Search commands (Ctrl K)');
    if (actions) actions.prepend(palette);
  }

  // ---- strip under the header: what JARVIS is, and the running version ----
  const strip = el('div', 'hz-strip'); const line = el('p'), warning = el('p', 'hz-warning', 'CORE NOT CONNECTED'); warning.hidden = true;
  ['ONE CORE', 'MANY CAPABILITIES', 'LOCAL AND PRIVATE'].forEach((text, i) => { if (i) line.append(el('b', 'hz-sep', '//')); line.append(el('span', '', text)); });
  warning.append(el('b', 'hz-sep', '//'), el('span', '', 'WHAT YOU SEE MAY BE OUT OF DATE'));
  const version = el('span', 'hz-version'); const owner = el('span', 'hz-owner', 'TEAGUE INDUSTRIES');
  const stripRight = el('span', 'hz-strip-right'); stripRight.append(version, owner);
  strip.append(el('span', 'hz-strip-edge'), line, warning, stripRight); topbar.append(strip);

  // ---- connection: one reading of the link to the Core for the light, the strip, the version and the line under
  // the small core. Green only while the Core has been heard from recently (static/dashboard-model.js). ----
  const model = typeof JarvisDashboardModel !== 'undefined' ? JarvisDashboardModel : null;
  const connection = q('#connection'), light = connection && connection.parentElement;
  const linkNote = el('span', 'hz-link-note'); if (light) light.append(linkNote);
  const telemetry = q('.ti-core-telemetry'), telemetrySpans = telemetry ? telemetry.querySelectorAll('span') : [];
  const linkNow = () => { const s = typeof state !== 'undefined' ? state : null, header = connection ? connection.textContent : '';
    if (!model || !s) return /lost|offline/i.test(header) ? 'lost' : 'online';
    return model.link({inspection: !!window.JARVIS_INSPECTION, connected: s.connected !== undefined ? s.connected : /lost/i.test(header) ? false : undefined,
      hasData: !!s.data, busy: !!(s.busy || s.transcribing), stateAt: s.stateAt, heartbeatAt: s.heartbeatAt, now: Date.now()}); };
  const write = (node, text) => { if (node && node.textContent !== text) node.textContent = text; };
  let lastLink = '';
  function tick() {
    const link = linkNow(), live = !model || model.live(link);
    if (link !== lastLink) { lastLink = link;
      if (light) { light.classList.toggle('lost', link === 'lost'); light.classList.toggle('pending', link !== 'lost' && link !== 'online'); }
      write(linkNote, link === 'online' || link === 'lost' || !model ? '' : model.LINK_TEXT[link]);
      line.hidden = link === 'lost'; warning.hidden = link !== 'lost';
      if (telemetry) { telemetry.classList.toggle('lost', link === 'lost'); telemetry.classList.toggle('pending', link !== 'lost' && link !== 'online');
        if (telemetrySpans[0] && telemetrySpans[0].lastChild) write(telemetrySpans[0].lastChild, link === 'online' ? ' CORE CONNECTED' : link === 'lost' ? ' CORE NOT CONNECTED' : ' CORE ' + (model ? model.LINK_TEXT[link] : ''));
        write(telemetrySpans[1], 'ONE CORE · LOCAL NODE'); }
    }
    const updates = live && typeof state !== 'undefined' && state.data && state.data.updates;
    const text = !updates ? '' : updates.installed_release ? 'v' + String(updates.installed_release).split('-')[0] : updates.source_revision ? 'DEV ' + String(updates.source_revision).slice(0, 7) : 'DEV';
    write(version, text); if (version.title !== (text ? 'Running release' : '')) version.title = text ? 'Running release' : '';
  }
  tick(); setInterval(tick, 1500);
  if (connection) new MutationObserver(tick).observe(connection, {childList: true, characterData: true, subtree: true});
  // Back in front after being hidden: app.js stopped asking the Core meanwhile and asks again only every 10 s.
  document.addEventListener('visibilitychange', () => { if (document.visibilityState !== 'visible' || window.JARVIS_INSPECTION) return;
    if (typeof refresh === 'function' && typeof state !== 'undefined' && !state.busy) Promise.resolve(refresh()).then(tick, tick); });

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
