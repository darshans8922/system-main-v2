# PowerShell script to set DATABASE_URL for local testing
# Run this before using test scripts: .\setup_env.ps1

$DATABASE_URL = "postgresql://postgres.oahhrydngdyilxjdwhqt:XUJ-XUJ-XUJ@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

Write-Host "Setting DATABASE_URL environment variable for this session..." -ForegroundColor Green
$env:DATABASE_URL = $DATABASE_URL

Write-Host "DATABASE_URL is now set!" -ForegroundColor Green
Write-Host "To make it permanent, add it to your system environment variables or create a .env file" -ForegroundColor Yellow
Write-Host ""
Write-Host "To test, run: python test_sse_helper.py verify bharat" -ForegroundColor Cyan

