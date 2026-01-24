# BetterLaser ERP 生产环境部署指南

本文档提供 Django ERP 系统的生产环境部署完整指南。

## 📋 目录

- [系统要求](#系统要求)
- [第一周完成内容](#第一周完成内容)
- [快速开始](#快速开始)
- [详细配置](#详细配置)
- [部署验证](#部署验证)
- [常见问题](#常见问题)
- [下一步工作](#下一步工作)

---

## 系统要求

### 硬件要求（推荐配置）

- **CPU**: 4核心或以上
- **内存**: 8GB RAM (最低 4GB)
- **硬盘**: 50GB SSD (数据库和媒体文件存储)
- **网络**: 稳定的互联网连接,支持 HTTPS

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+ / CentOS 8+ 推荐)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **域名**: 已解析到服务器的域名（用于 SSL 证书）

---

## 第一周完成内容

✅ **已完成的生产环境配置：**

### 1. Docker 容器化

- ✅ 多阶段 Dockerfile 构建
  - Python 依赖构建阶段
  - Frontend 资源构建阶段
  - 运行时环境优化
  - 非 root 用户运行
  - 健康检查集成

- ✅ .dockerignore 优化
  - 排除开发文件
  - 减小镜像体积

### 2. Docker Compose 编排

- ✅ 开发环境配置 (`docker-compose.yml`)
  - MySQL 8.0 数据库
  - Redis 7 缓存
  - Django Web 服务
  - Celery Worker
  - Celery Beat 定时任务
  - Nginx 反向代理 (可选)
  - 健康检查和依赖管理
  - 自定义网络隔离

- ✅ 生产环境配置 (`docker-compose.prod.yml`)
  - 资源限制 (CPU/内存)
  - 日志轮转策略
  - 副本部署支持
  - 持久化数据卷
  - 生产级优化参数

### 3. Nginx 反向代理

- ✅ 开发环境配置 (`docker/nginx/nginx.conf`)
  - 静态文件服务
  - 媒体文件服务
  - Gzip 压缩
  - 基础安全头部

- ✅ 生产环境配置 (`docker/nginx/nginx.prod.conf`)
  - HTTPS 强制重定向
  - SSL/TLS 优化配置
  - HSTS 安全策略
  - 速率限制 (防 DDoS)
  - API 和登录接口限速
  - 完整安全头部
  - 静态资源长期缓存

### 4. MySQL 数据库

- ✅ 初始化脚本 (`docker/mysql/init/01-init.sql`)
  - UTF-8MB4 字符集
  - 时区配置
  - 用户权限设置

- ✅ 开发环境优化 (`docker/mysql/conf.d/my.cnf`)
  - 适度缓冲区配置
  - 慢查询日志
  - InnoDB 优化

- ✅ 生产环境优化 (`docker/mysql/prod/conf.d/my.cnf`)
  - 大内存优化配置
  - 连接池优化
  - Binary Log 启用
  - 性能监控启用
  - 备份恢复支持

### 5. Django 配置优化

- ✅ 数据库配置 (`better_laser_erp/settings.py`)
  - 自动环境检测 (SQLite/MySQL)
  - 连接池配置 (CONN_MAX_AGE)
  - 自动事务包装
  - 超时配置

- ✅ Redis 缓存配置
  - 自动环境检测
  - 连接池优化
  - 超时和重试配置
  - Key 前缀隔离
  - Session 缓存支持

- ✅ Celery 配置
  - 自动环境检测
  - 任务超时控制
  - Worker 自动重启
  - 连接重试机制

- ✅ 安全配置强化
  - **SECRET_KEY**: 自动生成 + 生产环境强制检查
  - **DEBUG**: 生产环境强制检查 ALLOWED_HOSTS
  - **HTTPS**: 完整的 HTTPS 安全配置
    - SSL 重定向
    - HSTS 策略
    - 安全 Cookie
    - CSRF 防护
    - Referrer Policy
  - **Session**: 支持 Redis 会话存储

### 6. 生产依赖

- ✅ 更新 `requirements.txt`
  - mysqlclient (MySQL 驱动)
  - gunicorn (WSGI 服务器)
  - redis + django-redis (缓存)
  - celery + django-celery-beat (任务队列)
  - 可选：sentry-sdk (错误监控)

### 7. 配置文件模板

- ✅ 环境变量模板 (`.env.example`)
  - 完整的配置说明
  - 开发和生产环境示例
  - 安全提示

- ✅ Gunicorn 配置 (`gunicorn_config.py`)
  - Worker 进程管理
  - 日志配置
  - 超时和连接配置
  - 生命周期钩子

### 8. SSL 证书

- ✅ SSL 配置指南 (`docker/nginx/ssl/README.md`)
  - Let's Encrypt 免费证书
  - 自签名证书（测试）
  - 商业证书配置
  - 证书验证方法

---

## 快速开始

### 1. 克隆项目并配置环境

```bash
# 进入项目目录
cd /path/to/django_erp

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件,配置生产环境参数
nano .env
```

### 2. 必须配置的环境变量

在 `.env` 文件中配置以下关键参数：

```bash
# ============================================
# 生产环境必须配置的参数
# ============================================

# 调试模式（生产环境必须设为 False）
DEBUG=False

# 随机密钥（运行以下命令生成）
# python -c 'import secrets; print(secrets.token_urlsafe(50))'
SECRET_KEY=your-super-secret-random-key-here

# 允许的域名（替换为您的实际域名）
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# MySQL 数据库
DB_ENGINE=django.db.backends.mysql
DB_NAME=django_erp
DB_USER=django_user
DB_PASSWORD=CHANGE_THIS_STRONG_PASSWORD
DB_HOST=db
DB_PORT=3306
DB_ROOT_PASSWORD=CHANGE_THIS_ROOT_PASSWORD

# Redis 缓存
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=CHANGE_THIS_REDIS_PASSWORD

# Celery 任务队列
CELERY_BROKER_URL=redis://:CHANGE_THIS_REDIS_PASSWORD@redis:6379/0
CELERY_RESULT_BACKEND=redis://:CHANGE_THIS_REDIS_PASSWORD@redis:6379/0

# Gunicorn Worker 数量（CPU核心数 * 2 + 1）
GUNICORN_WORKERS=4
```

### 3. 生成 SECRET_KEY

```bash
python -c 'import secrets; print(secrets.token_urlsafe(50))'
```

将输出的随机字符串复制到 `.env` 文件的 `SECRET_KEY` 配置中。

### 4. 配置 SSL 证书

#### 方式A: Let's Encrypt（推荐）

```bash
# 安装 certbot
apt-get update && apt-get install -y certbot

# 生成证书
certbot certonly --webroot -w /var/www/certbot \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos

# 复制证书到项目目录
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/nginx/ssl/key.pem

# 设置权限
chmod 600 docker/nginx/ssl/key.pem
chmod 644 docker/nginx/ssl/cert.pem
```

#### 方式B: 自签名证书（仅测试）

```bash
cd docker/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem \
  -out cert.pem \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=BetterLaser/OU=IT/CN=localhost"
```

⚠️ **注意**: 自签名证书仅用于测试,浏览器会显示安全警告！

### 5. 创建持久化数据目录

```bash
# 创建生产环境数据目录
sudo mkdir -p /data/django_erp/{mysql,redis,media}

# 设置权限
sudo chown -R 999:999 /data/django_erp/mysql  # MySQL UID
sudo chown -R 999:999 /data/django_erp/redis  # Redis UID
sudo chown -R 1000:1000 /data/django_erp/media  # Django UID
```

### 6. 启动生产环境

```bash
# 构建镜像
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# 启动所有服务
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### 7. 创建超级用户

```bash
# 进入 web 容器
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web bash

# 创建超级用户
python manage.py createsuperuser

# 退出容器
exit
```

### 8. 访问系统

- **HTTPS 访问**: https://yourdomain.com
- **Admin 后台**: https://yourdomain.com/admin/
- **API 文档**: https://yourdomain.com/api/docs/

---

## 详细配置

### 环境变量完整配置

参考 `.env.example` 文件获取所有可配置的环境变量说明。

### 服务管理命令

```bash
# 停止所有服务
docker-compose -f docker-compose.yml -f docker-compose.prod.yml stop

# 重启所有服务
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart

# 停止并删除容器
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# 查看运行状态
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# 查看资源使用情况
docker stats
```

### 数据库管理

```bash
# 进入 MySQL 容器
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec db mysql -u root -p

# 导出数据库
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec db \
  mysqldump -u root -p django_erp > backup.sql

# 导入数据库
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db \
  mysql -u root -p django_erp < backup.sql
```

### 日志查看

```bash
# Django 应用日志
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f web

# Nginx 日志
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f nginx

# MySQL 慢查询日志
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec db \
  tail -f /var/lib/mysql/mysql-slow.log

# Celery Worker 日志
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f celery
```

---

## 部署验证

### 健康检查

```bash
# 检查所有服务状态
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# 检查 Web 服务健康
curl -I https://yourdomain.com/health/

# 检查 MySQL 连接
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec db \
  mysqladmin -u root -p ping

# 检查 Redis 连接
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec redis \
  redis-cli -a YOUR_REDIS_PASSWORD ping
```

### Django 系统检查

```bash
# 进入 web 容器
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web bash

# 运行系统检查
python manage.py check --deploy

# 检查数据库连接
python manage.py dbshell

# 运行测试
python manage.py test

# 退出容器
exit
```

### 性能测试

```bash
# 使用 Apache Bench 测试
ab -n 1000 -c 10 https://yourdomain.com/

# 使用 curl 测试响应时间
curl -w "@curl-format.txt" -o /dev/null -s https://yourdomain.com/
```

---

## 常见问题

### 1. 数据库连接失败

**问题**: `OperationalError: (2002, "Can't connect to MySQL server")`

**解决方案**:
```bash
# 检查 MySQL 容器状态
docker-compose ps db

# 查看 MySQL 日志
docker-compose logs db

# 确保 .env 中数据库配置正确
# 等待 MySQL 完全启动（约30秒）
```

### 2. 静态文件 404

**问题**: CSS/JS 文件无法加载

**解决方案**:
```bash
# 重新收集静态文件
docker-compose exec web python manage.py collectstatic --noinput --clear

# 检查 Nginx 配置
docker-compose exec nginx nginx -t

# 重启 Nginx
docker-compose restart nginx
```

### 3. SSL 证书错误

**问题**: 浏览器显示证书无效

**解决方案**:
```bash
# 检查证书文件是否存在
ls -la docker/nginx/ssl/

# 验证证书
openssl x509 -in docker/nginx/ssl/cert.pem -text -noout

# 检查证书和私钥是否匹配
openssl x509 -noout -modulus -in docker/nginx/ssl/cert.pem | openssl md5
openssl rsa -noout -modulus -in docker/nginx/ssl/key.pem | openssl md5
```

### 4. Celery 任务不执行

**问题**: 异步任务没有被处理

**解决方案**:
```bash
# 检查 Celery Worker 状态
docker-compose logs celery

# 检查 Redis 连接
docker-compose exec redis redis-cli -a YOUR_PASSWORD ping

# 重启 Celery
docker-compose restart celery celery-beat
```

### 5. 内存不足

**问题**: 容器被 OOM Killer 终止

**解决方案**:
```bash
# 检查内存使用情况
docker stats

# 调整 docker-compose.prod.yml 中的内存限制
# 减少 Gunicorn worker 数量
# 优化 MySQL innodb_buffer_pool_size
```

---

## 下一步工作

### 第二周任务（监控和日志）

1. ⏳ **Sentry 错误监控**
   - 注册 Sentry 账号
   - 集成 sentry-sdk
   - 配置错误报告

2. ⏳ **日志聚合**
   - ELK Stack 或 Loki
   - 集中式日志管理
   - 日志分析和告警

3. ⏳ **监控系统**
   - Prometheus + Grafana
   - 性能指标监控
   - 告警配置

4. ⏳ **备份策略**
   - 自动数据库备份
   - 媒体文件备份
   - 备份恢复测试

### 第三周任务（CI/CD 和优化）

1. ⏳ **CI/CD 管道**
   - GitHub Actions 或 GitLab CI
   - 自动化测试
   - 自动化部署

2. ⏳ **性能优化**
   - 数据库查询优化
   - Redis 缓存策略
   - CDN 配置

3. ⏳ **安全加固**
   - Web Application Firewall
   - DDoS 防护
   - 安全审计

4. ⏳ **文档完善**
   - API 文档自动生成
   - 运维手册
   - 故障排查指南

---

## 技术栈总结

- **Web 框架**: Django 4.2
- **WSGI 服务器**: Gunicorn
- **反向代理**: Nginx
- **数据库**: MySQL 8.0
- **缓存**: Redis 7
- **任务队列**: Celery
- **容器化**: Docker + Docker Compose
- **前端**: Tailwind CSS + Alpine.js
- **认证**: JWT + Session

---

## 支持和反馈

如有问题或建议,请通过以下方式联系：

- **项目仓库**: [GitHub Issues]
- **文档**: 参考 `django_erp/CLAUDE.md`
- **API 文档**: https://yourdomain.com/api/docs/

---

**最后更新时间**: 2025-11-13
**版本**: v1.0.0 (生产环境就绪)
