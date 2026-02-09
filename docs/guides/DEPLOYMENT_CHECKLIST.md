# Django ERP 生产环境部署检查清单 🚀

**文档版本**: v1.0
**最后更新**: 2026-02-08
**适用版本**: Django ERP v1.0

---

## 📋 部署前准备

### 1. 代码准备
- [ ] **代码已提交到Git仓库**
  ```bash
  git status
  git push origin main
  ```

- [ ] **所有测试通过**
  ```bash
  pytest apps/**/test_e2e_*.py -v
  ```

- [ ] **代码质量检查通过**
  ```bash
  black . --check --line-length=100
  flake8 . --max-line-length=100
  isort . --check-only
  ```

- [ ] **数据库迁移已准备**
  ```bash
  python manage.py makemigrations
  python manage.py migrate --plan
  ```

### 2. 服务器准备
- [ ] **服务器配置要求**
  - [ ] CPU: 最少2核，推荐4核
  - [ ] 内存: 最少4GB，推荐8GB
  - [ ] 磁盘: 最少20GB，推荐50GB+
  - [ ] 操作系统: Ubuntu 20.04+ / CentOS 8+ / Debian 11+

- [ ] **系统依赖已安装**
  ```bash
  # Docker
  docker --version  # 应 >= 20.10
  docker-compose --version  # 应 >= 2.0

  # 或直接安装Python依赖
  python3 --version  # 应 >= 3.13
  pip3 --version
  ```

- [ ] **网络配置**
  - [ ] 防火墙规则已配置
  - [ ] 域名已解析到服务器IP
  - [ ] SSL证书已准备（Let's Encrypt或其他）

---

## 🔐 安全配置检查

### 3. 环境变量配置
- [ ] **`.env`文件已创建**
  ```bash
  # 在服务器上创建.env文件
  nano /path/to/project/.env
  chmod 600 /path/to/project/.env  # 安全权限
  ```

- [ ] **生产环境密钥已配置**
  ```bash
  # 必须修改的密钥
  DEBUG=False  # ⚠️ 必须是False
  SECRET_KEY=强随机密钥-使用-secrets-token-urlsafe-50生成
  JWT_SECRET_KEY=另一个强随机密钥

  # 数据库密码
  DB_PASSWORD=强数据库密码

  # 其他敏感配置
  ENCRYPTION_KEY=用于加密API密钥的密码
  ```

- [ ] **允许的主机已配置**
  ```bash
  ALLOWED_HOSTS=your-domain.com,www.your-domain.com
  ```

### 4. 数据库安全
- [ ] **PostgreSQL配置（推荐）**
  ```bash
  # 使用PostgreSQL而非SQLite
  DB_ENGINE=django.db.backends.postgresql
  DB_HOST=localhost  # 或专用数据库服务器
  DB_PORT=5432
  DB_NAME=django_erp_prod
  DB_USER=django_erp
  DB_PASSWORD=强密码

  # 远程数据库配置
  # DB_HOST=db.example.com
  # SSL连接: ?sslmode=require
  ```

- [ ] **数据库备份配置**
  ```bash
  # 备份目录
  BACKUP_DIR=/var/backups/django-erp
  BACKUP_RETENTION_DAYS=30

  # 测试备份脚本
  ./scripts/backup.sh production
  ```

### 5. HTTPS和SSL配置
- [ ] **SSL证书已安装**
  ```bash
  # Let's Encrypt
  sudo certbot --nginx -d your-domain.com

  # 或使用商业证书
  # 证书路径: /etc/ssl/certs/your-domain.crt
  # 私钥路径: /etc/ssl/private/your-domain.key
  ```

- [ ] **Nginx配置已更新**
  ```nginx
  server {
      listen 443 ssl http2;
      server_name your-domain.com;

      ssl_certificate /etc/ssl/certs/your-domain.crt;
      ssl_certificate_key /etc/ssl/private/your-domain.key;

      # 推荐的SSL配置
      ssl_protocols TLSv1.2 TLSv1.3;
      ssl_ciphers HIGH:!aNULL:!MD5;
      ssl_prefer_server_ciphers on;

      location / {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }

  # HTTP重定向到HTTPS
  server {
      listen 80;
      server_name your-domain.com;
      return 301 https://$server_name$request_uri;
  }
  ```

---

## 🗄️ 数据库部署

### 6. 数据库初始化
- [ ] **创建数据库**
  ```bash
  # PostgreSQL
  sudo -u postgres psql
  CREATE DATABASE django_erp_prod;
  CREATE USER django_erp WITH PASSWORD 'strong-password';
  GRANT ALL PRIVILEGES ON DATABASE django_erp_prod TO django_erp;
  \q
  ```

- [ ] **运行数据库迁移**
  ```bash
  cd /path/to/project
  python manage.py migrate --noinput
  ```

- [ ] **创建超级用户**
  ```bash
  python manage.py createsuperuser
  ```

- [ ] **加载初始数据（可选）**
  ```bash
  python manage.py loaddata initial_data.json
  ```

### 7. 静态文件处理
- [ ] **收集静态文件**
  ```bash
  python manage.py collectstatic --noinput
  ```

- [ ] **Nginx静态文件配置**
  ```nginx
  location /static/ {
      alias /path/to/project/staticfiles/;
      expires 30d;
      add_header Cache-Control "public, immutable";
  }

  location /media/ {
      alias /path/to/project/media/;
      expires 7d;
  }
  ```

---

## 🐳 Docker部署（推荐）

### 8. Docker配置
- [ ] **Docker Compose配置文件**
  ```bash
  # 使用生产环境配置
  docker-compose -f docker-compose.prod.yml pull
  docker-compose -f docker-compose.prod.yml config
  ```

