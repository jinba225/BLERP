"""
修复付款单号序列表缺失的问题

问题描述：
- finance_payment 表中已存在 BILL 前缀的付款单号
- 但 core_document_number_sequence 表中缺少 BILL 前缀的序列记录
- 导致生成新付款单号时从序号1开始，冲突后重试5次仍失败

解决方案：
- 查询每个日期的最大序号
- 在序列表中插入对应的记录
"""
import os
import sys
import django

# 添加项目路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from core.models import DocumentNumberSequence
from finance.models import Payment
from django.db.models import Max


def fix_payment_sequence():
    """修复付款单号序列表"""

    print("🔍 开始检查付款单号序列...")
    print("=" * 60)

    # 1. 查询所有BILL前缀的付款单号
    bill_payments = Payment.objects.filter(
        payment_number__startswith='BILL',
        is_deleted=False
    ).values('payment_number', 'created_at')

    if not bill_payments:
        print("❌ 未找到BILL前缀的付款单号")
        return

    print(f"✅ 找到 {bill_payments.count()} 条BILL前缀的付款记录")

    # 2. 按日期分组，找出每个日期的最大序号
    from collections import defaultdict
    date_max_sequence = defaultdict(int)

    for payment in bill_payments:
        payment_number = payment['payment_number']
        # BILL + YYMMDD(6位) + 序号
        # 例如: BILL260116001
        if len(payment_number) >= 12:
            date_str = payment_number[4:10]  # 提取日期部分 YYMMDD
            sequence_str = payment_number[10:]  # 提取序号部分
            try:
                sequence = int(sequence_str)
                if sequence > date_max_sequence[date_str]:
                    date_max_sequence[date_str] = sequence
            except ValueError:
                continue

    # 3. 显示当前状态
    print("\n📋 当前数据库中的付款单号分布：")
    print("-" * 60)
    for date_str in sorted(date_max_sequence.keys()):
        max_seq = date_max_sequence[date_str]
        print(f"  日期 {date_str}: 最大序号 = {max_seq:03d}")

    # 4. 检查序列表中的记录
    print("\n🔍 检查序列表记录...")
    existing_sequences = DocumentNumberSequence.objects.filter(
        prefix='BILL'
    )

    if existing_sequences.exists():
        print("⚠️  序列表中已存在BILL前缀的记录：")
        for seq in existing_sequences:
            print(f"    {seq.prefix} - {seq.date_str} - current_number={seq.current_number}")
    else:
        print("❌ 序列表中不存在BILL前缀的记录")

    # 5. 插入缺失的序列记录
    print("\n🔧 开始插入缺失的序列记录...")
    print("-" * 60)

    created_count = 0
    updated_count = 0

    for date_str, max_sequence in sorted(date_max_sequence.items()):
        # 检查是否已存在
        sequence_obj = DocumentNumberSequence.objects.filter(
            prefix='BILL',
            date_str=date_str
        ).first()

        if sequence_obj:
            # 如果已存在，更新序号
            if sequence_obj.current_number < max_sequence:
                old_value = sequence_obj.current_number
                sequence_obj.current_number = max_sequence
                sequence_obj.save()
                print(f"✅ 更新 {date_str}: {old_value} → {max_sequence}")
                updated_count += 1
            else:
                print(f"⏭️  跳过 {date_str}: 当前值 {sequence_obj.current_number} 已正确")
        else:
            # 不存在则创建
            DocumentNumberSequence.objects.create(
                prefix='BILL',
                date_str=date_str,
                current_number=max_sequence
            )
            print(f"✨ 创建 {date_str}: current_number={max_sequence}")
            created_count += 1

    print("\n" + "=" * 60)
    print(f"✅ 修复完成！")
    print(f"   - 创建记录: {created_count} 条")
    print(f"   - 更新记录: {updated_count} 条")
    print("=" * 60)

    # 6. 验证结果
    print("\n🔍 验证修复结果...")
    all_sequences = DocumentNumberSequence.objects.filter(prefix='BILL')
    print(f"   序列表中BILL前缀记录总数: {all_sequences.count()}")
    for seq in all_sequences.order_by('-date_str'):
        print(f"   - {seq.date_str}: current_number={seq.current_number:03d}")

    print("\n✨ 现在可以正常生成付款单号了！")


if __name__ == '__main__':
    try:
        fix_payment_sequence()
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
