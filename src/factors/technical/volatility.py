"""
波动率类指标
"""
import pandas as pd
import numpy as np


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    计算ATR（平均真实波幅）
    
    Args:
        df: DataFrame
        period: 周期
        
    Returns:
        添加了ATR列的DataFrame
    """
    df = df.copy()
    
    # 计算真实波幅
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # 计算ATR
    df['ATR'] = tr.rolling(window=period).mean()
    
    return df


def calculate_volatility(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """
    计算历史波动率（年化）
    
    Args:
        df: DataFrame
        period: 周期
        
    Returns:
        添加了Volatility列的DataFrame
    """
    df = df.copy()
    
    returns = df['Close'].pct_change()
    df['Volatility'] = returns.rolling(window=period).std() * np.sqrt(252) * 100
    
    return df