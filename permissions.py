"""One table for what every JARVIS tool may do, and the one decision made from it.

Master document sections 6 and 18: every action is capability-scoped, attributable, revocable and
auditable; reading and changing are told apart; sensitive changes ask first; there is a kill switch.

Every tool call passes `server.App.tool`, which asks `decide()` here before anything runs. Other modules
that need a list of tools (what a wearable may call, which results are receipts, which results are kept
for the next question, what can be drafted for approval) take it from this table instead of keeping their
own list. test_permissions.py holds the table equal to `actions.TOOLS`: a tool without a row is refused.

This module imports nothing from JARVIS, so every other module can import it.
"""
import re
from collections import namedtuple

READS, CHANGES = 'reads', 'changes'

# Where a tool reaches. Used for the emergency stop: while it holds, only LOCAL reads from the owner's own
# interface still work, so the owner can look at what happened.
LOCAL = 'JARVIS on this PC'       # JARVIS's own saved data and files
SCREEN = 'the JARVIS window'      # what the interface shows or has switched on (microphone, sharing, sections)
PC = 'this PC'                    # other programs on this PC
ONLINE = 'the internet'           # a service on the internet
SELF = 'JARVIS itself'            # JARVIS's own personality, style and program files

# Does it ask first?
NEVER = 'no'
WORDS = 'your own words'          # runs only when the owner's own words in the question ask for exactly this
ALWAYS = 'always'                 # the owner approves on screen, seeing exactly what will happen, before it does

Rule = namedtuple('Rule', 'label effect reach undo asks repeat_adds wearable evidence receipt preview read_actions note device_writes')


def _rule(label, effect=READS, reach=LOCAL, undo='', asks=NEVER, repeat_adds=False, wearable=False,
          evidence=False, receipt=False, preview=False, read_actions=(), note='', device_writes=False):
    # device_writes (1.0.16): a paired device the owner ticked "may save memories and tasks" may call it too
    # (docs/PHONE-CORE-1.0.16.md). Only the saving of memories, notes, tasks and timers is marked.
    if effect == READS:
        undo = undo or 'Nothing to undo.'
    elif not undo:
        raise ValueError('A tool that changes something must say whether it can be undone: ' + label)
    return Rule(label, effect, reach, undo, asks, repeat_adds, wearable, evidence, receipt, preview, tuple(read_actions), note, device_writes)


