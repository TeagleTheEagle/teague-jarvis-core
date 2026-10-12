"""Where JARVIS keeps things.

Development (running from the repository): everything stays where it always was —
data, models and the .env beside the source.

Installed release (docs/RELEASE-DESIGN.md): the launcher sets
  JARVIS_DATA_DIR    canonical data (memory database, generated files, Core files, logs)
  JARVIS_CONFIG_DIR  owner configuration (.env keys, personality.txt, preferences.json)
  JARVIS_MODELS_DIR  bundled speech and wake-word models (read-only, inside the release)
so program files and the owner's data never mix: updates, rollback, uninstall and
reinstall replace the program without touching data or configuration.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# PyInstaller-style frozen builds keep configuration beside the executable.
APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else ROOT


def _env_path(name):
    value = os.getenv(name, '').strip()
    return Path(value) if value else None


def install_home():
    """The per-user install folder when this code runs from an installed release
    (<home>\\releases\\<id>\\app, beside the release manifest); None in development. Lets the
    shipped command lines (recovery.py, switch_over.py) find the install without the launcher."""
    if ROOT.name == 'app' and ROOT.parent.parent.name == 'releases' and (ROOT.parent / 'manifest.json').is_file():
        return ROOT.parent.parent.parent
    return None


def installed():
    return _env_path('JARVIS_DATA_DIR') is not None or install_home() is not None


def data_dir():
    configured = _env_path('JARVIS_DATA_DIR')
    if configured:
        return configured
    home = install_home()
    return home / 'data' if home else ROOT / 'data'


def config_dir():
    configured = _env_path('JARVIS_CONFIG_DIR')
    if configured:
        return configured
    home = install_home()
    return home / 'config' if home else APP_ROOT


def config_dir_for(root):
    """The owner-config folder of the installation whose app folder is `root`: this process's
    configured folder when root is this code's own folder; the install layout beside root when
    root is another installed release; otherwise root itself (development keeps config beside
    the code). Tools that operate on a given installation must use this, not config_dir()."""
    root = Path(root).resolve()
    if root == ROOT:
        return config_dir()
    if root.name == 'app' and root.parent.parent.name == 'releases' and (root.parent / 'manifest.json').is_file():
        return root.parent.parent.parent / 'config'
    return root


def models_dir():
    # Development keeps downloaded models in the repository's data folder, independent of
    # any --data-dir used by tests.
    configured = _env_path('JARVIS_MODELS_DIR')
    if configured:
        return configured
    return ROOT.parent / 'models' if install_home() else ROOT / 'data'


def release_id():
    """The installed release's identity from its manifest (docs/RELEASE-DESIGN.md); None in development."""
    manifest = ROOT.parent / 'manifest.json'
    if not installed() or not manifest.is_file():
        return None
    try:
        import json
        return json.loads(manifest.read_text(encoding='utf-8')).get('release_id')
    except (OSError, ValueError):
        return None


def env_file():
    return config_dir() / '.env'


# Every personality text a release has shipped (sha256 of the text with LF line endings, outer blank space
# removed). The installer copies the shipped personality into the config folder at the first install, so a
# copy that still equals one of these was never changed by the owner: the wording of the release that runs
# applies, not the copy frozen at the first install. ADD the new hash whenever personality.txt changes
# (test_permissions_review.py fails until it is here); never remove one.
SHIPPED_PERSONALITIES = frozenset({
    '3edf45e42879411a65161564c11d6d7b08ad57f8c772ad311378ce2ab293f5d5',  # baseline; shipped in 1.0.7 to 1.0.14
    '762841ddbc68a0bee528b5f0faf697f0d24a4b1532ab9d6593bd7802e7c51a0b',  # 1.0.15: changes to itself ask first
    '91dfed8bb38d24da92c74456b9372b9eef12b8a3a2425097aadec96147fe5cca',  # 1.0.17: mail and the calendar (item G)
    '438631dcdf07bf507ae69f85c8ca0bb48c8b1b21f3c8f202b2ee92e3f55d0737',  # system_diagnostics (the owner's request of 2026-10-12)
})


def personality_hash(text):
    import hashlib
    return hashlib.sha256(text.replace('\r\n', '\n').strip().encode('utf-8')).hexdigest()


def unchanged_shipped_copy(path):
    """True when this file is, word for word, a personality text that some release shipped."""
    try:
        return personality_hash(Path(path).read_text(encoding='utf-8')) in SHIPPED_PERSONALITIES
    except (OSError, ValueError):
        return False


def personality_file_for(root, config):
    """The personality in effect for the program in `root` with the owner's config folder `config`: the
    owner's own copy when it differs from everything a release shipped, else the running release's text."""
    shipped, configured = Path(root) / 'personality.txt', Path(config) / 'personality.txt'
    if configured.is_file() and not unchanged_shipped_copy(configured):
        return configured
    return shipped if shipped.is_file() else configured


def personality_file():
    """The owner's personality if the config folder holds one of their own, else the shipped default."""
    return personality_file_for(ROOT, config_dir())


def wearable_connection_file():
    return config_dir() / '.env.wearable-connection.json'
