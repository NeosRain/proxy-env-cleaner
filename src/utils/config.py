"""
Configuration manager / 配置管理器
"""
import json
import os
from pathlib import Path
from typing import Any, Dict

from .platform_utils import is_windows


DEFAULT_CONFIG = {
    "auto_clean_on_startup": True,      # 开机自动清理 / Auto clean on startup
    "show_notification": True,           # 显示通知 / Show notification
    "clean_system_proxy": True,          # 清理系统代理 / Clean system proxy
    "clean_env_variables": True,         # 清理环境变量 / Clean environment variables
    "clean_git_proxy": True,             # 清理 Git 代理 / Clean Git proxy
    "clean_apt_proxy": True,             # 清理 APT 代理 (Linux) / Clean APT proxy
    "minimize_to_tray": True,            # 最小化到托盘 / Minimize to tray
    "language": "bilingual",             # 语言: bilingual/zh/en
}


def get_config_dir() -> Path:
    """Get config directory / 获取配置目录"""
    if is_windows():
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    
    config_dir = base / "ClashEnvCleaner"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_file() -> Path:
    """Get config file path / 获取配置文件路径"""
    return get_config_dir() / "config.json"


class Config:
    """Configuration manager class / 配置管理类"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = {}
            cls._instance._load()
        return cls._instance
    
    def _load(self) -> None:
        """Load config from file / 从文件加载配置"""
        config_file = get_config_file()
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self.save()
    
    def save(self) -> None:
        """Save config to file / 保存配置到文件"""
        config_file = get_config_file()
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=4, ensure_ascii=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value / 获取配置值"""
        return self._config.get(key, DEFAULT_CONFIG.get(key, default))
    
    def set(self, key: str, value: Any) -> None:
        """Set config value / 设置配置值"""
        self._config[key] = value
        self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all config / 获取所有配置"""
        return self._config.copy()


# Global config instance / 全局配置实例
config = Config()
