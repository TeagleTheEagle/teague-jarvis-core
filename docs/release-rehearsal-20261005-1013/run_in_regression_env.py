"""Run a command with the environment tools/release_regression.py gives the test suites (debugging only).
Usage: python run_in_regression_env.py <regression work folder> <command...>   ({electron} {python} {app} are filled in)"""
import os
import subprocess
import sys
from pathlib import Path

work = Path(sys.argv[1])
copy = work / 'release'
app = copy / 'app'
python, electron = copy / 'python' / 'python.exe', copy / 'electron' / 'electron.exe'
home = work / 'home'
local, roaming, temp = home / 'AppData' / 'Local', home / 'AppData' / 'Roaming', home / 'AppData' / 'Local' / 'Temp'
keep = ('SYSTEMROOT', 'SYSTEMDRIVE', 'WINDIR', 'COMSPEC', 'PATHEXT', 'NUMBER_OF_PROCESSORS', 'PROCESSOR_ARCHITECTURE',
        'PROGRAMFILES', 'PROGRAMFILES(X86)', 'PROGRAMW6432', 'PROGRAMDATA', 'ALLUSERSPROFILE',
        'COMMONPROGRAMFILES', 'COMMONPROGRAMFILES(X86)', 'COMMONPROGRAMW6432')
env = {k: v for k, v in os.environ.items() if k.upper() in keep}
env.update({'PATH': os.pathsep.join([str(python.parent), str(Path(os.environ['SYSTEMROOT']) / 'System32'),
                                     str(Path(os.environ['SYSTEMROOT']) / 'System32' / 'WindowsPowerShell' / 'v1.0')]),
            'TEMP': str(temp), 'TMP': str(temp), 'USERPROFILE': str(home),
            'LOCALAPPDATA': str(local), 'APPDATA': str(roaming),
            'JARVIS_DATA_DIR': str(work / 'data'), 'JARVIS_CONFIG_DIR': str(work / 'config'),
            'JARVIS_MODELS_DIR': str(copy / 'models'), 'JARVIS_PYTHON': str(python),
            'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8', 'ELECTRON_RUN_AS_NODE': '1'})
command = [a.format(electron=electron, python=python, app=app) for a in sys.argv[2:]]
done = subprocess.run(command, cwd=str(app / 'desktop'), env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
print(done.stdout + done.stderr)
sys.exit(done.returncode)
