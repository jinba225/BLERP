# BetterLaser ERP 部署指南

本文档详细介绍如何在生产环境中部署 BetterLaser ERP 系统。

## 系统要求

### 硬件要求
- **CPU**: 4核心以上
- **内存**: 8GB以上（推荐16GB）
- **存储**: 100GB以上SSD硬盘
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Python**: 3.8+
- **Node.js**: 16+
- **MySQL**: 8.0+
- **Redis**: 6.0+
- **Nginx**: 1.18+

## 快速部署

### 1. 自动部署（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd django_erp

# 运行部署脚本
./deploy.sh
```

部署脚本会自动完成以下操作：
- 检查系统环境
- 创建虚拟环境
- 安装依赖
- 配置数据库
- 收集静态文件
- 设置系统服务

### 2. 手动部署

#### 步骤1: 环境准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础软件
sudo apt install -y python3 python3-pip python3-venv nodejs npm mysql-server redis-server nginx git

# 启动服务
sudo systemctl start mysql
sudo systemctl start redis-server
sudo systemctl enable mysql
sudo systemctl enable redis-server
```

#### 步骤2: 数据库配置

```bash
# 登录MySQL
sudo mysql -u root -p

# 创建数据库和用户
CREATE DATABASE better_laser_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'erp_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON better_laser_erp.* TO 'erp_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 步骤3: 应用部署

```bash
# 克隆项目
git clone <repository-url>
cd django_erp

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 安装Node.js依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 收集静态文件
python manage.py collectstatic --noinput

# 构建前端资源
npm run build
```

## 生产环境配置

### 1. Nginx 配置

创建 `/etc/nginx/sites-available/better-laser-erp`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    client_max_body_size 50M;

    # Static files
    location /static/ {
        alias /path/to/django_erp/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /path/to/django_erp/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Django application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/better-laser-erp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. Systemd 服务配置

#### Django 应用服务

创建 `/etc/systemd/system/better-laser-erp.service`：

```ini
[Unit]
Description=BetterLaser ERP Django Application
After=network.target mysql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/django_erp
Environment=PATH=/path/to/django_erp/venv/bin
EnvironmentFile=/path/to/django_erp/.env
ExecStart=/path/to/django_erp/venv/bin/gunicorn better_laser_erp.wsgi:application --bind 127.0.0.1:8000 --workers 4 --timeout 60
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### Celery Worker 服务

创建 `/etc/systemd/system/better-laser-erp-celery.service`：

```ini
[Unit]
Description=BetterLaser ERP Celery Worker
After=network.target mysql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/django_erp
Environment=PATH=/path/to/django_erp/venv/bin
EnvironmentFile=/path/to/django_erp/.env
ExecStart=/path/to/django_erp/venv/bin/celery -A better_laser_erp worker -l info
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### Celery Beat 服务

创建 `/etc/systemd/system/better-laser-erp-celery-beat.service`：

```ini
[Unit]
Description=BetterLaser ERP Celery Beat
After=network.target mysql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/django_erp
Environment=PATH=/path/to/django_erp/venv/bin
EnvironmentFile=/path/to/django_erp/.env
ExecStart=/path/to/django_erp/venv/bin/celery -A better_laser_erp beat -l info
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启用并启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable better-laser-erp.service
sudo systemctl enable better-laser-erp-celery.service
sudo systemctl enable better-laser-erp-celery-beat.service
sudo systemctl start better-laser-erp.service
sudo systemctl start better-laser-erp-celery.service
sudo systemctl start better-laser-erp-celery-beat.service
```

### 3. SSL 证书配置

#### 使用 Let's Encrypt（推荐）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 设置自动续期
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 4. 防火墙配置

```bash
# 启用UFW
sudo ufw enable

# 允许SSH
sudo ufw allow ssh

# 允许HTTP和HTTPS
sudo ufw allow 'Nginx Full'

