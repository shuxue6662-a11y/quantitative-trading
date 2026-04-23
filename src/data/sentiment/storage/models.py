"""
舆情数据模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SentimentText(Base):
    """原始舆情文本数据"""
    __tablename__ = 'sentiment_text'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, comment='股票代码')
    stock_name = Column(String(50), comment='股票名称')
    
    # 文本内容
    text = Column(Text, nullable=False, comment='原始文本')
    source_platform = Column(String(20), comment='来源平台（weibo/tieba/xueqiu）')
    source_url = Column(String(500), comment='来源URL')
    
    # 作者信息
    author = Column(String(100), comment='作者')
    author_followers = Column(Integer, comment='作者粉丝数')
    
    # 互动数据
    likes = Column(Integer, default=0, comment='点赞数')
    comments = Column(Integer, default=0, comment='评论数')
    shares = Column(Integer, default=0, comment='转发数')
    
    # 时间
    publish_time = Column(DateTime, comment='发布时间')
    crawl_time = Column(DateTime, default=datetime.now, comment='爬取时间')
    
    # 去重标识
    content_hash = Column(String(64), unique=True, comment='内容哈希（用于去重）')
    
    # 索引
    __table_args__ = (
        Index('idx_stock_time', 'stock_code', 'publish_time'),
        Index('idx_platform', 'source_platform'),
        Index('idx_crawl_time', 'crawl_time'),
    )


class SentimentScore(Base):
    """情绪分析结果"""
    __tablename__ = 'sentiment_score'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    text_id = Column(Integer, nullable=False, comment='关联的文本ID')
    stock_code = Column(String(10), nullable=False, comment='股票代码')
    
    # 情绪分数
    sentiment_score = Column(Float, comment='情绪分数（0-1，0极度悲观，1极度乐观）')
    confidence = Column(Float, comment='置信度（0-1）')
    
    # 分类结果
    sentiment_label = Column(String(20), comment='情绪标签（positive/neutral/negative）')
    
    # 关键词
    keywords = Column(Text, comment='关键词（JSON数组）')
    
    # 分析模型
    model_name = Column(String(50), comment='使用的模型')
    analysis_time = Column(DateTime, default=datetime.now, comment='分析时间')
    
    # 索引
    __table_args__ = (
        Index('idx_sentiment_stock', 'stock_code', 'analysis_time'),
    )


class DailySentiment(Base):
    """每日情绪汇总"""
    __tablename__ = 'daily_sentiment'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, comment='股票代码')
    trade_date = Column(DateTime, nullable=False, comment='日期')
    
    # 汇总指标
    avg_sentiment = Column(Float, comment='平均情绪分数')
    sentiment_std = Column(Float, comment='情绪标准差（分歧度）')
    positive_ratio = Column(Float, comment='正面占比')
    negative_ratio = Column(Float, comment='负面占比')
    
    # 数量统计
    total_count = Column(Integer, comment='总文本数')
    high_confidence_count = Column(Integer, comment='高置信度文本数')
    
    # 热度指标
    total_likes = Column(Integer, comment='总点赞数')
    total_comments = Column(Integer, comment='总评论数')
    heat_index = Column(Float, comment='热度指数')
    
    # 索引
    __table_args__ = (
        Index('idx_daily_stock_date', 'stock_code', 'trade_date', unique=True),
    )