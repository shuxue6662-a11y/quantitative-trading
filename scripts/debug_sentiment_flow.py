"""
诊断情绪分析流程
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.sentiment.storage.sentiment_db import SentimentDatabase
from src.llm.services.sentiment_analyzer import SentimentAnalyzer
from src.utils.logger import logger


def test_llm():
    """测试LLM分析"""
    print("="*60)
    print("测试1: LLM情绪分析")
    print("="*60)
    
    analyzer = SentimentAnalyzer()
    
    test_text = "贵州茅台今天大涨5%，业绩超预期，看好后市！"
    
    result = analyzer.analyze(test_text)
    
    if result:
        print(f"✅ LLM分析成功")
        print(f"   情绪分数: {result['sentiment_score']}")
        print(f"   置信度: {result['confidence']}")
    else:
        print(f"❌ LLM分析失败")
    
    return result is not None


def test_database():
    """测试数据库查询"""
    print("\n" + "="*60)
    print("测试2: 数据库查询")
    print("="*60)
    
    db = SentimentDatabase()
    
    # 尝试查询
    stock_code = '600498'
    today = datetime.now().date()
    
    df = db.get_daily_sentiment(stock_code, today, today)
    
    print(f"查询 {stock_code} 的今日情绪数据:")
    
    if not df.empty:
        print(f"✅ 找到数据: {len(df)} 条")
        print(df)
    else:
        print(f"❌ 无数据")
    
    return not df.empty


def main():
    """主测试"""
    results = []
    
    # 测试LLM
    results.append(('LLM分析', test_llm()))
    
    # 测试数据库
    results.append(('数据库查询', test_database()))
    
    # 汇总
    print("\n" + "="*60)
    print("诊断结果")
    print("="*60)
    
    for name, ok in results:
        status = '✅' if ok else '❌'
        print(f"{status} {name}")
    
    if all(r for _, r in results):
        print("\n✅ 所有组件正常")
    else:
        print("\n❌ 存在问题，需要修复")


if __name__ == '__main__':
    main()