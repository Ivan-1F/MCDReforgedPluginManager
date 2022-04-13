import re
from typing import List, Any

from mcdreforged.api.all import *


def italic(text: Any) -> RTextBase:
    return RText(text).set_styles(RStyle.italic)


def bold(text: Any) -> RTextBase:
    return RText(text).set_styles(RStyle.bold)


def link(text: Any, target: Any) -> RTextBase:
    return RText(text, RColor.blue) \
        .set_styles([RStyle.underlined]) \
        .c(RAction.open_url, target) \
        .h(target)


def new_line() -> RTextBase:
    return RText('\n')


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
