'use strict';
const $ = id => document.getElementById(id);
let token = '', pending = null, busy = false;
function status(text) { $('status').textContent = text; }
function controls() { $('save').disabled = !token || busy; $('refresh').disabled = !token || busy; $('connect').disabled = busy; }
async function request(method, body) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch('/v1/tasks', {method, signal: controller.signal, headers: {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}, ...(body ? {body: JSON.stringify(body)} : {})});
    const data = await response.json();
    if (!response.ok) { if (response.status === 401) token = ''; throw new Error(data.error || 'Request failed.'); }
    return data;
  } finally { clearTimeout(timeout); }
}
async function refresh() {
  const data = await request('GET');
  $('tasks').replaceChildren();
  for (const task of data.tasks) {
    const item = document.createElement('li');
    item.textContent = task.body + (task.completed ? ' · Completed' : '');
    $('tasks').append(item);
  }
  if (!data.tasks.length) { const item = document.createElement('li'); item.textContent = 'No saved tasks. Capture your first task above.'; $('tasks').append(item); }
}
async function run(action) { if (busy) return; busy = true; controls(); try { await action(); } catch (e) { status(e.name === 'AbortError' ? 'Connection timed out. Retry Save to check the same request; it will not create a duplicate.' : e.message); } finally { busy = false; controls(); } }
$('connect').onclick = () => run(async () => { token = $('key').value.trim(); $('key').value = ''; await refresh(); status('Connected. Tasks loaded from JARVIS.'); });
$('refresh').onclick = () => run(async () => { await refresh(); status('Tasks refreshed.'); });
$('save').onclick = () => run(async () => {
  const title = $('title').value.trim();
  if (!title) throw new Error('Enter a task title.');
  if (pending && pending.title !== title) throw new Error('The previous save is unresolved. Restore its title and retry before creating another task.');
  pending ??= {title, request_id: crypto.randomUUID()};
  const result = await request('POST', pending);
  if (result.status !== 'saved' || !result.task?.id) throw new Error('Save not confirmed. Retry using the same task.');
  pending = null; $('title').value = ''; status('Saved: ' + result.task.body);
  try { await refresh(); } catch (_) { status('Task saved. Refresh the list when the connection returns.'); }
});
$('disconnect').onclick = () => { token = ''; $('key').value = ''; $('tasks').replaceChildren(); controls(); status('Disconnected. The PC can revoke this device key.'); };
