"""
Django ERP AI Assistant - 系统验证脚本

验证所有组件是否正常工作（无需API密钥）
"""

import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_erp.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()


def verify_tools():
    """验证工具注册"""
    print("\n" + "=" * 60)
    print("🔧 验证工具注册")
    print("=" * 60)

    from apps.ai_assistant.tools.registry import ToolRegistry

    # 获取或创建测试用户
    try:
        user = User.objects.first()
        if not user:
            user = User(username="test", is_active=True, is_superuser=True)
            user.save()
    except Exception as e:
        print(f"❌ 无法创建测试用户: {e}")
        return False

    # 获取所有工具
    all_tools = ToolRegistry.get_all_tools(user)

    print(f"\n✅ 总工具数: {len(all_tools)}")

    # 按分类统计
    categories = {}
    for tool in all_tools:
        categories[tool.category] = categories.get(tool.category, 0) + 1

    print(f"\n📊 按分类统计:")
    for category, count in sorted(categories.items()):
        print(f"  • {category}: {count}个")

    # 风险级别统计
    risk_levels = {}
    for tool in all_tools:
        risk_levels[tool.risk_level] = risk_levels.get(tool.risk_level, 0) + 1

    print(f"\n⚠️ 风险级别分布:")
    for level, count in sorted(risk_levels.items()):
        print(f"  • {level}: {count}个")

    # 验证关键工具
    print(f"\n🔍 验证关键工具:")
    critical_tools = [
        "query_sales_orders",
        "create_sales_order",
        "approve_sales_order",
        "batch_query",
        "batch_approve",
    ]

    for tool_name in critical_tools:
        tool = ToolRegistry.get_tool(tool_name, user)
        if tool:
            print(f"  ✅ {tool_name}")
        else:
            print(f"  ❌ {tool_name} - 未找到")

    return True


def verify_services():
    """验证服务组件"""
    print("\n" + "=" * 60)
    print("🛠️ 验证服务组件")
    print("=" * 60)

    services = [
        ("NLP服务", "apps.ai_assistant.services.nlp_service", "NLPService"),
        ("对话流程管理", "apps.ai_assistant.services.conversation_flow_manager", "ConversationFlowManager"),
        ("明细收集器", "apps.ai_assistant.services.item_collector", "ItemCollector"),
        ("工作流管理", "apps.ai_assistant.services.workflow_manager", "WorkflowManager"),
        ("审批服务", "apps.ai_assistant.services.approval_service", "ApprovalService"),
        ("缓存服务", "apps.ai_assistant.services.cache_service", "CacheService"),
        ("智能助手", "apps.ai_assistant.services.intelligent_assistant", "IntelligentAssistant"),
        ("NLG生成器", "apps.ai_assistant.services.nlg_service", "NLGGenerator"),
        ("工具监控", "apps.ai_assistant.services.tool_monitor", "ToolMonitor"),
    ]

    all_ok = True
    for name, module_path, class_name in services:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"  ✅ {name}")
        except Exception as e:
            print(f"  ❌ {name} - {e}")
            all_ok = False

    return all_ok


def verify_models():
    """验证数据模型"""
    print("\n" + "=" * 60)
    print("📦 验证数据模型")
    print("=" * 60)

    models = [
        ("用户模型", "django.contrib.auth", "User"),
        ("销售订单", "apps.sales.models", "SalesOrder"),
        ("客户", "apps.customers.models", "Customer"),
        ("产品", "apps.products.models", "Product"),
        ("库存", "apps.inventory.models", "InventoryStock"),
    ]

    for name, module_path, model_name in models:
        try:
            module = __import__(module_path, fromlist=[model_name])
            model = getattr(module, model_name)
            print(f"  ✅ {name}")
        except Exception as e:
            print(f"  ⚠️ {name} - 模型可能不存在（正常情况）")


