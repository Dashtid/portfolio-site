#!/bin/bash
# Database connection fix script
# Run this to attach PostgreSQL to the backend

echo "=========================================="
echo "Portfolio Database Fix Script"
echo "=========================================="
echo ""
echo "This will connect PostgreSQL to your backend."
echo "You'll be prompted to confirm - type 'y' and press Enter."
echo ""
echo "Press Enter to continue..."
read

echo ""
echo "[1/3] Attaching PostgreSQL database..."
flyctl postgres attach dashti-portfolio-db -a dashti-portfolio-backend

echo ""
echo "[2/3] Waiting 30 seconds for backend to restart..."
sleep 30

echo ""
echo "[3/3] Verifying connection..."
flyctl ssh console -a dashti-portfolio-backend -C 'python -c "from app.config import settings; print(settings.async_database_url)"'

echo ""
echo "=========================================="
echo "Check the output above:"
echo "  ✓ If you see 'postgresql+asyncpg://' - SUCCESS!"
echo "  ✗ If you see 'sqlite+aiosqlite://' - Run: flyctl apps restart dashti-portfolio-backend"
echo "=========================================="
