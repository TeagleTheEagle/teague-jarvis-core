// Permissions in one place (1.0.15, docs/PERMISSIONS.md): the emergency stop that holds, shown on screen, and the
// table of what every tool may do with the owner's switch for each one (Settings > Permissions).
// The Core decides everything (permissions.py, server.App.tool); this file only shows it and sends the owner's clicks.
const JarvisPermissions = {
  // The same words the Core accepts (permissions.STOP_PHRASE). test_permissions.py holds the two equal.
  // Capitals and punctuation do not matter: speech recognition adds its own ("Emergency, stop."). Anything else
  // in the message (a digit, an emoji, a word in another script) means it is not the stop: "stop all 3".
  STOP_PHRASE: /^(?:(?:hey|ok|okay) )?(?:jarvis )?(?:emergency stop|stop everything|stop all|kill switch)(?: (?:now|please))?(?: jarvis)?$/,
  // Blanks and the ASCII marks except the underscore, the curly quotes, the dashes and the ellipsis: the same set,
  // character for character, as permissions._STOP_SEPARATORS.
  STOP_SEPARATORS: /[ \t\n\r\f\v !-\/:-@\[-\^`{-~‘’“”…–—]+/g,
  stopPhrase(text) {
    if (typeof text !== 'string' || Array.from(text).length > 80) return false;
    return JarvisPermissions.STOP_PHRASE.test(text.toLowerCase().replace(JarvisPermissions.STOP_SEPARATORS, ' ').replace(/^ +| +$/g, ''));
  },
  // The window answers a few exact commands by itself (a section, the microphone, a timer's status, an
  // inspection). They obey the same switches as the Core: while the emergency stop holds, or when the owner's
  // switch for the matching tool is not "Allowed", the window does not act and the words go to the Core, which
  // refuses, asks first or answers. `data` is the Core's state; before the first state the window may act.
  windowMay(data, tool) {
    if (!data) return true;
    if (data.control && data.control.stopped) return false;
    const mode = tool && data.permissions ? data.permissions[tool] : null;
    return !mode || mode === 'default';
  },
  // The words for one switch position of one tool.
  modeText(row, mode) {
    if (mode === 'ask') return 'Ask first';
    if (mode === 'off') return 'Off';
    return row.asks === 'always' ? 'Always asks' : row.asks === 'your own words' ? 'On your words only' : 'Allowed';
  },
  // What the table says about asking, for one row as the Core lists it.
  asksText(row) {
    if (row.mode === 'off') return 'Off: JARVIS cannot do this when answering.';
    if (row.asks === 'always') return 'Always asks you on screen first.';
    if (row.mode === 'ask') return 'Asks you on screen first (your switch).';
    if (row.asks === 'your own words') return 'Only when your own words ask for exactly this.';
    return row.effect === 'changes' ? 'Does not ask first.' : '';
  },
  // The line of the stop banner: when and from where.
  stopText(control, now) {
    if (!control || !control.stopped) return '';
    const since = typeof control.since === 'number' ? new Date(control.since * 1000) : null;
    const sameDay = since && now && since.toDateString() === now.toDateString();
    const when = !since ? '' : ' Stopped ' + (sameDay ? 'at ' : 'on ' + since.toLocaleDateString() + ' at ') + since.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
    const where = !control.device ? '' : control.device === 'pc' ? ' on this PC' : ' from ' + String(control.device).replaceAll('-', ' ');
    return 'JARVIS answers nothing and does nothing until you resume.' + when + (when ? where + '.' : '') +
      (control.saved === false ? ' The stop could not be saved to disk: it holds until JARVIS is restarted.' : '');
  },
};
if (typeof module !== 'undefined') module.exports = JarvisPermissions;

if (typeof document !== 'undefined') (() => {
  'use strict';
  if (document.querySelector('.es-banner')) return;
  const q = s => document.querySelector(s);
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  const inspecting = () => !!window.JARVIS_INSPECTION;
  const style = href => { const link = document.createElement('link'); link.rel = 'stylesheet'; link.href = href; document.head.append(link); };
  style('/permissions.css');
  // The owner's own style sheet (config folder), after every other style. Empty until a style change is approved.
  if (!inspecting()) style('/owner-style.css');

  const core = () => (typeof state !== 'undefined' ? state : null);
  const control = () => { const s = core(); return (s && s.data && s.data.control) || null; };
  const refreshNow = async () => { try { if (typeof refresh === 'function') await refresh(); } catch (e) { /* the connection light already says so */ } tick(); };

  let silencedAt = 0;  // when this window last silenced itself for a stop
  async function silence() {
    if (Date.now() - silencedAt < 5000) return;  // once per stop
    silencedAt = Date.now();
    try { if (typeof stop === 'function') await stop(); } catch (e) { /* silencing this window is best effort */ }
    // Screen sharing ends as well, as it does for a stop from the tray or the shortcut.
    try { if (typeof stopScreenVision === 'function') stopScreenVision(); } catch (e) { /* best effort */ }
  }
  async function emergencyStop(reason) {
    let reached = true;
    try { await api('/api/emergency-stop', {reason: String(reason || 'Stop button in the JARVIS window').slice(0, 120)}); }
    catch (e) { reached = false; toast('The emergency stop did not reach the Core (' + e.message + '). This window was silenced; JARVIS itself may still be running.', true); }
    await silence();
    await refreshNow();
    return reached;
  }
  async function resume() {
    try { await api('/api/resume', {}); toast('JARVIS resumed.'); } catch (e) { toast(e.message, true); }
    await refreshNow();
  }
  window.jarvisEmergencyStop = emergencyStop;

  // ---- the stop button: under the left end of the header in every section ----
  const stopButton = el('button', 'es-button', 'STOP ALL'); stopButton.type = 'button'; stopButton.id = 'emergencyStop';
  stopButton.title = 'Emergency stop: JARVIS stops and stays stopped until you resume.';
  stopButton.setAttribute('aria-label', 'Emergency stop: stop JARVIS and keep it stopped until you resume');
  stopButton.onclick = () => emergencyStop('Stop button in the JARVIS window');
  const topbar = q('.topbar'), actions = q('.top-actions');
  if (topbar && q('.hz-strip')) topbar.append(stopButton);
  else if (actions) { stopButton.classList.add('inline'); actions.append(stopButton); }

  // ---- the banner while the stop holds ----
  const banner = el('div', 'es-banner'); banner.hidden = true; banner.setAttribute('role', 'alert');
  const words = el('div', 'es-banner-text'), detail = el('span');
  words.append(el('b', '', 'EMERGENCY STOP IS ON'), detail);
  const resumeButton = el('button', 'es-resume', 'RESUME JARVIS'); resumeButton.type = 'button'; resumeButton.onclick = resume;
  banner.append(words, resumeButton); document.body.append(banner);

  // ---- Settings > Permissions ----
  const panel = el('section', 'permissions-panel');
  const intro = el('p');
  intro.append('What JARVIS may do, in one place. ', el('b', '', 'Allowed'), ' is how it works today. ', el('b', '', 'Ask first'),
    ': JARVIS asks you on screen before it does that. ', el('b', '', 'Off'), ': JARVIS cannot do it when answering; your own buttons in the interface still work. ',
    'A change JARVIS makes to itself always asks, and an installed JARVIS never changes its own program files. Each switch is saved the moment you change it.');
  const stopRow = el('div', 'perm-stop'), stopWords = el('div'), stopState = el('b'), stopDetail = el('span');
  const stopToggle = el('button'); stopToggle.type = 'button';
  stopWords.append(stopState, stopDetail); stopRow.append(stopWords, stopToggle);
  const table = el('div', 'perm-table'); table.setAttribute('aria-live', 'polite');
  panel.append(intro, stopRow, table);
  // Its own category in Settings (static/teague.js builds the categories); without them, the top of the page.
  const category = q('.ti-settings-group[data-setting="Permissions"]'), settingsView = q('#settingsView');
  if (category) category.append(panel); else if (settingsView) { panel.prepend(el('h2', '', 'Permissions')); settingsView.prepend(panel); }

  function rowNode(row) {
    const node = el('div', 'perm-row' + (row.mode !== 'default' ? ' changed' : ''));
    const name = el('div', 'perm-name'); name.append(el('b', '', row.label)); if (row.note) name.append(el('small', '', row.note));
    const facts = el('div', 'perm-facts');
    facts.append(el('span', 'perm-effect ' + row.effect, (row.effect === 'changes' ? 'Changes' : 'Reads') + ' · ' + row.reach));
    if (row.effect === 'changes') facts.append(el('span', '', 'Undo: ' + row.undo));
    const asks = JarvisPermissions.asksText(row); if (asks) facts.append(el('span', '', asks));
    if (row.repeat_adds) facts.append(el('span', '', 'Done twice, it happens twice.'));
    if (row.wearable) facts.append(el('span', '', 'Glasses may use it.'));
    const select = el('select'); select.setAttribute('aria-label', 'Your switch for: ' + row.label);
    for (const mode of row.modes) select.add(new Option(JarvisPermissions.modeText(row, mode), mode));
    select.value = row.mode;
    select.onchange = async () => {
      select.disabled = true;
      try { render(await api('/api/permissions', {tool: row.name, mode: select.value})); toast(row.label + ': ' + JarvisPermissions.modeText(row, select.value) + '.'); }
      catch (e) { toast(e.message, true); await load(); }
      await refreshNow();  // the commands this window answers by itself obey the new position at once
    };
    node.append(name, facts, select); return node;
  }
  function render(data) {
    const rows = (data && data.tools) || [], changes = rows.filter(r => r.effect === 'changes'), reads = rows.filter(r => r.effect !== 'changes');
    const open = !!table.querySelector('details[open]');
    table.replaceChildren(el('h3', 'perm-group', 'CHANGES SOMETHING (' + changes.length + ')'), ...changes.map(rowNode));
    const more = el('details'), summary = el('summary', 'perm-group', 'ONLY READS (' + reads.length + ')'); more.open = open;
    more.append(summary, ...reads.map(rowNode)); table.append(more);
  }
  async function load() {
    if (inspecting()) { table.textContent = 'Not shown during an inspection.'; return; }
    try { render(await api('/api/permissions')); } catch (e) { table.textContent = e.message; }
  }
  const settingsNav = q('.nav[data-view="settings"]'); if (settingsNav) settingsNav.addEventListener('click', load);

  // The stop controls stay visible and usable whatever a style sheet says (an approved owner style sheet is loaded
  // last and could otherwise hide them): these few properties are set on the elements themselves, as important.
  const pin = (node, shown) => {
    for (const [name, value] of [['display', shown ? (node === banner ? 'flex' : 'inline-flex') : 'none'], ['visibility', 'visible'], ['opacity', '1'], ['pointer-events', 'auto']])
      if (node.style.getPropertyValue(name) !== value || node.style.getPropertyPriority(name) !== 'important') node.style.setProperty(name, value, 'important');
  };

  // ---- one reading of the stop for the button, the banner and the panel ----
  let last = null, lastText = null;
  function tick() {
    const c = control(), stopped = !!(c && c.stopped), text = JarvisPermissions.stopText(c, new Date());
    pin(banner, stopped); pin(resumeButton, stopped); pin(stopButton, !stopped);
    if (stopped === last && text === lastText) return;
    const before = last; last = stopped; lastText = text;
    document.documentElement.classList.toggle('es-stopped', stopped);
    banner.hidden = !stopped; stopButton.hidden = stopped; detail.textContent = text;
    stopRow.classList.toggle('on', stopped);
    stopState.textContent = stopped ? 'EMERGENCY STOP IS ON' : 'JARVIS is running.';
    stopDetail.textContent = stopped ? text : 'The emergency stop stops everything and keeps JARVIS stopped until you resume here. Also: the tray menu, STOP ALL on the floating JARVIS, the emergency shortcut, or say “emergency stop”.';
    stopToggle.textContent = stopped ? 'RESUME JARVIS' : 'STOP ALL'; stopToggle.className = stopped ? 'es-resume' : 'es-inline-stop';
    stopToggle.onclick = stopped ? resume : () => emergencyStop('Stop button in Settings');
    // Stopped from somewhere else (tray, shortcut, another window, a voice): silence this window too.
    if (stopped && before === false) silence();
  }
  tick(); setInterval(tick, 1000);
  // While stopped, ask the Core more often, so a resume from the tray shows here quickly.
  setInterval(() => { if (last && !document.hidden && !inspecting()) refreshNow(); }, 3000);
  // The desktop app tells the window when its tray, shortcut or floating JARVIS stopped everything.
  if (window.jarvisDesktop && window.jarvisDesktop.onStop) window.jarvisDesktop.onStop(() => { setTimeout(refreshNow, 500); setTimeout(refreshNow, 2000); });
  load();
})();
