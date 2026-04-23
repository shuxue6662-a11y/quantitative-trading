"""
MediaCrawler配置管理
"""
import os
import sys
from pathlib import Path
from typing import List

from src.utils.logger import logger


class MediaCrawlerConfig:
    """MediaCrawler配置管理器"""
    
    def __init__(self):
        """初始化"""
        self.mc_path = Path('external/MediaCrawler')
        self.config_path = self.mc_path / 'config' / 'base_config.py'
        
        if not self.mc_path.exists():
            logger.error(f"MediaCrawler未找到: {self.mc_path}")
            self.available = False
        else:
            self.available = True
            logger.info(f"MediaCrawler路径: {self.mc_path}")
    
    def set_keywords(self, keywords: List[str]):
        """
        设置搜索关键词
        
        Args:
            keywords: 关键词列表（股票名称）
        """
        if not self.available:
            return
        
        # 读取配置文件
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = f.read()
        
        # 替换关键词
        keywords_str = ','.join(keywords)
        
        # 查找KEYWORDS行并替换
        lines = config.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('KEYWORDS = '):
                lines[i] = f'KEYWORDS = "{keywords_str}"'
                logger.info(f"设置关键词: {keywords_str}")
                break
        
        # 写回
        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def set_platform(self, platform: str):
        """设置平台"""
        if not self.available:
            return
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = f.read()
        
        lines = config.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('PLATFORM = '):
                lines[i] = f'PLATFORM = "{platform}"'
                logger.info(f"设置平台: {platform}")
                break
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))