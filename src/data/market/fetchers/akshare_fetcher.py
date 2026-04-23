"""
AKShare 数据获取封装
"""
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
from typing import Optional
import time

from src.utils.logger import logger
from src.utils.datetime_utils import get_date_str


class AKShareFetcher:
    """AKShare数据获取器"""
    
    def __init__(self, timeout: int = 30, retry_times: int = 3, retry_delay: int = 5):
        """
        初始化
        
        Args:
            timeout: 超时时间（秒）
            retry_times: 重试次数
            retry_delay: 重试延迟（秒）
        """
        self.timeout = timeout
        self.retry_times = retry_times
        self.retry_delay = retry_delay
    
    def get_stock_daily(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = 'qfq'
    ) -> Optional[pd.DataFrame]:
        """
        获取股票日线数据
        
        Args:
            stock_code: 6位股票代码
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            adjust: 复权类型 'qfq'-前复权, 'hfq'-后复权, ''-不复权
            
        Returns:
            DataFrame 或 None
        """
        # 默认时间范围
        if end_date is None:
            end_date = get_date_str()
        if start_date is None:
            start_date = get_date_str(
                datetime.now().date() - timedelta(days=400)
            )
        
        for attempt in range(self.retry_times):
            try:
                logger.info(f"获取 {stock_code} 数据: {start_date} ~ {end_date}")
                
                df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period='daily',
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust
                )
                
                if df.empty:
                    logger.warning(f"{stock_code} 无数据")
                    return None
                
                # 统一列名
                df = df.rename(columns={
                    '日期': 'Date',
                    '开盘': 'Open',
                    '收盘': 'Close',
                    '最高': 'High',
                    '最低': 'Low',
                    '成交量': 'Volume',
                    '成交额': 'Amount',
                    '涨跌幅': 'PctChange'
                })
                
                # 转换日期
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                df = df.sort_values('Date').reset_index(drop=True)
                
                logger.info(f"✓ 获取成功: {len(df)} 条")
                return df
                
            except Exception as e:
                logger.warning(f"获取失败 (尝试 {attempt+1}/{self.retry_times}): {e}")
                if attempt < self.retry_times - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"获取 {stock_code} 数据失败")
                    return None
    
    def get_stock_info(self, stock_code: str) -> Optional[dict]:
        """
        获取股票基础信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票信息字典
        """
        try:
            info_df = ak.stock_individual_info_em(symbol=stock_code)
            
            info = {}
            for _, row in info_df.iterrows():
                info[row['item']] = row['value']
            
            return {
                'code': stock_code,
                'name': info.get('股票简称', ''),
                'industry': info.get('行业', ''),
                'market_cap': info.get('总市值', 0),
                'pe_ttm': info.get('市盈率-动态', 0),
                'pb': info.get('市净率', 0)
            }
            
        except Exception as e:
            logger.error(f"获取 {stock_code} 信息失败: {e}")
            return None
    
    def get_realtime_quote(self, stock_code: str) -> Optional[dict]:
        """
        获取实时行情
        
        Args:
            stock_code: 股票代码
            
        Returns:
            实时行情字典
        """
        try:
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == stock_code]
            
            if stock_data.empty:
                return None
            
            row = stock_data.iloc[0]
            return {
                'code': row['代码'],
                'name': row['名称'],
                'price': row['最新价'],
                'pct_change': row['涨跌幅'],
                'volume': row['成交量'],
                'amount': row['成交额']
            }
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return None