"""
检查Ollama环境
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from src.utils.logger import logger
from src.utils.config_loader import config_loader


def check_ollama_service():
    """检查Ollama服务状态"""
    print("="*60)
    print("检查Ollama服务")
    print("="*60)
    
    config = config_loader.load('llm_config')
    base_url = config['ollama']['base_url']
    
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Ollama服务运行正常: {base_url}")
            return True
        else:
            print(f"❌ Ollama服务异常: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到Ollama: {base_url}")
        print("\n请检查:")
        print("  1. Ollama Desktop是否正在运行")
        print("  2. 或在终端运行: ollama serve")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


def list_installed_models():
    """列出已安装的模型"""
    print("\n" + "="*60)
    print("已安装的模型")
    print("="*60)
    
    config = config_loader.load('llm_config')
    base_url = config['ollama']['base_url']
    
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        response.raise_for_status()
        
        models = response.json().get('models', [])
        
        if not models:
            print("⚠️ 未找到已安装的模型")
            return []
        
        print(f"\n共 {len(models)} 个模型:\n")
        for model in models:
            name = model.get('name', 'unknown')
            size = model.get('size', 0) / (1024**3)  # 转换为GB
            modified = model.get('modified_at', '')
            
            print(f"  • {name}")
            print(f"    大小: {size:.1f} GB")
            print(f"    修改时间: {modified[:10]}")
            print()
        
        return [m['name'] for m in models]
        
    except Exception as e:
        print(f"❌ 获取模型列表失败: {e}")
        return []


def check_required_models():
    """检查配置文件中要求的模型是否已安装"""
    print("="*60)
    print("检查配置的模型")
    print("="*60)
    
    config = config_loader.load('llm_config')
    installed = list_installed_models()
    
    if not installed:
        return False
    
    print("\n" + "="*60)
    print("配置验证")
    print("="*60)
    
    all_ok = True
    
    for model_type, model_config in config['ollama']['models'].items():
        model_name = model_config['name']
        think = model_config.get('think', None)
        
        # 检查是否安装（模糊匹配，因为可能有版本号）
        is_installed = any(model_name in m for m in installed)
        
        if is_installed:
            think_status = f" (think={think})" if think is not None else ""
            print(f"✅ {model_type}: {model_name}{think_status}")
        else:
            print(f"❌ {model_type}: {model_name} (未安装)")
            all_ok = False
    
    if not all_ok:
        print("\n" + "="*60)
        print("⚠️ 缺少模型，请安装:")
        print("="*60)
        
        for model_type, model_config in config['ollama']['models'].items():
            model_name = model_config['name']
            is_installed = any(model_name in m for m in installed)
            
            if not is_installed:
                print(f"  ollama pull {model_name}")
    
    return all_ok


def test_model_generation():
    """测试模型生成"""
    print("\n" + "="*60)
    print("测试模型生成")
    print("="*60)
    
    config = config_loader.load('llm_config')
    base_url = config['ollama']['base_url']
    timeout = config['ollama']['timeout']
    
    # 测试情绪分析模型
    model_config = config['ollama']['models']['sentiment_analyzer']
    model_name = model_config['name']
    think = model_config.get('think', None)
    
    print(f"\n测试模型: {model_name}")
    print(f"超时设置: {timeout}秒")
    if think is not None:
        print(f"深度思考: {'启用' if think else '禁用'}")
    
    options = {
        "temperature": 0.7,
        "num_predict": 100
    }
    
    # 添加think参数
    if think is not None:
        options["think"] = think
    
    payload = {
        "model": model_name,
        "prompt": "请用一句话介绍量化交易",
        "stream": False,
        "options": options
    }
    
    try:
        print("发送请求...")
        import time
        start_time = time.time()
        
        response = requests.post(
            f"{base_url}/api/generate",
            json=payload,
            timeout=timeout
        )
        
        elapsed = time.time() - start_time
        print(f"耗时: {elapsed:.1f}秒")
        
        response.raise_for_status()
        
        result = response.json()
        generated_text = result.get('response', '')
        
        if generated_text:
            print(f"\n✅ 生成成功:")
            print(f"  {generated_text[:200]}")
            return True
        else:
            print("❌ 生成结果为空")
            print(f"完整响应: {result}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时（超过{timeout}秒）")
        print("\n建议:")
        print(f"  1. 增加超时: 修改 config/llm_config.yaml 中 timeout: {timeout} -> 180")
        print(f"  2. 禁用深度思考: 在 sentiment_analyzer 下添加 think: false")
        return False
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "🔍 Ollama环境检查工具\n")
    
    # 1. 检查服务
    if not check_ollama_service():
        print("\n❌ Ollama服务未启动，无法继续检查")
        return
    
    # 2. 检查模型
    if not check_required_models():
        print("\n⚠️ 请先安装缺少的模型")
        return
    
    # 3. 测试生成
    if test_model_generation():
        print("\n" + "="*60)
        print("✅ 所有检查通过！可以运行舆情系统测试")
        print("="*60)
        print("\n运行: python scripts/test_sentiment_system.py")
    else:
        print("\n❌ 模型生成测试失败")
        print("\n请按照上述建议修改配置后重试")


if __name__ == '__main__':
    main()