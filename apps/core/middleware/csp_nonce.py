"""
CSP Nonce 中间件

为每个请求生成唯一的 nonce 值，并将其添加到请求上下文中，
用于内容安全策略 (CSP) 中的内联脚本和样式。
"""
import secrets
from django.utils.deprecation import MiddlewareMixin


class CSPNonceMiddleware(MiddlewareMixin):
    """
    为每个请求生成 CSP nonce 值
    """
    
    def process_request(self, request):
        """
        为每个请求生成唯一的 nonce 值
        """
        # 生成 32 字节的随机 nonce 值
        nonce = secrets.token_hex(32)
        # 将 nonce 存储在请求对象中
        request.csp_nonce = nonce
        return None
    
    def process_response(self, request, response):
        """
        将 nonce 添加到 CSP 头部
        """
        if hasattr(request, 'csp_nonce'):
            # 获取现有的 CSP 头部
            csp_header = response.get('Content-Security-Policy', '')
            
            # 构建新的 CSP 头部，添加 nonce
            nonce = request.csp_nonce
            new_csp_parts = []
            
            # 处理 script-src
            if 'script-src' in csp_header:
                # 替换现有的 script-src
                import re
                csp_header = re.sub(
                    r'script-src\s+([^;]+)',
                    f'script-src \'self\' \'nonce-{nonce}\'',
                    csp_header
                )
            else:
                new_csp_parts.append(f'script-src \'self\' \'nonce-{nonce}\'',)
            
            # 处理 style-src
            if 'style-src' in csp_header:
                # 替换现有的 style-src
                csp_header = re.sub(
                    r'style-src\s+([^;]+)',
                    f'style-src \'self\' \'nonce-{nonce}\'',
                    csp_header
                )
            else:
                new_csp_parts.append(f'style-src \'self\' \'nonce-{nonce}\'',)
            
            # 添加新的 CSP 部分
            if new_csp_parts:
                if csp_header:
                    csp_header += '; ' + '; '.join(new_csp_parts)
                else:
                    csp_header = '; '.join(new_csp_parts)
            
            # 设置新的 CSP 头部
            if csp_header:
                response['Content-Security-Policy'] = csp_header
        
        return response