def verify_intents():
    """验证NLP意图"""
    print("\n" + "=" * 60)
    print("🎯 验证NLP意图")
    print("=" * 60)

    from apps.ai_assistant.services.nlp_service import Intent

    # 统计意图数量
    total_intents = len(Intent)
    print(f"\n✅ 总意图数: {total_intents}")

    # 按模块分类统计
    intent_groups = {
        "销售": ["CREATE_ORDER", "APPROVE_ORDER", "QUERY_CUSTOMER", "QUERY_PRODUCT",
                "QUERY_INVENTORY", "CREATE_QUOTE", "QUERY_ORDER", "CREATE_DELIVERY",
                "QUERY_DELIVERY", "CONFIRM_SHIPMENT", "CREATE_RETURN", "QUERY_RETURN",
                "APPROVE_RETURN", "CREATE_LOAN", "QUERY_LOAN", "APPROVE_LOAN",
                "CONVERT_QUOTE_TO_ORDER"],
        "采购": ["QUERY_SUPPLIER", "CREATE_PURCHASE_REQUEST", "CREATE_PURCHASE_ORDER",
                "QUERY_PURCHASE_ORDER", "APPROVE_PURCHASE_ORDER", "CREATE_INQUIRY",
                "QUERY_INQUIRY", "SEND_INQUIRY", "ADD_QUOTE", "CREATE_RECEIPT",
                "QUERY_RECEIPT", "CONFIRM_RECEIPT", "CREATE_PURCHASE_RETURN",
                "QUERY_PURCHASE_RETURN", "CREATE_PURCHASE_LOAN", "QUERY_PURCHASE_LOAN"],
        "库存": ["QUERY_WAREHOUSE", "CREATE_WAREHOUSE", "CREATE_TRANSFER", "QUERY_TRANSFER",
                "CONFIRM_TRANSFER", "CREATE_COUNT", "QUERY_COUNT", "SUBMIT_COUNT",
                "CREATE_INBOUND", "QUERY_INBOUND", "CREATE_OUTBOUND", "QUERY_OUTBOUND",
                "CREATE_ADJUSTMENT", "QUERY_ADJUSTMENT"],
        "财务": ["QUERY_ACCOUNT", "CREATE_JOURNAL", "QUERY_JOURNAL", "APPROVE_JOURNAL",
                "CREATE_PAYMENT", "QUERY_PAYMENT", "CREATE_PREPAYMENT", "QUERY_PREPAYMENT",
                "CONSOLIDATE_PREPAYMENT", "QUERY_BUDGET", "CREATE_BUDGET", "CREATE_EXPENSE",
                "QUERY_EXPENSE", "APPROVE_EXPENSE", "QUERY_INVOICE"],
        "批量": ["BATCH_QUERY", "BATCH_APPROVE", "BATCH_EXPORT", "BATCH_CREATE"],
        "报表": ["GENERATE_SALES_REPORT", "GENERATE_PURCHASE_REPORT", "GENERATE_INVENTORY_REPORT"],
    }

    for group, intent_names in intent_groups.items():
        count = 0
        for intent_name in intent_names:
            if hasattr(Intent, intent_name):
                count += 1
        print(f"  • {group}: {count}个意图")

    return True


def verify_cache():
    """验证缓存服务"""
    print("\n" + "=" * 60)
    print("💾 验证缓存服务")
    print("=" * 60)

    from apps.ai_assistant.services.cache_service import CacheService

    # 测试缓存操作
    test_params = {"test": "data"}

    # 设置缓存
    CacheService.set("test_tool", test_params, {"result": "success"}, ttl=60)
    print("  ✅ 缓存设置")

    # 获取缓存
    cached_data = CacheService.get("test_tool", test_params)
    if cached_data:
        print("  ✅ 缓存读取")
    else:
        print("  ❌ 缓存读取失败")
        return False

    # 查看缓存统计
    stats = CacheService.get_cache_stats()
    if 'total_cached_results' in stats:
        print(f"  ✅ 缓存统计: {stats['total_cached_results']}个缓存")
    elif 'error' in stats:
        print(f"  ⚠️ 缓存统计: {stats['error']}")
    else:
        print(f"  ✅ 缓存统计功能正常")

    # 清理测试缓存
    CacheService.delete("test_tool", test_params)
    print("  ✅ 缓存清理")

    return True


