from typing import Any


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
