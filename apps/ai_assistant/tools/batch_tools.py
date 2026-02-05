"""
批量操作工具

提供批量执行业务操作的工具，提高工作效率
"""

from typing import Dict, Any, List
from django.db import transaction
from .base_tool import BaseTool, ToolResult


class BatchQueryTool(BaseTool):
    """批量查询工具基类"""

    name = "batch_query"
    display_name = "批量查询"
    description = "批量查询多个对象的信息"
    category = "batch"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "description": "查询列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string", "description": "工具名称"},
                            "params": {"type": "object", "description": "工具参数"}
                        },
                        "required": ["tool_name", "params"]
                    }
                }
            },
            "required": ["queries"]
        }

    def execute(self, queries: List[Dict[str, Any]], **kwargs) -> ToolResult:
        """执行批量查询"""
        try:
            from .registry import ToolRegistry

            results = []
            errors = []

            for query in queries:
                tool_name = query["tool_name"]
                params = query["params"]

                # 获取工具
                tool = ToolRegistry.get_tool(tool_name, self.user)
                if not tool:
                    errors.append({
                        "query": query,
                        "error": f"工具 {tool_name} 不存在"
                    })
                    continue

                # 执行查询
                try:
                    result = tool.run(**params)
                    results.append({
                        "tool_name": tool_name,
                        "params": params,
                        "result": result.to_dict()
                    })
                except Exception as e:
                    errors.append({
                        "query": query,
                        "error": str(e)
                    })

            return ToolResult(
                success=True,
                data={
                    "results": results,
                    "success_count": len(results),
                    "error_count": len(errors),
                    "errors": errors
                },
                message=f"批量查询完成，成功 {len(results)} 个，失败 {len(errors)} 个"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"批量查询失败: {str(e)}"
            )


class BatchApproveTool(BaseTool):
    """批量审核工具"""

    name = "batch_approve"
    display_name = "批量审核"
    description = "批量审核多个业务对象"
    category = "batch"
    risk_level = "high"
    require_permission = "sales.batch_approve"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_type": {
                    "type": "string",
                    "description": "实体类型（sales_order/purchase_order/expense等）",
                    "enum": ["sales_order", "purchase_order", "expense"]
                },
                "entity_ids": {
                    "type": "array",
                    "description": "实体ID列表",
                    "items": {"type": "integer"}
                },
                "action": {
                    "type": "string",
                    "description": "操作类型",
                    "enum": ["approve", "reject"]
                },
                "notes": {
                    "type": "string",
                    "description": "审核备注（将应用于所有对象）"
                }
            },
            "required": ["entity_type", "entity_ids", "action"]
        }

    def execute(self, entity_type: str, entity_ids: List[int],
                action: str, notes: str = "", **kwargs) -> ToolResult:
        """执行批量审核"""
        try:
            from ..services.approval_service import ApprovalService, ApprovalRequest

            results = []
            errors = []

            for entity_id in entity_ids:
                try:
                    # 创建审批请求
                    request = ApprovalRequest(
                        request_type=f"batch_{action}_{entity_type}",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        entity_number=str(entity_id),
                        requester=self.user,
                        description=f"批量{action}"
                    )

                    # 执行审核
                    if action == "approve":
                        success, message, data = ApprovalService.approve_request(
                            request, self.user, notes
                        )
                    else:  # reject
                        success, message, data = ApprovalService.reject_request(
                            request, self.user, notes
                        )

                    results.append({
                        "entity_id": entity_id,
                        "success": success,
                        "message": message,
                        "data": data
                    })

                except Exception as e:
                    errors.append({
                        "entity_id": entity_id,
                        "error": str(e)
                    })

            return ToolResult(
                success=True,
                data={
                    "results": results,
                    "success_count": len([r for r in results if r["success"]]),
                    "error_count": len(errors),
                    "errors": errors
                },
                message=f"批量审核完成，成功 {len([r for r in results if r['success']])} 个，失败 {len(errors)} 个"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"批量审核失败: {str(e)}"
            )


