# 安装指南

本文档详细介绍了如何安装和配置 BetterLaser ERP 系统。

## 系统要求

### 硬件要求
- **CPU**: 2核心以上
- **内存**: 4GB RAM 以上（推荐 8GB）
- **存储**: 20GB 可用空间以上
- **网络**: 稳定的网络连接

### 软件要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / macOS 10.15+ / Windows 10+
- **Python**: 3.8 或更高版本
- **Node.js**: 16.0 或更高版本
- **数据库**: MySQL 8.0 或 PostgreSQL 12+
- **缓存**: Redis 6.0+
- **Web服务器**: Nginx 1.18+ (生产环境)

## 快速安装

### 1. 自动安装（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd django_erp

# 运行自动部署脚本
./deploy.sh
```

### 2. 手动安装

#### 步骤 1: 环境准备

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装系统依赖
sudo apt install -y python3 python3-pip python3-venv nodejs npm mysql-server redis-server nginx git

# 启动服务
sudo systemctl start mysql
sudo systemctl start redis-server
sudo systemctl enable mysql
sudo systemctl enable redis-server
```

#### 步骤 2: 项目设置

```bash
# 克隆项目
git clone <repository-url>
cd django_erp

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Node.js 依赖
npm install
```

#### 步骤 3: 数据库配置

```bash
# 登录 MySQL
sudo mysql -u root -p

# 创建数据库和用户
CREATE DATABASE better_laser_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'erp_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON better_laser_erp.* TO 'erp_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 步骤 4: 环境配置

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

配置示例：
```env
# Django 设置
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# 数据库设置
DB_NAME=better_laser_erp
DB_USER=erp_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# Redis 设置
REDIS_URL=redis://127.0.0.1:6379/1

# 邮件设置
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
```

#### 步骤 5: 数据库迁移

```bash
# 运行数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser
```

#### 步骤 6: 静态文件

```bash
# 构建前端资源
npm run build

# 收集静态文件
python manage.py collectstatic --noinput
```

#### 步骤 7: 测试运行

```bash
# 启动开发服务器
python manage.py runserver

# 在另一个终端启动 Celery
celery -A better_laser_erp worker -l info

# 在第三个终端启动 Celery Beat
celery -A better_laser_erp beat -l info
```

## 生产环境部署

### 1. Nginx 配置

创建 Nginx 配置文件：
```bash
sudo nano /etc/nginx/sites-available/better-laser-erp
```

配置内容：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 50M;
    
    location /static/ {
        alias /path/to/django_erp/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /path/to/django_erp/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/better-laser-erp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. SSL 证书配置

使用 Let's Encrypt：
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. 系统服务配置

创建 systemd 服务文件：

**Django 应用服务** (`/etc/systemd/system/better-laser-erp.service`):
```ini
[Unit]
Description=BetterLaser ERP Django Application
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/django_erp
Environment=PATH=/path/to/django_erp/venv/bin
ExecStart=/path/to/django_erp/venv/bin/gunicorn better_laser_erp.wsgi:application --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Celery Worker 服务** (`/etc/systemd/system/better-laser-erp-celery.service`):
```ini
[Unit]
Description=BetterLaser ERP Celery Worker
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/django_erp
Environment=PATH=/path/to/django_erp/venv/bin
ExecStart=/path/to/django_erp/venv/bin/celery -A better_laser_erp worker -l info
Restart=always

[Install]
WantedBy=multi-user.target
```

启用并启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable better-laser-erp.service
sudo systemctl enable better-laser-erp-celery.service
sudo systemctl start better-laser-erp.service
sudo systemctl start better-laser-erp-celery.service
```

## Docker 部署

### 1. 使用 Docker Compose

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 2. 数据库初始化

```bash
# 运行迁移
docker-compose exec web python manage.py migrate

# 创建超级用户
docker-compose exec web python manage.py createsuperuser

# 收集静态文件
docker-compose exec web python manage.py collectstatic --noinput
```

## 数据迁移

### 从旧系统迁移数据

1. **准备数据文件**
   ```bash
   # 将旧系统数据导出为 CSV 格式
   # 放置在 legacy_data/ 目录下
   ```

2. **运行迁移命令**
   ```bash
   # 迁移所有数据
   python manage.py migrate_legacy_data
   
   # 只迁移特定模块
   python manage.py migrate_legacy_data --module customers
   
   # 干运行（测试）
   python manage.py migrate_legacy_data --dry-run
   ```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证数据库配置信息
   - 确认防火墙设置

2. **静态文件无法加载**
   - 运行 `python manage.py collectstatic`
   - 检查 Nginx 配置
   - 验证文件权限

3. **Celery 任务不执行**
   - 检查 Redis 服务状态
   - 验证 Celery 配置
   - 查看 Celery 日志

4. **内存不足**
   - 增加服务器内存
   - 优化数据库查询
   - 配置缓存策略

### 日志查看

```bash
# Django 应用日志
sudo journalctl -u better-laser-erp.service -f

# Celery 日志
sudo journalctl -u better-laser-erp-celery.service -f

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 应用日志
tail -f logs/django.log
```

## 性能优化

### 1. 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_sales_order_date ON sales_salesorder(order_date);
CREATE INDEX idx_customer_code ON customers_customer(code);
CREATE INDEX idx_product_code ON products_product(code);
```

### 2. 缓存配置

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 3. 静态文件优化

```bash
# 启用 Gzip 压缩
# 配置 CDN
# 使用 WebP 图片格式
```

## 安全配置

### 1. 防火墙设置

```bash
# UFW 配置
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. 数据库安全

```bash
# MySQL 安全配置
sudo mysql_secure_installation
```

### 3. 应用安全

```python
# settings.py 生产环境配置
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

## 备份策略

### 1. 自动备份

```bash
# 添加到 crontab
0 2 * * * /path/to/django_erp/scripts/backup.sh

# 每日凌晨 2 点执行备份
```

### 2. 备份验证

```bash
# 定期测试备份恢复
./scripts/restore.sh backup_timestamp
```

## 监控和维护

### 1. 系统监控

- 使用 Prometheus + Grafana
- 配置告警规则
- 监控关键指标

### 2. 日志管理

- 配置日志轮转
- 集中日志收集
- 异常告警

### 3. 定期维护

- 数据库优化
- 清理临时文件
- 更新依赖包
- 安全补丁

## 支持

如果在安装过程中遇到问题，请：

1. 查看错误日志
2. 检查系统要求
3. 参考故障排除部分
4. 联系技术支持

更多信息请参考：
- [用户手册](user-guide.md)
- [API 文档](api.md)
- [开发指南](development.md)