#!/usr/bin/env python3
import os
import sys

# 直接导入必要的模块，避免Django设置的依赖
import sqlite3

# 数据库路径
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查找所有供应商
cursor.execute("SELECT id, name, code FROM suppliers_supplier WHERE is_deleted = 0 ORDER BY id")
suppliers = cursor.fetchall()

print(f'供应商数量: {len(suppliers)}')
for supplier in suppliers:
    print(f'ID: {supplier[0]}, 名称: {supplier[1]}, 代码: {supplier[2]}')

# 关闭连接
conn.close()
