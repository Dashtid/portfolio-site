#!/bin/bash
# Database population script
# Run this AFTER database is attached

echo "=========================================="
echo "Portfolio Database Population Script"
echo "=========================================="
echo ""
echo "This will load your portfolio content into the database."
echo "Prerequisites: PostgreSQL must be attached (run fix-database.sh first)"
echo ""
echo "Press Enter to continue..."
read

echo ""
echo "[1/4] Connecting to backend..."
echo "Running data migration scripts..."
echo ""

flyctl ssh console -a dashti-portfolio-backend << 'EOF'
cd /app
echo "[+] Running migrate_real_content.py..."
python migrate_real_content.py
echo ""
echo "[+] Running populate_documents.py..."
python populate_documents.py
echo ""
echo "[+] Running populate_experience_details.py..."
python populate_experience_details.py
echo ""
echo "[OK] All migration scripts completed!"
exit
EOF

echo ""
echo "[2/4] Waiting for changes to sync..."
sleep 5

echo ""
echo "[3/4] Verifying data..."
echo ""
echo "Companies:"
curl -s https://dashti-portfolio-backend.fly.dev/api/v1/companies | python -m json.tool 2>/dev/null | grep -E '"name"|"title"' | head -14

echo ""
echo "Education:"
curl -s https://dashti-portfolio-backend.fly.dev/api/v1/education | python -m json.tool 2>/dev/null | grep -E '"institution"|"degree"' | head -8

echo ""
echo "Projects:"
curl -s https://dashti-portfolio-backend.fly.dev/api/v1/projects | python -m json.tool 2>/dev/null | grep -E '"name"|"description"' | head -16

echo ""
echo "[4/4] Summary:"
COMPANIES=$(curl -s https://dashti-portfolio-backend.fly.dev/api/v1/companies | python -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
EDUCATION=$(curl -s https://dashti-portfolio-backend.fly.dev/api/v1/education | python -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
PROJECTS=$(curl -s https://dashti-portfolio-backend.fly.dev/api/v1/projects | python -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)

echo "=========================================="
echo "Database Population Complete!"
echo "=========================================="
echo "  Companies: $COMPANIES (expected: 7)"
echo "  Education: $EDUCATION (expected: 4)"
echo "  Projects: $PROJECTS (expected: 8)"
echo ""
if [ "$COMPANIES" = "7" ] && [ "$EDUCATION" = "4" ]; then
    echo "  ✓ SUCCESS - Database fully populated!"
else
    echo "  ⚠ Warning - Some data may be missing. Check logs above."
fi
echo "=========================================="
