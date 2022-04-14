import importlib
import re
from typing import Tuple

from mcdreforged.api.all import *


def get_package_version(package_name: str):
    try:
        module = importlib.import_module(package_name)

        if hasattr(module, '__version__'):
            return module.__version__
        else:
            return None
    except ImportError:
        return None


class RequirementParsingError(Exception):
    pass


def parse_python_requirement(line: str) -> Tuple[str, str]:
    matched = re.match(r'^[^<>=~^]+', line)
    if matched is None:
        raise RequirementParsingError
    package = matched.group()
    requirement = line.lstrip(package)
    if requirement == '':
        requirement = '*'
    else:
        if any([operator in requirement for operator in ['~=', '^=']]):
            # ~= -> ~, ^= -> ^
            requirement = requirement.replace('=', '')
    return package, requirement


if __name__ == '__main__':
    print(parse_python_requirement('mcdreforged>=2.0.1'))
    print(parse_python_requirement('mcdreforged~=2.0.1'))
