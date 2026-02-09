#!/bin/bash
# Django ERP 数据库备份脚本
# 用法: ./scripts/backup.sh [环境]
# 示例: ./scripts/backup.sh production

set -e  # 遇到错误立即退出

# ============================================
# 配置部分
# ============================================

# 从环境变量或命令行参数获取环境名称
ENVIRONMENT=${1:-${ENVIRONMENT:-development}}

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 备份配置
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}  # 保留30天的备份

# 数据库配置（从环境变量读取）
DB_ENGINE=${DB_ENGINE:-django.db.backends.sqlite3}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-django_erp}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-}

# ============================================
# 函数定义
# ============================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
    exit 1
}

success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log "创建备份目录: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi
}

backup_postgresql() {
    local backup_file="$BACKUP_DIR/postgresql_${ENVIRONMENT}_${DATE}.sql.gz"

    log "开始备份PostgreSQL数据库: $DB_NAME"

    # 检查pg_dump是否可用
    if ! command -v pg_dump &> /dev/null; then
        error "pg_dump未找到，请安装PostgreSQL客户端工具"
    fi

    # 使用pg_dump备份并压缩
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-owner \
        --no-acl \
        --verbose \
        2>&1 | gzip > "$backup_file"

    if [ $? -eq 0 ]; then
        success "PostgreSQL备份完成: $backup_file"
        local size=$(du -h "$backup_file" | cut -f1)
        log "备份文件大小: $size"

        # 创建备份信息文件
        cat > "$backup_file.info" << EOF
备份时间: $(date)
环境: $ENVIRONMENT
数据库: $DB_NAME
文件大小: $size
主机: $DB_HOST:$DB_PORT
数据库引擎: PostgreSQL
EOF
    else
        error "PostgreSQL备份失败"
    fi
}

backup_mysql() {
    local backup_file="$BACKUP_DIR/mysql_${ENVIRONMENT}_${DATE}.sql.gz"

    log "开始备份MySQL数据库: $DB_NAME"

    # 检查mysqldump是否可用
    if ! command -v mysqldump &> /dev/null; then
        error "mysqldump未找到，请安装MySQL客户端工具"
    fi

    # 使用mysqldump备份并压缩
    mysqldump \
        -h"$DB_HOST" \
        -P"$DB_PORT" \
        -u"$DB_USER" \
        -p"$DB_PASSWORD" \
        --single-transaction \
        --routines \
        --triggers \
        "$DB_NAME" 2>&1 | gzip > "$backup_file"

    if [ $? -eq 0 ]; then
        success "MySQL备份完成: $backup_file"
        local size=$(du -h "$backup_file" | cut -f1)
        log "备份文件大小: $size"

        # 创建备份信息文件
        cat > "$backup_file.info" << EOF
备份时间: $(date)
环境: $ENVIRONMENT
数据库: $DB_NAME
文件大小: $size
主机: $DB_HOST:$DB_PORT
数据库引擎: MySQL
EOF
    else
        error "MySQL备份失败"
    fi
}

backup_sqlite() {
    local db_file="${DB_NAME:-./db.sqlite3}"
    local backup_file="$BACKUP_DIR/sqlite_${ENVIRONMENT}_${DATE}.sqlite3"

    log "开始备份SQLite数据库: $db_file"

    if [ ! -f "$db_file" ]; then
        error "SQLite数据库文件不存在: $db_file"
    fi

    # 复制SQLite文件
    cp "$db_file" "$backup_file"

    if [ $? -eq 0 ]; then
        # 压缩备份文件
        gzip "$backup_file"
        backup_file="${backup_file}.gz"

        success "SQLite备份完成: $backup_file"
        local size=$(du -h "$backup_file" | cut -f1)
        log "备份文件大小: $size"

        # 创建备份信息文件
        cat > "${backup_file}.info" << EOF
备份时间: $(date)
环境: $ENVIRONMENT
数据库: $db_file
文件大小: $size
数据库引擎: SQLite
EOF
    else
        error "SQLite备份失败"
    fi
}

backup_media_files() {
    local backup_file="$BACKUP_DIR/media_${ENVIRONMENT}_${DATE}.tar.gz"

    log "开始备份媒体文件: ./media"

    if [ ! -d "./media" ]; then
        log "媒体文件目录不存在，跳过"
        return
    fi

    tar -czf "$backup_file" ./media 2>&1

    if [ $? -eq 0 ]; then
        success "媒体文件备份完成: $backup_file"
        local size=$(du -h "$backup_file" | cut -f1)
        log "备份文件大小: $size"
    else
        error "媒体文件备份失败"
    fi
}

cleanup_old_backups() {
    log "清理超过 ${RETENTION_DAYS} 天的旧备份"

    # 删除旧的备份文件
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "*.sqlite3.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "*.info" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true

    success "旧备份清理完成"
}

# ============================================
# 主程序
# ============================================

main() {
    log "=========================================="
    log "开始数据库备份 - 环境: $ENVIRONMENT"
    log "=========================================="

    create_backup_dir

    # 根据数据库类型选择备份方法
    case "$DB_ENGINE" in
        *postgresql*)
            backup_postgresql
            ;;
        *mysql*)
            backup_mysql
            ;;
        *sqlite3*)
            backup_sqlite
            ;;
        *)
            error "不支持的数据库引擎: $DB_ENGINE"
            ;;
    esac

    # 备份媒体文件（可选）
    if [ "${BACKUP_MEDIA:-false}" = "true" ]; then
        backup_media_files
    fi

    # 清理旧备份
    cleanup_old_backups

    log "=========================================="
    success "备份流程完成！"
    log "备份位置: $BACKUP_DIR"
    log "=========================================="
}

# 执行主程序
main "$@"
