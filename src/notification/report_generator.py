"""
报告生成器
"""
from typing import List, Dict
from datetime import datetime
from pathlib import Path
from jinja2 import Template

from src.utils.logger import logger


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        """初始化"""
        self.template_dir = Path('src/notification/templates')
    
    def generate_daily_report(self, signals: List[Dict]) -> str:
        """
        生成每日报告HTML
        
        Args:
            signals: 信号列表
            
        Returns:
            HTML内容
        """
        # 分类信号
        strong_buy = [s for s in signals if s['action'] == 'STRONG_BUY']
        buy = [s for s in signals if s['action'] == 'BUY']
        hold = [s for s in signals if s['action'] == 'HOLD']
        avoid = [s for s in signals if s['action'] == 'AVOID']
        
        # 排序（按评分）
        strong_buy.sort(key=lambda x: x['total_score'], reverse=True)
        buy.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 加载模板
        template_path = self.template_dir / 'daily_report.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            template = Template(f.read())
        
        # 渲染
        html = template.render(
            date=datetime.now().strftime('%Y年%m月%d日'),
            total_stocks=len(signals),
            buy_count=len(strong_buy) + len(buy),
            hold_count=len(hold),
            avoid_count=len(avoid),
            strong_buy_stocks=strong_buy,
            buy_stocks=buy,
            hold_stocks=hold,
            avoid_stocks=avoid
        )
        
        logger.info(f"报告生成完成: 买入{len(strong_buy)+len(buy)}只")
        
        return html