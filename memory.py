"""Deterministic memory commands: no model inference or hidden learning."""
import re

_RELATED = {
    'short': {'brief', 'concise', 'short'}, 'brief': {'brief', 'concise', 'short'},
    'concise': {'brief', 'concise', 'short'}, 'project': {'project', 'build', 'work'},
    'work': {'project', 'build', 'work'}, 'prefer': {'prefer', 'like', 'want'},
    'like': {'prefer', 'like', 'want'}, 'favorite': {'favorite', 'favourite', 'like'},
    'favourite': {'favorite', 'favourite', 'like'},
}

def _terms(text):
    raw = set(re.findall(r'\w{3,}', text.casefold()))
    expanded = set(raw)
    for word in raw: expanded.update(_RELATED.get(word, ()))
    return expanded


def key(body):
    text = ' '.join(body.strip().rstrip('.').casefold().split())
    if re.match(r'(?:my name is|call me|preferred name:)', text):
        return 'profile:name'
    project = re.match(r'project\s+([^:]{1,80}):', text)
    if project:
        return 'project:' + project[1].strip()
    fact = re.match(r'(my [\w ]{1,60}?)\s+(?:is|are)\s+', text)
    if fact:
        return 'fact:' + fact[1]
    return 'text:' + text


# 1.0.17 item E (docs/PHONE-ACCESS-1.0.17.md section 5): the model is told the release each fact was saved under, and
# one rule, so an older release's note about JARVIS itself stops arguing with today's build.
STAMP_NOTE = ('Each saved fact ends with the JARVIS release it was saved under; one without a release was saved before 1.0.17 and'
              ' counts as the oldest; a stamp beginning with "development" is a build newer than any numbered release. A fact'
              ' about the owner holds whatever the release. When two facts about JARVIS itself (what it can do, how it is set'
              ' up) disagree, the one saved under the newer release is right and the older one is out of date but stays saved:'
              ' say so if asked, never argue from the older one, never remove it yourself. When unsure whether a fact is about'
              ' the owner or about JARVIS, keep it and say which is older. Do not repeat the stamps unless asked.')


def stamped(item):
    """A saved fact as the model sees it, with the release it was saved under."""
    release = item.get('release') if isinstance(item, dict) else None
    return str(item['body']) + (' [saved under ' + str(release) + ']' if release else '')


def relevant(items, query, limit=20):
    words = _terms(query) - {'the', 'and', 'what', 'about', 'remember'}
    def score(item):
        return len(words & _terms(item['body']))
    return sorted(items, key=lambda item: (score(item), item['updated']), reverse=True)[:limit]


_PREFERENCE = re.compile(r'(?:remember|save|learn)(?: that)? I prefer\s+(.+)', re.I | re.S)
_CORRECTION = re.compile(r'(?:correct|update) preference:\s*(.+?)\s*=>\s*(.+)', re.I | re.S)
_NAME = re.compile(r'(?:my name is|call me|remember (?:that )?my name is)\s+([^\n!?]{1,80})[.!]?', re.I)
_PROJECT = re.compile(r'(?:remember |save |update )?project\s+([^:\n]{1,80}):\s*(.{1,4000})', re.I | re.S)
_REPLACE = re.compile(r'replace memory:\s*(.+?)\s*=>\s*(.+)', re.I | re.S)
_FORGET = re.compile(r'forget memory:\s*(.+)', re.I | re.S)
# "Remember that." said after a statement (1.0.17): the thing to remember is a line said before it in the
# conversation; since 1.0.18 (the owner's word, docs/CORE-FIXES-20261010.md) the owner's own last line, and JARVIS's
# last answer only for "remember what you said". Only the bare pointer, in its spoken forms ("remember that, please",
# "remember it for me"): "remember that I prefer tea" and "remember to buy milk" carry their own words and are
# handled as before.
# "yours" is the one form that points at JARVIS's words, not the owner's (1.0.18). Review 2026-10-10: "please" and
# "for me" any number of times, and "?" or "…" at the end ("Remember that?" saved the word "that?" before).
_POINTER = re.compile(r'(?:please\s+)?(?:remember|memori[sz]e)(?:\s+(?:that|this|it|what\s+i\s+(?:just\s+)?said|(?P<yours>what\s+you\s+(?:just\s+)?said)))?'
                      r'(?:[,\s]*(?:please|for me))*[.!?,…]*', re.I)
# What JARVIS answers to a command of its own, and the Core's own lines in a conversation (approvals, refusals):
# never the line "remember that" points at.
_CONFIRMATIONS = ('Remembered: ', 'Saved: ', 'Saved that preference', 'Saved the current details', 'Updated that', 'Deleted that',
                  'I’ll call you ', 'Emergency stop is on', 'Waiting for approval on screen', 'Approved on screen', 'Approved from ',
                  'Use the exact saved', 'There is nothing before this to remember', 'Credentials cannot be saved as memory',
                  'I couldn’t identify one')
NOTHING_BEFORE = 'There is nothing before this to remember. Say what to remember, for example “remember that I prefer short answers”.'


def is_pointer(text):
    """"Remember that" and its spoken forms, with any spacing, case and punctuation."""
    return _POINTER.fullmatch(' '.join(text.split())) is not None


def pointer_role(text):
    """Whose line a pointer means (1.0.18): JARVIS's ('assistant') for "remember what you (just) said", the owner's
    ('user') for every other form. Read from the same match as is_pointer, so the two never disagree."""
    match = _POINTER.fullmatch(' '.join(text.split()))
    return 'assistant' if match and match['yours'] else 'user'


