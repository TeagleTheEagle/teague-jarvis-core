/* What the dashboard and the header may claim (1.0.15). One place for the owner's rule: a value on screen comes from
   a real source, "configured" is not "working", and when the Core cannot be heard from, what was read before is
   shown as unknown rather than as its last value. No page elements here: shared by command-dashboard.js,
   horizon.js and test_dashboard_model.cjs. */
const JarvisDashboardModel = (() => {
  const SILENT_MS = 25000;  // the page asks the Core every 10 s (app.js); two missed rounds and a bit
  const configured = text => /configured/i.test(text || '') && !/not configured/i.test(text || '');

  // The connection to the Core, from what app.js records after each /api/state (state.connected, state.stateAt),
  // the dashboard's own readings (heartbeatAt) and whether a reply is arriving right now (busy):
  //   snapshot   a read-only inspection picture, not a live page
  //   connecting nothing heard from the Core yet
  //   lost       the last request failed
  //   checking   nothing heard for a while (window was hidden, or the Core accepted a request and went quiet)
  //   online     heard from recently
  function link({inspection, connected, hasData, busy, stateAt, heartbeatAt, now}) {
    if (inspection) return 'snapshot';
    if (connected === false) return 'lost';
    if (!hasData) return 'connecting';
    if (busy) return 'online';
    return now - Math.max(stateAt || 0, heartbeatAt || 0) > SILENT_MS ? 'checking' : 'online';
  }
  const live = state => state === 'online' || state === 'snapshot';  // Core data may be shown
  const LINK_TEXT = {snapshot: 'SNAPSHOT', connecting: 'CONNECTING', lost: 'CORE OFFLINE', checking: 'CHECKING', online: 'ONLINE'};

  // Six rows [name, state, text]; state is ok (set up), warn (needs a look), basic (works in a limited way, nothing
  // set up) or off (unknown or absent). Anything the Core did not say is UNKNOWN, never a guess.
  function systems(state, data) {
    const unknown = name => [name, 'off', 'UNKNOWN'], rest = ['AI', 'Memory', 'Voice', 'Search', 'Devices'];
    if (state === 'lost') return [['Core', 'warn', 'OFFLINE'], ...rest.map(unknown)];
    if (!live(state)) return [['Core', 'off', LINK_TEXT[state]], ...rest.map(unknown)];
    const d = data || {}, caps = d.capabilities || {}, settings = d.settings || {};
    const brain = typeof caps.brain === 'string' ? caps.brain : '';
    const ai = !brain ? unknown('AI') : configured(brain) ? ['AI', 'ok', brain.split(' ')[0].toUpperCase()]
      : ['AI', 'warn', /unsupported/i.test(brain) ? 'CHECK SETTING' : 'NO KEY'];
    const memory = Array.isArray(d.memory) ? ['Memory', 'ok', d.memory.length + ' SAVED'] : unknown('Memory');
    const profile = settings.voice_profile && settings.voice_profile !== 'auto' ? settings.voice_profile : caps.voice_provider;
    const voiceName = {qwen: 'QWEN VOICE', fish: 'FISH AUDIO', openai: 'OPENAI VOICE', browser: 'BROWSER VOICE'}[profile];
    const voiceReady = {qwen: caps.qwen_voice, fish: caps.fish, openai: caps.openai_voice, browser: true}[profile];
    const voice = !voiceName || typeof voiceReady !== 'boolean' ? unknown('Voice') : voiceReady ? ['Voice', 'ok', voiceName]
      : ['Voice', 'warn', voiceName.split(' ')[0] + ' NOT SET UP'];
    const search = typeof caps.search !== 'string' || !caps.search ? unknown('Search') : /openrouter/i.test(caps.search) ? ['Search', 'ok', 'OPENROUTER'] : /serpapi/i.test(caps.search) ? ['Search', 'ok', 'SERPAPI']
      : /brave/i.test(caps.search) ? ['Search', 'ok', 'BRAVE'] : ['Search', 'basic', 'BEST EFFORT'];
    const online = Array.isArray(d.devices) ? d.devices.filter(x => x.connected && !x.simulated).length : null;  // a simulated device is never counted
    const devices = online === null ? unknown('Devices') : ['Devices', online ? 'ok' : 'off', online + ' ONLINE'];
    return [state === 'snapshot' ? ['Core', 'off', 'SNAPSHOT'] : ['Core', 'ok', 'ONLINE'], ai, memory, voice, search, devices];
  }
  // The heading over the rows and the figure in the ring. `counted` is false whenever the count would be a guess.
  function summary(state, rows) {
    const ready = rows.filter(r => r[1] === 'ok').length, total = rows.length, counted = state === 'online';
    return {ready, total, counted, warn: state === 'lost' || rows.some(r => r[1] === 'warn'),
      text: !counted ? LINK_TEXT[state] : ready === total ? 'ALL CONFIGURED' : ready + ' OF ' + total + ' CONFIGURED'};
  }
  // The three device places of the one Core, from the device registry.
  function devices(state, data) {
    const known = live(state) && Array.isArray(data && data.devices), list = known ? data.devices : [];
    // A place shows its best device: a real one that is connected, then a real one, then a simulated test client.
    // A revoked device is not shown. Older rows without a kind are told apart by their id, as before.
    const rank = x => (x.simulated ? 0 : 2) + (x.connected ? 1 : 0);
    const find = (kind, re) => list.filter(x => !x.revoked && (x.kind ? x.kind === kind : re.test(x.device_id || ''))).sort((a, b) => rank(b) - rank(a))[0];
    return [['workstation', 'This PC', find('pc', /^pc$/)], ['mobile', 'Phone', find('phone', /phone|mobile/i)], ['glasses', 'Glasses', find('glasses', /glass|wear/i)]].map(([kind, name, device]) => (
      {kind, name, state: !known ? 'unknown' : !device ? 'none' : device.simulated ? 'simulated' : device.connected ? 'ok' : 'offline',
        text: !known ? 'Unknown' : !device ? 'Not paired' : device.simulated ? 'Simulated only' : device.connected ? 'Online' : 'Offline'}));
  }
  // The emergency stop holds (permissions.py): known only while the Core is heard from. While it holds the
  // dashboard says so instead of "standing by".
  const stopped = (state, data) => state === 'online' && !!(data && data.control && data.control.stopped);
  // The line under the waveform. The wake word is only offered while the detector is really waiting for it.
  function voiceLine({micOn, armed, manual, suspended, wakeEnabled}) {
    if (!micOn) return 'Microphone off. Press F4 to turn it on.';
    if (armed) return manual ? 'Listening while you hold to talk.' : 'Listening.';
    if (suspended) return 'Microphone paused while JARVIS replies.';
    if (wakeEnabled === false) return 'Microphone on, without the wake word.';
    return 'Say "Hey Jarvis", then your request.';
  }
  return {link, live, systems, summary, devices, stopped, voiceLine, configured, LINK_TEXT, SILENT_MS};
})();
if (typeof module !== 'undefined') module.exports = JarvisDashboardModel;
