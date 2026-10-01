"""Bounded local computer tools. No model-supplied shell commands."""
import json
import os
import re
import subprocess
import sys
import threading
import urllib.parse
import webbrowser
from pathlib import Path

TEST_LOCK = threading.Lock()
ROOT_FILES = {'server.py','actions.py','providers.py','wake.py','local_stt.py',
              'voice_engine.py','computer_tools.py','conversation_context.py','personality.txt',
              'requirements.txt','requirements-local-voice.txt','LOCAL-VOICE-LAB.md'}

def safe_text(text):
    for key, value in os.environ.items():
        if len(value) >= 8 and any(word in key.upper() for word in ('KEY','TOKEN','SECRET','PASSWORD')):
            text = text.replace(value, '[REDACTED]')
    return re.sub(r'\b(?:sk-proj-|sk-|gsk_)[A-Za-z0-9_-]{12,}', '[REDACTED]', text)

def source_files(root):
    root = Path(root).resolve()
    names = sorted(ROOT_FILES | {p.relative_to(root).as_posix() for p in (root/'static').glob('*') if p.suffix in ('.js','.css','.html')} | {p.name for p in root.glob('test_*.py')})
    return [name for name in names if (root/name).is_file() and not (root/name).is_symlink() and (root/name).resolve().is_relative_to(root)]

def read_source(root, path, start_line=1):
    if path not in source_files(root):
        raise ValueError('Choose a source path returned by computer_files. Credentials and personal data are excluded.')
    if not isinstance(start_line,int) or isinstance(start_line,bool) or start_line<1:
        raise ValueError('Start line must be a positive integer.')
    lines=(Path(root)/path).read_text(encoding='utf-8').splitlines()
    content='\n'.join(f'{n+1}: {line}' for n,line in enumerate(lines) if start_line-1<=n<start_line+199)
    return {'path':path,'content':safe_text(content[:24000]),'total_lines':len(lines),'start_line':start_line,'next_line':start_line+200 if start_line+199<len(lines) else None}

def system_info():
    script = "$ErrorActionPreference='Stop'; [ordered]@{cpu=@(Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors); memory_gb=[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB); gpu=@(Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion); audio=@(Get-CimInstance Win32_SoundDevice | Select-Object Name,Status); os=Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version} | ConvertTo-Json -Depth 4"
    executable=Path(os.environ.get('SystemRoot','C:/Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
    result=subprocess.run([str(executable),'-NoProfile','-NonInteractive','-Command',script],capture_output=True,text=True,timeout=25,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:
        raise ValueError('Windows hardware lookup failed or access was denied. No system changes were made.')
    return json.loads(result.stdout)

def run_tests(root):
    if not TEST_LOCK.acquire(False):
        raise ValueError('JARVIS tests are already running.')
    try:
        result=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(root),'-p','test_*.py'],cwd=root,capture_output=True,text=True,timeout=90,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        return {'status':'passed' if result.returncode==0 else 'failed','exit_code':result.returncode,
                'output':safe_text((result.stdout+'\n'+result.stderr)[-16000:]),
                'scope':'JARVIS Python tests; no microphone, visual or external API validation.'}
    except subprocess.TimeoutExpired:
        return {'status':'timed_out','output':'Test process exceeded 90 seconds and was stopped.'}
    finally:
        TEST_LOCK.release()

def open_page(url):
    parsed=urllib.parse.urlsplit(url)
    if len(url)>2000 or any(ord(c)<32 for c in url) or parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Provide a regular HTTP or HTTPS URL without embedded credentials.')
    if any(word in key.lower() for key,_ in urllib.parse.parse_qsl(parsed.query) for word in ('key','token','secret','password')):
        raise ValueError('Do not place credentials in browser URLs.')
    opened=webbrowser.open(url,new=2)
    return {'status':'requested' if opened else 'failed','url':url,'detail':'Requested opening in your default browser. Page loading and content were not verified.'}