def governed_by(text):
    """The tool whose permission covers this exact memory command (permissions.py), or None when the text
    is not a memory command that changes something. These commands are answered here, not by a tool call,
    so the Core asks the same table before it lets one run."""
    text = text.strip()
    if _PREFERENCE.fullmatch(text) or _NAME.fullmatch(text) or _PROJECT.fullmatch(text) or is_pointer(text):
        return 'save_item'
    if _CORRECTION.fullmatch(text) or _REPLACE.fullmatch(text) or _FORGET.fullmatch(text):
        return 'manage_saved_memory'
    return None


def previous_line(store, conversation, command):
    """The line `command` points at in this conversation (the command itself is already on record), as (role, text),
    or None: the owner's own last line, or JARVIS's last answer for "remember what you said" (pointer_role; 1.0.18,
    before which it was simply the line before, which after an answer was JARVIS's answer). Skipped: another memory
    command of the owner's (it saved itself, a repeated pointer included) and JARVIS's answers to such commands;
    whitespace is collapsed and the text cut at 500 characters. The last 20 lines are looked at (8 before 1.0.18: only
    one speaker's lines count now, and approval receipts can stand between)."""
    if not conversation:
        return None
    wanted = pointer_role(command)
    rows = [r for r in store.history(conversation, 20) if r.get('role') in ('user', 'assistant') and isinstance(r.get('content'), str)]
    if rows and rows[-1]['role'] == 'user' and rows[-1]['content'].strip() == command.strip():
        rows = rows[:-1]
    for row in reversed(rows):
        body = ' '.join(row['content'].split())
        if (not body or row['role'] != wanted or (row['role'] == 'user' and governed_by(body))
                or (row['role'] == 'assistant' and body.startswith(_CONFIRMATIONS))):
            continue
        return row['role'], body[:500]
    return None


def command(store, text, conversation=None, line=None):
    """An exact memory command, answered without the model; None when `text` is not one. `conversation` lets
    "remember that" find the line it points at (previous_line); `line` (role, text) is that line found earlier and
    carried with an approval (server.App.memory_command)."""
    text = text.strip()
    if is_pointer(text):
        previous = tuple(line) if line else previous_line(store, conversation, text)
        if previous is None:
            return NOTHING_BEFORE
        role, body = previous
        value = body if role == 'user' else 'JARVIS said: ' + body
        store.put('memory', value, source='explicit_user', confidence=1.0)
        return 'Remembered: ' + value
    preference = _PREFERENCE.fullmatch(text)
    if preference:
        value = 'Preference: I prefer ' + preference[1].strip().rstrip('.')
        store.put('memory', value, category='preference', source='explicit_user', confidence=1.0)
        return 'Saved that preference. You can say “forget memory: ' + value + '” any time.'
    correction = _CORRECTION.fullmatch(text)
    if correction:
        matches = [r for r in store.items('memory') if r.get('category') == 'preference' and r['body'].casefold().endswith(correction[1].strip().casefold())]
        if len(matches) == 1:
            store.put('memory', 'Preference: ' + correction[2].strip(), matches[0]['id'], category='preference', source='explicit_correction', confidence=1.0)
            return 'Updated that preference.'
        return 'I couldn’t identify one preference to update. Use the exact saved preference before =>.'
    name = _NAME.fullmatch(text)
    if name:
        value = name[1].strip().rstrip('.')
        store.put('memory', 'Preferred name: ' + value)
        store.save_settings({'name': value})
        return 'I’ll call you ' + value + '. Your preferred name is saved.'
    project = _PROJECT.fullmatch(text)
    if project:
        store.put('memory', 'Project ' + project[1].strip() + ': ' + project[2].strip())
        return 'Saved the current details for project ' + project[1].strip() + '.'
    replace = _REPLACE.fullmatch(text)
    if replace:
        matches = [r for r in store.items('memory') if key(r['body']) == key(replace[1])]
        if len(matches) != 1:
            return 'I couldn’t identify one saved memory to replace. Use Edit in the Memory Bank.'
        store.put('memory', replace[2], matches[0]['id'])
        return 'Updated that saved memory.'
    forget = _FORGET.fullmatch(text)
    if forget:
        matches = [r for r in store.items('memory') if r['body'].strip().casefold() == forget[1].strip().casefold()]
        if len(matches) != 1:
            return 'Use the exact saved text after “forget memory:” or Delete in the Memory Bank.'
        store.delete('memory', matches[0]['id'])
        return 'Deleted that saved memory. Existing chat history is separate.'
    query = re.fullmatch(r'(?:find|search) memor(?:y|ies)(?: for)?[: ]+(.+)', text, re.I)
    if query:
        words = set(re.findall(r'\w+', query[1].casefold()))
        rows = [r for r in relevant(store.items('memory'), query[1]) if words & set(re.findall(r'\w+', r['body'].casefold()))]
        return '\n'.join(r['body'] for r in rows) if rows else 'No matching saved memories.'
    if re.fullmatch(r'(?:list|show)(?: my)? projects[.!]?', text, re.I):
        rows = [r['body'] for r in store.items('memory') if key(r['body']).startswith('project:')]
        return '\n'.join(rows) if rows else 'No saved projects. Try “project Website: build the landing page next”.'
    return None
