"""JARVIS proposing changes to itself. Nothing here executes generated code.

Two kinds of file (permissions.py, master document section 6):

OWNER_FILES    the owner's customisations: the personality and a style sheet of the owner's own. They live in
               the config folder beside the key file, so an update, a rollback or a reinstall of the program
               keeps them, and the installed program files stay exactly as they were tested.
PROGRAM_FILES  parts of the program. Running from the source folder they can be changed after approval.
               An installed JARVIS never changes them: the change is saved as a proposal for a later release.

Every change waits for the owner's approval (server.App.approve) with the difference shown; none applies
by itself.
"""
import difflib
import hashlib
import json
import os
import re
import time
import uuid
from collections import namedtuple
from pathlib import Path

import runtime_paths

OWNER_FILES = ('personality.txt', 'owner-style.css')
PROGRAM_FILES = ('static/pro.css', 'static/app.js', 'static/voice.js', 'static/index.html', 'static/mic-worklet.js',
                 'desktop/companion.js', 'desktop/companion.html', 'desktop/companion.css',
                 'wake.py', 'local_stt.py', 'voice_engine.py', 'maps.py')
ALLOWED = OWNER_FILES + PROGRAM_FILES

PROPOSAL_ONLY = 'proposal only'
PROPOSAL_ONLY_NOTE = ('Saved as a proposal only. An installed JARVIS never changes its own program files; '
                      'the proposal is kept for the engineer and a later release.')

Layout = namedtuple('Layout', 'root data config installed')

# The owner's style sheet is for how things look: colours, fonts, text size, spacing, borders and shadows. A
# change JARVIS proposes to it may set only those properties, with sizes kept in a sane range, so it cannot hide,
# move, cover or relabel anything by the usual means (display, visibility, opacity, position, transform, size,
# generated text, @-rules). It also may not name the controls the owner stops and approves with.
# This LIMITS a style change; it is not a guarantee (text coloured like its background is still unreadable).
# What protects the owner is the difference shown before approval, Undo, and the ways to stop that no style
# sheet reaches: the tray, the shortcut, the spoken and the typed stop words.
_OWNER_CSS_PROPERTIES = frozenset('''
    color background background-color accent-color caret-color
    font-size font-family font-weight font-style font-variant line-height letter-spacing word-spacing
    text-align text-transform text-decoration text-shadow
    padding padding-top padding-right padding-bottom padding-left
    margin margin-top margin-right margin-bottom margin-left gap row-gap column-gap
    border border-top border-right border-bottom border-left border-color border-width border-style border-radius
    outline outline-color outline-width outline-style box-shadow'''.split())
_OWNER_CSS_FUNCTIONS = frozenset(('rgb', 'rgba', 'hsl', 'hsla', 'var', 'linear-gradient', 'radial-gradient'))
_OWNER_CSS_ACCEPTS = 'In owner-style.css a rule may set only colours, fonts, text size, spacing, borders and shadows. '
_PROTECTED_CSS = ('.es-', 'emergencystop', '.perm-', 'approval', 'action-review', 'reliability-panel', 'role=alert', "role='alert'", 'role="alert"')
_CSS_LENGTH = re.compile(r'(\d*\.?\d+)(px|pt|rem|em|vmin|vmax|vh|vw|ch|ex|cm|mm|in|q|%)')


def _transparent(value):
    """A colour written so that nothing shows: the word, a hex colour with no opacity, or an alpha of zero."""
    if re.search(r'\btransparent\b', value) or re.search(r'#(?:[0-9a-f]{3}0|[0-9a-f]{6}00)\b', value):
        return True
    for inside in re.findall(r'(?:rgba?|hsla?)\(([^()]*)\)', value):
        alpha = inside.rsplit('/', 1)[1] if '/' in inside else inside.split(',')[3] if inside.count(',') == 3 else None
        number = re.fullmatch(r'\s*(\d*\.?\d+)\s*%?\s*', alpha) if alpha is not None else None
        if number and float(number[1]) == 0:
            return True
    return False


