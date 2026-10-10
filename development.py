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

import content_guard
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
# change JARVIS proposes to it may set only those properties, with every number in a known unit and a sane
# range, in plain rules without attribute selectors, so it cannot hide, move, cover or relabel anything by the
# usual means (display, visibility, opacity, position, transform, size, generated text, @-rules, a layout
# variable). It also may not name the controls the owner stops, approves and manages devices with.
# This LIMITS a style change; it is not a guarantee (text coloured like its background is still unreadable).
# What protects the owner is the difference shown before approval, Undo, and the ways to stop that no style
# sheet reaches: the tray, the shortcut, the spoken and the typed stop words.
_SIDES = ('top', 'right', 'bottom', 'left')
_OWNER_CSS_PROPERTIES = frozenset("""
    color background background-color accent-color caret-color
    font-size font-family font-weight font-style font-variant line-height letter-spacing word-spacing
    text-align text-transform text-decoration text-shadow
    padding margin gap row-gap column-gap
    border border-color border-width border-style border-radius
    outline outline-color outline-width outline-style box-shadow""".split()
    + [f'{kind}-{side}' for kind in ('padding', 'margin', 'border') for side in _SIDES]
    + [f'border-{side}-{part}' for side in _SIDES for part in ('color', 'width', 'style')]
    + [f'border-{row}-{side}-radius' for row in ('top', 'bottom') for side in ('left', 'right')])
_OWNER_CSS_FUNCTIONS = frozenset(('rgb', 'rgba', 'hsl', 'hsla', 'var', 'linear-gradient', 'radial-gradient'))
_OWNER_CSS_ACCEPTS = 'In owner-style.css a rule may set only colours, fonts, text size, spacing, borders and shadows. '
# Rules may not name the controls the owner stops, approves and manages devices with.
_PROTECTED_CSS = ('.es-', 'emergencystop', '.perm-', 'permissions-panel', 'approval', 'action-review', 'reliability-panel', '.device')
_CSS_NUMBER = re.compile(r'(?<![a-z0-9_-])(-?)(\d*\.?\d+)([a-z%]*)')
_CSS_COLOUR = r'#[0-9a-f]{3,8}\b'
# The largest value a number may have, by its unit: everywhere, and for spacing (padding, margin, gap).
_CSS_LIMITS = {'': 1000, 'px': 400, 'pt': 300, 'em': 40, 'rem': 40, '%': 400}
_CSS_SPACING_LIMITS = {'': 0, 'px': 200, 'pt': 150, 'em': 20, 'rem': 20, '%': 50}
_CSS_NEGATIVE = frozenset(('box-shadow', 'text-shadow', 'letter-spacing', 'word-spacing', 'background'))
# Readable text: the sizes a text size or a line height may have, by unit (lowest, highest).
_CSS_TEXT_SIZE = {'px': (8, 96), 'pt': (6, 72), 'rem': (0.5, 6)}
_CSS_LINE_HEIGHT = {'': (0.8, 3), 'em': (0.8, 3), 'rem': (0.8, 3), '%': (80, 300), 'px': (8, 200), 'pt': (6, 150)}
_CSS_LETTER_SPACING = {'px': 20, 'pt': 15, 'em': 1, 'rem': 1}


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


def _check_owner_value(name, value):
    """One value of one property of the owner's style sheet. Raises ValueError with a sentence for the model."""
    def refuse(why):
        raise ValueError(_OWNER_CSS_ACCEPTS + why)
    custom = name.startswith('--')
    if '!' in value or any(function not in _OWNER_CSS_FUNCTIONS for function in re.findall(r'([a-z-]+)\(', value)):
        refuse(f'The value of "{name[:40]}" uses something that is not accepted.')
    if (name == 'color' or custom) and _transparent(value):
        refuse('Text cannot be made transparent, and a colour variable cannot be set to transparent.')
    if name in ('color', 'font-size', 'line-height') and 'var(' in value:
        refuse(f'"{name}" must be written out, not taken from a variable.')
    # What is left to read as numbers: no quoted names, no references to variables, no colours written in hex.
    plain = re.sub(_CSS_COLOUR, ' ', re.sub(r'var\(\s*--[a-z0-9_-]+\s*\)', ' ', re.sub(r'"[^"]*"|\'[^\']*\'', ' ', value)))
    if custom:
        # A variable of the owner's own may hold a colour and nothing else: the program lays itself out with
        # variables too, and a size put into one of those would move or shrink things.
        if re.search(r'\d', re.sub(r'(?:rgba?|hsla?)\([^()]*\)', ' ', plain)):
            refuse(f'A variable ("{name[:40]}") may hold a colour only.')
    spacing = name.split('-')[0] in ('padding', 'margin', 'gap') or name in ('row-gap', 'column-gap')
    radius = name.endswith('radius')
    numbers = [(sign == '-', float(number), unit) for sign, number, unit in _CSS_NUMBER.findall(plain)]
    for negative, number, unit in numbers:
        if unit == 'deg' and name == 'background':
            continue  # the direction of a gradient
        if unit not in _CSS_LIMITS:
            refuse(f'"{name[:40]}" has a number written in a way that is not accepted (use px, pt, em, rem or %).')
        if negative and name not in _CSS_NEGATIVE:
            refuse(f'"{name[:40]}" has a negative value; those are not accepted there.')
        limit = 9999 if radius and unit == 'px' else (_CSS_SPACING_LIMITS if spacing else _CSS_LIMITS)[unit]
        if number > limit and not (unit == '' and number == 0):
            refuse(f'"{name[:40]}" has a size that is too large.')
    if name == 'font-size' and (any(unit not in _CSS_TEXT_SIZE or not _CSS_TEXT_SIZE[unit][0] <= number <= _CSS_TEXT_SIZE[unit][1] for _, number, unit in numbers)):
        refuse('A text size is written in px, pt or rem and stays readable (8 to 96 px).')
    if name == 'line-height' and any(unit not in _CSS_LINE_HEIGHT or not _CSS_LINE_HEIGHT[unit][0] <= number <= _CSS_LINE_HEIGHT[unit][1] for _, number, unit in numbers):
        refuse('A line height stays between 0.8 and 3 times the text size.')
    if name in ('letter-spacing', 'word-spacing') and any(unit not in _CSS_LETTER_SPACING or number > _CSS_LETTER_SPACING[unit] for _, number, unit in numbers if number):
        refuse('The spacing between letters or words stays small (at most 20 px or 1 em).')


