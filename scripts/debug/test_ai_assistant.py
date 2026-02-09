"""
Django ERP AI Assistant - 命令行测试脚本

使用方法:
    python test_ai_assistant.py

这个脚本演示了如何直接使用AI Assistant，无需通过Telegram Bot。
"""

import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_erp.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.ai_assistant.services.nlp_service import NLPService
from apps.ai_assistant.services.conversation_flow_manager import ConversationFlowManager
from apps.ai_assistant.services.tool_monitor import ToolMonitor
from apps.ai_assistant.tools.registry import ToolRegistry

User = get_user_model()


class AIAssistantCLI:
    """AI Assistant命令行界面"""

    def __init__(self, username="test_user"):
        """初始化CLI"""
        # 获取或创建测试用户
        try:
            self.user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.user = User(username=username, is_active=True)
            self.user.save()
            print(f"✅ 创建测试用户: {username}")

        # 初始化服务
        from apps.ai_assistant.providers.deepseek_provider import DeepSeekProvider
        import os
        api_key = os.getenv('DEEPSEEK_API_KEY', 'test_key')
        ai_provider = DeepSeekProvider(api_key)
        self.nlp_service = NLPService(ai_provider)
        self.flow_manager = ConversationFlowManager(self.user)
        self.tool_monitor = ToolMonitor()

        # 显示欢迎信息
        self.show_welcome()

    def show_welcome(self):
        """显示欢迎信息"""
        print("\n" + "=" * 60)
        print("🤖 Django ERP AI Assistant - 命令行测试")
        print("=" * 60)
        print("\n可用命令:")
        print("  • 直接输入自然语言查询")
        print("  • 'stats' - 查看工具使用统计")
        print("  • 'tools' - 列出所有可用工具")
        print("  • 'clear' - 清空对话上下文")
        print("  • 'help' - 显示帮助信息")
        print("  • 'quit' 或 'exit' - 退出")
        print("\n" + "=" * 60)

    def show_stats(self):
        """显示工具使用统计"""
        print("\n📊 工具使用统计")
        print("-" * 60)

        stats = self.tool_monitor.get_all_tools_stats()

        if not stats:
            print("暂无使用记录")
            return

        print(f"\n总工具数: {len(stats)}")
        print(f"\n🔥 最常用的工具 (Top 10):")

        for i, stat in enumerate(stats[:10], 1):
            print(f"  {i}. {stat['tool_name']}")
            print(f"     执行次数: {stat['total_executions']}")
            print(f"     成功率: {stat['success_rate']}%")
            print(f"     平均时间: {stat['avg_execution_time']}秒")
            print()

        # 性能报告
        report = self.tool_monitor.get_performance_report()
        print(f"📈 性能报告:")
        print(f"  • 总执行次数: {report['total_executions']}")
        print(f"  • 平均成功率: {report['avg_success_rate']}%")
        print(f"  • 平均执行时间: {report['avg_execution_time']}秒")

    def show_tools(self):
        """显示所有可用工具"""
        print("\n🔧 可用工具列表")
        print("-" * 60)

        tools = ToolRegistry.get_available_tools(self.user)

        # 按分类组织
        categories = {}
        for tool in tools:
            category = tool.category
            if category not in categories:
                categories[category] = []
            categories[category].append(tool)

        for category, category_tools in sorted(categories.items()):
            print(f"\n📁 {category.upper()} ({len(category_tools)}个工具):")
            for tool in category_tools:
                risk_emoji = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🔴'
                }.get(tool.risk_level, '⚪')

                print(f"  {risk_emoji} {tool.name} - {tool.display_name}")
                print(f"     {tool.description[:80]}...")

    def process_message(self, message: str):
        """处理用户消息"""
        if not message.strip():
            return

        print(f"\n👤 用户: {message}")
        print("-" * 60)

        try:
            # NLP意图识别
            result = self.nlp_service.parse_user_input(message)

            print(f"\n🧠 NLP分析:")
            print(f"  • 意图: {result.intent.value if result.intent else 'unknown'}")
            print(f"  • 置信度: {result.confidence:.2f}")
            if result.entities:
                print(f"  • 实体: {result.entities}")

            # 检查是否需要多轮对话
            if self.flow_manager.is_ongoing_conversation():
                print(f"\n💬 继续对话...")
                response = self.flow_manager.continue_conversation(message)
            else:
                # 开始新对话
                response = self.flow_manager.start_new_conversation(message)

            # 显示响应
            print(f"\n🤖 Assistant:\n{response}")

            # 检查是否需要用户输入
            if self.flow_manager.is_ongoing_conversation():
                print(f"\n⏳ 等待用户输入...")

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()

    def run(self):
        """运行CLI"""
        print("\n准备就绪！开始对话...\n")

        while True:
            try:
                # 读取用户输入
                user_input = input("\n💬 您: ").strip()

                if not user_input:
                    continue

                # 处理特殊命令
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 再见！")
                    break

                elif user_input.lower() == 'stats':
                    self.show_stats()
                    continue

                elif user_input.lower() == 'tools':
                    self.show_tools()
                    continue

                elif user_input.lower() == 'clear':
                    self.flow_manager.clear_context()
                    print("\n✅ 对话上下文已清空")
                    continue

                elif user_input.lower() == 'help':
                    self.show_welcome()
                    continue

                # 处理普通消息
                self.process_message(user_input)

            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {str(e)}")


