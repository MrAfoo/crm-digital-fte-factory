# ============================================================
#  NovaDeskAI - One-Click Startup Script (Stage 1 + Stage 2)
#  Usage: .\start.ps1
# ============================================================

$Host.UI.RawUI.WindowTitle = 'NovaDeskAI Stack'

Write-Host ''
Write-Host '===============================================================' -ForegroundColor Cyan
Write-Host '   NovaDeskAI Customer Success Agent' -ForegroundColor Cyan
Write-Host '===============================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host '  Select mode:' -ForegroundColor White
Write-Host '  [1] Stage 1 - Prototype (no external dependencies)' -ForegroundColor Green
Write-Host '  [2] Stage 2 - Production (PostgreSQL + Kafka + full stack)' -ForegroundColor Yellow
Write-Host '  [3] Run Tests only' -ForegroundColor Cyan
Write-Host '  [4] Run Live Agent Demo (Groq API)' -ForegroundColor Magenta
Write-Host ''
$choice = Read-Host 'Enter choice (1/2/3/4)'

# Always kill stale port 8000 process before starting
$stale = (netstat -ano | Select-String ":8000 .*LISTENING").ToString().Trim().Split()[-1]
if ($stale -match '^\d+$') {
    Write-Host "  Freeing port 8000 (PID $stale)..." -ForegroundColor DarkGray
    taskkill /PID $stale /F 2>$null | Out-Null
    Start-Sleep -Seconds 1
}

# ── Check Python ────────────────────────────────────────────
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python not found. Please install Python 3.10+." -ForegroundColor Red
    exit 1
}

