"""
测试数据获取功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.market.fetchers import AKShareFetcher
from src.data.market.storage.market_db import MarketDatabase
from src.factors.technical import (
    calculate_ma, calculate_macd, calculate_rsi,
    calculate_bollinger_bands, calculate_atr
)
from src.utils.logger import logger


def main():
    """测试主函数"""
    print("="*60)
    print("测试数据获取和存储")
    print("="*60)
    
    # 测试股票
    test_stocks = [
        ('600519', '贵州茅台'),
        ('000858', '五粮液'),
    ]
    
    # 初始化
    fetcher = AKShareFetcher()
    db = MarketDatabase()
    
    for code, name in test_stocks:
        print(f"\n{'='*60}")
        print(f"正在处理: {name}({code})")
        print(f"{'='*60}")
        
        # 1. 获取数据
        df = fetcher.get_stock_daily(code)
        if df is None:
            logger.error(f"获取 {code} 数据失败")
            continue
        
        # 2. 计算指标
        df = calculate_ma(df)
        df = calculate_macd(df)
        df = calculate_rsi(df)
        df = calculate_bollinger_bands(df)
        df = calculate_atr(df)
        
        # 3. 保存到数据库
        db.save_daily_data(df, code, name)
        db.save_indicators(df, code)
        db.save_stock_info(code, name)
        
        # 4. 验证读取
        saved_df = db.get_daily_data(code)
        print(f"\n最新5条数据:")
        print(saved_df.tail())
        
        logger.info(f"✓ {name} 处理完成")
    
    print("\n✅ 测试完成！")


if __name__ == '__main__':
    main()