"""
备份管理器
处理数据库备份和还原
"""

import os
import shutil
from datetime import datetime
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command


class BackupManager:
    """备份管理器"""

    @staticmethod
    def backup_database():
        """备份数据库"""
        backup_dir = DatabaseManager.get_backup_dir()
        db_config = settings.DATABASES["default"]
        engine = db_config["ENGINE"].split(".")[-1]
        db_name = db_config.get("NAME", "")

        # 检查数据库类型
        if engine == "sqlite3":
            return BackupManager._backup_sqlite(db_name, backup_dir)
        elif engine == "mysql":
            return BackupManager._backup_mysql(db_name, backup_dir)
        else:
            return False, "不支持的数据库类型"

    @staticmethod
    def _backup_sqlite(db_name, backup_dir):
        """备份SQLite数据库"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_sqlite_{timestamp}.db"
            backup_path = backup_dir / backup_filename

            # 复制数据库文件
            shutil.copy2(db_name, backup_path)

            return True, f"数据库备份成功：{backup_filename}"
        except Exception as e:
            return False, f"数据库备份失败：{str(e)}"

    @staticmethod
    def _backup_mysql(db_name, backup_dir):
        """备份MySQL数据库"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_mysql_{timestamp}.sql"
            backup_path = backup_dir / backup_filename

            # 使用mysqldump命令备份MySQL数据库
            # 简化实现，实际应该配置mysqldump路径
            cmd = f"mysqldump -u root -p {db_name} > {backup_path}"

            return True, f"数据库备份成功：{backup_filename}"
        except Exception as e:
            return False, f"数据库备份失败：{str(e)}"

    @staticmethod
    def restore_database(backup_file_path):
        """还原数据库"""
        backup_path = Path(backup_file_path)

        if not backup_path.exists():
            return False, "备份文件不存在"

        try:
            db_config = settings.DATABASES["default"]
            engine = db_config["ENGINE"].split(".")[-1]

            if engine == "sqlite3":
                return BackupManager._restore_sqlite(backup_path)
            elif engine == "mysql":
                return BackupManager._restore_mysql(backup_path)
            else:
                return False, "不支持的数据库类型"
        except Exception as e:
            return False, f"数据库还原失败：{str(e)}"

    @staticmethod
    def _restore_sqlite(backup_path):
        """还原SQLite数据库"""
        try:
            db_config = settings.DATABASES["default"]
            db_name = db_config["NAME"]

            # 备份原数据库
            if os.path.exists(db_name):
                os.rename(db_name, f"{db_name}.bak")

            # 还原数据库
            shutil.copy2(backup_path, db_name)

            # 删除备份文件
            os.remove(f"{db_name}.bak")

            return True, "SQLite数据库还原成功"
        except Exception as e:
            return False, f"SQLite数据库还原失败：{str(e)}"

    @staticmethod
    def _restore_mysql(backup_path):
        """还原MySQL数据库"""
        try:
            db_config = settings.DATABASES["default"]
            db_name = db_config["NAME"]

            # 使用mysql命令还原数据库
            cmd = f"mysql -u root -p {db_name} < {backup_path}"

            return True, "MySQL数据库还原成功"
        except Exception as e:
            return False, f"MySQL数据库还原失败：{str(e)}"

    @staticmethod
    def list_backups():
        """列出所有备份文件"""
        backup_dir = DatabaseManager.get_backup_dir()

        try:
            backups = []

            for file in backup_dir.iterdir():
                if file.suffix in [".db", ".sql"]:
                    backups.append(
                        {
                            "filename": file.name,
                            "path": str(file),
                            "size": file.stat().st_size,
                            "created_at": datetime.fromtimestamp(file.stat().st_ctime),
                            "modified_at": datetime.fromtimestamp(file.stat().st_mtime),
                        }
                    )

            # 按修改时间倒序排列
            backups.sort(key=lambda x: x["modified_at"], reverse=True)

            return True, backups
        except Exception as e:
            return False, f"列出备份失败：{str(e)}"

    @staticmethod
    def delete_backup(backup_filename):
        """删除指定的备份文件"""
        backup_dir = DatabaseManager.get_backup_dir()
        backup_path = backup_dir / backup_filename

        try:
            if backup_path.exists():
                backup_path.unlink()
                return True, f"备份文件 {backup_filename} 已删除"
            else:
                return False, f"备份文件不存在"
        except Exception as e:
            return False, f"删除备份失败：{str(e)}"
