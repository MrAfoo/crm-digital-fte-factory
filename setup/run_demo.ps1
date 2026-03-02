# NovaDeskAI Demo Runner - PowerShell Script
# Kills existing process on port 8000, starts API, runs automated demo
# Usage: .\setup\run_demo.ps1

param(
    [switch]$KeepRunning = $false,
    [int]$Port = 8000
)

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Accent { Write-Host $args -ForegroundColor Magenta }

# Header
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                            ║" -ForegroundColor Cyan
Write-Host "║         🚀 NovaDeskAI Demo Runner (PowerShell) 🚀          ║" -ForegroundColor Cyan
Write-Host "║                                                            ║" -ForegroundColor Cyan
Write-Host "║              Customer Success Agent Live Demo              ║" -ForegroundColor Cyan
Write-Host "║                                                            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 1: Kill existing process on port 8000
Write-Info "🔍 Step 1: Checking for existing process on port $Port..."
$existingProcess = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($existingProcess) {
    $processId = $existingProcess.OwningProcess
    Write-Warning "  Found process $processId using port $Port, killing..."
    try {
        Stop-Process -Id $processId -Force -ErrorAction Stop
        Write-Success "  ✓ Killed process $processId"
        Start-Sleep -Seconds 1
    }
    catch {
        Write-Error "  ✗ Failed to kill process: $_"
        exit 1
    }
}
else {
    Write-Success "  ✓ Port $Port is free"
}

Write-Host ""

# Step 2: Start API in background
Write-Info "🚀 Step 2: Starting NovaDeskAI API..."
Write-Host "  Command: python production/api/main.py"

$apiProcess = Start-Process -FilePath "python" `
    -ArgumentList "production/api/main.py" `
    -NoNewWindow `
    -PassThru `
    -ErrorAction Stop

Write-Success "  ✓ API process started (PID: $($apiProcess.Id))"
Write-Host ""

# Step 3: Wait for API to be ready
Write-Info "⏳ Step 3: Waiting for API to be ready..."
$maxAttempts = 30
$attempt = 0
$apiReady = $false

while ($attempt -lt $maxAttempts -and -not $apiReady) {
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Port/api/health" `
            -Method Get `
            -TimeoutSec 2 `
            -ErrorAction SilentlyContinue
        
        if ($response.StatusCode -eq 200) {
            $apiReady = $true
            Write-Success "  ✓ API is ready and responding"
        }
    }
    catch {
        # Still waiting
        Write-Host "  ⏳ Waiting... (attempt $attempt/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 1
    }
}

if (-not $apiReady) {
    Write-Error "  ✗ API did not respond after $maxAttempts seconds"
    Write-Error "  Check if there are any errors in the API startup"
    Stop-Process -Id $apiProcess.Id -Force
    exit 1
}

Write-Host ""

# Step 4: Run demo runner
Write-Info "🎬 Step 4: Running automated demo..."
Write-Host ""

try {
    python setup/demo_runner.py
    $demoSuccess = $?
}
catch {
    Write-Error "Demo failed: $_"
    $demoSuccess = $false
}

Write-Host ""

# Step 5: Show status
if ($demoSuccess) {
    Write-Success "✅ Demo completed successfully!"
}
else {
    Write-Error "⚠️  Demo encountered errors (see above)"
}

Write-Host ""

# Step 6: Handle process cleanup
if ($KeepRunning) {
    Write-Warning "API is still running in background (PID: $($apiProcess.Id))"
    Write-Info "To stop it, run: Stop-Process -Id $($apiProcess.Id) -Force"
    Write-Host ""
    Write-Info "Open these URLs to explore:"
    Write-Host "  • Health:  http://localhost:$Port/api/health" -ForegroundColor DarkGray
    Write-Host "  • Tickets: http://localhost:$Port/api/tickets" -ForegroundColor DarkGray
    Write-Host "  • Stats:   http://localhost:$Port/api/stats" -ForegroundColor DarkGray
    Write-Host "  • Web Form: http://localhost:$Port/web-form/" -ForegroundColor DarkGray
    Write-Host ""
    Write-Warning "Press Ctrl+C to stop the API when done"
    
    # Keep the console open
    Wait-Process -Id $apiProcess.Id
}
else {
    Write-Info "Stopping API..."
    Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
    Write-Success "✓ API stopped"
    Write-Host ""
    Write-Info "To keep the API running for manual testing, use:"
    Write-Host "  .\setup\run_demo.ps1 -KeepRunning" -ForegroundColor DarkGray
    Write-Host ""
}

Write-Host "═══════════════════════════════════════════════════════════"
Write-Host ""
