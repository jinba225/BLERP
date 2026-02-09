# Django ERP 运维工具使用指南 🛠️

**适用人员**: 运维工程师、DevOps工程师
**环境**: 开发 / 测试 / 生产
**最后更新**: 2026-02-08

---

## 📋 工具清单

本指南涵盖以下运维工具：

1. ✅ `deploy.sh` - 一键部署脚本
2. ✅ `backup.sh` - 数据库备份脚本
3. ✅ `health_check.sh` - 系统健康检查
4. ✅ `locustfile.py` - 性能测试脚本
5. ✅ `crontab.example` - 定时任务配置

---

## 🚀 1. 一键部署脚本

### 基本用法

```bash
./scripts/deploy.sh [环境] [操作]
```

### 开发环境

```bash
# 初始化开发环境
./scripts/deploy.sh development setup

# 部署开发环境
./scripts/deploy.sh development deploy

# 运行测试
./scripts/deploy.sh development test
```

### 预发布环境

```bash
# 部署到预发布
./scripts/deploy.sh staging deploy
```

### 生产环境

```bash
# 部署到生产环境
./scripts/deploy.sh production deploy

# 回滚到上一版本
./scripts/deploy.sh production rollback

# 备份数据库
./scripts/deploy.sh production backup
```

### 自动化流程

部署脚本会自动执行以下操作：

1. ✅ 检查系统依赖
2. ✅ 运行代码质量检查
3. ✅ 运行E2E测试
4. ✅ 备份数据库（生产环境）
5. ✅ 运行数据库迁移
6. ✅ 收集静态文件
7. ✅ 重启服务

---

## 💾 2. 数据库备份脚本

### 基本用法

```bash
./scripts/backup.sh [环境]
```

### 备份不同环境

```bash
# 开发环境备份（SQLite）
./scripts/backup.sh development

# 生产环境备份（PostgreSQL）
./scripts/backup.sh production

# 自定义环境
ENVIRONMENT=staging ./scripts/backup.sh
```

### 备份媒体文件

```bash
BACKUP_MEDIA=true ./scripts/backup.sh production
```

### 查看备份文件

```bash
ls -lh backups/
```

输出示例：
```
-rw-r--r-- 1 user user 1.2M Feb  8 10:00 postgresql_production_20260208_100000.sql.gz
-rw-r--r-- 1 user user  15K Feb  8 10:00 postgresql_production_20260208_100000.sql.gz.info
```

### 恢复数据库

```bash
# PostgreSQL恢复
gunzip -c backups/postgresql_production_20260208_100000.sql.gz | \
  psql -U postgres -d django_erp

# SQLite恢复
gunzip -c backups/sqlite_development_20260208_100000.sqlite3.gz > db.sqlite3
```

---

## 🏥 3. 系统健康检查

### 运行健康检查

```bash
./scripts/health_check.sh
```

### 检查项目

健康检查脚本会验证以下10个方面：

1. **环境检查**
   - Python版本（需要 >= 3.13）
   - Django版本
   - .env文件配置
   - DEBUG模式
   - SECRET_KEY

2. **数据库检查**
   - 数据库文件存在
   - 数据库连接
   - 数据库权限

3. **应用检查**
   - Django系统检查
   - 数据库迁移状态
   - 静态文件收集

4. **依赖检查**
   - djangorestframework
   - django_filters
   - celery
   - redis
   - pytest

5. **性能检查**
   - Redis连接
   - Celery worker状态

6. **安全检查**
   - 部署安全配置
   - HTTPS重定向
   - HSTS配置

7. **测试检查**
   - E2E测试文件存在

8. **备份检查**
   - 备份文件存在
   - 备份时间戳

9. **监控检查**
   - Sentry配置

10. **代码质量检查**
    - Black格式
    - flake8检查

### 输出示例

```
==========================================
Django ERP 系统健康检查
==========================================

📋 环境检查...
✓ Python版本: 3.13.5
✓ Django版本: 5.0.9
✓ .env文件存在
✓ 生产环境配置: DEBUG=False
✓ SECRET_KEY已配置

💾 数据库检查...
✓ PostgreSQL客户端已安装
✓ 数据库连接正常

🚀 应用检查...
✓ Django系统检查通过
✓ 所有迁移已应用
✓ 静态文件已收集: 1523 个文件

...

==========================================
健康检查完成
==========================================

✓ 所有检查通过！
  通过: 45
  失败: 0

🎉 系统健康状况良好！
```

