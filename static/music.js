// Music (1.0.16, docs/MUSIC.md): Settings > Music. The owner's music folder, the nicknames, what is playing and the
// volume. The Core plays the files itself (music.py); this panel shows its answers and sends the owner's clicks.
const JarvisMusic = {
  // One line about what is playing, from the Core's own status.
  nowText(now) {
    if (!now || now.state === 'nothing') return 'Nothing is playing.';
    const name = now.title + (now.nickname ? ' (' + now.nickname + ')' : '');
    return (now.state === 'paused' ? 'Paused: ' : 'Playing: ') + name;
  },
  // Minutes and seconds of a position in milliseconds; empty when the Core has none.
  timeText(ms) {
    if (typeof ms !== 'number' || ms < 0) return '';
    const total = Math.round(ms / 1000);
    return Math.floor(total / 60) + ':' + String(total % 60).padStart(2, '0');
  },
  filesText(count) { return count === 0 ? 'No music files yet.' : count === 1 ? '1 music file.' : count + ' music files.'; },
  volumeText(volume) { return 'Volume ' + volume + '%'; },
  // A nickname row: the file it points at, or that the file is gone.
  rowText(row) { return row.present ? row.title : row.file + ' (file not in the folder)'; },
  // The start-up song line: what plays after JARVIS's greeting at a sign-in start (the setting music_startup).
  startupText(startup, present) {
    if (!startup) return 'No start-up song: after his greeting at sign-in, JARVIS stays quiet.';
    return 'After his greeting at sign-in, JARVIS plays: ' + startup + (present ? '' : ' (not in the folder, so nothing plays)') + '. Not in quiet hours, and not while the emergency stop holds.';
  },
};
if (typeof module !== 'undefined') module.exports = JarvisMusic;

