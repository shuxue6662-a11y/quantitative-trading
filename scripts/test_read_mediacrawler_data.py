"""
测试读取MediaCrawler爬取的数据
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.sentiment.crawler.media_crawler_wrapper import MediaCrawlerWrapper
from src.utils.logger import logger


def main():
    """测试主函数"""
    print("="*60)
    print("测试读取MediaCrawler数据")
    print("="*60)
    
    # 创建读取器
    wrapper = MediaCrawlerWrapper()
    
    # 测试读取
    stock_name = "贵州茅台"
    
    print(f"\n读取 {stock_name} 数据...")
    results = wrapper.crawl_weibo_stock('600519', stock_name, limit=20)
    
    print(f"\n{'='*60}")
    print(f"读取结果")
    print(f"{'='*60}")
    print(f"总数: {len(results)} 条")
    
    if results:
        print(f"\n前5条数据:")
        for i, item in enumerate(results[:5], 1):
            print(f"\n{i}. 【{item['author']}】")
            print(f"   文本: {item['text'][:50]}...")
            print(f"   点赞: {item['likes']} | 评论: {item['comments']} | 时间: {item['publish_time']}")
        
        # 数据类型统计
        is_real = not any('模拟用户' in str(item.get('author', '')) for item in results)
        data_type = '真实数据' if is_real else '模拟数据'
        
        print(f"\n{'='*60}")
        print(f"数据类型: {data_type}")
        print(f"{'='*60}")
        
    else:
        print("❌ 未读取到数据")
    
    print("\n✅ 测试完成！")


if __name__ == '__main__':
    main()