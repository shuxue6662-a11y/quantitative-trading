"""
舆情数据库操作
"""
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
import hashlib
import json

from .models import Base, SentimentText, SentimentScore, DailySentiment
from src.utils.logger import logger


class SentimentDatabase:
    """舆情数据库管理"""
    
    def __init__(self, db_path: str = 'database/sentiment_data.db'):
        """初始化数据库"""
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        logger.info(f"舆情数据库初始化完成: {db_path}")
    
    def _generate_hash(self, text: str) -> str:
        """生成文本哈希值（用于去重）"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def save_text(
        self,
        stock_code: str,
        stock_name: str,
        text: str,
        platform: str,
        **kwargs
    ) -> Optional[int]:
        """
        保存原始文本
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            text: 文本内容
            platform: 平台名称
            **kwargs: 其他字段
            
        Returns:
            文本ID，如果重复则返回None
        """
        session = self.Session()
        
        try:
            # 生成哈希
            content_hash = self._generate_hash(text)
            
            # 检查是否已存在
            existing = session.query(SentimentText).filter(
                SentimentText.content_hash == content_hash
            ).first()
            
            if existing:
                logger.debug(f"文本已存在，跳过: {text[:50]}...")
                return None
            
            # 创建新记录
            record = SentimentText(
                stock_code=stock_code,
                stock_name=stock_name,
                text=text,
                source_platform=platform,
                content_hash=content_hash,
                source_url=kwargs.get('url', ''),
                author=kwargs.get('author', ''),
                author_followers=kwargs.get('followers', 0),
                likes=kwargs.get('likes', 0),
                comments=kwargs.get('comments', 0),
                shares=kwargs.get('shares', 0),
                publish_time=kwargs.get('publish_time', datetime.now())
            )
            
            session.add(record)
            session.commit()
            
            text_id = record.id
            logger.debug(f"保存文本 ID={text_id}: {text[:50]}...")
            return text_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"保存文本失败: {e}")
            return None
        finally:
            session.close()
    
    def save_sentiment(
        self,
        text_id: int,
        stock_code: str,
        sentiment_score: float,
        confidence: float,
        keywords: List[str],
        model_name: str = 'qwen2.5:14b'
    ):
        """
        保存情绪分析结果
        
        Args:
            text_id: 文本ID
            stock_code: 股票代码
            sentiment_score: 情绪分数（0-1）
            confidence: 置信度
            keywords: 关键词列表
            model_name: 模型名称
        """
        session = self.Session()
        
        try:
            # 判断情绪标签
            if sentiment_score > 0.6:
                label = 'positive'
            elif sentiment_score < 0.4:
                label = 'negative'
            else:
                label = 'neutral'
            
            record = SentimentScore(
                text_id=text_id,
                stock_code=stock_code,
                sentiment_score=sentiment_score,
                confidence=confidence,
                sentiment_label=label,
                keywords=json.dumps(keywords, ensure_ascii=False),
                model_name=model_name
            )
            
            session.add(record)
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"保存情绪分数失败: {e}")
            raise
        finally:
            session.close()
    
    def get_texts_for_analysis(
        self,
        stock_code: Optional[str] = None,
        limit: int = 100,
        analyzed: bool = False
    ) -> List[dict]:
        """
        获取待分析的文本
        
        Args:
            stock_code: 股票代码，None表示所有
            limit: 最大数量
            analyzed: 是否只获取已分析的
            
        Returns:
            文本列表
        """
        session = self.Session()
        
        try:
            query = session.query(SentimentText)
            
            if stock_code:
                query = query.filter(SentimentText.stock_code == stock_code)
            
            if not analyzed:
                # 只获取未分析的（left join为空）
                analyzed_ids = session.query(SentimentScore.text_id).distinct()
                query = query.filter(~SentimentText.id.in_(analyzed_ids))
            
            query = query.order_by(SentimentText.crawl_time.desc()).limit(limit)
            
            records = query.all()
            
            return [
                {
                    'id': r.id,
                    'stock_code': r.stock_code,
                    'text': r.text,
                    'platform': r.source_platform,
                    'publish_time': r.publish_time
                }
                for r in records
            ]
            
        finally:
            session.close()
    
    def calculate_daily_sentiment(self, stock_code: str, trade_date: date):
        """
        计算并保存每日情绪汇总
        
        Args:
            stock_code: 股票代码
            trade_date: 日期
        """
        session = self.Session()
        
        try:
            # 获取当天的情绪数据
            start_time = datetime.combine(trade_date, datetime.min.time())
            end_time = datetime.combine(trade_date, datetime.max.time())
            
            # 联表查询
            results = session.query(
                SentimentScore.sentiment_score,
                SentimentScore.confidence,
                SentimentScore.sentiment_label,
                SentimentText.likes,
                SentimentText.comments
            ).join(
                SentimentText,
                SentimentScore.text_id == SentimentText.id
            ).filter(
                and_(
                    SentimentScore.stock_code == stock_code,
                    SentimentText.publish_time >= start_time,
                    SentimentText.publish_time <= end_time
                )
            ).all()
            
            if not results:
                logger.warning(f"无数据: {stock_code} {trade_date}")
                return
            
            # 计算统计指标
            scores = [r.sentiment_score for r in results]
            confidences = [r.confidence for r in results]
            labels = [r.sentiment_label for r in results]
            
            avg_sentiment = sum(scores) / len(scores)
            sentiment_std = pd.Series(scores).std()
            
            positive_ratio = labels.count('positive') / len(labels)
            negative_ratio = labels.count('negative') / len(labels)
            
            high_confidence_count = sum(1 for c in confidences if c > 0.7)
            
            total_likes = sum(r.likes for r in results)
            total_comments = sum(r.comments for r in results)
            
            # 热度指数（简单加权）
            heat_index = len(results) + total_likes * 0.1 + total_comments * 0.2
            
            # 保存或更新
            existing = session.query(DailySentiment).filter(
                and_(
                    DailySentiment.stock_code == stock_code,
                    DailySentiment.trade_date == start_time
                )
            ).first()
            
            if existing:
                existing.avg_sentiment = avg_sentiment
                existing.sentiment_std = sentiment_std
                existing.positive_ratio = positive_ratio
                existing.negative_ratio = negative_ratio
                existing.total_count = len(results)
                existing.high_confidence_count = high_confidence_count
                existing.total_likes = total_likes
                existing.total_comments = total_comments
                existing.heat_index = heat_index
            else:
                daily = DailySentiment(
                    stock_code=stock_code,
                    trade_date=start_time,
                    avg_sentiment=avg_sentiment,
                    sentiment_std=sentiment_std,
                    positive_ratio=positive_ratio,
                    negative_ratio=negative_ratio,
                    total_count=len(results),
                    high_confidence_count=high_confidence_count,
                    total_likes=total_likes,
                    total_comments=total_comments,
                    heat_index=heat_index
                )
                session.add(daily)
            
            session.commit()
            logger.info(f"保存每日情绪: {stock_code} {trade_date} 平均分={avg_sentiment:.2f}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"计算每日情绪失败: {e}")
            raise
        finally:
            session.close()
    
    def get_daily_sentiment(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """获取每日情绪数据"""
        session = self.Session()
        
        try:
            logger.debug(f"查询数据库: {stock_code}, {start_date} ~ {end_date}")
            
            query = session.query(DailySentiment).filter(
                DailySentiment.stock_code == stock_code
            )
            
            if start_date:
                # 🔥 修复：确保日期类型一致
                query = query.filter(DailySentiment.trade_date >= datetime.combine(start_date, datetime.min.time()))
            if end_date:
                query = query.filter(DailySentiment.trade_date <= datetime.combine(end_date, datetime.max.time()))
            
            query = query.order_by(DailySentiment.trade_date)
            records = query.all()
            
            logger.debug(f"查询结果: {len(records)} 条")  # 添加调试
            
            if not records:
                logger.warning(f"数据库中无 {stock_code} 的情绪数据")
                return pd.DataFrame()
            
            
            data = []
            for r in records:
                data.append({
                    'Date': r.trade_date.date(),
                    'AvgSentiment': r.avg_sentiment,
                    'SentimentStd': r.sentiment_std,
                    'PositiveRatio': r.positive_ratio,
                    'NegativeRatio': r.negative_ratio,
                    'TotalCount': r.total_count,
                    'HeatIndex': r.heat_index
                })
            
            return pd.DataFrame(data)
            
        finally:
            session.close()