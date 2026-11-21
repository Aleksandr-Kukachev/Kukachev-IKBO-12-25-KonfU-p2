# Запуск приложения из любой папки.
$ErrorActionPreference = 'Stop'
$pythonPath = $env:MAVENGRAPH_PYTHON
$pythonArgs = @()
$localConfig = Join-Path $PSScriptRoot '.local\python.txt'
if (-not $pythonPath -and (Test-Path -LiteralPath $localConfig)) {
    $pythonPath = (Get-Content -LiteralPath $localConfig -Raw).Trim()
}
if (-not $pythonPath) {
    foreach ($name in @('python', 'py')) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command -and $command.Source -notlike '*Microsoft\WindowsApps*') {
            $pythonPath = $command.Source
            if ($name -eq 'py') { $pythonArgs = @('-3') }
            break
        }
    }
}
if (-not $pythonPath) { throw 'Python не найден. Установите Python 3.10+ или задайте путь в MAVENGRAPH_PYTHON.' }
$savedPath = $env:PATH
$savedPythonPath = $env:PYTHONPATH
$savedEncoding = $env:PYTHONIOENCODING
Push-Location $PSScriptRoot
try {
    $env:PYTHONPATH = (Join-Path $PSScriptRoot 'src') + [IO.Path]::PathSeparator + $savedPythonPath
    $env:PYTHONIOENCODING = 'utf-8'
    $localDot = Get-ChildItem (Join-Path $PSScriptRoot '.tools\graphviz\*\bin\dot.exe') -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($localDot) { $env:PATH = "$($localDot.DirectoryName);$env:PATH" }
    & $pythonPath @pythonArgs -m mavengraph @args
    $resultCode = $LASTEXITCODE
} finally {
    $env:PYTHONPATH = $savedPythonPath
    $env:PATH = $savedPath
    $env:PYTHONIOENCODING = $savedEncoding
    Pop-Location
}
exit $resultCode
