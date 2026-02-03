[根目录](../../../CLAUDE.md) > [django_erp](../../) > [apps](../) > **products**

# Products模块文档

## 模块职责

Products模块负责产品信息管理，是ERP系统的基础数据模块之一。主要职责包括：

- **产品信息管理**: 产品基础信息、规格参数、图片等维护
- **分类体系管理**: 层级化的产品分类和目录管理 
- **品牌管理**: 产品品牌信息和品牌关联
- **定价体系**: 产品价格管理和价格策略
- **库存基础**: 为库存管理提供产品基础数据
- **销售支持**: 为销售流程提供产品数据支撑

## 入口与启动

### 模型文件
- **主文件**: `models.py`
- **核心模型**:
  - `Product` - 产品主表
  - `ProductCategory` - 产品分类（树形结构）
  - `Brand` - 品牌信息
  - `Unit` - 计量单位

### 视图入口
- **文件**: `views.py`
- **功能**: Django模板视图和CRUD操作

### URL配置
- **路由文件**: `urls.py`
- **命名空间**: `products`

### 管理命令
- **初始化命令**: `management/commands/init_base_data.py`
- **功能**: 初始化基础数据（分类、品牌、单位等）

## 对外接口

### 前端页面路由
```python
path('', views.product_list, name='product_list')                       # 产品列表
path('create/', views.product_create, name='product_create')            # 创建产品
path('<int:pk>/', views.product_detail, name='product_detail')          # 产品详情
path('<int:pk>/edit/', views.product_update, name='product_update')     # 编辑产品
path('<int:pk>/delete/', views.product_delete, name='product_delete')   # 删除产品
```

### API接口
暂时通过Django视图提供数据，未来可扩展REST API。

## 关键依赖与配置

### 内部模块依赖
```python
from apps.core.models import BaseModel                    # 基础模型
from django.contrib.auth import get_user_model           # 用户模型
from mptt.models import MPTTModel, TreeForeignKey        # 树形结构模型
```

### 外部依赖
```python
from django.core.validators import MinValueValidator      # 最小值验证器
from decimal import Decimal                              # 精确小数计算
```

### 树形结构配置
```python
# 使用django-mptt实现产品分类的层级结构
class ProductCategory(MPTTModel, BaseModel):
    class MPTTMeta:
        order_insertion_by = ['sort_order', 'name']      # 排序规则
```

## 数据模型

### ProductCategory (产品分类)
```python
class ProductCategory(MPTTModel, BaseModel):
    name = CharField('分类名称', max_length=100)                # 分类名称
    code = CharField('分类代码', max_length=50, unique=True)    # 分类代码
    parent = TreeForeignKey('self', on_delete=CASCADE, null=True) # 父分类
    description = TextField('分类描述', blank=True)             # 描述
    image = ImageField('分类图片', upload_to='categories/')     # 分类图片
    sort_order = PositiveIntegerField('排序', default=0)       # 排序
    is_active = BooleanField('是否启用', default=True)         # 状态
```

**特性**:
- **层级结构**: 支持无限层级的分类体系
- **自动排序**: 按排序字段和名称自动排序
- **路径显示**: `full_name` 属性显示完整分类路径
- **图片支持**: 分类可关联图片

### Brand (品牌)
```python
class Brand(BaseModel):
    name = CharField('品牌名称', max_length=100, unique=True)   # 品牌名称
    code = CharField('品牌代码', max_length=50, unique=True)    # 品牌代码
    description = TextField('品牌描述', blank=True)             # 品牌描述
    logo = ImageField('品牌Logo', upload_to='brands/')         # 品牌Logo
    website = URLField('官方网站', blank=True)                  # 官网
    country = CharField('国家/地区', max_length=50, blank=True) # 国家
    is_active = BooleanField('是否启用', default=True)         # 状态
```

**用途**:
- 品牌信息管理
- 产品品牌关联
- 品牌统计分析
- 供应商品牌授权

### Unit (计量单位)
```python  
class Unit(BaseModel):
    name = CharField('单位名称', max_length=50, unique=True)    # 单位名称
    symbol = CharField('单位符号', max_length=20, unique=True)  # 单位符号
    description = TextField('单位描述', blank=True)             # 描述
    is_active = BooleanField('是否启用', default=True)         # 状态
```

**常见单位**:
- 件、个、台、套
- 米、厘米、毫米
- 公斤、克、吨
- 升、毫升

