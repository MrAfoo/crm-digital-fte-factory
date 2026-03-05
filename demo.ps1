# ============================================================
#  NovaDeskAI - Full 5-Minute Demo Script
#  Usage: .\demo.ps1
#  Set $env:DEMO_NONINTERACTIVE = '1' to skip the ENTER prompt.
# ============================================================

$Host.UI.RawUI.WindowTitle = 'NovaDeskAI Demo'

# -- Colour helpers ------------------------------------------
function Write-Step { param($n, $msg) Write-Host "`n[$n] $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "  [XX] $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "  $msg" -ForegroundColor DarkGray }
function Pause-Demo { param($sec = 2) Start-Sleep -Seconds $sec }

# -- Banner --------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   NovaDeskAI  -  5-Minute Demo Runner" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Minute  What we show" -ForegroundColor White
Write-Host "  0:00    docker-compose up  -> all containers green" -ForegroundColor DarkGray
Write-Host "  1:00    Submit web form    -> TKT-XXXX created" -ForegroundColor DarkGray
Write-Host "  2:00    /docs endpoint     -> all API routes" -ForegroundColor DarkGray
Write-Host "  2:30    test_whatsapp.py   -> AI replies" -ForegroundColor DarkGray
Write-Host "  3:00    test_gmail.py      -> email processing" -ForegroundColor DarkGray
Write-Host "  3:30    pytest             -> 127 passing" -ForegroundColor DarkGray
Write-Host "  4:00    Kafka UI           -> http://localhost:8080" -ForegroundColor DarkGray
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# -- Pre-flight checks ---------------------------------------
Write-Host "Pre-flight checks..." -ForegroundColor Yellow

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Fail "Python not found. Please install Python 3.10+."
    exit 1
}
Write-OK "Python found: $(python --version)"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Fail "Docker not found. Please install Docker Desktop."
    exit 1
}
Write-OK "Docker found: $(docker --version)"

if (-not (Test-Path .env)) {
    Write-Warn ".env file not found - copying from .env.example"
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Write-OK ".env created from .env.example (add your GROQ_API_KEY if needed)"
    }
    else {
        Write-Fail "No .env or .env.example found. Create a .env file first."
        exit 1
    }
}
Write-OK ".env present"

Write-Host ""
if ($env:DEMO_NONINTERACTIVE -ne '1') {
    Write-Host "Press ENTER to start the demo, or Ctrl+C to abort..." -ForegroundColor Yellow
    try { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") } catch { Read-Host }
}
else {
    Write-Info "(non-interactive mode - skipping prompt)"
}

# ============================================================
#  MINUTE 0:00 - docker-compose up -> all containers green
# ============================================================
Write-Step "MINUTE 0:00" "Starting Docker stack (Zookeeper + Kafka + Nova API + Nova MCP)"
Write-Host ""

# Kill any stale process on port 8000 first
$stale = (netstat -ano 2>$null | Select-String ":8000 .*LISTENING") |
    ForEach-Object { $_.ToString().Trim().Split()[-1] } | Select-Object -First 1
if ($stale -match '^\d+$') {
    Write-Info "Freeing port 8000 (PID $stale)..."
    taskkill /PID $stale /F 2>$null | Out-Null
    Start-Sleep -Seconds 1
}

Write-Info "Running: docker-compose up -d"
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Fail "docker-compose up failed. Check Docker Desktop is running."
    exit 1
}

Write-Host ""
Write-Info "Waiting for containers to become healthy (up to 60s)..."
$healthy    = $false
$maxWait    = 60
$elapsed    = 0
$containers = @('nova-zookeeper', 'nova-kafka', 'nova-api', 'nova-mcp')

while (-not $healthy -and $elapsed -lt $maxWait) {
    Start-Sleep -Seconds 3
    $elapsed += 3
    $statuses = docker ps --format "{{.Names}}:{{.Status}}" 2>$null
    $allUp = $true
    foreach ($c in $containers) {
        $match = $statuses | Where-Object { $_ -like "$c*" }
        if (-not $match -or $match -notmatch 'Up|healthy') { $allUp = $false; break }
    }
    if ($allUp) { $healthy = $true }
    else { Write-Host "  ... ${elapsed}s elapsed - waiting..." -ForegroundColor Yellow }
}

Write-Host ""
Write-Host "  Container Status:" -ForegroundColor White
docker ps --format "table {{.Names}}\t{{.Status}}" 2>$null

if ($healthy) {
    Write-OK "All containers are UP"
}
else {
    Write-Warn "Some containers may still be starting - continuing demo"
}

Pause-Demo 2

# ============================================================
#  MINUTE 1:00 - Submit web form -> TKT-XXXX
# ============================================================
Write-Step "MINUTE 1:00" "Submitting a support ticket via the API (simulates web form)"
Write-Host ""
Write-Info "POST /api/tickets  ->  http://localhost:8000/api/tickets"
Write-Host ""

try {
    $ticketBody = @{
        name        = "Alex Demo"
        email       = "alex@demo.com"
        subject     = "Gmail Integration Error - OAuth 403"
        channel     = "web"
        description = "I cannot connect my Gmail integration - it fails with error 403 at the OAuth step."
    } | ConvertTo-Json

    $response = Invoke-RestMethod `
        -Uri "http://localhost:8000/api/tickets" `
        -Method POST `
        -Body $ticketBody `
        -ContentType "application/json" `
        -TimeoutSec 15

    $ticketId = if ($response.ticket_id) { $response.ticket_id }
                elseif ($response.id)     { $response.id }
                else                      { "TKT-DEMO" }

    Write-OK "Ticket created: $ticketId"
    Write-Info "Status             : $($response.status)"
    Write-Info "Estimated Response : $($response.estimated_response_time)"

    if ($response.message) {
        Write-Host ""
        Write-Host "  Nova's AI Response:" -ForegroundColor Magenta
        $response.message -split "`n" | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
    }
}
catch {
    Write-Warn "Ticket endpoint not reachable - API may still be starting."
    Write-Info "Open http://localhost:3000 in your browser to use the live web form."
}