### 集成到CI/CD

```yaml
# .github/workflows/ci.yml
- name: 运行健康检查
  run: |
    chmod +x scripts/health_check.sh
    ./scripts/health_check.sh
```

---

## ⚡ 4. 性能测试

### Locust性能测试

```bash
# 开发环境测试（启动Web UI）
locust -f locustfile.py --host=http://localhost:8000

# 无头模式（命令行）
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users=50 \
  --spawn-rate=5 \
  --run-time=1m
```

### 测试场景

脚本包含3种用户类型：

1. **ERPUserBehavior** - 普通ERP用户
   - 查看仪表盘
   - 浏览订单列表
   - 查看库存
   - 执行搜索

2. **AdminUserBehavior** - 管理员用户
   - 查看Admin后台
   - 管理订单
   - 管理产品
   - 查看用户

3. **APIUserBehavior** - API客户端
   - 高频API调用
   - 获取产品/订单
   - 创建订单

### 性能测试场景

```bash
# 场景1: 开发环境验证（10用户）
locust -f locustfile.py --host=http://localhost:8000 \
  --users=10 --spawn-rate=1

# 场景2: 中等负载测试（50用户，5分钟）
locust -f locustfile.py --host=http://staging.example.com \
  --users=50 --spawn-rate=5 --run-time=5m

# 场景3: 压力测试（200用户，10分钟）
locust -f locustfile.py --host=http://staging.example.com \
  --users=200 --spawn-rate=20 --run-time=10m

# 场景4: 峰值测试（500用户，2分钟）
locust -f locustfile.py --host=http://staging.example.com \
  --users=500 --spawn-rate=50 --run-time=2m

# 场景5: 稳定性测试（100用户，1小时）
locust -f locustfile.py --host=http://staging.example.com \
  --users=100 --spawn-rate=10 --run-time=1h
```

### 性能目标

- ✅ 平均响应时间 < 500ms
- ✅ 95%请求响应时间 < 1s
- ✅ 错误率 < 1%
- ✅ 支持100并发用户

### 查看Web UI

启动Locust后，访问 http://localhost:8089

- 设置用户数量
- 设置spawn rate（每秒启动用户数）
- 点击"Start Swarming"开始测试
- 实时查看性能指标

---

## ⏰ 5. 定时任务配置

### 配置Cron定时任务

```bash
# 1. 复制配置示例
cp scripts/crontab.example /tmp/my-crontab

# 2. 编辑配置
nano /tmp/my-crontab

# 3. 修改项目路径
PROJECT_DIR=/path/to/django_erp

# 4. 安装定时任务
crontab /tmp/my-crontab

# 5. 查看已安装的任务
crontab -l
```

### 常用定时任务

```bash
# 每天凌晨2点数据库备份
0 2 * * * cd /path/to/project && ./scripts/backup.sh production

# 每天凌晨3点清理会话
0 3 * * * cd /path/to/project && python manage.py clearsessions

# 每小时运行健康检查
0 * * * * cd /path/to/project && ./scripts/health_check.sh

# 每周日0点完整备份（含媒体文件）
0 0 * * 0 cd /path/to/project && BACKUP_MEDIA=true ./scripts/backup.sh production

# 每6小时备份数据库
0 */6 * * * cd /path/to/project && ./scripts/backup.sh production
```

### 查看定时任务日志

```bash
# 查看备份日志
tail -f logs/cron_backup.log

# 查看系统cron日志
sudo tail -f /var/log/syslog | grep CRON
```

---

## 🔄 6. 完整运维流程

### 日常运维

```bash
# 1. 每日健康检查
./scripts/health_check.sh

# 2. 查看系统资源
htop  # 或 top
df -h  # 磁盘使用
free -h  # 内存使用

# 3. 查看应用日志
tail -f logs/django.log

# 4. 查看Celery状态
celery -A django_erp inspect active
```

### 部署流程

```bash
# 1. 运行健康检查
./scripts/health_check.sh

# 2. 拉取最新代码
git pull origin main

# 3. 运行测试
pytest apps/**/test_e2e_*.py -v

# 4. 备份数据库（生产环境）
./scripts/backup.sh production

# 5. 部署
./scripts/deploy.sh production deploy

# 6. 验证部署
curl -I https://your-domain.com
./scripts/health_check.sh
```

