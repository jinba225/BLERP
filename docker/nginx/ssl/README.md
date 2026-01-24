# SSL 证书配置说明

## 开发环境

开发环境使用 HTTP,无需配置 SSL 证书。

## 生产环境

生产环境强制使用 HTTPS,需要配置 SSL 证书。

### 方式1: 使用 Let's Encrypt (推荐)

Let's Encrypt 提供免费的 SSL 证书,自动续期。

```bash
# 安装 certbot
apt-get update && apt-get install -y certbot

# 生成证书(需要域名解析到服务器)
certbot certonly --webroot -w /var/www/certbot \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos \
  --no-eff-email

# 证书会生成在
/etc/letsencrypt/live/yourdomain.com/fullchain.pem
/etc/letsencrypt/live/yourdomain.com/privkey.pem

# 复制到项目目录
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/nginx/ssl/key.pem

# 设置自动续期 (crontab)
0 0 1 * * certbot renew --quiet && docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx
```

### 方式2: 自签名证书 (仅用于测试)

⚠️ **警告**: 自签名证书仅用于测试环境,浏览器会显示安全警告!

```bash
# 进入 SSL 目录
cd docker/nginx/ssl

# 生成私钥和证书 (有效期365天)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem \
  -out cert.pem \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=BetterLaser/OU=IT/CN=localhost"

# 查看证书信息
openssl x509 -in cert.pem -text -noout

# 设置权限
chmod 600 key.pem
chmod 644 cert.pem
```

### 方式3: 商业证书

如果已购买商业 SSL 证书:

1. 将证书文件复制到 `docker/nginx/ssl/cert.pem`
2. 将私钥文件复制到 `docker/nginx/ssl/key.pem`
3. 如果有证书链,需要将中间证书合并到 cert.pem

```bash
# 合并证书链
cat your_domain.crt intermediate.crt root.crt > docker/nginx/ssl/cert.pem
cp your_domain.key docker/nginx/ssl/key.pem
```

## 证书文件权限

确保证书文件权限正确:

```bash
chmod 600 docker/nginx/ssl/key.pem  # 私钥必须严格保护
chmod 644 docker/nginx/ssl/cert.pem  # 公钥证书可读
chown root:root docker/nginx/ssl/*   # 生产环境推荐 root 所有
```

## 证书验证

```bash
# 检查证书有效期
openssl x509 -in docker/nginx/ssl/cert.pem -noout -dates

# 检查证书和私钥是否匹配
openssl x509 -noout -modulus -in docker/nginx/ssl/cert.pem | openssl md5
openssl rsa -noout -modulus -in docker/nginx/ssl/key.pem | openssl md5
# 两个 MD5 值应该相同

# 测试 HTTPS 连接
curl -I https://yourdomain.com
```

## 注意事项

1. **私钥保护**: `key.pem` 文件包含私钥,必须严格保护,不能提交到 Git
2. **证书续期**: Let's Encrypt 证书90天有效期,需要设置自动续期
3. **证书链**: 确保包含完整的证书链,否则某些客户端会显示不可信
4. **HSTS**: 生产环境已启用 HSTS,确保证书始终有效
5. **通配符证书**: 如果有多个子域名,考虑申请通配符证书 (*.yourdomain.com)

## Git 忽略

已在 `.gitignore` 中排除:

```
docker/nginx/ssl/*.pem
docker/nginx/ssl/*.key
docker/nginx/ssl/*.crt
```

证书文件不应提交到版本控制系统中!
