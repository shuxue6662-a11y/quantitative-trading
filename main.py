"""
量化交易系统 - 主程序
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.data.market.fetchers import MultiSourceFetcher
from src.data.market.storage.market_db import MarketDatabase
from src.data.sentiment.crawler.media_crawler_wrapper import MediaCrawlerWrapper
from src.data.sentiment.storage.sentiment_db import SentimentDatabase
from src.llm.services.sentiment_analyzer import SentimentAnalyzer
from src.strategy.signal_generator import SignalGenerator
from src.notification.email_sender import EmailSender
from src.notification.report_generator import ReportGenerator
from src.factors.technical import (
    calculate_ma, calculate_macd, calculate_rsi,
    calculate_bollinger_bands, calculate_atr
)
from src.utils.logger import logger
from src.utils.config_loader import config_loader


class QuantSystem:
    """量化交易系统主类"""
    
    def __init__(self):
        """初始化系统"""
        logger.info("="*60)
        logger.info("🚀 量化交易系统启动")
        logger.info("="*60)
        
        # 初始化组件
        self.market_fetcher = MultiSourceFetcher()
        self.market_db = MarketDatabase()
        self.sentiment_db = SentimentDatabase()
        self.crawler = MediaCrawlerWrapper()
        self.analyzer = SentimentAnalyzer()
        self.signal_gen = SignalGenerator()
        self.report_gen = ReportGenerator()
        self.email_sender = EmailSender()
        
        # 股票池
        self.stock_pool = self._load_stock_pool()
        
        logger.info(f"股票池: {len(self.stock_pool)} 只")
    
    def _load_stock_pool(self):
        """从配置文件加载股票池"""
        try:
            stock_config = config_loader.load('stock_pool')
            custom_stocks = stock_config.get('custom_stocks', [])
            
            if not custom_stocks:
                logger.warning("stock_pool.yaml 中未配置股票，使用默认股票池")
                return [
                    ('600519', '贵州茅台'),
                    ('000858', '五粮液'),
                ]
            
            # 转换为 (code, name) 元组列表
            stock_list = []
            for stock in custom_stocks:
                code = stock.get('code', '').strip()
                name = stock.get('name', '').strip()
                
                if code and name:
                    stock_list.append((code, name))
                else:
                    logger.warning(f"跳过无效股票配置: {stock}")
            
            logger.info(f"从配置文件加载 {len(stock_list)} 只股票")
            return stock_list
            
        except Exception as e:
            logger.error(f"加载股票池配置失败: {e}")
            logger.info("使用默认股票池")
            return [
                ('600519', '贵州茅台'),
                ('000858', '五粮液'),
            ]
    
    def update_market_data(self):
        """更新市场数据"""
        logger.info("📊 更新市场数据...")
        
        for code, name in self.stock_pool:
            logger.info(f"  处理 {name}({code})")
            
            try:
                # 获取数据
                df = self.market_fetcher.get_stock_daily(code)
                
                if df is None or df.empty:
                    logger.warning(f"  {name} 数据为空，跳过")
                    continue
                
                # 计算指标
                df = calculate_ma(df)
                df = calculate_macd(df)
                df = calculate_rsi(df)
                df = calculate_bollinger_bands(df)
                df = calculate_atr(df)
                
                # 保存
                self.market_db.save_daily_data(df, code, name)
                self.market_db.save_indicators(df, code)
                self.market_db.save_stock_info(code, name)
                
                logger.info(f"  ✅ {name} 更新成功 ({len(df)} 条)")
                
            except Exception as e:
                logger.error(f"  ❌ {name} 更新失败: {e}")
        
        logger.info("市场数据更新完成")
    
    def crawl_sentiment(self):
        """爬取舆情数据"""
        logger.info("🕷️ 爬取舆情数据...")
        
        for code, name in self.stock_pool:
            logger.info(f"  爬取 {name}({code})")
            
            try:
                # 爬取（当前是模拟数据）
                texts = self.crawler.crawl_weibo_stock(code, name, limit=20)
                
                # 保存原始文本
                text_ids = []
                for item in texts:
                    text_id = self.sentiment_db.save_text(
                        stock_code=code,
                        stock_name=name,
                        text=item['text'],
                        platform=item['platform'],
                        author=item.get('author', ''),
                        followers=item.get('followers', 0),
                        likes=item.get('likes', 0),
                        comments=item.get('comments', 0),
                        shares=item.get('shares', 0),
                        publish_time=item.get('publish_time'),
                        url=item.get('url', '')
                    )
                    if text_id:
                        text_ids.append((text_id, item['text']))
                
                # LLM分析
                for text_id, text_content in text_ids:
                    result = self.analyzer.analyze(text_content)
                    if result:
                        self.sentiment_db.save_sentiment(
                            text_id=text_id,
                            stock_code=code,
                            sentiment_score=result['sentiment_score'],
                            confidence=result['confidence'],
                            keywords=result['keywords']
                        )
                
                # 计算每日汇总
                today = datetime.now().date()
                self.sentiment_db.calculate_daily_sentiment(code, today)
                
                logger.info(f"  ✅ {name} 舆情分析完成")
                
            except Exception as e:
                logger.error(f"  ❌ {name} 舆情分析失败: {e}")
        
        logger.info("舆情数据爬取完成")
    
    def generate_signals(self):
        """生成交易信号"""
        logger.info("📈 生成交易信号...")
        
        signals = []
        
        for code, name in self.stock_pool:
            try:
                signal = self.signal_gen.analyze_stock(code, name)
                if signal:
                    signals.append(signal)
                    logger.info(
                        f"  {name}: {signal['action']} "
                        f"(评分 {signal['total_score']:.0f}/100)"
                    )
            except Exception as e:
                logger.error(f"  ❌ {name} 分析失败: {e}")
        
        logger.info(f"信号生成完成: 共 {len(signals)} 只")
        
        return signals
    
    def send_daily_report(self, signals):
        """发送每日报告"""
        logger.info("📧 发送每日报告...")
        
        try:
            # 生成报告
            html = self.report_gen.generate_daily_report(signals)
            
            # 保存到文件
            output_path = Path('data/exports/daily_report.html')
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            logger.info(f"  报告已保存: {output_path}")
            
            # 发送邮件
            subject = f"📊 量化交易日报 - {datetime.now().strftime('%Y-%m-%d')}"
            
            success = self.email_sender.send_html_email(
                subject=subject,
                html_content=html
            )
            
            if success:
                logger.info("  ✅ 邮件发送成功")
            else:
                logger.error("  ❌ 邮件发送失败")
            
        except Exception as e:
            logger.error(f"发送报告失败: {e}")
    
    def run_daily_workflow(self):
        """每日完整流程"""
        logger.info("\n" + "="*60)
        logger.info("🔄 执行每日工作流")
        logger.info("="*60)
        
        start_time = datetime.now()
        
        # 1. 更新市场数据
        self.update_market_data()
        
        # 2. 爬取舆情
        self.crawl_sentiment()
        
        # 3. 生成信号
        signals = self.generate_signals()
        
        # 4. 发送报告
        if signals:
            self.send_daily_report(signals)
        else:
            logger.warning("无信号数据，跳过报告发送")
        
        # 完成
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("="*60)
        logger.info(f"✅ 每日工作流完成！耗时 {elapsed:.1f} 秒")
        logger.info("="*60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='量化交易系统')
    parser.add_argument(
        '--mode',
        type=str,
        choices=['update', 'crawl', 'signal', 'report', 'full'],
        default='full',
        help='运行模式'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='调试模式'
    )
    
    args = parser.parse_args()
    
    # 创建系统实例
    system = QuantSystem()
    
    # 根据模式执行
    if args.mode == 'update':
        system.update_market_data()
        
    elif args.mode == 'crawl':
        system.crawl_sentiment()
        
    elif args.mode == 'signal':
        signals = system.generate_signals()
        for s in signals:
            print(f"{s['stock_name']}: {s['action']} ({s['total_score']:.0f}分)")
        
    elif args.mode == 'report':
        signals = system.generate_signals()
        system.send_daily_report(signals)
        
    elif args.mode == 'full':
        system.run_daily_workflow()


if __name__ == '__main__':
    main()