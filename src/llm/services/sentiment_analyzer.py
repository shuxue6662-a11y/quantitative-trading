"""
情绪分析服务
"""
import json
import re
from typing import Dict, List, Optional
from pathlib import Path

from src.llm.core.ollama_client import OllamaClient
from src.utils.logger import logger
from src.utils.config_loader import config_loader


class SentimentAnalyzer:
    """LLM情绪分析器"""
    
    def __init__(self):
        """初始化"""
        self.client = OllamaClient()
        
        # 加载配置
        llm_config = config_loader.load('llm_config')
        model_config = llm_config['ollama']['models']['sentiment_analyzer']
        
        self.model_name = model_config['name']
        self.temperature = model_config['temperature']
        self.max_tokens = model_config['max_tokens']
        self.think = model_config.get('think', False)  # 获取think配置
        
        # 加载Prompt模板
        prompt_path = Path('src/llm/prompts/sentiment_analysis.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
        
        logger.info(f"情绪分析器初始化: {self.model_name} (think={self.think})")
    
    def analyze(self, text: str) -> Optional[Dict]:
        """
        分析单条文本的情绪
        
        Args:
            text: 文本内容
            
        Returns:
            {
                'sentiment_score': float,  # 0-1
                'confidence': float,       # 0-1
                'keywords': List[str],
                'reason': str
            }
        """
        # 文本预处理
        text = text.strip()
        if len(text) < 10:
            logger.warning("文本过短，跳过分析")
            return None
        
        # 截断过长文本
        if len(text) > 500:
            text = text[:500] + "..."
        
        # 构造Prompt
        prompt = self.prompt_template.format(text=text)
        
        # 调用LLM
        logger.debug(f"分析文本: {text[:50]}...")
        response = self.client.generate(
            model=self.model_name,
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            think=self.think  # 传入think参数
        )
        
        if not response:
            logger.error("LLM返回为空")
            return None
        
        # 解析JSON
        result = self._parse_response(response)
        
        if result:
            logger.debug(
                f"分析结果: score={result['sentiment_score']:.2f}, "
                f"confidence={result['confidence']:.2f}"
            )
        
        return result
    
    def _parse_response(self, response: str) -> Optional[Dict]:
        """
        解析LLM返回的JSON
        
        Args:
            response: LLM原始响应
            
        Returns:
            解析后的字典
        """
        try:
            # 尝试提取JSON部分（处理LLM可能添加的额外文字）
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
            else:
                result = json.loads(response)
            
            # 验证必要字段
            required_fields = ['sentiment_score', 'confidence', 'keywords']
            if not all(field in result for field in required_fields):
                logger.error(f"缺少必要字段: {result}")
                return None
            
            # 验证数值范围
            if not (0 <= result['sentiment_score'] <= 1):
                logger.warning(f"sentiment_score超出范围: {result['sentiment_score']}")
                result['sentiment_score'] = max(0, min(1, result['sentiment_score']))
            
            if not (0 <= result['confidence'] <= 1):
                logger.warning(f"confidence超出范围: {result['confidence']}")
                result['confidence'] = max(0, min(1, result['confidence']))
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}\n原始响应: {response}")
            return None
        except Exception as e:
            logger.error(f"解析响应失败: {e}")
            return None
    
    def analyze_batch(self, texts: List[str], batch_size: int = 10) -> List[Dict]:
        """
        批量分析
        
        Args:
            texts: 文本列表
            batch_size: 每批数量
            
        Returns:
            结果列表
        """
        results = []
        
        for i, text in enumerate(texts):
            logger.info(f"分析进度: {i+1}/{len(texts)}")
            
            result = self.analyze(text)
            if result:
                results.append(result)
            else:
                # 失败时添加默认值
                results.append({
                    'sentiment_score': 0.5,
                    'confidence': 0.0,
                    'keywords': [],
                    'reason': '分析失败'
                })
        
        return results