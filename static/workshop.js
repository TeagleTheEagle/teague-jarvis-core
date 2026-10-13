// The Workshop (docs/WORKSHOP.md): Settings > Workshop. JARVIS's own folder on this PC, the folders the owner adds,
// the mission time limit, which Python can run a script, the missions (start one, stop one, read the plan and the
// log) and the lessons JARVIS kept. The Core decides and does everything (workshop.py); this panel shows its answers
// and sends the owner's clicks.
const JarvisWorkshop = {
  stateText(state) {
    return {planning: 'Planning', running: 'Running', finished: 'Done', failed: 'Not completed', stopped: 'Stopped'}[state] || String(state || '');
  },
  missionLine(mission) { return JarvisWorkshop.stateText(mission.state) + ': ' + (mission.goal || ''); },
  goalState(state) {
    return {proposed: 'Waiting for your answer', adopted: 'Approved', declined: 'Declined', expired: 'Lapsed unanswered', failed: 'Approved, but could not start'}[state] || String(state || '');
  },
  // A skill (skills.py): know-how JARVIS keeps for a job that comes up again, each one approved by the owner.
  skillState(state) {
    return {proposed: 'Waiting for your answer', active: 'On', off: 'Off', paused: 'Paused', declined: 'Declined',
            expired: 'Lapsed unanswered', replaced: 'Replaced by a newer version'}[state] || String(state || '');
  },
  skillLine(skill) { return JarvisWorkshop.skillState(skill.state) + ': ' + (skill.name || '') + (skill.description ? ' (' + skill.description + ')' : ''); },
  skillUse(skill) {
    const used = Number(skill.used) || 0;
    return 'Read ' + (used === 0 ? 'not yet' : used === 1 ? 'once' : used + ' times') + (skill.script_name ? ' · script ' + skill.script_name : ' · no script') +
      (skill.source ? ' · taken from ' + skill.source : '');
  },
  minutesText(minutes) { return 'A mission may run for up to ' + minutes + ' minute' + (minutes === 1 ? '' : 's') + ' and ' + 60 + ' tool calls; then it stops and reports.'; },
  foldersText(folders) {
    if (!folders || !folders.length) return 'No other folder: JARVIS may use the workshop folder only.';
    return 'JARVIS may also use: ' + folders.join('; ');
  },
  // The folders of the setting the Core would not take, each with its reason (JARVIS's own folders, a folder that is
  // not there, a path that is not full).
  refusedText(rows) {
    if (!rows || !rows.length) return '';
    return 'Not taken: ' + rows.map(r => r.folder + ' (' + r.why + ')').join('; ') + '.';
  },
  // One line about which Python can run a script, from the Core's own status.
  interpreterText(status) {
    if (!status) return '';
    const own = 'JARVIS\'s own Python ' + (status.jarvis_python ? status.jarvis_python.version : '') + ' runs scripts with the shipped packages (nothing can be installed into it)';
    if (status.workshop_env) return own + '; the workshop\'s own environment is ready, so "pip install" and "python" use it.';
    if (status.pc_python) return own + '; the PC\'s Python ' + status.pc_python.version + ' can make the workshop\'s own environment when a package is needed.';
    return own + '; no other Python is installed on this PC, so no package can be installed (installing Python from python.org is your step).';
  },
  lessonText(row) { return row.text + (row.tags ? ' [' + row.tags + ']' : ''); },
  logLine(entry) {
    const when = entry.at ? new Date(entry.at * 1000).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}) + ' ' : '';
    const head = entry.kind === 'step' && entry.step ? 'step ' + entry.step : entry.kind === 'tool' ? (entry.tool || 'tool') : entry.kind;
    return when + head + ': ' + (entry.text || '');
  },
};
if (typeof module !== 'undefined') module.exports = JarvisWorkshop;

