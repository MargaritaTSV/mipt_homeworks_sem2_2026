import os

from openai import OpenAI

from app.chat import get_model, send_message
from app.config import load_config
from app.file_processing import file_chunk_mode, process_file_refs
from app.history import trim_history


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
