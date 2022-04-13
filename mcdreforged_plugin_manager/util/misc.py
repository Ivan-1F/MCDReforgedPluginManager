import importlib
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


def parse_python_requirement(line: str) -> Tuple[str, str]:
    for criterion in VersionRequirement.CRITERIONS.keys():
        comps = line.rsplit(criterion, 1)
        if len(comps) == 2:
            package = comps[0]
            requirement = criterion + comps[1]
            return package, requirement
    return line, '*'


if __name__ == '__main__':
    print(parse_python_requirement('mcdreforged>=2.0.1'))
