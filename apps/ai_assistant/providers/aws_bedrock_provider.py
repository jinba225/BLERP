"""
AWS Bedrock Provider

支持模型：
- Anthropic Claude 3 Sonnet
- Anthropic Claude 2
- Amazon Titan Text
- Amazon Titan Embeddings

官方文档：https://docs.aws.amazon.com/bedrock/
"""

from typing import Dict, Any, Optional
from ..base import BaseAIProvider, AIResponse, ProviderException
import boto3
from typing import Dict, Any, Optional, Iterator
from ..base import BaseAIProvider, AIResponse, ProviderException
import boto3
from ..base import BaseAIProvider, AIResponse, ProviderException


class BedrockProvider(BaseAIProvider):
    """AWS Bedrock 提供商"""
    
    def __init__(self, aws_access_key: str, aws_secret_key: str,
                 region: str = "us-east-1", model_id: str = None):
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.region = region
        self.model_id = model_id
    
    def chat(self, messages: list, **kwargs) -> AIResponse:
        """调用 Bedrock API"""
        # 构建 Bedrock 请求
        request_body = self._build_request_body(messages, **kwargs)
        
        # 创建 Bedrock 客户端
        client = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.region,
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key
        )
        
        try:
            # 调用 Bedrock API
            response = client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
        except Exception as e:
            raise ProviderAPIException(f"AWS Bedrock API 调用失败: {str(e)}")
        
        # 解析 Bedrock 响应
        response_body = json.loads(response['Body'].read())
        content = response_body.get('output', {}).get('text', '')
        usage = response_body.get('inputTokenCount', 0) + response_body.get('generationTokenCount', 0)
        
        return AIResponse(
            content=content,
            model=self.model_id,
            usage={
                'prompt_tokens': response_body.get('inputTokenCount', 0),
                'completion_tokens': response_body.get('generationTokenCount', 0)
            },
            raw_response=response_body
        )
    
    def _build_request_body(self, messages: list, **kwargs) -> Dict:
        """构建 Bedrock 请求体"""
        # 转换为 Bedrock 格式
        bedrock_messages = []
        for msg in messages:
            if msg.get('role') == 'system':
                bedrock_messages.append({
                    "role": msg.get('role'),
                    "content": [{"text": msg.get('content')}]
                })
            elif msg.get('role') == 'user':
                bedrock_messages.append({
                    "role": "user",
                    "content": [{"text": msg.get('content')}]
                })
            elif msg.get('role') == 'assistant':
                bedrock_messages.append({
                    "role": "assistant",
                    "content": [{"text": msg.get('content')}]
                })
        
        # 构建推理配置
        inference_config = {
            "maxTokens": kwargs.get('max_tokens', 2048),
            "temperature": kwargs.get('temperature', 0.7),
            "topP": kwargs.get('top_p', 0.95),
            "stopSequences": kwargs.get('stop_sequences', []),
        }
        
        return {
            "messages": bedrock_messages,
            "inferenceConfig": inference_config
        }
