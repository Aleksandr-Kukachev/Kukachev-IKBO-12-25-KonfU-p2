# Run from any directory. Prefer installed Python, then Codex's bundled runtime.
$ErrorActionPreference = 'Stop'
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$pythonPath = if ($env:MAVENGRAPH_PYTHON) { $env:MAVENGRAPH_PYTHON } elseif ($pythonCommand -and $pythonCommand.Source -notlike '*Microsoft\WindowsApps*') { $pythonCommand.Source } else { $null }
if (-not $pythonPath) {
    $runtime = Get-ChildItem 'C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime*\dependencies\python\python.exe' -ErrorAction SilentlyContinue | Select-Object -Last 1
    if ($runtime) { $pythonPath = $runtime.FullName }
}
if (-not $pythonPath) {
    # Direct fallback for this desktop: WindowsApps directory enumeration can be restricted.
    $knownRuntime = 'C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1117-1425-0_26.1117.1425.0_x64__3k8sg7r9htsxt\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $knownRuntime) { $pythonPath = $knownRuntime }
}
if (-not $pythonPath) { throw 'Python 3.10+ не найден. Установите Python и запустите python -m mavengraph.' }
$env:PYTHONIOENCODING = 'utf-8'
Push-Location $PSScriptRoot
try {
    $bundledDot = Join-Path $PSScriptRoot '.tools\graphviz\Graphviz-16.1.1-win64\bin'
    $savedPath = $env:PATH
    if (Test-Path $bundledDot) { $env:PATH = "$bundledDot;$env:PATH" }
    & $pythonPath -m mavengraph @args
    $resultCode = $LASTEXITCODE
} finally {
    $env:PATH = $savedPath
    Pop-Location
}
exit $resultCode
