"""
测试策略信号生成系统
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategy.signal_generator import SignalGenerator
from src.notification.email_sender import EmailSender
from src.notification.report_generator import ReportGenerator
from src.utils.logger import logger


def test_signal_generation():
    """测试信号生成"""
    print("="*60)
    print("测试信号生成")
    print("="*60)
    
    generator = SignalGenerator()
    
    # 测试股票
    test_stocks = [
        ('600519', '贵州茅台'),
        ('000858', '五粮液'),
    ]
    
    signals = []
    
    for code, name in test_stocks:
        print(f"\n分析 {name}({code})...")
        signal = generator.analyze_stock(code, name)
        
        if signal:
            signals.append(signal)
            print(f"  ✅ 综合评分: {signal['total_score']:.0f}/100")
            print(f"  技术评分: {signal['tech_score']:.0f}")
            print(f"  情绪评分: {signal['sentiment_score']:.0f}")
            print(f"  决策: {signal['action']}")
            print(f"  理由: {', '.join(signal['reasons'][:3])}")
        else:
            print(f"  ❌ 分析失败")
    
    return signals


def test_report_generation(signals):
    """测试报告生成"""
    print("\n" + "="*60)
    print("测试报告生成")
    print("="*60)
    
    generator = ReportGenerator()
    
    html = generator.generate_daily_report(signals)
    
    # 保存到文件
    output_path = Path('data/exports/daily_report.html')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 报告已保存: {output_path}")
    print(f"   用浏览器打开查看效果")
    
    return html


def test_email_sending(html):
    """测试邮件发送"""
    print("\n" + "="*60)
    print("测试邮件发送")
    print("="*60)
    
    try:
        sender = EmailSender()
        
        subject = f"📊 量化交易日报 - {Path.cwd().name}"
        
        success = sender.send_html_email(
            subject=subject,
            html_content=html
        )
        
        if success:
            print("✅ 邮件发送成功！")
            print(f"   请检查邮箱: {sender.receiver}")
        else:
            print("❌ 邮件发送失败")
            
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        print("\n请检查:")
        print("  1. config/secrets.yaml 配置是否正确")
        print("  2. QQ邮箱授权码是否正确（不是QQ密码！）")
        print("  3. SMTP设置是否正确")


def main():
    """主函数"""
    print("="*60)
    print("🧪 策略系统测试")
    print("="*60)
    
    # 1. 测试信号生成
    signals = test_signal_generation()
    
    if not signals:
        print("\n❌ 无信号数据，测试终止")
        return
    
    # 2. 测试报告生成
    html = test_report_generation(signals)
    
    # 3. 测试邮件发送
    test_email_sending(html)
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60)


if __name__ == '__main__':
    main()