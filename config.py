# -*- coding: utf-8 -*-
"""配置加载：DeepSeek API key 与模型参数。

优先级：环境变量 DEEPSEEK_API_KEY > config.json 里的 deepseek_api_key。
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

DEFAULTS = {
    "deepseek_api_key": "",
    "deepseek_base_url": "https://api.deepseek.com",
    "deepseek_model": "deepseek-chat",
    "deepseek_temperature": 0.1,
    "host": "0.0.0.0",
    "port": 5000,
}


def load_config():
    cfg = dict(DEFAULTS)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass
    env_key = os.environ.get("DEEPSEEK_API_KEY")
    if env_key:
        cfg["deepseek_api_key"] = env_key
    return cfg
