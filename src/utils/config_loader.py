"""
配置加载模块
"""
import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_dir: str = './config'):
        self.config_dir = Path(config_dir)
        self._configs = {}
    
    def load(self, config_name: str) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_name: 配置文件名（不含.yaml后缀）
            
        Returns:
            配置字典
        """
        if config_name in self._configs:
            return self._configs[config_name]
        
        config_file = self.config_dir / f"{config_name}.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self._configs[config_name] = config
        return config
    
    def get(self, config_name: str, key_path: str, default: Any = None) -> Any:
        """
        获取配置项（支持嵌套key）
        
        Args:
            config_name: 配置文件名
            key_path: 配置路径，如 'database.type'
            default: 默认值
            
        Returns:
            配置值
        
        Example:
            >>> loader = ConfigLoader()
            >>> db_type = loader.get('base_config', 'database.type')
        """
        config = self.load(config_name)
        
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value


# 创建全局配置加载器
config_loader = ConfigLoader()