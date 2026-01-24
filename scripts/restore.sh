#!/bin/bash

# BetterLaser ERP Restore Script
# This script restores backups of the database and media files

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[RESTORE]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_timestamp> [backup_directory]"
    echo "Example: $0 20240101_120000"
    echo "Example: $0 20240101_120000 /var/backups/better-laser-erp"
    exit 1
fi

BACKUP_TIMESTAMP=$1
BACKUP_DIR=${2:-"/var/backups/better-laser-erp"}

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if backup files exist
DB_BACKUP="$BACKUP_DIR/database_$BACKUP_TIMESTAMP.sql.gz"
MEDIA_BACKUP="$BACKUP_DIR/media_$BACKUP_TIMESTAMP.tar.gz"
CODE_BACKUP="$BACKUP_DIR/code_$BACKUP_TIMESTAMP.tar.gz"
MANIFEST="$BACKUP_DIR/manifest_$BACKUP_TIMESTAMP.txt"

print_status "Checking backup files..."

if [ ! -f "$DB_BACKUP" ]; then
    print_error "Database backup not found: $DB_BACKUP"
    exit 1
fi

if [ ! -f "$MEDIA_BACKUP" ]; then
    print_warning "Media backup not found: $MEDIA_BACKUP"
fi

if [ ! -f "$CODE_BACKUP" ]; then
    print_warning "Code backup not found: $CODE_BACKUP"
fi

if [ -f "$MANIFEST" ]; then
    print_status "Backup manifest found:"
    cat "$MANIFEST"
    echo ""
fi

# Confirmation
echo "⚠️  WARNING: This will restore data from backup timestamp: $BACKUP_TIMESTAMP"
echo "   This operation will overwrite existing data!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    print_status "Restore cancelled by user"
    exit 0
fi

# Stop services if they're running
print_status "Stopping services..."
if command -v systemctl &> /dev/null; then
    sudo systemctl stop better-laser-erp.service 2>/dev/null || true
    sudo systemctl stop better-laser-erp-celery.service 2>/dev/null || true
    sudo systemctl stop better-laser-erp-celery-beat.service 2>/dev/null || true
fi

# Restore database
print_status "Restoring database..."
if command -v mysql &> /dev/null; then
    # Create database if it doesn't exist
    mysql -h"${DB_HOST:-localhost}" -P"${DB_PORT:-3306}" -u"${DB_USER:-root}" -p"${DB_PASSWORD}" -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME:-better_laser_erp} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    
    # Drop all tables first (optional, for clean restore)
    read -p "Drop all existing tables before restore? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        mysql -h"${DB_HOST:-localhost}" -P"${DB_PORT:-3306}" -u"${DB_USER:-root}" -p"${DB_PASSWORD}" "${DB_NAME:-better_laser_erp}" -e "SET FOREIGN_KEY_CHECKS = 0; SET GROUP_CONCAT_MAX_LEN=32768; SET @tables = NULL; SELECT GROUP_CONCAT('\`', table_name, '\`') INTO @tables FROM information_schema.tables WHERE table_schema = '${DB_NAME:-better_laser_erp}'; SELECT IFNULL(@tables,'dummy') INTO @tables; SET @tables = CONCAT('DROP TABLE IF EXISTS ', @tables); PREPARE stmt FROM @tables; EXECUTE stmt; DEALLOCATE PREPARE stmt; SET FOREIGN_KEY_CHECKS = 1;"
        print_status "Existing tables dropped"
    fi
    
    # Restore from backup
    gunzip -c "$DB_BACKUP" | mysql -h"${DB_HOST:-localhost}" -P"${DB_PORT:-3306}" -u"${DB_USER:-root}" -p"${DB_PASSWORD}" "${DB_NAME:-better_laser_erp}"
    print_success "Database restored successfully"
else
    print_error "MySQL client not found. Cannot restore database."
    exit 1
fi

# Restore media files
if [ -f "$MEDIA_BACKUP" ]; then
    print_status "Restoring media files..."
    
    # Backup existing media directory
    if [ -d "media" ]; then
        mv media "media.backup.$(date +%Y%m%d_%H%M%S)"
        print_status "Existing media directory backed up"
    fi
    
    # Extract media backup
    tar -xzf "$MEDIA_BACKUP"
    print_success "Media files restored successfully"
else
    print_warning "Skipping media files restore (backup not found)"
fi

# Restore code (optional)
if [ -f "$CODE_BACKUP" ]; then
    read -p "Restore application code? This will overwrite current code (yes/no): " -r
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_status "Restoring application code..."
        
        # Backup current code
        tar --exclude='venv' --exclude='node_modules' -czf "code.backup.$(date +%Y%m%d_%H%M%S).tar.gz" . 2>/dev/null || true
        
        # Extract code backup
        tar -xzf "$CODE_BACKUP"
        print_success "Application code restored successfully"
        
        print_warning "You may need to:"
        print_warning "  1. Reinstall dependencies: pip install -r requirements.txt"
        print_warning "  2. Run migrations: python manage.py migrate"
        print_warning "  3. Collect static files: python manage.py collectstatic"
    fi
fi

# Run post-restore tasks
print_status "Running post-restore tasks..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run migrations to ensure database schema is up to date
if command -v python &> /dev/null; then
    python manage.py migrate --run-syncdb
    print_status "Database migrations completed"
    
    # Collect static files
    python manage.py collectstatic --noinput
    print_status "Static files collected"
fi

# Fix permissions
print_status "Fixing file permissions..."
chmod -R 755 media/ 2>/dev/null || true
chmod -R 755 staticfiles/ 2>/dev/null || true

# Start services
print_status "Starting services..."
if command -v systemctl &> /dev/null; then
    sudo systemctl start better-laser-erp.service 2>/dev/null || true
    sudo systemctl start better-laser-erp-celery.service 2>/dev/null || true
    sudo systemctl start better-laser-erp-celery-beat.service 2>/dev/null || true
fi

echo ""
echo "✅ Restore completed successfully!"
echo ""
echo "📊 Restore Summary:"
echo "  • Database: ✅ Restored from $DB_BACKUP"
echo "  • Media Files: $([ -f "$MEDIA_BACKUP" ] && echo "✅ Restored" || echo "⚠️  Skipped")"
echo "  • Application Code: $([ -f "$CODE_BACKUP" ] && echo "✅ Available" || echo "⚠️  Not found")"
echo "  • Timestamp: $BACKUP_TIMESTAMP"
echo ""
echo "🔍 Next Steps:"
echo "  1. Verify application functionality"
echo "  2. Check logs for any errors"
echo "  3. Test critical features"
echo "  4. Update configurations if needed"
echo ""

print_success "Restore process completed!"