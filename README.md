# 📊 Quantitative Trading System（README暂未编写完成）

> 基于本地大模型的A股量化交易系统（学生个人版）

## 🎯 项目简介

这是一个面向学生的免费量化交易系统，具有以下特点：

- ✅ **完全免费**：使用免费数据源（AKShare、Tushare）
- 🤖 **本地AI增强**：集成Ollama本地大模型（DeepSeek-Coder + Qwen3）
- 📈 **情绪因子**：基于MediaCrawler爬取社交媒体情绪
- 💰 **多维因子**：技术指标 + 基本面 + 舆情分析
- 📧 **邮件通知**：QQ邮箱自动发送交易信号
- 🔙 **完整回测**：支持策略历史验证

## 🚀 快速开始

### 1. 环境准备

```powershell
# 检查Python版本（需要3.11+）
python --version

# 安装依赖
pip install -r requirements.txt

2. 配置系统
PowerShell

# 复制配置文件
copy config\secrets.yaml.example config\secrets.yaml

# 编辑 config/secrets.yaml，填入QQ邮箱授权码
3. 初始化数据库
PowerShell

python scripts/setup_database.py
4. 运行测试
PowerShell

python scripts/test_data_fetch.py
📁 项目结构
text

quantitative-trading/
├── src/              # 核心源代码
├── config/           # 配置文件
├── database/         # SQLite数据库
├── data/             # 数据文件
├── logs/             # 日志
├── notebooks/        # Jupyter研究笔记
└── scripts/          # 工具脚本
📧 联系方式
Email: hongguang_22@qq.com
📄 开源协议
MIT License
