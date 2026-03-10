param(
    [int]$ApiPort = 8000,
    [switch]$NoNgrok
)

$ErrorActionPreference = 'Stop'

function Write-Section($text) {
    Write-Host "`n============================================================" -ForegroundColor DarkCyan
    Write-Host " $text" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor DarkCyan
}

function Write-Ok($text)   { Write-Host "[OK]  $text" -ForegroundColor Green }
function Write-Info($text) { Write-Host "[INFO] $text" -ForegroundColor Yellow }
function Write-WarnMsg($text) { Write-Host "[WARN] $text" -ForegroundColor Magenta }

function Get-ComposeCommand {
    try {
        docker compose version *> $null
        if ($LASTEXITCODE -eq 0) { return 'docker compose' }
    } catch { }

    try {
        docker-compose version *> $null
        if ($LASTEXITCODE -eq 0) { return 'docker-compose' }
    } catch { }

    throw 'Neither `docker compose` nor `docker-compose` is available.'
}

function Get-ListeningPid([int]$Port) {
    $line = netstat -ano 2>$null | Select-String (":$Port\s+.*LISTENING") | Select-Object -First 1
    if (-not $line) { return $null }
    $parts = ($line.ToString().Trim() -split '\s+')
    if ($parts.Count -gt 0) { return $parts[-1] }
    return $null
}

function Stop-PortProcess([int]$Port) {
    $procPid = Get-ListeningPid $Port
    if ($procPid -and $procPid -match '^\d+$') {
        Write-Info "Freeing port $Port (PID $procPid)..."
        try {
            Stop-Process -Id ([int]$procPid) -Force -ErrorAction Stop
            Start-Sleep -Seconds 1
            Write-Ok "Port $Port is free"
        } catch {
            Write-WarnMsg "Could not stop PID $procPid on port ${Port}: $($_.Exception.Message)"
        }
    }
}

function Start-Window($Title, $Command) {
    Start-Process powershell -ArgumentList @(
        '-NoExit',
        '-Command',
        "`$Host.UI.RawUI.WindowTitle = '$Title'; Set-Location '$PWD'; $Command"
    ) -WindowStyle Normal | Out-Null
}

Write-Section 'NovaDeskAI Demo Starter'

$compose = Get-ComposeCommand
Write-Ok "Using compose command: $compose"

Write-Section 'Starting Docker infrastructure'
Write-Info 'Starting: zookeeper, kafka, kafka-ui'
Invoke-Expression "$compose up -d zookeeper kafka kafka-ui"
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to start Docker infrastructure.'
}
Write-Ok 'Docker infrastructure started'

Write-Section 'Opening API window'
Stop-PortProcess -Port $ApiPort
Start-Window -Title 'NovaDeskAI API' -Command "python production/api/main.py"
Write-Ok "API window opened on port $ApiPort"

Write-Section 'Opening web form window'
Stop-PortProcess -Port 3000
Start-Window -Title 'NovaDeskAI Web Form' -Command "Set-Location '$PWD\web-form-nextjs'; npm run dev"
Write-Ok 'Web form window opened on port 3000'

if (-not $NoNgrok) {
    Write-Section 'Opening ngrok window'
    Stop-PortProcess -Port 4040
    Start-Window -Title 'ngrok Tunnel' -Command "ngrok http $ApiPort"
    Write-Ok 'ngrok window opened'
} else {
    Write-WarnMsg 'Skipping ngrok because -NoNgrok was supplied'
}

Write-Section 'Useful URLs'
Write-Host "Kafka UI        http://localhost:8080" -ForegroundColor Cyan
Write-Host "API             http://localhost:$ApiPort" -ForegroundColor Cyan
Write-Host "API Docs        http://localhost:$ApiPort/docs" -ForegroundColor Cyan
Write-Host "Web Form        http://localhost:3000" -ForegroundColor Cyan
Write-Host "ngrok Inspector http://localhost:4040" -ForegroundColor Cyan

Write-Host "`nNotes:" -ForegroundColor White
Write-Host "- This script starts Docker infra only (Kafka stack), not the API in Docker." -ForegroundColor Gray
Write-Host "- The API runs in its own PowerShell window: python production/api/main.py" -ForegroundColor Gray
Write-Host "- The web form runs in its own PowerShell window: cd web-form-nextjs; npm run dev" -ForegroundColor Gray
Write-Host "- ngrok runs in its own PowerShell window so you can copy the public URL." -ForegroundColor Gray
Write-Host "- If you do not want ngrok, run: .\demo.ps1 -NoNgrok" -ForegroundColor Gray

Write-Section 'Done'
