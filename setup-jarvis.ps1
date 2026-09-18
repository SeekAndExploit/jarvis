# One-time setup for JARVIS on Windows. Run from this folder:
#   Right-click > "Run with PowerShell"   (or: powershell -ExecutionPolicy Bypass -File setup-jarvis.ps1)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Have($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
}

Write-Host "`n== 1/6 Python 3.11+ ==" -ForegroundColor Cyan
$py = $null
if (Have "py") { try { & py -3 -c "import sys; assert sys.version_info >= (3,11)" 2>$null; if ($LASTEXITCODE -eq 0) { $py = "py -3" } } catch {} }
if (-not $py -and (Have "python")) { try { & python -c "import sys; assert sys.version_info >= (3,11)" 2>$null; if ($LASTEXITCODE -eq 0) { $py = "python" } } catch {} }
if (-not $py) {
  Write-Host "Installing Python 3.12 via winget..."
  winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
  Refresh-Path; $py = "py -3"
}
Write-Host "Using: $py"

Write-Host "`n== 2/6 Node.js 18+ ==" -ForegroundColor Cyan
if (-not (Have "node")) {
  Write-Host "Installing Node.js LTS via winget..."
  winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
  Refresh-Path
}
node --version

Write-Host "`n== 3/6 Claude Code ==" -ForegroundColor Cyan
if (-not (Have "claude")) {
  Write-Host "Installing Claude Code..."
  npm install -g @anthropic-ai/claude-code
  Refresh-Path
}
claude --version

Write-Host "`n== 4/6 Python packages (in .venv) ==" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) { Invoke-Expression "$py -m venv .venv" }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m playwright install chromium

Write-Host "`n== 5/6 Frontend packages ==" -ForegroundColor Cyan
Push-Location frontend; npm install; Pop-Location

Write-Host "`n== 6/6 .env ==" -ForegroundColor Cyan
if (-not (Test-Path ".env")) { Copy-Item .env.example .env }
$envText = Get-Content .env -Raw
if ($envText -match "FISH_API_KEY=your-fish-audio-api-key-here") {
  $key = Read-Host "Paste your Fish Audio API key (https://fish.audio) or press Enter to skip (text-only replies)"
  if ($key) { ($envText -replace "FISH_API_KEY=your-fish-audio-api-key-here", "FISH_API_KEY=$key") | Set-Content .env -NoNewline -Encoding utf8 }
}
$name = Read-Host "What should JARVIS call you? (Enter to skip)"
if ($name) { Add-Content .env "`nUSER_NAME=$name" -Encoding utf8 }

Write-Host "`nSetup done." -ForegroundColor Green
Write-Host "If you haven't logged into Claude Code yet, open a terminal, run:  claude   and log in, then exit it."
Write-Host "Then double-click start-jarvis.bat"
Read-Host "Press Enter to close"
