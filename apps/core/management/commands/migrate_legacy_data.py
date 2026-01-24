"""
Management command to migrate data from legacy ERP system.
"""
import os
import csv
import json
from decimal import Decimal
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.customers.models import Customer, CustomerCategory, CustomerContact, CustomerAddress
from apps.suppliers.models import Supplier, SupplierCategory, SupplierContact
from apps.products.models import Product, ProductCategory, Brand, Unit
from apps.departments.models import Department
from apps.users.models import Role, UserRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Migrate data from legacy ERP system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default='legacy_data',
            help='Directory containing legacy data files'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run migration without saving data'
        )
        parser.add_argument(
            '--module',
            type=str,
            choices=['users', 'customers', 'suppliers', 'products', 'all'],
            default='all',
            help='Specific module to migrate'
        )

    def handle(self, *args, **options):
        self.data_dir = options['data_dir']
        self.dry_run = options['dry_run']
        self.module = options['module']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('Running in DRY RUN mode - no data will be saved')
            )
        
        if not os.path.exists(self.data_dir):
            raise CommandError(f'Data directory {self.data_dir} does not exist')
        
        try:
            if self.module == 'all':
                self.migrate_all()
            else:
                getattr(self, f'migrate_{self.module}')()
                
            self.stdout.write(
                self.style.SUCCESS('Data migration completed successfully')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Migration failed: {str(e)}')
            )
            raise

    def migrate_all(self):
        """Migrate all modules in correct order."""
        self.stdout.write('Starting full data migration...')
        
        # Order is important due to foreign key dependencies
        self.migrate_users()
        self.migrate_departments()
        self.migrate_customers()
        self.migrate_suppliers()
        self.migrate_products()

    @transaction.atomic
    def migrate_users(self):
        """Migrate user data."""
        self.stdout.write('Migrating users...')
        
        users_file = os.path.join(self.data_dir, 'users.csv')
        if not os.path.exists(users_file):
            self.stdout.write(
                self.style.WARNING('Users file not found, skipping...')
            )
            return
        
        with open(users_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            users_created = 0
            
            for row in reader:
                try:
                    if not self.dry_run:
                        user, created = User.objects.get_or_create(
                            username=row['username'],
                            defaults={
                                'email': row.get('email', ''),
                                'first_name': row.get('first_name', ''),
                                'last_name': row.get('last_name', ''),
                                'employee_id': row.get('employee_id', ''),
                                'phone': row.get('phone', ''),
                                'is_active': row.get('is_active', 'true').lower() == 'true',
                            }
                        )
                        if created:
                            users_created += 1
                    else:
                        users_created += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating user {row.get("username")}: {e}')
                    )
        
        self.stdout.write(f'Created {users_created} users')

    @transaction.atomic
    def migrate_departments(self):
        """Migrate department data."""
        self.stdout.write('Migrating departments...')
        
        dept_file = os.path.join(self.data_dir, 'departments.csv')
        if not os.path.exists(dept_file):
            self.stdout.write(
                self.style.WARNING('Departments file not found, skipping...')
            )
            return
        
        with open(dept_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            depts_created = 0
            
            for row in reader:
                try:
                    if not self.dry_run:
                        dept, created = Department.objects.get_or_create(
                            code=row['code'],
                            defaults={
                                'name': row['name'],
                                'description': row.get('description', ''),
                                'phone': row.get('phone', ''),
                                'email': row.get('email', ''),
                                'address': row.get('address', ''),
                                'is_active': row.get('is_active', 'true').lower() == 'true',
                            }
                        )
                        if created:
                            depts_created += 1
                    else:
                        depts_created += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating department {row.get("code")}: {e}')
                    )
        
        self.stdout.write(f'Created {depts_created} departments')

    @transaction.atomic
    def migrate_customers(self):
        """Migrate customer data."""
        self.stdout.write('Migrating customers...')
        
        # First migrate customer categories
        categories_file = os.path.join(self.data_dir, 'customer_categories.csv')
        if os.path.exists(categories_file):
            with open(categories_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not self.dry_run:
                        CustomerCategory.objects.get_or_create(
                            code=row['code'],
                            defaults={
                                'name': row['name'],
                                'description': row.get('description', ''),
                                'discount_rate': Decimal(row.get('discount_rate', '0')),
                            }
                        )
        
        # Then migrate customers
        customers_file = os.path.join(self.data_dir, 'customers.csv')
        if not os.path.exists(customers_file):
            self.stdout.write(
                self.style.WARNING('Customers file not found, skipping...')
            )
            return
        
        with open(customers_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            customers_created = 0
            
            for row in reader:
                try:
                    category = None
                    if row.get('category_code'):
                        try:
                            category = CustomerCategory.objects.get(code=row['category_code'])
                        except CustomerCategory.DoesNotExist:
                            pass
                    
                    if not self.dry_run:
                        customer, created = Customer.objects.get_or_create(
                            code=row['code'],
                            defaults={
                                'name': row['name'],
                                'customer_type': row.get('customer_type', 'enterprise'),
                                'category': category,
                                'level': row.get('level', 'C'),
                                'contact_person': row.get('contact_person', ''),
                                'phone': row.get('phone', ''),
                                'mobile': row.get('mobile', ''),
                                'email': row.get('email', ''),
                                'address': row.get('address', ''),
                                'city': row.get('city', ''),
                                'province': row.get('province', ''),
                                'tax_number': row.get('tax_number', ''),
                                'credit_limit': Decimal(row.get('credit_limit', '0')),
                                'is_active': row.get('is_active', 'true').lower() == 'true',
                            }
                        )
                        if created:
                            customers_created += 1
                    else:
                        customers_created += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating customer {row.get("code")}: {e}')
                    )
        
        self.stdout.write(f'Created {customers_created} customers')

    @transaction.atomic
    def migrate_suppliers(self):
        """Migrate supplier data."""
        self.stdout.write('Migrating suppliers...')
        
        # First migrate supplier categories
        categories_file = os.path.join(self.data_dir, 'supplier_categories.csv')
        if os.path.exists(categories_file):
            with open(categories_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not self.dry_run:
                        SupplierCategory.objects.get_or_create(
                            code=row['code'],
                            defaults={
                                'name': row['name'],
                                'description': row.get('description', ''),
                            }
                        )
        
        # Then migrate suppliers
        suppliers_file = os.path.join(self.data_dir, 'suppliers.csv')
        if not os.path.exists(suppliers_file):
            self.stdout.write(
                self.style.WARNING('Suppliers file not found, skipping...')
            )
            return
        
        with open(suppliers_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            suppliers_created = 0
            
            for row in reader:
                try:
                    category = None
                    if row.get('category_code'):
                        try:
                            category = SupplierCategory.objects.get(code=row['category_code'])
                        except SupplierCategory.DoesNotExist:
                            pass
                    
                    if not self.dry_run:
                        supplier, created = Supplier.objects.get_or_create(
                            code=row['code'],
                            defaults={
                                'name': row['name'],
                                'supplier_type': row.get('supplier_type', 'manufacturer'),
                                'category': category,
                                'level': row.get('level', 'C'),
                                'contact_person': row.get('contact_person', ''),
                                'phone': row.get('phone', ''),
                                'mobile': row.get('mobile', ''),
                                'email': row.get('email', ''),
                                'address': row.get('address', ''),
                                'city': row.get('city', ''),
                                'province': row.get('province', ''),
                                'tax_number': row.get('tax_number', ''),
                                'payment_terms': row.get('payment_terms', ''),
                                'lead_time': int(row.get('lead_time', '0')),
                                'is_active': row.get('is_active', 'true').lower() == 'true',
                            }
                        )
                        if created:
                            suppliers_created += 1
                    else:
                        suppliers_created += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating supplier {row.get("code")}: {e}')
                    )
        
        self.stdout.write(f'Created {suppliers_created} suppliers')

    @transaction.atomic
    def migrate_products(self):
        """Migrate product data."""
        self.stdout.write('Migrating products...')
        
        # First migrate units
        units_file = os.path.join(self.data_dir, 'units.csv')
        if os.path.exists(units_file):
            with open(units_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not self.dry_run:
                        Unit.objects.get_or_create(
                            symbol=row['symbol'],
                            defaults={
                                'name': row['name'],
                                'unit_type': row.get('unit_type', 'basic'),
                                'conversion_factor': Decimal(row.get('conversion_factor', '1')),
                            }
                        )
        
        # Then migrate brands
        brands_file = os.path.join(self.data_dir, 'brands.csv')
        if os.path.exists(brands_file):
            with open(brands_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not self.dry_run:
                        Brand.objects.get_or_create(
                            code=row['code'],
                            defaults={
                                'name': row['name'],
                                'description': row.get('description', ''),
                                'country': row.get('country', ''),
                            }
                        )
        
        # Then migrate product categories
        categories_file = os.path.join(self.data_dir, 'product_categories.csv')
        if os.path.exists(categories_file):
            with open(categories_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not self.dry_run:
                        ProductCategory.objects.get_or_create(
                            code=row['code'],
                            defaults={
                                'name': row['name'],
                                'description': row.get('description', ''),
                            }
                        )
        
        # Finally migrate products
        products_file = os.path.join(self.data_dir, 'products.csv')
        if not os.path.exists(products_file):
            self.stdout.write(
                self.style.WARNING('Products file not found, skipping...')
            )
            return
        
        with open(products_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            products_created = 0
            
            for row in reader:
                try:
                    # Get related objects
                    category = None
                    if row.get('category_code'):
                        try:
                            category = ProductCategory.objects.get(code=row['category_code'])
                        except ProductCategory.DoesNotExist:
                            pass
                    
                    brand = None
                    if row.get('brand_code'):
                        try:
                            brand = Brand.objects.get(code=row['brand_code'])
                        except Brand.DoesNotExist:
                            pass
                    
                    base_unit = None
                    if row.get('base_unit_symbol'):
                        try:
                            base_unit = Unit.objects.get(symbol=row['base_unit_symbol'])
                        except Unit.DoesNotExist:
                            # Create default unit if not exists
                            base_unit = Unit.objects.create(
                                name='个',
                                symbol='个',
                                unit_type='quantity'
                            )
                    
                    if not self.dry_run and base_unit:
                        product, created = Product.objects.get_or_create(
                            code=row['code'],
                            defaults={
                                'name': row['name'],
                                'product_type': row.get('product_type', 'finished'),
                                'category': category,
                                'brand': brand,
                                'base_unit': base_unit,
                                'description': row.get('description', ''),
                                'specifications': row.get('specifications', ''),
                                'model': row.get('model', ''),
                                'cost_price': Decimal(row.get('cost_price', '0')),
                                'purchase_price': Decimal(row.get('purchase_price', '0')),
                                'sales_price': Decimal(row.get('sales_price', '0')),
                                'min_stock': Decimal(row.get('min_stock', '0')),
                                'max_stock': Decimal(row.get('max_stock', '0')),
                                'status': row.get('status', 'active'),
                                'is_active': row.get('is_active', 'true').lower() == 'true',
                            }
                        )
                        if created:
                            products_created += 1
                    else:
                        products_created += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating product {row.get("code")}: {e}')
                    )
        
        self.stdout.write(f'Created {products_created} products')