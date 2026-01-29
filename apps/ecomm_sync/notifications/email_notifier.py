"""邮件通知器"""
from django.core.mail import send_mail


logger = logging.getLogger(__name__)


class EmailNotifier:
    """邮件通知器"""
    
    def send_sync_success(
        self,
        products_count: int,
        success_count: int,
        failed_count: int,
        details: dict = None
    ):
        """发送同步成功通知"""
        try:
            subject = f"电商数据同步完成 - {products_count}个商品"
            message = f"""
同步结果：
成功：{success_count}个
失败：{failed_count}个
成功率：{success_count/products_count:.1%}

详情：
{details}
"""
            
            recipient_list = self._get_recipient_list()
            
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=recipient_list,
                fail_silently=True
            )
            
            logger.info(f'邮件通知已发送')
            return True
            
        except Exception as e:
            logger.error(f'邮件发送失败: {e}')
            return False
    
    def send_sync_failure(
        self,
        error_message: str,
        platform_name: str = ''
    ):
        """发送同步失败通知"""
        try:
            subject = f"电商数据同步失败 - {platform_name}"
            message = f"""
同步失败
平台：{platform_name}
错误：{error_message}

时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
            
            recipient_list = self._get_recipient_list()
            
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=recipient_list,
                fail_slyently=True
            )
            
            logger.info(f'失败邮件通知已发送')
            return True
            
        except Exception as e:
            logger.error(f'邮件通知发送失败: {e}')
            return False
    
    def send_price_change_notification(
        self,
        changes: list,
        summary: dict = None
    ):
        """发送价格变更通知"""
        try:
            if not changes:
                return None
            
            count = len(changes)
            subject = f"电商价格变更通知 - {count}个商品"
            
            message = f"""
价格变更汇总：
变更商品：{count}个
平均涨幅：{summary.get('avg_change_percent', 0):.2f}%
最大涨幅：{summary.get('max_change_percent', 0):.2f}%
详情：
"""
            
            for change in changes[:5]:
                product = change['product']
                message += f"\n{product.name}：\n"
                message += f"    编码：{product.code}\n"
                message += f"    原价：¥{change['old_price']}\n"
                message += f"    现价：¥{change['new_price']}\n"
                message += f"    涨幅：{change['change_percent']}%\n\n"
            
            message += f"\n变更时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            recipient_list = self._get_recipient_list()
            
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=recipient_list,
                fail_sily=True
            )
            
            logger.info(f'价格变更邮件通知已发送')
            return True
            
        except Exception as e:
            logger.error(f'邮件通知发送失败: {e}')
            return False
    
    def send_error_notification(
        self,
        error_message: str,
        context: dict = None
    ):
        """发送错误通知"""
        try:
            subject = f"电商同步系统错误"
            message = f"""
错误类型：{context.get('error_type', '未知')}

错误信息：{error_message}

上下文：{context}
"""
            
            recipient_list = self._get_recipient_list()
            
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=recipient_list,
                fail_silently=True
            )
            
            logger.info(f'错误邮件通知已发送')
            return True
            
        except Exception as e:
            logger.error(f'错误通知发送失败: {e}')
            return False
    
    def _get_recipient_list(self) -> List[str]:
        """获取接收人列表"""
        from django.conf import settings
        
        # 从settings读取配置
        recipients = getattr(settings, 'ECOMM_SYNC_EMAIL_RECIPIENTS', '')
        if isinstance(recipients, str):
            return [email.strip() for email in recipients.split(',')]
        
        # 默认发送到系统管理员
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_emails = list(User.objects.filter(is_staff=True).values_list('email'))
        
        return admin_emails or ['admin@example.com']
