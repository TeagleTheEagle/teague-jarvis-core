// Devices (1.0.15, docs/DEVICES.md): the owner's panel for the devices of the one Core. Settings > Devices.
// The Core keeps the list and decides everything (devices.py, server.App); this file shows it and sends the
// owner's clicks. A device is never shown as online, real or allowed unless the Core says so.
const JarvisDevices = {
  KINDS: {pc: 'This PC', phone: 'Phone', glasses: 'Glasses', computer: 'Computer', other: 'Other device'},
  CAPABILITIES: {microphone: 'Microphone', camera: 'Camera', speakers: 'Speakers', display: 'Display'},
  // One line of state for a row as the Core lists it.
  stateText(d) {
    if (d.revoked) return 'Revoked';
    if (d.simulated) return d.connected ? 'Simulated test client, connected' : 'Simulated test client, not connected';
    if (d.builtin) return d.connected ? 'Online' : 'Not connected';
    if (d.key_valid === false) return 'Its key belongs to another installation: pair it again';
    return d.connected ? 'Online' : 'Not connected';
  },
  stateClass(d) { return d.revoked || d.key_valid === false ? 'warn' : d.connected && !d.simulated ? 'ok' : 'off'; },
  // "Last seen" in words; nothing when the Core has no time for it.
  seenText(d, nowSeconds) {
    if (typeof d.last_seen !== 'number' || d.builtin) return '';
    const age = Math.max(0, nowSeconds - d.last_seen);
    if (age < 90) return 'Last seen just now';
    if (age < 3600) return 'Last seen ' + Math.round(age / 60) + ' minutes ago';
    if (age < 172800) return 'Last seen ' + Math.round(age / 3600) + ' hours ago';
    return 'Last seen ' + Math.round(age / 86400) + ' days ago';
  },
  // The pairing code as shown, and how long it is still good for.
  remainingText(expires, nowSeconds) {
    const left = Math.max(0, Math.round(expires - nowSeconds));
    return left ? 'Good for ' + Math.floor(left / 60) + ':' + String(left % 60).padStart(2, '0') : 'This code has run out. Start again.';
  },
};
if (typeof module !== 'undefined') module.exports = JarvisDevices;

