import re
from typing import List, Any, Optional, Union
import time as python_time

from mcdreforged.api.all import *


def italic(text: Any) -> RTextBase:
    return RText(text).set_styles(RStyle.italic)


def bold(text: Any) -> RTextBase:
    return RText(text).set_styles(RStyle.bold)


def link(text: Any, target: Any) -> RTextBase:
    return RText(text, RColor.aqua) \
        .set_styles([RStyle.underlined]) \
        .c(RAction.open_url, target) \
        .h(target)


def time(created_at: str, precision: str = 'second') -> str:
    """
    :param created_at: The created_at field from github api
    :param precision: should be 'day' or 'second'
    """
    st = python_time.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ')
    fmt = '%Y/%m/%d'
    if precision == 'second':
        fmt += ' %H:%M:%S'
    return python_time.strftime(fmt, st)


def size(byte: int) -> str:
    for c in ('B', 'KB', 'MB', 'GB', 'TB'):
        unit = c
        if byte < 2 ** 10:
            break
        byte /= 2 ** 10
    return str(round(byte, 2)) + unit


def new_line() -> RTextBase:
    return RText('\n')


def insert_new_lines(texts: Union[List[RTextBase], RTextList]) -> RTextBase:
    return insert_between(texts, new_line())


def insert_between(texts: Union[List[RTextBase], RTextList], insertion: RTextBase) -> RTextBase:
    result = RTextList()
    if isinstance(texts, RTextList):
        texts = texts.children
    for index, text in enumerate(texts):
        result.append(text)
        if index != len(texts) - 1:
            result.append(insertion)
    return result


def command_run(message: Any, command: str, text: Optional[Any] = None):
    fancy_text = message.copy() if isinstance(message, RTextBase) else RText(message)
    return fancy_text.set_hover_text(text).set_click_event(RAction.run_command, command)


def parse_markdown(text: str) -> RTextList:
    components: List[RTextBase] = []

    pos = -1

    def next_pos(_):
        nonlocal pos
        pos += 1
        return '{' + str(pos) + '}'

    [components.append(item) for item in map(lambda x: link(*x), re.findall(r'\[(.*?)]\((.*?)\)', text))]
    text = re.sub(r'\[(.*?)]\((.*?)\)', next_pos, text)

    [components.append(item) for item in map(bold, re.findall(r'\*\*(.*)\*\*', text))]
    text = re.sub(r'\*\*(.*)\*\*', next_pos, text)

    [components.append(item) for item in map(italic, re.findall(r'\*(.*)\*', text))]
    text = re.sub(r'\*(.*)\*', next_pos, text)

    pointer = 0
    ret = RTextList()
    for item in re.finditer(r'{(\d)}', text):
        index = int(item.group(1))
        start, end = item.span()
        ret.append(text[pointer:start])
        ret.append(components[index])
        pointer = end
    ret.append(text[pointer:len(text)])

    return ret


if __name__ == '__main__':
    parse_markdown('[QuickBackupM](https://github.com/TISUnion/QuickBackupM) is a plugin of [MCDReforged]('
                   'https://github.com/Fallen_Breath/MCDReforged) to **backup** the *server*')

    print(insert_new_lines([]).to_json_str())
    print(insert_new_lines([RText('message')]).to_json_str())
    print(RText('message').to_json_str())
    print(insert_new_lines([RText('hello'), RText('world')]).to_json_str())
    print(RText('message').to_json_str())
