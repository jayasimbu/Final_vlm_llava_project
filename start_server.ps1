# VLM Invoice Server Startup Script for PowerShell
$env:PYTHONPATH = "."

Write-Host "Starting VLM Invoice Server..." -ForegroundColor Cyan
Write-Host "-------------------------------"

py -m uvicorn app.main:app --reload

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nERROR: Server failed to start." -ForegroundColor Red
    Write-Host "Check port 8000 usage or python dependencies."
}

Write-Host "-------------------------------"
Read-Host "Press Enter to exit"
