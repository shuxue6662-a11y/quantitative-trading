"""
Tushare 数据获取封装（可选）
"""
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta
import time

from src.utils.logger import logger
from src.utils.datetime_utils import get_date_str
from src.utils.config_loader import config_loader


class TushareFetcher:
    """Tushare数据获取器"""
    
    def __init__(self, retry_times: int = 3, retry_delay: int = 3):
        """初始化"""
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        
        # 加载token
        try:
            secrets = config_loader.load('secrets')
            token = secrets.get('tushare', {}).get('token', '')
            
            if not token:
                logger.warning("Tushare token未配置，该数据源不可用")
                self.ts = None
            else:
                import tushare as ts
                ts.set_token(token)
                self.ts = ts.pro_api()
                logger.info("Tushare初始化成功")
        except Exception as e:
            logger.warning(f"Tushare初始化失败: {e}")
            self.ts = None
    
    def _convert_ts_code(self, stock_code: str) -> str:
        """
        转换为Tushare代码格式
        
        Args:
            stock_code: 6位代码
            
        Returns:
            Tushare格式（如 600519.SH）
        """
        if stock_code.startswith('6'):
            return f'{stock_code}.SH'
        elif stock_code.startswith(('0', '3')):
            return f'{stock_code}.SZ'
        else:
            return f'{stock_code}.SZ'
    
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
            adjust: 复权类型
            
        Returns:
            DataFrame 或 None
        """
        if self.ts is None:
            logger.warning("Tushare不可用")
            return None
        
        # 默认时间范围
        if end_date is None:
            end_date = get_date_str()
        if start_date is None:
            start_date = get_date_str(
                datetime.now().date() - timedelta(days=400)
            )
        
        # 转换代码
        ts_code = self._convert_ts_code(stock_code)
        
        for attempt in range(self.retry_times):
            try:
                logger.info(f"获取 {stock_code} 数据: {start_date} ~ {end_date}")
                
                # 获取数据
                df = self.ts.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if df is None or df.empty:
                    logger.warning(f"{stock_code} 无数据")
                    return None
                
                # 如果需要复权，获取复权因子
                if adjust in ['qfq', 'hfq']:
                    adj_df = self.ts.adj_factor(
                        ts_code=ts_code,
                        start_date=start_date,
                        end_date=end_date
                    )
                    if adj_df is not None and not adj_df.empty:
                        df = df.merge(adj_df[['trade_date', 'adj_factor']], on='trade_date', how='left')
                        df['adj_factor'] = df['adj_factor'].fillna(method='ffill').fillna(1)
                        
                        # 应用复权
                        for col in ['open', 'high', 'low', 'close']:
                            df[col] = df[col] * df['adj_factor']
                
                # 统一列名
                df = df.rename(columns={
                    'trade_date': 'Date',
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'vol': 'Volume',
                    'amount': 'Amount',
                    'pct_chg': 'PctChange'
                })
                
                # 转换日期
                df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d').dt.date
                df = df.sort_values('Date').reset_index(drop=True)
                
                # 选择需要的列
                df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Amount', 'PctChange']]
                
                logger.info(f"✓ 获取成功: {len(df)} 条")
                return df
                
            except Exception as e:
                logger.warning(f"获取失败 (尝试 {attempt+1}/{self.retry_times}): {e}")
                if attempt < self.retry_times - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"获取 {stock_code} 数据失败")
                    return None
        
        return None