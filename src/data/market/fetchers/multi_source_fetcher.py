"""
多数据源智能切换
"""
import pandas as pd
from typing import Optional, List
from datetime import datetime

from .akshare_fetcher import AKShareFetcher
from .baostock_fetcher import BaoStockFetcher
from .tushare_fetcher import TushareFetcher
from src.utils.logger import logger
from src.utils.config_loader import config_loader


class MultiSourceFetcher:
    """多数据源智能切换器"""
    
    def __init__(self):
        """初始化所有数据源"""
        # 加载配置
        config = config_loader.load('data_sources')
        
        # 初始化数据源
        self.sources = {}
        
        if config.get('akshare', {}).get('enabled', True):
            self.sources['akshare'] = AKShareFetcher()
            logger.info("✓ AKShare 数据源已启用")
        
        if config.get('baostock', {}).get('enabled', True):
            self.sources['baostock'] = BaoStockFetcher()
            logger.info("✓ BaoStock 数据源已启用")
        
        if config.get('tushare', {}).get('enabled', False):
            ts_fetcher = TushareFetcher()
            if ts_fetcher.ts is not None:
                self.sources['tushare'] = ts_fetcher
                logger.info("✓ Tushare 数据源已启用")
        
        # 数据源优先级（可配置）
        self.priority = config.get('priority', ['akshare', 'baostock', 'tushare'])
        
        # 过滤掉未启用的源
        self.priority = [s for s in self.priority if s in self.sources]
        
        logger.info(f"数据源优先级: {' > '.join(self.priority)}")
        
        # 健康状态跟踪
        self.health_status = {source: True for source in self.sources}
        self.failure_count = {source: 0 for source in self.sources}
    
    def get_stock_daily(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = 'qfq'
    ) -> Optional[pd.DataFrame]:
        """
        智能多源获取数据
        
        自动按优先级尝试各数据源，直到成功
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            
        Returns:
            DataFrame 或 None
        """
        logger.info(f"📥 多源获取 {stock_code}")
        
        for source_name in self.priority:
            # 跳过不健康的源（连续失败3次）
            if self.failure_count[source_name] >= 3:
                logger.debug(f"  跳过 {source_name}（不健康）")
                continue
            
            try:
                logger.info(f"  尝试 {source_name}...")
                
                fetcher = self.sources[source_name]
                df = fetcher.get_stock_daily(stock_code, start_date, end_date, adjust)
                
                if df is not None and len(df) > 0:
                    logger.info(f"  ✅ {source_name} 成功 ({len(df)} 条)")
                    
                    # 重置失败计数
                    self.failure_count[source_name] = 0
                    self.health_status[source_name] = True
                    
                    # 添加数据源标记
                    df['DataSource'] = source_name
                    
                    return df
                else:
                    logger.warning(f"  ⚠️ {source_name} 返回空数据")
                    self.failure_count[source_name] += 1
                    
            except Exception as e:
                logger.warning(f"  ❌ {source_name} 失败: {e}")
                self.failure_count[source_name] += 1
                
                # 连续失败3次标记为不健康
                if self.failure_count[source_name] >= 3:
                    self.health_status[source_name] = False
                    logger.warning(f"  🚫 {source_name} 已标记为不健康")
        
        # 所有源都失败
        logger.error(f"❌ 所有数据源均失败: {stock_code}")
        return None
    
    def get_health_report(self) -> dict:
        """获取数据源健康报告"""
        return {
            'sources': list(self.sources.keys()),
            'priority': self.priority,
            'health': self.health_status,
            'failures': self.failure_count
        }
    
    def reset_health(self, source_name: Optional[str] = None):
        """重置健康状态"""
        if source_name:
            self.failure_count[source_name] = 0
            self.health_status[source_name] = True
            logger.info(f"重置 {source_name} 健康状态")
        else:
            for source in self.sources:
                self.failure_count[source] = 0
                self.health_status[source] = True
            logger.info("重置所有数据源健康状态")