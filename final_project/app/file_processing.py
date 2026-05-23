import os
import re
from typing import Any

from app.chat import send_message


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
