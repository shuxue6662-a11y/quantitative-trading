"""
测试多数据源切换
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.market.fetchers import MultiSourceFetcher
from src.utils.logger import logger


def main():
    """测试主函数"""
    print("="*60)
    print("测试多数据源智能切换")
    print("="*60)
    
    # 创建多源获取器
    fetcher = MultiSourceFetcher()
    
    # 显示配置
    health = fetcher.get_health_report()
    print(f"\n可用数据源: {', '.join(health['sources'])}")
    print(f"优先级: {' > '.join(health['priority'])}")
    
    # 测试股票
    test_stocks = [
        '600519',  # 贵州茅台
        '000858',  # 五粮液
        '600887',  # 伊利股份
    ]
    
    results = []
    
    for code in test_stocks:
        print(f"\n{'='*60}")
        print(f"测试: {code}")
        print(f"{'='*60}")
        
        df = fetcher.get_stock_daily(code)
        
        if df is not None:
            source = df['DataSource'].iloc[0]
            print(f"✅ 成功！数据源: {source}, 数据量: {len(df)} 条")
            print(f"   日期范围: {df['Date'].min()} ~ {df['Date'].max()}")
            print(f"   最新收盘价: {df['Close'].iloc[-1]:.2f}")
            results.append((code, source, len(df)))
        else:
            print(f"❌ 失败！所有数据源均无法获取")
            results.append((code, 'FAILED', 0))
    
    # 汇总
    print(f"\n{'='*60}")
    print("测试汇总")
    print(f"{'='*60}")
    
    for code, source, count in results:
        status = '✅' if count > 0 else '❌'
        print(f"{status} {code}: {source} ({count} 条)")
    
    # 健康报告
    health = fetcher.get_health_report()
    print(f"\n数据源健康状态:")
    for source, healthy in health['health'].items():
        status = '🟢' if healthy else '🔴'
        failures = health['failures'][source]
        print(f"  {status} {source}: 失败次数 {failures}")
    
    print(f"\n{'='*60}")
    print("✅ 测试完成！")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()