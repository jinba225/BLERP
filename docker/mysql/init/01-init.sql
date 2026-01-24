-- ============================================
-- MySQL 初始化脚本
-- ============================================
-- 此脚本在数据库首次启动时自动执行

-- 设置默认字符集和排序规则
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 确保时区设置正确
SET time_zone = '+08:00';

-- 创建数据库(如果不存在)
CREATE DATABASE IF NOT EXISTS django_erp
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 授予用户完整权限
GRANT ALL PRIVILEGES ON django_erp.* TO 'django_user'@'%';
FLUSH PRIVILEGES;

-- 显示数据库信息
SELECT
    '✅ MySQL 初始化完成' AS Status,
    DATABASE() AS CurrentDB,
    @@character_set_database AS Charset,
    @@collation_database AS Collation,
    @@time_zone AS TimeZone;
