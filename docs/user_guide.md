# 量化交易系统使用指南

## 🚀 快速开始

### 1. 手动运行完整流程

```powershell
# 执行完整工作流（数据更新+舆情+信号+报告）
python main.py --mode full

2. 分步运行
PowerShell

# 只更新市场数据
python main.py --mode update

# 只爬取舆情
python main.py --mode crawl

# 只生成信号
python main.py --mode signal

# 只发送报告
python main.py --mode report
3. 启动定时任务
PowerShell

# 启动调度器（后台运行）
python scripts/run_scheduler.py
⚙️ 配置说明
股票池配置
编辑 config/stock_pool.yaml：

YAML

custom_stocks:
  - code: "600519"
    name: "贵州茅台"
  # 添加更多股票...
定时任务配置
编辑 config/base_config.yaml：

YAML

schedule:
  market_data_update: "15:30"  # 盘后数据更新
  sentiment_crawl: "19:30"     # 舆情爬取
  signal_generation: "20:30"   # 信号生成
  daily_report: "21:00"        # 发送报告
邮件配置
编辑 config/secrets.yaml：

YAML

email:
  sender: "your_email@qq.com"
  password: "your_auth_code"  # QQ邮箱授权码
  receiver: "your_email@qq.com"
📊 数据查看
查看数据库
PowerShell

# 安装 SQLite 浏览器
# 推荐：DB Browser for SQLite (https://sqlitebrowser.org/)

# 打开数据库文件
database/market_data.db     # 市场数据
database/sentiment_data.db  # 舆情数据
查看报告
PowerShell

# HTML报告自动保存在
data/exports/daily_report.html

# 用浏览器打开查看
🔧 常见问题
Q1: 邮件发送失败
A: 检查以下几点：

QQ邮箱授权码是否正确（不是QQ密码）
防火墙是否拦截
查看日志文件 logs/app.log
Q2: Ollama超时
A: 增加超时时间：

YAML

# config/llm_config.yaml
ollama:
  timeout: 300  # 改为5分钟
Q3: 数据获取失败
A:

检查网络连接
AKShare可能被限流，稍后重试
使用备用数据源（在代码中切换）
📅 推荐工作流
每日流程（自动）
text

15:30 → 更新市场数据
19:30 → 爬取舆情数据
20:30 → 分析并生成信号
21:00 → 发送邮件报告
周末流程（手动）
text

1. 回顾本周信号准确率
2. 调整股票池
3. 优化因子权重
4. 测试新策略
🛡️ 风险提示
⚠️ 重要声明

本系统仅供学习研究使用
不构成投资建议
投资有风险，决策需谨慎
请勿用于实盘交易（除非充分测试）
📞 支持
邮箱：hongguang_22@qq.com
GitHub：[项目地址]