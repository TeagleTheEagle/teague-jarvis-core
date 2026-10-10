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
    if name_from(body):   # one rule for names (1.0.18): "my name is on the lease" is not one
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
# A name, and only a name (1.0.18, reviews of 2026-10-10): "Call me when the build finishes." saved "when the build
# finishes" as the owner's name, also through a saved memory ("remember that my name is on the lease"). name_from is the
# one rule for the name command, for key() and for the store's name setting.
_NAME_LEAD = re.compile(r'(?:remember (?:that )?my name is|my name is|call me|preferred name:)\s+', re.I)
_NAME_NEVER = frozenset(('today tomorrow tonight later soon now whenever anytime sometime asap next this morning afternoon evening '
                         'night monday tuesday wednesday thursday friday saturday sunday january february march april june july '
                         'august september october november december').split())
_NAME_NOT_LOWER = frozenset('when if after before at in on by back please up about with a an the maybe again as once spelled spelt not'.split())


def name_from(text):
    """The name in "my name is ...", "call me ...", "remember that my name is ..." or a saved "Preferred name: ...", or
    None when what follows does not look like a name: at most four words of letters (with . ' -), no digits or commas;
    never a time ("tomorrow", "Monday"); never a lowercase "when", "back", "a" and the like first; and more than one
    word only when every word is capitalised ("Mr. Teague", "An Nguyen")."""
    text = ' '.join(text.strip().split())
    lead = _NAME_LEAD.match(text)
    if not lead:
        return None
    value = text[lead.end():].rstrip('.!').strip()
    words = value.split()
    if not words or len(words) > 4 or len(value) > 60:
        return None
    if not all(re.fullmatch(r"[^\W\d_]+(?:[.'\-][^\W\d_]+)*\.?", w) for w in words):
        return None
    first = words[0].strip(".'-").lower()
    if first in _NAME_NEVER or (words[0][0].islower() and first in _NAME_NOT_LOWER):
        return None
    if len(words) > 1 and not all(w[0].isupper() for w in words):
        return None
    return value
_PROJECT = re.compile(r'(?:remember |save |update )?project\s+([^:\n]{1,80}):\s*(.{1,4000})', re.I | re.S)
_REPLACE = re.compile(r'replace memory:\s*(.+?)\s*=>\s*(.+)', re.I | re.S)
_FORGET = re.compile(r'forget memory:\s*(.+)', re.I | re.S)
# "Remember that." said after a statement (1.0.17): the thing to remember is a line said before it in the
# conversation; since 1.0.18 (the owner's word, docs/CORE-FIXES-20261010.md) the owner's own last line, and JARVIS's
# last answer only for "remember what you said". Only the bare pointer, in its spoken forms ("remember that, please",
# "remember it for me"): "remember that I prefer tea" and "remember to buy milk" carry their own words and are
# handled as before.
# "mine" and "yours" name whose words are meant; "that", "this", "it" and a bare "remember" are decided by the
# owner's last line itself (pointer_role, previous_line; 1.0.18). Reviews of 2026-10-10: "please", "for me" and
# "Jarvis" any number of times, "Jarvis," first, and "?" or "…" at the end ("Remember that?" saved the word "that?"
# and "Remember that, Jarvis." the words "that, Jarvis." before).
_POINTER = re.compile(r'(?:(?:(?:hey|ok|okay)\s+)?jarvis[,\s]+)?(?:please\s+)?(?:remember|memori[sz]e)'
                      r'(?:\s+(?:that|this|it|(?P<mine>what\s+i\s+(?:just\s+)?said)|(?P<yours>what\s+you\s+(?:just\s+)?said)))?'
                      r'(?:[,\s]*(?:please|for me|jarvis))*[.!?,…]*', re.I)
# What JARVIS answers to a command of its own, and the Core's own lines in a conversation (approvals, refusals):
# never the line "remember that" points at.
_CONFIRMATIONS = ('Remembered: ', 'Saved: ', 'Saved that preference', 'Saved the current details', 'Updated that', 'Deleted that',
                  'I’ll call you ', 'Emergency stop is on', 'Waiting for approval on screen', 'Approved on screen', 'Approved from ',
                  'Use the exact saved', 'There is nothing before this to remember', 'Credentials cannot be saved as memory',
                  'I couldn’t identify one', 'Nothing saved: that was a command')
NOTHING_BEFORE = 'There is nothing before this to remember. Say what to remember, for example “remember that I prefer short answers”.'
COMMAND_HINT = ('Nothing saved: that was a command, not something to remember. Say what to remember, for example “remember that '
                'the gate code is 4421”, or “remember what you said” for my answer.')
