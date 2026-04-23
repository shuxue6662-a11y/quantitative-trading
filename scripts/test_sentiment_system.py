"""
测试舆情系统完整流程
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.sentiment.storage.sentiment_db import SentimentDatabase
from src.data.sentiment.crawler.media_crawler_wrapper import MediaCrawlerWrapper
from src.llm.services.sentiment_analyzer import SentimentAnalyzer
from src.llm.core.ollama_client import OllamaClient
from src.factors.alternative.sentiment_factor import SentimentFactor
from src.utils.logger import logger
from src.utils.config_loader import config_loader


def test_ollama_connection():
    """测试Ollama连接"""
    print("\n" + "="*60)
    print("步骤1: 测试Ollama连接")
    print("="*60)
    
    client = OllamaClient()
    
    if not client.check_health():
        print("❌ Ollama服务未启动！")
        print("\n请先启动Ollama:")
        print("  - Windows: 确保Ollama Desktop正在运行")
        print("  - 或在终端运行: ollama serve")
        return False
    
    print("✅ Ollama服务正常")
    
    # 从配置文件获取模型名称
    config = config_loader.load('llm_config')
    model_name = config['ollama']['models']['sentiment_analyzer']['name']
    
    # 测试生成
    print(f"\n测试文本生成（模型: {model_name}）...")
    response = client.generate(
        model=model_name,  # 使用配置文件中的模型
        prompt="请用一句话介绍量化交易",
        temperature=0.7,
        max_tokens=100
    )
    
    if response:
        print(f"✅ 生成成功: {response[:100]}...")
        return True
    else:
        print("❌ 生成失败")
        print(f"\n可能原因:")
        print(f"  1. 模型 '{model_name}' 未安装")
        print(f"  2. 运行: ollama pull {model_name}")
        print(f"  3. 或者修改 config/llm_config.yaml 中的模型名称")
        return False


def test_sentiment_analysis():
    """测试情绪分析"""
    print("\n" + "="*60)
    print("步骤2: 测试情绪分析")
    print("="*60)
    
    try:
        analyzer = SentimentAnalyzer()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 测试文本
    test_texts = [
        "贵州茅台今天表现不错，业绩超预期，看好后市发展！",
        "茅台跌了，但我觉得长期还是很有价值的",
        "今天茅台涨停了，太棒了！",
        "茅台估值太高了，风险很大，建议谨慎",
        "持有茅台三年了，收益还不错"
    ]
    
    success_count = 0
    
    for i, text in enumerate(test_texts):
        print(f"\n测试文本 {i+1}: {text}")
        result = analyzer.analyze(text)
        
        if result:
            print(f"  ✅ 情绪分数: {result['sentiment_score']:.2f}")
            print(f"  置信度: {result['confidence']:.2f}")
            print(f"  关键词: {result['keywords']}")
            print(f"  理由: {result.get('reason', '')}")
            success_count += 1
        else:
            print("  ❌ 分析失败")
    
    print(f"\n成功率: {success_count}/{len(test_texts)}")
    
    if success_count > 0:
        print("✅ 情绪分析测试完成")
    else:
        print("❌ 所有分析均失败，请检查模型配置")


def test_full_pipeline():
    """测试完整流程"""
    print("\n" + "="*60)
    print("步骤3: 测试完整舆情分析流程")
    print("="*60)
    
    stock_code = '600519'
    stock_name = '贵州茅台'
    
    # 初始化组件
    try:
        db = SentimentDatabase()
        crawler = MediaCrawlerWrapper()
        analyzer = SentimentAnalyzer()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 1. 爬取数据（模拟）
    print(f"\n1. 爬取 {stock_name} 舆情数据...")
    texts = crawler.crawl_weibo_stock(stock_code, stock_name, limit=10)  # 减少到10条测试
    print(f"  获取 {len(texts)} 条数据")
    
    # 2. 保存原始文本
    print("\n2. 保存原始文本到数据库...")
    text_ids = []
    for item in texts:
        text_id = db.save_text(
            stock_code=stock_code,
            stock_name=stock_name,
            text=item['text'],
            platform=item['platform'],
            author=item['author'],
            followers=item['followers'],
            likes=item['likes'],
            comments=item['comments'],
            shares=item['shares'],
            publish_time=item['publish_time'],
            url=item['url']
        )
        if text_id:
            text_ids.append(text_id)
    
    print(f"  保存 {len(text_ids)} 条新文本")
    
    if not text_ids:
        print("  ⚠️ 没有新文本需要分析（可能已存在）")
        # 获取已有的未分析文本
        existing_texts = db.get_texts_for_analysis(stock_code, limit=10, analyzed=False)
        if existing_texts:
            print(f"  使用已有的 {len(existing_texts)} 条未分析文本")
            text_ids = [t['id'] for t in existing_texts]
            texts = existing_texts
        else:
            print("  ℹ️ 数据库中所有文本已分析，跳到查询结果")
            # 直接跳到查询
            factor_calc = SentimentFactor()
            sentiment_info = factor_calc.get_latest_sentiment(stock_code)
            
            print(f"\n{'='*60}")
            print(f"📊 {stock_name} 最新情绪分析结果（历史数据）")
            print(f"{'='*60}")
            print(f"情绪分数: {sentiment_info['sentiment']:.2f} (0-1，越高越乐观)")
            print(f"情绪趋势: {sentiment_info['trend']}")
            print(f"讨论热度: {sentiment_info['heat']}")
            print(f"{'='*60}")
            
            print("\n✅ 使用历史数据测试完成")
            return
    
    # 3. LLM情绪分析
    print("\n3. LLM情绪分析...")
    analysis_success = 0
    
    for i, (text_id, item) in enumerate(zip(text_ids, texts)):
        # 获取文本内容
        if isinstance(item, dict):
            text_content = item.get('text', '')
        else:
            text_content = item
        
        print(f"  分析 {i+1}/{len(text_ids)}: {text_content[:30]}...")
        
        try:
            result = analyzer.analyze(text_content)
            
            if result:
                db.save_sentiment(
                    text_id=text_id,
                    stock_code=stock_code,
                    sentiment_score=result['sentiment_score'],
                    confidence=result['confidence'],
                    keywords=result['keywords']
                )
                analysis_success += 1
                print(f"    ✅ 分数: {result['sentiment_score']:.2f}")
            else:
                print(f"    ❌ 分析失败")
        except Exception as e:
            print(f"    ❌ 错误: {e}")
    
    print(f"\n  分析成功: {analysis_success}/{len(text_ids)}")
    
    if analysis_success == 0:
        print("  ❌ 所有分析均失败")
        return
    
    # 4. 计算每日情绪
    print("\n4. 计算每日情绪汇总...")
    today = datetime.now().date()
    try:
        db.calculate_daily_sentiment(stock_code, today)
        print("  ✅ 计算完成")
    except Exception as e:
        print(f"  ❌ 计算失败: {e}")
        return
    
    # 5. 计算情绪因子
    print("\n5. 计算情绪因子...")
    try:
        factor_calc = SentimentFactor()
        sentiment_info = factor_calc.get_latest_sentiment(stock_code)
        
        print(f"\n{'='*60}")
        print(f"📊 {stock_name} 最新情绪分析结果")
        print(f"{'='*60}")
        print(f"情绪分数: {sentiment_info['sentiment']:.2f} (0-1，越高越乐观)")
        print(f"情绪趋势: {sentiment_info['trend']}")
        print(f"讨论热度: {sentiment_info['heat']}")
        print(f"{'='*60}")
        
        print("\n✅ 完整流程测试成功！")
        
    except Exception as e:
        print(f"  ❌ 计算因子失败: {e}")


def main():
    """主函数"""
    print("="*60)
    print("🧪 舆情系统测试")
    print("="*60)
    
    # 测试Ollama
    if not test_ollama_connection():
        print("\n⚠️ Ollama测试失败，请先运行: python scripts/check_ollama.py")
        print("   检查环境配置")
        return
    
    # 测试情绪分析
    test_sentiment_analysis()
    
    # 测试完整流程
    test_full_pipeline()
    
    print("\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60)


if __name__ == '__main__':
    main()