# 服务器安全配置

## 1. 概述

本文档旨在确保Django ERP系统的服务器安全，通过配置防火墙、加强SSH安全和系统安全更新等措施，提高服务器的安全性和稳定性。

## 2. 防火墙配置

### 2.1 UFW 防火墙

#### 2.1.1 安装和启用

```bash
# 安装 UFW
sudo apt install ufw

# 启用 UFW
sudo ufw enable

# 查看状态
sudo ufw status
```

#### 2.1.2 配置规则

```bash
# 允许 SSH
sudo ufw allow ssh

# 允许 HTTP
sudo ufw allow 80/tcp

# 允许 HTTPS
sudo ufw allow 443/tcp

# 允许 Django 应用
sudo ufw allow 8000/tcp

# 允许 PostgreSQL (如果使用)
sudo ufw allow 5432/tcp

# 允许 Redis (如果使用)
sudo ufw allow 6379/tcp

# 拒绝所有其他入站流量
sudo ufw default deny incoming

# 允许所有出站流量
sudo ufw default allow outgoing
```

#### 2.1.3 检查配置

```bash
sudo ufw status verbose
```

### 2.2 iptables 配置

对于不使用 UFW 的系统，可以直接配置 iptables：

```bash
# 清除现有规则
sudo iptables -F

# 设置默认策略
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# 允许回环接口
sudo iptables -A INPUT -i lo -j ACCEPT

# 允许已建立的连接
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 允许 SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# 允许 HTTP
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT

# 允许 HTTPS
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 允许 Django 应用
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT

# 保存配置
sudo iptables-save > /etc/iptables/rules.v4
```

## 3. SSH 安全配置

### 3.1 配置 SSH

编辑 `/etc/ssh/sshd_config` 文件：

```bash
sudo nano /etc/ssh/sshd_config
```

修改以下配置：

```
# 禁用 root 登录
PermitRootLogin no

# 禁用密码登录（使用密钥认证）
PasswordAuthentication no

# 禁用空密码
PermitEmptyPasswords no

# 限制登录尝试次数
MaxAuthTries 3

# 限制登录时间
LoginGraceTime 30

# 禁用 X11 转发
X11Forwarding no

# 禁用 TCP 端口转发
AllowTcpForwarding no

# 禁用 Agent 转发
AllowAgentForwarding no

# 限制用户登录
AllowUsers your_username

# 更改 SSH 端口（可选）
# Port 2222
```

### 3.2 重启 SSH 服务

```bash
sudo systemctl restart sshd
```

### 3.3 生成 SSH 密钥

```bash
# 生成密钥对
ssh-keygen -t ed25519 -C "your_email@example.com"

# 复制公钥到服务器
ssh-copy-id username@server_ip
```

## 4. 系统安全更新

### 4.1 自动安全更新

#### 4.1.1 安装 unattended-upgrades

```bash
sudo apt install unattended-upgrades
```

#### 4.1.2 配置自动更新

```bash
sudo dpkg-reconfigure -plow unattended-upgrades
```

编辑配置文件 `/etc/apt/apt.conf.d/50unattended-upgrades`：

```
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}:${distro_codename}-updates";
};

Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";
```

### 4.2 定期手动更新

```bash
# 更新包列表
sudo apt update

# 升级所有包
sudo apt upgrade -y

# 升级系统
sudo apt dist-upgrade -y

# 清理无用包
sudo apt autoremove -y
sudo apt autoclean
```

## 5. 系统强化

### 5.1 禁用不必要的服务

```bash
# 查看运行中的服务
systemctl list-unit-files --type=service | grep enabled

# 禁用不必要的服务
sudo systemctl disable service_name
sudo systemctl stop service_name
```

### 5.2 配置系统限制

编辑 `/etc/security/limits.conf` 文件：

```
# 限制最大打开文件数
* soft nofile 65536
* hard nofile 65536

# 限制最大进程数
* soft nproc 4096
* hard nproc 4096
```

### 5.3 配置系统日志

确保系统日志配置正确，定期检查日志：

```bash
# 查看系统日志
sudo journalctl -f

# 查看安全日志
sudo grep "Failed password" /var/log/auth.log
```

## 6. 服务安全配置

### 6.1 Nginx 安全配置

编辑 Nginx 配置文件：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 配置
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全头部
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # 其他配置...
}
```

### 6.2 PostgreSQL 安全配置

编辑 PostgreSQL 配置文件 `/etc/postgresql/14/main/postgresql.conf`：

```
# 监听地址
listen_addresses = 'localhost'

# 最大连接数
max_connections = 100

# 密码加密
password_encryption = scram-sha-256
```

编辑 `/etc/postgresql/14/main/pg_hba.conf`：

```
# 本地连接
local   all             all                                     scram-sha-256

# IPv4 连接
host    all             all             127.0.0.1/32            scram-sha-256

# IPv6 连接
host    all             all             ::1/128                 scram-sha-256
```

## 7. 监控和告警

### 7.1 系统监控

安装和配置监控工具：

```bash
# 安装 htop
sudo apt install htop

# 安装 net-tools
sudo apt install net-tools

# 安装 fail2ban
sudo apt install fail2ban
```

### 7.2 配置 fail2ban

创建 fail2ban 配置文件 `/etc/fail2ban/jail.local`：

```
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 3600
```

重启 fail2ban：

```bash
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
```

## 8. 安全审计

### 8.1 定期安全扫描

```bash
# 安装 nmap
sudo apt install nmap

# 扫描开放端口
nmap -sV localhost

# 安装 lynis
sudo apt install lynis

# 运行安全审计
sudo lynis audit system
```

### 8.2 检查系统漏洞

```bash
# 安装 OpenVAS（可选）
sudo apt install openvas

# 启动 OpenVAS
sudo gvm-setup
sudo gvm-start
```

## 9. 应急响应

### 9.1 安全事件响应

1. **检测**: 发现安全事件
2. **响应**: 立即采取措施控制影响
3. **调查**: 分析事件原因
4. **恢复**: 恢复系统正常运行
5. **预防**: 采取措施防止类似事件再次发生

### 9.2 紧急措施

- **隔离系统**: 断开网络连接
- **备份证据**: 保存日志和相关文件
- **重置密码**: 更改所有账户密码
- **更新系统**: 安装最新安全补丁

## 10. 最佳实践

- **最小权限**: 只授予必要的权限
- **定期更新**: 及时安装安全补丁
- **强密码**: 使用复杂密码和密钥认证
- **日志监控**: 定期检查系统日志
- **备份**: 定期备份系统和数据
- **安全培训**: 提高团队安全意识

## 11. 结论

通过实施本服务器安全配置，可以显著提高服务器的安全性和稳定性，减少安全风险。服务器安全是一个持续的过程，需要定期更新和维护，以适应新的安全威胁和挑战。
