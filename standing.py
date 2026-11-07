"""Standing responsibilities and emergency authority (owner, 2026-10-13, after the MCU breakdown: "broad standing access,
independent execution within assigned goals, explicit authorization for major consequential actions, and narrowly
defined emergency authority"; "all four").

Four things, each a setting the owner can switch in Settings > Permissions (SWITCHES; all on as shipped):

  A  watch_problems      The standing watch: every few minutes the Core looks at the drives, the battery and the
                         automatic backups and raises a notice, once per condition, when something is wrong (Watch).
                         Warnings only: the watch fixes nothing. Spoken as a nudge is (the "proactive" setting, quiet
                         hours), shown on the PC and the devices.
  B  mission_covers      An assigned goal: when the owner approved a mission (the card, a goal he adopted, or his own
                         click in Settings > Workshop), that approval covers the mission's file and command work
                         INSIDE THE WORKSHOP for that mission only (server.App.tool: a switch at "ask first" is read as
                         Allowed for those tools, in that mission). Never outside the workshop, never the internet,
                         the mail or JARVIS himself; never after taint; never a tool switched Off; the stop still ends it.
  C  emergency_restart   The desktop app starts the Core again, once, after a crash (desktop/backend.cjs reads this
                         from standing.json beside the Core's data). A second crash within RESTART_WINDOW seconds is
                         reported as before.
     emergency_backup    When the automatic backups keep failing (two periods overdue, or never succeeded), the watch
                         tries one at once and tells the owner, once per streak.
     emergency_lockdown  Under attack (LOCKDOWN_HITS questions marked by the guard within LOCKDOWN_WINDOW seconds:
                         outside text that tried to instruct the AI), the Core locks itself down: every tool that can
                         ask asks first, whatever its switch, until the owner ends the lockdown in Settings > Permissions.
  D  warn_risky          Before a risky action the owner asked for (risk(): a command that wipes or shuts down, deleting
                         a folder, a program to download), JARVIS says what the risk is and asks once, on the approval
                         card. Not a veto: the owner's yes runs it. Only tools that would otherwise run at once; a tool
                         that always asks shows its whole call on its own card already.

Nothing here spends, sends, deletes or changes JARVIS himself on its own.
"""
import json
import re
import time
from pathlib import Path

import system_diagnostics

SWITCHES = {
    'watch_problems': ('Warn you about problems on his own', 'A drive nearly full, the battery critical, the automatic backups failing: '
                       'JARVIS tells you without being asked, once per problem. He fixes nothing by himself.'),
    'mission_covers': ('Your approval of a mission covers its workshop work', 'Approving a mission (or a goal he suggested, or starting one yourself) '
                       'lets that mission read, write and run commands inside the workshop without asking for each step. Outside the workshop, '
                       'the internet, your mail and JARVIS himself still ask.'),
    'emergency_restart': ('Start himself again after a crash', 'The desktop app starts the Core again once if it stops unexpectedly; '
                          'a second crash within ten minutes is shown as before.'),
    'emergency_backup': ('Make a backup when backups keep failing', 'When the automatic backups are overdue or have never worked, '
                         'he tries one at once and tells you.'),
    'emergency_lockdown': ('Lock himself down under attack', 'When several questions in a row read text that tried to instruct the AI, '
                           'every action asks you first until you end the lockdown here.'),
    'warn_risky': ('Warn you before a risky action', 'Deleting a folder, a command that wipes or shuts down, a program to download: '
                   'he says the risk and asks once. Your yes runs it.'),
}
DEFAULTS = {name: True for name in SWITCHES}
FILE = 'standing.json'           # beside the Core's data, for the desktop app (emergency_restart)
WATCH_SECONDS = 300              # the standing watch looks this often
RESTART_WINDOW = 600             # one automatic restart within this many seconds
LOCKDOWN_HITS, LOCKDOWN_WINDOW = 3, 600
LOCKDOWN_NOTICE = ('JARVIS locked himself down: {hits} questions in the last {minutes} minutes read text that tried to instruct the AI. '
                   'Every action now asks you first. End the lockdown in Settings > Permissions when you have looked.')
COVERED_TOOLS = ('workshop_files', 'workshop_run', 'workshop_python')   # what a mission's approval covers, inside the workshop

# ---- D: what counts as risky. Plain patterns, bounded; anything not named here is not judged. ----
_WIPE = re.compile(r'(?i)(?:^|[&|;(]\s*)(?:rm\s+(?:-\w*r\w*\s+)+|rmdir\s+(?:/s|-r)|rd\s+/s|del\s+(?:/\w\s+)*?/s|Remove-Item\b[^|&\n]*-Recurse'
                   r'|format(?:\.com)?\s+[a-z]:|diskpart\b|cipher\s+/w|reg(?:\.exe)?\s+delete|shutdown(?:\.exe)?\s+[/-][srf]'
                   r'|Stop-Computer|Restart-Computer|taskkill\b[^|&\n]*(?:/f|/im\s+(?:explorer|winlogon|csrss))'
                   r'|net\s+user\b[^|&\n]*/(?:add|delete)|git\s+push\b[^|&\n]*(?:--force|-f\b)|git\s+reset\s+--hard|git\s+clean\s+-\w*f'
                   r'|pip\s+uninstall|bcdedit\b|vssadmin\s+delete|wmic\b[^|&\n]*delete)')


