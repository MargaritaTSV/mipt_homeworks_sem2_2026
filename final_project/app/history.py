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