if (typeof document !== 'undefined') (() => {
  'use strict';
  if (document.querySelector('.workshop-panel')) return;
  const q = s => document.querySelector(s);
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  const button = (text, cls, onclick) => { const b = el('button', cls, text); b.type = 'button'; b.onclick = onclick; return b; };
  const inspecting = () => !!window.JARVIS_INSPECTION;

  const sheet = document.createElement('link'); sheet.rel = 'stylesheet'; sheet.href = '/workshop.css'; document.head.append(sheet);
  const panel = el('section', 'workshop-panel');
  const intro = el('p', '', 'JARVIS\'s own folder on this PC, where he reads, writes and runs things himself: files, commands, his own Python ' +
    'environment for packages, lessons he keeps from one job to the next, and missions: a goal he plans, carries out step by step, ' +
    'checks and corrects on his own, then reports. Say "Jarvis, start a mission: ..." or type a goal below. Every tool a mission uses ' +
    'obeys its switch in Settings > Permissions; the emergency stop ends a mission at once.');
  const folderLine = el('p', 'workshop-folder'), foldersBox = el('div', 'workshop-folders'), minutesBox = el('div', 'workshop-minutes'),
        pythonLine = el('p', 'workshop-python'), missionBox = el('div', 'workshop-missions'), lessonBox = el('div', 'workshop-lessons'),
        skillBox = el('div', 'workshop-skills');
  missionBox.setAttribute('aria-live', 'polite');
  panel.append(intro, folderLine, pythonLine, foldersBox, minutesBox, missionBox, skillBox, lessonBox);
  const category = q('.ti-settings-group[data-setting="Workshop"]'), settingsView = q('#settingsView');
  if (category) category.append(panel); else if (settingsView) { panel.prepend(el('h2', '', 'Workshop')); settingsView.prepend(panel); }

  let busy = false;
  async function act(body, said) {
    if (busy) return false;
    busy = true;
    let ok = true;
    try { const answer = await api('/api/workshop', body); if (said !== false) toast(answer.message || 'Done.'); }
    catch (e) { toast(e.message, true); ok = false; }
    busy = false;
    await load();
    return ok;
  }
  async function save(values, said) {
    try { await api('/api/settings', values); toast(said || 'Saved.'); } catch (e) { toast(e.message, true); }
    await load();
  }

  function renderFolders(data) {
    if (foldersBox.contains(document.activeElement)) return;
    const input = el('input'); input.maxLength = 2000; input.value = data.folders_setting || '';
    input.placeholder = 'D:\\Projects;C:\\Users\\you\\Documents\\scripts'; input.setAttribute('aria-label', 'Other folders JARVIS may use, separated by semicolons');
    const note = el('p', 'workshop-note', JarvisWorkshop.foldersText(data.extra_folders));
    const refused = JarvisWorkshop.refusedText(data.refused_folders);
    foldersBox.replaceChildren(el('h3', '', 'Other folders JARVIS may use'), note, ...(refused ? [el('p', 'workshop-note warn', refused)] : []), input,
      button('SAVE', 'outline', () => save({workshop_folders: input.value.trim()}, 'Folders saved.')),
      el('p', 'workshop-note', 'A command JARVIS runs starts in a workshop folder and can reach what your account can on this PC; JARVIS\'s own config, data and program folders and its key file are refused by name. Commands ship as "ask first": you approve each one on the PC before it runs. For a mission to run commands unattended, set "Run commands on this PC in the workshop" to Allowed in Settings > Permissions.'));
  }

  function renderMinutes(data) {
    if (minutesBox.contains(document.activeElement)) return;
    const input = el('input'); input.type = 'number'; input.min = 1; input.max = 180; input.value = data.minutes; input.setAttribute('aria-label', 'Mission time limit in minutes');
    minutesBox.replaceChildren(el('h3', '', 'Mission time limit'), el('p', 'workshop-note', JarvisWorkshop.minutesText(data.minutes)), input,
      button('SAVE', 'outline', () => save({workshop_minutes: Number(input.value)}, 'Time limit saved.')));
  }

  function renderMissions(data) {
    const goalBox = missionBox.querySelector('textarea');
    const typed = goalBox && goalBox.value;
    if (document.activeElement === goalBox) return;  // a goal being typed stays
    const goal = el('textarea'); goal.rows = 3; goal.maxLength = 4000; goal.placeholder = 'The goal, in a sentence or two: for example "Write a Python script that lists the ten largest files in the workshop, and make it run."';
    goal.setAttribute('aria-label', 'Mission goal'); if (typed) goal.value = typed;
    // The goal box is emptied on a start that the Core accepted; on a refusal the words come back.
    const start = button('START MISSION', 'primary', async () => { const text = goal.value.trim(); goal.value = ''; if (!(await act({action: 'start', goal: text}))) { const box = missionBox.querySelector('textarea'); if (box) box.value = text; } });
    start.disabled = !!data.running;
    const controls = el('div', 'workshop-controls'); controls.append(start);
    if (data.running) controls.append(button('STOP THE MISSION', 'text-button', () => act({action: 'stop'})));
    const rows = (data.missions || []).map(m => {
      const node = el('article', 'workshop-mission ' + (m.state === 'running' || m.state === 'planning' ? 'ok' : m.state === 'finished' ? '' : 'warn'));
      node.append(el('b', '', JarvisWorkshop.missionLine(m)));
      if (m.plan && m.plan.length) { const ol = el('ol', 'workshop-plan'); m.plan.forEach(s => ol.append(el('li', '', s))); node.append(ol); }
      if (m.log && m.log.length) { const ul = el('ul', 'workshop-log'); m.log.slice(-8).forEach(e => ul.append(el('li', '', JarvisWorkshop.logLine(e)))); node.append(ul); }
      if (m.result) node.append(el('p', 'workshop-result', m.result));
      node.append(el('small', '', 'Chat: ' + m.chat + ' · ' + m.tool_calls + ' tool calls'));
      return node;
    });
    // Goals JARVIS suggested on his own (goals.py): the owner answers on the approval card (Reliability > waiting
    // approvals, or the chat); this is the record. Nothing starts from here.
    const goalRows = (data.goals || []).map(g => {
      const node = el('article', 'workshop-mission ' + (g.state === 'adopted' ? 'ok' : g.state === 'proposed' ? '' : 'warn'));
      node.append(el('b', '', JarvisWorkshop.goalState(g.state) + ': ' + (g.goal || '')));
      if (g.why) node.append(el('p', 'workshop-result', 'Why: ' + g.why));
      node.append(el('small', '', 'Suggested by ' + (g.by || 'JARVIS') + ' ' + new Date(g.created * 1000).toLocaleString() + (g.mission && g.state === 'adopted' ? ' · mission ' + g.mission : '')));
      return node;
    });
    missionBox.replaceChildren(el('h3', '', 'Missions'), goal, controls, ...(rows.length ? rows : [el('p', 'workshop-note', 'No mission has run yet.')]),
      el('h3', '', 'Goals JARVIS suggested'),
      el('p', 'workshop-note', 'JARVIS may suggest a goal he thinks worth doing. Each waits for your answer on screen for a day, like any approval; a goal you approve runs as a mission above, under every mission limit. Nothing starts until you say yes.'),
      ...(goalRows.length ? goalRows : [el('p', 'workshop-note', 'No goal has been suggested yet.')]));
  }

  function renderLessons(data) {
    const rows = data.lessons || [];
    lessonBox.replaceChildren(el('h3', '', 'Lessons JARVIS kept (' + rows.length + ')'), ...(rows.length ? rows.map(row => {
      const node = el('article', 'workshop-lesson');
      node.append(el('span', '', JarvisWorkshop.lessonText(row)), button('DELETE', 'text-button', () => act({action: 'delete_lesson', id: row.id})));
      return node;
    }) : [el('p', 'workshop-note', 'Nothing yet. JARVIS saves a lesson when a job taught him something worth keeping.')]));
  }

  // Skills (skills.py): the owner answers a suggestion on its approval card (Reliability > waiting approvals, or the
  // chat); here he reads every skill and turns it off, on, or deletes it. JARVIS reads the steps from his database,
  // so nothing typed into the files in the workshop changes a skill.
  const openSkills = new Set();
  function renderSkills(data) {
    const rows = (data.skills || []).map(s => {
      const kept = s.state === 'active' || s.state === 'off' || s.state === 'paused';
      const node = el('article', 'workshop-mission workshop-skill ' + (s.state === 'active' ? 'ok' : s.state === 'proposed' ? '' : 'warn'));
      node.append(el('b', '', JarvisWorkshop.skillLine(s)));
      if (s.note) node.append(el('p', 'workshop-note warn', s.note));
      const steps = el('details'); steps.open = openSkills.has(s.id);
      steps.ontoggle = () => { if (steps.open) openSkills.add(s.id); else openSkills.delete(s.id); };
      steps.append(el('summary', '', 'Steps' + (s.script_name ? ' and script' : '')), el('pre', 'workshop-result', s.instructions || ''));
      if (s.script_name) steps.append(el('p', 'workshop-note', s.script_name + ' (in the workshop: skills/' + s.name + '/)'), el('pre', 'workshop-result', s.script || ''));
      node.append(steps, el('small', '', JarvisWorkshop.skillUse(s) + ' · suggested by ' + (s.by || 'JARVIS') + ' ' + new Date(s.created * 1000).toLocaleString()));
      if (kept) {
        const controls = el('div', 'workshop-controls');
        controls.append(s.state === 'active' ? button('TURN OFF', 'text-button', () => act({action: 'skill_off', id: s.id}))
                                             : button('TURN ON', 'text-button', () => act({action: 'skill_on', id: s.id})),
          button('DELETE', 'text-button', () => { if (window.confirm('Delete the skill "' + s.name + '"? Its files go to the workshop\'s recycle folder.')) act({action: 'delete_skill', id: s.id}); }));
        node.append(controls);
      } else if (s.state !== 'proposed') {
        node.append(button('DELETE', 'text-button', () => act({action: 'delete_skill', id: s.id})));
      }
      return node;
    });
    skillBox.replaceChildren(el('h3', '', 'Skills'),
      el('p', 'workshop-note', 'Know-how JARVIS keeps for jobs that come up again: the steps, and at most one script. He suggests one when he has worked out a job, or when you show him one; you read the whole text on the approval card and it is kept only if you say yes. A skill gives him no new tool and no permission.'),
      ...(rows.length ? rows : [el('p', 'workshop-note', 'No skill yet.')]));
  }

  function render(data) {
    folderLine.replaceChildren(el('span', '', 'Folder: '), el('code', '', data.folder || ''), button('REFRESH', 'text-button', load),
      el('span', 'workshop-note', ' Replaced and deleted files are kept in ' + (data.recycle || '') + '.'));
    pythonLine.textContent = JarvisWorkshop.interpreterText(data.interpreters);
    renderFolders(data); renderMinutes(data); renderMissions(data); renderSkills(data); renderLessons(data);
  }
  async function load() {
    if (inspecting()) { missionBox.textContent = 'Not shown during an inspection.'; return; }
    try { render(await api('/api/workshop')); } catch (e) { if (!missionBox.children.length) missionBox.textContent = e.message; }
  }
  const settingsNav = q('.nav[data-view="settings"]'); if (settingsNav) settingsNav.addEventListener('click', load);
  const categoryButton = q('[data-settings-category="Workshop"]'); if (categoryButton) categoryButton.addEventListener('click', load);
  setInterval(() => { if (!document.hidden && panel.offsetParent !== null && !busy) load(); }, 4000);
  load();
})();
