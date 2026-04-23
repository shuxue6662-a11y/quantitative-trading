"""
市场数据模型（SQLAlchemy ORM）
"""
from datetime import date
from sqlalchemy import Column, String, Float, Integer, Date, BigInteger, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class StockDaily(Base):
    """股票日线数据"""
    __tablename__ = 'stock_daily'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, comment='股票代码')
    stock_name = Column(String(50), comment='股票名称')
    trade_date = Column(Date, nullable=False, comment='交易日期')
    
    # OHLCV数据
    open = Column(Float, comment='开盘价')
    high = Column(Float, comment='最高价')
    low = Column(Float, comment='最低价')
    close = Column(Float, comment='收盘价')
    volume = Column(BigInteger, comment='成交量')
    amount = Column(Float, comment='成交额')
    
    # 涨跌幅
    pct_change = Column(Float, comment='涨跌幅%')
    
    # 复权因子
    adj_factor = Column(Float, comment='复权因子')
    
    # 索引
    __table_args__ = (
        Index('idx_stock_date', 'stock_code', 'trade_date', unique=True),
        Index('idx_trade_date', 'trade_date'),
    )
    
    def __repr__(self):
        return f"<StockDaily(code={self.stock_code}, date={self.trade_date}, close={self.close})>"


class StockInfo(Base):
    """股票基础信息"""
    __tablename__ = 'stock_info'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), unique=True, nullable=False, comment='股票代码')
    stock_name = Column(String(50), comment='股票名称')
    industry = Column(String(50), comment='所属行业')
    market = Column(String(10), comment='上市板块（SH/SZ）')
    list_date = Column(Date, comment='上市日期')
    
    # 最新数据
    latest_price = Column(Float, comment='最新价')
    market_cap = Column(Float, comment='总市值（亿元）')
    pe_ttm = Column(Float, comment='市盈率TTM')
    pb = Column(Float, comment='市净率')
    
    def __repr__(self):
        return f"<StockInfo(code={self.stock_code}, name={self.stock_name})>"


class TechnicalIndicator(Base):
    """技术指标数据"""
    __tablename__ = 'technical_indicators'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False)
    trade_date = Column(Date, nullable=False)
    
    # 均线
    ma5 = Column(Float, comment='5日均线')
    ma10 = Column(Float, comment='10日均线')
    ma20 = Column(Float, comment='20日均线')
    ma60 = Column(Float, comment='60日均线')
    
    # MACD
    macd = Column(Float, comment='MACD')
    macd_signal = Column(Float, comment='MACD信号线')
    macd_hist = Column(Float, comment='MACD柱状图')
    
    # RSI
    rsi6 = Column(Float, comment='6日RSI')
    rsi12 = Column(Float, comment='12日RSI')
    rsi24 = Column(Float, comment='24日RSI')
    
    # 布林带
    bb_upper = Column(Float, comment='布林上轨')
    bb_middle = Column(Float, comment='布林中轨')
    bb_lower = Column(Float, comment='布林下轨')
    
    # ATR
    atr = Column(Float, comment='平均真实波幅')
    
    # 索引
    __table_args__ = (
        Index('idx_indicator_stock_date', 'stock_code', 'trade_date', unique=True),
    )