# 检查状态
sudo ufw status
```

## 监控和日志

### 1. 日志配置

应用日志位置：
- Django: `/path/to/django_erp/logs/django.log`
- Nginx: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- MySQL: `/var/log/mysql/error.log`

### 2. 监控设置

#### 系统监控

```bash
# 安装监控工具
sudo apt install htop iotop nethogs

# 检查服务状态
sudo systemctl status better-laser-erp
sudo systemctl status better-laser-erp-celery
sudo systemctl status better-laser-erp-celery-beat
```

#### 应用监控

```bash
# 检查Django应用
curl -I http://localhost:8000/

# 检查数据库连接
python manage.py dbshell

# 检查Redis连接
redis-cli ping
```

## 备份策略

### 1. 自动备份

设置定时备份任务：

```bash
# 编辑crontab
sudo crontab -e

# 添加备份任务（每天凌晨2点）
0 2 * * * /path/to/django_erp/scripts/backup.sh

# 添加日志清理任务（每周日凌晨3点）
0 3 * * 0 find /path/to/django_erp/logs -name "*.log" -mtime +30 -delete
```

### 2. 备份验证

定期验证备份文件的完整性：

```bash
# 测试数据库备份
gunzip -t /var/backups/better-laser-erp/database_*.sql.gz

# 测试文件备份
tar -tzf /var/backups/better-laser-erp/media_*.tar.gz > /dev/null
```

## 性能优化

### 1. 数据库优化

MySQL 配置优化（`/etc/mysql/mysql.conf.d/mysqld.cnf`）：

```ini
[mysqld]
# InnoDB Settings
innodb_buffer_pool_size = 2G
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# Query Cache
query_cache_type = 1
query_cache_size = 256M

# Connection Settings
max_connections = 200
wait_timeout = 600
interactive_timeout = 600
```

### 2. Redis 优化

Redis 配置优化（`/etc/redis/redis.conf`）：

```ini
# Memory Management
maxmemory 1gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Network
tcp-keepalive 300
timeout 0
```

### 3. 应用优化

```python
# settings.py 生产环境优化
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']

# 数据库连接池
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'CONN_MAX_AGE': 3600,  # 连接池
    }
}

# 缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}

# 静态文件压缩
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

## 安全配置

### 1. 系统安全

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 配置自动安全更新
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# 配置fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 2. 应用安全

```python
# settings.py 安全配置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
```

## 故障排除

### 常见问题

1. **服务无法启动**
   ```bash
   sudo systemctl status better-laser-erp
   sudo journalctl -u better-laser-erp -f
   ```

2. **数据库连接失败**
   ```bash
   python manage.py dbshell
   sudo systemctl status mysql
   ```

3. **静态文件404**
   ```bash
   python manage.py collectstatic --noinput
   sudo nginx -t
   ```

4. **Celery任务不执行**
   ```bash
   sudo systemctl status better-laser-erp-celery
   redis-cli ping
   ```

### 日志分析

```bash
# 查看应用日志
tail -f /path/to/django_erp/logs/django.log

# 查看Nginx日志
tail -f /var/log/nginx/error.log

# 查看系统日志
sudo journalctl -f
```

## 维护计划

### 日常维护
- 检查服务状态
- 监控磁盘空间
- 查看错误日志
- 验证备份

### 周期维护
- 更新系统补丁
- 清理日志文件
- 数据库优化
- 性能监控

### 定期维护
- 安全审计
- 备份恢复测试
- 容量规划
- 系统升级

## 扩展部署

### 负载均衡

使用多台服务器部署时的配置：

```nginx
upstream django_backend {
    server 192.168.1.10:8000;
    server 192.168.1.11:8000;
    server 192.168.1.12:8000;
}

server {
    location / {
        proxy_pass http://django_backend;
    }
}
```

### 数据库集群

配置MySQL主从复制或集群部署。

### 容器化部署

使用Docker和Docker Compose进行容器化部署：

```bash
docker-compose up -d
```

## 支持和联系

如有部署问题，请：
1. 查看日志文件
2. 检查配置文件
3. 参考故障排除指南
4. 联系技术支持团队