# Whose words "remember that" keeps (the owner's choice of 2026-10-10, docs/CORE-FIXES-20261010.md): the owner's own
# line when they told JARVIS something; JARVIS's answer when they asked something (a question, a request, "analyse my
# screen"); nothing after a command. SCREEN_PROMPT is how the PC window's screen question starts (static/app.js
# screenDefaultQuestion; test_phone_core_fixes keeps the two in step).
SCREEN_PROMPT = 'Analyse this screenshot naturally.'
LIVE_FRAME = 'Live-session frame captured at'   # static/app.js: a frame the live screen sharing sends by itself
# The words line_kind reads, after "Jarvis," and "can you" / "please" are taken off (reviews of 2026-10-10):
_VOCATIVE = re.compile(r"^(?:(?:hey|ok|okay)\s+)?jarvis\b[,.!]?\s*|[,\s]+jarvis[.!?]*$", re.I)
_POLITE = re.compile(r"^(?:please\s+|(?:can|could|would|will)\s+(?:you|u)\s+(?:please\s+)?)", re.I)
_COPULA = re.compile(r"\b(?:is|are|was|were)\b", re.I)   # "Lock code for the shed is 1234.": a statement, not "lock ..."
_WANT = re.compile(r"i(?:'d| would)? (?:like|need|want) (?:a|an|some|the|to see|to know)\b", re.I)
_WH = frozenset("what what's whats when when's where where's who who's whom whose which why how how's".split())
_AUX = frozenset('is are am was were do does did can could will would should shall have has had may might'.split())
_SUBJECTS = frozenset(('i you we they he she it there this that these those my your our their his her its the a an any anyone '
                       'anything someone something').split())
_COMMAND_VERBS = frozenset(('set start stop cancel open close launch play pause resume skip turn switch mute unmute send delete '
                            'remove approve reject lock unlock restart shut remind kill').split())
_REQUEST_VERBS = frozenset(('tell show explain describe write draft give find search look check analyse analyze summarise summarize '
                            'translate list read compare calculate recommend suggest help make create plan define teach brainstorm '
                            'outline review').split())
# A word of thanks, a yes or a greeting is not what "remember that" means: looked past, with JARVIS's reply to it.
# Words, not a pattern, so no line can make the check slow.
_COURTESY = frozenset(("thanks thank you ty cheers ta ok okay cool nice great lovely perfect awesome good sounds sure yes yeah yep yup "
                       "no nope alright right got it that's thats all very much so a lot please jarvis mate sir fine brilliant excellent "
                       "appreciated appreciate hi hello hey morning afternoon evening night g'day gday").split())


def is_pointer(text):
    """"Remember that" and its spoken forms, with any spacing, case and punctuation."""
    return _POINTER.fullmatch(' '.join(text.split())) is not None


def pointer_role(text):
    """Whose line a pointer means (1.0.18): JARVIS's ('assistant') for "remember what you (just) said", the owner's
    ('user') for "remember what I (just) said", and 'auto' for "that", "this", "it" and a bare "remember", which the
    owner's last line decides (line_kind). Read from the same match as is_pointer, so the two never disagree."""
    match = _POINTER.fullmatch(' '.join(text.split()))
    return 'assistant' if match and match['yours'] else 'user' if match and match['mine'] else 'auto'


def line_kind(text):
    """What the owner's line was (1.0.18):
      - 'request': a question or a request, or the window's screen question; JARVIS's answer is what to keep;
      - 'command': it made JARVIS do something; there is nothing to keep;
      - 'saved': "remember <words>" or a note, which saved itself;
      - 'thanks': thanks, a yes or a greeting; looked past;
      - 'automatic': a frame the live screen sharing sent by itself; looked past;
      - 'statement': the owner told JARVIS something; the line itself is what to keep.
    Commands are recognised before questions, so "Can you set a timer?" is a command and "May 12 is Mum's
    birthday." a statement."""
    import actions, answer_evidence, music, permissions   # here, not at the top: memory is imported by much of the Core
    text = ' '.join(text.replace('’', "'").replace('‘', "'").split())   # the iPhone's curly apostrophe
    if text.startswith(SCREEN_PROMPT):
        return 'automatic' if LIVE_FRAME in text else 'request'
    words = re.findall(r"[a-z']+", text.lower())
    if words and len(words) <= 6 and not re.search(r'\d', text) and all(w in _COURTESY for w in words):
        return 'thanks'
    core = _VOCATIVE.sub('', text).strip()
    polite = bool(_POLITE.match(core))
    bare = _POLITE.sub('', core).strip().rstrip('?.!').strip()
    if permissions.stop_phrase(text) or permissions.stop_phrase(bare):
        return 'command'
    local = actions.local_command(bare)
    if local:
        name, args = local
        if name == 'save_item':
            return 'saved'
        return 'command' if name in permissions.TABLE and permissions.effect(name, args) == permissions.CHANGES else 'request'
    if music.command(bare, open=True):
        return 'command'
    if answer_evidence.command(bare):
        return 'request'
    w = re.findall(r"[a-z0-9']+", bare.lower())
    if not w:
        return 'statement'
    first, second = w[0], (w[1] if len(w) > 1 else '')
    if first == 'remind' and second == 'me' and len(w) > 2 and w[2] in ('what', 'when', 'where', 'who', 'how', 'of', 'about'):
        return 'request'   # "remind me what the gate code is" asks; "remind me to ..." sets a reminder
    if first in _COMMAND_VERBS and not _COPULA.search(bare):
        return 'command'
    if polite or text.endswith('?') or (first in _WH and ',' not in bare) or (first in _AUX and second in _SUBJECTS):
        return 'request'   # a question also without its "?", as speech leaves it; "Will is my brother." is not one
    if (first in _REQUEST_VERBS and not _COPULA.search(bare)) or _WANT.match(bare):
        return 'request'
    return 'statement'