### Product (产品主表)
```python
class Product(BaseModel):
    # 基础信息
    name = CharField('产品名称', max_length=200)                # 产品名称
    code = CharField('产品编码', max_length=100, unique=True)   # 产品编码
    barcode = CharField('条形码', max_length=100, unique=True)  # 条形码
    
    # 分类关联
    category = ForeignKey(ProductCategory, on_delete=SET_NULL)  # 产品分类
    brand = ForeignKey(Brand, on_delete=SET_NULL)              # 品牌
    
    # 规格信息
    model = CharField('型号', max_length=100, blank=True)       # 产品型号
    specifications = TextField('规格参数', blank=True)          # 规格参数
    description = TextField('产品描述', blank=True)             # 产品描述
    
    # 计量单位
    unit = ForeignKey(Unit, on_delete=PROTECT)                 # 基本单位
    
    # 定价信息
    standard_cost = DecimalField('标准成本', max_digits=10, decimal_places=2, default=0)
    list_price = DecimalField('标准售价', max_digits=10, decimal_places=2, default=0)
    min_price = DecimalField('最低售价', max_digits=10, decimal_places=2, default=0)
    
    # 库存参数
    min_stock_level = PositiveIntegerField('最低库存', default=0)    # 安全库存
    max_stock_level = PositiveIntegerField('最高库存', default=0)    # 最大库存
    reorder_point = PositiveIntegerField('再订货点', default=0)      # 再订货点
    
    # 产品特性
    is_serialized = BooleanField('是否序列号管理', default=False)    # 序列号管理
    is_active = BooleanField('是否启用', default=True)              # 产品状态
    is_purchased = BooleanField('可采购', default=True)             # 采购标记
    is_sold = BooleanField('可销售', default=True)                  # 销售标记
    is_manufactured = BooleanField('可生产', default=False)         # 生产标记
    
    # 图片和附件
    image = ImageField('产品图片', upload_to='products/', blank=True) # 主图
    
    # 其他信息
    weight = DecimalField('重量(kg)', max_digits=8, decimal_places=3, null=True, blank=True)
    dimensions = CharField('尺寸', max_length=100, blank=True)       # 长宽高
    color = CharField('颜色', max_length=50, blank=True)             # 颜色
    material = CharField('材质', max_length=100, blank=True)         # 材质
    origin = CharField('产地', max_length=100, blank=True)           # 产地
```

## 业务特性

### 1. 层级分类管理
- **树形结构**: 使用MPTT实现无限层级分类
- **路径展示**: 自动生成分类路径（如：电子产品 > 计算机 > 笔记本）
- **批量操作**: 支持分类的批量移动和编辑

### 2. 产品编码体系
- **唯一编码**: 系统强制产品编码唯一性
- **条形码管理**: 支持标准条形码和自定义编码
- **编码规则**: 可配置编码生成规则

### 3. 多维度定价
- **成本价格**: 标准成本用于盈利分析
- **标准售价**: 默认销售价格
- **价格区间**: 最低价格控制销售底线

### 4. 库存参数设置
- **安全库存**: 最低/最高库存水位
- **补货提醒**: 再订货点触发采购提醒
- **库存策略**: 支持不同的库存管理策略

### 5. 产品特性标记
- **业务标记**: 可采购/可销售/可生产标记
- **序列号管理**: 高价值产品的序列号跟踪
- **状态管理**: 产品启用/停用状态

## Admin管理界面

### 产品管理
```python
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'brand', 'list_price', 'is_active']
    list_filter = ['category', 'brand', 'is_active', 'is_purchased', 'is_sold']
    search_fields = ['code', 'name', 'barcode']
    readonly_fields = ['created_at', 'updated_at']
```

### 分类管理
```python
@admin.register(ProductCategory) 
class ProductCategoryAdmin(MPTTModelAdmin):
    list_display = ['name', 'code', 'parent', 'is_active']
    search_fields = ['name', 'code']
```

## 页面模板

```
templates/products/
├── product_list.html            # 产品列表页面
├── product_form.html            # 产品编辑表单
├── product_detail.html          # 产品详情页面
└── product_confirm_delete.html  # 删除确认页面
```

## 测试与质量

### 测试文件位置
```bash
apps/products/tests/  # 测试目录 (需要创建)
```

### 测试覆盖缺口
- ❌ 缺少模型测试
- ❌ 缺少视图测试
- ❌ 缺少分类树形结构测试
- ❌ 缺少价格验证测试

### 建议测试重点
1. **产品编码唯一性**: 确保产品编码和条形码不重复
2. **分类树形结构**: 测试MPTT树形操作的正确性
3. **价格验证**: 确保最低价格不超过标准售价
4. **库存参数**: 验证库存水位设置的合理性
5. **产品状态**: 测试产品启用/停用的业务逻辑

## 常见问题 (FAQ)

### Q: 如何批量导入产品信息？
A: 可以通过Django Admin的批量操作或编写自定义管理命令进行批量导入。

### Q: 产品分类可以有多少层级？
A: 理论上无限制，但建议控制在3-4层以内，便于管理和使用。

### Q: 如何处理产品的多图片需求？
A: 当前只支持一张主图，多图片需求可以通过附件系统(Attachment)实现。

### Q: 产品价格支持多货币吗？
A: 当前版本只支持单一货币，多货币功能需要扩展开发。

