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


def personality_file():
    """The owner's personality if present in the config folder, else the shipped default."""
    configured = config_dir() / 'personality.txt'
    return configured if configured.is_file() else ROOT / 'personality.txt'


def wearable_connection_file():
    return config_dir() / '.env.wearable-connection.json'