TABLE = {
    # ---- the interface ----
    'assistant_control': _rule('Microphone, screen sharing and the floating JARVIS', CHANGES, SCREEN,
        'Yes: say the opposite command.', asks=WORDS, receipt=True,
        read_actions=('hologram_status', 'screen_status', 'microphone_status'),
        note='The window that asked must confirm within 30 seconds.'),
    'navigate_panel': _rule('Open a section of the interface', CHANGES, SCREEN, 'Yes: open another section.', receipt=True),
    'inspect_interface': _rule('Inspect the interface with screenshots', CHANGES, ONLINE,
        'No: a saved inspection report is kept.', receipt=True,
        note='Pictures of the interface go to the AI provider only when you allow sending.'),
    'inspection_reports': _rule('Read saved inspection reports'),
    'inspection_findings': _rule('Read the list of interface findings',
        note='Reading the list also brings each finding\'s status up to date in JARVIS\'s own records.'),
    'inspection_link_change': _rule('Link a proposed change to a finding', CHANGES, LOCAL,
        'No: the history is kept; a later entry corrects it.'),
    # ---- saved things ----
    'save_item': _rule('Save a note, a task or a fact', CHANGES, LOCAL, 'Yes: delete it in Memory or Tasks.',
        repeat_adds=True, evidence=True, receipt=True, preview=True, device_writes=True,
        note='A fact is saved only when your own words ask JARVIS to remember it.'),
    'list_items': _rule('Read saved facts, notes or tasks', wearable=True),
    'manage_saved_memory': _rule('Change or delete a saved fact', CHANGES, LOCAL,
        'No: a deleted fact is gone (your last backup still has it).', asks=WORDS, receipt=True, device_writes=True),
    'set_timer': _rule('Set a timer', CHANGES, LOCAL, 'Yes: cancel the timer.', repeat_adds=True,
        evidence=True, receipt=True, preview=True, device_writes=True),
    'manage_timer': _rule('List, cancel or change timers', CHANGES, LOCAL,
        'No: a cancelled timer is gone; set it again.', asks=WORDS, receipt=True, read_actions=('list',), device_writes=True),
    'create_file': _rule('Create a document file', CHANGES, LOCAL,
        'No automatic undo: the file stays in the generated folder.', repeat_adds=True,
        evidence=True, receipt=True, preview=True),
    'preview_action': _rule('Draft a note, task, timer or file for your approval', CHANGES, LOCAL,
        'Nothing happens unless you approve.', asks=ALWAYS, receipt=True),
    # ---- chats and projects ----
    'conversation_search': _rule('Search past chats', wearable=True),
    'conversation_read': _rule('Read a past chat', wearable=True),
    'project_catalog': _rule('List projects and chats', wearable=True),
    'project_read': _rule('Read a project', wearable=True),
    'project_link_chat': _rule('Link a chat to a project', CHANGES, LOCAL, 'Yes: link the chat to another project.',
        evidence=True, receipt=True),
    'project_save_document': _rule('Save a project document', CHANGES, LOCAL,
        'No automatic undo: the document stays in Files.', repeat_adds=True, evidence=True, receipt=True),
    'research_report': _rule('Gather saved research for a report'),
    # ---- the web and media ----
    'web_search': _rule('Search the web', reach=ONLINE, wearable=True),
    'news_search': _rule('Search the news', reach=ONLINE, wearable=True),
    'image_search': _rule('Search for pictures', reach=ONLINE),
    'daily_briefing': _rule('Prepare the daily briefing', reach=ONLINE),
    'get_directions': _rule('Get directions from Google Maps', reach=ONLINE),
    # ---- mail and the calendar (1.0.17, item G of docs/PHONE-ACCESS-PLAN.md; the owner's steps in docs/GOOGLE-STEPS.md) ----
    'mail_search': _rule('Search your mail', reach=ONLINE, wearable=True,
        note='Gmail over IMAP with an app password: reads what the question asks for and marks nothing read.'),
    'mail_read': _rule('Read one mail', reach=ONLINE, wearable=True,
        note='The mail\'s text is data from its sender, not instructions.'),
    'mail_send': _rule('Send a mail from your address', CHANGES, ONLINE, 'No: a sent mail cannot be unsent.', asks=ALWAYS, receipt=True,
        note='Always asks first: you see to whom, the subject and the text before anything leaves (on the PC, or on a device that may approve).'),
    'calendar_events': _rule('Read your calendar', reach=ONLINE, wearable=True,
        note='From the calendar\'s secret address (Settings > Connections); reading only.'),
    'youtube': _rule('Find and load a YouTube video', CHANGES, ONLINE, 'Yes: load another video or close the panel.'),
    'spotify': _rule('Control Spotify', CHANGES, ONLINE, 'Yes: say the opposite command.', receipt=True,
        read_actions=('status',)),
    'play_music': _rule('Play music from your files', CHANGES, PC, 'Yes: say "stop the music".', receipt=True,
        read_actions=('status', 'list'),
        note='Your own music files in the music folder (Settings > Music), played on this PC\'s speakers; the Core answers "play <nickname>" itself.'),
    # ---- this PC ----
    'computer_system_info': _rule('Read this PC\'s hardware and Windows details', reach=PC),
    'computer_files': _rule('List JARVIS\'s own source files'),
    'computer_read_file': _rule('Read one of JARVIS\'s own source files'),
    'computer_run_tests': _rule('Run JARVIS\'s own tests', reach=PC, note='Runs the fixed test suite; nothing else can be run.'),
    'computer_open_page': _rule('Open a web page in your browser', CHANGES, PC, 'Yes: close the tab.', repeat_adds=True),
    'open_app': _rule('Open Calculator, Notepad or Paint', CHANGES, PC, 'Yes: close the program.', repeat_adds=True, receipt=True),
    # ---- answers about itself ----
    'time_now': _rule('Read the time', wearable=True),
    'calculate': _rule('Calculate', evidence=True),
    'suit_diagram': _rule('Draw a concept diagram', evidence=True),
    'device_registry': _rule('Read the list of devices', wearable=True),
    'response_timings': _rule('Read how long recent answers took'),
    'service_status': _rule('Read the results of earlier connection checks'),
    'system_health': _rule('Check the AI and search connections', reach=ONLINE),
    # ---- JARVIS changing itself: always the owner's approval, with the difference shown ----
    'development_history': _rule('Read the history of its own changes', reach=SELF),
    'development_read': _rule('Read one of its own files', reach=SELF),
    'development_propose': _rule('Propose a change to its own personality, style or program', CHANGES, SELF,
        'Yes: Undo in Release history (asks again).', asks=ALWAYS, receipt=True,
        note='An installed JARVIS never changes its program files: those changes are saved as proposals only.'),
    'development_edit': _rule('Propose an exact edit to its own personality, style or program', CHANGES, SELF,
        'Yes: Undo in Release history (asks again).', asks=ALWAYS, receipt=True,
        note='An installed JARVIS never changes its program files: those changes are saved as proposals only.'),
    'development_rollback': _rule('Undo one of its own changes', CHANGES, SELF,
        'Yes: the change can be made again.', asks=ALWAYS, receipt=True),
}

