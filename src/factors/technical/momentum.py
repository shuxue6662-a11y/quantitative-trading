"""
动量类技术指标
"""
import pandas as pd
import numpy as np


def calculate_rsi(df: pd.DataFrame, periods: list = [6, 12, 24]) -> pd.DataFrame:
    """
    计算RSI指标
    
    Args:
        df: DataFrame
        periods: 周期列表
        
    Returns:
        添加了RSI列的DataFrame
    """
    df = df.copy()
    
    # 计算价格变化
    delta = df['Close'].diff()
    
    for period in periods:
        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # 计算RS和RSI
        rs = avg_gain / avg_loss
        df[f'RSI{period}'] = 100 - (100 / (1 + rs))
    
    return df


def calculate_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    """
    计算KDJ指标
    
    Args:
        df: DataFrame
        n: RSV周期
        m1: K值平滑周期
        m2: D值平滑周期
        
    Returns:
        添加了KDJ列的DataFrame
    """
    df = df.copy()
    
    # 计算RSV
    low_n = df['Low'].rolling(window=n).min()
    high_n = df['High'].rolling(window=n).max()
    
    df['RSV'] = (df['Close'] - low_n) / (high_n - low_n) * 100
    
    # 计算K值和D值
    df['K'] = df['RSV'].ewm(com=m1-1).mean()
    df['D'] = df['K'].ewm(com=m2-1).mean()
    
    # 计算J值
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    return df