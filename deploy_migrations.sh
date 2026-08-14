#!/bin/bash
# Deployment script for production server migrations
# Run this on your production server at api.iqraamark.com

set -e  # Exit on any error

echo "=========================================="
echo "Production Migration Deployment Script"
echo "=========================================="
echo ""

# Configuration
PROJECT_DIR="/var/www/house-of-vaz/house-of-vaz-backend-system"
VENV_PATH="$PROJECT_DIR/venv"
BACKUP_DIR="$PROJECT_DIR/backups"

# Navigate to project directory
cd "$PROJECT_DIR"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup database
BACKUP_FILE="$BACKUP_DIR/db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)"
echo "1. Creating database backup..."
cp db.sqlite3 "$BACKUP_FILE"
echo "   ✓ Backup created: $BACKUP_FILE"
echo ""

# Activate virtual environment
echo "2. Activating virtual environment..."
source "$VENV_PATH/bin/activate"
echo "   ✓ Virtual environment activated"
echo ""

# Pull latest code (if using git)
echo "3. Pulling latest code from repository..."
git pull origin main || echo "   ⚠ Git pull failed or not using git - continuing..."
echo ""

# Show pending migrations
echo "4. Checking pending migrations..."
python manage.py showmigrations products
echo ""

# Run migrations
echo "5. Running product migrations..."
python manage.py migrate products
echo "   ✓ Migrations applied successfully"
echo ""

# Restart gunicorn
echo "6. Restarting gunicorn service..."
sudo systemctl restart gunicorn
echo "   ✓ Gunicorn restarted"
echo ""

# Check service status
echo "7. Checking gunicorn status..."
sudo systemctl status gunicorn --no-pager | head -n 10
echo ""

echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test product creation API"
echo "2. Verify required_points field is working"
echo "3. If issues occur, restore backup:"
echo "   cp $BACKUP_FILE db.sqlite3"
echo "   sudo systemctl restart gunicorn"
echo ""
