"""
市场数据库操作
"""
import pandas as pd
from datetime import date
from pathlib import Path
from typing import Optional, List
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

from .models import Base, StockDaily, StockInfo, TechnicalIndicator
from src.utils.logger import logger


class MarketDatabase:
    """市场数据库管理"""
    
    def __init__(self, db_path: str = 'database/market_data.db'):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库路径
        """
        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 创建引擎
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        
        # 创建表
        Base.metadata.create_all(self.engine)
        
        # 创建会话工厂
        self.Session = sessionmaker(bind=self.engine)
        
        logger.info(f"数据库初始化完成: {db_path}")
    
    def save_daily_data(self, df: pd.DataFrame, stock_code: str, stock_name: str = ''):
        """
        保存日线数据
        
        Args:
            df: DataFrame，必须包含 Date, Open, High, Low, Close, Volume等列
            stock_code: 股票代码
            stock_name: 股票名称
        """
        session = self.Session()
        
        try:
            for _, row in df.iterrows():
                # 检查是否已存在
                existing = session.query(StockDaily).filter(
                    and_(
                        StockDaily.stock_code == stock_code,
                        StockDaily.trade_date == row['Date']
                    )
                ).first()
                
                if existing:
                    # 更新
                    existing.open = row.get('Open')
                    existing.high = row.get('High')
                    existing.low = row.get('Low')
                    existing.close = row.get('Close')
                    existing.volume = row.get('Volume')
                    existing.amount = row.get('Amount', 0)
                    existing.pct_change = row.get('PctChange', 0)
                else:
                    # 插入新记录
                    record = StockDaily(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        trade_date=row['Date'],
                        open=row.get('Open'),
                        high=row.get('High'),
                        low=row.get('Low'),
                        close=row.get('Close'),
                        volume=row.get('Volume'),
                        amount=row.get('Amount', 0),
                        pct_change=row.get('PctChange', 0)
                    )
                    session.add(record)
            
            session.commit()
            logger.info(f"保存 {stock_code} 数据: {len(df)} 条")
            
        except Exception as e:
            session.rollback()
            logger.error(f"保存数据失败: {e}")
            raise
        finally:
            session.close()
    
    def get_daily_data(
        self, 
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        读取日线数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame
        """
        session = self.Session()
        
        try:
            query = session.query(StockDaily).filter(StockDaily.stock_code == stock_code)
            
            if start_date:
                query = query.filter(StockDaily.trade_date >= start_date)
            if end_date:
                query = query.filter(StockDaily.trade_date <= end_date)
            
            query = query.order_by(StockDaily.trade_date)
            
            records = query.all()
            
            if not records:
                logger.warning(f"未找到 {stock_code} 的数据")
                return pd.DataFrame()
            
            # 转换为DataFrame
            data = []
            for r in records:
                data.append({
                    'Date': r.trade_date,
                    'Open': r.open,
                    'High': r.high,
                    'Low': r.low,
                    'Close': r.close,
                    'Volume': r.volume,
                    'Amount': r.amount,
                    'PctChange': r.pct_change
                })
            
            df = pd.DataFrame(data)
            return df
            
        finally:
            session.close()
    
    def save_stock_info(self, code: str, name: str, **kwargs):
        """保存股票基础信息"""
        session = self.Session()
        
        try:
            existing = session.query(StockInfo).filter(StockInfo.stock_code == code).first()
            
            if existing:
                existing.stock_name = name
                for key, value in kwargs.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                info = StockInfo(stock_code=code, stock_name=name, **kwargs)
                session.add(info)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"保存股票信息失败: {e}")
        finally:
            session.close()
    
    def get_all_stocks(self) -> List[dict]:
        """获取所有股票列表"""
        session = self.Session()
        
        try:
            stocks = session.query(StockInfo).all()
            return [
                {'code': s.stock_code, 'name': s.stock_name}
                for s in stocks
            ]
        finally:
            session.close()
    
    def save_indicators(self, df: pd.DataFrame, stock_code: str):
        """
        保存技术指标数据
        
        Args:
            df: DataFrame，包含技术指标列
            stock_code: 股票代码
        """
        session = self.Session()
        
        try:
            for _, row in df.iterrows():
                existing = session.query(TechnicalIndicator).filter(
                    and_(
                        TechnicalIndicator.stock_code == stock_code,
                        TechnicalIndicator.trade_date == row['Date']
                    )
                ).first()
                
                indicator_data = {
                    'stock_code': stock_code,
                    'trade_date': row['Date'],
                    'ma5': row.get('MA5'),
                    'ma10': row.get('MA10'),
                    'ma20': row.get('MA20'),
                    'ma60': row.get('MA60'),
                    'macd': row.get('MACD'),
                    'macd_signal': row.get('MACD_Signal'),
                    'macd_hist': row.get('MACD_Hist'),
                    'rsi6': row.get('RSI6'),
                    'rsi12': row.get('RSI12'),
                    'bb_upper': row.get('BB_Upper'),
                    'bb_middle': row.get('BB_Middle'),
                    'bb_lower': row.get('BB_Lower'),
                    'atr': row.get('ATR')
                }
                
                if existing:
                    for key, value in indicator_data.items():
                        if key not in ['stock_code', 'trade_date']:
                            setattr(existing, key, value)
                else:
                    indicator = TechnicalIndicator(**indicator_data)
                    session.add(indicator)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"保存指标失败: {e}")
            raise
        finally:
            session.close()