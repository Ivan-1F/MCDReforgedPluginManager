import re
from typing import List

from mcdreforged.api.all import *


def parse_markdown(text: str) -> RTextList:
    components: List[RTextBase] = []

    pos = -1

    def next_pos(_):
        nonlocal pos
        pos += 1
        return '{' + str(pos) + '}'

    links = [
        RText(link[0], RColor.blue)
        .set_styles([RStyle.underlined])
        .c(RAction.open_url, link[1])
        .h(link[1])
        for link in re.findall(r'\[(.*?)]\((.*?)\)', text)
    ]
    [components.append(link) for link in links]
    text = re.sub(r'\[(.*?)]\((.*?)\)', next_pos, text)

    bolds = [RText(bold).set_styles(RStyle.bold) for bold in re.findall(r'\*\*(.*)\*\*', text)]
    [components.append(bold) for bold in bolds]
    text = re.sub(r'\*\*(.*)\*\*', next_pos, text)

    italics = [RText(italic).set_styles(RStyle.italic) for italic in re.findall(r'\*(.*)\*', text)]
    [components.append(italic) for italic in italics]
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
