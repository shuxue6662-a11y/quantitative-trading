"""
初始化数据库脚本
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.market.storage.market_db import MarketDatabase
from src.utils.logger import logger


def main():
    """主函数"""
    print("="*60)
    print("初始化数据库")
    print("="*60)
    
    try:
        # 创建市场数据库
        market_db = MarketDatabase()
        logger.info("✓ 市场数据库创建成功")
        
        # TODO: 创建其他数据库
        # sentiment_db = SentimentDatabase()
        # factor_db = FactorDatabase()
        
        print("\n✅ 数据库初始化完成！")
        
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        raise


if __name__ == '__main__':
    main()