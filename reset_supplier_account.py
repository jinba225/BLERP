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

# 查找测试供应商丁的ID
cursor.execute("SELECT id FROM suppliers_supplier WHERE name = '测试供应商丁' AND is_deleted = 0")
supplier_result = cursor.fetchone()

if supplier_result:
    supplier_id = supplier_result[0]
    print(f'测试供应商丁的ID: {supplier_id}')
    
    # 重置该供应商的应付账款记录为原始的未税金额
    cursor.execute("""
        UPDATE finance_supplier_account 
        SET invoice_amount = 550000, balance = 550000 
        WHERE supplier_id = ? AND is_deleted = 0
    """, (supplier_id,))
    
    # 提交事务
    conn.commit()
    print('已重置测试供应商丁的应付账款记录为 ¥550000')
else:
    print('未找到测试供应商丁')

# 关闭连接
conn.close()
