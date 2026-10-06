// Connectors (1.0.17, item G of docs/PHONE-ACCESS-PLAN.md; the owner's steps in docs/GOOGLE-STEPS.md): Gmail and
// Google Calendar as the Core reports them. Settings > Connections. The Core decides what is configured
// (capabilities.mail_connected, calendar_connected: true only when the key file has the lines); this file shows it and
// runs the owner's TEST through /api/connections/test. No address, password or calendar link is ever shown.
const JarvisConnectors = {
  CARDS: [
    {service: 'mail', title: 'Gmail', flag: 'mail_connected',
     what: 'Search and read your mail when you ask; send a mail only after you approve it on screen. Marks nothing read.',
     setup: 'An app password and your address in the key file (docs/GOOGLE-STEPS.md, part 1), then start JARVIS again.'},
    {service: 'calendar', title: 'Google Calendar', flag: 'calendar_connected',
     what: 'Your events for a question, the daily briefing and the phone\'s Upcoming panel. Reading only.',
     setup: 'The calendar\'s secret address in iCal format in the key file (docs/GOOGLE-STEPS.md, part 2), then start JARVIS again.'},
  ],
  // One line of state for a card, from the Core's capability flags only.
  stateText(caps, card) {
    if (!caps) return 'Not known yet';
    return caps[card.flag] ? 'Configured' : 'Not configured';
  },
  stateClass(caps, card) { return caps && caps[card.flag] ? 'ok' : 'off'; },
  // The result of a TEST in words.
  resultText(result) {
    if (!result) return '';
    const when = result.checked_at ? new Date(result.checked_at * 1000).toLocaleTimeString() : '';
    const head = {passed: 'OK', failed: 'FAILED', not_configured: 'NOT CONFIGURED', manual_check: 'CHECK BY HAND'}[result.status] || String(result.status || '').toUpperCase();
    return head + (when ? ' at ' + when : '') + (result.detail ? ': ' + result.detail : '');
  },
};
if (typeof module !== 'undefined') module.exports = JarvisConnectors;

if (typeof document !== 'undefined') (() => {
  'use strict';
  if (document.querySelector('.connectors-panel')) return;
  const q = s => document.querySelector(s);
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  const button = (text, cls, onclick) => { const b = el('button', cls, text); b.type = 'button'; b.onclick = onclick; return b; };
  const inspecting = () => !!window.JARVIS_INSPECTION;

  const sheet = document.createElement('link'); sheet.rel = 'stylesheet'; sheet.href = '/connectors.css'; document.head.append(sheet);
  const panel = el('section', 'connectors-panel');
  panel.append(el('h3', '', 'Connectors'), el('p', 'connectors-note',
    'Your mail and your calendar, read when you ask; once a phone shows its Overview, the unread count and the next day\'s events are also read in the background every few minutes. Each is set up once by lines in your key file (docs/GOOGLE-STEPS.md); ' +
    'nothing here shows an address, a password or a link. Whatever JARVIS reads goes to the AI provider with your question, as every question does.'));
  const cards = el('div', 'connectors-cards');
  panel.append(cards);
  const category = q('.ti-settings-group[data-setting="Connections"]'), settingsView = q('#settingsView');
  if (category) category.append(panel); else if (settingsView) settingsView.append(panel);

  const states = {};
  function render(caps) {
    cards.replaceChildren();
    for (const card of JarvisConnectors.CARDS) {
      const node = el('article', 'connector-card ' + JarvisConnectors.stateClass(caps, card));
      const head = el('div', 'connector-head');
      head.append(el('b', '', card.title), el('span', 'connector-state', JarvisConnectors.stateText(caps, card)));
      const what = el('p', 'connectors-note', card.what), setup = el('p', 'connectors-note', card.setup);
      const result = el('p', 'connector-result', JarvisConnectors.resultText(states[card.service]));
      result.setAttribute('role', 'status');
      const test = button('TEST', 'outline', async () => {
        test.disabled = true; result.textContent = 'Testing…';
        try { states[card.service] = await api('/api/connections/test', {service: card.service}); }
        catch (e) { states[card.service] = {status: 'failed', detail: e.message}; }
        result.textContent = JarvisConnectors.resultText(states[card.service]); test.disabled = false;
      });
      node.append(head, what, setup, test, result);
      cards.append(node);
    }
  }
  async function load() {
    if (inspecting()) { cards.textContent = 'Not shown during an inspection.'; return; }
    const known = (typeof state !== 'undefined' && state && state.data && state.data.capabilities) || null;
    if (known) { render(known); return; }
    try { render((await api('/api/state')).capabilities); } catch (e) { render(null); }
  }
  const settingsNav = q('.nav[data-view="settings"]'); if (settingsNav) settingsNav.addEventListener('click', load);
  const categoryButton = q('[data-settings-category="Connections"]'); if (categoryButton) categoryButton.addEventListener('click', load);
  load();
})();
