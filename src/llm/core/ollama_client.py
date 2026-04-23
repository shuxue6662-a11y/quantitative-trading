"""
Ollama客户端封装
"""
import requests
import json
from typing import Dict, Any, Optional
from src.utils.logger import logger
from src.utils.config_loader import config_loader


class OllamaClient:
    """Ollama本地大模型客户端"""
    
    def __init__(self):
        """初始化客户端"""
        # 加载配置
        self.config = config_loader.load('llm_config')
        self.base_url = self.config['ollama']['base_url']
        self.timeout = self.config['ollama']['timeout']
        
        logger.info(f"Ollama客户端初始化: {self.base_url} (超时: {self.timeout}s)")
    
    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        think: Optional[bool] = None,  # 新增参数
        **kwargs
    ) -> Optional[str]:
        """
        生成文本
        
        Args:
            model: 模型名称
            prompt: 提示词
            temperature: 温度
            max_tokens: 最大token数
            think: 是否启用深度思考（针对Qwen3）
            
        Returns:
            生成的文本
        """
        url = f"{self.base_url}/api/generate"
        
        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
            **kwargs
        }
        
        # 如果明确指定think参数
        if think is not None:
            options["think"] = think
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": options
        }
        
        try:
            logger.debug(f"请求模型: {model}, 超时: {self.timeout}s")
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get('response', '')
            
            if not generated_text:
                logger.warning(f"模型返回为空，完整响应: {result}")
            
            return generated_text
            
        except requests.exceptions.Timeout:
            logger.error(f"请求超时 ({self.timeout}s): {model}")
            logger.info("提示: Qwen3深度思考需要更长时间，可以:")
            logger.info("  1. 增加 config/llm_config.yaml 中的 timeout")
            logger.info("  2. 或禁用深度思考 (think: false)")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return None
    
    def chat(
        self,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 500,
        think: Optional[bool] = None  # 新增参数
    ) -> Optional[str]:
        """
        对话模式
        
        Args:
            model: 模型名称
            messages: 消息列表 [{"role": "user", "content": "..."}]
            think: 是否启用深度思考
            
        Returns:
            回复文本
        """
        url = f"{self.base_url}/api/chat"
        
        options = {
            "temperature": temperature,
            "num_predict": max_tokens
        }
        
        if think is not None:
            options["think"] = think
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get('message', {}).get('content', '')
            
        except Exception as e:
            logger.error(f"对话失败: {e}")
            return None
    
    def check_health(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False