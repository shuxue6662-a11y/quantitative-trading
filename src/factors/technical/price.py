"""
价格动量类因子
"""
import pandas as pd
import numpy as np


def calculate_price_momentum(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算多周期价格动量
    """
    df = df.copy()
    
    # 多周期收益率
    df['Return1D'] = df['Close'].pct_change(1) * 100
    df['Return3D'] = df['Close'].pct_change(3) * 100
    df['Return5D'] = df['Close'].pct_change(5) * 100
    df['Return10D'] = df['Close'].pct_change(10) * 100
    df['Return20D'] = df['Close'].pct_change(20) * 100
    
    # 动量强度（20日收益率的Z-Score）
    df['MomentumStrength'] = (
        (df['Return20D'] - df['Return20D'].rolling(60).mean()) /
        df['Return20D'].rolling(60).std()
    )
    
    # 加速度（动量的变化率）
    df['MomentumAccel'] = df['Return5D'] - df['Return20D']
    
    return df


def calculate_price_position(df: pd.DataFrame, periods=[20, 60, 120]) -> pd.DataFrame:
    """
    计算价格在历史区间的位置
    
    返回：0-100，越高越接近高点
    """
    df = df.copy()
    
    for period in periods:
        high_n = df['High'].rolling(period).max()
        low_n = df['Low'].rolling(period).min()
        
        df[f'PricePosition{period}D'] = (
            (df['Close'] - low_n) / (high_n - low_n) * 100
        )
    
    return df


def calculate_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算跳空缺口
    """
    df = df.copy()
    
    # 向上跳空
    df['GapUp'] = (df['Low'] > df['High'].shift(1)).astype(int)
    
    # 向下跳空
    df['GapDown'] = (df['High'] < df['Low'].shift(1)).astype(int)
    
    # 累计跳空次数（20日）
    df['GapUpCount20D'] = df['GapUp'].rolling(20).sum()
    df['GapDownCount20D'] = df['GapDown'].rolling(20).sum()
    
    return df