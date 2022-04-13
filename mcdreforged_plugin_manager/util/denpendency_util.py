from mcdreforged.api.all import *

from mcdreforged_plugin_manager.constants import psi


def check_dependency(dependency: str, requirement: str):
    if dependency not in psi.get_plugin_list():
        return False, False
    metadata = psi.get_plugin_metadata(dependency)
    if not VersionRequirement(requirement).accept(metadata.version):
        return True, False
    return True, True
