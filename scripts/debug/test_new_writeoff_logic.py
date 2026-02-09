#!/usr/bin/env python3
"""
测试新的核销逻辑

场景：
- 应付账单：¥2,000
- 预付款余额：¥1,000
- 场景1：现金支付¥0，预付款¥1,000 → 总核销¥1,000，应付剩余¥1,000
- 场景2：现金支付¥1,000，预付款¥1,000 → 总核销¥2,000，应付剩余¥0
"""

from decimal import Decimal

print("=" * 70)
print("🔍 新核销逻辑测试")
print("=" * 70)

print("\n📊 测试数据:")
print("  应付账单余额: ¥2,000")
print("  预付款余额: ¥1,000")

print("\n" + "-" * 70)
print("场景1: 仅使用预付款")
print("-" * 70)

account_balance = Decimal("2000")
prepay_balance = Decimal("1000")
cash_amount = Decimal("0")

print(f"  现金支付金额: ¥{cash_amount}")
print(f"  预付款全部使用: ¥{prepay_balance}")
print(f"  总核销: ¥{prepay_balance} + ¥{cash_amount} = ¥{prepay_balance + cash_amount}")

total_offset = prepay_balance + cash_amount
remaining = account_balance - total_offset

print(f"  应付剩余: ¥{account_balance} - ¥{total_offset} = ¥{remaining}")
print(f'  状态: {"部分核销" if remaining > 0 else "已核销"}')

if total_offset <= account_balance:
    print(f"  ✅ 验证通过: ¥{total_offset} <= ¥{account_balance}")
else:
    print(f"  ❌ 验证失败: ¥{total_offset} > ¥{account_balance}")

print("\n" + "-" * 70)
print("场景2: 预付款 + 现金各支付一半")
print("-" * 70)

account_balance = Decimal("2000")
prepay_balance = Decimal("1000")
cash_amount = Decimal("1000")

print(f"  现金支付金额: ¥{cash_amount}")
print(f"  预付款全部使用: ¥{prepay_balance}")
print(f"  总核销: ¥{prepay_balance} + ¥{cash_amount} = ¥{prepay_balance + cash_amount}")

total_offset = prepay_balance + cash_amount
remaining = account_balance - total_offset

print(f"  应付剩余: ¥{account_balance} - ¥{total_offset} = ¥{remaining}")
print(f'  状态: {"部分核销" if remaining > 0 else "已核销"}')

if total_offset <= account_balance:
    print(f"  ✅ 验证通过: ¥{total_offset} <= ¥{account_balance}")
else:
    print(f"  ❌ 验证失败: ¥{total_offset} > ¥{account_balance}")

print("\n" + "-" * 70)
print("场景3: 仅使用现金（不选预付款）")
print("-" * 70)

account_balance = Decimal("2000")
prepay_balance = Decimal("0")  # 不使用预付款
cash_amount = Decimal("1500")

print(f"  现金支付金额: ¥{cash_amount}")
print(f"  预付款: 未选择")
print(f"  总核销: ¥{prepay_balance} + ¥{cash_amount} = ¥{prepay_balance + cash_amount}")

total_offset = prepay_balance + cash_amount
remaining = account_balance - total_offset

print(f"  应付剩余: ¥{account_balance} - ¥{total_offset} = ¥{remaining}")
print(f'  状态: {"部分核销" if remaining > 0 else "已核销"}')

if total_offset <= account_balance:
    print(f"  ✅ 验证通过: ¥{total_offset} <= ¥{account_balance}")
else:
    print(f"  ❌ 验证失败: ¥{total_offset} > ¥{account_balance}")

print("\n" + "-" * 70)
print("场景4: 尝试超过应付余额（应该失败）")
print("-" * 70)

account_balance = Decimal("2000")
prepay_balance = Decimal("1000")
cash_amount = Decimal("1500")

print(f"  现金支付金额: ¥{cash_amount}")
print(f"  预付款全部使用: ¥{prepay_balance}")
print(f"  总核销: ¥{prepay_balance} + ¥{cash_amount} = ¥{prepay_balance + cash_amount}")

total_offset = prepay_balance + cash_amount

print(f"  应付余额: ¥{account_balance}")
if total_offset <= account_balance:
    print(f"  ✅ 验证通过: ¥{total_offset} <= ¥{account_balance}")
else:
    print(f"  ❌ 验证失败: ¥{total_offset} > ¥{account_balance}")
    print(f"  错误提示: 总核销金额（¥{total_offset}）不能超过应付余额（¥{account_balance}）")

print("\n" + "=" * 70)
print("✅ 新核销逻辑测试完成")
print("=" * 70)
print("\n💡 关键改进:")
print("  1. 现金支付金额可以填0")
print("  2. 预付款全部使用（不限制）")
print("  3. 总核销 = 预付款 + 现金")
print("  4. 允许部分核销，不要求一次核销完")
print("  5. 验证总核销不超过应付余额")
print("=" * 70)
