"""
百度文心一言 Provider

支持 ERNIE-Bot-4.0, ERNIE-Bot-turbo 等模型
"""

from typing import List, Dict, Any, Optional, Iterator
import requests
import json
from .base import (
    BaseAIProvider,
    AIResponse,
    ProviderAPIException,
    ProviderAuthException,
    ProviderTimeoutException,
    ProviderRateLimitException,
)


class BaiduProvider(BaseAIProvider):
    """百度文心一言 Provider 实现"""

    # 模型对应的API端点
    MODEL_ENDPOINTS = {
        "ernie-bot-4.0": "completions_pro",
        "ernie-bot-turbo": "eb-instant",
        "ernie-bot": "completions",
    }

    def __init__(self, api_key: str, api_base: Optional[str] = None,
                 model_name: str = "ernie-bot-4.0", **kwargs):
        super().__init__(api_key, api_base, model_name, **kwargs)

        # API Key格式: "API_KEY,SECRET_KEY"
        if ',' in self.api_key:
            self.api_key, self.secret_key = self.api_key.split(',', 1)
        else:
            raise ValueError("百度文心API Key格式错误，应为: API_KEY,SECRET_KEY")

        self.access_token = None
        self._get_access_token()

    def _get_access_token(self):
        """获取access_token"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }

        try:
            response = requests.post(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            if "access_token" in result:
                self.access_token = result["access_token"]
            else:
                raise ProviderAuthException(f"获取access_token失败: {result}")

        except requests.exceptions.RequestException as e:
            raise ProviderAPIException(f"获取access_token失败: {str(e)}")

    def _get_api_url(self) -> str:
        """获取API URL"""
        endpoint = self.MODEL_ENDPOINTS.get(self.model_name, "completions_pro")

        if self.api_base:
            return f"{self.api_base}/{endpoint}?access_token={self.access_token}"
        else:
            return f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{endpoint}?access_token={self.access_token}"

    def chat(self, messages: List[Dict[str, str]],
             tools: Optional[List[Dict[str, Any]]] = None) -> AIResponse:
        """
        发送对话请求

        Args:
            messages: 消息列表
            tools: 工具列表（可选）

        Returns:
            AIResponse对象
        """
        try:
            url = self._get_api_url()

            # 构建请求体
            payload = {
                "messages": messages,
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
            }

            # 如果有工具定义，添加到参数中
            if tools:
                payload["functions"] = self._build_tools(tools)

            # 发送请求
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()

            # 检查错误
            if "error_code" in result:
                error_msg = result.get("error_msg", "未知错误")
                if result["error_code"] == 110:
                    raise ProviderAuthException(f"文心认证失败: {error_msg}")
                elif result["error_code"] == 18:
                    raise ProviderRateLimitException(f"文心频率限制: {error_msg}")
                else:
                    raise ProviderAPIException(f"文心API错误: {error_msg}")

            # 解析响应
            content = result.get("result", "")
            tool_calls = None

            # 检查是否有函数调用
            if "function_call" in result:
                fc = result["function_call"]
                tool_calls = [{
                    "id": "call_" + fc.get("name", ""),
                    "type": "function",
                    "function": {
                        "name": fc.get("name"),
                        "arguments": fc.get("arguments", "{}"),
                    }
                }]

            return AIResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=result.get("finish_reason"),
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
                model=self.model_name,
            )

        except requests.exceptions.Timeout:
            raise ProviderTimeoutException("文心请求超时")
        except requests.exceptions.RequestException as e:
            raise ProviderAPIException(f"文心API调用失败: {str(e)}")
        except Exception as e:
            raise ProviderAPIException(f"文心API调用失败: {str(e)}")

    def stream_chat(self, messages: List[Dict[str, str]],
                   tools: Optional[List[Dict[str, Any]]] = None) -> Iterator[str]:
        """
        流式对话请求

        Args:
            messages: 消息列表
            tools: 工具列表（可选）

        Yields:
            生成的文本片段
        """
        try:
            url = self._get_api_url()

            # 构建请求体
            payload = {
                "messages": messages,
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "stream": True,
            }

            # 如果有工具定义，添加到参数中
            if tools:
                payload["functions"] = self._build_tools(tools)

            # 发送流式请求
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
                stream=True
            )
            response.raise_for_status()

            # 逐行解析SSE响应
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data_str = line_text[6:]  # 去掉 "data: " 前缀
                        try:
                            data = json.loads(data_str)
                            if "result" in data:
                                yield data["result"]
                        except json.JSONDecodeError:
                            continue

        except requests.exceptions.Timeout:
            raise ProviderTimeoutException("文心请求超时")
        except requests.exceptions.RequestException as e:
            raise ProviderAPIException(f"文心API调用失败: {str(e)}")
        except Exception as e:
            raise ProviderAPIException(f"文心API调用失败: {str(e)}")

    def _build_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """
        构建文心工具格式

        Args:
            tools: 标准工具格式

        Returns:
            文心工具格式
        """
        if not tools:
            return None

        baidu_tools = []
        for tool in tools:
            baidu_tools.append({
                "name": tool.get("name"),
                "description": tool.get("description"),
                "parameters": tool.get("parameters", {}),
            })

        return baidu_tools
