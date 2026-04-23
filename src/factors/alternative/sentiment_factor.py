"""
情绪因子
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data.sentiment.storage.sentiment_db import SentimentDatabase
from src.utils.logger import logger


class SentimentFactor:
    """情绪因子计算"""
    
    def __init__(self):
        """初始化"""
        self.db = SentimentDatabase()
    
    def calculate(self, stock_code: str, days: int = 30) -> pd.DataFrame:
        """
        计算情绪因子
        
        Args:
            stock_code: 股票代码
            days: 计算天数
            
        Returns:
            DataFrame，包含情绪因子列
        """
        # 获取每日情绪数据
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        df = self.db.get_daily_sentiment(stock_code, start_date, end_date)
        
        if df.empty:
            logger.warning(f"{stock_code} 无情绪数据")
            return pd.DataFrame()
        
        # 计算因子
        df = self._calculate_factors(df)
        
        return df
    
    def _calculate_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算具体因子"""
        df = df.copy()
        
        # 因子1: 情绪分数
        df['Sentiment'] = df['AvgSentiment']
        
        # 因子2: 情绪变化率（3日）
        df['SentimentChange3D'] = df['AvgSentiment'].pct_change(3) * 100
        
        # 因子3: 情绪分歧度（标准差）
        df['SentimentDivergence'] = df['SentimentStd']
        
        # 因子4: 情绪趋势（5日均线斜率）
        df['SentimentTrend'] = df['AvgSentiment'].rolling(5).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 5 else 0
        )
        
        # 因子5: 热度指数（标准化）
        df['HeatIndexNorm'] = (
            (df['HeatIndex'] - df['HeatIndex'].rolling(20).mean()) /
            df['HeatIndex'].rolling(20).std()
        )
        
        # 因子6: 正负比（正面占比 - 负面占比）
        df['SentimentBalance'] = df['PositiveRatio'] - df['NegativeRatio']
        
        return df
    
    def get_latest_sentiment(self, stock_code: str) -> dict:
        """
        获取最新情绪指标
        
        Returns:
            {
                'sentiment': float,
                'trend': str,
                'heat': str
            }
        """
        df = self.calculate(stock_code, days=7)
        
        if df.empty:
            return {
                'sentiment': 0.5,
                'trend': 'unknown',
                'heat': 'low'
            }
        
        latest = df.iloc[-1]
        
        # 判断趋势
        if latest['SentimentChange3D'] > 5:
            trend = 'rising'
        elif latest['SentimentChange3D'] < -5:
            trend = 'falling'
        else:
            trend = 'stable'
        
        # 判断热度
        if latest['HeatIndexNorm'] > 1:
            heat = 'high'
        elif latest['HeatIndexNorm'] < -1:
            heat = 'low'
        else:
            heat = 'medium'
        
        return {
            'sentiment': latest['Sentiment'],
            'trend': trend,
            'heat': heat
        }