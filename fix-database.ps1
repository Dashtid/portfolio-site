# Database connection fix script (PowerShell)
# Run this to attach PostgreSQL to the backend

Write-Host "=========================================="
Write-Host "Portfolio Database Fix Script"
Write-Host "=========================================="
Write-Host ""
Write-Host "This will connect PostgreSQL to your backend."
Write-Host "You'll be prompted to confirm - type 'y' and press Enter."
Write-Host ""
Write-Host "Press Enter to continue..."
Read-Host

Write-Host ""
Write-Host "[1/3] Attaching PostgreSQL database..."
flyctl postgres attach dashti-portfolio-db -a dashti-portfolio-backend

Write-Host ""
Write-Host "[2/3] Waiting 30 seconds for backend to restart..."
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "[3/3] Verifying connection..."
flyctl ssh console -a dashti-portfolio-backend -C 'python -c "from app.config import settings; print(settings.async_database_url)"'

Write-Host ""
Write-Host "=========================================="
Write-Host "Check the output above:"
Write-Host "  [OK] If you see 'postgresql+asyncpg://' - SUCCESS!"
Write-Host "  [X] If you see 'sqlite+aiosqlite://' - Run: flyctl apps restart dashti-portfolio-backend"
Write-Host "=========================================="
