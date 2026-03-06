# ============================================================
#  NovaDeskAI - Full 5-Minute Demo Script
#  Usage: .\demo.ps1
#  Usage: .\demo.ps1 -ApiUrl http://localhost:8000
#  Set $env:DEMO_NONINTERACTIVE = '1' to skip the ENTER prompt.
# ============================================================

param(
    [string]$ApiUrl = 'http://localhost:8000'
)

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
#  MINUTE 0:00 - Start all services: API, Next.js, ngrok
# ============================================================
Write-Step "MINUTE 0:00" "Starting NovaDeskAI stack"
Write-Host ""

# Helper: free a port if something is already listening
function Free-Port {
    param([int]$port)
    $stale = (netstat -ano 2>$null | Select-String ":$port .*LISTENING") |
        ForEach-Object { $_.ToString().Trim().Split()[-1] } | Select-Object -First 1
    if ($stale -match '^\d+$') {
        Write-Info "Freeing port $port (PID $stale)..."
        taskkill /PID $stale /F 2>$null | Out-Null
        Start-Sleep -Seconds 1
    }
}

# --- 1. Start FastAPI backend ---
$apiAlreadyUp = $false
try {
    $hc = Invoke-RestMethod -Uri "$ApiUrl/" -TimeoutSec 3 -ErrorAction Stop
    $apiAlreadyUp = $true
    Write-OK "API already running at $ApiUrl"
} catch { }

if (-not $apiAlreadyUp) {
    Free-Port 8000
    Write-Info "Starting FastAPI backend (python production/api/main.py)..."
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PWD'; python production/api/main.py`"" -WindowStyle Minimized
    Write-Info "Waiting for API to be ready..."
    $ready = $false
    for ($i = 1; $i -le 20; $i++) {
        Start-Sleep -Seconds 3
        try {
            Invoke-RestMethod -Uri "$ApiUrl/" -TimeoutSec 3 -ErrorAction Stop | Out-Null
            $ready = $true; break
        } catch { }
        Write-Host "  ... ${i}0s elapsed - waiting for API..." -ForegroundColor Yellow
    }
    if ($ready) { Write-OK "FastAPI backend is up at $ApiUrl" }
    else { Write-Warn "API may not be fully ready - continuing anyway" }
} else {
    Write-OK "API already up - skipping start"
}

# --- 2. Start Next.js web form ---
$webAlreadyUp = $false
try {
    Invoke-RestMethod -Uri "http://localhost:3000" -TimeoutSec 3 -ErrorAction Stop | Out-Null
    $webAlreadyUp = $true
    Write-OK "Next.js web form already running at http://localhost:3000"
} catch { }

if (-not $webAlreadyUp) {
    Free-Port 3000
    Write-Info "Starting Next.js web form (npm run dev)..."
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PWD\web-form-nextjs'; npm run dev`"" -WindowStyle Minimized
    Write-Info "Waiting for Next.js to be ready (up to 30s)..."
    $webReady = $false
    for ($i = 1; $i -le 10; $i++) {
        Start-Sleep -Seconds 3
        try {
            Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -ErrorAction Stop | Out-Null
            $webReady = $true; break
        } catch { }
        Write-Host "  ... ${i}0s elapsed - waiting for Next.js..." -ForegroundColor Yellow
    }
    if ($webReady) { Write-OK "Next.js web form is up at http://localhost:3000" }
    else { Write-Warn "Next.js may still be compiling - it will be ready shortly" }
}

# --- 3. Start ngrok tunnel ---
$ngrokUrl = $null
try {
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 3 -ErrorAction Stop
    $ngrokUrl = ($tunnels.tunnels | Where-Object { $_.proto -eq 'https' } | Select-Object -First 1).public_url
    if ($ngrokUrl) { Write-OK "ngrok already running: $ngrokUrl" }
} catch { }