### 故障排查

```bash
# 1. 检查服务状态
sudo systemctl status gunicorn
sudo systemctl status nginx

# 2. 查看错误日志
tail -f logs/django.log | grep ERROR

# 3. 检查数据库连接
python manage.py dbshell

# 4. 检查Redis
redis-cli ping

# 5. 检查Celery
celery -A django_erp inspect active

# 6. 运行健康检查
./scripts/health_check.sh

# 7. 查看Sentry错误
# 访问Sentry后台
```

### 应急响应

```bash
# 1. 立即回滚
./scripts/deploy.sh production rollback

# 2. 恢复数据库
gunzip -c backups/latest.sql.gz | psql -U postgres -d django_erp

# 3. 重启服务
sudo systemctl restart gunicorn
sudo systemctl reload nginx

# 4. 检查系统状态
./scripts/health_check.sh

# 5. 通知相关人员
# 发送告警通知
```

---

## 📊 7. 监控指标

### 系统指标

```bash
# CPU使用率
top -bn1 | grep "Cpu(s)"

# 内存使用率
free -h

# 磁盘使用率
df -h

# 网络连接
netstat -tulpn | grep :8000
```

### 应用指标

```bash
# 请求响应时间（通过Sentry）
# 访问Sentry后台查看

# 错误率（通过Sentry）
# 访问Sentry后台查看

# 并发用户数
# 通过应用监控工具

# 数据库查询性能
python manage.py debugsqlshell
```

### 业务指标

```bash
# 今日订单量
python manage.py shell -c "
from sales.models import SalesOrder
from django.utils import timezone
from datetime import timedelta
today = timezone.now().date()
print(SalesOrder.objects.filter(order_date=today).count())
"

# 库存预警
python manage.py shell -c "
from inventory.models import InventoryStock
print(InventoryStock.objects.filter(quantity__lt=10).count())
"

# 应收账款统计
python manage.py shell -c "
from finance.models import CustomerAccount
from django.db.models import Sum
print(CustomerAccount.objects.aggregate(Sum('balance')))
"
```

---

## 🔧 8. 工具维护

### 更新脚本

```bash
# 定期检查脚本版本
git log scripts/ -1

# 更新到最新版本
git pull origin main
```

### 测试脚本

```bash
# 在测试环境测试新脚本
./scripts/deploy.sh staging test

# 验证备份脚本
./scripts/backup.sh staging
```

### 自定义脚本

```bash
# 复制现有脚本
cp scripts/backup.sh scripts/custom_backup.sh

# 编辑并测试
nano scripts/custom_backup.sh
chmod +x scripts/custom_backup.sh
./scripts/custom_backup.sh development
```

---

## 📞 9. 故障处理

### 常见问题

#### 问题1: 部署失败

```bash
# 检查日志
./scripts/deploy.sh production deploy 2>&1 | tee deploy.log

# 查看Django日志
tail -f logs/django.log

# 运行健康检查
./scripts/health_check.sh
```

#### 问题2: 数据库连接失败

```bash
# 检查数据库状态
sudo systemctl status postgresql

# 测试连接
python manage.py dbshell

# 检查配置
grep "DB_" .env
```

#### 问题3: 性能下降

```bash
# 运行性能测试
locust -f locustfile.py --headless --users=50

# 查看慢查询
tail -f logs/django.log | grep "Slow query"

# 重启服务
sudo systemctl restart gunicorn
```

#### 问题4: 磁盘空间不足

```bash
# 检查磁盘使用
df -h

# 清理旧日志
find logs/ -name "*.log" -mtime +30 -delete

# 清理旧备份
find backups/ -name "*.gz" -mtime +30 -delete

# 清理Docker
docker system prune -a
```

---

## 📚 10. 相关文档

- **快速启动指南**: `QUICK_START_GUIDE.md`
- **部署检查清单**: `DEPLOYMENT_CHECKLIST.md`
- **最终实施报告**: `FINAL_IMPLEMENTATION_REPORT.md`
- **上线准备报告**: `PRODUCTION_READINESS_REPORT.md`

---

**文档维护**: 请定期更新此文档以反映最新的运维实践

**最后更新**: 2026-02-08
**文档版本**: v1.0
