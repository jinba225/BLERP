"""
数据库管理工具类
提供数据库备份、还原、测试数据管理等功能
"""
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import connection


class DatabaseHelper:
    """数据库管理助手类"""

    @staticmethod
    def get_backup_dir():
        """获取备份目录路径"""
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(exist_ok=True)
        return backup_dir

    @staticmethod
    def is_sqlite():
        """检查是否使用SQLite数据库"""
        return settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"

    @staticmethod
    def is_mysql():
        """检查是否使用MySQL数据库"""
        return settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql"

    @staticmethod
    def get_db_info():
        """获取数据库信息"""
        db_config = settings.DATABASES["default"]
        engine = db_config["ENGINE"].split(".")[-1]

        info = {
            "engine": engine,
            "name": db_config.get("NAME", ""),
        }

        if DatabaseHelper.is_sqlite():
            db_path = Path(db_config["NAME"])
            if db_path.exists():
                info["size"] = db_path.stat().st_size
                info["size_mb"] = round(info["size"] / (1024 * 1024), 2)
            else:
                info["size"] = 0
                info["size_mb"] = 0

        # 获取表数量
        with connection.cursor() as cursor:
            if DatabaseHelper.is_sqlite():
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            elif DatabaseHelper.is_mysql():
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()"
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )

            info["table_count"] = cursor.fetchone()[0]

        return info

    @staticmethod
    def backup_database():
        """
        备份数据库
        返回: (success, message, backup_file_path)
        """
        try:
            backup_dir = DatabaseHelper.get_backup_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if DatabaseHelper.is_sqlite():
                # SQLite备份：直接复制文件
                db_name = settings.DATABASES["default"]["NAME"]
                backup_filename = f"backup_sqlite_{timestamp}.db"
                backup_path = backup_dir / backup_filename

                shutil.copy2(db_name, backup_path)

                return True, f"数据库备份成功: {backup_filename}", str(backup_path)

            elif DatabaseHelper.is_mysql():
                # MySQL备份：使用mysqldump
                db_config = settings.DATABASES["default"]
                backup_filename = f"backup_mysql_{timestamp}.sql"
                backup_path = backup_dir / backup_filename

                cmd = [
                    "mysqldump",
                    "-h",
                    db_config.get("HOST", "localhost"),
                    "-P",
                    str(db_config.get("PORT", 3306)),
                    "-u",
                    db_config.get("USER", "root"),
                ]

                if db_config.get("PASSWORD"):
                    cmd.extend(["-p" + db_config["PASSWORD"]])

                cmd.append(db_config["NAME"])

                with open(backup_path, "w", encoding="utf-8") as f:
                    result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)

                if result.returncode == 0:
                    return True, f"数据库备份成功: {backup_filename}", str(backup_path)
                else:
                    return False, f"MySQL备份失败: {result.stderr}", None

            else:
                return False, "不支持的数据库类型", None

        except Exception as e:
            return False, f"备份失败: {str(e)}", None

    @staticmethod
    def restore_database(backup_file_path):
        """
        从备份文件还原数据库
        参数: backup_file_path - 备份文件路径
        返回: (success, message)
        """
        try:
            backup_path = Path(backup_file_path)
            if not backup_path.exists():
                return False, "备份文件不存在"

            # 先备份当前数据库
            success, msg, current_backup = DatabaseHelper.backup_database()
            if not success:
                return False, f"无法备份当前数据库: {msg}"

            if DatabaseHelper.is_sqlite():
                # SQLite还原：直接复制文件
                db_name = settings.DATABASES["default"]["NAME"]

                # 关闭所有数据库连接
                connection.close()

                # 复制备份文件
                shutil.copy2(backup_path, db_name)

                return True, f"数据库还原成功（当前数据库已备份到: {Path(current_backup).name}）"

            elif DatabaseHelper.is_mysql():
                # MySQL还原：使用mysql命令
                db_config = settings.DATABASES["default"]

                cmd = [
                    "mysql",
                    "-h",
                    db_config.get("HOST", "localhost"),
                    "-P",
                    str(db_config.get("PORT", 3306)),
                    "-u",
                    db_config.get("USER", "root"),
                ]

                if db_config.get("PASSWORD"):
                    cmd.extend(["-p" + db_config["PASSWORD"]])

                cmd.append(db_config["NAME"])

                with open(backup_path, "r", encoding="utf-8") as f:
                    result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)

                if result.returncode == 0:
                    return True, f"数据库还原成功（当前数据库已备份到: {Path(current_backup).name}）"
                else:
                    return False, f"MySQL还原失败: {result.stderr}"

            else:
                return False, "不支持的数据库类型"

        except Exception as e:
            return False, f"还原失败: {str(e)}"

    @staticmethod
    def list_backups():
        """
        列出所有备份文件
        返回: 备份文件列表（按时间倒序）
        """
        backup_dir = DatabaseHelper.get_backup_dir()
        backups = []

        for file_path in backup_dir.glob("backup_*"):
            if file_path.is_file():
                stat = file_path.stat()
                backups.append(
                    {
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created_at": datetime.fromtimestamp(stat.st_mtime),
                    }
                )

        # 按创建时间倒序排序
        backups.sort(key=lambda x: x["created_at"], reverse=True)

        return backups

    @staticmethod
    def add_test_data():
        """
        添加完整的测试数据（包含所有必要字段和关联数据）
        创建各个模块的示例数据，支持完整的业务流程测试
        返回: (success, message, stats)
        """
        try:
            from decimal import Decimal

            stats = {
                "tax_rates_created": 0,
                "units_created": 0,
                "brands_created": 0,
                "categories_created": 0,
                "warehouses_created": 0,
                "customers": 0,
                "customer_contacts": 0,
                "suppliers": 0,
                "supplier_contacts": 0,
                "products": 0,
            }

            # 导入必要的模型
            from customers.models import Customer, CustomerContact
            from django.db.models import Q
            from finance.models import TaxRate
            from inventory.models import Location, Warehouse
            from products.models import Brand, Product, ProductCategory, Unit
            from suppliers.models import Supplier, SupplierContact
            from users.models import User

            # ========== 预清理：硬删除所有已软删除的测试数据（释放唯一性约束）==========
            # 硬删除已软删除的客户
            for customer in Customer.objects.filter(code__startswith="TEST_CUST", is_deleted=True):
                customer.hard_delete()

            # 硬删除已软删除的供应商
            for supplier in Supplier.objects.filter(code__startswith="TEST_SUP", is_deleted=True):
                supplier.hard_delete()

            # 硬删除已软删除的产品
            for product in Product.objects.filter(code__startswith="TEST_PROD", is_deleted=True):
                product.hard_delete()

            # 获取或创建默认用户
            test_user = User.objects.filter(is_superuser=True).first()
            if not test_user:
                return False, "请先创建管理员用户", stats

            # ========== 0. 创建税率 ==========
            tax_rates_data = [
                {
                    "name": "增值税13%",
                    "code": "VAT_13",
                    "rate": Decimal("0.13"),
                    "is_default": True,
                    "tax_type": "vat",
                },
                {
                    "name": "增值税9%",
                    "code": "VAT_09",
                    "rate": Decimal("0.09"),
                    "is_default": False,
                    "tax_type": "vat",
                },
                {
                    "name": "增值税6%",
                    "code": "VAT_06",
                    "rate": Decimal("0.06"),
                    "is_default": False,
                    "tax_type": "vat",
                },
                {
                    "name": "零税率",
                    "code": "VAT_0",
                    "rate": Decimal("0.00"),
                    "is_default": False,
                    "tax_type": "vat",
                },
            ]

            stats["tax_rates_created"] = 0
            for tax_data in tax_rates_data:
                existing = TaxRate.objects.filter(code=tax_data["code"], is_deleted=False).first()
                if not existing:
                    TaxRate.objects.create(
                        name=tax_data["name"],
                        code=tax_data["code"],
                        rate=tax_data["rate"],
                        is_default=tax_data["is_default"],
                        tax_type=tax_data["tax_type"],
                        created_by=test_user,
                    )
                    stats["tax_rates_created"] += 1

            # ========== 1. 创建计量单位 ==========
            units_data = [
                {"name": "激光台", "symbol": "UNIT", "unit_type": "count", "description": "测试计量单位-台"},
                {"name": "激光套", "symbol": "SET", "unit_type": "count", "description": "测试计量单位-套"},
                {"name": "激光件", "symbol": "PC", "unit_type": "count", "description": "测试计量单位-件"},
            ]

            for unit_data in units_data:
                existing = Unit.objects.filter(
                    Q(name=unit_data["name"]) | Q(symbol=unit_data["symbol"]), is_deleted=False
                ).first()

                if not existing:
                    Unit.objects.create(
                        name=unit_data["name"],
                        symbol=unit_data["symbol"],
                        unit_type=unit_data["unit_type"],
                        description=unit_data["description"],
                        created_by=test_user,
                    )
                    stats["units_created"] += 1

            # ========== 2. 创建品牌 ==========
            brands_data = [
                {
                    "name": "测试激光品牌A",
                    "code": "TEST_BL001",
                    "description": "专业激光设备制造商，国际知名品牌",
                    "country": "中国",
                    "website": "https://www.test-laser-a.com",
                },
                {
                    "name": "测试激光品牌B",
                    "code": "TEST_TC001",
                    "description": "创新型激光技术企业，行业领先者",
                    "country": "德国",
                    "website": "https://www.test-tech-b.com",
                },
            ]

            for brand_data in brands_data:
                existing = Brand.objects.filter(
                    Q(name=brand_data["name"]) | Q(code=brand_data["code"]), is_deleted=False
                ).first()

                if not existing:
                    Brand.objects.create(**{**brand_data, "created_by": test_user})
                    stats["brands_created"] += 1

            # ========== 3. 创建产品分类（层级结构）==========
            categories_data = [
                {"name": "测试激光设备", "code": "TEST_LASER", "parent": None},
                {"name": "测试激光切割机", "code": "TEST_LASER_CUT", "parent": "TEST_LASER"},
                {"name": "测试激光焊接机", "code": "TEST_LASER_WELD", "parent": "TEST_LASER"},
                {"name": "测试激光打标机", "code": "TEST_LASER_MARK", "parent": "TEST_LASER"},
            ]

            created_categories = {}
            for cat_data in categories_data:
                parent_code = cat_data.pop("parent")
                parent_obj = created_categories.get(parent_code) if parent_code else None

                category, created = ProductCategory.objects.get_or_create(
                    code=cat_data["code"],
                    is_deleted=False,
                    defaults={
                        **cat_data,
                        "parent": parent_obj,
                        "created_by": test_user,
                    },
                )
                created_categories[cat_data["code"]] = category
                if created:
                    stats["categories_created"] += 1

            # ========== 4. 创建仓库 ==========
            warehouses_data = [
                {
                    "code": "TEST_WH001",
                    "name": "测试主仓库",
                    "address": "测试市高新区科技路123号",
                    "warehouse_type": "main",
                    "capacity": Decimal("10000.00"),
                    "is_active": True,
                },
                {
                    "code": "TEST_WH002",
                    "name": "测试借用仓",
                    "address": "测试市工业园区东路456号",
                    "warehouse_type": "borrow",
                    "capacity": Decimal("3000.00"),
                    "is_active": True,
                },
            ]

            for wh_data in warehouses_data:
                warehouse, created = Warehouse.objects.get_or_create(
                    code=wh_data["code"],
                    is_deleted=False,
                    defaults={**wh_data, "created_by": test_user},
                )
                if created:
                    stats["warehouses_created"] += 1

                # 为每个仓库创建库位
                if created or True:  # 确保库位存在
                    locations_data = [
                        {
                            "code": "A-01-01",
                            "name": "A区1排1层",
                            "aisle": "A",
                            "shelf": "01",
                            "level": "01",
                        },
                        {
                            "code": "A-01-02",
                            "name": "A区1排2层",
                            "aisle": "A",
                            "shelf": "01",
                            "level": "02",
                        },
                        {
                            "code": "B-01-01",
                            "name": "B区1排1层",
                            "aisle": "B",
                            "shelf": "01",
                            "level": "01",
                        },
                    ]
                    for loc_data in locations_data:
                        Location.objects.get_or_create(
                            warehouse=warehouse,
                            code=loc_data["code"],
                            is_deleted=False,
                            defaults={**loc_data, "created_by": test_user},
                        )

            # ========== 5. 创建客户（详细信息）==========
            customers_data = [
                {
                    "name": "测试客户A公司",
                    "code": "TEST_CUST001",
                    "customer_level": "A",
                    "status": "active",
                    "address": "北京市朝阳区建国路88号",
                    "city": "北京市",
                    "province": "北京",
                    "country": "中国",
                    "industry": "制造业",
                    "credit_limit": Decimal("1000000.00"),
                    "payment_terms": "30",
                    "discount_rate": Decimal("5.00"),
                    "notes": "重要客户，优先服务",
                },
                {
                    "name": "测试客户B公司",
                    "code": "TEST_CUST002",
                    "customer_level": "B",
                    "status": "active",
                    "address": "上海市浦东新区张江高科技园区",
                    "city": "上海市",
                    "province": "上海",
                    "country": "中国",
                    "industry": "科技服务",
                    "credit_limit": Decimal("500000.00"),
                    "payment_terms": "15",
                    "discount_rate": Decimal("3.00"),
                },
                {
                    "name": "测试客户C公司",
                    "code": "TEST_CUST003",
                    "customer_level": "C",
                    "status": "active",
                    "address": "广州市天河区珠江新城",
                    "city": "广州市",
                    "province": "广东",
                    "country": "中国",
                    "industry": "贸易",
                    "credit_limit": Decimal("200000.00"),
                    "payment_terms": "0",
                },
                {
                    "name": "测试客户D公司",
                    "code": "TEST_CUST004",
                    "customer_level": "A",
                    "status": "active",
                    "address": "深圳市南山区科技园南路",
                    "city": "深圳市",
                    "province": "广东",
                    "country": "中国",
                    "industry": "电子制造",
                    "credit_limit": Decimal("800000.00"),
                    "payment_terms": "30",
                    "discount_rate": Decimal("4.00"),
                },
                {
                    "name": "测试客户E公司",
                    "code": "TEST_CUST005",
                    "customer_level": "B",
                    "status": "active",
                    "address": "杭州市西湖区文三路",
                    "city": "杭州市",
                    "province": "浙江",
                    "country": "中国",
                    "industry": "汽车制造",
                    "credit_limit": Decimal("600000.00"),
                    "payment_terms": "20",
                    "discount_rate": Decimal("3.50"),
                },
                {
                    "name": "测试客户F公司",
                    "code": "TEST_CUST006",
                    "customer_level": "B",
                    "status": "active",
                    "address": "成都市高新区天府大道",
                    "city": "成都市",
                    "province": "四川",
                    "country": "中国",
                    "industry": "机械设备",
                    "credit_limit": Decimal("450000.00"),
                    "payment_terms": "15",
                    "discount_rate": Decimal("2.50"),
                },
                {
                    "name": "测试客户G公司",
                    "code": "TEST_CUST007",
                    "customer_level": "C",
                    "status": "active",
                    "address": "武汉市江汉区中山大道",
                    "city": "武汉市",
                    "province": "湖北",
                    "country": "中国",
                    "industry": "建筑工程",
                    "credit_limit": Decimal("300000.00"),
                    "payment_terms": "10",
                    "discount_rate": Decimal("2.00"),
                },
                {
                    "name": "测试客户H公司",
                    "code": "TEST_CUST008",
                    "customer_level": "A",
                    "status": "active",
                    "address": "南京市玄武区中山路",
                    "city": "南京市",
                    "province": "江苏",
                    "country": "中国",
                    "industry": "航空航天",
                    "credit_limit": Decimal("1200000.00"),
                    "payment_terms": "45",
                    "discount_rate": Decimal("5.50"),
                },
                {
                    "name": "测试客户I公司",
                    "code": "TEST_CUST009",
                    "customer_level": "B",
                    "status": "active",
                    "address": "天津市和平区南京路",
                    "city": "天津市",
                    "province": "天津",
                    "country": "中国",
                    "industry": "化工制造",
                    "credit_limit": Decimal("550000.00"),
                    "payment_terms": "20",
                    "discount_rate": Decimal("3.00"),
                },
                {
                    "name": "测试客户J公司",
                    "code": "TEST_CUST010",
                    "customer_level": "C",
                    "status": "active",
                    "address": "重庆市渝中区解放碑",
                    "city": "重庆市",
                    "province": "重庆",
                    "country": "中国",
                    "industry": "物流运输",
                    "credit_limit": Decimal("250000.00"),
                    "payment_terms": "7",
                    "discount_rate": Decimal("1.50"),
                },
            ]

            for cust_data in customers_data:
                customer, created = Customer.objects.get_or_create(
                    code=cust_data["code"],
                    is_deleted=False,
                    defaults={**cust_data, "created_by": test_user},
                )
                if created:
                    stats["customers"] += 1

                    # 为每个客户创建联系人（通用方式）
                    customer_code = cust_data["code"]
                    cust_num = customer_code.replace("TEST_CUST", "")

                    # 每个客户创建1个主联系人
                    contact_data = {
                        "name": f"{customer_code[-1]}经理",
                        "position": "采购经理",
                        "mobile": f"138{cust_num.zfill(8)}",
                        "email": f"manager{cust_num}@test-cust.com",
                        "is_primary": True,
                    }
                    CustomerContact.objects.get_or_create(
                        customer=customer,
                        name=contact_data["name"],
                        defaults={**contact_data, "created_by": test_user},
                    )
                    stats["customer_contacts"] += 1

            # ========== 6. 创建供应商（详细信息）==========
            suppliers_data = [
                {
                    "name": "测试供应商甲",
                    "code": "TEST_SUP001",
                    "level": "A",
                    "address": "深圳市南山区科技园",
                    "city": "深圳市",
                    "province": "广东",
                    "country": "中国",
                    "payment_terms": "60",
                    "currency": "CNY",
                    "lead_time": 30,
                    "quality_rating": Decimal("4.5"),
                    "delivery_rating": Decimal("4.8"),
                    "is_active": True,
                    "is_approved": True,
                },
                {
                    "name": "测试供应商乙",
                    "code": "TEST_SUP002",
                    "level": "B",
                    "address": "杭州市滨江区高新技术开发区",
                    "city": "杭州市",
                    "province": "浙江",
                    "country": "中国",
                    "payment_terms": "45",
                    "currency": "CNY",
                    "lead_time": 20,
                    "quality_rating": Decimal("4.2"),
                    "delivery_rating": Decimal("4.5"),
                    "is_active": True,
                    "is_approved": True,
                },
                {
                    "name": "测试供应商丙",
                    "code": "TEST_SUP003",
                    "level": "A",
                    "address": "苏州市工业园区星湖街",
                    "city": "苏州市",
                    "province": "江苏",
                    "country": "中国",
                    "payment_terms": "60",
                    "currency": "CNY",
                    "lead_time": 25,
                    "quality_rating": Decimal("4.7"),
                    "delivery_rating": Decimal("4.6"),
                    "is_active": True,
                    "is_approved": True,
                },
                {
                    "name": "测试供应商丁",
                    "code": "TEST_SUP004",
                    "level": "B",
                    "address": "东莞市松山湖高新技术开发区",
                    "city": "东莞市",
                    "province": "广东",
                    "country": "中国",
                    "payment_terms": "30",
                    "currency": "CNY",
                    "lead_time": 15,
                    "quality_rating": Decimal("4.0"),
                    "delivery_rating": Decimal("4.3"),
                    "is_active": True,
                    "is_approved": True,
                },
                {
                    "name": "测试供应商戊",
                    "code": "TEST_SUP005",
                    "level": "A",
                    "address": "宁波市鄞州区科技园区",
                    "city": "宁波市",
                    "province": "浙江",
                    "country": "中国",
                    "payment_terms": "45",
                    "currency": "CNY",
                    "lead_time": 20,
                    "quality_rating": Decimal("4.6"),
                    "delivery_rating": Decimal("4.7"),
                    "is_active": True,
                    "is_approved": True,
                },
                {
                    "name": "测试供应商己",
                    "code": "TEST_SUP006",
                    "level": "C",
                    "address": "佛山市顺德区工业大道",
                    "city": "佛山市",
                    "province": "广东",
                    "country": "中国",
                    "payment_terms": "20",
                    "currency": "CNY",
                    "lead_time": 10,
                    "quality_rating": Decimal("3.8"),
                    "delivery_rating": Decimal("4.0"),
                    "is_active": True,
                    "is_approved": True,
                },
            ]

            for sup_data in suppliers_data:
                supplier, created = Supplier.objects.get_or_create(
                    code=sup_data["code"],
                    is_deleted=False,
                    defaults={**sup_data, "created_by": test_user},
                )
                if created:
                    stats["suppliers"] += 1

                    # 为每个供应商创建联系人（通用方式）
                    supplier_code = sup_data["code"]
                    sup_num = supplier_code.replace("TEST_SUP", "")

                    # 每个供应商创建1个主联系人
                    contact_data = {
                        "name": f"供应商{sup_num}经理",
                        "position": "销售经理",
                        "mobile": f"137{sup_num.zfill(8)}",
                        "email": f"sales{sup_num}@test-supplier.com",
                        "is_primary": True,
                    }
                    SupplierContact.objects.get_or_create(
                        supplier=supplier,
                        name=contact_data["name"],
                        defaults={**contact_data, "created_by": test_user},
                    )
                    stats["supplier_contacts"] += 1

            # ========== 7. 创建产品（完整信息）==========
            default_unit = Unit.objects.first()
            default_brand = Brand.objects.first()

            if not all([default_unit, default_brand]):
                return False, "缺少必需的基础数据（计量单位/品牌）", stats

            # 按分类创建产品
            products_data = [
                # 激光切割机系列 (8个)
                {
                    "name": "测试激光切割机-1000W",
                    "code": "TEST_PROD001",
                    "category_code": "TEST_LASER_CUT",
                    "model": "LC-1000",
                    "specifications": "功率: 1000W, 切割厚度: 0-8mm, 工作台面: 1000x2000mm",
                    "description": "入门级激光切割机，适用于薄板切割",
                    "cost_price": Decimal("45000.00"),
                    "selling_price": Decimal("75000.00"),
                    "weight": Decimal("1800.00"),
                    "length": Decimal("250.00"),
                    "width": Decimal("180.00"),
                    "height": Decimal("150.00"),
                    "min_stock": 3,
                    "max_stock": 15,
                    "reorder_point": 5,
                    "warranty_period": 12,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光切割机-3000W",
                    "code": "TEST_PROD002",
                    "category_code": "TEST_LASER_CUT",
                    "model": "LC-3000",
                    "specifications": "功率: 3000W, 切割厚度: 0-20mm, 工作台面: 1300x2500mm",
                    "description": "高精度激光切割机，适用于金属板材切割",
                    "cost_price": Decimal("90000.00"),
                    "selling_price": Decimal("150000.00"),
                    "weight": Decimal("2500.00"),
                    "length": Decimal("300.00"),
                    "width": Decimal("200.00"),
                    "height": Decimal("180.00"),
                    "min_stock": 2,
                    "max_stock": 10,
                    "reorder_point": 3,
                    "warranty_period": 24,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光切割机-6000W",
                    "code": "TEST_PROD003",
                    "category_code": "TEST_LASER_CUT",
                    "model": "LC-6000",
                    "specifications": "功率: 6000W, 切割厚度: 0-30mm, 工作台面: 1500x3000mm",
                    "description": "重型激光切割机，适用于厚板切割",
                    "cost_price": Decimal("168000.00"),
                    "selling_price": Decimal("280000.00"),
                    "weight": Decimal("4500.00"),
                    "length": Decimal("400.00"),
                    "width": Decimal("300.00"),
                    "height": Decimal("220.00"),
                    "min_stock": 1,
                    "max_stock": 5,
                    "reorder_point": 2,
                    "warranty_period": 36,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光切割机-12000W",
                    "code": "TEST_PROD004",
                    "category_code": "TEST_LASER_CUT",
                    "model": "LC-12000",
                    "specifications": "功率: 12000W, 切割厚度: 0-50mm, 工作台面: 2000x4000mm",
                    "description": "超高功率激光切割机，工业级重型设备",
                    "cost_price": Decimal("320000.00"),
                    "selling_price": Decimal("550000.00"),
                    "weight": Decimal("7000.00"),
                    "length": Decimal("500.00"),
                    "width": Decimal("350.00"),
                    "height": Decimal("250.00"),
                    "min_stock": 1,
                    "max_stock": 3,
                    "reorder_point": 1,
                    "warranty_period": 48,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光切割机-2000W便携",
                    "code": "TEST_PROD005",
                    "category_code": "TEST_LASER_CUT",
                    "model": "LC-2000P",
                    "specifications": "功率: 2000W, 切割厚度: 0-12mm, 工作台面: 1200x2400mm",
                    "description": "便携式激光切割机，轻量化设计",
                    "cost_price": Decimal("65000.00"),
                    "selling_price": Decimal("110000.00"),
                    "weight": Decimal("2000.00"),
                    "length": Decimal("280.00"),
                    "width": Decimal("190.00"),
                    "height": Decimal("160.00"),
                    "min_stock": 2,
                    "max_stock": 12,
                    "reorder_point": 4,
                    "warranty_period": 18,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光切割机-4000W",
                    "code": "TEST_PROD006",
                    "category_code": "TEST_LASER_CUT",
                    "model": "LC-4000",
                    "specifications": "功率: 4000W, 切割厚度: 0-25mm, 工作台面: 1500x3000mm",
                    "description": "中高功率激光切割机，性价比高",
                    "cost_price": Decimal("125000.00"),
                    "selling_price": Decimal("210000.00"),
                    "weight": Decimal("3200.00"),
                    "length": Decimal("350.00"),
                    "width": Decimal("220.00"),
                    "height": Decimal("200.00"),
                    "min_stock": 2,
                    "max_stock": 8,
                    "reorder_point": 3,
                    "warranty_period": 30,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光切割机-8000W",
                    "code": "TEST_PROD007",
                    "category_code": "TEST_LASER_CUT",
                    "model": "LC-8000",
                    "specifications": "功率: 8000W, 切割厚度: 0-40mm, 工作台面: 1800x3500mm",
                    "description": "高端激光切割机，高效率生产",
                    "cost_price": Decimal("230000.00"),
                    "selling_price": Decimal("390000.00"),
                    "weight": Decimal("5500.00"),
                    "length": Decimal("450.00"),
                    "width": Decimal("320.00"),
                    "height": Decimal("230.00"),
                    "min_stock": 1,
                    "max_stock": 4,
                    "reorder_point": 1,
                    "warranty_period": 42,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光切割机-1500W精密",
                    "code": "TEST_PROD008",
                    "category_code": "TEST_LASER_CUT",
                    "model": "LC-1500P",
                    "specifications": "功率: 1500W, 切割厚度: 0-10mm, 工作台面: 1000x2000mm",
                    "description": "精密激光切割机，适用于精细加工",
                    "cost_price": Decimal("55000.00"),
                    "selling_price": Decimal("92000.00"),
                    "weight": Decimal("2100.00"),
                    "length": Decimal("260.00"),
                    "width": Decimal("185.00"),
                    "height": Decimal("155.00"),
                    "min_stock": 3,
                    "max_stock": 12,
                    "reorder_point": 4,
                    "warranty_period": 18,
                    "product_type": "finished",
                },
                # 激光焊接机系列 (7个)
                {
                    "name": "测试激光焊接机-1000W",
                    "code": "TEST_PROD009",
                    "category_code": "TEST_LASER_WELD",
                    "model": "LW-1000",
                    "specifications": "功率: 1000W, 焊接厚度: 0-3mm, 焊接速度: 0-80mm/s",
                    "description": "小功率激光焊接机，适用于薄板焊接",
                    "cost_price": Decimal("28000.00"),
                    "selling_price": Decimal("48000.00"),
                    "weight": Decimal("500.00"),
                    "length": Decimal("100.00"),
                    "width": Decimal("70.00"),
                    "height": Decimal("85.00"),
                    "min_stock": 5,
                    "max_stock": 20,
                    "reorder_point": 8,
                    "warranty_period": 12,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光焊接机-2000W",
                    "code": "TEST_PROD010",
                    "category_code": "TEST_LASER_WELD",
                    "model": "LW-2000",
                    "specifications": "功率: 2000W, 焊接厚度: 0-6mm, 焊接速度: 0-120mm/s",
                    "description": "便携式激光焊接机，适用于精密焊接",
                    "cost_price": Decimal("48000.00"),
                    "selling_price": Decimal("80000.00"),
                    "weight": Decimal("800.00"),
                    "length": Decimal("120.00"),
                    "width": Decimal("80.00"),
                    "height": Decimal("100.00"),
                    "min_stock": 3,
                    "max_stock": 15,
                    "reorder_point": 5,
                    "warranty_period": 18,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光焊接机-3000W",
                    "code": "TEST_PROD011",
                    "category_code": "TEST_LASER_WELD",
                    "model": "LW-3000",
                    "specifications": "功率: 3000W, 焊接厚度: 0-10mm, 焊接速度: 0-150mm/s",
                    "description": "高功率激光焊接机，适用于重工业焊接",
                    "cost_price": Decimal("72000.00"),
                    "selling_price": Decimal("120000.00"),
                    "weight": Decimal("1500.00"),
                    "length": Decimal("150.00"),
                    "width": Decimal("100.00"),
                    "height": Decimal("120.00"),
                    "min_stock": 2,
                    "max_stock": 10,
                    "reorder_point": 4,
                    "warranty_period": 24,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光焊接机-4000W",
                    "code": "TEST_PROD012",
                    "category_code": "TEST_LASER_WELD",
                    "model": "LW-4000",
                    "specifications": "功率: 4000W, 焊接厚度: 0-15mm, 焊接速度: 0-180mm/s",
                    "description": "超高功率激光焊接机，工业级设备",
                    "cost_price": Decimal("98000.00"),
                    "selling_price": Decimal("165000.00"),
                    "weight": Decimal("2000.00"),
                    "length": Decimal("180.00"),
                    "width": Decimal("120.00"),
                    "height": Decimal("140.00"),
                    "min_stock": 1,
                    "max_stock": 8,
                    "reorder_point": 3,
                    "warranty_period": 30,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光焊接机-1500W手持",
                    "code": "TEST_PROD013",
                    "category_code": "TEST_LASER_WELD",
                    "model": "LW-1500H",
                    "specifications": "功率: 1500W, 焊接厚度: 0-5mm, 焊接速度: 0-100mm/s",
                    "description": "手持式激光焊接机，灵活便携",
                    "cost_price": Decimal("38000.00"),
                    "selling_price": Decimal("65000.00"),
                    "weight": Decimal("650.00"),
                    "length": Decimal("110.00"),
                    "width": Decimal("75.00"),
                    "height": Decimal("90.00"),
                    "min_stock": 4,
                    "max_stock": 18,
                    "reorder_point": 6,
                    "warranty_period": 15,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光焊接机-2500W",
                    "code": "TEST_PROD014",
                    "category_code": "TEST_LASER_WELD",
                    "model": "LW-2500",
                    "specifications": "功率: 2500W, 焊接厚度: 0-8mm, 焊接速度: 0-135mm/s",
                    "description": "中功率激光焊接机，通用型设备",
                    "cost_price": Decimal("58000.00"),
                    "selling_price": Decimal("98000.00"),
                    "weight": Decimal("1100.00"),
                    "length": Decimal("135.00"),
                    "width": Decimal("90.00"),
                    "height": Decimal("110.00"),
                    "min_stock": 3,
                    "max_stock": 12,
                    "reorder_point": 5,
                    "warranty_period": 20,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光焊接机-3500W",
                    "code": "TEST_PROD015",
                    "category_code": "TEST_LASER_WELD",
                    "model": "LW-3500",
                    "specifications": "功率: 3500W, 焊接厚度: 0-12mm, 焊接速度: 0-165mm/s",
                    "description": "高端激光焊接机，高效稳定",
                    "cost_price": Decimal("85000.00"),
                    "selling_price": Decimal("142000.00"),
                    "weight": Decimal("1750.00"),
                    "length": Decimal("165.00"),
                    "width": Decimal("110.00"),
                    "height": Decimal("130.00"),
                    "min_stock": 2,
                    "max_stock": 9,
                    "reorder_point": 3,
                    "warranty_period": 27,
                    "product_type": "finished",
                },
                # 激光打标机系列 (5个)
                {
                    "name": "测试激光打标机-20W",
                    "code": "TEST_PROD016",
                    "category_code": "TEST_LASER_MARK",
                    "model": "LM-20",
                    "specifications": "功率: 20W, 标刻范围: 80x80mm, 标刻速度: ≤5000mm/s",
                    "description": "小功率激光打标机，适用于小型工件",
                    "cost_price": Decimal("8000.00"),
                    "selling_price": Decimal("15000.00"),
                    "weight": Decimal("100.00"),
                    "length": Decimal("50.00"),
                    "width": Decimal("45.00"),
                    "height": Decimal("60.00"),
                    "min_stock": 8,
                    "max_stock": 30,
                    "reorder_point": 12,
                    "warranty_period": 12,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光打标机-50W",
                    "code": "TEST_PROD017",
                    "category_code": "TEST_LASER_MARK",
                    "model": "LM-50",
                    "specifications": "功率: 50W, 标刻范围: 110x110mm, 标刻速度: ≤7000mm/s",
                    "description": "光纤激光打标机，适用于金属和部分塑料标记",
                    "cost_price": Decimal("15000.00"),
                    "selling_price": Decimal("25000.00"),
                    "weight": Decimal("150.00"),
                    "length": Decimal("60.00"),
                    "width": Decimal("50.00"),
                    "height": Decimal("70.00"),
                    "min_stock": 5,
                    "max_stock": 20,
                    "reorder_point": 8,
                    "warranty_period": 18,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光打标机-100W",
                    "code": "TEST_PROD018",
                    "category_code": "TEST_LASER_MARK",
                    "model": "LM-100",
                    "specifications": "功率: 100W, 标刻范围: 150x150mm, 标刻速度: ≤10000mm/s",
                    "description": "高功率激光打标机，高速深度打标",
                    "cost_price": Decimal("28000.00"),
                    "selling_price": Decimal("48000.00"),
                    "weight": Decimal("220.00"),
                    "length": Decimal("70.00"),
                    "width": Decimal("60.00"),
                    "height": Decimal("85.00"),
                    "min_stock": 3,
                    "max_stock": 15,
                    "reorder_point": 5,
                    "warranty_period": 24,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光打标机-30W便携",
                    "code": "TEST_PROD019",
                    "category_code": "TEST_LASER_MARK",
                    "model": "LM-30P",
                    "specifications": "功率: 30W, 标刻范围: 90x90mm, 标刻速度: ≤6000mm/s",
                    "description": "便携式激光打标机，轻便灵活",
                    "cost_price": Decimal("11000.00"),
                    "selling_price": Decimal("19000.00"),
                    "weight": Decimal("120.00"),
                    "length": Decimal("55.00"),
                    "width": Decimal("48.00"),
                    "height": Decimal("65.00"),
                    "min_stock": 6,
                    "max_stock": 25,
                    "reorder_point": 10,
                    "warranty_period": 15,
                    "product_type": "finished",
                },
                {
                    "name": "测试激光打标机-75W",
                    "code": "TEST_PROD020",
                    "category_code": "TEST_LASER_MARK",
                    "model": "LM-75",
                    "specifications": "功率: 75W, 标刻范围: 130x130mm, 标刻速度: ≤8500mm/s",
                    "description": "中高功率激光打标机，通用型设备",
                    "cost_price": Decimal("21000.00"),
                    "selling_price": Decimal("36000.00"),
                    "weight": Decimal("185.00"),
                    "length": Decimal("65.00"),
                    "width": Decimal("55.00"),
                    "height": Decimal("78.00"),
                    "min_stock": 4,
                    "max_stock": 18,
                    "reorder_point": 7,
                    "warranty_period": 20,
                    "product_type": "finished",
                },
            ]

            for prod_data in products_data:
                category_code = prod_data.pop("category_code")
                category = created_categories.get(category_code)

                _, created = Product.objects.get_or_create(
                    code=prod_data["code"],
                    is_deleted=False,
                    defaults={
                        **prod_data,
                        "unit": default_unit,
                        "category": category,
                        "brand": default_brand,
                        "status": "active",
                        "track_inventory": True,
                        "created_by": test_user,
                    },
                )
                if created:
                    stats["products"] += 1

            # 构建成功消息
            total_created = sum(stats.values())

            message = (
                f"✅ 测试数据添加完成！共创建 {total_created} 条记录\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "  📦 基础数据:\n"
                f'    • 计量单位: {stats["units_created"]} 个\n'
                f'    • 品牌: {stats["brands_created"]} 个\n'
                f'    • 产品分类: {stats["categories_created"]} 个\n'
                f'    • 仓库: {stats["warehouses_created"]} 个\n'
                "  👥 客户数据:\n"
                f'    • 客户: {stats["customers"]} 家\n'
                f'    • 客户联系人: {stats["customer_contacts"]} 个\n'
                "  🏭 供应商数据:\n"
                f'    • 供应商: {stats["suppliers"]} 家\n'
                f'    • 供应商联系人: {stats["supplier_contacts"]} 个\n'
                "  🔧 产品数据:\n"
                f'    • 产品: {stats["products"]} 个\n'
                f'    • 税率: {stats["tax_rates_created"]} 个'
            )

            return True, message, stats

        except Exception as e:
            import traceback

            error_detail = traceback.format_exc()
            return False, f"❌ 添加测试数据失败: {str(e)}\n\n详细信息:\n{error_detail}", stats

    @staticmethod
    def reset_auto_increment():
        """
        重置数据库自增ID（重置所有业务表的自增ID）
        返回: (success, message)
        """
        try:
            # 需要重置ID的表列表（按模块分组）
            tables = [
                # 用户相关
                "users_user",
                "users_user_profile",
                "users_role",
                "users_permission",
                "users_login_log",
                # 客户相关
                "customers_customer",
                "customers_contact",
                "customers_address",
                "customers_category",
                "customers_credit_history",
                "customers_visit",
                # 供应商相关
                "suppliers_supplier",
                "suppliers_contact",
                "suppliers_category",
                "suppliers_product",
                "suppliers_evaluation",
                # 产品相关
                "products_product",
                "products_brand",
                "products_category",
                "products_unit",
                "products_attribute",
                "products_attribute_value",
                "products_price_history",
                "products_image",
                # 销售相关
                "sales_quote",
                "sales_quote_item",
                "sales_order",
                "sales_order_item",
                "sales_delivery",
                "sales_delivery_item",
                "sales_return",
                "sales_return_item",
                # 采购相关
                "purchase_request",
                "purchase_request_item",
                "purchase_inquiry",
                "purchase_inquiry_item",
                "purchase_order",
                "purchase_order_item",
                "purchase_receipt",
                "purchase_receipt_item",
                "purchase_return",
                "purchase_return_item",
                "supplier_quotation",
                "supplier_quotation_item",
                "purchase_borrow",
                "purchase_borrow_item",
                # 库存相关
                "inventory_stock",
                "inventory_warehouse",
                "inventory_location",
                "inventory_adjustment",
                "inventory_count",
                "inventory_count_item",
                "inventory_count_counters",
                "inventory_inbound_order",
                "inventory_inbound_order_item",
                "inventory_outbound_order",
                "inventory_outbound_order_item",
                "inventory_transfer",
                "inventory_transfer_item",
                "inventory_transaction",
                # 财务相关
                "finance_customer_account",
                "finance_supplier_account",
                "finance_customer_prepayment",
                "finance_supplier_prepayment",
                "finance_tax_rate",
                "finance_invoice",
                "finance_invoice_item",
                "finance_payment",
                "finance_account",
                "finance_journal",
                "finance_journal_entry",
                "finance_budget",
                "finance_budget_line",
                "finance_financial_report",
                # 部门相关
                "departments_department",
                "departments_position",
                "departments_budget",
                # 核心相关
                "core_company",
                "core_system_config",
                "core_notification",
                "core_audit_log",
                "core_attachment",
                "core_document_number_sequence",
                "core_print_template",
                "core_default_template_mapping",
                "core_choice_option_group",
                "core_choice_option",
                # 质检相关
                "quality_inspection",
                "quality_inspection_item",
                "quality_inspection_template",
                "non_conforming_product",
            ]

            with connection.cursor() as cursor:
                if DatabaseHelper.is_sqlite():
                    # SQLite：删除 sqlite_sequence 表中的记录
                    for table in tables:
                        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                    return True, "SQLite 自增ID已重置"

                elif DatabaseHelper.is_mysql():
                    # MySQL：重置 AUTO_INCREMENT
                    for table in tables:
                        try:
                            cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
                        except Exception:
                            # 忽略不存在的表
                            pass
                    return True, "MySQL 自增ID已重置"

                else:
                    return False, "不支持的数据库类型"

        except Exception as e:
            return False, f"重置ID失败: {str(e)}"

    @staticmethod
    def clear_test_data():
        """
        清除测试数据（保留基础配置）并重置ID
        步骤：
        1. 硬删除所有已软删除的数据（释放唯一约束）
        2. 软删除当前所有数据
        3. 重置自增ID
        4. 重置单据号序列（下次创建单据将从001开始）
        返回: (success, message, stats)
        """
        try:
            stats = {
                "customers": 0,
                "suppliers": 0,
                "products": 0,
                "sales_quotes": 0,
                "sales_orders": 0,
                "deliveries": 0,
                "sales_returns": 0,
                "purchase_inquiries": 0,
                "purchase_requests": 0,
                "purchase_orders": 0,
                "purchase_receipts": 0,
                "purchase_returns": 0,
                "purchase_borrows": 0,
                "customer_accounts": 0,
                "supplier_accounts": 0,
                "inventory_stocks": 0,
                "units": 0,
                "brands": 0,
                "categories": 0,
                "warehouses": 0,
                "locations": 0,
                "tax_rates": 0,
                "document_sequences": 0,
                "journals": 0,
                "financial_reports": 0,
            }

            # 导入模型
            from core.models import DocumentNumberSequence
            from customers.models import Customer
            from finance.models import (
                CustomerAccount,
                FinancialReport,
                Journal,
                SupplierAccount,
                TaxRate,
            )
            from inventory.models import InventoryStock, Location, Warehouse
            from products.models import Brand, Product, ProductCategory, Unit
            from purchase.models import (
                Borrow,
                PurchaseInquiry,
                PurchaseOrder,
                PurchaseReceipt,
                PurchaseRequest,
                PurchaseRequestItem,
                PurchaseReturn,
            )
            from sales.models import Delivery, Quote, SalesOrder, SalesReturn
            from suppliers.models import Supplier

            # 步骤1: 硬删除所有已软删除的数据（释放唯一约束）
            # 遍历每个对象并调用 hard_delete 方法
            for customer in Customer.objects.filter(is_deleted=True):
                customer.hard_delete()
            for supplier in Supplier.objects.filter(is_deleted=True):
                supplier.hard_delete()
            for product in Product.objects.filter(is_deleted=True):
                product.hard_delete()
            for quote in Quote.objects.filter(is_deleted=True):
                quote.hard_delete()
            for order in SalesOrder.objects.filter(is_deleted=True):
                order.hard_delete()
            for delivery in Delivery.objects.filter(is_deleted=True):
                delivery.hard_delete()
            for ret in SalesReturn.objects.filter(is_deleted=True):
                ret.hard_delete()
            for request in PurchaseRequest.objects.filter(is_deleted=True):
                request.hard_delete()
            for request_item in PurchaseRequestItem.objects.filter(is_deleted=True):
                request_item.hard_delete()
            for order in PurchaseOrder.objects.filter(is_deleted=True):
                order.hard_delete()
            for ret in PurchaseReturn.objects.filter(is_deleted=True):
                ret.hard_delete()
            for inquiry in PurchaseInquiry.objects.filter(is_deleted=True):
                inquiry.hard_delete()
            for receipt in PurchaseReceipt.objects.filter(is_deleted=True):
                receipt.hard_delete()
            for borrow in Borrow.objects.filter(is_deleted=True):
                borrow.hard_delete()
            for account in CustomerAccount.objects.filter(is_deleted=True):
                account.hard_delete()
            for account in SupplierAccount.objects.filter(is_deleted=True):
                account.hard_delete()

            # 步骤2: 软删除当前所有数据并统计
            stats["customers"] = Customer.objects.filter(is_deleted=False).count()
            Customer.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["suppliers"] = Supplier.objects.filter(is_deleted=False).count()
            Supplier.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["products"] = Product.objects.filter(is_deleted=False).count()
            Product.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["sales_quotes"] = Quote.objects.filter(is_deleted=False).count()
            Quote.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["sales_orders"] = SalesOrder.objects.filter(is_deleted=False).count()
            SalesOrder.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["deliveries"] = Delivery.objects.filter(is_deleted=False).count()
            Delivery.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["sales_returns"] = SalesReturn.objects.filter(is_deleted=False).count()
            SalesReturn.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["purchase_requests"] = PurchaseRequest.objects.filter(is_deleted=False).count()
            PurchaseRequest.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["purchase_orders"] = PurchaseOrder.objects.filter(is_deleted=False).count()
            PurchaseOrder.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["purchase_returns"] = PurchaseReturn.objects.filter(is_deleted=False).count()
            PurchaseReturn.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["purchase_inquiries"] = PurchaseInquiry.objects.filter(is_deleted=False).count()
            PurchaseInquiry.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["purchase_receipts"] = PurchaseReceipt.objects.filter(is_deleted=False).count()
            PurchaseReceipt.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["purchase_borrows"] = Borrow.objects.filter(is_deleted=False).count()
            Borrow.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["customer_accounts"] = CustomerAccount.objects.filter(is_deleted=False).count()
            CustomerAccount.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["supplier_accounts"] = SupplierAccount.objects.filter(is_deleted=False).count()
            SupplierAccount.objects.filter(is_deleted=False).update(is_deleted=True)

            stats["inventory_stocks"] = InventoryStock.objects.count()
            InventoryStock.objects.all().delete()  # 库存直接删除

            # 基础数据硬删除（释放唯一性约束）
            stats["units"] = Unit.objects.filter(is_deleted=False).count()
            Unit.objects.all().delete()  # 硬删除所有计量单位

            stats["brands"] = Brand.objects.filter(is_deleted=False).count()
            Brand.objects.all().delete()  # 硬删除所有品牌

            stats["categories"] = ProductCategory.objects.filter(is_deleted=False).count()
            ProductCategory.objects.all().delete()  # 硬删除所有产品分类

            stats["locations"] = Location.objects.filter(is_deleted=False).count()
            Location.objects.all().delete()  # 硬删除所有库位

            stats["warehouses"] = Warehouse.objects.filter(is_deleted=False).count()
            Warehouse.objects.all().delete()  # 硬删除所有仓库

            stats["tax_rates"] = TaxRate.objects.filter(is_deleted=False).count()
            TaxRate.objects.all().delete()  # 硬删除所有税率

            # 财务报表和会计凭证数据
            stats["journals"] = Journal.objects.filter(is_deleted=False).count()
            Journal.objects.filter(is_deleted=False).update(is_deleted=True)
            # JournalEntry会通过外键级联删除

            stats["financial_reports"] = FinancialReport.objects.filter(is_deleted=False).count()
            FinancialReport.objects.filter(is_deleted=False).update(is_deleted=True)

            # 步骤3: 重置自增ID
            reset_success, reset_msg = DatabaseHelper.reset_auto_increment()
            id_reset_info = f"，{reset_msg}" if reset_success else ""

            # 步骤4: 重置单据号序列
            stats["document_sequences"] = DocumentNumberSequence.objects.count()
            DocumentNumberSequence.objects.all().delete()  # 删除所有单据号序列记录

            total_cleared = sum(stats.values())
            message = (
                f"已清除 {total_cleared} 条数据（"
                f'客户: {stats["customers"]}, '
                f'供应商: {stats["suppliers"]}, '
                f'产品: {stats["products"]}, '
                f'报价单: {stats["sales_quotes"]}, '
                f'销售订单: {stats["sales_orders"]}, '
                f'发货单: {stats["deliveries"]}, '
                f'销售退货: {stats["sales_returns"]}, '
                f'采购询价: {stats["purchase_inquiries"]}, '
                f'采购申请: {stats["purchase_requests"]}, '
                f'采购订单: {stats["purchase_orders"]}, '
                f'采购收货: {stats["purchase_receipts"]}, '
                f'采购退货: {stats["purchase_returns"]}, '
                f'采购借用: {stats["purchase_borrows"]}, '
                f'应收账款: {stats["customer_accounts"]}, '
                f'应付账款: {stats["supplier_accounts"]}, '
                f'库存: {stats["inventory_stocks"]}, '
                f'单位: {stats.get("units", 0)}, '
                f'品牌: {stats.get("brands", 0)}, '
                f'分类: {stats.get("categories", 0)}, '
                f'仓库: {stats.get("warehouses", 0)}, '
                f'库位: {stats.get("locations", 0)}, '
                f'税率: {stats.get("tax_rates", 0)}, '
                f'会计凭证: {stats["journals"]}, '
                f'财务报表: {stats["financial_reports"]}, '
                f'单据号序列: {stats["document_sequences"]}'
                f"）{id_reset_info}，单据号已重置，下次创建将从001开始"
            )

            return True, message, stats

        except Exception as e:
            return False, f"清除数据失败: {str(e)}", {}