class BatchExportTool(BaseTool):
    """批量导出工具"""

    name = "batch_export"
    display_name = "批量导出"
    description = "批量导出查询结果为Excel或CSV格式"
    category = "batch"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query_results": {
                    "type": "array",
                    "description": "查询结果列表（来自批量查询工具的data.results）"
                },
                "format": {
                    "type": "string",
                    "description": "导出格式",
                    "enum": ["excel", "csv", "json"]
                },
                "filename": {
                    "type": "string",
                    "description": "文件名（不含扩展名）"
                }
            },
            "required": ["query_results", "format"]
        }

    def execute(self, query_results: List[Dict[str, Any]], format: str = "excel",
                filename: str = "export", **kwargs) -> ToolResult:
        """执行批量导出"""
        try:
            import pandas as pd
            from django.conf import settings
            import os
            from datetime import datetime

            # 展平数据
            flat_data = []
            for result in query_results:
                result_data = result.get("result", {})
                tool_name = result.get("tool_name", "")
                params = result.get("params", {})

                for item in result_data.get("data", []):
                    flat_data.append({
                        "工具": tool_name,
                        "参数": str(params),
                        **item
                    })

            if not flat_data:
                return ToolResult(
                    success=False,
                    error="没有可导出的数据"
                )

            # 创建DataFrame
            df = pd.DataFrame(flat_data)

            # 确定导出目录
            export_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
            os.makedirs(export_dir, exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_full = f"{filename}_{timestamp}"

            # 导出文件
            file_path = ""
            if format == "excel":
                file_path = os.path.join(export_dir, f"{filename_full}.xlsx")
                df.to_excel(file_path, index=False, engine='openpyxl')
            elif format == "csv":
                file_path = os.path.join(export_dir, f"{filename_full}.csv")
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            else:  # json
                file_path = os.path.join(export_dir, f"{filename_full}.json")
                df.to_json(file_path, orient='records', force_ascii=False, indent=2)

            # 返回下载链接
            download_url = f"/media/exports/{os.path.basename(file_path)}"

            return ToolResult(
                success=True,
                data={
                    "file_path": file_path,
                    "download_url": download_url,
                    "rows_count": len(flat_data),
                    "file_size": os.path.getsize(file_path)
                },
                message=f"导出成功，文件包含 {len(flat_data)} 行数据"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"批量导出失败: {str(e)}"
            )


class BatchCreateTool(BaseTool):
    """批量创建工具基类"""

    name = "batch_create"
    display_name = "批量创建"
    description = "批量创建多个业务对象"
    category = "batch"
    risk_level = "high"
    require_permission = "sales.batch_create"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": "创建项目列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string", "description": "工具名称"},
                            "params": {"type": "object", "description": "工具参数"}
                        },
                        "required": ["tool_name", "params"]
                    }
                }
            },
            "required": ["items"]
        }

    def execute(self, items: List[Dict[str, Any]], **kwargs) -> ToolResult:
        """执行批量创建"""
        try:
            from .registry import ToolRegistry

            results = []
            errors = []

            for item in items:
                tool_name = item["tool_name"]
                params = item["params"]

                # 获取工具
                tool = ToolRegistry.get_tool(tool_name, self.user)
                if not tool:
                    errors.append({
                        "item": item,
                        "error": f"工具 {tool_name} 不存在"
                    })
                    continue

                # 执行创建
                try:
                    result = tool.run(**params)
                    results.append({
                        "tool_name": tool_name,
                        "params": params,
                        "result": result.to_dict()
                    })
                except Exception as e:
                    errors.append({
                        "item": item,
                        "error": str(e)
                    })

            return ToolResult(
                success=True,
                data={
                    "results": results,
                    "success_count": len([r for r in results if r["result"]["success"]]),
                    "error_count": len(errors),
                    "errors": errors
                },
                message=f"批量创建完成，成功 {len([r for r in results if r['result']['success']])} 个，失败 {len(errors)} 个"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"批量创建失败: {str(e)}"
            )