def _check_owner_css(content):
    """The owner's style sheet as JARVIS may propose it: plain rules, known properties, sane sizes."""
    text = re.sub(r'/\*.*?\*/', ' ', content.lower(), flags=re.S)
    if '/*' in text or '@' in text:
        raise ValueError(_OWNER_CSS_ACCEPTS + '@-rules and unfinished comments are not accepted.')
    if not re.fullmatch(r'(\s*[^{};]+\{[^{}]*\})*\s*', text):
        raise ValueError(_OWNER_CSS_ACCEPTS + 'Write plain rules: a selector, then its properties in braces.')
    for selector, body in re.findall(r'([^{};]+)\{([^{}]*)\}', text):
        if '[' in selector or '::' in selector or re.search(r':(before|after|first-letter|first-line|marker|placeholder|selection|backdrop)\b', selector):
            raise ValueError(_OWNER_CSS_ACCEPTS + 'Rules that pick elements by an attribute ([...]) or for generated or partial content (::before, ::after and the like) are not accepted.')
        if any(name in re.sub(r'\s+', '', selector) for name in _PROTECTED_CSS):
            raise ValueError('A style change cannot restyle the emergency stop, the approval cards, the Permissions switches or the Devices panel.')
        for declaration in filter(None, (part.strip() for part in body.split(';'))):
            name, colon, value = declaration.partition(':')
            name, value = name.strip(), re.sub(r'!\s*important\s*$', '', value.strip()).strip()
            if not colon or not value:
                raise ValueError(_OWNER_CSS_ACCEPTS + f'"{declaration[:60]}" is not a property with a value.')
            if name not in _OWNER_CSS_PROPERTIES and not re.fullmatch(r'--[a-z0-9_-]+', name):
                raise ValueError(_OWNER_CSS_ACCEPTS + f'"{name[:40]}" is not accepted.')
            _check_owner_value(name, value)


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
    return ('\nYou have real development_read, development_propose, development_edit and development_rollback tools. For a request to change your interface text size, colours or spacing, use them now rather than referring the user to device settings: read static/pro.css to find the rule, then put an overriding rule in owner-style.css (the owner\'s own style sheet, loaded last; it accepts only colours, fonts, text size in px, pt or rem, spacing, borders and shadows, in plain rules without attribute selectors, @-rules, positions, sizes or hidden elements). For a request to change your personality, edit personality.txt. '
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


def prepare(root, path, content, reason, restoring=False):
    """restoring: the content is what the file held before an applied change (Undo). It is shown and approved
    like any change, but today's rules for a newly proposed style sheet are not applied to it: the owner can
    always go back, also to a sheet they wrote by hand."""
    where = layout(root)
    before = read(where, path)
    if not isinstance(content, str) or len(content) > 200000 or (not content.strip() and path != 'owner-style.css'):
        raise ValueError('Replacement must contain 1–200000 characters.')
    held = content_guard.placeholders(content, before)   # the guard's stand-ins would replace real text (1.0.19)
    if held:
        raise ValueError(content_guard.WRITE_BACK.format(what=held[0]))
    if path.endswith('.css') and not (restoring and path in OWNER_FILES):
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
    return prepare(where, meta['path'], (folder / 'before.txt').read_text(encoding='utf-8'), 'Restore backup ' + proposal, restoring=True)


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
