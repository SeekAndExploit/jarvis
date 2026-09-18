# One-time setup for JARVIS on Windows. Run from this folder:
#   Right-click > "Run with PowerShell"   (or: powershell -ExecutionPolicy Bypass -File setup-jarvis.ps1)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Have($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
}
function Add-UserPath($dir) {
  $user = [Environment]::GetEnvironmentVariable("Path","User")
  if (-not ($user -split ";" | Where-Object { $_ -eq $dir })) {
    [Environment]::SetEnvironmentVariable("Path", ($user.TrimEnd(";") + ";" + $dir), "User")
  }
  Refresh-Path
}
function Need($what, $url) {
  Write-Host "`n$what is missing. Install it from:" -ForegroundColor Yellow
  Write-Host "  $url"
  Write-Host "then open a NEW PowerShell window and run this script again."
  Read-Host "Press Enter to close"; exit 1
}

Write-Host "`n== 1/6 Python 3.11+ ==" -ForegroundColor Cyan
$py = $null
foreach ($c in @("py -3", "python")) {
  try { Invoke-Expression "$c -c `"import sys; assert sys.version_info >= (3,11)`"" 2>$null; if ($LASTEXITCODE -eq 0) { $py = $c; break } } catch {}
}
if (-not $py) {
  if (Have "winget") { winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements; Refresh-Path; $py = "py -3" }
  else { Need "Python 3.11+" "https://www.python.org/downloads/windows/  (tick 'Add python.exe to PATH')" }
}
Write-Host "Using: $py"

Write-Host "`n== 2/6 Node.js 18+ ==" -ForegroundColor Cyan
if (-not (Have "node")) {
  if (Have "winget") { winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements; Refresh-Path }
  else { Need "Node.js" "https://nodejs.org/  (LTS)" }
}
node --version

Write-Host "`n== 3/6 Claude Code ==" -ForegroundColor Cyan
$localBin = Join-Path $env:USERPROFILE ".local\bin"
if (Test-Path (Join-Path $localBin "claude.exe")) { Add-UserPath $localBin }
if (-not (Have "claude")) {
  Write-Host "Installing Claude Code (official installer)..."
  Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
  Add-UserPath $localBin
}
claude --version

Write-Host "`n== 4/6 Python packages (in .venv) ==" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) { Invoke-Expression "$py -m venv .venv" }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt edge-tts cryptography
& .\.venv\Scripts\python.exe -m playwright install chromium

Write-Host "`n== 5/6 Frontend packages ==" -ForegroundColor Cyan
Push-Location frontend; npm install; Pop-Location

Write-Host "`n== 6/6 .env and certificate ==" -ForegroundColor Cyan
if (-not (Test-Path ".env")) { Copy-Item .env.example .env }
$envText = Get-Content .env -Raw
if ($envText -match "FISH_API_KEY=your-fish-audio-api-key-here") {
  $key = Read-Host "Fish Audio API key (Enter to skip and use the free Edge voice)"
  if ($key) { $envText = $envText -replace "FISH_API_KEY=your-fish-audio-api-key-here", "FISH_API_KEY=$key" }
  else { $envText += "`nTTS_ENGINE=edge`n" }
  [IO.File]::WriteAllText((Join-Path $PSScriptRoot ".env"), $envText)
}
if (-not ((Test-Path "cert.pem") -and (Test-Path "key.pem"))) {
  & .\.venv\Scripts\python.exe scripts\make_cert.py
}

Write-Host "`nSetup done." -ForegroundColor Green
Write-Host "1. If Claude Code isn't logged in yet: open a NEW PowerShell, run  claude  and log in, then /exit"
Write-Host "2. Double-click start-jarvis.bat"
Write-Host "Optional check:  .venv\Scripts\python windows_selftest.py"
Read-Host "Press Enter to close"
