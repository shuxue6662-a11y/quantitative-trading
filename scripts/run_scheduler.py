"""
启动定时任务调度器
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import QuantSystem
from src.scheduler.daily_scheduler import DailyScheduler


def main():
    """主函数"""
    # 创建系统
    system = QuantSystem()
    
    # 创建调度器
    scheduler = DailyScheduler(system)
    
    # 运行
    scheduler.run()


if __name__ == '__main__':
    main()