#!/bin/bash
"""
备份验证脚本

验证备份文件的完整性和可恢复性
"""

# 配置变量
BACKUP_DIR="/var/backups/django_erp"
LOG_FILE="${BACKUP_DIR}/verify_backup.log"

# 显示可用的备份文件
echo "可用的备份文件："
ls -la ${BACKUP_DIR}/*.tar.gz

# 提示用户选择要验证的备份文件
read -p "请输入要验证的备份文件名：" BACKUP_FILE

# 检查备份文件是否存在
if [ ! -f ${BACKUP_DIR}/${BACKUP_FILE} ]; then
    echo "错误：备份文件不存在！"
    exit 1
fi

# 记录验证开始
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 开始验证备份..." >> ${LOG_FILE}
echo "验证备份文件：${BACKUP_FILE}" >> ${LOG_FILE}

# 验证备份文件的完整性
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 验证备份文件完整性..." >> ${LOG_FILE}
if gzip -t ${BACKUP_DIR}/${BACKUP_FILE}; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 备份文件完整性验证通过" >> ${LOG_FILE}
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 备份文件完整性验证失败！" >> ${LOG_FILE}
    exit 1
fi

# 检查备份文件的内容
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 检查备份文件内容..." >> ${LOG_FILE}
tar -tzf ${BACKUP_DIR}/${BACKUP_FILE} | head -20 >> ${LOG_FILE}

# 检查是否包含关键文件
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 检查关键文件..." >> ${LOG_FILE}
KEY_FILES=(".env" "django_erp/settings.py" "apps/")
for file in "${KEY_FILES[@]}"; do
    if tar -tzf ${BACKUP_DIR}/${BACKUP_FILE} | grep -q "${file}"; then
        echo "[$(date +"%Y-%m-%d %H:%M:%S")] 包含关键文件: ${file}" >> ${LOG_FILE}
    else
        echo "[$(date +"%Y-%m-%d %H:%M:%S")] 缺少关键文件: ${file}" >> ${LOG_FILE}
    fi
done

# 检查是否包含数据库备份
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 检查数据库备份..." >> ${LOG_FILE}
if tar -tzf ${BACKUP_DIR}/${BACKUP_FILE} | grep -q "\.sql\|\.sqlite3"; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 包含数据库备份" >> ${LOG_FILE}
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 缺少数据库备份" >> ${LOG_FILE}
fi

# 测试解压
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 测试解压..." >> ${LOG_FILE}
mkdir -p /tmp/django_erp_verify
if tar -xzf ${BACKUP_DIR}/${BACKUP_FILE} -C /tmp/django_erp_verify; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 解压测试通过" >> ${LOG_FILE}
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 解压测试失败！" >> ${LOG_FILE}
fi

# 清理临时文件
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 清理临时文件..." >> ${LOG_FILE}
rm -rf /tmp/django_erp_verify

# 记录验证结束
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 备份验证完成！" >> ${LOG_FILE}
echo "----------------------------------------" >> ${LOG_FILE}

# 发送验证通知（可选）
# echo "Django ERP 备份验证完成: ${BACKUP_FILE}" | mail -s "Django ERP 备份验证通知" admin@example.com

# 退出
exit 0
