#!/bin/bash
"""
恢复脚本

从备份文件中恢复系统
"""

# 配置变量
BACKUP_DIR="/var/backups/django_erp"
LOG_FILE="${BACKUP_DIR}/restore.log"

# 显示可用的备份文件
echo "可用的备份文件："
ls -la ${BACKUP_DIR}/*.tar.gz

# 提示用户选择备份文件
read -p "请输入要恢复的备份文件名：" BACKUP_FILE

# 检查备份文件是否存在
if [ ! -f ${BACKUP_DIR}/${BACKUP_FILE} ]; then
    echo "错误：备份文件不存在！"
    exit 1
fi

# 记录恢复开始
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 开始恢复..." >> ${LOG_FILE}
echo "恢复备份文件：${BACKUP_FILE}" >> ${LOG_FILE}

# 解压备份文件
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 解压备份文件..." >> ${LOG_FILE}
tar -xzf ${BACKUP_DIR}/${BACKUP_FILE} -C /tmp/django_erp_restore

# 停止相关服务（可选）
# echo "[$(date +"%Y-%m-%d %H:%M:%S")] 停止相关服务..." >> ${LOG_FILE}
# systemctl stop django_erp
# systemctl stop celery

# 恢复数据库
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 恢复数据库..." >> ${LOG_FILE}
DB_FILE=$(find /tmp/django_erp_restore -name "*.sql" -o -name "*.sqlite3" | head -1)
if [ -n "${DB_FILE}" ]; then
    if [[ "${DB_FILE}" == *.sql ]]; then
        # 恢复 SQL 数据库
        DB_ENGINE=$(grep DB_ENGINE /tmp/django_erp_restore/.env | cut -d '=' -f2)
        DB_NAME=$(grep DB_NAME /tmp/django_erp_restore/.env | cut -d '=' -f2)
        DB_USER=$(grep DB_USER /tmp/django_erp_restore/.env | cut -d '=' -f2)
        DB_PASSWORD=$(grep DB_PASSWORD /tmp/django_erp_restore/.env | cut -d '=' -f2)
        DB_HOST=$(grep DB_HOST /tmp/django_erp_restore/.env | cut -d '=' -f2)
        DB_PORT=$(grep DB_PORT /tmp/django_erp_restore/.env | cut -d '=' -f2)

        if [ "${DB_ENGINE}" = "django.db.backends.postgresql" ]; then
            echo "[$(date +"%Y-%m-%d %H:%M:%S")] 恢复 PostgreSQL 数据库..." >> ${LOG_FILE}
            PGPASSWORD=${DB_PASSWORD} psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} ${DB_NAME} < ${DB_FILE}
        elif [ "${DB_ENGINE}" = "django.db.backends.mysql" ]; then
            echo "[$(date +"%Y-%m-%d %H:%M:%S")] 恢复 MySQL 数据库..." >> ${LOG_FILE}
            mysql -h ${DB_HOST} -P ${DB_PORT} -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME} < ${DB_FILE}
        fi
    elif [[ "${DB_FILE}" == *.sqlite3 ]]; then
        # 恢复 SQLite 数据库
        echo "[$(date +"%Y-%m-%d %H:%M:%S")] 恢复 SQLite 数据库..." >> ${LOG_FILE}
        DB_NAME=$(grep DB_NAME /tmp/django_erp_restore/.env | cut -d '=' -f2)
        cp ${DB_FILE} ${DB_NAME}
    fi
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 未找到数据库备份文件" >> ${LOG_FILE}
fi

# 恢复文件
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 恢复文件..." >> ${LOG_FILE}
cp -r /tmp/django_erp_restore/* .

# 清理临时文件
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 清理临时文件..." >> ${LOG_FILE}
rm -rf /tmp/django_erp_restore

# 启动相关服务（可选）
# echo "[$(date +"%Y-%m-%d %H:%M:%S")] 启动相关服务..." >> ${LOG_FILE}
# systemctl start django_erp
# systemctl start celery

# 记录恢复结束
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 恢复完成！" >> ${LOG_FILE}
echo "----------------------------------------" >> ${LOG_FILE}

# 发送恢复通知（可选）
# echo "Django ERP 恢复完成: ${BACKUP_FILE}" | mail -s "Django ERP 恢复通知" admin@example.com

# 退出
exit 0
