// Command dashboard (1.0.15): the owner's concept layout around the existing core canvas, with real data only.
// Sources: /api/state (state.data, refreshed by app.js), /api/metrics (this PC), /api/workspaces (projects), the
// assistant mode (state.mode) and the microphone (voice, voiceDiagnostic). A value that has no source is not shown.
(() => {
  const view = document.querySelector('#commandView');
  if (!view || document.querySelector('.cd-header')) return;
  const SVG = 'http://www.w3.org/2000/svg';
  const ICONS = {
    overview: 'M12 3l8 4.5v9L12 21l-8-4.5v-9z M12 12l8-4.5 M12 12v9 M12 12L4 7.5',
    communications: 'M4 5h16v10H9l-5 4z',
    web: 'M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M3 12h18 M12 3c3.5 3.5 3.5 14.5 0 18 M12 3c-3.5 3.5-3.5 14.5 0 18',
    projects: 'M3 6h6l2 2h10v11H3z',
    memory: 'M7 7h10v10H7z M9 3v4 M15 3v4 M9 17v4 M15 17v4 M3 9h4 M3 15h4 M17 9h4 M17 15h4',
    focus: 'M9 6h11 M9 12h11 M9 18h11 M4 6l1 1 2-2 M4 12l1 1 2-2 M4 18l1 1 2-2',
    settings: 'M12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6z M12 2v3 M12 19v3 M2 12h3 M19 12h3 M4.9 4.9L7 7 M17 17l2.1 2.1 M4.9 19.1L7 17 M17 7l2.1-2.1',
    workstation: 'M3 5h18v11H3z M8 20h8 M12 16v4',
    mobile: 'M8 2h8a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z M11 18h2',
    glasses: 'M2 13a3.5 3.5 0 0 0 7 0 M15 13a3.5 3.5 0 0 0 7 0 M9 13h6 M2 13l2-5 M22 13l-2-5',
    mic: 'M12 3a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3z M5 11a7 7 0 0 0 14 0 M12 18v3'};
  const TILES = [['overview', 'command', 'Overview'], ['communications', 'communications', 'Comms'], ['web', 'web', 'Web'],
    ['projects', 'projects', 'Projects'], ['memory', 'memory', 'Memory'], ['focus', 'focus', 'Tasks'], ['settings', 'settings', 'Settings']];
  const MODES = {standby: 'STANDING BY', listening: 'LISTENING', thinking: 'THINKING', processing: 'THINKING', speaking: 'SPEAKING',
    error: 'ATTENTION NEEDED', interrupted: 'INTERRUPTED', understood: 'UNDERSTOOD'};
  const DOT = ' · ';

  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  const icon = name => { const s = document.createElementNS(SVG, 'svg'); s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('aria-hidden', 'true');
    for (const d of ICONS[name].split(' M').map((p, i) => (i ? 'M' : '') + p)) { const p = document.createElementNS(SVG, 'path'); p.setAttribute('d', d); s.append(p); }
    return s; };
  const panel = (title, cls) => { const p = el('section', 'cd-panel ' + (cls || '')); p.setAttribute('aria-label', title);
    const h = el('header'); const meta = el('small'); h.append(el('h2', '', title), meta); p.append(h); return [p, meta]; };
  const data = () => (typeof state !== 'undefined' && state.data) || null;
  const visible = () => document.visibilityState === 'visible' && !view.classList.contains('hidden');
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const gb = bytes => (bytes / 1073741824).toFixed(bytes >= 107374182400 ? 0 : 1);
  const duration = s => s < 3600 ? Math.floor(s / 60) + 'm' : Math.floor(s / 3600) + 'h ' + Math.floor(s % 3600 / 60) + 'm';
  const clock = t => new Date(t * 1000).toLocaleTimeString(undefined, {hour: 'numeric', minute: '2-digit'});
  const configured = text => /configured/i.test(text || '') && !/not configured/i.test(text || '');

  // ---- build ----
  view.classList.add('cd-on');
  const header = el('div', 'cd-header');
  const brand = el('div', 'cd-brand', 'TEAGUE INDUSTRIES'); brand.append(el('small', '', 'A BRIGHTER TOMORROW'));
  const title = el('div', 'cd-title'); title.append(el('b', '', 'JARVIS'), el('small', '', 'INTELLIGENCE AMPLIFIES HUMANITY'));
  const facts = el('div', 'cd-facts'); const timeBox = el('div', 'cd-time'); const timeText = el('b'); const dateText = el('small');
  timeBox.append(timeText, dateText);
  const fact = lines => { const s = el('span'); lines.forEach((line, i) => { if (i) s.append(el('br')); s.append(document.createTextNode(line)); }); return s; };
  facts.append(fact(['People', 'Technology', 'A cleaner, brighter tomorrow']), fact(['Local core', '127.0.0.1', 'Keys stay on this PC']), timeBox);
  header.append(brand, title, facts);

  const left = el('div', 'cd-left'); const right = el('div', 'cd-right');
  const [statusPanel, statusMeta] = panel('System status', 'cd-fixed');
  const status = el('div', 'cd-status'); const rows = el('ul', 'cd-rows'); const ring = el('div', 'cd-ring');
  ring.innerHTML = '<svg viewBox="0 0 120 120"><circle class="track" cx="60" cy="60" r="50"></circle><circle class="value" cx="60" cy="60" r="50"></circle></svg>';
  const ringText = el('div'); const ringValue = el('b', '', '-'); ringText.append(ringValue, el('small', '', 'READY'));
  ring.append(ringText); status.append(rows, ring);
  const quote = el('p', 'cd-quote', '"Higher intelligence. A brighter tomorrow."'); quote.append(el('small', '', '- Teague Industries'));
  statusPanel.append(status, el('p', 'cd-note', 'Ready means configured; Settings runs the live checks.'), quote);
  const [devicePanel, deviceMeta] = panel('Devices', 'cd-fixed'); const devices = el('div', 'cd-devices'); devicePanel.append(devices);
  const [knowledgePanel, knowledgeMeta] = panel('Knowledge', 'cd-grow'); const knowledge = el('div', 'cd-knowledge'); knowledgePanel.append(knowledge);
  knowledgeMeta.textContent = 'ON THIS PC';
  left.append(statusPanel, devicePanel, knowledgePanel);

  const [voicePanel, voiceMeta] = panel('Voice input', 'cd-fixed');
  const voiceBox = el('div', 'cd-voice'); const mic = el('div', 'cd-mic'); mic.append(icon('mic'));
  const wave = el('canvas', 'cd-wave'); wave.width = 360; wave.height = 46; const voiceHint = el('p');
  voiceBox.append(mic, wave, voiceHint); voicePanel.append(voiceBox);
  const [diagPanel, diagMeta] = panel('Live diagnostics', 'cd-fixed'); const diag = el('div', 'cd-diagnostics');
  const metric = (label, spark) => { const box = el('div', 'cd-metric'); const value = el('b', '', '-'); const note = el('em', '', '');
    box.append(el('small', '', label), value); let canvas = null; if (spark) { canvas = el('canvas'); canvas.width = 120; canvas.height = 20; box.append(canvas); } else box.append(note);
    diag.append(box); return {value, note, canvas, history: []}; };
  const m = {cpu: metric('Processor', true), memory: metric('Memory', true), disk: metric('Disk'), uptime: metric('Core uptime'),
    response: metric('Last reply'), model: metric('AI model')};
  diagPanel.append(diag, el('p', 'cd-note', 'Graphics, temperature and network are not measured.'));
  const [projectPanel, projectMeta] = panel('Active projects', 'cd-grow'); const projects = el('ul', 'cd-list'); projectPanel.append(projects);
  const [upcomingPanel, upcomingMeta] = panel('Upcoming', 'cd-fixed'); const upcoming = el('ul', 'cd-list'); upcomingPanel.append(upcoming);
  right.append(voicePanel, diagPanel, projectPanel, upcomingPanel);

  const frame = el('div', 'cd-core-frame');
  const labelsLeft = el('ul', 'cd-labels left'); const labelsRight = el('ul', 'cd-labels right');
  const foot = el('div', 'cd-core-foot'); const activity = el('div', 'cd-activity'); activity.append(el('i'));
  const coreMode = el('p', 'cd-mode'); coreMode.setAttribute('aria-live', 'polite');
  foot.append(el('small', '', 'HUMAN POTENTIAL. AMPLIFIED.'), activity, coreMode);
  frame.append(labelsLeft, labelsRight, foot);

  const tiles = el('nav', 'cd-tiles'); tiles.setAttribute('aria-label', 'Sections');
  for (const [name, target, label] of TILES) {
    const b = el('button', target === 'command' ? 'active' : ''); b.type = 'button'; b.append(icon(name), el('span', '', label));
    b.addEventListener('click', () => { const nav = document.querySelector(`.nav[data-view="${target}"]`);
      if (nav) nav.click(); else if (typeof window.view === 'function') window.view(target); });
    tiles.append(b);
  }
  view.append(header, left, frame, tiles, right);

  // ---- render from real data ----
  let metrics = null, metricsOk = false, metricsTried = false, workspaces = null;
  const list = (target, items, empty) => { target.replaceChildren(...(items.length ? items : [el('li', 'cd-empty', empty)])); };

  function render() {
    const now = new Date();
    timeText.textContent = now.toLocaleTimeString(undefined, {hour: 'numeric', minute: '2-digit'}).toUpperCase();
    const zone = new Intl.DateTimeFormat(undefined, {timeZoneName: 'short'}).formatToParts(now).find(p => p.type === 'timeZoneName');
    dateText.textContent = now.toLocaleDateString(undefined, {weekday: 'short', day: 'numeric', month: 'short', year: 'numeric'}).toUpperCase() + (zone ? DOT + zone.value : '');
    const d = data(); const caps = (d && d.capabilities) || {};
    const connection = (document.querySelector('#connection') || {}).textContent || '';
    const online = !!d && connection !== 'CONNECTION LOST';
    const brain = caps.brain || '';
    const aiOk = configured(brain);
    const settings = (d && d.settings) || {};
    const voiceKind = settings.voice_profile && settings.voice_profile !== 'auto' ? settings.voice_profile : caps.voice_provider;
    const deviceList = (d && d.devices) || [];
    const connected = deviceList.filter(x => x.connected && !x.simulated);  // a simulated device is shown, never counted
    const searchName = /serpapi/i.test(caps.search || '') ? 'SERPAPI READY' : /brave/i.test(caps.search || '') ? 'BRAVE READY' : caps.search ? 'BEST EFFORT' : 'UNKNOWN';
    const statusRows = [
      ['Core', online ? 'ok' : 'off', online ? 'ONLINE' : 'OFFLINE'],
      ['AI provider', aiOk ? 'ok' : 'warn', aiOk ? brain.split(' ')[0].toUpperCase() + ' READY' : /unsupported/i.test(brain) ? 'CHECK SETTING' : 'NO KEY'],
      ['Memory', d ? 'ok' : 'off', d ? (d.memory || []).length + ' SAVED' : 'UNKNOWN'],
      ['Voice', voiceKind ? 'ok' : 'off', ({qwen: 'QWEN VOICE', fish: 'FISH AUDIO', openai: 'OPENAI VOICE', browser: 'BROWSER VOICE'})[voiceKind] || 'UNKNOWN'],
      ['Web search', caps.search ? 'ok' : 'off', searchName],
      ['Devices', connected.length ? 'ok' : 'off', connected.length + ' ONLINE']];
    rows.replaceChildren(...statusRows.map(([name, cls, text]) => { const li = el('li', cls); li.append(el('i'), el('span', '', name), el('em', '', text)); return li; }));
    const ready = statusRows.filter(r => r[1] === 'ok').length;
    ringValue.textContent = ready + '/' + statusRows.length;
    const circle = ring.querySelector('.value'); const length = 2 * Math.PI * 50;
    circle.style.strokeDasharray = String(length); circle.style.strokeDashoffset = String(length * (1 - ready / statusRows.length));
    statusMeta.textContent = ready === statusRows.length ? 'ALL SYSTEMS READY' : (statusRows.length - ready) + ' NEED ATTENTION';

    const find = re => deviceList.find(x => re.test(x.device_id));
    const deviceTiles = [['workstation', 'Workstation', find(/^pc$/)], ['mobile', 'Mobile', find(/phone|mobile/i)], ['glasses', 'Glasses', find(/glass|wear/i)]];
    devices.replaceChildren(...deviceTiles.map(([kind, name, device]) => {
      const ok = device && device.connected && !device.simulated; const tile = el('div', 'cd-device' + (ok ? ' ok' : ''));
      tile.append(icon(kind), el('b', '', name.toUpperCase()),
        el('small', '', ok ? 'Online' : device && device.connected ? 'Simulated only' : device ? 'Offline' : 'Not paired'));
      return tile; }));
    deviceMeta.textContent = connected.length + ' CONNECTED';

    const count = key => d && Array.isArray(d[key]) ? String(d[key].length) : '-';
    knowledge.replaceChildren(...[['memory', 'Memories'], ['documents', 'Documents'], ['notes', 'Notes'], ['conversations', 'Conversations']].map(([key, label]) => {
      const box = el('div'); box.append(el('b', '', count(key)), el('small', '', label)); return box; }));

    const mode = (typeof state !== 'undefined' && state.mode) || 'standby';
    coreMode.classList.toggle('offline', !online);
    coreMode.textContent = online ? MODES[mode] || mode.toUpperCase() : 'CORE OFFLINE';
    activity.className = 'cd-activity ' + mode;
    const label = ([text, on]) => el('li', on ? '' : 'off', text);
    labelsLeft.replaceChildren(...[['ANALYZE', !!caps.vision], ['SYNTHESIZE', aiOk], ['REASON', aiOk], ['EXECUTE', online], ['REMEMBER', !!d]].map(label));
    labelsRight.replaceChildren(...[['VISION', !!caps.vision], ['VOICE', !!voiceKind], ['LANGUAGE', aiOk], ['RESEARCH', !!caps.search], ['APPROVALS', online]].map(label));

    const micOn = typeof state !== 'undefined' && !!state.mic;
    const armed = typeof voice !== 'undefined' && !!voice.armed;
    voiceBox.classList.toggle('on', micOn);
    voiceMeta.textContent = armed ? 'LISTENING' : micOn ? 'WAITING FOR WAKE WORD' : 'MIC OFF';
    voiceHint.textContent = micOn ? 'Say "Hey Jarvis", then your command.' : 'The microphone is off.';

    if (metrics) {
      const cpu = metrics.cpu_percent, memory = metrics.memory, disk = metrics.disk;
      m.cpu.value.replaceChildren(cpu == null ? '-' : String(Math.round(cpu)), el('span', '', cpu == null ? '' : '%'));
      m.memory.value.replaceChildren(memory ? String(memory.used_percent) : '-', el('span', '', memory ? '%' : ''));
      m.disk.value.replaceChildren(disk ? String(Math.round(disk.used_percent)) : '-', el('span', '', disk ? '%' : ''));
      m.disk.note.textContent = disk ? gb(disk.free_bytes) + ' GB free' : 'not readable';
      m.uptime.value.textContent = duration(metrics.core_uptime_seconds); m.uptime.note.textContent = 'this Core session';
      m.response.value.textContent = metrics.last_response_ms == null ? '-' : (metrics.last_response_ms / 1000).toFixed(1) + ' s';
      m.response.note.textContent = metrics.last_response_ms == null ? 'no reply yet' : 'last completed request';
    }
    m.model.value.textContent = aiOk && caps.model ? caps.model : '-'; m.model.value.title = aiOk ? caps.model || '' : '';
    m.model.note.textContent = aiOk ? brain.split(' ')[0] : 'AI not configured';
    diagMeta.textContent = metricsOk ? 'THIS PC' + DOT + 'LIVE' : metricsTried ? 'NOT READING' : 'READING...';
    for (const item of [m.cpu, m.memory]) spark(item);

    const tasks = (d && d.tasks) || [];
    const projectItems = (workspaces || []).slice(0, 5).map(p => {
      const linked = (p.links || []).filter(x => x.kind === 'task');
      const done = linked.filter(x => (tasks.find(t => t.id === x.ref) || {}).completed).length;
      const li = el('li', 'cd-project'); const name = el('div'); name.append(el('b', '', p.name),
        el('small', '', linked.length ? done + ' of ' + linked.length + ' tasks done' : (p.links || []).length + ' linked items' + DOT + 'no tasks'));
      const bar = el('div', 'cd-bar'); const fill = el('i'); bar.append(fill);
      const pct = linked.length ? Math.round(done * 100 / linked.length) : null;
      if (pct === null) bar.hidden = true; else fill.style.width = pct + '%';
      li.append(name, bar, el('em', '', pct === null ? '' : pct + '%')); return li; });
    list(projects, projectItems, workspaces ? 'No projects yet. Create one in Projects.' : 'Loading projects...');
    projectMeta.textContent = workspaces ? workspaces.length + ' SAVED' : '';

    const nowS = Date.now() / 1000; const end = new Date(); end.setHours(24, 0, 0, 0); const endS = end.getTime() / 1000;
    const events = [...((d && d.reminders) || []).filter(r => !r.fired && r.due >= nowS && r.due < endS).map(r => [r.due, r.title, 'Reminder']),
      ...tasks.filter(t => !t.completed && t.due && t.due >= nowS && t.due < endS).map(t => [t.due, t.body, 'Task'])].sort((a, b) => a[0] - b[0]);
    list(upcoming, events.slice(0, 4).map(([due, text, kind]) => { const li = el('li', 'cd-event'); const t = el('time', '', clock(due));
      li.append(t, el('span', '', text), el('small', '', kind)); return li; }), 'Nothing scheduled for the rest of today.');
    upcomingMeta.textContent = events.length + ' TODAY';
  }

  function spark(item) {
    const c = item.canvas; if (!c) return; const g = c.getContext('2d'); g.clearRect(0, 0, c.width, c.height);
    const h = item.history; if (h.length < 2) return;
    g.strokeStyle = '#3ed1ff'; g.lineWidth = 1.5; g.beginPath();
    h.forEach((v, i) => { const x = i * c.width / (h.length - 1), y = c.height - 2 - v / 100 * (c.height - 4); i ? g.lineTo(x, y) : g.moveTo(x, y); });
    g.stroke();
  }

  async function poll(force) {
    if (!force && !visible()) return;
    try {
      metrics = await api('/api/metrics'); metricsOk = true;
      if (metrics.cpu_percent != null) m.cpu.history.push(metrics.cpu_percent);
      if (metrics.memory) m.memory.history.push(metrics.memory.used_percent);
      for (const item of [m.cpu, m.memory]) if (item.history.length > 40) item.history.shift();
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
    g.strokeStyle = '#3ed1ff'; g.lineWidth = 1.5; g.shadowColor = '#3ed1ff'; g.shadowBlur = 6; g.beginPath();
    const live = typeof state !== 'undefined' && state.mic ? analyserFor() : null;
    if (live) {
      live.getFloatTimeDomainData(samples);
      for (let i = 0; i < samples.length; i += 4) { const x = i / (samples.length - 1) * w, y = h / 2 + samples[i] * h * 2.2; i ? g.lineTo(x, y) : g.moveTo(x, y); }
    } else {
      const fresh = typeof voiceDiagnostic !== 'undefined' && voiceDiagnostic.frameAt && performance.now() - voiceDiagnostic.frameAt < 400;
      levels.push(fresh ? Math.min(1, (voiceDiagnostic.level || 0) * 8) : 0); if (levels.length > 72) levels.shift();
      levels.forEach((v, i) => { const x = i * w / 71, a = v * h / 2; g.moveTo(x, h / 2 - a); g.lineTo(x, h / 2 + a + 0.5); });
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
  // Coming back to the Command view or to the window: read at once rather than at the next interval.
  let wasVisible = visible();
  const resume = () => { const now = visible(); if (now && !wasVisible) { poll(); pollProjects(); render(); } wasVisible = now; };
  document.addEventListener('visibilitychange', resume);
  new MutationObserver(resume).observe(view, {attributes: true, attributeFilter: ['class']});
  requestAnimationFrame(frameLoop);
})();
