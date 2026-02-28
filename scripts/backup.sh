#!/bin/bash
"""
自动备份脚本

定期备份数据库和重要文件
"""

# 配置变量
BACKUP_DIR="/var/backups/django_erp"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="django_erp_backup_${DATE}.tar.gz"
LOG_FILE="${BACKUP_DIR}/backup.log"

# 数据库配置
DB_ENGINE=$(grep DB_ENGINE .env | cut -d '=' -f2)
DB_NAME=$(grep DB_NAME .env | cut -d '=' -f2)
DB_USER=$(grep DB_USER .env | cut -d '=' -f2)
DB_PASSWORD=$(grep DB_PASSWORD .env | cut -d '=' -f2)
DB_HOST=$(grep DB_HOST .env | cut -d '=' -f2)
DB_PORT=$(grep DB_PORT .env | cut -d '=' -f2)

# 创建备份目录
mkdir -p ${BACKUP_DIR}

# 记录备份开始
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 开始备份..." >> ${LOG_FILE}

# 备份数据库
if [ "${DB_ENGINE}" = "django.db.backends.postgresql" ]; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 备份 PostgreSQL 数据库..." >> ${LOG_FILE}
    PGPASSWORD=${DB_PASSWORD} pg_dump -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} ${DB_NAME} > ${BACKUP_DIR}/${DB_NAME}_${DATE}.sql
elif [ "${DB_ENGINE}" = "django.db.backends.mysql" ]; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 备份 MySQL 数据库..." >> ${LOG_FILE}
    mysqldump -h ${DB_HOST} -P ${DB_PORT} -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME} > ${BACKUP_DIR}/${DB_NAME}_${DATE}.sql
elif [ "${DB_ENGINE}" = "django.db.backends.sqlite3" ]; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 备份 SQLite 数据库..." >> ${LOG_FILE}
    cp ${DB_NAME} ${BACKUP_DIR}/${DB_NAME}_${DATE}.sqlite3
fi

# 备份重要文件
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 备份重要文件..." >> ${LOG_FILE}
tar -czf ${BACKUP_DIR}/${BACKUP_FILE} \
    --exclude="*.pyc" \
    --exclude="__pycache__" \
    --exclude="venv" \
    --exclude="node_modules" \
    --exclude="staticfiles" \
    --exclude="media" \
    .env \
    django_erp/ \
    apps/ \
    scripts/ \
    docs/ \
    ${BACKUP_DIR}/${DB_NAME}_${DATE}.*

# 清理临时数据库备份文件
rm -f ${BACKUP_DIR}/${DB_NAME}_${DATE}.*

# 清理过期备份（保留最近7天的备份）
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 清理过期备份..." >> ${LOG_FILE}
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +7 -delete

# 验证备份文件
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 验证备份文件..." >> ${LOG_FILE}
if [ -f ${BACKUP_DIR}/${BACKUP_FILE} ]; then
    BACKUP_SIZE=$(du -h ${BACKUP_DIR}/${BACKUP_FILE} | cut -f1)
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 备份完成！备份文件: ${BACKUP_FILE}, 大小: ${BACKUP_SIZE}" >> ${LOG_FILE}
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 备份失败！备份文件不存在" >> ${LOG_FILE}
fi

# 记录备份结束
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 备份结束" >> ${LOG_FILE}
echo "----------------------------------------" >> ${LOG_FILE}

# 发送备份通知（可选）
# echo "Django ERP 备份完成: ${BACKUP_FILE}" | mail -s "Django ERP 备份通知" admin@example.com

# 退出
exit 0