### Q: 如何设置产品的序列号管理？
A: 通过产品的 `is_serialized` 字段标记，具体的序列号跟踪在库存模块中实现。

## 相关文件清单

### 核心文件
- `__init__.py` - 包初始化
- `apps.py` - Django应用配置
- `models.py` - 数据模型定义 (约300行)
- `views.py` - 业务视图逻辑
- `urls.py` - URL路由配置
- `admin.py` - Admin后台配置

### 管理命令
- `management/commands/__init__.py` - 命令包初始化
- `management/commands/init_base_data.py` - 基础数据初始化命令

### 数据库迁移
- `migrations/` - 数据库迁移文件
  - `0001_initial.py` - 初始迁移
  - `0002_initial.py` - 补充迁移

### 模板文件
- `templates/products/` - 4个HTML模板文件

## 与其他模块的集成

### 销售模块 (Sales)
- 提供产品信息用于报价和订单
- 产品价格和成本信息
- 产品规格和描述

### 库存模块 (Inventory)
- 产品库存管理的基础数据
- 库存水位设置参数
- 序列号管理标记

### 采购模块 (Purchase)
- 采购订单的产品选择
- 产品成本信息
- 供应商产品关联

### 生产模块 (Production)
- 生产计划的产品信息
- 物料清单(BOM)基础
- 生产标记识别

## 扩展功能建议

### 近期扩展
1. **产品规格参数化**: 结构化的产品规格管理
2. **多图片支持**: 产品多角度图片展示
3. **产品变体**: 颜色、尺寸等��体管理
4. **价格历史**: 价格变更历史记录

### 长期扩展
1. **多货币定价**: 支持不同市场的货币定价
2. **客户专用价**: 针对特定客户的专用价格
3. **促销价格**: 时间段促销价格管理
4. **产品套装**: 产品组合和套装管理

## 测试与质量

### 测试文件位置
```bash
apps/products/tests/
├── __init__.py
└── test_models.py  # 产品模型测试
```

### 测试覆盖情况
✅ **测试完成度: 100%** (27/27 测试通过)

#### ProductCategory模型测试 (6个测试)
- ✅ `test_category_creation` - 分类创建
- ✅ `test_category_hierarchy` - 层级关系(MPTT)
- ✅ `test_category_unique_code` - 分类代码唯一性
- ✅ `test_category_full_name` - 完整路径名称
- ✅ `test_category_ordering` - 树形排序
- ✅ `test_category_str_representation` - 字符串表示

#### Brand模型测试 (4个测试)
- ✅ `test_brand_creation` - 品牌创建
- ✅ `test_brand_unique_name` - 品牌名称唯一性
- ✅ `test_brand_ordering` - 排序规则
- ✅ `test_brand_str_representation` - 字符串表示

#### Unit模型测试 (4个测试)
- ✅ `test_unit_creation` - 计量单位创建
- ✅ `test_unit_unique_fields` - 唯一性约束
- ✅ `test_unit_ordering` - 排序规则
- ✅ `test_unit_str_representation` - 字符串表示

#### Product模型测试 (13个测试)
- ✅ `test_product_creation` - 产品创建
- ✅ `test_product_unique_code` - 产品编码唯一性
- ✅ `test_product_with_category` - 分类关联
- ✅ `test_product_with_brand` - 品牌关联
- ✅ `test_product_with_unit` - 单位关联
- ✅ `test_product_price_fields` - 价格字段验证
- ✅ `test_product_stock_fields` - 库存字段验证
- ✅ `test_product_profit_margin` - 利润率计算
- ✅ `test_product_is_low_stock` - 低库存判断
- ✅ `test_product_is_out_of_stock` - 缺货判断
- ✅ `test_product_soft_delete` - 软删除功能
- ✅ `test_product_ordering` - 排序规则
- ✅ `test_product_str_representation` - 字符串表示

### 测试要点
- **MPTT树形结构**: 产品分类的层级管理和查询
- **计算属性**: profit_margin、is_low_stock、is_out_of_stock等业务逻辑
- **唯一性约束**: 产品编码、品牌名称、单位名称等
- **价格字段**: DecimalField精度处理
- **关联关系**: 分类、品牌、单位的外键关联
- **软删除**: BaseModel的软删除功能继承

## 变更记录 (Changelog)

### 2025-11-13
- **测试完成**: 添加27个单元测试，覆盖4个核心模型
- **测试通过率**: 100% (27/27)
- **测试内容**: ProductCategory(MPTT)、Brand、Unit、Product

### 2025-11-08 23:26:47
- **文档初始化**: 创建Products模块完整文档
- **模型分析**: 详细分析了4个核心模型的设计和关系
- **特性识别**: 识别了分类管理、定价体系、库存参数等关键特性
- **集成分析**: 梳理了与销售、库存、采购等模块的集成关系
- **扩展规划**: 提出了近期和长期的功能扩展建议