"""
MediaCrawler数据读取封装（简化版）
直接读取MediaCrawler爬取的JSONL文件
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import random

from src.utils.logger import logger


class MediaCrawlerWrapper:
    """MediaCrawler数据读取器"""
    
    def __init__(self):
        """初始化"""
        # 数据目录
        self.data_dir = Path('data/raw/sentiment/weibo/jsonl')
        
        # 检查是否存在真实数据
        self.has_real_data = self.data_dir.exists() and any(self.data_dir.glob('*.jsonl'))
        
        if self.has_real_data:
            logger.info(f"MediaCrawler数据目录: {self.data_dir}")
            logger.info("将使用真实爬取数据")
        else:
            logger.info("未找到真实数据，将使用模拟数据")
    
    def crawl_weibo_stock(
        self, 
        stock_code: str, 
        stock_name: str, 
        limit: int = 50
    ) -> List[Dict]:
        """
        读取微博股票数据
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            limit: 数量限制
            
        Returns:
            文本列表
        """
        if self.has_real_data:
            # 尝试读取真实数据
            real_data = self._read_real_data(stock_name, limit)
            
            if real_data:
                logger.info(f"使用真实数据: {stock_name} ({len(real_data)} 条)")
                return real_data
            else:
                logger.warning(f"{stock_name} 无真实数据，使用模拟数据")
        
        # 使用模拟数据
        return self._generate_mock_data(stock_name, limit)
    
    def _read_real_data(self, stock_name: str, limit: int) -> List[Dict]:
        """读取真实爬取的数据"""
        results = []
        
        try:
            # 查找最新的数据文件
            content_files = sorted(
                self.data_dir.glob('search_contents_*.jsonl'),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            comment_files = sorted(
                self.data_dir.glob('search_comments_*.jsonl'),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            if not content_files:
                logger.warning(f"未找到数据文件")
                return []
            
            # 读取内容文件
            for file in content_files[:3]:
                logger.info(f"读取文件: {file.name}")
                
                with open(file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if not line.strip():
                            continue
                        
                        if len(results) >= limit:
                            break
                        
                        try:
                            data = json.loads(line)
                            
                            # 🔥 真实格式字段映射
                            text = data.get('content', data.get('note_desc', ''))
                            
                            # 跳过空文本
                            if not text or len(text) < 10:
                                continue
                            
                            # 关键词过滤
                            if stock_name not in text:
                                short_name = stock_name.replace('股份', '').replace('集团', '').replace('科技', '')
                                if short_name not in text:
                                    continue
                            
                            # 🔥 构建标准格式（真实字段）
                            results.append({
                                'text': text,
                                'author': data.get('nickname', ''),
                                'followers': 0,  # 需要从user对象获取
                                'likes': int(data.get('liked_count', 0)),
                                'comments': int(data.get('comments_count', 0)),
                                'shares': int(data.get('shared_count', 0)),
                                'publish_time': self._parse_time(data.get('create_time', '')),
                                'url': data.get('note_url', ''),
                                'platform': 'weibo'
                            })
                            
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.debug(f"  行 {line_num} 解析失败: {e}")
                            continue
                
                logger.info(f"  过滤后保留 {len(results)} 条相关数据")
                
                if results:
                    break
            
            # 补充评论数据
            if len(results) < limit and comment_files:
                logger.info("补充评论数据...")
                
                for file in comment_files[:1]:
                    with open(file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if not line.strip():
                                continue
                            
                            if len(results) >= limit:
                                break
                            
                            try:
                                data = json.loads(line)
                                
                                # 🔥 评论字段映射
                                text = data.get('content', '')
                                
                                if not text or len(text) < 10:
                                    continue
                                
                                # 关键词过滤
                                if stock_name not in text:
                                    short_name = stock_name.replace('股份', '').replace('集团', '').replace('科技', '')
                                    if short_name not in text:
                                        continue
                                
                                results.append({
                                    'text': text,
                                    'author': data.get('nickname', ''),
                                    'followers': 0,
                                    'likes': int(data.get('comment_like_count', 0)),
                                    'comments': int(data.get('sub_comment_count', 0)),
                                    'shares': 0,
                                    'publish_time': self._parse_time(data.get('create_time', '')),
                                    'url': '',
                                    'platform': 'weibo'
                                })
                                
                            except (json.JSONDecodeError, ValueError):
                                continue
                    
                    logger.info(f"  补充 {len(results)} 条评论数据")
            
        except Exception as e:
            logger.error(f"读取真实数据失败: {e}")
        
        return results[:limit]
    
    def _parse_time(self, time_str) -> datetime:
        """解析时间字符串"""
        if not time_str:
            return datetime.now()
        
        # 时间戳（秒）
        if isinstance(time_str, (int, float)):
            try:
                if time_str > 1e10:  # 毫秒时间戳
                    return datetime.fromtimestamp(time_str / 1000)
                else:  # 秒时间戳
                    return datetime.fromtimestamp(time_str)
            except:
                pass
        
        # 字符串格式
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%m-%d %H:%M',  # 微博特殊格式
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(str(time_str), fmt)
                # 如果只有月日，补充年份
                if fmt == '%m-%d %H:%M':
                    dt = dt.replace(year=datetime.now().year)
                return dt
            except:
                continue
        
        # 相对时间（如"1小时前"）
        time_str = str(time_str).lower()
        now = datetime.now()
        
        if '分钟' in time_str or 'minute' in time_str:
            try:
                mins = int(''.join(filter(str.isdigit, time_str)))
                return now - timedelta(minutes=mins)
            except:
                pass
        elif '小时' in time_str or 'hour' in time_str:
            try:
                hours = int(''.join(filter(str.isdigit, time_str)))
                return now - timedelta(hours=hours)
            except:
                pass
        elif '天' in time_str or 'day' in time_str:
            try:
                days = int(''.join(filter(str.isdigit, time_str)))
                return now - timedelta(days=days)
            except:
                pass
        
        return now
    
    def _generate_mock_data(self, stock_name: str, limit: int) -> List[Dict]:
        """生成模拟数据（作为备选）"""
        logger.info(f"生成模拟数据: {stock_name}")
        
        mock_texts = [
            f"{stock_name}今天表现不错，看好后市发展",
            f"业绩超预期！{stock_name}值得关注",
            f"{stock_name}技术面已经走强，建议关注",
            f"今天{stock_name}跌了，但长期看好",
            f"{stock_name}最近资金流入明显，可能有行情",
            f"机构开始调研{stock_name}了，利好信号",
            f"{stock_name}的估值还是偏高，要谨慎",
            f"刚买入{stock_name}，期待未来表现",
            f"{stock_name}行业前景很好，长期持有",
            f"卖出{stock_name}，获利了结"
        ]
        
        results = []
        for i in range(min(limit, len(mock_texts))):
            results.append({
                'text': mock_texts[i % len(mock_texts)],
                'platform': 'weibo',
                'author': f'模拟用户{random.randint(1000, 9999)}',
                'followers': random.randint(100, 10000),
                'likes': random.randint(0, 100),
                'comments': random.randint(0, 50),
                'shares': random.randint(0, 20),
                'publish_time': datetime.now() - timedelta(hours=random.randint(1, 48)),
                'url': f'https://weibo.com/mock/{i}'
            })
        
        return results
    
    def crawl_stock_tieba(self, stock_name: str, limit: int = 50) -> List[Dict]:
        """爬取股吧（暂时用模拟数据）"""
        return self._generate_mock_data(stock_name, min(limit, 20))