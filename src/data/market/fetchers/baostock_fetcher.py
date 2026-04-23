"""
BaoStock 数据获取封装
"""
import pandas as pd
import baostock as bs
from datetime import datetime, timedelta
from typing import Optional
import time

from src.utils.logger import logger
from src.utils.datetime_utils import get_date_str


class BaoStockFetcher:
    """BaoStock数据获取器"""
    
    def __init__(self, retry_times: int = 3, retry_delay: int = 3):
        """
        初始化
        
        Args:
            retry_times: 重试次数
            retry_delay: 重试延迟（秒）
        """
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self._logged_in = False
    
    def _login(self):
        """登录BaoStock"""
        if not self._logged_in:
            lg = bs.login()
            if lg.error_code != '0':
                logger.error(f"BaoStock登录失败: {lg.error_msg}")
                return False
            self._logged_in = True
            logger.debug("BaoStock登录成功")
        return True
    
    def _logout(self):
        """登出"""
        if self._logged_in:
            bs.logout()
            self._logged_in = False
    
    def _get_bs_code(self, stock_code: str) -> str:
        """
        转换为BaoStock代码格式
        
        Args:
            stock_code: 6位代码
            
        Returns:
            BaoStock格式代码（如 sh.600519）
        """
        if stock_code.startswith('6'):
            return f'sh.{stock_code}'
        elif stock_code.startswith(('0', '3')):
            return f'sz.{stock_code}'
        else:
            return f'sz.{stock_code}'
    
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
            adjust: 复权类型（baostock: 1=后复权, 2=前复权, 3=不复权）
            
        Returns:
            DataFrame 或 None
        """
        # 默认时间范围
        if end_date is None:
            end_date = get_date_str(fmt='%Y-%m-%d')
        else:
            # 转换格式 YYYYMMDD -> YYYY-MM-DD
            end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
        
        if start_date is None:
            start_date = get_date_str(
                datetime.now().date() - timedelta(days=400),
                fmt='%Y-%m-%d'
            )
        else:
            start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        
        # 转换复权参数
        adjustflag = '2' if adjust == 'qfq' else '1' if adjust == 'hfq' else '3'
        
        for attempt in range(self.retry_times):
            try:
                # 登录
                if not self._login():
                    return None
                
                # 转换代码格式
                bs_code = self._get_bs_code(stock_code)
                
                logger.info(f"获取 {stock_code} 数据: {start_date} ~ {end_date}")
                
                # 查询日K线数据
                rs = bs.query_history_k_data_plus(
                    bs_code,
                    "date,open,high,low,close,volume,amount,pctChg",
                    start_date=start_date,
                    end_date=end_date,
                    frequency="d",
                    adjustflag=adjustflag
                )
                
                if rs.error_code != '0':
                    logger.error(f"查询失败: {rs.error_msg}")
                    return None
                
                # 获取数据
                data_list = []
                while rs.error_code == '0' and rs.next():
                    data_list.append(rs.get_row_data())
                
                if not data_list:
                    logger.warning(f"{stock_code} 无数据")
                    return None
                
                # 转换为DataFrame
                df = pd.DataFrame(
                    data_list,
                    columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Amount', 'PctChange']
                )
                
                # 转换数据类型
                for col in ['Open', 'High', 'Low', 'Close', 'Volume', 'Amount', 'PctChange']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # 转换日期
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                df = df.dropna().sort_values('Date').reset_index(drop=True)
                
                logger.info(f"✓ 获取成功: {len(df)} 条")
                return df
                
            except Exception as e:
                logger.warning(f"获取失败 (尝试 {attempt+1}/{self.retry_times}): {e}")
                if attempt < self.retry_times - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"获取 {stock_code} 数据失败")
                    return None
            finally:
                # 不要每次都登出，保持登录状态
                pass
    
    def __del__(self):
        """析构时登出"""
        self._logout()