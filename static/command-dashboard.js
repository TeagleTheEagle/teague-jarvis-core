// Command dashboard (1.0.15, second layout): the owner's dashboard picture around the existing core canvas, with
// real data only (docs/design/NEW-LOOK.md lists every panel and its source).
// Sources: /api/state (state.data, refreshed by app.js), /api/metrics (this PC), /api/workspaces (projects), the
// assistant mode (state.mode), the activity log app.js keeps, and the microphone. A value without a source is not
// shown: there is no weather and no mail count here. While the Core cannot be reached, everything that came from
// it reads as unknown rather than as its last value. The graphics follow the same rule: the rings around the core
// move with the real assistant state and carry the six system states, the map shows the real day and night sides
// (static/world-map.js), the network picture is the device registry, the graph is this PC's readings.
(() => {
  const view = document.querySelector('#commandView');
  if (!view || document.querySelector('.cd-left')) return;
  const SVG = 'http://www.w3.org/2000/svg';
  const ICONS = {
    workstation: 'M3 5h18v11H3z M8 20h8 M12 16v4',
    mobile: 'M8 2h8a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z M11 18h2',
    glasses: 'M2 13a3.5 3.5 0 0 0 7 0 M15 13a3.5 3.5 0 0 0 7 0 M9 13h6 M2 13l2-5 M22 13l-2-5',
    mic: 'M12 3a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3z M5 11a7 7 0 0 0 14 0 M12 18v3',
    send: 'M4 12l16-8-6 16-3-6z M11 14l9-10',
    note: 'M5 4h10l4 4v12H5z M15 4v4h4 M8 12h8 M8 16h6',
    analyse: 'M3 5h18v11H3z M8 20h8 M12 16v4 M8 11l3-3 2 2 3-3',
    timer: 'M12 7a7 7 0 1 0 0 14a7 7 0 1 0 0-14z M12 10v4l3 2 M9 3h6',
    search: 'M11 4a7 7 0 1 0 0 14a7 7 0 1 0 0-14z M16 16l5 5',
    settings: 'M12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6z M12 2v3 M12 19v3 M2 12h3 M19 12h3 M4.9 4.9L7 7 M17 17l2.1 2.1 M4.9 19.1L7 17 M17 7l2.1-2.1',
    project: 'M3 6h6l2 2h10v11H3z',
    system: 'M12 3l8 4.5v9L12 21l-8-4.5v-9z M12 12l8-4.5 M12 12v9 M12 12L4 7.5',
    voice: 'M4 10v4 M8 7v10 M12 4v16 M16 7v10 M20 10v4',
    memory: 'M7 7h10v10H7z M9 3v4 M15 3v4 M9 17v4 M15 17v4 M3 9h4 M3 15h4 M17 9h4 M17 15h4',
    file: 'M6 3h9l4 4v14H6z M15 3v4h4',
    message: 'M4 5h16v10H9l-5 4z',
    shield: 'M12 3l8 3v6c0 5-3.5 8-8 9c-4.5-1-8-4-8-9V6z',
    dot: 'M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8z'};
  const MODES = {standby: 'STANDING BY', listening: 'LISTENING', thinking: 'THINKING', processing: 'THINKING', speaking: 'SPEAKING',
    error: 'ATTENTION NEEDED', interrupted: 'INTERRUPTED', understood: 'UNDERSTOOD'};
  const PROMPTS = ['Give me my daily briefing', 'What is on my schedule today?', 'Summarise my open tasks', 'Help me plan my day'];
  const DOT = ' · ';

  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  const icon = name => { const s = document.createElementNS(SVG, 'svg'); s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('aria-hidden', 'true');
    for (const d of ICONS[name].split(' M').map((p, i) => (i ? 'M' : '') + p)) { const p = document.createElementNS(SVG, 'path'); p.setAttribute('d', d); s.append(p); }
    return s; };
  const svg = (tag, attrs, text) => { const e = document.createElementNS(SVG, tag); for (const k in attrs || {}) e.setAttribute(k, attrs[k]); if (text !== undefined) e.textContent = text; return e; };
  const panel = (title, cls) => { const p = el('section', 'cd-panel ' + (cls || '')); p.setAttribute('aria-label', title);
    const h = el('header'); const meta = el('small'); h.append(el('h2', '', title), meta); p.append(h); return [p, meta]; };
  const set = (node, text) => { if (node.textContent !== text) node.textContent = text; };  // no churn for screen readers
  const data = () => (typeof state !== 'undefined' && state.data) || null;
  const visible = () => document.visibilityState === 'visible' && !view.classList.contains('hidden');
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches || document.documentElement.dataset.motion === 'reduced';
  const gb = bytes => (bytes / 1073741824).toFixed(bytes >= 107374182400 ? 0 : 1);
  const duration = s => s < 3600 ? Math.floor(s / 60) + 'm' : Math.floor(s / 3600) + 'h ' + Math.floor(s % 3600 / 60) + 'm';
  const clock = t => new Date(t * 1000).toLocaleTimeString(undefined, {hour: 'numeric', minute: '2-digit'});
  const configured = text => /configured/i.test(text || '') && !/not configured/i.test(text || '');
  const go = name => { const nav = document.querySelector(`.nav[data-view="${name}"]`); if (nav) nav.click(); else if (typeof window.view === 'function') window.view(name); };
  const press = selector => { const b = document.querySelector(selector); if (b) b.click(); };
  // A question typed or chosen here goes to JARVIS through the existing send(); the conversation opens so the reply is seen.
  const ask = text => { text = (text || '').trim(); if (!text || typeof send !== 'function') return; go('communications'); send(text); };
  const linkButton = (text, action) => { const b = el('button', 'cd-link', text); b.type = 'button'; b.addEventListener('click', action); return b; };

  // ---- build ----
  view.classList.add('cd-on');
  const left = el('div', 'cd-left'), right = el('div', 'cd-right');

  const hello = el('section', 'cd-panel cd-hello cd-fixed'); hello.setAttribute('aria-label', 'Today');
  const helloEyebrow = el('small', 'cd-eyebrow'), helloDate = el('b', 'cd-date'), helloTime = el('span', 'cd-daytime');
  const helloPlace = el('div', 'cd-place'); const placeName = el('b'), placeNote = el('small');
  helloPlace.append(placeName, placeNote);
  const helloMain = el('div'); helloMain.append(helloEyebrow, helloDate, helloTime);
  const helloTop = el('div', 'cd-hello-top'); helloTop.append(helloMain, helloPlace);
  const quote = el('p', 'cd-quote', '"A more capable you, every day."'); quote.append(el('small', '', '- JARVIS'));
  // World map: a drawing with the real day and night sides and the place the PC's time zone is named after.
  const mapBox = el('div', 'cd-map'); const mapCanvas = el('canvas'); mapCanvas.setAttribute('aria-hidden', 'true');
  const mapPin = el('i', 'cd-map-pin'); mapPin.hidden = true; mapBox.append(mapCanvas, mapPin);
  const zoneLine = el('small', 'cd-zone');
  hello.append(mapBox, helloTop, quote, zoneLine);

  const [activityPanel, activityMeta] = panel('Recent activity', 'cd-grow'); const activityList = el('ul', 'cd-list cd-activity-list');
  activityPanel.append(activityList, linkButton('View all activity', () => go('mission')));

  const [perfPanel, perfMeta] = panel('System performance', 'cd-fixed'); const rings = el('div', 'cd-rings');
  const ring = label => { const box = el('div', 'cd-ring');
    box.innerHTML = '<svg viewBox="0 0 120 120"><circle class="track" cx="60" cy="60" r="50"></circle><circle class="value" cx="60" cy="60" r="50"></circle></svg>';
    const value = el('b', '', '-'); const inner = el('div'); inner.append(value); const cell = el('div', 'cd-ring-cell'); const note = el('small', '', label);
    box.append(inner); cell.append(box, note); rings.append(cell);
    return {value, circle: box.querySelector('.value'), cell, note}; };
  const r = {cpu: ring('CPU'), memory: ring('MEMORY'), disk: ring('STORAGE'), ready: ring('CONFIGURED')};
  const perfFacts = el('p', 'cd-facts');
  const historyCanvas = el('canvas', 'cd-history'); historyCanvas.setAttribute('aria-hidden', 'true');
  const legend = el('div', 'cd-legend'); legend.append(el('span', 'cpu', 'CPU'), el('span', 'mem', 'MEMORY'), el('small', '', 'LAST 3 MINUTES, WHILE THIS PAGE IS OPEN'));
  const cpuHistory = [], memHistory = [], HISTORY = 60;  // one reading every 3 s
  perfPanel.append(rings, historyCanvas, legend, perfFacts, el('p', 'cd-note', 'Configured is not the same as tested: Settings runs the live checks. Network, graphics and temperature are not measured.'));
  left.append(hello, activityPanel, perfPanel);

  const [overviewPanel, overviewMeta] = panel('Core overview', 'cd-fixed'); const overview = el('div', 'cd-overview');
  const knowledge = el('div', 'cd-knowledge');
  const net = svg('svg', {class: 'cd-net', viewBox: '0 0 262 112', role: 'img'}); const netTitle = svg('title'); net.append(netTitle);
  const NODES = [['workstation', 'THIS PC', 18], ['mobile', 'PHONE', 56], ['glasses', 'GLASSES', 94]]; const netNode = {};
  for (const [kind, label, y] of NODES) {
    const link = svg('path', {class: 'link', d: `M53 50 C 108 50, 100 ${y}, 149 ${y}`}); const group = svg('g', {class: 'node'});
    const glyph = svg('g', {transform: `translate(${164 - 9} ${y - 9}) scale(.75)`});
    for (const d of ICONS[kind].split(' M').map((part, i) => (i ? 'M' : '') + part)) glyph.append(svg('path', {d}));
    const status = svg('text', {class: 'status', x: 186, y: y + 11});
    group.append(svg('circle', {cx: 164, cy: y, r: 14.5}), glyph, svg('text', {class: 'name', x: 186, y: y - 1}, label), status);
    net.append(link, group); netNode[kind] = {link, group, status};
  }
  const netCore = svg('g', {class: 'core'});
  netCore.append(svg('circle', {class: 'halo', cx: 32, cy: 50, r: 28}), svg('circle', {cx: 32, cy: 50, r: 21}), svg('circle', {class: 'dot', cx: 32, cy: 50, r: 7}),
    svg('text', {class: 'name', x: 32, y: 94, 'text-anchor': 'middle'}, 'CORE'));
  const netCoreState = svg('text', {class: 'status', x: 32, y: 107, 'text-anchor': 'middle'}); netCore.append(netCoreState); net.append(netCore);
  overview.append(net, knowledge); overviewPanel.append(overview);
  const [projectPanel, projectMeta] = panel('Projects', 'cd-grow'); const projects = el('ul', 'cd-list');
  projectPanel.append(projects, linkButton('Open projects', () => go('projects')));
  const [schedulePanel, scheduleMeta] = panel("Today's schedule", 'cd-grow'); const schedule = el('ul', 'cd-list');
  const dayLine = el('div', 'cd-day'); dayLine.setAttribute('aria-hidden', 'true'); const dayFill = el('i', 'cd-day-fill'), dayNow = el('i', 'cd-day-now'), dayMarks = el('div', 'cd-day-marks');
  for (const hour of [0, 6, 12, 18]) { const tick = el('span', '', String(hour).padStart(2, '0')); tick.style.left = hour / 24 * 100 + '%'; dayLine.append(tick); }
  dayLine.append(dayFill, dayMarks, dayNow);
  schedulePanel.append(dayLine, schedule, linkButton('Open tasks', () => go('focus')));
  const [toolsPanel, toolsMeta] = panel('Quick tools', 'cd-fixed'); const tools = el('div', 'cd-tools'); toolsMeta.textContent = 'ON THIS PC';
  for (const [name, label, action] of [['note', 'New note', () => press('#quickNote')], ['analyse', 'Analyse', () => press('#captureScreen')],
    ['timer', 'Timer', () => press('#timerButton')], ['search', 'Search', () => { go('web'); const box = document.querySelector('#webQuery'); if (box) box.focus(); }],
    ['settings', 'Settings', () => go('settings')]]) {
    const b = el('button'); b.type = 'button'; b.append(icon(name), el('span', '', label)); b.addEventListener('click', action); tools.append(b);
  }
  toolsPanel.append(tools);
  right.append(overviewPanel, projectPanel, schedulePanel, toolsPanel);

  // Centre: an overlay on the cell that holds the existing canvas.
  const frame = el('div', 'cd-core-frame');
  const meters = el('ul', 'cd-meters'); const meter = {};
  for (const key of ['online', 'listening', 'thinking', 'speaking']) { const li = el('li'); const bars = el('span', 'cd-bars'); for (let i = 0; i < 7; i++) bars.append(el('i'));
    li.append(el('b', '', key === 'online' ? 'ONLINE' : key.toUpperCase()), bars); meters.append(li); meter[key] = li; }
  const systems = el('div', 'cd-systems'); const systemsHead = el('div', 'cd-systems-head'); const systemsState = el('b');
  systemsHead.append(el('small', '', 'SYSTEMS'), systemsState); const rows = el('ul', 'cd-rows'); systems.append(systemsHead, rows);
  const stack = el('div', 'cd-stack'); const greetLine = el('p', 'cd-greet'), serviceLine = el('p', 'cd-service', 'At your service.');
  const coreMode = el('p', 'cd-mode'); coreMode.setAttribute('role', 'status'); coreMode.setAttribute('aria-live', 'polite');
  const wave = el('canvas', 'cd-wave'); wave.width = 520; wave.height = 40; wave.setAttribute('aria-hidden', 'true');
  const voiceHint = el('p', 'cd-voice-hint');
  const chips = el('div', 'cd-chips'); chips.setAttribute('role', 'group'); chips.setAttribute('aria-label', 'Suggested requests');
  for (const text of PROMPTS) { const b = el('button', '', text); b.type = 'button'; b.addEventListener('click', () => ask(text)); chips.append(b); }
  const screenChip = el('button', '', 'Analyse my screen'); screenChip.type = 'button'; screenChip.addEventListener('click', () => press('#captureScreen')); chips.append(screenChip);
  stack.append(greetLine, serviceLine, coreMode, wave, voiceHint, el('small', 'cd-prompt', 'What can I help you with?'), chips);
  // Rings around the core. Each ring is its own layer so the browser turns it without redrawing; the six arcs are
  // the six system rows, and the speed follows the assistant state.
  const reactor = el('div', 'cd-reactor'); reactor.setAttribute('aria-hidden', 'true');
  const layer = (cls, body) => { const s = svg('svg', {class: cls, viewBox: '-500 -500 1000 1000'}); s.innerHTML = body; reactor.append(s); return s; };
  reactor.append(el('div', 'cd-bloom'));
  layer('cd-r-static', '<circle class="edge" r="494"/><circle class="inner" r="386"/><path class="cross" d="M-500 0h36M464 0h36M0-500v36M0 464v36"/>');
  const arcLayer = layer('cd-r-systems', ''); const arcs = [];
  for (let i = 0; i < 6; i++) { const a0 = (-90 + i * 60 + 6) * Math.PI / 180, a1 = (-90 + (i + 1) * 60 - 6) * Math.PI / 180, R = 440;
    const arc = svg('path', {d: `M${(R * Math.cos(a0)).toFixed(1)} ${(R * Math.sin(a0)).toFixed(1)}A${R} ${R} 0 0 1 ${(R * Math.cos(a1)).toFixed(1)} ${(R * Math.sin(a1)).toFixed(1)}`}); arcLayer.append(arc); arcs.push(arc); }
  layer('cd-r-ticks', '<circle r="468"/>');
  layer('cd-r-dash', '<circle class="dash" r="412"/><circle class="amber" r="412"/>');
  for (const name of ['a', 'b']) { const orbit = el('div', 'cd-orbit ' + name); orbit.innerHTML = '<svg viewBox="-500 -500 1000 1000"><circle r="497"/></svg><div class="cd-orbit-spin"><i></i></div>'; reactor.append(orbit); }
  frame.append(reactor, meters, systems, stack);

  // Bottom band: brand, the ask bar, and what stays true of this installation.
  const foot = el('div', 'cd-foot');
  const footBrand = el('div', 'cd-foot-brand'); const footMark = el('img'); footMark.src = '/assets/branding/teague/teague-mark.svg'; footMark.alt = '';
  const footText = el('div'); footText.append(el('b', '', 'TEAGUE INDUSTRIES'), el('small', '', 'A BRIGHTER TOMORROW')); footBrand.append(footMark, footText);
  const askForm = el('form', 'cd-ask'); askForm.setAttribute('aria-label', 'Ask JARVIS');
  const micToggle = el('button', 'cd-ask-mic'); micToggle.type = 'button'; micToggle.append(icon('voice')); micToggle.addEventListener('click', () => press('#micButton'));
  const askInput = el('input'); askInput.type = 'text'; askInput.maxLength = 12000; askInput.placeholder = 'Ask JARVIS anything...'; askInput.setAttribute('aria-label', 'Ask JARVIS anything');
  askInput.autocomplete = 'off';
  const askSend = el('button', 'cd-ask-send'); askSend.type = 'submit'; askSend.setAttribute('aria-label', 'Send to JARVIS'); askSend.append(icon('send'));
  askForm.append(micToggle, askInput, askSend);
  askForm.addEventListener('submit', e => { e.preventDefault(); const text = askInput.value; if (!text.trim()) return; askInput.value = ''; ask(text); });
  const footFacts = el('div', 'cd-foot-facts');
  ['LOCAL', 'PRIVATE', 'ALWAYS WITH YOU'].forEach((text, i) => { if (i) footFacts.append(el('b', 'cd-sep', '/')); footFacts.append(el('span', '', text)); });
  const footDot = el('b', 'cd-foot-dot'); footFacts.append(footDot);
  foot.append(footBrand, askForm, footFacts);
  view.append(left, frame, right, foot);

  // ---- render from real data ----
  let metrics = null, metricsOk = false, metricsTried = false, workspaces = null;
  const list = (target, items, empty) => { target.replaceChildren(...(items.length ? items : [el('li', 'cd-empty', empty)])); };
  // How many rows of a list fit in its panel, from the room the list has and the height of a row already drawn.
  const capacity = (target, most) => { const row = target.querySelector('li:not(.cd-empty)'); const each = row ? row.offsetHeight : 50;
    return target.clientHeight ? Math.max(1, Math.min(most, Math.floor((target.clientHeight + 2) / each))) : most; };
  const setRing = (item, percent, text) => { const length = 2 * Math.PI * 50; item.circle.style.strokeDasharray = String(length);
    item.circle.style.strokeDashoffset = String(length * (1 - Math.max(0, Math.min(100, percent == null ? 0 : percent)) / 100));
    item.value.replaceChildren(text); item.cell.classList.toggle('unknown', percent == null); };
  const percentText = value => { const f = document.createDocumentFragment(); f.append(String(Math.round(value)), el('span', '', '%')); return f; };
  const activityIcon = entry => { const t = (entry.status + ' ' + entry.action).toLowerCase();
    return /voice|speech|micro|wake/.test(t) ? 'voice' : /memory|remember|note/.test(t) ? 'memory' : /file|document|upload|export|backup/.test(t) ? 'file'
      : /chat|message|conversation|run|answer/.test(t) ? 'message' : /privacy|approval|permission|security|session/.test(t) ? 'shield' : /search|web/.test(t) ? 'search'
      : /task|timer|reminder/.test(t) ? 'timer' : 'system'; };

  // World map: redrawn when the minute or the size changes. The marker is the city the PC's time zone is named
  // after (a Windows setting), not a measured position.
  let mapStamp = '';
  function drawMap(now) {
    if (typeof JarvisWorldMap === 'undefined') { mapBox.hidden = true; zoneLine.hidden = true; return; }
    const stamp = Math.floor(now.getTime() / 60000) + ':' + mapCanvas.clientWidth + 'x' + mapCanvas.clientHeight; if (stamp === mapStamp || !mapCanvas.clientWidth) return;
    mapStamp = stamp;
    let zone = ''; try { zone = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) { /* no zone name: no marker */ }
    const pin = JarvisWorldMap.draw(mapCanvas, now, JarvisWorldMap.zonePoint(zone));
    mapPin.hidden = !pin; if (pin) { mapPin.style.left = (pin.x * 100).toFixed(2) + '%'; mapPin.style.top = (pin.y * 100).toFixed(2) + '%'; }
    const offset = -now.getTimezoneOffset(), sign = offset < 0 ? '-' : '+', hours = Math.floor(Math.abs(offset) / 60), minutes = Math.abs(offset) % 60;
    set(zoneLine, 'TIME ZONE' + DOT + (zone ? zone.replaceAll('_', ' ').toUpperCase() + DOT : '') + 'UTC' + sign + hours + (minutes ? ':' + String(minutes).padStart(2, '0') : '')
      + (pin ? DOT + (pin.day ? 'DAYLIGHT NOW' : 'NIGHT NOW') : ''));
  }
  // Processor and memory readings taken while this page is open; cleared when they can no longer be read.
  function drawHistory(show) {
    const w = historyCanvas.clientWidth, h = historyCanvas.clientHeight; if (!w || !h) return;
    const ratio = Math.min(devicePixelRatio || 1, 2); if (historyCanvas.width !== Math.round(w * ratio)) { historyCanvas.width = Math.round(w * ratio); historyCanvas.height = Math.round(h * ratio); }
    const g = historyCanvas.getContext('2d'); g.setTransform(ratio, 0, 0, ratio, 0, 0); g.clearRect(0, 0, w, h);
    g.strokeStyle = '#2f8fdc26'; g.lineWidth = 1; g.beginPath(); for (const level of [.25, .5, .75]) { g.moveTo(0, Math.round(h * level) + .5); g.lineTo(w, Math.round(h * level) + .5); } g.stroke();
    if (!show) return;
    const trace = (values, colour, fill) => { if (values.length < 2) return; const x = i => w - (values.length - 1 - i) * w / (HISTORY - 1), y = v => h - 2 - Math.max(0, Math.min(100, v)) / 100 * (h - 4);
      g.beginPath(); values.forEach((v, i) => i ? g.lineTo(x(i), y(v)) : g.moveTo(x(i), y(v)));
      if (fill) { g.lineTo(w, h); g.lineTo(x(0), h); g.closePath(); const shade = g.createLinearGradient(0, 0, 0, h); shade.addColorStop(0, fill); shade.addColorStop(1, 'rgba(56,182,255,0)'); g.fillStyle = shade; g.fill();
        g.beginPath(); values.forEach((v, i) => i ? g.lineTo(x(i), y(v)) : g.moveTo(x(i), y(v))); }
      g.strokeStyle = colour; g.lineWidth = 1.6; g.stroke(); };
    trace(cpuHistory, '#5cc8ff', 'rgba(56,182,255,.32)'); trace(memHistory, '#4de3c1');
  }

  function render() {
    const now = new Date(), hour = now.getHours();
    const d = data(); const settings = (d && d.settings) || {};
    const connection = (document.querySelector('#connection') || {}).textContent || '';
    // Three states: not heard from the Core yet, connected, and lost (what was read before is then stale).
    const lost = connection === 'CONNECTION LOST', online = !!d && !lost, live = online ? d : null;
    const caps = (live && live.capabilities) || {};
    view.classList.toggle('cd-offline', !online);
    const brain = caps.brain || '', aiOk = configured(brain);

    const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
    set(helloEyebrow, greeting.toUpperCase());
    set(helloDate, now.toLocaleDateString(undefined, {month: 'long', day: 'numeric', year: 'numeric'}));
    set(helloTime, now.toLocaleDateString(undefined, {weekday: 'long'}) + ', ' + now.toLocaleTimeString(undefined, {hour: '2-digit', minute: '2-digit'}));
    const place = ((document.querySelector('#clockLocation') || {}).textContent || '').replace(/\s*↗\s*$/, '').trim();
    const hasPlace = !!place && !/^set location/i.test(place);
    helloPlace.hidden = !hasPlace; if (hasPlace) { set(placeName, place); set(placeNote, 'YOUR LOCATION LABEL'); }
    set(greetLine, greeting + (settings.name ? ', ' + settings.name + '.' : '.') + " I'm JARVIS.");
    drawMap(now);

    // Systems: a row is green only when the thing it names is set up; nothing here is a live test.
    const profile = settings.voice_profile && settings.voice_profile !== 'auto' ? settings.voice_profile : caps.voice_provider;
    const voiceReady = {qwen: !!caps.qwen_voice, fish: !!caps.fish, openai: !!caps.transcription || /^openai configured/i.test(brain), browser: true}[profile];
    const voiceName = ({qwen: 'QWEN VOICE', fish: 'FISH AUDIO', openai: 'OPENAI VOICE', browser: 'BROWSER VOICE'})[profile];
    const deviceList = (live && live.devices) || [];
    const connected = deviceList.filter(x => x.connected && !x.simulated);  // a simulated device is shown, never counted
    const searchName = /serpapi/i.test(caps.search || '') ? 'SERPAPI' : /brave/i.test(caps.search || '') ? 'BRAVE' : caps.search ? 'BEST EFFORT' : 'UNKNOWN';
    const unknown = name => [name, 'off', 'UNKNOWN'];
    const statusRows = !d && !lost ? [['Core', 'off', 'CONNECTING'], unknown('AI'), unknown('Memory'), unknown('Voice'), unknown('Search'), unknown('Devices')]
      : !online ? [['Core', 'warn', 'OFFLINE'], unknown('AI'), unknown('Memory'), unknown('Voice'), unknown('Search'), unknown('Devices')]
      : [['Core', 'ok', 'ONLINE'],
        ['AI', aiOk ? 'ok' : 'warn', aiOk ? brain.split(' ')[0].toUpperCase() : /unsupported/i.test(brain) ? 'CHECK SETTING' : 'NO KEY'],
        ['Memory', 'ok', (live.memory || []).length + ' SAVED'],
        ['Voice', !voiceName ? 'off' : voiceReady ? 'ok' : 'warn', !voiceName ? 'UNKNOWN' : voiceReady ? voiceName : voiceName.split(' ')[0] + ' NOT SET UP'],
        ['Search', caps.search ? 'ok' : 'off', searchName],
        ['Devices', connected.length ? 'ok' : 'off', connected.length + ' ONLINE']];
    rows.replaceChildren(...statusRows.map(([name, cls, text]) => { const li = el('li', cls); li.append(el('i'), el('span', '', name), el('em', '', text)); return li; }));
    const ready = statusRows.filter(x => x[1] === 'ok').length, total = statusRows.length;
    set(systemsState, !d && !lost ? 'CONNECTING' : !online ? 'CORE OFFLINE' : ready === total ? 'ALL CONFIGURED' : (total - ready) + ' TO CHECK');
    systemsState.className = online && ready === total ? '' : 'warn';
    setRing(r.ready, online ? ready * 100 / total : null, online ? ready + '/' + total : '-');
    arcs.forEach((arc, i) => { if (arc.getAttribute('class') !== statusRows[i][1]) arc.setAttribute('class', statusRows[i][1]); });

    // Mode: announced only when it changes.
    const mode = (typeof state !== 'undefined' && state.mode) || 'standby';
    set(coreMode, !d && !lost ? 'CONNECTING' : online ? MODES[mode] || mode.toUpperCase() : 'CORE OFFLINE');
    coreMode.classList.toggle('offline', !online);
    meter.online.className = online ? 'on' : ''; meter.listening.className = online && mode === 'listening' ? 'on live' : '';
    meter.thinking.className = online && (mode === 'thinking' || mode === 'processing') ? 'on live' : ''; meter.speaking.className = online && mode === 'speaking' ? 'on live' : '';
    footDot.className = 'cd-foot-dot' + (online ? ' on' : ''); footDot.title = online ? 'Core connected' : 'Core not connected';
    const motion = !online ? 'offline' : mode === 'processing' ? 'thinking' : mode; if (reactor.dataset.mode !== motion) reactor.dataset.mode = motion;

    // Voice line: the wake word only applies when the microphone is waiting for it.
    const micOn = typeof state !== 'undefined' && !!state.mic;
    const armed = typeof voice !== 'undefined' && !!voice.armed, manual = typeof voice !== 'undefined' && !!voice.manual;
    set(voiceHint, armed && manual ? 'Listening while you hold to talk.' : armed ? 'Listening.' : micOn ? 'Say "Hey Jarvis", then your request.' : 'Microphone off. Press F4 to turn it on.');
    micToggle.setAttribute('aria-pressed', String(micOn)); micToggle.setAttribute('aria-label', micOn ? 'Turn the microphone off' : 'Turn the microphone on');
    micToggle.title = micOn ? 'Microphone on (F4)' : 'Microphone off (F4)';

    // Recent activity: the same entries as the activity log (this session's events and the Core's audit trail).
    const local = (typeof state !== 'undefined' && state.localLogs) || [];
    const entries = [...local, ...((live && live.logs) || [])].filter(x => x && x.action).sort((a, b) => b.created - a.created).slice(0, capacity(activityList, 6));
    list(activityList, entries.map(entry => { const li = el('li', 'cd-activity-row'); const box = el('div'); const mark = el('span', 'cd-activity-icon'); mark.append(icon(activityIcon(entry)));
      box.append(el('b', '', String(entry.action).replaceAll('_', ' ')), el('small', '', String(entry.status || '').toLowerCase()));
      li.append(mark, box, el('time', '', new Date(entry.created * 1000).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit', hour12: false}))); return li; }),
      'Nothing recorded yet in this session.');
    set(activityMeta, online ? 'LIVE' : 'THIS SESSION');

    // Performance: this PC, read by the Core.
    const fresh = online && metricsOk && metrics && !metrics.omitted ? metrics : null;
    const cpu = fresh ? fresh.cpu_percent : null, memory = fresh && fresh.memory ? fresh.memory.used_percent : null, disk = fresh && fresh.disk ? fresh.disk.used_percent : null;
    setRing(r.cpu, cpu, cpu == null ? '-' : percentText(cpu)); setRing(r.memory, memory, memory == null ? '-' : percentText(memory)); setRing(r.disk, disk, disk == null ? '-' : percentText(disk));
    r.disk.cell.title = fresh && fresh.disk ? gb(fresh.disk.free_bytes) + ' GB free on the JARVIS data drive' : '';
    const facts = [];
    if (fresh) { facts.push('Core up ' + duration(fresh.core_uptime_seconds));
      facts.push(fresh.last_response_ms == null ? 'No reply yet' : 'Last reply ' + (fresh.last_response_ms / 1000).toFixed(1) + ' s'); }
    if (aiOk && caps.model) facts.push(caps.model);
    set(perfFacts, facts.join(DOT)); perfFacts.hidden = !facts.length;
    if (!fresh) { cpuHistory.length = 0; memHistory.length = 0; }
    drawHistory(!!fresh);
    set(perfMeta, fresh ? 'THIS PC' + DOT + 'LIVE' : metrics && metrics.omitted ? 'NOT READ' : !online && (d || lost) ? 'CORE OFFLINE' : metricsTried ? 'NOT READING' : 'READING...');

    // Core overview: devices and what JARVIS keeps on this PC.
    const find = re => deviceList.find(x => re.test(x.device_id));
    const described = [];
    for (const [kind, name, device] of [['workstation', 'This PC', find(/^pc$/)], ['mobile', 'Phone', find(/phone|mobile/i)], ['glasses', 'Glasses', find(/glass|wear/i)]]) {
      const text = !online ? 'Unknown' : !device ? 'Not paired' : device.simulated ? 'Simulated only' : device.connected ? 'Online' : 'Offline';
      const cls = !online ? 'unknown' : !device ? 'none' : device.simulated ? 'simulated' : device.connected ? 'ok' : 'offline';
      const node = netNode[kind]; set(node.status, text);
      if (node.group.getAttribute('class') !== 'node ' + cls) { node.group.setAttribute('class', 'node ' + cls); node.link.setAttribute('class', 'link ' + cls); }
      described.push(name + ': ' + text.toLowerCase());
    }
    set(netCoreState, !d && !lost ? 'CONNECTING' : online ? 'ONLINE' : 'OFFLINE');
    if (netCore.getAttribute('class') !== 'core' + (online ? ' ok' : '')) netCore.setAttribute('class', 'core' + (online ? ' ok' : ''));
    set(netTitle, 'Devices of the one Core. ' + described.join('; ') + '.');
    set(overviewMeta, online ? connected.length + ' DEVICE' + (connected.length === 1 ? '' : 'S') + ' ONLINE' : 'UNKNOWN');
    // The Core lists at most 100 conversations, so 100 means "100 or more".
    const count = key => { if (!live || !Array.isArray(live[key])) return '-'; const n = live[key].length; return key === 'conversations' && n >= 100 ? '100+' : String(n); };
    knowledge.replaceChildren(...[['memory', 'Memories'], ['documents', 'Documents'], ['notes', 'Notes'], ['conversations', 'Conversations']].map(([key, label]) => {
      const box = el('div'); box.append(el('b', '', count(key)), el('small', '', label)); return box; }));

    // Projects: progress only where linked tasks that still exist allow it to be counted.
    const tasks = (live && live.tasks) || [];
    const shownProjects = online ? workspaces : null;
    const projectItems = (shownProjects || []).slice(0, capacity(projects, 5)).map(p => {
      const linked = (p.links || []).filter(x => x.kind === 'task').map(x => tasks.find(t => t.id === x.ref)).filter(Boolean);
      const done = linked.filter(t => t.completed).length; const pct = linked.length ? Math.round(done * 100 / linked.length) : null;
      const li = el('li', 'cd-project'); const mark = el('span', 'cd-activity-icon'); mark.append(icon('project'));
      const name = el('div'); name.append(el('b', '', p.name), el('small', '', linked.length ? done + ' of ' + linked.length + ' tasks done' : (p.links || []).length + ' linked items' + DOT + 'no tasks'));
      const bar = el('div', 'cd-bar'); const fill = el('i'); bar.append(fill); if (pct === null) bar.style.visibility = 'hidden'; else fill.style.width = pct + '%';
      const stateText = pct === null ? 'NO TASKS' : pct === 100 ? 'DONE' : 'IN PROGRESS';
      li.append(mark, name, bar, el('em', '', pct === null ? '' : pct + '%'), el('small', 'cd-chip' + (pct === 100 ? ' done' : pct === null ? ' off' : ''), stateText)); return li; });
    list(projects, projectItems, !online ? 'Unknown while the Core is not connected.' : shownProjects ? 'No projects yet. Create one in Projects.' : 'Loading projects...');
    set(projectMeta, shownProjects ? shownProjects.length + ' SAVED' : '');

    const nowS = Date.now() / 1000; const end = new Date(); end.setHours(24, 0, 0, 0); const endS = end.getTime() / 1000;
    const events = [...((live && live.reminders) || []).filter(x => !x.fired && x.due >= nowS && x.due < endS).map(x => [x.due, x.title, 'Reminder']),
      ...tasks.filter(t => !t.completed && t.due && t.due >= nowS && t.due < endS).map(t => [t.due, t.body, 'Task'])].sort((a, b) => a[0] - b[0]);
    list(schedule, events.slice(0, capacity(schedule, 6)).map(([due, text, kind]) => { const li = el('li', 'cd-event'); li.append(el('time', '', clock(due)), el('span', '', text), el('small', '', kind)); return li; }),
      online ? 'Nothing scheduled for the rest of today.' : 'Unknown while the Core is not connected.');
    set(scheduleMeta, online ? events.length + ' TODAY' : '');
    // The day as a line: where the clock is now, and everything due today (what has passed is dimmed).
    const startS = endS - 86400, part = t => Math.max(0, Math.min(1, (t - startS) / 86400)) * 100 + '%';
    dayFill.style.width = part(nowS); dayNow.style.left = part(nowS);
    const marks = [...((live && live.reminders) || []).filter(x => x.due >= startS && x.due < endS).map(x => [x.due, 'cd-due-reminder', x.due < nowS || x.fired]),
      ...tasks.filter(t => t.due && t.due >= startS && t.due < endS).map(t => [t.due, 'cd-due-task', t.due < nowS || t.completed])];
    dayMarks.replaceChildren(...marks.map(([due, kind, past]) => { const mark = el('i', kind + (past ? ' cd-past' : '')); mark.style.left = part(due); return mark; }));
  }

  async function poll(force) {
    if (!force && !visible()) return;
    try { metrics = await api('/api/metrics'); metricsOk = true;
      if (!metrics.omitted && metrics.cpu_percent != null) { cpuHistory.push(metrics.cpu_percent); if (cpuHistory.length > HISTORY) cpuHistory.shift(); }
      if (!metrics.omitted && metrics.memory) { memHistory.push(metrics.memory.used_percent); if (memHistory.length > HISTORY) memHistory.shift(); }
    } catch (e) { metricsOk = false; }
    metricsTried = true; render();
  }
  async function pollProjects(force) {
    if (!force && !visible()) return;
    try { workspaces = (await api('/api/workspaces')).projects || []; render(); } catch (e) { /* the panel keeps its last listing */ }
  }

  // ---- live microphone waveform (local only; nothing is recorded) ----
  const levels = []; let analyser = null, analyserSource = null, samples = null;
  function analyserFor() {
    try {
      if (typeof voice === 'undefined' || !voice.active || !voice.source || !voice.context) return null;
      if (analyserSource !== voice.source) { analyser = voice.context.createAnalyser(); analyser.fftSize = 1024; voice.source.connect(analyser);
        analyserSource = voice.source; samples = new Float32Array(analyser.fftSize); }
      return analyser;
    } catch (e) { return null; }
  }
  function drawWave() {
    const g = wave.getContext('2d'); const w = wave.width, h = wave.height; g.clearRect(0, 0, w, h);
    const micOn = typeof state !== 'undefined' && !!state.mic;
    g.strokeStyle = micOn ? '#5cc8ff' : '#2a5b85'; g.lineWidth = 1.5; g.shadowColor = '#38b6ff'; g.shadowBlur = micOn ? 6 : 0; g.beginPath();
    const live = micOn ? analyserFor() : null;
    if (live) {
      live.getFloatTimeDomainData(samples);
      for (let i = 0; i < samples.length; i += 4) { const x = i / (samples.length - 1) * w, y = h / 2 + samples[i] * h * 2.2; i ? g.lineTo(x, y) : g.moveTo(x, y); }
    } else {
      // voiceDiagnostic.frameAt is a Date.now() stamp (app.js); with the microphone off the line stays flat.
      const fresh = micOn && typeof voiceDiagnostic !== 'undefined' && voiceDiagnostic.frameAt && Date.now() - voiceDiagnostic.frameAt < 400;
      levels.push(fresh ? Math.min(1, (voiceDiagnostic.level || 0) * 8) : 0); if (levels.length > 96) levels.shift();
      levels.forEach((v, i) => { const x = i * w / 95, a = v * h / 2; g.moveTo(x, h / 2 - a); g.lineTo(x, h / 2 + a + 0.5); });
    }
    g.stroke();
  }
  let last = 0;
  function frameLoop(ms) {
    if (visible() && ms - last > (reduced() ? 400 : 33)) { last = ms; drawWave(); }
    requestAnimationFrame(frameLoop);
  }

  render(); poll(true); pollProjects(true);
  setInterval(render, 1500); setInterval(poll, 3000); setInterval(pollProjects, 20000);
  // Coming back to the dashboard or to the window: read at once rather than at the next interval.
  let wasVisible = visible();
  const resume = () => { const now = visible(); if (now && !wasVisible) { poll(); pollProjects(); render(); } wasVisible = now; };
  document.addEventListener('visibilitychange', resume);
  new MutationObserver(resume).observe(view, {attributes: true, attributeFilter: ['class']});
  requestAnimationFrame(frameLoop);
})();