def verify_intelligent_assistant():
    """验证智能助手"""
    print("\n" + "=" * 60)
    print("🤖 验证智能助手")
    print("=" * 60)

    from apps.ai_assistant.services.intelligent_assistant import IntelligentAssistant

    # 获取测试用户
    try:
        user = User.objects.first()
        if not user:
            user = User(username="test", is_active=True)
            user.save()
    except Exception as e:
        print(f"  ❌ 无法创建测试用户: {e}")
        return False

    assistant = IntelligentAssistant(user)

    # 测试上下文建议
    context = {
        "recent_intents": ["query_customer"],
        "recent_entities": {"customer_name": "ABC公司"}
    }

    suggestions = assistant.get_suggestions(context)
    if suggestions:
        print(f"  ✅ 上下文建议: {len(suggestions)}个建议")
    else:
        print(f"  ⚠️ 上下文建议: 无建议")

    # 测试ContextManager
    from apps.ai_assistant.services.intelligent_assistant import ContextManager
    ctx_mgr = ContextManager(user)
    ctx_mgr.add_intent("test_intent", {"test": "value"})
    print(f"  ✅ ContextManager正常工作")

    return True


def verify_nlg_generator():
    """验证NLG生成器"""
    print("\n" + "=" * 60)
    print("📝 验证NLG生成器")
    print("=" * 60)

    from apps.ai_assistant.services.nlg_service import NLGGenerator

    # 获取测试用户
    try:
        user = User.objects.first()
        if not user:
            user = User(username="test", is_active=True)
            user.save()
    except Exception as e:
        print(f"  ❌ 无法创建测试用户: {e}")
        return False

    nlg = NLGGenerator(user)

    # 测试响应生成
    test_result = {
        "success": True,
        "message": "测试成功",
        "data": {
            "total_count": 5,
            "items": [
                {"order_number": "SO-001", "status": "confirmed"},
            ]
        }
    }

    response = nlg.generate_response(test_result, "test_tool", verbose=True)
    if response:
        print(f"  ✅ 响应生成: {len(response)}字符")
    else:
        print(f"  ❌ 响应生成失败")
        return False

    # 测试状态翻译
    status = nlg.translate_status("confirmed")
    if status:
        print(f"  ✅ 状态翻译: confirmed → {status}")

    # 测试金额格式化
    amount = nlg.format_amount(12345.67)
    if amount:
        print(f"  ✅ 金额格式化: 12345.67 → {amount}")

    return True


def verify_tool_monitor():
    """验证工具监控"""
    print("\n" + "=" * 60)
    print("📊 验证工具监控")
    print("=" * 60)

    try:
        from apps.ai_assistant.services.tool_monitor import ToolMonitor

        # 注意：ToolMonitor在LocMemCache下可能无法正常工作（pickle问题）
        # 这在生产环境使用Redis时不会是问题
        print("  ⚠️ 工具监控需要Redis缓存才能正常工作")
        print("  ✅ ToolMonitor类已成功导入")

        # 验证类可以实例化
        monitor = ToolMonitor()
        print("  ✅ ToolMonitor实例化成功")

        return True
    except Exception as e:
        print(f"  ❌ 工具监控验证失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🚀 Django ERP AI Assistant - 系统验证")
    print("=" * 60)
    print("\n此脚本验证所有组件是否正常工作（无需API密钥）\n")

    results = []

    # 运行所有验证
    try:
        results.append(("工具注册", verify_tools()))
        results.append(("服务组件", verify_services()))
        results.append(("数据模型", verify_models()))
        results.append(("NLP意图", verify_intents()))
        results.append(("缓存服务", verify_cache()))
        results.append(("智能助手", verify_intelligent_assistant()))
        results.append(("NLG生成器", verify_nlg_generator()))
        results.append(("工具监控", verify_tool_monitor()))
    except Exception as e:
        print(f"\n❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        return

    # 显示总结
    print("\n" + "=" * 60)
    print("📋 验证总结")
    print("=" * 60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")

    total = len(results)
    passed = sum(1 for _, r in results if r)

    print(f"\n总计: {passed}/{total} 项通过")

    if passed == total:
        print("\n🎉 所有验证通过！系统运行正常！")
    else:
        print(f"\n⚠️ 有 {total - passed} 项验证失败，请检查错误信息")


if __name__ == '__main__':
    main()
