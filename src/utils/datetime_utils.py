"""
时间工具模块
"""
from datetime import datetime, timedelta, date
from typing import Optional


def get_today() -> date:
    """获取今天日期"""
    return datetime.now().date()


def get_date_str(dt: Optional[date] = None, fmt: str = '%Y%m%d') -> str:
    """
    获取日期字符串
    
    Args:
        dt: 日期对象，None表示今天
        fmt: 格式
        
    Returns:
        日期字符串
    """
    if dt is None:
        dt = get_today()
    return dt.strftime(fmt)


def get_date_range(start_date: str, end_date: str, fmt: str = '%Y%m%d') -> list:
    """
    获取日期范围列表
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        fmt: 日期格式
        
    Returns:
        日期列表
    """
    start = datetime.strptime(start_date, fmt)
    end = datetime.strptime(end_date, fmt)
    
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime(fmt))
        current += timedelta(days=1)
    
    return dates


def is_trading_day(dt: Optional[date] = None) -> bool:
    """
    判断是否是交易日（简化版，仅排除周末）
    
    注：完整版需要考虑节假日，可以后续优化
    """
    if dt is None:
        dt = get_today()
    
    # 周一到周五
    return dt.weekday() < 5


def get_latest_trading_day() -> date:
    """获取最近的交易日"""
    today = get_today()
    
    if is_trading_day(today):
        # 如果当前时间在15:00之前，返回上一个交易日
        if datetime.now().hour < 15:
            today = today - timedelta(days=1)
    
    # 往前找到最近的交易日
    while not is_trading_day(today):
        today = today - timedelta(days=1)
    
    return today


def format_datetime(dt: datetime, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """格式化时间"""
    return dt.strftime(fmt)