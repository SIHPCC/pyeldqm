Param(
    [switch]$SmokeTest = $false,
    [int]$Port = 8065
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Python executable not found: $pythonExe"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$workPath = Join-Path $repoRoot ("build_exe\" + $stamp)
$distPath = Join-Path $repoRoot ("dist_exe\" + $stamp)

New-Item -ItemType Directory -Force -Path $workPath | Out-Null
New-Item -ItemType Directory -Force -Path $distPath | Out-Null

Write-Host "[build] workPath: $workPath"
Write-Host "[build] distPath: $distPath"

& $pythonExe -m PyInstaller --clean --noconfirm --workpath $workPath --distpath $distPath pyELDQM.spec

$exePath = Join-Path $distPath "pyELDQM.exe"
if (-not (Test-Path $exePath)) {
    throw "Build finished but executable not found at $exePath"
}

Write-Host "[build] executable: $exePath"

if ($SmokeTest) {
    Write-Host "[smoke] launching executable on port $Port"
    $env:AUTO_OPEN_BROWSER = "false"
    $env:DEBUG = "false"
    $env:PORT = "$Port"

    $proc = Start-Process -FilePath $exePath -PassThru
    Start-Sleep -Seconds 8

    $listening = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($listening) {
        Write-Host "[smoke] PASS: server listening on http://localhost:$Port"
    }
    else {
        Write-Warning "[smoke] FAIL: no listener on port $Port (check console logs)."
    }

    if (-not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force
    }
}
