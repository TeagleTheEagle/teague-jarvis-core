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


def installed():
    return _env_path('JARVIS_DATA_DIR') is not None


def data_dir():
    return _env_path('JARVIS_DATA_DIR') or ROOT / 'data'


def config_dir():
    return _env_path('JARVIS_CONFIG_DIR') or APP_ROOT


def models_dir():
    # Development keeps downloaded models in the repository's data folder, independent of
    # any --data-dir used by tests.
    return _env_path('JARVIS_MODELS_DIR') or ROOT / 'data'


def env_file():
    return config_dir() / '.env'


def personality_file():
    """The owner's personality if present in the config folder, else the shipped default."""
    configured = config_dir() / 'personality.txt'
    return configured if configured.is_file() else ROOT / 'personality.txt'


def wearable_connection_file():
    return config_dir() / '.env.wearable-connection.json'