# Lists other modules used to keep for themselves.
WEARABLE_TOOLS = frozenset(name for name, rule in TABLE.items() if rule.wearable)
DEVICE_WRITE_TOOLS = frozenset(name for name, rule in TABLE.items() if rule.device_writes)  # with the owner's tick only
# Tools whose result only the JARVIS window that asked carries out (opening a section, starting an inspection,
# loading a video): a device has no asking window, so even with "may use this PC's tools" (1.0.17) they are
# refused and not offered. The window's controls (assistant_control) are carried to the window for a device's
# question instead (docs/PHONE-ACCESS-1.0.17.md item C).
WINDOW_TOOLS = frozenset(('navigate_panel', 'inspect_interface', 'youtube'))
ACTION_TOOLS = frozenset(name for name, rule in TABLE.items() if rule.receipt)
EVIDENCE_TOOLS = frozenset(name for name, rule in TABLE.items() if rule.evidence)
PREVIEW_TOOLS = ('save_item', 'set_timer', 'create_file')
assert set(PREVIEW_TOOLS) == {name for name, rule in TABLE.items() if rule.preview}

# The owner's switch for each tool (Settings > Permissions). It can only make a tool stricter.
DEFAULT, ASK, OFF = 'default', 'ask', 'off'
MODES = (DEFAULT, ASK, OFF)

STOPPED_MESSAGE = 'JARVIS is stopped (emergency stop). Nothing runs until you press RESUME on the PC.'
# The emergency stop by voice or typing, from any device. Only the whole message counts, so talking about
# stopping something is not a stop. Capitals and punctuation do not matter (speech recognition adds its own:
# "Emergency, stop." and "Emergency stop?" both stop). Anything else in the message, a digit, an emoji or a word
# in another script, means it is not the stop ("stop all 3" is about three things). There is deliberately no
# phrase that resumes. The window uses the same words (static/permissions.js); the tests hold the two equal.
STOP_PHRASE = re.compile(r"(?:(?:hey|ok|okay) )?(?:jarvis )?(?:emergency stop|stop everything|stop all|kill switch)"
                         r"(?: (?:now|please))?(?: jarvis)?")
# What counts as punctuation here: blanks and the ASCII marks except the underscore, plus the curly quotes, the
# dashes and the ellipsis that keyboards and speech recognition put in. Written out so that Python and JavaScript
# read exactly the same set.
_STOP_SEPARATORS = re.compile('[ \\t\\n\\r\\f\\v\\u00a0!-/:-@\\[-\\^`{-~\\u2018\\u2019\\u201c\\u201d\\u2026\\u2013\\u2014]+')


def stop_phrase(text):
    if not isinstance(text, str) or len(text) > 80:
        return False
    return bool(STOP_PHRASE.fullmatch(_STOP_SEPARATORS.sub(' ', text.lower()).strip(' ')))


