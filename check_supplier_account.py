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
    
    # 查找该供应商的应付账款
    cursor.execute("""
        SELECT 
            invoice_number, 
            invoice_amount, 
            paid_amount, 
            balance 
        FROM 
            finance_supplier_account 
        WHERE 
            supplier_id = ? AND is_deleted = 0
    """, (supplier_id,))
    
    accounts = cursor.fetchall()
    print(f'应付账款数量: {len(accounts)}')
    
    for account in accounts:
        invoice_number = account[0] if account[0] else "无"
        print(f'  发票号: {invoice_number}, 应付金额: ¥{account[1]}, 已付金额: ¥{account[2]}, 未付余额: ¥{account[3]}')
        
    # 查找该供应商的应付明细
    cursor.execute("""
        SELECT 
            detail_type, 
            amount, 
            allocated_amount 
        FROM 
            finance_supplier_accountdetail 
        WHERE 
            supplier_id = ? AND is_deleted = 0
    """, (supplier_id,))
    
    details = cursor.fetchall()
    print(f'应付明细数量: {len(details)}')
    
    for detail in details:
        detail_type = '收货正应付' if detail[0] == 'receipt' else '退货负应付'
        print(f'    明细类型: {detail_type}, 金额: ¥{detail[1]}, 已核销: ¥{detail[2]}')
else:
    print('未找到测试供应商丁')

# 关闭连接
conn.close()