if (typeof document !== 'undefined') (() => {
  'use strict';
  if (document.querySelector('.music-panel')) return;
  const q = s => document.querySelector(s);
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  const button = (text, cls, onclick) => { const b = el('button', cls, text); b.type = 'button'; b.onclick = onclick; return b; };
  const inspecting = () => !!window.JARVIS_INSPECTION;

  const sheet = document.createElement('link'); sheet.rel = 'stylesheet'; sheet.href = '/music.css'; document.head.append(sheet);
  const panel = el('section', 'music-panel');
  const intro = el('p', '', 'Your own music, played by JARVIS on this PC\'s speakers. Copy MP3 files (WAV works too) into the folder below, ' +
    'give a song a nickname, and say "Jarvis, play <nickname>". "Stop the music", "pause", "resume", "volume up" and "volume down" work the same way.');
  const folderLine = el('p', 'music-folder'), nowBox = el('div', 'music-now'), startupBox = el('div', 'music-startup'), addBox = el('div', 'music-add'), list = el('div', 'music-list');
  list.setAttribute('aria-live', 'polite');
  panel.append(intro, folderLine, nowBox, startupBox, addBox, list);
  const category = q('.ti-settings-group[data-setting="Music"]'), settingsView = q('#settingsView');
  if (category) category.append(panel); else if (settingsView) { panel.prepend(el('h2', '', 'Music')); settingsView.prepend(panel); }

  let busy = false, pendingVolume = null;
  async function act(body, said) {
    if (busy) { if (body.action === 'volume') pendingVolume = body.volume; return; }  // a slider move during a request is kept, not dropped
    busy = true;
    try { const answer = await api('/api/music', body); if (said !== false) toast(answer.message || 'Done.'); }
    catch (e) { toast(e.message, true); }
    busy = false;
    if (pendingVolume !== null) { const volume = pendingVolume; pendingVolume = null; return act({action: 'volume', volume}, false); }
    await load();
  }

  function renderNow(data) {
    if (nowBox.contains(document.activeElement)) return;  // not redrawn under the owner's hand (the slider, a button)
    const now = data.now || {state: 'nothing'};
    const line = el('p', 'music-now-line ' + (now.state === 'playing' ? 'ok' : now.state === 'paused' ? 'warn' : 'off'), JarvisMusic.nowText(now));
    const time = JarvisMusic.timeText(now.position_ms), length = JarvisMusic.timeText(now.length_ms);
    if (time) line.append(el('span', 'music-time', ' ' + time + (length ? ' / ' + length : '')));
    const controls = el('div', 'music-controls');
    if (now.state === 'playing') controls.append(button('PAUSE', 'outline', () => act({action: 'pause'})));
    if (now.state === 'paused') controls.append(button('RESUME', 'outline', () => act({action: 'resume'})));
    if (now.state !== 'nothing') controls.append(button('STOP', 'text-button', () => act({action: 'stop'})));
    const volumeLabel = el('label', 'music-volume'), volume = el('input'); volume.type = 'range'; volume.min = 0; volume.max = 100; volume.step = 5;
    volume.value = data.volume; volume.setAttribute('aria-label', 'Music volume');
    const volumeText = el('span', '', JarvisMusic.volumeText(data.volume));
    volume.oninput = () => { volumeText.textContent = JarvisMusic.volumeText(Number(volume.value)); };
    volume.onchange = () => act({action: 'volume', volume: Number(volume.value)}, false);
    volumeLabel.append(volumeText, volume);
    controls.append(volumeLabel);
    nowBox.replaceChildren(el('h3', '', 'Now playing'), line, controls);
  }

  function renderAdd(data) {
    const files = data.files || [];
    const name = el('input'); name.maxLength = 60; name.placeholder = 'Nickname, for example: workshop warrior'; name.setAttribute('aria-label', 'Nickname for a song');
    const file = el('select'); file.setAttribute('aria-label', 'Music file');
    for (const f of files) file.add(new Option(f, f));
    const add = button('ADD', 'primary', () => act({action: 'add', nickname: name.value, file: file.value}));
    add.disabled = !files.length;
    addBox.replaceChildren(el('h3', '', 'Give a song a nickname'), name, file, add,
      el('p', 'music-note', files.length ? JarvisMusic.filesText(files.length) + ' A song without a nickname can still be played by its file name.' : 'Copy MP3 files into the folder above, then REFRESH.'));
  }

  function renderList(data) {
    const rows = data.nicknames || [];
    list.replaceChildren(el('h3', '', 'Nicknames (' + rows.length + ')'), ...rows.map(row => {
      const node = el('article', 'music-row ' + (row.present ? '' : 'warn'));
      node.append(el('b', '', row.nickname), el('span', 'music-row-file', JarvisMusic.rowText(row)));
      const actions = el('div', 'music-actions');
      const play = button('PLAY', 'outline', () => act({action: 'play', query: row.nickname})); play.disabled = !row.present;
      actions.append(play, button('REMOVE', 'text-button', () => act({action: 'remove', nickname: row.nickname})));
      node.append(actions);
      return node;
    }));
  }

  // The start-up song: the song JARVIS plays once his greeting at a sign-in start has been spoken (setting
  // music_startup, a nickname or a file name; nothing = quiet). Saved the moment it is chosen.
  function renderStartup(data) {
    if (startupBox.contains(document.activeElement)) return;
    const current = data.startup || '';
    const note = el('p', 'music-note', JarvisMusic.startupText(current, !!data.startup_present));
    const choice = el('select'); choice.setAttribute('aria-label', 'Song played after the greeting at sign-in');
    choice.add(new Option('Nothing', ''));
    const named = new Set();
    for (const row of data.nicknames || []) if (row.present) { named.add(row.file); choice.add(new Option(row.nickname + ' (' + row.title + ')', row.nickname)); }
    for (const f of data.files || []) if (!named.has(f)) choice.add(new Option(f, f));   // a file with a nickname is listed once, by its nickname
    if (current && ![...choice.options].some(o => o.value === current)) choice.add(new Option(current + ' (not in the folder)', current));
    choice.value = current;
    choice.onchange = async () => {
      const wanted = choice.value;
      try {
        await api('/api/settings', {music_startup: wanted});
        toast(wanted ? 'Start-up song saved.' : 'No start-up song.');
        note.textContent = JarvisMusic.startupText(wanted, true);   // said at once, even while the select keeps the focus
      } catch (e) { toast(e.message, true); choice.value = current; }
      await load();
    };
    startupBox.replaceChildren(el('h3', '', 'When JARVIS starts'), note, choice);
  }

  function render(data) {
    folderLine.replaceChildren(el('span', '', 'Folder: '), el('code', '', data.folder || ''), button('REFRESH', 'text-button', load));
    if (!addBox.contains(document.activeElement)) renderAdd(data);  // a nickname being typed or a file being chosen stays
    renderNow(data);
    renderStartup(data);
    renderList(data);
  }
  async function load() {
    if (inspecting()) { list.textContent = 'Not shown during an inspection.'; return; }
    try { render(await api('/api/music')); } catch (e) { if (!list.children.length) list.textContent = e.message; }
  }
  const settingsNav = q('.nav[data-view="settings"]'); if (settingsNav) settingsNav.addEventListener('click', load);
  const categoryButton = q('[data-settings-category="Music"]'); if (categoryButton) categoryButton.addEventListener('click', load);
  setInterval(() => { if (!document.hidden && panel.offsetParent !== null && !busy) load(); }, 3000);
  load();
})();
