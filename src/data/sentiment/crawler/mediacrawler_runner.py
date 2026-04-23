"""
MediaCrawler运行器
"""
import subprocess
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from src.utils.logger import logger


class MediaCrawlerRunner:
    """MediaCrawler运行器"""
    
    def __init__(self):
        """初始化"""
        self.mc_path = Path('external/MediaCrawler')
        self.data_dir = Path('data/raw/sentiment')
        
        # 确保数据目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.mc_path.exists():
            logger.error("MediaCrawler未安装")
            self.available = False
        else:
            self.available = True
    
    def crawl_weibo_keywords(
        self, 
        keywords: List[str],
        max_notes: int = 20
    ) -> List[Dict]:
        """
        爬取微博关键词
        
        Args:
            keywords: 关键词列表
            max_notes: 每个关键词最大帖子数
            
        Returns:
            爬取结果列表
        """
        if not self.available:
            logger.warning("MediaCrawler不可用，返回空数据")
            return []
        
        try:
            logger.info(f"启动MediaCrawler爬取: {', '.join(keywords)}")
            
            # 构建命令
            cmd = [
                'uv', 'run', 'main.py',
                '--platform', 'weibo',
                '--lt', 'cookie',  # 使用cookie登录（需要提前配置）
                '--type', 'search',
            ]
            
            # 运行MediaCrawler
            result = subprocess.run(
                cmd,
                cwd=self.mc_path,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                logger.error(f"MediaCrawler执行失败: {result.stderr}")
                return []
            
            # 读取输出文件
            return self._read_crawled_data()
            
        except subprocess.TimeoutExpired:
            logger.error("MediaCrawler执行超时")
            return []
        except Exception as e:
            logger.error(f"运行MediaCrawler失败: {e}")
            return []
    
    def _read_crawled_data(self) -> List[Dict]:
        """读取爬取的数据"""
        results = []
        
        # MediaCrawler输出路径（根据实际配置调整）
        output_dir = self.mc_path / 'data' / 'weibo'
        
        if not output_dir.exists():
            logger.warning(f"输出目录不存在: {output_dir}")
            return []
        
        # 读取JSONL文件
        jsonl_files = list(output_dir.glob('*.jsonl'))
        
        for file in jsonl_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            results.append({
                                'text': data.get('note_desc', ''),
                                'author': data.get('user_info', {}).get('nickname', ''),
                                'likes': data.get('liked_count', 0),
                                'comments': data.get('comments_count', 0),
                                'shares': data.get('shared_count', 0),
                                'publish_time': self._parse_time(data.get('publish_time', '')),
                                'url': data.get('note_url', ''),
                                'platform': 'weibo'
                            })
            except Exception as e:
                logger.error(f"读取文件失败 {file}: {e}")
        
        logger.info(f"读取到 {len(results)} 条数据")
        return results
    
    def _parse_time(self, time_str: str) -> datetime:
        """解析时间字符串"""
        try:
            return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        except:
            return datetime.now()