def _check_owner_css(content):
    """The owner's style sheet as JARVIS may propose it: plain rules, known properties, sane sizes."""
    low = content.lower()
    if any(x in low.replace(' ', '').replace('\t', '') for x in _PROTECTED_CSS):
        raise ValueError('A style change cannot restyle the emergency stop, the approval cards or the Permissions switches.')
    text = re.sub(r'/\*.*?\*/', ' ', low, flags=re.S)
    if '/*' in text or '@' in text:
        raise ValueError(_OWNER_CSS_ACCEPTS + '@-rules and unfinished comments are not accepted.')
    if not re.fullmatch(r'(\s*[^{};]+\{[^{}]*\})*\s*', text):
        raise ValueError(_OWNER_CSS_ACCEPTS + 'Write plain rules: a selector, then its properties in braces.')
    for selector, body in re.findall(r'([^{};]+)\{([^{}]*)\}', text):
        if '::' in selector or re.search(r':(before|after|first-letter|first-line|marker|placeholder|selection|backdrop)\b', selector):
            raise ValueError(_OWNER_CSS_ACCEPTS + 'Rules for generated or partial content (::before, ::after and the like) are not accepted.')
        for declaration in filter(None, (part.strip() for part in body.split(';'))):
            name, colon, value = declaration.partition(':')
            name, value = name.strip(), re.sub(r'!\s*important\s*$', '', value.strip()).strip()
            if not colon or not value:
                raise ValueError(_OWNER_CSS_ACCEPTS + f'"{declaration[:60]}" is not a property with a value.')
            if name not in _OWNER_CSS_PROPERTIES and not re.fullmatch(r'--[a-z0-9_-]+', name):
                raise ValueError(_OWNER_CSS_ACCEPTS + f'"{name[:40]}" is not accepted.')
            if '!' in value or any(function not in _OWNER_CSS_FUNCTIONS for function in re.findall(r'([a-z-]+)\(', value)):
                raise ValueError(_OWNER_CSS_ACCEPTS + f'The value of "{name[:40]}" uses something that is not accepted.')
            plain = re.sub(r'#[0-9a-f]{3,8}\b', ' ', value)  # a colour written in hex is not a number
            if re.search(r'(?<![\w#-])-\s*\.?\d', plain):
                raise ValueError(_OWNER_CSS_ACCEPTS + f'"{name[:40]}" has a negative value; those are not accepted.')
            for number, unit in _CSS_LENGTH.findall(plain):
                if float(number) > (400 if unit in ('px', 'pt', '%') else 40):
                    raise ValueError(_OWNER_CSS_ACCEPTS + f'"{name[:40]}" has a size that is too large.')
            if name == 'font-size':
                sizes = _CSS_LENGTH.findall(plain)
                smallest = {'px': 8, 'pt': 6, 'em': 0.5, 'rem': 0.5, '%': 50}
                if 'var(' in value or (not sizes and re.search(r'\d', plain)) or any(float(number) < smallest.get(unit, 1) for number, unit in sizes):
                    raise ValueError(_OWNER_CSS_ACCEPTS + 'A text size must be written out and stay readable (at least 8px, 0.5em or 50%).')
            if name == 'color' and _transparent(value):
                raise ValueError(_OWNER_CSS_ACCEPTS + 'Text cannot be made transparent.')


def _check_css(path, content):
    low = content.lower()
    if content.count('{') != content.count('}') or any(x in low for x in ('url(', '@import', 'expression(')):
        raise ValueError('CSS requires balanced braces and cannot load external resources.')
    if chr(92) in content:  # a backslash: an escaped character could spell a refused word or a hidden selector
        raise ValueError('CSS in a proposed change cannot contain a backslash (escaped characters are not accepted).')
    if path in OWNER_FILES:
        _check_owner_css(content)


def guidance(installed):
    """What the AI model is told about changing JARVIS itself (added to the instructions of every question;
    tools/host/make_request_template.py copies the installed wording for the owner-run provider checks)."""
    program = ('This JARVIS is installed: its program files are never changed from here. A change to any other allowlisted file is saved as a proposal only, for the engineer and a later release; say so plainly. '
               if installed else
               'Changes to the other allowlisted source files also wait for approval; syntax checks do not prove runtime correctness. Offer computer_run_tests and explain restart requirements after approval. ')
    return ('\nYou have real development_read, development_propose, development_edit and development_rollback tools. For a request to change your interface text size, colours or spacing, use them now rather than referring the user to device settings: read static/pro.css to find the rule, then put an overriding rule in owner-style.css (the owner\'s own style sheet, loaded last; it accepts only colours, fonts, text size, spacing, borders and shadows, in plain rules without @-rules, positions, sizes or hidden elements). For a request to change your personality, edit personality.txt. '
            'Every change waits for the owner\'s approval in the interface, with the difference shown: say that it is waiting, never that it is applied. This replaces any earlier wording about applying style or personality changes directly. '
            + program + 'Credentials, launchers, permission enforcement and arbitrary files cannot be changed by these tools. A missing provider integration still needs an implementation and the user must complete that provider\'s consent flow.')


def layout(root, data=None, config=None, installed=False):
    """Where things are. A bare folder means the source layout: proposals in <root>/data, owner files in <root>."""
    if isinstance(root, Layout):
        return root
    root = Path(root)
    return Layout(root, Path(data) if data else root / 'data', Path(config) if config else root, bool(installed))


