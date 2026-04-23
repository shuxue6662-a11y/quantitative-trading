"""
数据获取模块
"""
from .akshare_fetcher import AKShareFetcher
from .baostock_fetcher import BaoStockFetcher
from .tushare_fetcher import TushareFetcher
from .multi_source_fetcher import MultiSourceFetcher

__all__ = [
    'AKShareFetcher',
    'BaoStockFetcher', 
    'TushareFetcher',
    'MultiSourceFetcher'
]