def governed_by(text):
    """The tool whose permission covers this exact memory command (permissions.py), or None when the text
    is not a memory command that changes something. These commands are answered here, not by a tool call,
    so the Core asks the same table before it lets one run."""
    text = text.strip()
    if _PREFERENCE.fullmatch(text) or name_from(text) or _PROJECT.fullmatch(text) or is_pointer(text):
        return 'save_item'
    if _CORRECTION.fullmatch(text) or _REPLACE.fullmatch(text) or _FORGET.fullmatch(text):
        return 'manage_saved_memory'
    return None


def previous_line(store, conversation, command):
    """The line `command` points at in this conversation (the command itself is already on record), as (role, text),
    ('command', text) when it points at a command, or None (1.0.18, docs/CORE-FIXES-20261010.md; before, it was simply
    the line before, which after an answer was JARVIS's answer):
      - "remember what you said": JARVIS's last answer; "remember what I said": the owner's own last line;
      - "remember that" / "this" / "it": the owner's last line decides (line_kind, the owner's choice of 2026-10-10):
        a statement is kept as it is; after a question or a request, JARVIS's answer to it; after a command, nothing.
    The conversation is read as exchanges: a line of the owner's with JARVIS's lines after it. An exchange is looked
    past whole when the owner's line was another memory command (it saved itself, a repeated pointer included), thanks,
    a line that saved itself or a live-sharing frame (line_kind). The Core's own lines (_CONFIRMATIONS) are never
    JARVIS's words. Whitespace is collapsed and the text cut at 500 characters. The last 20 lines are looked at."""
    if not conversation:
        return None
    wanted = pointer_role(command)
    rows = [r for r in store.history(conversation, 20) if r.get('role') in ('user', 'assistant') and isinstance(r.get('content'), str)]
    if rows and rows[-1]['role'] == 'user' and rows[-1]['content'].strip() == command.strip():
        rows = rows[:-1]
    exchanges = []   # [owner's line or None, [JARVIS's lines after it]]
    for row in rows:
        body = ' '.join(row['content'].split())
        if not body:
            continue
        if row['role'] == 'user':
            exchanges.append([body, []])
        elif not body.startswith(_CONFIRMATIONS):
            if not exchanges:
                exchanges.append([None, []])
            exchanges[-1][1].append(body)
    for owner, answers in reversed(exchanges):
        kind = None
        if owner is not None:
            if governed_by(owner):
                continue
            kind = line_kind(owner)
            if kind in ('thanks', 'saved', 'automatic'):
                continue   # looked past, with JARVIS's reply to it
        if wanted == 'assistant':
            if answers:
                return 'assistant', answers[-1][:500]
            continue
        if owner is None:
            continue
        if wanted == 'user' or kind == 'statement':
            return 'user', owner[:500]
        if kind == 'command':
            return 'command', owner[:500]
        return ('assistant', answers[0][:500]) if answers else None
    return None


def saved_value(line):
    """What a pointer's line is saved as, and what an approval card shows: the owner's words as they are, JARVIS's as
    "JARVIS said: ..."."""
    role, body = line
    return body if role == 'user' else 'JARVIS said: ' + body


def command(store, text, conversation=None, line=None):
    """An exact memory command, answered without the model; None when `text` is not one. `conversation` lets
    "remember that" find the line it points at (previous_line); `line` (role, text) is that line found earlier and
    carried with an approval (server.App.memory_command)."""
    text = text.strip()
    if is_pointer(text):
        previous = tuple(line) if line else previous_line(store, conversation, text)
        if previous is None:
            return NOTHING_BEFORE
        if previous[0] == 'command':
            return COMMAND_HINT
        value = saved_value(previous)
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
    value = name_from(text)
    if value:
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
