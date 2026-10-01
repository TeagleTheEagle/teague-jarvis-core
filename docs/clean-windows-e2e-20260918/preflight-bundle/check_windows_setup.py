"""Read-only deployment preflight; never imports the Core or reads .env."""
import argparse
import ctypes
import json
import platform
import shutil
import struct
import subprocess
import sys


def runtime_errors(system, version, bits):
    errors = []
    if system != 'Windows':
        errors.append('This setup path requires Windows.')
    if tuple(version[:2]) != (3, 12) or bits != 64:
        errors.append('Use Python 3.12 x64; rebuild incompatible venvs separately.')
    return errors


def check(local_voice=False, tests=False, installed=False):
    errors = runtime_errors(platform.system(), sys.version_info, struct.calcsize('P') * 8)
    result = {'python': platform.python_version(), 'errors': errors}
    if tests:
        node = shutil.which('node')
        if not node:
            errors.append('Node.js 24.x is required for JS-backed regression tests.')
        else:
            try:
                version = subprocess.run([node, '--version'], capture_output=True, text=True,
                                         timeout=10, check=True).stdout.strip()
                result['node'] = version
                if not version.startswith('v24.'):
                    errors.append('Use the validated Node.js 24.x test toolchain.')
            except (OSError, subprocess.SubprocessError):
                errors.append('Node.js version check failed.')
    if local_voice and platform.system() == 'Windows':
        for dll in ('vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll'):
            try:
                # System32 only: do not accept a DLL planted in the working directory.
                ctypes.WinDLL(dll, winmode=0x00000800)
            except OSError:
                errors.append('Microsoft Visual C++ x64 Redistributable required: ' + dll)
        if installed and not errors:
            probe = subprocess.run([sys.executable, '-B', '-c',
                                    'import ctranslate2; import faster_whisper'],
                                   capture_output=True, timeout=60)
            result['stt_native_import'] = probe.returncode == 0
            if probe.returncode:
                errors.append('CTranslate2/faster-whisper native import failed; check VC++ x64 runtime and package installation.')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-voice', action='store_true')
    parser.add_argument('--tests', action='store_true')
    parser.add_argument('--installed', action='store_true')
    args = parser.parse_args()
    try:
        result = check(args.local_voice, args.tests, args.installed)
    except (OSError, subprocess.SubprocessError):
        result = {'errors': ['Prerequisite probe failed or timed out.']}
    print(json.dumps(result))
    sys.exit(bool(result['errors']))
