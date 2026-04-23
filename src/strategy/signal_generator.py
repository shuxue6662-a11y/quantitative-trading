"""
综合信号生成器
整合技术指标、基本面、情绪因子
"""
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime

from src.data.market.fetchers import AKShareFetcher
from src.data.market.storage.market_db import MarketDatabase
from src.factors.technical import (
    calculate_ma, calculate_macd, calculate_rsi,
    calculate_bollinger_bands, calculate_atr
)
from src.factors.alternative.sentiment_factor import SentimentFactor
from src.utils.logger import logger


class SignalGenerator:
    """综合信号生成器"""
    
    def __init__(self):
        """初始化"""
        self.fetcher = AKShareFetcher()
        self.market_db = MarketDatabase()
        self.sentiment_factor = SentimentFactor()
        
        logger.info("信号生成器初始化完成")
    
    def analyze_stock(self, stock_code: str, stock_name: str) -> Optional[Dict]:
        """
        分析单只股票，生成综合信号
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            
        Returns:
            信号字典
        """
        logger.info(f"分析 {stock_name}({stock_code})")
        
        # 1. 获取市场数据
        df = self.market_db.get_daily_data(stock_code)
        
        if df.empty or len(df) < 60:
            logger.warning(f"{stock_code} 数据不足")
            return None
        
        # 2. 计算技术指标
        df = calculate_ma(df)
        df = calculate_macd(df)
        df = calculate_rsi(df)
        df = calculate_bollinger_bands(df)
        df = calculate_atr(df)
        
        # 3. 获取最新数据
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 4. 计算技术指标评分
        tech_score, tech_signals = self._calculate_tech_score(df, latest, prev)
        
        # 5. 获取情绪因子
        sentiment_info = self.sentiment_factor.get_latest_sentiment(stock_code)
        sentiment_score, sentiment_signals = self._calculate_sentiment_score(sentiment_info)
        
        # 6. 综合评分（技术70% + 情绪30%）
        total_score = tech_score * 0.7 + sentiment_score * 0.3
        
        # 7. 生成信号
        action, reasons, risks = self._generate_signal(
            total_score, tech_signals, sentiment_signals, latest
        )
        
        return {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'date': latest['Date'],
            'price': latest['Close'],
            
            # 评分
            'tech_score': tech_score,
            'sentiment_score': sentiment_score,
            'total_score': total_score,
            
            # 技术指标
            'ma5': latest['MA5'],
            'ma20': latest['MA20'],
            'ma60': latest['MA60'],
            'macd': latest['MACD'],
            'macd_signal': latest['MACD_Signal'],
            'rsi': latest['RSI6'],
            'atr': latest['ATR'],
            
            # 情绪指标
            'sentiment': sentiment_info['sentiment'],
            'sentiment_trend': sentiment_info['trend'],
            'heat': sentiment_info['heat'],
            
            # 决策
            'action': action,
            'reasons': reasons,
            'risks': risks,
            
            # 额外信息
            'tech_signals': tech_signals,
            'sentiment_signals': sentiment_signals
        }
    
    def _calculate_tech_score(
        self, 
        df: pd.DataFrame, 
        latest: pd.Series, 
        prev: pd.Series
    ) -> Tuple[float, list]:
        """
        计算技术指标评分（0-100）
        
        Returns:
            (score, signals)
        """
        score = 0
        signals = []
        
        close = latest['Close']
        ma5 = latest['MA5']
        ma20 = latest['MA20']
        ma60 = latest['MA60']
        macd = latest['MACD']
        macd_signal = latest['MACD_Signal']
        rsi = latest['RSI6']
        
        # 1. 价格位置（30分）
        if close > ma5:
            score += 10
            signals.append("价格>MA5")
        if close > ma20:
            score += 10
            signals.append("价格>MA20")
        if close > ma60:
            score += 10
            signals.append("价格>MA60")
        
        # 2. 均线排列（20分）
        if ma5 > ma20:
            score += 10
            signals.append("MA5>MA20")
        if ma20 > ma60:
            score += 10
            signals.append("MA20>MA60")
        
        # 3. MACD（30分）
        if macd > macd_signal:
            score += 15
            signals.append("MACD多头")
        
        # MACD金叉
        if prev['MACD'] <= prev['MACD_Signal'] and macd > macd_signal:
            score += 15
            signals.append("⭐MACD金叉")
        
        # 4. RSI（20分）
        if 40 < rsi < 70:
            score += 20
            signals.append("RSI健康")
        elif 30 < rsi <= 40:
            score += 10
            signals.append("RSI偏低")
        elif 70 <= rsi < 80:
            score += 10
            signals.append("RSI偏高")
        
        return score, signals
    
    def _calculate_sentiment_score(self, sentiment_info: Dict) -> Tuple[float, list]:
        """
        计算情绪评分（0-100）
        
        Returns:
            (score, signals)
        """
        score = 0
        signals = []
        
        sentiment = sentiment_info['sentiment']
        trend = sentiment_info['trend']
        heat = sentiment_info['heat']
        
        # 1. 情绪分数（60分）
        if sentiment >= 0.7:
            score += 60
            signals.append("情绪乐观")
        elif sentiment >= 0.6:
            score += 40
            signals.append("情绪偏乐观")
        elif sentiment >= 0.4:
            score += 20
            signals.append("情绪中性")
        else:
            score += 0
            signals.append("情绪悲观")
        
        # 2. 情绪趋势（20分）
        if trend == 'rising':
            score += 20
            signals.append("⭐情绪上升")
        elif trend == 'stable':
            score += 10
            signals.append("情绪稳定")
        
        # 3. 讨论热度（20分）
        if heat == 'high':
            score += 20
            signals.append("讨论活跃")
        elif heat == 'medium':
            score += 10
            signals.append("讨论一般")
        
        return score, signals
    
    def _generate_signal(
        self,
        total_score: float,
        tech_signals: list,
        sentiment_signals: list,
        latest: pd.Series
    ) -> Tuple[str, list, list]:
        """
        生成交易信号
        
        Returns:
            (action, reasons, risks)
        """
        rsi = latest['RSI6']
        price = latest['Close']
        ma20 = latest['MA20']
        
        reasons = []
        risks = []
        
        # 决策逻辑
        if total_score >= 70:
            action = "STRONG_BUY"
            reasons.append(f"综合评分 {total_score:.0f}/100，强势信号")
            reasons.extend(tech_signals[:3])  # 前3个技术信号
            reasons.extend(sentiment_signals[:2])  # 前2个情绪信号
            
        elif total_score >= 55:
            action = "BUY"
            reasons.append(f"综合评分 {total_score:.0f}/100，买入信号")
            reasons.extend(tech_signals[:2])
            reasons.extend(sentiment_signals[:1])
            
        elif total_score >= 40:
            action = "HOLD"
            reasons.append(f"综合评分 {total_score:.0f}/100，观望为主")
            
        else:
            action = "AVOID"
            reasons.append(f"综合评分仅 {total_score:.0f}/100，趋势较弱")
        
        # 风险检查
        if rsi > 80:
            risks.append("⚠️ RSI超买，谨防回调")
            if action in ["STRONG_BUY", "BUY"]:
                action = "HOLD"
        
        if price > ma20 * 1.15:
            risks.append("⚠️ 价格远离MA20，追高风险")
        
        if "MACD金叉" in tech_signals and "情绪上升" in sentiment_signals:
            reasons.append("💡 技术+情绪共振，关注度高")
        
        return action, reasons, risks