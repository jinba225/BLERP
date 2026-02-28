"""
数据冲突解决器
支持冲突检测和自动解决（5种策略）

保障数据一致性：
- 自动检测冲突
- 智能解决策略
- 冲突日志记录
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from core.config import CONFLICT_STRATEGIES, ResolutionStrategy
from django.utils import timezone

logger = logging.getLogger(__name__)


class Conflict:
    """数据冲突对象"""

    def __init__(
        self,
        field: str,
        local_value: Any,
        remote_value: Any,
        strategy: ResolutionStrategy,
        local_version: Optional[int] = None,
        remote_version: Optional[int] = None,
    ):
        """
        初始化冲突对象

        Args:
            field: 字段名
            local_value: 本地值
            remote_value: 远程值
            strategy: 解决策略
            local_version: 本地版本号
            remote_version: 远程版本号
        """
        self.field = field
        self.local_value = local_value
        self.remote_value = remote_value
        self.strategy = strategy
        self.local_version = local_version
        self.remote_version = remote_version

    def __repr__(self):
        return (
            f"Conflict(field={self.field}, "
            f"local={self.local_value}, remote={self.remote_value}, "
            f"strategy={self.strategy.value})"
        )


class ConflictResolver:
    """
    数据冲突解决器

    功能：
    - 冲突检测
    - 自动解决（5种策略）
    - 冲突日志
    - 人工审核接口

    解决策略：
    - LAST_WRITE_WINS: 最后写入胜出
    - LOCAL_PRIORITY: 本地优先
    - REMOTE_PRIORITY: 远程优先
    - MERGE: 合并
    - MANUAL: 人工处理
    """

    def __init__(self):
        """初始化冲突解决器"""
        self.strategies = CONFLICT_STRATEGIES
        self.conflict_history = []  # 冲突历史记录

        logger.info("初始化数据冲突解决器")

    async def detect_conflicts(self, local_data: Dict, remote_data: Dict) -> List[Conflict]:
        """
        检测数据冲突

        Args:
            local_data: 本地数据
            remote_data: 远程数据

        Returns:
            list: 冲突列表

        Example:
            >>> resolver = ConflictResolver()
            >>> conflicts = await resolver.detect_conflicts(local_product, remote_product)
            >>> for conflict in conflicts:
            ...     print(f"字段 {conflict.field} 存在冲突")
        """
        conflicts = []

        # 遍历所有配置的字段
        for field, strategy in self.strategies.items():
            # 获取本地和远程值
            local_value = local_data.get(field)
            remote_value = remote_data.get(field)

            # 检查是否冲突
            if self._is_conflicting(field, local_value, remote_value, local_data, remote_data):
                conflict = Conflict(
                    field=field,
                    local_value=local_value,
                    remote_value=remote_value,
                    strategy=strategy,
                    local_version=local_data.get("version"),
                    remote_version=remote_data.get("version"),
                )
                conflicts.append(conflict)

                logger.warning(
                    f"检测到冲突: field={field}, " f"local={local_value}, remote={remote_value}"
                )

        return conflicts

    async def resolve_conflict(
        self, conflict: Conflict, auto_resolve: bool = True
    ) -> Dict[str, Any]:
        """
        解决单个冲突

        Args:
            conflict: 冲突对象
            auto_resolve: 是否自动解决（False时返回冲突信息供人工处理）

        Returns:
            dict: 解决结果

        Example:
            >>> resolver = ConflictResolver()
            >>> result = await resolver.resolve_conflict(conflict)
            >>> print(result['value'])
        """
        strategy = conflict.strategy

        if not auto_resolve and strategy == ResolutionStrategy.MANUAL:
            # 人工处理
            return {
                "field": conflict.field,
                "status": "pending_manual_review",
                "local_value": conflict.local_value,
                "remote_value": conflict.remote_value,
                "reason": "需要人工处理",
            }

        # 自动解决
        if strategy == ResolutionStrategy.LAST_WRITE_WINS:
            result = self._resolve_last_write_wins(conflict)

        elif strategy == ResolutionStrategy.LOCAL_PRIORITY:
            result = self._resolve_local_priority(conflict)

        elif strategy == ResolutionStrategy.REMOTE_PRIORITY:
            result = self._resolve_remote_priority(conflict)

        elif strategy == ResolutionStrategy.MERGE:
            result = self._resolve_merge(conflict)

        else:
            # 默认使用远程优先
            result = self._resolve_remote_priority(conflict)

        # 记录冲突历史
        self._record_conflict(conflict, result)

        return result

    async def resolve_conflicts(
        self, conflicts: List[Conflict], auto_resolve: bool = True
    ) -> Dict[str, Any]:
        """
        批量解决冲突

        Args:
            conflicts: 冲突列表
            auto_resolve: 是否自动解决

        Returns:
            dict: 解决结果

        Example:
            >>> resolver = ConflictResolver()
            >>> conflicts = await resolver.detect_conflicts(local_data, remote_data)
            >>> result = await resolver.resolve_conflicts(conflicts)
            >>> print(result['resolved_data'])
        """
        resolved_data = {}
        pending_manual = []

        for conflict in conflicts:
            result = await self.resolve_conflict(conflict, auto_resolve)

            if result.get("status") == "pending_manual_review":
                pending_manual.append(result)
            else:
                resolved_data[conflict.field] = result["value"]

        return {
            "resolved_data": resolved_data,
            "pending_manual": pending_manual,
            "total_conflicts": len(conflicts),
            "resolved_count": len(conflicts) - len(pending_manual),
            "manual_count": len(pending_manual),
        }

    def _is_conflicting(
        self,
        field: str,
        local_value: Any,
        remote_value: Any,
        local_data: Dict,
        remote_data: Dict,
    ) -> bool:
        """
        判断是否存在冲突

        Args:
            field: 字段名
            local_value: 本地值
            remote_value: 远程值
            local_data: 本地数据
            remote_data: 远程数据

        Returns:
            bool: 是否冲突
        """
        # 值相同，不冲突
        if local_value == remote_value:
            return False

        # 其中一个为空，不冲突（以有值的为准）
        if local_value is None or remote_value is None:
            return False

        # 检查版本号
        local_version = local_data.get("version")
        remote_version = remote_data.get("version")

        if local_version is not None and remote_version is not None:
            # 版本号相同但值不同，存在冲突
            if local_version == remote_version:
                return True
            # 版本号不同，不冲突（以新版本为准）
            else:
                return False

        # 无版本号信息，值不同即冲突
        return True

    def _resolve_last_write_wins(self, conflict: Conflict) -> Dict:
        """
        最后写入胜出策略

        Args:
            conflict: 冲突对象

        Returns:
            dict: 解决结果
        """
        # 比较版本号
        if conflict.local_version is not None and conflict.remote_version is not None:
            if conflict.local_version > conflict.remote_version:
                value = conflict.local_value
                source = "local"
            else:
                value = conflict.remote_value
                source = "remote"
        else:
            # 无版本号，使用远程值
            value = conflict.remote_value
            source = "remote"

        return {
            "field": conflict.field,
            "value": value,
            "source": source,
            "reason": "Last Write Wins",
        }

    def _resolve_local_priority(self, conflict: Conflict) -> Dict:
        """
        本地优先策略

        Args:
            conflict: 冲突对象

        Returns:
            dict: 解决结果
        """
        return {
            "field": conflict.field,
            "value": conflict.local_value,
            "source": "local",
            "reason": "Local Priority",
        }

    def _resolve_remote_priority(self, conflict: Conflict) -> Dict:
        """
        远程优先策略

        Args:
            conflict: 冲突对象

        Returns:
            dict: 解决结果
        """
        return {
            "field": conflict.field,
            "value": conflict.remote_value,
            "source": "remote",
            "reason": "Remote Priority",
        }

    def _resolve_merge(self, conflict: Conflict) -> Dict:
        """
        合并策略

        Args:
            conflict: 冲突对象

        Returns:
            dict: 解决结果
        """
        local = conflict.local_value
        remote = conflict.remote_value

        # 根据字段类型合并
        if conflict.field in ["title", "listing_title"]:
            # 标题：取较长的
            value = local if len(local) > len(remote) else remote

        elif conflict.field in ["description"]:
            # 描述：合并
            value = f"{local}\n\n{remote}"

        elif conflict.field in ["images"]:
            # 图片：合并去重
            local_images = set(local) if isinstance(local, list) else {local}
            remote_images = set(remote) if isinstance(remote, list) else {remote}
            value = list(local_images | remote_images)

        elif conflict.field in ["sku", "category"]:
            # SKU和分类：远程优先
            value = remote

        else:
            # 默认：远程优先
            value = remote

        return {
            "field": conflict.field,
            "value": value,
            "source": "merged",
            "reason": "Merged",
        }

    def _record_conflict(self, conflict: Conflict, result: Dict):
        """
        记录冲突历史

        Args:
            conflict: 冲突对象
            result: 解决结果
        """
        record = {
            "timestamp": timezone.now().isoformat(),
            "field": conflict.field,
            "local_value": conflict.local_value,
            "remote_value": conflict.remote_value,
            "strategy": conflict.strategy.value,
            "resolved_value": result.get("value"),
            "resolved_source": result.get("source"),
        }

        self.conflict_history.append(record)

        # 保留最近1000条记录
        if len(self.conflict_history) > 1000:
            self.conflict_history = self.conflict_history[-1000:]

        logger.debug(f"记录冲突历史: {record}")

    def get_conflict_history(self, field: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        获取冲突历史

        Args:
            field: 字段名（None表示所有字段）
            limit: 返回数量

        Returns:
            list: 冲突历史列表

        Example:
            >>> resolver = ConflictResolver()
            >>> history = resolver.get_conflict_history(field='price', limit=10)
        """
        history = self.conflict_history

        # 过滤字段
        if field:
            history = [h for h in history if h["field"] == field]

        # 返回最近的记录
        return history[-limit:][::-1]


# 全局单例
_conflict_resolver_instance = None


def get_conflict_resolver() -> ConflictResolver:
    """
    获取冲突解决器实例（单例模式）

    Returns:
        ConflictResolver: 冲突解决器实例

    Example:
        >>> from ecomm_sync.services.conflict_resolver import get_conflict_resolver
        >>> resolver = get_conflict_resolver()
        >>> conflicts = await resolver.detect_conflicts(local_data, remote_data)
    """
    global _conflict_resolver_instance
    if _conflict_resolver_instance is None:
        _conflict_resolver_instance = ConflictResolver()
    return _conflict_resolver_instance