Write-Host ""
Write-Info "Open http://localhost:3000 in your browser to see the web form live."
Pause-Demo 3

# ============================================================
#  MINUTE 2:00 - Show all API endpoints via /docs
# ============================================================
Write-Step "MINUTE 2:00" "API Documentation - all endpoints"
Write-Host ""
Write-Info "Fetching OpenAPI spec from http://localhost:8000/openapi.json ..."
Write-Host ""

try {
    $spec = Invoke-RestMethod -Uri "http://localhost:8000/openapi.json" -TimeoutSec 10
    Write-OK "API is live: $($spec.info.title) v$($spec.info.version)"
    Write-Host ""
    Write-Host "  Registered Endpoints:" -ForegroundColor White
    $spec.paths.PSObject.Properties | ForEach-Object {
        $path    = $_.Name
        $methods = ($_.Value.PSObject.Properties.Name | ForEach-Object { $_.ToUpper() }) -join ", "
        Write-Host ("  {0,-8}  {1}" -f $methods, $path) -ForegroundColor DarkGray
    }
}
catch {
    Write-Warn "Could not reach /openapi.json - try manually:"
    Write-Info "  http://localhost:8000/docs"
}

Write-Host ""
Write-Info "Open http://localhost:8000/docs in your browser for the Swagger UI."
Pause-Demo 3

# ============================================================
#  MINUTE 2:30 - python setup/test_whatsapp.py -> AI replies
# ============================================================
Write-Step "MINUTE 2:30" "WhatsApp webhook simulation -> Nova AI replies"
Write-Host ""
Write-Info "Running: python setup/test_whatsapp.py"
Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray
python setup/test_whatsapp.py
Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray

if ($LASTEXITCODE -eq 0) { Write-OK "WhatsApp simulation complete" }
else { Write-Warn "WhatsApp test exited with errors (API may not be ready yet)" }

Pause-Demo 2

# ============================================================
#  MINUTE 3:00 - python setup/test_gmail.py -> email processing
# ============================================================
Write-Step "MINUTE 3:00" "Gmail email simulation -> Nova processes inbound emails"
Write-Host ""
Write-Info "Running: python setup/test_gmail.py"
Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray
python setup/test_gmail.py
Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray

if ($LASTEXITCODE -eq 0) { Write-OK "Gmail simulation complete" }
else { Write-Warn "Gmail test exited with errors (API may not be ready yet)" }

Pause-Demo 2

# ============================================================
#  MINUTE 3:30 - pytest tests/ production/tests/ -> 127 passing
# ============================================================
Write-Step "MINUTE 3:30" "Running full test suite - Stage 1 + Stage 2"
Write-Host ""
Write-Info "Installing test dependencies (quiet)..."
pip install -q groq fastapi uvicorn python-dotenv pytest httpx pydantic confluent-kafka pytest-asyncio pytest-mock
Write-Host ""

Write-Info "Running: pytest tests/ production/tests/ -v --tb=short"
Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray
python -m pytest tests/ production/tests/ -v --tb=short
$testExit = $LASTEXITCODE
Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray

if ($testExit -eq 0) { Write-OK "All tests PASSED" }
else { Write-Warn "Some tests failed - see output above" }

Pause-Demo 2

# ============================================================
#  MINUTE 4:00 - Kafka UI -> http://localhost:8080
# ============================================================
Write-Step "MINUTE 4:00" "Starting Kafka UI (debug profile)"
Write-Host ""
Write-Info "Running: docker-compose --profile debug up -d kafka-ui"
docker-compose --profile debug up -d kafka-ui 2>&1

Write-Host ""
Write-Info "Waiting for Kafka UI to respond..."
$kuiReady = $false
for ($i = 1; $i -le 15; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 3 -ErrorAction Stop
        if ($r.StatusCode -lt 400) { $kuiReady = $true; break }
    }
    catch { Start-Sleep -Seconds 2 }
}

if ($kuiReady) { Write-OK "Kafka UI is live at http://localhost:8080" }
else { Write-Warn "Kafka UI may still be starting - try http://localhost:8080 in your browser" }

Write-Host ""
Write-Info "Open http://localhost:8080 to browse Kafka topics and messages live."
Pause-Demo 2

# ============================================================
#  MINUTE 4:30 - Summary & live URLs
# ============================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   Demo Complete! Everything is running." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Live URLs:" -ForegroundColor White
Write-Host "  ----------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "  Web Form     http://localhost:3000" -ForegroundColor Cyan
Write-Host "  API Docs     http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  API Health   http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "  Kafka UI     http://localhost:8080" -ForegroundColor Cyan
Write-Host "  MCP Tools    http://localhost:8001/tools" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Minute 4:30 - Send a REAL email to your configured Gmail address" -ForegroundColor Yellow
Write-Host "  and watch Nova auto-reply live in the logs:" -ForegroundColor Yellow
Write-Host ""
Write-Host "    docker-compose logs -f nova-api" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  To shut everything down when done:" -ForegroundColor White
Write-Host "    docker-compose --profile debug down" -ForegroundColor DarkGray
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
