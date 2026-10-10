// The You page (1.0.19, about_you.py, docs/ABOUT-YOU.md; the owner's "lets make jarvis and me more connected
// personally", "He knows my life"): a panel at the top of the Memory section with what the owner told JARVIS about
// their life. JARVIS reads a short summary of it with every question and may offer to add to it; an offer is an
// approval card, and nothing is kept until the owner approves it. This file shows the entries and sends the owner's
// own clicks (GET and POST /api/profile).
const JarvisYou = {
  SECTIONS: ['about', 'person', 'date', 'like', 'dislike', 'goal'],
  NAMES: {about: 'About you', person: 'People', date: 'Dates', like: 'Likes', dislike: 'Dislikes', goal: 'Goals'},
  MONTHS: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
  // What the add form asks for in each section: the title's label and example, the detail's (none when empty), and
  // the date's label (none when empty; "optional" when it may stay empty).
  FORM: {
    about: {title: 'A line about you', example: 'For example: I work as an electrician in Sydney', detail: '', date: ''},
    person: {title: 'Name', example: 'For example: Will', detail: 'Who they are to you, for example: brother', date: 'Birthday (optional)'},
    date: {title: 'What it is', example: 'For example: Wedding anniversary', detail: 'A note (optional)', date: 'The date'},
    like: {title: 'Something you like', example: 'For example: AC/DC', detail: '', date: ''},
    dislike: {title: 'Something you dislike', example: 'For example: long answers', detail: '', date: ''},
    goal: {title: 'A goal', example: 'For example: run 10 km by Christmas', detail: 'A note (optional)', date: ''},
  },
  // The entries grouped by section, in the page's order; empty sections are left out.
  grouped(entries) {
    const groups = [];
    for (const id of JarvisYou.SECTIONS) {
      const rows = (entries || []).filter(e => e.section === id);
      if (rows.length) groups.push({id, name: JarvisYou.NAMES[id], rows});
    }
    return groups;
  },
  countText(n) { return n === 1 ? '1 entry' : n + ' entries'; },
  // The fields the Core is sent for an add: the date only where the section has one, and only when the day and the
  // month are both chosen; the year only when written.
  addBody(section, title, detail, day, month, year) {
    const body = {action: 'add', section, title: String(title || '').trim(), detail: JarvisYou.FORM[section] && JarvisYou.FORM[section].detail ? String(detail || '').trim() : ''};
    if (JarvisYou.FORM[section] && JarvisYou.FORM[section].date && day && month) {
      body.day = Number(day); body.month = Number(month);
      if (String(year || '').trim()) body.year = Number(year);
    }
    return body;
  },
};
if (typeof module !== 'undefined') module.exports = JarvisYou;

if (typeof document !== 'undefined') (() => {
  'use strict';
  if (document.querySelector('.you-panel')) return;
  const q = s => document.querySelector(s);
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  const button = (text, cls, onclick) => { const b = el('button', cls, text); b.type = 'button'; b.onclick = onclick; return b; };
  const inspecting = () => !!window.JARVIS_INSPECTION;

  const sheet = document.createElement('link'); sheet.rel = 'stylesheet'; sheet.href = '/you.css'; document.head.append(sheet);
  const panel = el('section', 'panel you-panel');
  const heading = el('div', 'panel-heading'), count = el('span', 'you-count', '');
  heading.append(el('h2', '', 'YOU'), count);
  panel.append(heading, el('p', 'you-note', 'What JARVIS knows about your life. A short summary goes with every question you ask, to the AI ' +
    'service like everything you ask. JARVIS may offer to add something you mention; nothing is kept until you approve it. ' +
    'Passwords and keys do not belong here.'));
  const soon = el('div', 'you-soon'), list = el('div', 'you-list'), form = el('div', 'you-add');
  list.setAttribute('aria-live', 'polite');
  panel.append(soon, list, form);
  const grid = q('#memoryView .memory-grid'), view = q('#memoryView');
  if (grid) grid.prepend(panel); else if (view) view.append(panel);

  function addForm() {
    form.replaceChildren(el('h3', '', 'Add to your page'));
    const section = el('select'); section.setAttribute('aria-label', 'Section');
    for (const id of JarvisYou.SECTIONS) { const o = el('option', '', JarvisYou.NAMES[id]); o.value = id; section.append(o); }
    const title = el('input'); title.maxLength = 200; title.setAttribute('aria-label', 'Title');
    const detail = el('input'); detail.maxLength = 300; detail.setAttribute('aria-label', 'Detail');
    const day = el('input'); day.type = 'number'; day.min = 1; day.max = 31; day.placeholder = 'Day'; day.setAttribute('aria-label', 'Day');
    const month = el('select'); month.setAttribute('aria-label', 'Month');
    month.append(Object.assign(el('option', '', 'Month'), {value: ''}));
    JarvisYou.MONTHS.forEach((name, i) => { const o = el('option', '', name); o.value = String(i + 1); month.append(o); });
    const year = el('input'); year.type = 'number'; year.min = 1900; year.placeholder = 'Year'; year.setAttribute('aria-label', 'Year');
    const dateLabel = el('span', 'you-date-label'), date = el('div', 'you-date');
    date.append(dateLabel, day, month, year);
    const add = button('ADD', 'primary', async () => {
      add.disabled = true;
      try {
        render(await api('/api/profile', JarvisYou.addBody(section.value, title.value, detail.value, day.value, month.value, year.value)));
        toast('Added to your page.'); title.value = detail.value = day.value = year.value = ''; month.value = '';
      } catch (e) { toast(e.message, true); }
      add.disabled = false;
    });
    function shape() {
      const spec = JarvisYou.FORM[section.value];
      title.placeholder = spec.title + ' (' + spec.example.replace(/^For example: /, 'e.g. ') + ')';
      detail.hidden = !spec.detail; detail.placeholder = spec.detail;
      date.hidden = !spec.date; dateLabel.textContent = spec.date;
    }
    section.onchange = shape;
    for (const input of [title, detail, day, year]) input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); add.click(); } });
    shape();
    form.append(section, title, detail, date, add);
  }
  function render(data) {
    const entries = (data && data.entries) || [];
    count.textContent = JarvisYou.countText(entries.length);
    const coming = (data && data.coming_up) || [];
    soon.replaceChildren();
    if (coming.length) {
      soon.append(el('h3', '', 'Coming up'));
      for (const line of coming) soon.append(el('p', 'you-soon-line', line));
    }
    list.replaceChildren();
    if (!entries.length) list.append(el('p', 'you-note', 'Nothing yet. Add the people who matter, dates to remember, what you like and your goals below, ' +
      'or tell JARVIS about them and approve what he offers to keep.'));
    for (const group of JarvisYou.grouped(entries)) {
      list.append(el('h3', '', group.name));
      for (const row of group.rows) {
        const line = el('div', 'saved-item you-entry');
        line.append(el('span', '', row.line), button('REMOVE', 'text-button', async () => {
          try { render(await api('/api/profile', {action: 'remove', id: row.id})); } catch (e) { toast(e.message, true); }
        }));
        list.append(line);
      }
    }
  }
  async function load() {
    if (inspecting()) { list.textContent = 'Not shown during an inspection.'; return; }
    try { render(await api('/api/profile')); } catch (e) { if (!list.children.length) list.textContent = e.message; }
  }
  addForm();
  const memoryNav = q('.nav[data-view="memory"]'); if (memoryNav) memoryNav.addEventListener('click', load);
  load();
})();
