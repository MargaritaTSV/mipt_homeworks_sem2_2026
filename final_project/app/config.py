import os
import sys
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def load_config() -> dict[str, Any]:
    load_dotenv()

    config: dict[str, Any] = {}
    yaml_path = Path(__file__).resolve().parent.parent / 'config.yaml'
    if yaml_path.exists():
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data:
                config = data

    api_key = os.environ.get('API_KEY', config.get('api_key'))
    limit_chars_before = os.environ.get('LIMIT_CHARS', config.get('limit_chars'))
    api_host = os.environ.get('API_HOST', config.get('api_host'))
    limit_msg_before = os.environ.get('LIMIT_MESSAGE', config.get('limit_message'))
    temp_raw = os.environ.get('TEMPERATURE', config.get('temperature'))
    system_prompt = os.environ.get('SYSTEM_PROMPT', config.get('system_prompt'))
    model_name = os.environ.get('MODEL', config.get('model'))

    if not api_key or not api_host:
        print('Ошибка: не найдены настройки. Задайте переменные окружения или создайте config.yaml')
        sys.exit(1)

    limit_msg = int(limit_msg_before) if limit_msg_before else 20
    limit_chars = int(limit_chars_before) if limit_chars_before else 4000
    temp = float(temp_raw) if temp_raw else 0.7

    return {
        'api_key': api_key,
        'api_host': api_host,
        'limit_message': limit_msg,
        'limit_chars': limit_chars,
        'temperature': temp,
        'system_prompt': system_prompt,
        'model': model_name,
    }