- [ ] **构建Docker镜像**
  ```bash
  docker-compose -f docker-compose.prod.yml build
  ```

- [ ] **启动容器**
  ```bash
  docker-compose -f docker-compose.prod.yml up -d
  ```

- [ ] **检查容器状态**
  ```bash
  docker-compose ps
  docker-compose logs -f
  ```

### 9. 服务健康检查
- [ ] **Web服务运行正常**
  ```bash
  curl https://your-domain.com/health/
  # 应返回: {"status": "ok"}
  ```

- [ ] **数据库连接正常**
  ```bash
  python manage.py dbshell
  # 应能连接到数据库
  ```

- [ ] **Redis连接正常（如果使用）**
  ```bash
  python manage.py shell
  >>> from django.core.cache import cache
  >>> cache.set('test', 'hello', 60)
  >>> cache.get('test')
  'hello'
  ```

---

## 🔍 部署后验证

### 10. 功能测试
- [ ] **用户登录/登出**
  - 访问: https://your-domain.com/login/
  - 测试登录功能
  - 测试登出功能

- [ ] **核心业务功能**
  - [ ] 创建采购订单
  - [ ] 创建销售订单
  - [ ] 查看库存列表
  - [ ] 查看财务报表

- [ ] **API接口测试**
  ```bash
  # 测试API端点
  curl https://your-domain.com/api/docs/
  ```

### 11. 性能检查
- [ ] **页面加载速度**
  - 首页 < 2秒
  - 列表页 < 3秒
  - 详情页 < 2秒

- [ ] **数据库查询性能**
  ```bash
  python manage.py showmigrations  # 所有迁移已应用
  python manage.py check --database default  # 数据库配置正确
  ```

- [ ] **缓存配置**
  ```bash
  # 检查Redis缓存
  python manage.py shell
  >>> from django.core.cache import cache
  >>> cache.set('test', 'value', 300)
  >>> cache.get('test')
  'value'
  ```

### 12. 监控和日志
- [ ] **Sentry错误监控已配置**
  ```bash
  # .env文件中
  SENTRY_DSN=https://your-dsn@sentry.io/project-id
  ENVIRONMENT=production

  # 验证: 故意触发一个错误，检查Sentry是否收到
  ```

- [ ] **日志文件配置**
  ```bash
  # 检查日志目录
  ls -lh logs/

  # 实时查看日志
  tail -f logs/django.log
  ```

- [ ] **Celery任务监控（如果使用）**
  ```bash
  # 检查Celery worker状态
  celery -A django_erp inspect active

  # 检查Celery Beat任务
  celery -A django_erp inspect registered
  ```

---

## 🔒 安全加固

### 13. 安全配置验证
- [ ] **Django安全检查通过**
  ```bash
  python manage.py check --deploy
  # 应没有错误，只有警告
  ```

- [ ] **DEBUG模式已关闭**
  ```bash
  # .env文件
  DEBUG=False

  # 验证: 访问不存在的URL应看到404页面，而不是调试页面
  ```

- [ ] **HSTS已启用**
  ```bash
  # 检查HTTP响应头
  curl -I https://your-domain.com
  # 应包含: Strict-Transport-Security: max-age=31536000
  ```

### 14. 备份和恢复
- [ ] **自动备份已配置**
  ```bash
  # 配置cron定时任务
  crontab -e
  # 添加: 0 2 * * * cd /path/to/project && ./scripts/backup.sh production
  ```

- [ ] **备份恢复已测试**
  ```bash
  # 测试恢复流程
  ./scripts/restore.sh latest-backup.sql.gz
  ```

---

## 📊 监控和维护

### 15. 监控配置
- [ ] **系统监控**
  - CPU使用率 < 80%
  - 内存使用率 < 85%
  - 磁盘使用率 < 80%

- [ ] **应用监控**
  - 响应时间监控
  - 错误率监控
  - 并发用户数监控

- [ ] **业务监控**
  - 订单量监控
  - 库存预警
  - 应收应付提醒

### 16. 文档和交接
- [ ] **部署文档已更新**
  - 服务器信息
  - 访问凭据（安全存储）
  - 部署流程

- [ ] **运维手册已准备**
  - 日常维护任务
  - 故障排查指南
  - 应急响应流程

- [ ] **团队交接已完成**
  - 开发团队
  - 运维团队
  - 业务团队

---

## ✅ 部署完成确认

### 最终检查清单
- [ ] 所有测试通过 ✅
- [ ] 安全配置完整 ✅
- [ ] 数据库正常运行 ✅
- [ ] 备份策略已配置 ✅
- [ ] 监控系统已启用 ✅
- [ ] 文档已更新 ✅
- [ ] 团队已交接 ✅

### 上线批准
- [ ] **技术负责人批准**: _______________ 日期: _______
- [ ] **产品负责人批准**: _______________ 日期: _______
- [ ] **运维负责人批准**: _______________ 日期: _______

---

## 🆘 应急回滚计划

如果部署后出现严重问题：

1. **立即回滚到上一版本**
   ```bash
   git checkout <previous-stable-tag>
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

2. **从备份恢复数据库**
   ```bash
   ./scripts/restore.sh backups/postgresql_production_<timestamp>.sql.gz
   ```

3. **通知相关人员**
   - 技术团队
   - 管理层
   - 用户（如需要）

4. **分析问题原因**
   - 查看日志
   - 检查Sentry错误
   - 复现问题

5. **修复后重新部署**
   - 在测试环境验证
   - 重新执行检查清单
   - 灰度发布

---

**检查清单完成标准**: 所有✅标记项目均已完成

**文档维护**: 每次部署后更新此文档

**联系方式**:
- 技术支持: support@example.com
- 紧急联系: +86-XXX-XXXX-XXXX
