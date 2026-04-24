"""
成交量类指标
"""
import pandas as pd
import numpy as np


def calculate_obv(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算OBV（能量潮）
    
    原理：涨时累加成交量，跌时减去成交量
    用途：判断主力资金流入流出
    """
    df = df.copy()
    
    # 价格变化方向
    price_diff = df['Close'].diff()
    
    # OBV累计
    obv = []
    obv_value = 0
    
    for i, diff in enumerate(price_diff):
        if pd.isna(diff):
            obv.append(0)
        elif diff > 0:
            obv_value += df['Volume'].iloc[i]
            obv.append(obv_value)
        elif diff < 0:
            obv_value -= df['Volume'].iloc[i]
            obv.append(obv_value)
        else:
            obv.append(obv_value)
    
    df['OBV'] = obv
    df['OBV_MA5'] = df['OBV'].rolling(5).mean()
    df['OBV_MA10'] = df['OBV'].rolling(10).mean()
    
    return df


def calculate_vwap(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """
    计算VWAP（成交量加权平均价）
    
    用途：判断价格是否偏离成交量中心
    """
    df = df.copy()
    
    # 典型价格
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    
    # VWAP
    df[f'VWAP{period}'] = (
        (typical_price * df['Volume']).rolling(period).sum() /
        df['Volume'].rolling(period).sum()
    )
    
    return df


def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    计算MFI（资金流量指标）
    
    原理：类似RSI，但考虑成交量
    范围：0-100
    用途：超买超卖 + 背离判断
    """
    df = df.copy()
    
    # 典型价格
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    
    # 资金流量
    money_flow = typical_price * df['Volume']
    
    # 价格变化
    price_diff = typical_price.diff()
    
    # 正负资金流
    positive_flow = money_flow.where(price_diff > 0, 0).rolling(period).sum()
    negative_flow = money_flow.where(price_diff < 0, 0).rolling(period).sum()
    
    # MFI
    mfi_ratio = positive_flow / negative_flow
    df['MFI'] = 100 - (100 / (1 + mfi_ratio))
    
    return df