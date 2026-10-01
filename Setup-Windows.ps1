param([switch]$LocalVoice, [switch]$Tests, [switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$setupPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$setupProbe = Join-Path $PSScriptRoot 'check_windows_setup.py'
$probeArgs = @()
if ($LocalVoice) { $probeArgs += '--local-voice' }
if ($Tests) { $probeArgs += '--tests' }
if (Test-Path -LiteralPath $setupPython) {
    & $setupPython -B $setupProbe @probeArgs
} else {
    # Explicit version selection; never fall back to developer-bundled Python.
    & py -3.12 -B $setupProbe @probeArgs
}
if ($LASTEXITCODE -ne 0) { throw 'Prerequisites failed. No installation attempted.' }
if ($CheckOnly) { return }
if (-not (Test-Path -LiteralPath $setupPython)) {
    & py -3.12 -m venv (Join-Path $PSScriptRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}
$setupRequirements = @('requirements.txt')
if ($LocalVoice) { $setupRequirements += 'requirements-local-voice.txt' }
if ($Tests) { $setupRequirements += 'requirements-test.txt' }
foreach ($requirement in $setupRequirements) {
    & $setupPython -m pip install --disable-pip-version-check -r (Join-Path $PSScriptRoot $requirement)
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed: $requirement" }
}
& $setupPython -B $setupProbe @probeArgs --installed
if ($LASTEXITCODE -ne 0) { throw 'Installed dependency verification failed.' }
Write-Output 'Setup verified. No Core started; credentials and model data remain external.'
