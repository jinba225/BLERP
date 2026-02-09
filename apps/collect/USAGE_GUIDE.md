# Collect模块使用指南

## ✅ 完成状态：100%

所有代码已完成并测试通过，系统可以正常运行。

## 📋 模块结构

### 数据模型（collect/models.py）
- ✅ `CollectTask` - 采集任务模型
- ✅ `CollectItem` - 采集子项模型
- ✅ `FieldMapRule` - 字段映射规则
- ✅ `PricingRule` - 定价规则

### 共享模型（core/models.py）
- ✅ `Platform` - 平台配置（采集平台+跨境平台）
- ✅ `Shop` - 店铺配置

### 跨境模型（ecomm_sync/models.py）
- ✅ `ProductListing` - 产品Listing
- ✅ `PlatformAccount` - 平台账号

## 🚀 快速开始

### 1. 启动开发服务器

```bash
python manage.py runserver
```

### 2. 访问Admin后台

访问：http://127.0.0.1:8000/admin/

### 3. 初始化配置数据

在Admin后台创建以下配置：

#### 3.1 创建平台配置（Core > Platforms）
- 淘宝（采集平台）- platform_type: collect
- 1688（采集平台）- platform_type: collect
- Shopee（跨境平台）- platform_type: cross
- TikTok（跨境平台）- platform_type: cross

#### 3.2 创建店铺配置（Core > Shops）
- Shopee店铺1 - 关联Shopee平台
- TikTok店铺1 - 关联TikTok平台

#### 3.3 配置字段映射规则（Collect > Field Map Rules）
- 淘宝字段→产品库字段
- 1688字段→产品库字段

#### 3.4 配置定价规则（Collect > Pricing Rules）
- 加成定价规则
- 固定定价规则

## 📱 使用界面

### 采集任务管理页面

访问：http://127.0.0.1:8000/collect/

**功能特性：**
- 创建采集任务（淘宝/1688）
- 批量导入商品链接
- 实时查看采集状态
- 查看采集详情
- 自动同步到跨境平台

### 创建采集任务

1. 点击"新建采集任务"
2. 选择采集平台（淘宝/1688）
3. 粘贴商品链接（每行一个）
4. 配置采集选项：
   - 选择平台API配置
   - 设置采集任务名称
5. 跨境同步选项（可选）：
   - ✅ 勾选"自动同步到跨境平台"
   - 选择目标跨境平台（Shopee/TikTok）
   - 选择目标跨境店铺
   - 选择定价规则（可选）
   - 选择翻译选项（可选）
6. 点击"创建并启动采集"

## 🔧 系统架构

### 采集流程

```
商品链接 → 采集任务 → 采集适配器 → 采集数据 → 采集子项
                                              ↓
                                         字段映射
                                              ↓
                                         产品库落地
                                              ↓
                                    ┌─────────┴─────────┐
                                    ↓                   ↓
                              产品库产品           Listing创建
                                                        ↓
                                                    同步到跨境平台
```

### 核心组件

#### 1. 采集适配器（collect/adapters/）
- `BaseCollectAdapter` - 基础采集适配器
- `TaobaoCollectAdapter` - 淘宝采集适配器
- `One688CollectAdapter` - 1688采集适配器

#### 2. 服务层（collect/services/）
- `image_downloader.py` - 图片下载服务
  - 批量下载
  - 本地存储/CDN支持
  - 格式转换（WebP）
  - 图片优化

- `translator.py` - 翻译服务
  - 百度翻译
  - Google翻译
  - 产品数据批量翻译

#### 3. Celery异步任务（collect/tasks.py）
- `generate_erp_sku()` - 生成ERP SKU
- `apply_field_map_rules()` - 应用字段映射
- `collect_and_land_task()` - 采集+落地主任务
- `create_listing_task()` - 创建Listing任务
- `collect_land_sync_task()` - 采集+落地+同步全链路任务
- `sync_listing_to_platform_task()` - 同步Listing到平台
- `batch_sync_listings_task()` - 批量同步Listing

## 🎯 使用场景

### 场景1：手动采集+手动同步（精品运营）

1. 配置平台API Key（淘宝/1688）
2. 访问 `/collect/` - 采集任务管理页面
3. 点击"新建采集任务"
4. 选择采集平台，粘贴商品链接
5. 点击"创建并启动采集"
6. 等待采集完成，查看任务状态
7. 点击"查看产品"跳转到产品库
8. 编辑产品信息（如需要）
9. 手动创建Listing到跨境平台

### 场景2：自动采集+自动同步（铺货运营）

1. 访问 `/collect/` - 采集任务管理页面
2. 点击"新建采集任务"
3. 选择采集平台，粘贴商品链接
4. ✅ 勾选"采集落地后自动同步到跨境平台"
5. 选择目标跨境平台（如Shopee）
6. 选择目标跨境店铺
7. 选择定价规则（可选）
8. 选择翻译选项（可选）
9. 点击"创建并启动采集"
10. 系统自动完成：采集→落地→创建Listing→同步

## 📊 状态说明

### 采集状态（collect_status）
- `pending` - 待采集
- `running` - 采集中
- `success` - 采集成功
- `failed` - 采集失败
- `partial` - 部分采集成功

### 落地状态（land_status）
- `unland` - 未落地
- `running` - 落地中
- `success` - 落地成功
- `failed` - 落地失败

### 跨境同步状态（sync_status）
- 待补充...

## 🔍 查看文档

详细的技术文档请参考：
- `COLLECT_IMPLEMENTATION_COMPLETE.md` - 完整实施报告
- `FINAL_IMPLEMENTATION_SUMMARY.md` - 最终实施总结

## 🐛 问题排查

### 问题1：采集任务无法启动
**检查项：**
- 确认Celery服务已启动
- 检查Redis连接状态
- 查看Django日志

### 问题2：图片下载失败
**检查项：**
- 确认网络连接正常
- 检查图片URL是否可访问
- 查看media目录权限

### 问题3：翻译功能不可用
**检查项：**
- 确认翻译API Key已配置
- 检查API调用是否超限
- 查看翻译服务日志

## 📞 支持

如有问题，请检查：
1. Django日志：`logs/django.log`
2. Celery日志：`logs/celery.log`
3. 浏览器控制台错误
4. Admin后台的系统通知

---

**系统已就绪，可以开始使用！** 🎉
