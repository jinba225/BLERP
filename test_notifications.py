#!/usr/bin/env python
"""
测试通知功能
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.sales.models import SalesOrder, SalesReturn
from apps.core.models import Notification

User = get_user_model()

print("=== 测试通知功能 ===\n")

# 查找现有的退货单
sales_return = SalesReturn.objects.filter(is_deleted=False).first()

if not sales_return:
    print("❌ 没有找到退货单，请先创建一个退货单")
else:
    print(f"测试退货单: {sales_return.return_number}")
    print(f"状态: {sales_return.get_status_display()}")
    print(f"客户: {sales_return.sales_order.customer.name}\n")

    # 查找与此退货单相关的通知
    notifications = Notification.objects.filter(
        reference_type='sales_return',
        reference_id=str(sales_return.id)
    ).order_by('-created_at')

    print(f"找到 {notifications.count()} 条相关通知:\n")

    for notif in notifications:
        print(f"📬 通知 #{notif.id}")
        print(f"  接收人: {notif.recipient.username}")
        print(f"  标题: {notif.title}")
        print(f"  类型: {notif.get_notification_type_display()}")
        print(f"  分类: {notif.get_category_display()}")
        print(f"  是否已读: {'是' if notif.is_read else '否'}")
        print(f"  创建时间: {notif.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  消息内容:")
        for line in notif.message.split('\n'):
            print(f"    {line}")
        print()

# 显示所有用户的未读通知统计
print("\n=== 用户未读通知统计 ===\n")
users = User.objects.filter(is_active=True)
for user in users:
    unread_count = Notification.objects.filter(
        recipient=user,
        is_read=False
    ).count()
    if unread_count > 0:
        print(f"👤 {user.username}: {unread_count} 条未读通知")

print("\n✅ 通知功能测试完成！")
