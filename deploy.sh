#!/bin/bash

# BetterLaser ERP Deployment Script
# This script automates the deployment process

set -e  # Exit on any error

echo "🚀 Starting BetterLaser ERP Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check environment
ENVIRONMENT=${1:-development}
print_status "Deploying to: $ENVIRONMENT"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found, copying from .env.example"
    cp .env.example .env
    print_warning "Please edit .env file with your configuration"
fi

# Create necessary directories
print_status "Creating directories..."
mkdir -p logs
mkdir -p media
mkdir -p staticfiles
mkdir -p legacy_data

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies
if command -v npm &> /dev/null; then
    print_status "Installing Node.js dependencies..."
    npm install
    
    # Build frontend assets
    print_status "Building frontend assets..."
    npm run build
else
    print_warning "npm not found, skipping frontend build"
fi

# Database operations
print_status "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if it doesn't exist
print_status "Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...')
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# Load initial data if available
if [ -f "fixtures/initial_data.json" ]; then
    print_status "Loading initial data..."
    python manage.py loaddata fixtures/initial_data.json
fi

# Set up log rotation
print_status "Setting up log rotation..."
cat > logs/logrotate.conf << EOF
$(pwd)/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $(whoami) $(whoami)
}
EOF

# Production-specific setup
if [ "$ENVIRONMENT" = "production" ]; then
    print_status "Setting up production environment..."
    
    # Check if Docker is available
    if command -v docker &> /dev/null; then
        print_status "Docker found, building containers..."
        docker-compose build
        
        # Start services
        print_status "Starting services..."
        docker-compose up -d
        
        # Wait for services to be ready
        print_status "Waiting for services to be ready..."
        sleep 30
        
        # Run migrations in container
        docker-compose exec web python manage.py migrate
        docker-compose exec web python manage.py collectstatic --noinput
        
    else
        print_warning "Docker not found, manual setup required"
        
        # Install and configure Nginx (if not exists)
        if ! command -v nginx &> /dev/null; then
            print_warning "Nginx not found, please install manually"
        fi
        
        # Install and configure systemd service
        print_status "Creating systemd service..."
        sudo tee /etc/systemd/system/better-laser-erp.service > /dev/null << EOF
[Unit]
Description=BetterLaser ERP
After=network.target

[Service]
Type=exec
User=$(whoami)
Group=$(whoami)
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/gunicorn better_laser_erp.wsgi:application --bind 0.0.0.0:8000
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable better-laser-erp
        sudo systemctl start better-laser-erp
    fi
    
    # Set up SSL certificate (Let's Encrypt)
    if command -v certbot &> /dev/null; then
        print_status "Setting up SSL certificate..."
        # This would need domain configuration
        print_warning "SSL setup requires domain configuration"
    fi
fi

# Development-specific setup
if [ "$ENVIRONMENT" = "development" ]; then
    print_status "Setting up development environment..."
    
    # Install development dependencies
    pip install django-debug-toolbar ipython
    
    # Create sample data
    print_status "Creating sample data..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.departments.models import Department
from apps.customers.models import Customer, CustomerCategory
from apps.suppliers.models import Supplier, SupplierCategory
from apps.products.models import Product, ProductCategory, Unit, Brand

User = get_user_model()

# Create sample departments
dept, created = Department.objects.get_or_create(
    code='SALES',
    defaults={'name': '销售部', 'description': '负责产品销售'}
)

# Create sample customer category
cat, created = CustomerCategory.objects.get_or_create(
    code='ENTERPRISE',
    defaults={'name': '企业客户', 'description': '企业类型客户'}
)

# Create sample customer
customer, created = Customer.objects.get_or_create(
    code='CUST001',
    defaults={
        'name': '示例客户A',
        'category': cat,
        'customer_type': 'enterprise',
        'contact_person': '张三',
        'phone': '13800138000',
        'email': 'zhangsan@example.com'
    }
)

print('Sample data created successfully')
"
fi

# Health check
print_status "Running health check..."
python manage.py check --deploy

# Test database connection
python manage.py shell -c "
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('Database connection: OK')
except Exception as e:
    print(f'Database connection: FAILED - {e}')
"

# Final status
print_success "Deployment completed successfully!"
print_status "Environment: $ENVIRONMENT"

if [ "$ENVIRONMENT" = "development" ]; then
    print_status "To start development server:"
    print_status "  source venv/bin/activate"
    print_status "  python manage.py runserver"
    print_status ""
    print_status "Admin URL: http://localhost:8000/admin/"
    print_status "Admin credentials: admin/admin123"
elif [ "$ENVIRONMENT" = "production" ]; then
    if command -v docker &> /dev/null; then
        print_status "Services are running via Docker Compose"
        print_status "Check status: docker-compose ps"
        print_status "View logs: docker-compose logs -f"
    else
        print_status "Service status: sudo systemctl status better-laser-erp"
        print_status "View logs: sudo journalctl -u better-laser-erp -f"
    fi
fi

print_status "Deployment log saved to: logs/deployment.log"
echo "$(date): Deployment completed successfully" >> logs/deployment.log