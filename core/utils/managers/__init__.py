"""
Core utils managers package
"""
from .database_manager import DatabaseManager
from .backup_manager import BackupManager
from .test_data_generator import TestDataGenerator

# 保持向后兼容
DatabaseHelper = DatabaseManager

# 便捷导出
__all__ = [
    'DatabaseManager',
    'BackupManager',
    'TestDataGenerator',
]