def risk(name, args):
    """One plain sentence about the risk of this call, or None. Only tools the owner's own request can reach at once."""
    args = args if isinstance(args, dict) else {}
    if name == 'workshop_run':
        command = str(args.get('command') or '')
        if _WIPE.search(command):
            return 'This command can wipe, remove, shut down or force something that is hard to undo: ' + ' '.join(command.split())[:160]
    elif name == 'workshop_files' and args.get('action') == 'delete':
        path = str(args.get('path') or '').strip().replace('\\', '/').rstrip('/')
        if not path or path == '.':
            return 'This would delete the whole workshop folder.'
        if '.' not in path.rsplit('/', 1)[-1]:
            return 'This deletes a folder and everything in it (kept in the recycle folder, but all at once): ' + path[:160]
    elif name == 'computer_open_page':
        url = str(args.get('url') or '').lower().split('?', 1)[0]
        if url.endswith(('.exe', '.msi', '.bat', '.cmd', '.ps1', '.scr', '.vbs', '.js', '.jar')):
            return 'This address is a program to download and run, not a page to read: ' + url[:160]
    return None


# ---- the settings, as the Core reads them and the desktop app reads them ----
def switches(settings):
    """The six switches as they stand: the owner's saved value, else on."""
    return {name: bool(settings.get(name, True)) for name in SWITCHES}


def write_file(root, settings):
    """standing.json beside the Core's data: what the desktop app needs (emergency_restart). Never raises."""
    try:
        Path(root).joinpath(FILE).write_text(json.dumps({'emergency_restart': switches(settings)['emergency_restart'],
                                                          'restart_window_seconds': RESTART_WINDOW}), encoding='utf-8')
    except Exception:
        pass


def panel(settings):
    """Settings > Permissions > Standing responsibilities: each switch with its words and its position."""
    on = switches(settings)
    return {'switches': [{'name': name, 'label': label, 'note': note, 'on': on[name]} for name, (label, note) in SWITCHES.items()],
            'lockdown': bool(settings.get('lockdown'))}


# ---- C: the lockdown ----
class Lockdown:
    """Counts the questions the guard marked (content_guard.mark sets run.tainted); LOCKDOWN_HITS within LOCKDOWN_WINDOW
    seconds, with the switch on, lock the Core down (the setting `lockdown`, read by server.App.tool_mode). The owner
    ends it in Settings > Permissions."""

    def __init__(self, settings, save, notify, clock=time.time):
        self.settings, self.save, self.notify, self.clock = settings, save, notify, clock
        self.hits = []

    def tainted(self, run=None):
        now = self.clock()
        self.hits = [t for t in self.hits if now - t < LOCKDOWN_WINDOW] + [now]
        settings = self.settings()
        if settings.get('lockdown') or not switches(settings)['emergency_lockdown'] or len(self.hits) < LOCKDOWN_HITS:
            return False
        self.save({'lockdown': True})
        self.hits = []
        try:
            self.notify(LOCKDOWN_NOTICE.format(hits=LOCKDOWN_HITS, minutes=LOCKDOWN_WINDOW // 60))
        except Exception:
            pass
        return True

    def end(self):
        self.save({'lockdown': False})
        self.hits = []


# ---- A and C: the standing watch ----
class Watch:
    """Every WATCH_SECONDS (started by server.main like the backups' clock): the drives, the battery, the automatic
    backups. One notice per condition while it lasts (keyed); the key is dropped when the condition clears, so it can
    be raised again later. `backup` is the AutoBackup (status(), run()); `notify(text, key)` is the Core's (a notice,
    spoken as the owner's settings allow); `drop(key)` forgets a cleared one."""

    def __init__(self, settings, notify, drop, backup=None, read=None, clock=time.time):
        self.settings, self.notify, self.drop, self.backup, self.clock = settings, notify, drop, backup, clock
        self.read = read or (lambda: {'drives': system_diagnostics.drives(), 'battery': system_diagnostics.battery()})
        self.last = {}

    def conditions(self):
        """{key: sentence} of what is wrong now."""
        found = {}
        try:
            parts = self.read()
        except Exception:
            parts = {}
        for d in parts.get('drives') or ():
            try:
                if d['free_percent'] < system_diagnostics.LOW_DRIVE_PERCENT:
                    found['watch:drive:' + d['drive']] = f"Drive {d['drive']} is nearly full: {d['free_gb']} GB free of {d['total_gb']} GB."
            except (KeyError, TypeError):
                pass
        b = parts.get('battery')
        try:
            if b and b['present'] and b['percent'] is not None and b['percent'] <= system_diagnostics.LOW_BATTERY_PERCENT and b['on_mains'] is False:
                found['watch:battery'] = f"The battery is at {b['percent']}% and not on mains power."
        except (KeyError, TypeError):
            pass
        if self.backup is not None:
            try:
                status = self.backup.status()
                if status['enabled'] and (status['overdue'] or status['never_succeeded']):
                    found['watch:backup'] = ('The automatic backups have not worked' + (' yet' if status['never_succeeded'] else ' for a while')
                                             + (': ' + str(status['last_error']) if status['last_error'] else '') + '.')
            except Exception:
                pass
        return found

    def run_once(self):
        on = switches(self.settings())
        found = self.conditions() if on['watch_problems'] or on['emergency_backup'] else {}
        raised = []
        for key in list(self.last):
            if key not in found:
                self.last.pop(key, None)
                try:
                    self.drop(key)
                except Exception:
                    pass
        for key, text in found.items():
            if key == 'watch:backup' and on['emergency_backup'] and self.backup is not None and key not in self.last:
                # C: one try at once (AutoBackup.run records its own result; a failure is in the next look's sentence).
                try:
                    self.backup.run()
                except Exception:
                    pass
                text += ' JARVIS tried one just now; Settings > Backups shows the result.'
            if key not in self.last and (on['watch_problems'] or key == 'watch:backup' and on['emergency_backup']):
                self.last[key] = text
                try:
                    if self.notify(text, key):
                        raised.append(key)
                except Exception:
                    pass
        return raised
