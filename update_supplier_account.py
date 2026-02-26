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
    
    # 查找该供应商的应付账款，只选择发票金额为550000的记录（未税金额）
    cursor.execute("""
        SELECT 
            id, invoice_number, invoice_amount, paid_amount, balance 
        FROM 
            finance_supplier_account 
        WHERE 
            supplier_id = ? AND is_deleted = 0 AND invoice_amount = 550000
    """, (supplier_id,))
    
    accounts = cursor.fetchall()
    print(f'符合条件的应付账款数量: {len(accounts)}')
    
    if len(accounts) == 0:
        # 查找所有应付账款记录，查看当前状态
        cursor.execute("""
            SELECT 
                id, invoice_number, invoice_amount, paid_amount, balance 
            FROM 
                finance_supplier_account 
            WHERE 
                supplier_id = ? AND is_deleted = 0
        """, (supplier_id,))
        
        all_accounts = cursor.fetchall()
        print(f'所有应付账款数量: {len(all_accounts)}')
        for account in all_accounts:
            account_id = account[0]
            invoice_number = account[1] if account[1] else "无"
            current_invoice_amount = account[2]
            paid_amount = account[3]
            balance = account[4]
            print(f'  账户ID: {account_id}, 发票号: {invoice_number}, 当前应付金额: ¥{current_invoice_amount}')
    else:
        for account in accounts:
            account_id = account[0]
            invoice_number = account[1] if account[1] else "无"
            current_invoice_amount = account[2]
            paid_amount = account[3]
            balance = account[4]
            
            print(f'  账户ID: {account_id}, 发票号: {invoice_number}, 当前应付金额: ¥{current_invoice_amount}')
            
            # 计算正确的应付金额（包含13%的税额）
            correct_invoice_amount = 550000 * 1.13  # 直接使用550000作为未税金额
            correct_balance = correct_invoice_amount - paid_amount
            
            print(f'  正确的应付金额: ¥{correct_invoice_amount:.2f}, 正确的未付余额: ¥{correct_balance:.2f}')
            
            # 更新应付账款记录
            cursor.execute("""
                UPDATE finance_supplier_account 
                SET invoice_amount = ?, balance = ? 
                WHERE id = ?
            """, (correct_invoice_amount, correct_balance, account_id))
            
            print(f'  已更新应付账款记录')
        
        # 提交事务
        conn.commit()
        print('\n更新完成！')
else:
    print('未找到测试供应商丁')

# 关闭连接
conn.close()