def effect(name, args=None):
    """What this call does: a few tools only read for some of their actions (listing timers, a status)."""
    rule = TABLE[name]
    if rule.effect == CHANGES and isinstance(args, dict) and args.get('action') in rule.read_actions:
        return READS
    return rule.effect


def modes_for(name):
    """The switch positions the owner can choose for a tool."""
    rule = TABLE[name]
    # "Ask first" is offered where it adds something: for a change that today happens at once. Not for a tool
    # that already asks or already needs the owner's exact words, and not for what happens inside the window
    # that asked (it needs the question that is still open, and can be undone with a word).
    return (DEFAULT, ASK, OFF) if rule.effect == CHANGES and rule.asks == NEVER and rule.reach != SCREEN else (DEFAULT, OFF)


def decide(name, args=None, *, stopped=False, by_jarvis=True, wearable=False, mode=DEFAULT, approved=False, writes=False, tools=False):
    """('run' | 'ask' | 'refuse', message) for one tool call.

    by_jarvis: the call belongs to a question JARVIS is answering (the AI model or a typed or spoken
    command). False for the owner's own click in the interface, which is its own approval.
    approved: the owner has just approved exactly this call on screen (on the PC or, 1.0.17, from a device).
    writes: the question comes from a paired device the owner ticked "may save memories and tasks" for.
    tools: the question comes from a paired device the owner ticked "may use this PC's tools" for (1.0.17,
    docs/PHONE-ACCESS-1.0.17.md): it may call every tool the PC's question may, under the same switches.
    """
    rule = TABLE.get(name)
    if rule is None:
        return 'refuse', 'Unknown tool.'
    does = effect(name, args)
    if stopped and (by_jarvis or does != READS or rule.reach not in (LOCAL, SELF)):
        return 'refuse', STOPPED_MESSAGE
    if wearable and name in WINDOW_TOOLS:
        return 'refuse', 'This needs the JARVIS window on the PC.'
    if wearable and not tools and not rule.wearable and not (writes and rule.device_writes):
        if rule.device_writes:  # a device without the owner's tick: say what would allow it
            return 'refuse', ('This operation is unavailable from the wearable client: this device may not save memories or tasks. '
                              'The owner allows that in Settings > Devices on the PC.')
        return 'refuse', 'This operation is unavailable from the wearable client.'
    if by_jarvis and mode == OFF:
        return 'refuse', f'"{rule.label}" is switched off in Settings > Permissions. Only the owner can switch it on.'
    if by_jarvis and mode == ASK and ASK in modes_for(name) and does == CHANGES and not approved:
        return 'ask', ''
    return 'run', ''


ASK_NOTE = (' The owner has chosen to be asked on screen before this happens: the call returns "awaiting approval" and'
            ' nothing has happened until they approve. Say that it is waiting, never that it is done.')


def offered(tool, mode):
    """A tool as the AI model is offered it: one set to "ask first" says so in its description."""
    name = tool['function']['name']
    if mode != ASK or name not in TABLE or ASK not in modes_for(name):
        return tool
    return {**tool, 'function': {**tool['function'], 'description': tool['function']['description'] + ASK_NOTE}}


def changed(modes=None):
    """The owner's switches that differ from "Allowed", as the window needs them: the few commands it answers
    by itself (sections, the microphone, timers, inspections) obey the same switches as the Core."""
    return {name: mode for name, mode in (modes or {}).items()
            if name in TABLE and mode != DEFAULT and mode in modes_for(name)}


def listing(modes=None):
    """The table as the interface shows it, with the owner's switch for each tool."""
    modes = modes or {}
    rows = []
    for name, rule in TABLE.items():
        mode = modes.get(name) if modes.get(name) in modes_for(name) else DEFAULT
        rows.append({'name': name, 'label': rule.label, 'effect': rule.effect, 'reach': rule.reach, 'undo': rule.undo,
                     'asks': rule.asks, 'repeat_adds': rule.repeat_adds, 'wearable': rule.wearable, 'note': rule.note,
                     'reads_for': list(rule.read_actions), 'mode': mode, 'modes': list(modes_for(name)), 'device_writes': rule.device_writes})
    return rows
