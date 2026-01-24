#!/bin/bash

# BetterLaser ERP Backup Script
# This script creates backups of the database and media files

set -e

# Configuration
BACKUP_DIR="/var/backups/better-laser-erp"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[BACKUP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

print_status "Starting backup process..."

# Database backup
print_status "Backing up database..."
if command -v mysqldump &> /dev/null; then
    mysqldump \
        -h"${DB_HOST:-localhost}" \
        -P"${DB_PORT:-3306}" \
        -u"${DB_USER:-root}" \
        -p"${DB_PASSWORD}" \
        --single-transaction \
        --routines \
        --triggers \
        "${DB_NAME:-better_laser_erp}" | gzip > "$BACKUP_DIR/database_$DATE.sql.gz"
    
    print_status "Database backup completed: database_$DATE.sql.gz"
else
    print_error "mysqldump not found. Skipping database backup."
fi

# Media files backup
print_status "Backing up media files..."
if [ -d "media" ]; then
    tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" media/
    print_status "Media files backup completed: media_$DATE.tar.gz"
else
    print_warning "Media directory not found. Skipping media backup."
fi

# Application code backup (excluding venv and node_modules)
print_status "Backing up application code..."
tar --exclude='venv' \
    --exclude='node_modules' \
    --exclude='staticfiles' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    -czf "$BACKUP_DIR/code_$DATE.tar.gz" .

print_status "Application code backup completed: code_$DATE.tar.gz"

# Clean up old backups
print_status "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete
print_status "Old backups cleaned up"

# Create backup manifest
cat > "$BACKUP_DIR/manifest_$DATE.txt" << EOF
BetterLaser ERP Backup Manifest
Generated: $(date)
Backup Directory: $BACKUP_DIR

Files in this backup:
- database_$DATE.sql.gz (Database dump)
- media_$DATE.tar.gz (Media files)
- code_$DATE.tar.gz (Application code)

Database Info:
- Host: ${DB_HOST:-localhost}
- Database: ${DB_NAME:-better_laser_erp}
- Backup Time: $(date)

Restore Instructions:
1. Database: gunzip -c database_$DATE.sql.gz | mysql -u[user] -p[password] [database]
2. Media: tar -xzf media_$DATE.tar.gz
3. Code: tar -xzf code_$DATE.tar.gz
EOF

print_status "Backup manifest created: manifest_$DATE.txt"

# Calculate backup sizes
DB_SIZE=$(du -h "$BACKUP_DIR/database_$DATE.sql.gz" 2>/dev/null | cut -f1 || echo "N/A")
MEDIA_SIZE=$(du -h "$BACKUP_DIR/media_$DATE.tar.gz" 2>/dev/null | cut -f1 || echo "N/A")
CODE_SIZE=$(du -h "$BACKUP_DIR/code_$DATE.tar.gz" 2>/dev/null | cut -f1 || echo "N/A")

echo ""
echo "✅ Backup completed successfully!"
echo ""
echo "📊 Backup Summary:"
echo "  • Database: $DB_SIZE"
echo "  • Media Files: $MEDIA_SIZE"
echo "  • Application Code: $CODE_SIZE"
echo "  • Location: $BACKUP_DIR"
echo "  • Timestamp: $DATE"
echo ""

print_status "Backup process completed!"