class BatchTestRunner:
    """批量测试运行器"""

    def __init__(self):
        """初始化测试运行器"""
        User = get_user_model()
        try:
            self.user = User.objects.first()
            if not self.user:
                self.user = User(username="test", is_active=True, is_superuser=True)
                self.user.save()
        except Exception as e:
            print(f"❌ 无法创建测试用户: {e}")
            return

        from apps.ai_assistant.providers.deepseek_provider import DeepSeekProvider
        # 使用测试API密钥（从环境变量或使用默认值）
        import os
        api_key = os.getenv('DEEPSEEK_API_KEY', 'test_key')
        ai_provider = DeepSeekProvider(api_key)
        self.nlp_service = NLPService(ai_provider)
        self.tool_monitor = ToolMonitor()

    def test_intent_recognition(self):
        """测试意图识别"""
        print("\n" + "=" * 60)
        print("🧪 测试1: 意图识别")
        print("=" * 60)

        test_cases = [
            "查询今天的销售订单",
            "创建一个新的销售订单",
            "审核订单SO-2025-001",
            "查询笔记本电脑的库存",
            "为客户ABC公司创建发货单",
            "批量审核订单001、002、003",
            "查询2025年1月的费用报销",
            "创建会计凭证",
        ]

        for test in test_cases:
            result = self.nlp_service.parse_user_input(test)
            print(f"\n测试: {test}")
            print(f"  → 意图: {result.intent.value if result.intent else 'unknown'}")
            print(f"  → 置信度: {result.confidence:.2f}")
            if result.entities:
                print(f"  → 实体: {result.entities}")

    def test_tool_registration(self):
        """测试工具注册"""
        print("\n" + "=" * 60)
        print("🧪 测试2: 工具注册")
        print("=" * 60)

        from apps.ai_assistant.tools.registry import ToolRegistry

        all_tools = ToolRegistry.get_all_tools(self.user)

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

    def test_cache_service(self):
        """测试缓存服务"""
        print("\n" + "=" * 60)
        print("🧪 测试3: 缓存服务")
        print("=" * 60)

        from apps.ai_assistant.services.cache_service import CacheService

        # 测试缓存操作
        test_params = {"date": "2025-02-05"}

        # 设置缓存
        CacheService.set(
            "query_sales_orders",
            test_params,
            {"test": "data", "count": 10},
            ttl=60
        )
        print("✅ 缓存设置成功")

        # 获取缓存
        cached_data = CacheService.get("query_sales_orders", test_params)
        print(f"✅ 缓存读取成功: {cached_data}")

        # 查看缓存统计
        stats = CacheService.get_cache_stats()
        print(f"\n📊 缓存统计:")
        print(f"  • 总缓存数: {stats['total_cached_results']}")
        print(f"  • 有缓存的工具: {stats['tools_with_cache']}")

        # 清理测试缓存
        CacheService.delete("query_sales_orders", test_params)
        print("\n✅ 测试缓存已清理")

    def test_intelligent_assistant(self):
        """测试智能助手"""
        print("\n" + "=" * 60)
        print("🧪 测试4: 智能助手")
        print("=" * 60)

        from apps.ai_assistant.services.intelligent_assistant import IntelligentAssistant

        assistant = IntelligentAssistant(self.user)

        # 测试上下文建议
        context = {
            "recent_intents": ["query_customer"],
            "recent_entities": {"customer_name": "ABC公司"}
        }

        suggestions = assistant.get_suggestions(context)
        print(f"\n💡 上下文建议 (查询客户后):")
        for suggestion in suggestions:
            print(f"  • {suggestion['suggestion']}")
            print(f"    理由: {suggestion['reason']}")

        # 测试自动补全
        print(f"\n🔍 自动补全测试:")
        results = assistant.autocomplete_parameter(
            "customer_name",
            "ABC",
            context
        )
        print(f"  客户名称 'ABC' 的补全结果:")
        for result in results[:3]:
            print(f"    • {result['display']}")

    def test_nlg_generator(self):
        """测试NLG生成器"""
        print("\n" + "=" * 60)
        print("🧪 测试5: NLG生成器")
        print("=" * 60)

        from apps.ai_assistant.services.nlg_service import NLGGenerator

        nlg = NLGGenerator(self.user)

        # 测试响应生成
        test_result = {
            "success": True,
            "message": "查询成功",
            "data": {
                "total_count": 5,
                "items": [
                    {"order_number": "SO-001", "status": "confirmed"},
                    {"order_number": "SO-002", "status": "pending"},
                ]
            }
        }

        response = nlg.generate_response(test_result, "query_sales_orders", verbose=True)
        print(f"\n生成的响应:\n{response}")

        # 测试状态翻译
        print(f"\n状态翻译:")
        print(f"  confirmed → {nlg.translate_status('confirmed')}")
        print(f"  pending → {nlg.translate_status('pending')}")
        print(f"  shipped → {nlg.translate_status('shipped')}")

        # 测试金额格式化
        print(f"\n金额格式化:")
        print(f"  12345.67 → {nlg.format_amount(12345.67)}")
        print(f"  1000000 → {nlg.format_amount(1000000)}")

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("🚀 Django ERP AI Assistant - 批量测试")
        print("=" * 60)

        try:
            self.test_intent_recognition()
            self.test_tool_registration()
            self.test_cache_service()
            self.test_intelligent_assistant()
            self.test_nlg_generator()

            print("\n" + "=" * 60)
            print("✅ 所有测试完成!")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Django ERP AI Assistant CLI')
    parser.add_argument(
        '--mode',
        choices=['cli', 'test'],
        default='cli',
        help='运行模式: cli=交互式命令行, test=批量测试'
    )
    parser.add_argument(
        '--user',
        default='test_user',
        help='测试用户名'
    )

    args = parser.parse_args()

    if args.mode == 'cli':
        # 交互式命令行模式
        cli = AIAssistantCLI(args.user)
        cli.run()
    else:
        # 批量测试模式
        tester = BatchTestRunner()
        tester.run_all_tests()


if __name__ == '__main__':
    main()
