"""
实时数据消费者
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database
from asgire_redis.consumers import AsyncChannelLayerConsumer
from channels.layers import get_channel_layer
from channels.db import async_db
from django.db.models import Count

from .services import RealtimeDashboardService


logger = logging.getLogger(__name__)


class DashboardConsumer(AsyncWebsocketConsumer):
    """大屏WebSocket消费者"""
    
    async def connect(self, message):
        """WebSocket连接"""
        await self.accept()
        await self.send(text_data=json.dumps({'type': 'connected', 'message': 'Connected'}))
    
    async def disconnect(self, close_code):
        """WebSocket断开连接"""
        await self.close(close_code)
        await self.send(text_data=json.dumps({'type': 'disconnected', 'message': 'Disconnected'}))
    
    async def receive(self, text_data):
        """接收WebSocket消息"""
        try:
            data = json.loads(text_data)
            
            message_type = data.get('type', '')
            
            if message_type == 'subscribe':
                await self.subscribe(data)
            elif message_type == 'unsubscribe':
                await self.unsubscribe(data)
            elif message_type == 'refresh':
                await self.refresh(data)
            elif message_type == 'ping':
                await self.ping(data)
            else:
                await self.send(text_data=json.dumps({'type': 'error', 'message': 'Unknown message type'}))
                
        except json.JSONDecodeError:
            await self.send(text_data({'type': 'error', 'message': 'Invalid JSON format'}))
    
    async def subscribe(self, data):
        """订阅大屏数据"""
        from asgire_redis.consumers import get_channel_layer
        channel_layer = get_channel_layer('dashboard')
        
        # 验证是否为订阅操作
        if data.get('action') != 'subscribe':
            await self.send(text_data({'type': 'error', 'message': 'Invalid action'}))
            return
        
        dashboard_id = data.get('dashboard_id')
        
        # 创建Redis channel
        async def get_or_create_channel():
            channel_name = f"dashboard:{dashboard_id}"
            await channel_layer.new_channel(
                channel_name,
                {
                    'type': 'realtime',
                    'django_asgi_redis': True,
                'consuming_groups': 'dashboard',
                    'channel_layers': [],
                'consuming_channels': ['realtime_updates']
                }
            )
            
            await self.channel_layer.send({
                'type': 'subscribed',
                'dashboard_id': dashboard_id,
                'message': f'Subscribed to {channel_name}'
            })
            
            # 监听该通道
            await channel_layer.group_send(f'dashboard:{dashboard_id}')
            await self.channel_layer.group_add(f'dashboard:{dashboard_id}', self.channel_name)
            
        except Exception as e:
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": f"Subscription failed: {str(e)}"}
                )
            )
    
    async def unsubscribe(self, data):
        """取消订阅大屏数据"""
        from asgire_redis.consumers import get_channel_layer
        channel_layer = get_channel_layer('dashboard')
        
        if data.get('action') != 'unsubscribe':
            await self.send(text_data({'type': 'error', 'message': 'Invalid action'}))
            return
        
        dashboard_id = data.get('dashboard_id')
        
        try:
            channel_name = f"dashboard:{dashboard_id}"
            
            await channel_layer.send({
                'type': 'unsubscribed',
                'dashboard_id': dashboard_id,
                'message': f'Unsubscribed from {channel_name}'
            })
            
            await channel_layer.group_discard(f'dashboard:{dashboard_id}', self.channel_name)
            
            await self.send(text_data=json.dumps({'type': 'success', 'message': f'Unsubscribed from {channel_name}'}))
            
        except Exception as e:
            await self.send(text_data({'type': 'error', 'message': f'Unsubscription failed: {str(e)}'}'))
    
    async def refresh(self, data):
        """刷新大屏数据"""
        from .services import RealtimeDashboardService
        
        dashboard_id = data.get('dashboard_id')
        dashboard_data = RealtimeDashboardService.get_dashboard_data(dashboard_id)
        
        await self.send(text_data({'type': 'refresh', 'dashboard_data': dashboard_data}))
    
    async def ping(self, data):
        """心跳检测"""
        await self.send(text_data=json.dumps({'type': 'pong', 'message': 'pong'}))


class MetricCardConsumer(AsyncWebsocketConsumer):
    """指标卡WebSocket消费者"""
    
    async def connect(self, message):
        """WebSocket连接"""
        await self.accept()
        await self.send(text_data=json.dumps({'type': 'connected', 'message': 'Connected'}))
    
    async def disconnect(self, close_code):
        """WebSocket断开连接"""
        await self.close(close_code)
        await self.send(text_data=json.dumps({'type': 'disconnected', 'message': 'Disconnected'}))
    
    async def receive(self, text_data):
        """接收WebSocket消息"""
        try:
            data = json.loads(text_data)
            
            widget_id = data.get('widget_id')
            
            if widget_id:
                # 获取指标数据
                from .services import RealtimeDashboardService
                service = RealtimeDashboardService()
                metric_data = service.get_widget_data(widget_id)
                
                await self.send(text_data=json.dumps({'type': 'metric_update', 'widget_data': metric_data})))
            else:
                await self.send(text_data=json.dumps({'type': 'error', 'message': 'Unknown widget'})))
                
        except json.JSONDecodeError:
            await self.send(text_data({'type': 'error', 'message': 'Invalid JSON format'}))


class DataExportConsumer(AsyncWebsocketConsumer):
    """数据导出WebSocket消费者"""
    
    async def connect(self, message):
        """WebSocket连接"""
        await self.accept()
        await self.send(text_data=json.dumps({'type': 'connected', 'message': 'Connected'}))
    
    async def disconnect(self, close_code):
        """WebSocket断开连接"""
        await self.close(close_code)
        await self.send(text_data=json.dumps({'type': 'disconnected', 'message': 'Disconnected'}))
    
    async def receive(self, text_data):
        """接收WebSocket消息"""
        try:
            data = json.loads(text_data)
            
            request_type = data.get('type', '')
            
            if request_type == 'export':
                await self.export_data(data)
            else:
                await self.send(text_data=json.dumps({'type': 'error', 'message': 'Unknown request type'})))
                
        except json.JSONDecodeError:
            await self.send(text_data({'type': 'error', 'message': 'Invalid JSON format'}))
    
    async def export_data(self, data):
        """导出数据"""
        from .services import DataExportViewSet
        
        export_type = data.get('export_type', '')
        
        if export_type == 'sales':
            export_data = await self.export_sales_data(data)
        elif export_type == 'inventory':
            export_data = await self.export_inventory_data(data)
        elif export_type == 'platform':
            export_data = await self.export_platform_data(data)
        else:
            await self.send(text_data=json.dumps({'type': 'error', 'message': 'Unsupported export type'})))
    
    async def export_sales_data(self, data):
        """导出销售数据"""
        export_data = await self._export_data_helper(
            queryset=SalesSummary.objects.all(),
            file_type='csv',
            fields=['日期', '平台', '订单数', '销售额', '平均订单金额']
        )
        
        await self.send(text_data=json.dumps({'type': 'export_success', 'message': 'Sales data exported', 'file_url': export_data.get('file_url', '')})))
    
    async def export_inventory_data(self, data):
        """导出库存数据"""
        export_data = await self._export_data_helper(
            queryset=InventoryAnalysis.objects.all(),
            file_type='csv',
            fields=['商品名称', '当前库存', '库存状态', '周转天数', '库存价值']
        )
        
        await self.send(text_data=json.dumps({'type': 'export_success', 'message': 'Inventory data exported', 'file_url': export_data.get('file_url', '')})))
    
    async def export_platform_data(self, data):
        """导出平台对比数据"""
        export_data = await self._export_data_helper(
            queryset=PlatformComparison.objects.all(),
            file_type='csv',
            fields=['平台', '订单数', '销售额', '增长率', '转化率', '平均订单金额']
        )
        
        await self.send(text_data=json.dumps({'type': 'export_success', 'message': 'Platform comparison data exported', 'file_url': export_data.get('file_url', '')})))
    
    async def _export_data_helper(self, queryset, file_type: str, fields: List[str]) -> Dict:
        """导出数据帮助方法"""
        from django.http import HttpResponse
        import csv
        import io
        import tempfile
        import os
        from datetime import datetime
        
        # 导出数据
        if file_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f"attachment; filename=\"export_{file_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv\""
            
            writer = csv.writer(response)
            
            # 写入表头
            writer.writerow(fields)
            
            # 写入数据行
            for item in queryset.values_list(*fields):
                writer.writerow([str(item.get(f, '') for f in fields])
            
            return response
        else:
            return HttpResponse({'error': 'Unsupported file type'}, status=400)
    
    async def send(self, text_data):
        """发送WebSocket消息"""
        await self.send(text_data)