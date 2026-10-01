$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$python = Join-Path $root '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Create .venv before building.' }
& $python -B (Join-Path $root 'check_windows_setup.py')
if ($LASTEXITCODE -ne 0) { throw 'Build requires validated Windows Python 3.12 x64.' }
& $python -m pip install --disable-pip-version-check pyinstaller
& $python setup_wake.py
$dist = Join-Path $root 'release'
New-Item -ItemType Directory -Force -Path $dist | Out-Null
& $python -m PyInstaller --noconfirm --clean --onedir --name JARVIS `
  --distpath (Join-Path $dist 'app') --workpath (Join-Path $root 'build') --specpath (Join-Path $root 'build') `
  --add-data "$(Join-Path $root 'static');static" --add-data "$(Join-Path $root 'data/wake-models');data/wake-models" --add-data "$(Join-Path $root 'personality.txt');." --add-data "$(Join-Path $root '.env.example');." `
  --collect-all openwakeword --collect-all scipy --collect-all sklearn desktop_launcher.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed; no portable package was created.' }
$app = Join-Path $dist 'app/JARVIS'
New-Item -ItemType Directory -Force (Join-Path $app 'data') | Out-Null
Copy-Item (Join-Path $root 'README.md') $app
Copy-Item (Join-Path $root 'VOICE-AND-MEMORY.md') $app
Copy-Item (Join-Path $root 'API.md') $app
Compress-Archive -Path $app -DestinationPath (Join-Path $dist 'JARVIS-Windows-Portable.zip') -Force
Write-Host "Portable build created: $dist/JARVIS-Windows-Portable.zip"