if (typeof document !== 'undefined') (() => {
  'use strict';
  if (document.querySelector('.devices-panel')) return;
  const q = s => document.querySelector(s);
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  const button = (text, cls, onclick) => { const b = el('button', cls, text); b.type = 'button'; b.onclick = onclick; return b; };
  const inspecting = () => !!window.JARVIS_INSPECTION;
  const now = () => Date.now() / 1000;

  const sheet = document.createElement('link'); sheet.rel = 'stylesheet'; sheet.href = '/devices.css'; document.head.append(sheet);
  const panel = el('section', 'devices-panel');
  const intro = el('p', '', 'The devices of your one JARVIS. A device pairs with a code that you read here, and pairing gives it a key of its own. ' +
    'What a device says it can do is listed; what it may use is your choice, and you can revoke a device at any time. ' +
    'A paired device can ask questions and read; it cannot change saved things.');
  const reach = el('p', 'devices-note', 'Today JARVIS listens only on this PC. Programs on this PC can pair now; a phone or glasses can pair once you decide how JARVIS is reached from other devices.');
  const pairBox = el('div', 'devices-pair'), list = el('div', 'devices-list');
  list.setAttribute('aria-live', 'polite');
  panel.append(intro, reach, pairBox, list);
  const category = q('.ti-settings-group[data-setting="Devices"]'), settingsView = q('#settingsView');
  if (category) category.append(panel); else if (settingsView) { panel.prepend(el('h2', '', 'Devices')); settingsView.prepend(panel); }

  // ---- pairing ----
  let shownCode = null, countdown = 0;  // the code is shown from the Core's one answer and kept nowhere else
  function pairForm() {
    clearInterval(countdown); shownCode = null;
    const name = el('input'); name.maxLength = 60; name.placeholder = 'Name, for example: My phone'; name.setAttribute('aria-label', 'Name for the new device');
    const kind = el('select'); kind.setAttribute('aria-label', 'Kind of device');
    for (const value of ['phone', 'glasses', 'computer', 'other']) kind.add(new Option(JarvisDevices.KINDS[value], value));
    const start = button('PAIR A DEVICE', 'primary', async () => {
      start.disabled = true;
      try { showCode(await api('/api/devices', {action: 'pair', name: name.value, kind: kind.value})); }
      catch (e) { toast(e.message, true); start.disabled = false; }
    });
    pairBox.replaceChildren(el('h3', '', 'Pair a new device'), name, kind, start);
  }
  function showCode(started) {
    shownCode = started;
    const code = el('strong', 'devices-code', started.code), left = el('span', 'devices-left');
    const cancel = button('CANCEL', 'text-button', async () => { try { await api('/api/devices', {action: 'cancel_pairing'}); } catch (e) { toast(e.message, true); } pairForm(); });
    pairBox.replaceChildren(el('h3', '', 'Type this code on ' + started.name), code, left, cancel,
      el('p', 'devices-note', 'The code works once, for the first device that hands it over within five minutes. Read it only to your own device. CANCEL ends it.'));
    const tick = () => { left.textContent = JarvisDevices.remainingText(started.expires, now()); if (started.expires <= now()) { clearInterval(countdown); } };
    tick(); clearInterval(countdown); countdown = setInterval(async () => { tick(); await load(); }, 2000);
  }

  // ---- the list ----
  function row(d) {
    const node = el('article', 'device-row ' + JarvisDevices.stateClass(d));
    const head = el('div', 'device-head'), title = el('b', '', d.name), kind = el('span', 'device-kind', JarvisDevices.KINDS[d.kind] || d.kind);
    const state = el('span', 'device-state', JarvisDevices.stateText(d)), seen = JarvisDevices.seenText(d, now());
    head.append(title, kind, state); if (seen) head.append(el('span', 'device-seen', seen));
    node.append(head);
    if (d.builtin || d.simulated) {
      node.append(el('p', 'devices-note', d.builtin ? 'The PC JARVIS runs on. It is not paired and cannot be revoked.'
        : 'A test client on this PC, used to try the glasses pipeline. It is never counted as a real device, and it only reads.'));
      return node;
    }
    const caps = el('div', 'device-caps');
    if (!d.declared.length) caps.append(el('span', 'devices-note', 'It declares no microphone, camera, speakers or display.'));
    for (const name of d.declared) {
      const label = el('label', 'check-label'), box = el('input'); box.type = 'checkbox'; box.value = name; box.checked = d.allowed.includes(name); box.disabled = !!d.revoked;
      box.onchange = async () => {
        // What is ticked now, read from the row itself, and no second click in this row until the Core has answered:
        // two quick clicks cannot undo each other.
        const boxes = [...caps.querySelectorAll('input')], wanted = boxes.filter(b => b.checked).map(b => b.value);
        boxes.forEach(b => { b.disabled = true; });
        try { await api('/api/devices', {action: 'allow', id: d.device_id, capabilities: wanted}); toast(d.name + ': ' + JarvisDevices.CAPABILITIES[name] + (box.checked ? ' allowed.' : ' not allowed.')); }
        catch (e) { toast(e.message, true); }
        await load();
      };
      label.append(box, el('span', '', JarvisDevices.CAPABILITIES[name] || name)); caps.append(label);
    }
    const actions = el('div', 'device-actions');
    actions.append(button('RENAME', 'text-button', () => {
      if (head.querySelector('input')) return;
      const input = el('input'); input.value = d.name; input.maxLength = 60; input.setAttribute('aria-label', 'New name for ' + d.name);
      // The text box is taken away before the list is read again: while one is open the list is not redrawn.
      const done = () => { input.replaceWith(title); save.remove(); cancel.remove(); };
      const save = button('SAVE NAME', 'outline', async () => { const name = input.value; done(); try { await api('/api/devices', {action: 'rename', id: d.device_id, name}); } catch (e) { toast(e.message, true); } await load(); });
      const cancel = button('CANCEL', 'text-button', () => { done(); load(); });
      input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); save.click(); } else if (e.key === 'Escape') cancel.click(); });
      title.replaceWith(input, save, cancel); input.focus();
    }));
    if (d.revoked) actions.append(button('REMOVE FROM LIST', 'text-button', async () => { try { await api('/api/devices', {action: 'forget', id: d.device_id}); } catch (e) { toast(e.message, true); } await load(); }));
    else {
      const revoke = button('REVOKE', 'device-revoke', () => {
        // Two clicks: revoking cannot be undone (the device pairs again), so the second click says so.
        // The second click counts only once the new words have been on screen for a moment (not a double click).
        if (revoke.dataset.armed) { if (Date.now() - Number(revoke.dataset.armed) < 700) return; return void api('/api/devices', {action: 'revoke', id: d.device_id}).then(() => toast(d.name + ' is revoked. Its key no longer works.'), e => toast(e.message, true)).then(load); }
        revoke.dataset.armed = String(Date.now()); revoke.textContent = 'REVOKE NOW: ITS KEY STOPS WORKING';
        setTimeout(() => { delete revoke.dataset.armed; revoke.textContent = 'REVOKE'; }, 6000);
      });
      actions.append(revoke);
    }
    node.append(caps, actions);
    return node;
  }
  let renaming = () => !!list.querySelector('input:not([type=checkbox])');
  function render(data) {
    if (renaming()) return;  // do not take the text box away while the owner types a name
    const devices = (data && data.devices) || [];
    // The count is of paired devices only: this PC and the simulated test client are listed, not counted.
    list.replaceChildren(el('h3', '', 'Devices (' + devices.filter(d => !d.revoked && !d.builtin && !d.simulated).length + ' paired)'), ...devices.map(row));
    if (shownCode && !(data && data.pairing)) {  // the code was used, cancelled or ran out
      const paired = devices.find(d => d.name === shownCode.name && !d.revoked && d.created >= shownCode.expires - 300 - 5);
      if (paired) toast(shownCode.name + ' is paired.');
      pairForm();
    }
  }
  async function load() {
    if (inspecting()) { list.textContent = 'Not shown during an inspection.'; return; }
    try { render(await api('/api/devices')); } catch (e) { if (!list.children.length) list.textContent = e.message; }
  }
  pairForm();
  const settingsNav = q('.nav[data-view="settings"]'); if (settingsNav) settingsNav.addEventListener('click', load);
  const categoryButton = q('[data-settings-category="Devices"]'); if (categoryButton) categoryButton.addEventListener('click', load);
  setInterval(() => { if (!document.hidden && panel.offsetParent !== null && !shownCode) load(); }, 10000);
  load();
})();