def _target(where, path):
    """The file a change to `path` would write."""
    if path not in ALLOWED:
        raise ValueError('Choose an allowed development source. Credentials, permissions, launchers and the action gateway are excluded.')
    if path in OWNER_FILES:
        target = where.config / path
        if target.is_symlink():
            raise ValueError('Unsafe development target.')
        return target
    target = where.root / path
    if target.is_symlink() or target.resolve() != where.root.resolve() / path:
        raise ValueError('Unsafe development target.')
    return target


def applies(where, path):
    """Can a change to this file be applied here at all (after approval)?"""
    where = layout(where)
    if not where.installed:
        return True
    # Installed: only the owner's own files, and only when they live outside the program folder. (A config
    # folder that is the program folder itself would put the change among the tested program files.)
    return path in OWNER_FILES and where.config.resolve() != where.root.resolve()


def read(root, path):
    where = layout(root)
    target = _target(where, path)
    if path == 'personality.txt':
        # The personality in effect: the owner's own copy, or the text the program ships with when there is no
        # copy yet or the copy is still the untouched text of an earlier release (runtime_paths).
        target = runtime_paths.personality_file_for(where.root, where.config)
    if path == 'owner-style.css' and not target.is_file():
        return ''  # no custom style yet
    return target.read_text(encoding='utf-8')


def prepare(root, path, content, reason):
    where = layout(root)
    before = read(where, path)
    if not isinstance(content, str) or len(content) > 200000 or (not content.strip() and path != 'owner-style.css'):
        raise ValueError('Replacement must contain 1–200000 characters.')
    if path.endswith('.css'):
        _check_css(path, content)
    validation = validate(where, path, content)
    if content == before:
        raise ValueError('No changes proposed.')
    can_apply = applies(where, path)
    if path in OWNER_FILES:
        validation += f' {len(content):,} characters (now {len(before):,}).'
    if path == 'personality.txt' and can_apply and _earlier_release_wording(where, content):
        # For example undoing the owner's own change after an update: what comes back is not this old text.
        validation += (' This is the wording of an earlier release. After approval no wording of your own is left,'
                       ' and the personality of the release that is running applies, not this older text.')
    folder = where.data / 'development' / uuid.uuid4().hex
    folder.mkdir(parents=True)
    (folder / 'before.txt').write_text(before, encoding='utf-8')
    (folder / 'candidate.txt').write_text(content, encoding='utf-8')
    meta = {'status': 'staged' if can_apply else PROPOSAL_ONLY, 'created': time.time(), 'path': path, 'reason': reason,
            'hash': hashlib.sha256(before.encode()).hexdigest(), 'candidate_hash': hashlib.sha256(content.encode()).hexdigest(),
            'validation': validation}
    (folder / 'meta.json').write_text(json.dumps(meta), encoding='utf-8')
    result = {'proposal': folder.name, 'path': path, 'reason': reason,
              'diff': ''.join(difflib.unified_diff(before.splitlines(True), content.splitlines(True), fromfile=path, tofile=path)),
              'validation': validation, 'requires_approval': can_apply}
    if not can_apply:
        result.update(status=PROPOSAL_ONLY, summary=PROPOSAL_ONLY_NOTE)
    return result


def _earlier_release_wording(where, text):
    """True when `text` is a personality some earlier release shipped and not the one the running release ships.
    Such a text in the config folder counts as "no wording of the owner's own" (runtime_paths)."""
    shipped = where.root / 'personality.txt'
    if where.config.resolve() == where.root.resolve() or not shipped.is_file():
        return False
    return runtime_paths.personality_hash(text) in runtime_paths.SHIPPED_PERSONALITIES and text != shipped.read_text(encoding='utf-8')


def _load(where, proposal):
    if not isinstance(proposal, str) or len(proposal) != 32 or any(x not in '0123456789abcdef' for x in proposal):
        raise ValueError('Invalid proposal.')
    folder = where.data / 'development' / proposal
    return folder, json.loads((folder / 'meta.json').read_text(encoding='utf-8'))


def _write(where, path, candidate):
    target = _target(where, path)
    if path == 'owner-style.css' and not candidate.strip():
        target.unlink(missing_ok=True)  # no custom style
        return
    shipped = where.root / path
    if path == 'personality.txt' and target.resolve() != shipped.resolve() and shipped.is_file() and (
            candidate == shipped.read_text(encoding='utf-8') or _earlier_release_wording(where, candidate)):
        # Back to a personality the program shipped (this release's or an earlier one's): no private copy is
        # kept, so the wording of the release that runs applies, now and after later updates.
        target.unlink(missing_ok=True)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + '.new')
    partial.write_text(candidate, encoding='utf-8')
    os.replace(partial, target)  # the file is never seen half written


