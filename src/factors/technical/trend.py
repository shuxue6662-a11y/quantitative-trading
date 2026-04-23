"""
趋势类技术指标
"""
import pandas as pd
import numpy as np


def calculate_ma(df: pd.DataFrame, periods: list = [5, 10, 20, 60]) -> pd.DataFrame:
    """
    计算移动平均线
    
    Args:
        df: DataFrame，必须包含Close列
        periods: 周期列表
        
    Returns:
        添加了MA列的DataFrame
    """
    df = df.copy()
    
    for period in periods:
        df[f'MA{period}'] = df['Close'].rolling(window=period).mean()
    
    return df


def calculate_macd(
    df: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> pd.DataFrame:
    """
    计算MACD指标
    
    Args:
        df: DataFrame
        fast_period: 快线周期
        slow_period: 慢线周期
        signal_period: 信号线周期
        
    Returns:
        添加了MACD列的DataFrame
    """
    df = df.copy()
    
    # 计算EMA
    ema_fast = df['Close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow_period, adjust=False).mean()
    
    # MACD线
    df['MACD'] = ema_fast - ema_slow
    
    # 信号线
    df['MACD_Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
    
    # 柱状图
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    return df


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    num_std: float = 2.0
) -> pd.DataFrame:
    """
    计算布林带
    
    Args:
        df: DataFrame
        period: 周期
        num_std: 标准差倍数
        
    Returns:
        添加了布林带列的DataFrame
    """
    df = df.copy()
    
    df['BB_Middle'] = df['Close'].rolling(window=period).mean()
    df['BB_Std'] = df['Close'].rolling(window=period).std()
    df['BB_Upper'] = df['BB_Middle'] + num_std * df['BB_Std']
    df['BB_Lower'] = df['BB_Middle'] - num_std * df['BB_Std']
    
    return df