// Routine and notices (1.0.17, item F of docs/PHONE-ACCESS-PLAN.md; nudges.py). Settings > Routine: the owner's week
// as blocks (days, start, end, label); the Core finds the collisions (a task or a reminder due during a block or just
// after it) and raises one nudge each, spoken when "Announce due reminders" (proactive) is on. This file shows the
// blocks, sends the owner's clicks, and shows each new notice the Core kept (state.notices) as a toast on the PC.
const JarvisRoutine = {
  DAYS: ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'],
  DAY_NAMES: {MO: 'Mon', TU: 'Tue', WE: 'Wed', TH: 'Thu', FR: 'Fri', SA: 'Sat', SU: 'Sun'},
  // A block in words: "Mon, Wed 18:00 to 19:00: Gym".
  blockText(b) { return b.days.split(',').map(d => JarvisRoutine.DAY_NAMES[d] || d).join(', ') + ' ' + b.start + ' to ' + b.end + ': ' + b.label; },
  // The notices not yet shown as toasts: the ids seen so far are kept, and the first reading seeds them without toasts.
  fresh(notices, seen, first) {
    const out = [];
    for (const n of notices || []) { if (!seen.has(n.id)) { seen.add(n.id); if (!first) out.push(n); } }
    return out;
  },
  noticeText(n) { return ({nudge: 'Nudge: ', announce: '', approval: 'Approval: ', system: 'JARVIS: '}[n.kind] || '') + n.text; },
  // An approval already has its card on the PC's screen: no toast for it there.
  toastable(n) { return !!n && n.kind !== 'approval'; },
};
if (typeof module !== 'undefined') module.exports = JarvisRoutine;

if (typeof document !== 'undefined') (() => {
  'use strict';
  if (document.querySelector('.routine-panel')) return;
  const q = s => document.querySelector(s);
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  const button = (text, cls, onclick) => { const b = el('button', cls, text); b.type = 'button'; b.onclick = onclick; return b; };
  const inspecting = () => !!window.JARVIS_INSPECTION;

  const sheet = document.createElement('link'); sheet.rel = 'stylesheet'; sheet.href = '/routine.css'; document.head.append(sheet);
  const panel = el('section', 'routine-panel');
  panel.append(el('p', 'routine-note', 'Your week as blocks (work, gym, school). When a task with a due time or a reminder falls inside a block or within an ' +
    'hour after it, JARVIS nudges you once as the block is about to start, never again for the same one, and not in quiet hours. ' +
    'Nudges are spoken on this PC when "Announce due reminders and routine nudges" is on in General and the voice is on, and listed on your phone. ' +
    'A block ends on the day it starts: split a night shift into two blocks.'));
  const list = el('div', 'routine-list'), form = el('div', 'routine-add');
  list.setAttribute('aria-live', 'polite');
  panel.append(list, form);
  const category = q('.ti-settings-group[data-setting="Routine"]'), settingsView = q('#settingsView');
  if (category) category.append(panel); else if (settingsView) settingsView.append(panel);

  function addForm() {
    form.replaceChildren(el('h3', '', 'Add a block'));
    const days = el('div', 'routine-days');
    for (const d of JarvisRoutine.DAYS) {
      const label = el('label', 'check-label'), box = el('input'); box.type = 'checkbox'; box.value = d; box.checked = ['MO', 'TU', 'WE', 'TH', 'FR'].includes(d);
      label.append(box, el('span', '', JarvisRoutine.DAY_NAMES[d])); days.append(label);
    }
    const start = el('input'); start.type = 'time'; start.value = '09:00'; start.setAttribute('aria-label', 'Start');
    const end = el('input'); end.type = 'time'; end.value = '17:00'; end.setAttribute('aria-label', 'End');
    const label = el('input'); label.maxLength = 40; label.placeholder = 'Label, for example: Work'; label.setAttribute('aria-label', 'Label');
    const add = button('ADD BLOCK', 'primary', async () => {
      add.disabled = true;
      const chosen = [...days.querySelectorAll('input')].filter(b => b.checked).map(b => b.value);
      try { render(await api('/api/routine', {action: 'add', days: chosen, start: start.value, end: end.value, label: label.value})); toast('Block added.'); label.value = ''; }
      catch (e) { toast(e.message, true); }
      add.disabled = false;
    });
    // Enter in one of these inputs adds the block; it must not submit the preferences form around them.
    for (const input of [start, end, label]) input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); add.click(); } });
    const times = el('div', 'routine-times'); times.append(el('span', '', 'From'), start, el('span', '', 'to'), end);
    form.append(days, times, label, add);
  }
  function render(data) {
    const blocks = (data && data.blocks) || [];
    list.replaceChildren(el('h3', '', 'Your week (' + blocks.length + (blocks.length === 1 ? ' block)' : ' blocks)')));
    if (!blocks.length) list.append(el('p', 'routine-note', 'No blocks yet. Add your working hours, training and classes below.'));
    for (const b of blocks) {
      const row = el('div', 'routine-block');
      row.append(el('span', '', JarvisRoutine.blockText(b)), button('REMOVE', 'text-button', async () => {
        try { render(await api('/api/routine', {action: 'remove', id: b.id})); } catch (e) { toast(e.message, true); }
      }));
      list.append(row);
    }
  }
  async function load() {
    if (inspecting()) { list.textContent = 'Not shown during an inspection.'; return; }
    try { render(await api('/api/routine')); } catch (e) { if (!list.children.length) list.textContent = e.message; }
  }
  addForm();
  const settingsNav = q('.nav[data-view="settings"]'); if (settingsNav) settingsNav.addEventListener('click', load);
  const categoryButton = q('[data-settings-category="Routine"]'); if (categoryButton) categoryButton.addEventListener('click', load);
  load();

  // Notices as toasts: the Core keeps them (state.notices, newest first); each new one is shown once. The first reading
  // seeds the seen ids, so a restart of the window does not replay old notices.
  const seen = new Set();
  let first = true, pausedForPc = false;
  setInterval(() => {
    if (inspecting() || typeof state === 'undefined' || !state || !state.data) return;
    // While the PC makes or plays a sound of its own (a nudge, an announcement), the window's wake detection pauses
    // as it does for the window's own replies, and resumes after unless a reply of the window's own is playing.
    const speaking = !!state.data.speaking;
    if (speaking && !pausedForPc && typeof pauseRecognition === 'function') { pauseRecognition(); pausedForPc = true; }
    else if (!speaking && pausedForPc) {
      pausedForPc = false;
      const ownReply = (typeof speechRequest !== 'undefined' && !!speechRequest) || !!(state.audio && !state.audio.paused);
      if (!ownReply && typeof resumeRecognition === 'function') resumeRecognition();
    }
    for (const n of JarvisRoutine.fresh(state.data.notices, seen, first)) if (JarvisRoutine.toastable(n)) toast(JarvisRoutine.noticeText(n));
    first = false;
  }, 3000);
})();