# ──────────────────────────────────────────────────────────────
# CHOICE 1: Stage 1 Prototype
# ──────────────────────────────────────────────────────────────
if ($choice -eq '1') {
    Write-Host ""
    Write-Host "========== STAGE 1: PROTOTYPE ==========" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "[1/5] Installing Stage 1 dependencies..." -ForegroundColor Yellow
    try {
        pip install -q -r src/agent/requirements.txt
        Write-Host "      Done." -ForegroundColor Green
    } catch {
        Write-Host "      Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
    
    Write-Host "[2/5] Running Stage 1 tests..." -ForegroundColor Yellow
    python -m pytest tests/ -q --tb=short
    Write-Host ""
    
    Write-Host "[3/5] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Yellow
    $api = Start-Process -FilePath "python" `
        -ArgumentList "src/api/main.py" `
        -PassThru -WindowStyle Minimized
    Write-Host "      PID $($api.Id) - Backend running." -ForegroundColor Green
    Start-Sleep -Seconds 2
    Write-Host ""
    
    Write-Host "[4/5] Starting MCP Tool Server on http://localhost:8001..." -ForegroundColor Yellow
    $mcp = Start-Process -FilePath "python" `
        -ArgumentList "src/agent/mcp_server.py" `
        -PassThru -WindowStyle Minimized
    Write-Host "      PID $($mcp.Id) - MCP Server running." -ForegroundColor Green
    Start-Sleep -Seconds 2
    Write-Host ""
    
    Write-Host "[5/5] Running live agent demo..." -ForegroundColor Yellow
    Write-Host ""
    python src/agent/prototype.py
    Write-Host ""
    
    Write-Host "===============================================================" -ForegroundColor Cyan
    Write-Host "   Stage 1 Services Running" -ForegroundColor Green
    Write-Host "===============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Service         URL" -ForegroundColor White
    Write-Host "  --------------- ------------------------------------" -ForegroundColor DarkGray
    Write-Host "  FastAPI Backend  http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  MCP Tools List   http://localhost:8001/tools" -ForegroundColor White
    Write-Host "  Web Form         Open src/web-form/index.html in browser" -ForegroundColor White
    Write-Host ""
    Write-Host "  Press ENTER to shut down all services and exit." -ForegroundColor Yellow
    Write-Host ""
    
    try { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") } catch { Start-Sleep -Seconds 9999 }
    
    Write-Host ""
    Write-Host "Shutting down services..." -ForegroundColor Yellow
    Stop-Process -Id $api.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $mcp.Id -Force -ErrorAction SilentlyContinue
    Write-Host "All services stopped. Goodbye!" -ForegroundColor Green
    Write-Host ""
}

# ──────────────────────────────────────────────────────────────
# CHOICE 2: Stage 2 Production
# ──────────────────────────────────────────────────────────────
elseif ($choice -eq '2') {
    Write-Host ""
    Write-Host "========== STAGE 2: PRODUCTION ==========" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "[1/4] Installing Stage 2 dependencies..." -ForegroundColor Yellow
    try {
        pip install -q -r production/k8s/requirements.txt
        Write-Host "      Done." -ForegroundColor Green
    } catch {
        Write-Host "      Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
    
    Write-Host "[2/4] Running Stage 2 tests..." -ForegroundColor Yellow
    python -m pytest production/tests/ -q --tb=short
    Write-Host ""
    
    Write-Host "[3/4] Starting Production API on http://localhost:8000..." -ForegroundColor Yellow
    $api = Start-Process -FilePath "python" `
        -ArgumentList "production/api/main.py" `
        -PassThru -WindowStyle Minimized
    Write-Host "      PID $($api.Id) - API running." -ForegroundColor Green
    Start-Sleep -Seconds 3
    Write-Host ""
    
    Write-Host "[4/4] Configuration complete!" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "===============================================================" -ForegroundColor Cyan
    Write-Host "   Stage 2 Production API Running" -ForegroundColor Yellow
    Write-Host "===============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Service              URL" -ForegroundColor White
    Write-Host "  -------------------- ------------------------------------" -ForegroundColor DarkGray
    Write-Host "  API Health           http://localhost:8000/health" -ForegroundColor White
    Write-Host "  API Docs             http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  API Stats            http://localhost:8000/api/stats" -ForegroundColor White
    Write-Host "  API Tickets          http://localhost:8000/api/tickets" -ForegroundColor White
    Write-Host "  API Metrics          http://localhost:8000/api/metrics" -ForegroundColor White
    Write-Host ""
    Write-Host "  For full stack with PostgreSQL + Kafka, run:" -ForegroundColor Cyan
    Write-Host "  docker-compose -f production/k8s/docker-compose.yml up" -ForegroundColor White
    Write-Host ""
    Write-Host "  Press ENTER to shut down the API and exit." -ForegroundColor Yellow
    Write-Host ""
    
    try { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") } catch { Start-Sleep -Seconds 9999 }
    
    Write-Host ""
    Write-Host "Shutting down services..." -ForegroundColor Yellow
    Stop-Process -Id $api.Id -Force -ErrorAction SilentlyContinue
    Write-Host "API stopped. Goodbye!" -ForegroundColor Green
    Write-Host ""
}

# ──────────────────────────────────────────────────────────────
# CHOICE 3: Run Tests Only
# ──────────────────────────────────────────────────────────────
elseif ($choice -eq '3') {
    Write-Host ""
    Write-Host "========== RUNNING ALL TESTS ==========" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "[1/2] Installing dependencies..." -ForegroundColor Yellow
    try {
        pip install -q groq fastapi uvicorn python-dotenv pytest httpx pydantic confluent-kafka pytest-asyncio pytest-mock
        Write-Host "      Done." -ForegroundColor Green
    } catch {
        Write-Host "      Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
    
    Write-Host "[2/2] Running all tests (Stage 1 + Stage 2)..." -ForegroundColor Yellow
    Write-Host ""
    python -m pytest tests/ production/tests/ -v --tb=short
    
    Write-Host ""
    Write-Host "Test run complete!" -ForegroundColor Green
    Write-Host ""
}

# ──────────────────────────────────────────────────────────────
# CHOICE 4: Live Agent Demo (Groq API)
# ──────────────────────────────────────────────────────────────
elseif ($choice -eq '4') {
    Write-Host ""
    Write-Host "========== LIVE AGENT DEMO (GROQ API) ==========" -ForegroundColor Magenta
    Write-Host ""
    
    # Check for GROQ_API_KEY
    if (-not (Test-Path .env)) {
        Write-Host "[ERROR] .env file not found!" -ForegroundColor Red
        Write-Host "        Create .env with: GROQ_API_KEY=your_key_here" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "[1/2] Installing dependencies..." -ForegroundColor Yellow
    try {
        pip install -q groq python-dotenv pytest-asyncio
        Write-Host "      Done." -ForegroundColor Green
    } catch {
        Write-Host "      Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
    
    Write-Host "[2/2] Starting live agent demo..." -ForegroundColor Yellow
    Write-Host ""
    
    python production/agent/customer_success_agent.py
    
    Write-Host ""
    Write-Host "Demo complete!" -ForegroundColor Green
    Write-Host ""
}

# ──────────────────────────────────────────────────────────────
# Invalid Choice
# ──────────────────────────────────────────────────────────────
else {
    Write-Host "[ERROR] Invalid choice. Please select 1, 2, 3, or 4." -ForegroundColor Red
    exit 1
}
