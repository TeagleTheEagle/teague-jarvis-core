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


def governed_by(text):
    """The tool whose permission covers this exact memory command (permissions.py), or None when the text
    is not a memory command that changes something. These commands are answered here, not by a tool call,
    so the Core asks the same table before it lets one run."""
    text = text.strip()
    if _PREFERENCE.fullmatch(text) or _NAME.fullmatch(text) or _PROJECT.fullmatch(text):
        return 'save_item'
    if _CORRECTION.fullmatch(text) or _REPLACE.fullmatch(text) or _FORGET.fullmatch(text):
        return 'manage_saved_memory'
    return None


def command(store, text):
    text = text.strip()
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
