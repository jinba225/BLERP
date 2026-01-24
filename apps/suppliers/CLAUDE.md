[根目录](../../../CLAUDE.md) > [django_erp](../../) > [apps](../) > **suppliers**

# Suppliers模块文档

## 模块职责

Suppliers模块负责供应商关系管理。主要职责包括：
- **供应商信息管理**: 供应商基础信息和联系方式
- **供应商分类**: 供应商类型和等级管理
- **采购支持**: 为采购流程提供供应商数据

## 核心模型
```python
class Supplier(BaseModel):
    name = CharField('供应商名称', max_length=200)
    code = CharField('供应商编码', max_length=100, unique=True)
    contact_person = CharField('联系人', max_length=100)
    phone = CharField('电话', max_length=20)
    email = EmailField('邮箱', blank=True)
    address = TextField('地址', blank=True)
    payment_terms = CharField('付款条件', max_length=50)
    credit_rating = CharField('信用等级', max_length=1, choices=CREDIT_RATINGS)
    is_active = BooleanField('是否启用', default=True)
```

## 主要功能
- ✅ 供应商基础信息管理
- ✅ 联系方式管理
- ✅ 信用等级评估
- ⚠️ 需要完善供应商评估体系

## 页面模板
- `supplier_list.html` - 供应商列表
- `supplier_form.html` - 供应商表单
- `supplier_detail.html` - 供应商详情
- `supplier_confirm_delete.html` - 删除确认

## 集成关系
- **Purchase**: 采购订单的供应商选择
- **Products**: 供应商产品关联

## 测试与质量

### 测试文件位置
```bash
apps/suppliers/tests/
├── __init__.py
└── test_models.py  # 供应商模型测试
```

### 测试覆盖情况
✅ **测试完成度: 100%** (24/24 测试通过)

#### Supplier模型测试 (7个测试)
- ✅ `test_supplier_creation` - 供应商创建
- ✅ `test_supplier_unique_code` - 供应商编码唯一性
- ✅ `test_supplier_credit_ratings` - 所有信用等级验证
- ✅ `test_supplier_average_rating` - 平均评分计算
- ✅ `test_supplier_soft_delete` - 软删除功能
- ✅ `test_supplier_ordering` - 排序规则
- ✅ `test_supplier_str_representation` - 字符串表示

#### SupplierContact模型测试 (3个测试)
- ✅ `test_contact_creation` - 联系人创建
- ✅ `test_contact_ordering` - 排序规则
- ✅ `test_contact_str_representation` - 字符串表示

#### SupplierProduct模型测试 (4个测试)
- ✅ `test_supplier_product_creation` - 供应商产品关联创建
- ✅ `test_supplier_product_price_fields` - 价格字段验证
- ✅ `test_supplier_product_ordering` - 排序规则
- ✅ `test_supplier_product_str_representation` - 字符串表示

#### SupplierEvaluation模型测试 (7个测试)
- ✅ `test_evaluation_creation` - 评估创建
- ✅ `test_evaluation_scores_range` - 分数范围验证(0-100)
- ✅ `test_evaluation_overall_score_calculation` - 总分自动计算
- ✅ `test_evaluation_ordering` - 按评估日期倒序
- ✅ `test_evaluation_str_representation` - 字符串表示
- ✅ `test_evaluation_decimal_precision` - Decimal精度处理
- ✅ `test_supplier_average_rating_with_evaluations` - 供应商平均评分

#### PurchaseHistory模型测试 (3个测试)
- ✅ `test_purchase_history_creation` - 采购历史创建
- ✅ `test_purchase_history_ordering` - 按采购日期倒序
- ✅ `test_purchase_history_str_representation` - 字符串表示

### 测试要点
- **信用等级**: 所有等级(A/B/C/D/E)的验证
- **评分计算**: 加权平均分自动计算 (质量30% + 交付30% + 服务20% + 价格20%)
- **Decimal精度**: DecimalField与Decimal类型的正确使用
- **唯一性约束**: 供应商编码的唯一性
- **排序规则**: 各模型的默认排序
- **软删除**: BaseModel的软删除功能

### 已修复的Bug
- **DecimalField类型错误**: 修复了SupplierEvaluation.save()中DecimalField与float混合运算的类型错误，统一使用Decimal('0.3')等形式

## 变更记录
### 2025-11-13
- **测试完成**: 添加24个单元测试，覆盖5个核心模型
- **测试通过率**: 100% (24/24)
- **测试内容**: Supplier、SupplierContact、SupplierProduct、SupplierEvaluation、PurchaseHistory
- **Bug修复**: SupplierEvaluation模型的DecimalField类型处理

### 2025-11-08 23:26:47
- 文档初始化，识别基础供应商管理功能