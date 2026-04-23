"""
定时任务调度器
"""
import schedule
import time
from datetime import datetime

from src.utils.logger import logger
from src.utils.config_loader import config_loader


class DailyScheduler:
    """每日定时任务"""
    
    def __init__(self, system):
        """
        初始化
        
        Args:
            system: QuantSystem实例
        """
        self.system = system
        
        # 加载配置
        config = config_loader.load('base_config')
        self.schedule_config = config['schedule']
    
    def setup_jobs(self):
        """设置定时任务"""
        # 市场数据更新（盘后15:30）
        market_update_time = self.schedule_config.get('market_data_update', '15:30')
        schedule.every().day.at(market_update_time).do(self._job_update_market)
        logger.info(f"定时任务: 市场数据更新 - 每日 {market_update_time}")
        
        # 舆情爬取（晚上19:30）
        sentiment_time = self.schedule_config.get('sentiment_crawl', '19:30')
        schedule.every().day.at(sentiment_time).do(self._job_crawl_sentiment)
        logger.info(f"定时任务: 舆情爬取 - 每日 {sentiment_time}")
        
        # 信号生成（晚上20:30）
        signal_time = self.schedule_config.get('signal_generation', '20:30')
        schedule.every().day.at(signal_time).do(self._job_generate_signals)
        logger.info(f"定时任务: 信号生成 - 每日 {signal_time}")
        
        # 每日报告（晚上21:00）
        report_time = self.schedule_config.get('daily_report', '21:00')
        schedule.every().day.at(report_time).do(self._job_send_report)
        logger.info(f"定时任务: 每日报告 - 每日 {report_time}")
    
    def _job_update_market(self):
        """任务：更新市场数据"""
        logger.info("⏰ 定时任务触发: 更新市场数据")
        try:
            self.system.update_market_data()
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
    
    def _job_crawl_sentiment(self):
        """任务：爬取舆情"""
        logger.info("⏰ 定时任务触发: 爬取舆情")
        try:
            self.system.crawl_sentiment()
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
    
    def _job_generate_signals(self):
        """任务：生成信号"""
        logger.info("⏰ 定时任务触发: 生成信号")
        try:
            self.system.generate_signals()
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
    
    def _job_send_report(self):
        """任务：发送报告"""
        logger.info("⏰ 定时任务触发: 发送每日报告")
        try:
            signals = self.system.generate_signals()
            if signals:
                self.system.send_daily_report(signals)
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
    
    def run(self):
        """启动调度器"""
        logger.info("="*60)
        logger.info("⏰ 定时任务调度器启动")
        logger.info("="*60)
        
        self.setup_jobs()
        
        logger.info("\n等待任务执行...")
        logger.info("按 Ctrl+C 停止\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("\n⏹️ 调度器已停止")