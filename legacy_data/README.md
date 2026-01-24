# 数据迁移文件说明

此目录包含从原始ERP系统导出的数据文件，用于迁移到新的Django ERP系统。

## 文件格式

所有数据文件都应该是UTF-8编码的CSV格式，第一行为列标题。

## 必需文件

### 1. users.csv - 用户数据
```csv
username,email,first_name,last_name,employee_id,phone,is_active
admin,admin@company.com,管理员,,EMP001,13800138000,true
user1,user1@company.com,张,三,EMP002,13800138001,true
```

### 2. departments.csv - 部门数据
```csv
code,name,description,phone,email,address,is_active
DEPT001,总经理办公室,公司最高管理部门,021-12345678,ceo@company.com,上海市浦东新区,true
DEPT002,销售部,负责产品销售,021-12345679,sales@company.com,上海市浦东新区,true
```

### 3. customer_categories.csv - 客户分类
```csv
code,name,description,discount_rate
CAT001,重点客户,公司重点客户,5.00
CAT002,普通客户,一般客户,0.00
```

### 4. customers.csv - 客户数据
```csv
code,name,customer_type,category_code,level,contact_person,phone,mobile,email,address,city,province,tax_number,credit_limit,is_active
CUS001,上海激光科技有限公司,enterprise,CAT001,A,张经理,021-12345678,13800138000,zhang@laser.com,上海市浦东新区张江路100号,上海,上海,91310000123456789X,1000000.00,true
```

### 5. supplier_categories.csv - 供应商分类
```csv
code,name,description
SUP_CAT001,原材料供应商,提供生产原材料
SUP_CAT002,设备供应商,提供生产设备
```

### 6. suppliers.csv - 供应商数据
```csv
code,name,supplier_type,category_code,level,contact_person,phone,mobile,email,address,city,province,tax_number,payment_terms,lead_time,is_active
SUP001,北京钢材有限公司,manufacturer,SUP_CAT001,A,李经理,010-12345678,13900139000,li@steel.com,北京市朝阳区工业路200号,北京,北京,91110000123456789Y,月结30天,7,true
```

### 7. units.csv - 计量单位
```csv
symbol,name,unit_type,conversion_factor
个,个,quantity,1.0000
台,台,quantity,1.0000
kg,千克,weight,1.0000
m,米,length,1.0000
```

### 8. brands.csv - 品牌数据
```csv
code,name,description,country
BRAND001,BetterLaser,自主品牌激光设备,中国
BRAND002,IPG,进口激光器品牌,美国
```

### 9. product_categories.csv - 产品分类
```csv
code,name,description
PROD_CAT001,激光切割机,用于金属切割的激光设备
PROD_CAT002,激光焊接机,用于金属焊接的激光设备
```

### 10. products.csv - 产品数据
```csv
code,name,product_type,category_code,brand_code,base_unit_symbol,description,specifications,model,cost_price,purchase_price,sales_price,min_stock,max_stock,status,is_active
PROD001,1000W光纤激光切割机,finished,PROD_CAT001,BRAND001,台,高精度光纤激光切割机,切割厚度0.1-10mm,BL-1000,80000.00,85000.00,120000.00,2.0000,10.0000,active,true
```

## 使用方法

1. 将原始ERP系统的数据导出为上述格式的CSV文件
2. 将文件放置在此目录中
3. 运行迁移命令：

```bash
# 迁移所有数据
python manage.py migrate_legacy_data --data-dir legacy_data

# 只迁移特定模块
python manage.py migrate_legacy_data --data-dir legacy_data --module customers

# 干运行（不保存数据，只检查格式）
python manage.py migrate_legacy_data --data-dir legacy_data --dry-run
```

## 注意事项

1. 确保CSV文件使用UTF-8编码
2. 日期格式使用 YYYY-MM-DD
3. 布尔值使用 true/false
4. 数字字段不要包含千分位分隔符
5. 外键字段使用对应的code值
6. 迁移前请备份现有数据库