def apply(root, proposal):
    where = layout(root)
    folder, meta = _load(where, proposal)
    current = read(where, meta['path'])
    if meta.get('status') == PROPOSAL_ONLY or not applies(where, meta['path']):
        raise ValueError('This is a proposal only: an installed JARVIS never changes its own program files.')
    if meta.get('status') != 'staged':
        raise ValueError('This proposal has already been applied.')
    if hashlib.sha256(current.encode()).hexdigest() != meta['hash']:
        raise ValueError('File changed since preview. Prepare a new proposal.')
    candidate = (folder / 'candidate.txt').read_text(encoding='utf-8')
    if meta.get('candidate_hash') and hashlib.sha256(candidate.encode()).hexdigest() != meta['candidate_hash']:
        raise ValueError('Candidate changed since preview. Prepare a new proposal.')
    validation = validate(where, meta['path'], candidate)
    _write(where, meta['path'], candidate)
    meta.update(status='applied', applied=time.time())
    (folder / 'meta.json').write_text(json.dumps(meta), encoding='utf-8')
    next_step = ('A personality change applies from the next question. Reload the JARVIS window to see a style change.'
                 if meta['path'] in OWNER_FILES else
                 'Restart JARVIS for Python changes; refresh for interface changes. Run the test suite and a live feature test before relying on the change.')
    return {'status': 'applied', 'path': meta['path'], 'proposal': proposal, 'validation': validation, 'next_step': next_step}


def rollback(root, proposal):
    where = layout(root)
    folder, meta = _load(where, proposal)
    if meta.get('status') != 'applied':
        raise ValueError('Only an applied change can be rolled back.')
    if read(where, meta['path']) != (folder / 'candidate.txt').read_text(encoding='utf-8'):
        raise ValueError('File changed after this proposal. Read the current source and prepare a new edit.')
    return prepare(where, meta['path'], (folder / 'before.txt').read_text(encoding='utf-8'), 'Restore backup ' + proposal)


def history(root):
    where = layout(root)
    rows = []
    for folder in (where.data / 'development').glob('*'):
        if not folder.is_dir() or folder.is_symlink():
            continue
        try:
            meta = json.loads((folder / 'meta.json').read_text(encoding='utf-8'))
            before = (folder / 'before.txt').read_text(encoding='utf-8')
            after = (folder / 'candidate.txt').read_text(encoding='utf-8')
            current = read(where, meta['path'])
            rows.append({**meta, 'proposal': folder.name, 'created': meta.get('created', folder.stat().st_mtime),
                         'status': meta.get('status', 'legacy — status not recorded'),
                         'can_undo': meta.get('status') == 'applied' and current == after and before != after,
                         'diff': ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=meta['path'], tofile=meta['path'])),
                         'validation': meta.get('validation', 'Basic content checks only. Runtime tests were not performed.')})
        except (OSError, ValueError, KeyError):
            continue
    return {'changes': sorted(rows, key=lambda r: r['created'], reverse=True)[:50]}


def validate(root, path, content):
    where = layout(root)
    if path.endswith('.py'):
        import ast
        try:
            ast.parse(content)
        except SyntaxError as exc:
            raise ValueError(f'Python syntax error at line {exc.lineno}: {exc.msg}') from None
        return 'Python syntax checked without execution. Runtime behavior is untested.'
    if path.endswith('.js'):
        import subprocess, tempfile
        executable = where.root / 'desktop/node_modules/electron/dist/electron.exe'
        if not executable.is_file():
            if not applies(where, path):
                return 'Not syntax-checked: an installed JARVIS has no JavaScript checker.'
            raise ValueError('The installed JavaScript checker is unavailable.')
        with tempfile.TemporaryDirectory(prefix='jarvis-syntax-') as folder:
            candidate = Path(folder) / 'candidate.js'
            candidate.write_text(content, encoding='utf-8')
            result = subprocess.run([str(executable), '--check', str(candidate)], capture_output=True, text=True, timeout=15, env={**os.environ, 'ELECTRON_RUN_AS_NODE': '1'}, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            raise ValueError('JavaScript syntax check failed. ' + result.stderr[-1500:])
        return 'JavaScript syntax checked without execution. Runtime behavior is untested.'
    return 'Basic content checks only. Rendering and behavior need a live test.'


def edit(root, path, old, new, reason):
    where = layout(root)
    before = read(where, path)
    if not old or before.count(old) != 1:
        raise ValueError('The exact original text must match once. Read the source again.')
    return prepare(where, path, before.replace(old, new, 1), reason)
