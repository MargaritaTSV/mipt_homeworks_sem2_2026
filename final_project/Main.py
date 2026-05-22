import os
import re
import sys
from typing import Any
import yaml
from openai import OpenAI


def load_config() -> dict[str, Any]:
    config = {}
    yaml_path = 'config.yaml'
    if os.path.exists(yaml_path):
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


def trim_history(
    messages: list[dict[str, str]], limit_msg: int, limit_chars: int
) -> list[dict[str, str]]:
    if limit_msg is not None:
        while len(messages) > limit_msg:
            messages.pop(0)

    if limit_chars is not None:
        total = sum(len(m['content']) for m in messages)
        while total > limit_chars and len(messages) > 0:
            total -= len(messages[0]['content'])
            messages.pop(0)

    return messages


def process_file_refs(text: str) -> str:
    pattern = r'@::(.+?)::'
    matches = re.findall(pattern, text)
    result = re.sub(pattern, '', text).strip()

    for fpath in matches:
        fpath = fpath.strip()
        if not os.path.exists(fpath):
            print(f'Файл не найден: {fpath}')
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        result = result + '\n' + content

    return result


def send_message(
    client: Any, model: str, messages: list[dict[str, str]], sys_prompt: str, temperature: float
) -> str:
    req_messages = []
    if sys_prompt:
        req_messages.append({'role': 'system', 'content': sys_prompt})
    req_messages.extend(messages)

    stream = client.chat.completions.create(
        model=model,
        messages=req_messages,
        temperature=temperature,
        stream=True,
    )

    full_response = ''
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            piece = chunk.choices[0].delta.content
            print(piece, end='', flush=True)
            full_response += piece
    print()
    return full_response


def get_model(client: Any, config_model: str | None) -> str:
    if config_model:
        return config_model
    models = client.models.list()
    if models.data:
        return str(models.data[0].id)
    return 'gemma3:4b'


def parse_file_chunk_args(cmd_text: str) -> tuple[int, int | None, bool]:
    parts = cmd_text.strip().split()
    paragraph = 1
    char_len = None
    auto = False

    for p in parts:
        if p.startswith('paragraph='):
            paragraph = int(p.split('=')[1])
        elif p.startswith('len='):
            char_len = int(p.split('=')[1])
        elif p == '-y':
            auto = True

    return paragraph, char_len, auto


def split_into_chunks(text: str, paragraph_count: int, char_len: int | None) -> list[str]:
    if char_len is not None:
        chunks = []
        for i in range(0, len(text), char_len):
            chunks.append(text[i : i + char_len])
        return chunks

    paragraphs = text.split('\n')
    paragraphs = [p for p in paragraphs if p.strip()]
    chunks = []
    for i in range(0, len(paragraphs), paragraph_count):
        chunk = '\n'.join(paragraphs[i : i + paragraph_count])
        chunks.append(chunk)
    return chunks


def file_chunk_mode(client: Any, model: str, config: dict[str, Any], cmd_text: str) -> None:
    paragraph_count, char_len, auto = parse_file_chunk_args(cmd_text)

    filepath = input('Введите путь до файла\n').strip()
    if not os.path.exists(filepath):
        print(f'Файл не найден: {filepath}')
        return
    fsize = os.path.getsize(filepath)
    if fsize > 5 * 1024 * 1024:
        print('Файл слишком большой (лимит 5MB)')
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        file_text = f.read()

    user_prompt = input('Файл был получен. Что необходимо сделать?\n').strip()
    print('Начинаю обработку:')

    chunks = split_into_chunks(file_text, paragraph_count, char_len)

    for i, chunk in enumerate(chunks):
        msg_content = user_prompt + '\n\n' + chunk
        messages = [{'role': 'user', 'content': msg_content}]

        try:
            send_message(client, model, messages, config['system_prompt'], config['temperature'])
        except KeyboardInterrupt:
            print('\nЗапрос прерван.')

        if i < len(chunks) - 1:
            if not auto:
                try:
                    input()
                except EOFError:
                    break
                except KeyboardInterrupt:
                    print()
                    break

    print('Обработка файла завершена.')


def clear_screen() -> None:
    os.system('cls')


def main() -> None:
    config = load_config()
    client = OpenAI(api_key=config['api_key'], base_url=config['api_host'])
    model = get_model(client, config.get('model'))

    history: list[dict[str, str]] = []

    print('GigaVibeMiptCode - ИИ-ассистент')
    print('Команды: \\q - выход, /reset - очистить историю')
    print('/file_chunk - обработка файла по частям')
    print()

    while True:
        try:
            user_input = input('>>> ')
        except KeyboardInterrupt:
            print()
            break

        if user_input.strip() == '\\q':
            break

        if user_input.strip() == '/reset':
            history = []
            clear_screen()
            print('История очищена.')
            continue

        if user_input.strip().startswith('/file_chunk'):
            cmd_text = user_input.strip()[len('/file_chunk') :]
            file_chunk_mode(client, model, config, cmd_text)
            continue

        if not user_input.strip():
            continue

        processed = process_file_refs(user_input)
        history.append({'role': 'user', 'content': processed})
        history = trim_history(history, config['limit_message'], config['limit_chars'])

        try:
            response = send_message(
                client, model, history, config['system_prompt'], config['temperature']
            )
            history.append({'role': 'assistant', 'content': response})
            history = trim_history(history, config['limit_message'], config['limit_chars'])
        except KeyboardInterrupt:
            print('\nЗапрос прерван.')


if __name__ == '__main__':
    main()
