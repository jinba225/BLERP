"""
数据库管理器
处理数据库连接和基础操作
"""

from pathlib import Path

from django.conf import settings


class DatabaseManager:
    """数据库管理器"""

    @staticmethod
    def get_backup_dir():
        """获取备份目录路径"""
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(exist_ok=True)
        return backup_dir

    @staticmethod
    def is_sqlite():
        """检查是否使用SQLite数据库"""
        return settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"

    @staticmethod
    def is_mysql():
        """检查是否使用MySQL数据库"""
        return settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql"

    @staticmethod
    def get_db_info():
        """获取数据库信息"""
        db_config = settings.DATABASES["default"]
        engine = db_config["ENGINE"].split(".")[-1]

        info = {
            "engine": engine,
            "name": db_config.get("NAME", ""),
        }

        if DatabaseManager.is_sqlite():
            db_path = Path(db_config["NAME"])
            if db_path.exists():
                info["size"] = db_path.stat().st_size
                info["path"] = str(db_path)

        return info

    @staticmethod
    def get_db_connection():
        """获取数据库连接"""
        from django.db import connection

        return connection

    @staticmethod
    def close_db_connection():
        """关闭数据库连接"""
        from django.db import connection

        connection.close()

    @staticmethod
    def test_connection():
        """测试数据库连接"""
        try:
            connection = DatabaseManager.get_db_connection()
            connection.cursor().execute("SELECT 1")
            return True, "数据库连接正常"
        except Exception as e:
            return False, f"数据库连接失败：{str(e)}"