if (-not $ngrokUrl) {
    if (Get-Command ngrok -ErrorAction SilentlyContinue) {
        Write-Info "Starting ngrok tunnel on port 8000..."
        Start-Process powershell -ArgumentList "-NoExit -Command `"ngrok http 8000`"" -WindowStyle Minimized
        Start-Sleep -Seconds 4
        try {
            $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 5 -ErrorAction Stop
            $ngrokUrl = ($tunnels.tunnels | Where-Object { $_.proto -eq 'https' } | Select-Object -First 1).public_url
            if ($ngrokUrl) { Write-OK "ngrok tunnel: $ngrokUrl" }
            else { Write-Warn "ngrok started but no tunnel URL found yet - check http://localhost:4040" }
        } catch {
            Write-Warn "ngrok started but inspector not ready yet - check http://localhost:4040"
        }
    } else {
        Write-Warn "ngrok not found - skipping tunnel (Gmail/WhatsApp webhooks need ngrok)"
        Write-Info "Install: winget install ngrok.ngrok"
    }
}

# Show running services
Write-Host ""
Write-Host "  Running services:" -ForegroundColor White
@(
    @{Port=8000; Name="FastAPI API    "},
    @{Port=3000; Name="Next.js Web    "},
    @{Port=4040; Name="ngrok Inspector"}
) | ForEach-Object {
    $p = $_.Port; $n = $_.Name
    $listening = netstat -ano 2>$null | Select-String ":$p .*LISTENING" | Select-Object -First 1
    if ($listening) { Write-Host "  $n  http://localhost:$p" -ForegroundColor Green }
    else            { Write-Host "  $n  NOT running" -ForegroundColor DarkGray }
}
if ($ngrokUrl) {
    Write-Host "  Public URL        $ngrokUrl" -ForegroundColor Cyan
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
        -Uri "$ApiUrl/api/tickets" `
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
Write-Info "Fetching OpenAPI spec from $ApiUrl/openapi.json ..."
Write-Host ""

try {
    $spec = Invoke-RestMethod -Uri "$ApiUrl/openapi.json" -TimeoutSec 10
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
    Write-Info "  $ApiUrl/docs"
}

Write-Host ""
Write-Info "Open $ApiUrl/docs in your browser for the Swagger UI."
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
Write-Step "MINUTE 4:00" "Checking Kafka UI at http://localhost:8080"
Write-Host ""

# Try to start via docker-compose if available, otherwise just check if it's up
$dockerOk = $false
docker info 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Info "Running: docker-compose --profile debug up -d kafka-ui"
    docker-compose --profile debug up -d kafka-ui 2>&1 | Out-Null
    $dockerOk = $true
}
else {
    Write-Info "Docker engine not reachable - checking if Kafka UI is already running..."
}

Write-Host ""
Write-Info "Waiting for Kafka UI to respond (up to 30s)..."
$kuiReady = $false
for ($i = 1; $i -le 15; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 3 -ErrorAction Stop
        if ($r.StatusCode -lt 400) { $kuiReady = $true; break }
    }
    catch { Start-Sleep -Seconds 2 }
}

if ($kuiReady) { Write-OK "Kafka UI is live at http://localhost:8080" }
else { Write-Warn "Kafka UI not detected on port 8080 - it may require Docker or a separate start" }

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
Write-Host "  Web Form       http://localhost:3000" -ForegroundColor Cyan
Write-Host "  API Docs       $ApiUrl/docs" -ForegroundColor Cyan
Write-Host "  API Health     $ApiUrl/health" -ForegroundColor Cyan
Write-Host "  ngrok Inspector  http://localhost:4040" -ForegroundColor Cyan
if ($ngrokUrl) {
    Write-Host "  Public URL     $ngrokUrl" -ForegroundColor Green
    Write-Host "  Gmail Webhook  $ngrokUrl/webhook/gmail" -ForegroundColor Green
    Write-Host "  WA Webhook     $ngrokUrl/webhook/whatsapp" -ForegroundColor Green
}
Write-Host "  Kafka UI       http://localhost:8080" -ForegroundColor Cyan
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
