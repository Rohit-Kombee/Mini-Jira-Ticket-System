# Generate traces and verify they reach Tempo.
# Run with: .\scripts\generate-and-verify-traces.ps1
# Prereqs: Docker stack running (docker compose up -d), backend on localhost:8000, Tempo on localhost:3200

$ErrorActionPreference = "Stop"
$BackendUrl = "http://localhost:8000"
$TempoUrl = "http://localhost:3200"

Write-Host "=== 1. Generate API traffic (traces) ===" -ForegroundColor Cyan
# Health (no auth)
Invoke-RestMethod -Uri "$BackendUrl/health" -Method Get | Out-Null
# Login to get token
$loginBody = @{ email = "admin"; password = "admin" } | ConvertTo-Json
$loginResp = Invoke-RestMethod -Uri "$BackendUrl/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
$token = $loginResp.access_token
$headers = @{ Authorization = "Bearer $token" }
# List tickets (creates spans)
Invoke-RestMethod -Uri "$BackendUrl/tickets" -Method Get -Headers $headers | Out-Null
Write-Host "  Sent requests to backend. Waiting 20s for spans to flush to Tempo..." -ForegroundColor Gray
Start-Sleep -Seconds 20

Write-Host "`n=== 2. Query Tempo search API ===" -ForegroundColor Cyan
try {
    $searchUrl = "$TempoUrl/api/search?q=%7B%20resource.service.name%3D%22support-ticket-api%22%20%7D&limit=5"
    $response = Invoke-RestMethod -Uri $searchUrl -Method Get
    $traces = $response.traces
    if ($traces -and $traces.Count -gt 0) {
        Write-Host "  OK: Tempo returned $($traces.Count) trace(s). Pipeline is working." -ForegroundColor Green
        $traces | ForEach-Object { Write-Host "    - TraceID: $($_.traceID)" }
    } else {
        Write-Host "  No traces in response. Check: (1) backend logs for 'tracing_initialized', (2) otel-collector logs, (3) Tempo logs." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Error calling Tempo: $_" -ForegroundColor Red
    Write-Host "  Ensure Tempo is up: docker compose ps tempo" -ForegroundColor Gray
}

Write-Host "`n=== 3. In Grafana ===" -ForegroundColor Cyan
Write-Host "  Set time range to 'Last 15 minutes' or 'Last 6 hours', then open dashboard 'Distributed Traces (Tempo)' or use 'View traces in Explore' link." -ForegroundColor Gray
