import logging
from typing import List, Dict
from django.utils import timezone
from django.db import transaction
from .api import WooCommerceAPI
from .mapper import WooCommerceMapper
from ecomm_sync.models import EcommProduct, ProductChangeLog, SyncLog


logger = logging.getLogger(__name__)


class WooCommerceBatchSync:
    """WooCommerce批量同步器"""

    def __init__(self, api: WooCommerceAPI = None):
        """
        初始化批量同步器

        Args:
            api: WooCommerce API客户端（可选）
        """
        self.api = api or WooCommerceAPI.get_active()
        if not self.api:
            raise ValueError('未配置WooCommerce API')

    def sync_single_product(self, ecomm_product: EcommProduct, update_type: str = 'full') -> dict:
        """
        同步单个产品到WooCommerce

        Args:
            ecomm_product: 电商产品
            update_type: 更新类型

        Returns:
            同步结果
        """
        try:
            if update_type == 'full':
                woo_data = WooCommerceMapper.map_to_woo(ecomm_product)
                
                if ecomm_product.woo_product_id:
                    result = self.api.update_product(
                        ecomm_product.woo_product_id,
                        woo_data
                    )
                    logger.info(f'更新产品: {ecomm_product.product.name}')
                else:
                    result = self.api.create_product(woo_data)
                    ecomm_product.woo_product_id = result['id']
                    ecomm_product.sync_status = 'synced'
                    logger.info(f'创建产品: {ecomm_product.product.name}')
                
            elif update_type == 'price':
                woo_data = WooCommerceMapper.extract_price_update(ecomm_product)
                result = self.api.update_product(
                    ecomm_product.woo_product_id,
                    woo_data
                )
                
            elif update_type == 'stock':
                woo_data = WooCommerceMapper.extract_stock_update(ecomm_product)
                result = self.api.update_product(
                    ecomm_product.woo_product_id,
                    woo_data
                )
                
            elif update_type == 'status':
                woo_data = WooCommerceMapper.extract_status_update(ecomm_product)
                result = self.api.update_product(
                    ecomm_product.woo_product_id,
                    woo_data
                )
            else:
                raise ValueError(f'不支持的更新类型: {update_type}')

            ecomm_product.last_synced_at = timezone.now()
            ecomm_product.save()

            return {
                'success': True,
                'woo_product_id': result['id'],
                'ecomm_product_id': ecomm_product.id,
            }

        except Exception as e:
            logger.error(f'同步产品失败: {ecomm_product.id}, 错误: {e}')
            return {
                'success': False,
                'error': str(e),
                'ecomm_product_id': ecomm_product.id,
            }

    def sync_batch_products(
        self, 
        ecomm_products: List[EcommProduct],
        update_type: str = 'full'
    ) -> Dict:
        """
        批量同步产品

        Args:
            ecomm_products: 产品列表
            update_type: 更新类型

        Returns:
            批量同步结果
        """
        results = {
            'total': len(ecomm_products),
            'succeeded': 0,
            'failed': 0,
            'errors': []
        }

        for ecomm_product in ecomm_products:
            result = self.sync_single_product(ecomm_product, update_type)
            
            if result['success']:
                results['succeeded'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(result['error'])

        return results

    def sync_batch_using_woo_batch(self, updates: List[dict]) -> Dict:
        """
        使用WooCommerce批量API同步

        Args:
            updates: 批量更新数据

        Returns:
            同步结果
        """
        try:
            result = self.api.batch_update_products(updates)
            
            logger.info(f'批量更新完成: {len(updates)} 个产品')
            
            return {
                'success': True,
                'updated': len(result.get('update', [])),
                'data': result
            }
            
        except Exception as e:
            logger.error(f'批量同步失败: {e}')
            return {
                'success': False,
                'error': str(e)
            }

    def sync_change_logs(self, change_logs: List[ProductChangeLog]) -> Dict:
        """
        同步变更日志到WooCommerce

        Args:
            change_logs: 变更日志列表

        Returns:
            同步结果
        """
        results = {
            'total': len(change_logs),
            'succeeded': 0,
            'failed': 0,
            'errors': []
        }

        grouped_changes = self._group_changes_by_product(change_logs)

        for ecomm_product, changes in grouped_changes.items():
            update_type = self._determine_update_type(changes)
            
            result = self.sync_single_product(ecomm_product, update_type)
            
            if result['success']:
                results['succeeded'] += 1
                
                with transaction.atomic():
                    for change in changes:
                        change.synced_to_woo = True
                        change.woo_synced_at = timezone.now()
                        change.save()
            else:
                results['failed'] += 1
                results['errors'].append({
                    'ecomm_product_id': ecomm_product.id,
                    'error': result['error']
                })

        return results

    def _group_changes_by_product(self, change_logs: List[ProductChangeLog]) -> Dict[EcommProduct, List]:
        """按产品分组变更"""
        grouped = {}
        for change_log in change_logs:
            if change_log.ecomm_product not in grouped:
                grouped[change_log.ecomm_product] = []
            grouped[change_log.ecomm_product].append(change_log)
        return grouped

    def _determine_update_type(self, changes: List[ProductChangeLog]) -> str:
        """确定更新类型"""
        change_types = {change.change_type for change in changes}
        
        if len(change_types) == 1:
            change_type = list(change_types)[0]
            type_map = {
                'price': 'price',
                'stock': 'stock',
                'status': 'status',
            }
            return type_map.get(change_type, 'full')
        
        return 'full'

    def sync_pending_products(self, limit: int = None) -> Dict:
        """
        同步待同步的产品

        Args:
            limit: 限制数量

        Returns:
            同步结果
        """
        pending_products = EcommProduct.objects.filter(
            sync_status='pending',
            product__isnull=False
        ).select_related('product', 'platform')

        if limit:
            pending_products = pending_products[:limit]

        return self.sync_batch_products(list(pending_products), update_type='full')

    def sync_changes_batch(self, limit: int = 100) -> Dict:
        """
        同步变更批次

        Args:
            limit: 批次大小

        Returns:
            同步结果
        """
        unsynced_changes = ProductChangeLog.objects.filter(
            synced_to_woo=False
        ).select_related('ecomm_product__product')[:limit]

        return self.sync_change_logs(list(unsynced_changes))

    @staticmethod
    def create_sync_log(platform, log_type: str) -> SyncLog:
        """
        创建同步日志

        Args:
            platform: 电商平台
            log_type: 日志类型

        Returns:
            同步日志实例
        """
        return SyncLog.objects.create(
            log_type=log_type,
            platform=platform,
            status='running'
        )

    @staticmethod
    def update_sync_log(
        sync_log: SyncLog,
        status: str,
        records_processed: int,
        records_succeeded: int,
        records_failed: int,
        error_message: str = '',
        execution_time: float = 0
    ):
        """
        更新同步日志

        Args:
            sync_log: 同步日志实例
            status: 状态
            records_processed: 处理记录数
            records_succeeded: 成功记录数
            records_failed: 失败记录数
            error_message: 错误信息
            execution_time: 执行时间
        """
        sync_log.status = status
        sync_log.records_processed = records_processed
        sync_log.records_succeeded = records_succeeded
        sync_log.records_failed = records_failed
        sync_log.error_message = error_message
        sync_log.execution_time = execution_time
        sync_log.save()
