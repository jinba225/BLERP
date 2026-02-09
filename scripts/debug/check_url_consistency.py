#!/usr/bin/env python
"""
Django URL 一致性检查脚本

功能：
1. 扫描所有 Django 应用的 urls.py 文件
2. 提取所有定义的 URL name（包括 namespace）
3. 扫描所有模板文件中的 {% url %} 标签
4. 对比两者，找出不匹配的 URL name
5. 生成详细报告

使用方法：
    python scripts/check_url_consistency.py
"""

import ast
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "better_laser_erp.settings")

import django

django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver


class URLExtractor:
    """URL 提取器"""

    def __init__(self):
        self.defined_urls = {}  # {(namespace, name): pattern}
        self.all_url_names = set()  # 所有定义的 URL name

    def extract_from_urlconf(self):
        """从 Django URL 配置中提取所有定义的 URL"""
        print("正在提取 URL 定义...")

        try:
            resolver = get_resolver()
            self._traverse_url_resolver(resolver, namespace=None)
            print(f"✓ 找到 {len(self.defined_urls)} 个定义的 URL")
        except Exception as e:
            print(f"✗ 提取 URL 定义时出错: {e}")

    def _traverse_url_resolver(self, resolver, namespace=None):
        """递归遍历 URL 解析器"""
        for url_pattern in resolver.url_patterns:
            if isinstance(url_pattern, URLResolver):
                # 处理包含的 URL 配置（include）
                new_namespace = url_pattern.namespace
                if new_namespace:
                    if namespace:
                        new_namespace = f"{namespace}:{new_namespace}"
                    self._traverse_url_resolver(url_pattern, new_namespace)
                else:
                    self._traverse_url_resolver(url_pattern, namespace)
            elif isinstance(url_pattern, URLPattern):
                # 处理 URL 模式
                pattern = url_pattern.pattern
                name = url_pattern.name

                if name:
                    # 构建完整的 URL name（包含 namespace）
                    full_name = f"{namespace}:{name}" if namespace else name
                    self.defined_urls[full_name] = str(pattern)
                    self.all_url_names.add(name)

                    # 也记录不带 namespace 的 name
                    if namespace:
                        self.all_url_names.add(f"{namespace}:{name}")

    def extract_from_urls_files(self):
        """直接从 urls.py 文件中提取 URL 定义（备用方法）"""
        print("\n正在从 urls.py 文件中提取 URL 定义...")

        apps_dir = project_root / "apps"
        if not apps_dir.exists():
            return

        for app_dir in apps_dir.iterdir():
            if app_dir.is_dir():
                urls_file = app_dir / "urls.py"
                if urls_file.exists():
                    self._parse_urls_file(urls_file, app_dir.name)

        # 检查主 URL 配置
        main_urls = project_root / "better_laser_erp" / "urls.py"
        if main_urls.exists():
            self._parse_urls_file(main_urls, "main")

    def _parse_urls_file(self, urls_file, app_name):
        """解析单个 urls.py 文件"""
        try:
            with open(urls_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取 app_name
            app_name_match = re.search(r"app_name\s*=\s*['\"]([^'\"]+)['\"]", content)
            namespace = app_name_match.group(1) if app_name_match else None

            # 提取所有 path() 调用中的 name 参数
            path_pattern = r"path\s*\(\s*[^)]*?name\s*=\s*['\"]([^'\"]+)['\"]"
            names = re.findall(path_pattern, content)

            for name in names:
                if namespace:
                    full_name = f"{namespace}:{name}"
                    self.defined_urls[full_name] = f"从 {app_name}/urls.py 提取"
                else:
                    self.defined_urls[name] = f"从 {app_name}/urls.py 提取"
                self.all_url_names.add(name)

        except Exception as e:
            print(f"✗ 解析 {urls_file} 时出错: {e}")


class TemplateURLExtractor:
    """模板 URL 提取器"""

    def __init__(self):
        self.template_urls = defaultdict(list)  # {url_name: [(file, line_number), ...]}
        self.url_pattern = re.compile(r"{%\s*url\s+(['\"]?[^'\"]+['\"]?)")

    def extract_from_templates(self):
        """从所有模板文件中提取 URL 引用"""
        print("\n正在扫描模板文件...")

        templates_dir = project_root / "templates"
        if not templates_dir.exists():
            print("✗ 未找到 templates 目录")
            return

        html_files = list(templates_dir.rglob("*.html"))
        print(f"找到 {len(html_files)} 个模板文件")

        for html_file in html_files:
            self._parse_template_file(html_file)

        print(f"✓ 从模板中提取到 {len(self.template_urls)} 个不同的 URL 引用")

    def _parse_template_file(self, template_file):
        """解析单个模板文件"""
        try:
            with open(template_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    matches = self.url_pattern.findall(line)
                    for match in matches:
                        # 清理 URL name（移除引号和空格）
                        url_name = match.strip("'\"")
                        # 提取实际的 URL name（可能是带引号的字符串）
                        if " " in url_name:
                            # 处理 {% url 'namespace:name' %} 格式
                            parts = url_name.split()
                            if parts:
                                url_name = parts[0].strip("'\"")

                        if url_name and not url_name.startswith("{"):
                            self.template_urls[url_name].append((str(template_file), line_num))
        except Exception as e:
            print(f"✗ 解析 {template_file} 时出错: {e}")


class URLConsistencyChecker:
    """URL 一致性检查器"""

    def __init__(self):
        self.url_extractor = URLExtractor()
        self.template_extractor = TemplateURLExtractor()
        self.results = {
            "undefined_in_urls": [],  # 模板中引用但未定义的 URL
            "unused_in_templates": [],  # 定义了但模板中未使用的 URL
            "total_defined": 0,
            "total_used": 0,
        }

    def check(self):
        """执行一致性检查"""
        print("=" * 70)
        print("Django URL 一致性检查工具")
        print("=" * 70)

        # 提取 URL 定义
        self.url_extractor.extract_from_urlconf()
        if not self.url_extractor.defined_urls:
            print("\n尝试备用方法...")
            self.url_extractor.extract_from_urls_files()

        # 提取模板中的 URL 使用
        self.template_extractor.extract_from_templates()

        # 执行检查
        self._find_undefined_urls()
        self._find_unused_urls()

        # 生成报告
        self._generate_report()

    def _find_undefined_urls(self):
        """找出模板中引用但未定义的 URL"""
        print("\n正在检查未定义的 URL...")

        for url_name, references in self.template_extractor.template_urls.items():
            # 检查是否在定义的 URL 中
            found = False

            # 首先检查完全匹配
            if url_name in self.url_extractor.defined_urls:
                found = True
            else:
                # 检查是否可能是带 namespace 的格式
                if ":" in url_name:
                    namespace, name = url_name.split(":", 1)
                    # 尝试不同的组合
                    possible_names = [
                        url_name,  # namespace:name
                        name,  # 仅 name
                    ]

                    for possible_name in possible_names:
                        if possible_name in self.url_extractor.defined_urls:
                            found = True
                            break
                else:
                    # 检查是否可能是某个 namespace 下的 URL
                    for defined_url in self.url_extractor.defined_urls:
                        if defined_url.endswith(f":{url_name}") or defined_url == url_name:
                            found = True
                            break

            if not found:
                self.results["undefined_in_urls"].append(
                    {"name": url_name, "references": references}
                )

    def _find_unused_urls(self):
        """找出定义了但模板中未使用的 URL"""
        print("\n正在检查未使用的 URL...")

        # 收集所有模板中使用的 URL name（不含 namespace）
        used_names = set()
        for url_name in self.template_extractor.template_urls.keys():
            if ":" in url_name:
                _, name = url_name.split(":", 1)
                used_names.add(name)
            used_names.add(url_name)

        # 检查每个定义的 URL
        for defined_url in self.url_extractor.defined_urls:
            # 检查是否被使用
            is_used = False

            if ":" in defined_url:
                namespace, name = defined_url.split(":", 1)
                if (
                    defined_url in used_names
                    or name in used_names
                    or any(
                        defined_url in ref for ref in self.template_extractor.template_urls.keys()
                    )
                ):
                    is_used = True
            else:
                if defined_url in used_names:
                    is_used = True

            if not is_used:
                # 排除一些特殊的 URL（如 admin、API 等）
                if not self._is_excluded_url(defined_url):
                    self.results["unused_in_templates"].append(
                        {
                            "name": defined_url,
                            "pattern": self.url_extractor.defined_urls[defined_url],
                        }
                    )

        self.results["total_defined"] = len(self.url_extractor.defined_urls)
        self.results["total_used"] = len(self.template_extractor.template_urls)

    def _is_excluded_url(self, url_name):
        """检查是否是需要排除的 URL"""
        excluded_patterns = [
            "admin:",  # Admin URLs
            "api_",  # API URLs（可能只在 JavaScript 中使用）
            "__debug__",  # Debug toolbar
        ]

        return any(url_name.startswith(pattern) for pattern in excluded_patterns)

    def _generate_report(self):
        """生成检查报告"""
        print("\n" + "=" * 70)
        print("检查报告")
        print("=" * 70)

        # 统计信息
        print(f"\n📊 统计信息:")
        print(f"  • 定义的 URL 总数: {self.results['total_defined']}")
        print(f"  • 模板中使用的 URL: {self.results['total_used']}")
        print(f"  • 未定义的 URL: {len(self.results['undefined_in_urls'])}")
        print(f"  • 未使用的 URL: {len(self.results['unused_in_templates'])}")

        # 未定义的 URL（严重问题）
        if self.results["undefined_in_urls"]:
            print(f"\n{'=' * 70}")
            print(f"❌ 模板中引用但未定义的 URL ({len(self.results['undefined_in_urls'])} 个)")
            print(f"{'=' * 70}")

            for item in sorted(self.results["undefined_in_urls"], key=lambda x: x["name"]):
                print(f"\n🔴 URL: '{item['name']}'")
                print(f"   引用位置:")
                for file_path, line_num in item["references"]:
                    rel_path = Path(file_path).relative_to(project_root)
                    print(f"   • {rel_path}:{line_num}")

                # 尝试建议正确的 URL name
                suggestions = self._suggest_correct_name(item["name"])
                if suggestions:
                    print(f"   💡 建议的正确名称:")
                    for suggestion in suggestions:
                        print(f"   • {suggestion}")
        else:
            print(f"\n✅ 所有模板中引用的 URL 都已正确定义")

        # 未使用的 URL（警告）
        if self.results["unused_in_templates"]:
            print(f"\n{'=' * 70}")
            print(f"⚠️  定义了但模板中未使用的 URL ({len(self.results['unused_in_templates'])} 个)")
            print(f"{'=' * 70}")
            print("（这些 URL 可能在 Python 代码、JavaScript 或重定向中使用）\n")

            # 显示所有未使用的 URL
            for item in sorted(self.results["unused_in_templates"], key=lambda x: x["name"]):
                print(f"• {item['name']}")
        else:
            print(f"\n✅ 所有定义的 URL 都在模板中被使用")

        # 总结
        print(f"\n{'=' * 70}")
        if self.results["undefined_in_urls"]:
            print("❌ 检查完成：发现需要修复的问题")
        else:
            print("✅ 检查完成：所有 URL 一致")
        print(f"{'=' * 70}")

        # 生成 JSON 报告
        self._generate_json_report()

    def _generate_json_report(self):
        """生成 JSON 格式的详细报告"""
        report = {
            "summary": {
                "total_defined": self.results["total_defined"],
                "total_used": self.results["total_used"],
                "undefined_count": len(self.results["undefined_in_urls"]),
                "unused_count": len(self.results["unused_in_templates"]),
            },
            "undefined_urls": [],
            "unused_urls": [],
        }

        # 未定义的 URL
        for item in self.results["undefined_in_urls"]:
            references = [
                {"file": str(Path(ref[0]).relative_to(project_root)), "line": ref[1]}
                for ref in item["references"]
            ]
            report["undefined_urls"].append({"name": item["name"], "references": references})

        # 未使用的 URL
        for item in self.results["unused_in_templates"]:
            report["unused_urls"].append({"name": item["name"], "pattern": item["pattern"]})

        # 保存报告
        report_file = project_root / "url_consistency_report.json"
        import json

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 详细报告已保存到: {report_file.relative_to(project_root)}")

    def _suggest_correct_name(self, wrong_name):
        """建议正确的 URL name"""
        suggestions = []

        # 检查是否缺少 namespace
        if ":" not in wrong_name:
            for defined_url in self.url_extractor.defined_urls:
                if ":" in defined_url:
                    namespace, name = defined_url.split(":", 1)
                    if name == wrong_name:
                        suggestions.append(f"可能需要添加 namespace: '{defined_url}'")

        # 检查相似的名称
        for defined_url in self.url_extractor.defined_urls:
            if self._are_similar(wrong_name, defined_url):
                if defined_url not in suggestions:
                    suggestions.append(f"相似的 URL: '{defined_url}'")

        return suggestions

    def _are_similar(self, name1, name2):
        """检查两个 URL name 是否相似"""
        # 简单的相似度检查
        if name1 == name2:
            return True

        # 检查去掉 namespace 后是否相同
        if ":" in name1:
            _, n1 = name1.split(":", 1)
        else:
            n1 = name1

        if ":" in name2:
            _, n2 = name2.split(":", 1)
        else:
            n2 = name2

        if n1 == n2:
            return True

        # 检查编辑距离
        if len(n1) > 0 and len(n2) > 0:
            distance = sum(1 for a, b in zip(n1, n2) if a != b) + abs(len(n1) - len(n2))
            if distance <= 2:  # 编辑距离 <= 2 认为相似
                return True

        return False


def main():
    """主函数"""
    checker = URLConsistencyChecker()
    try:
        checker.check()
    except Exception as e:
        print(f"\n✗ 检查过程中出错: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
