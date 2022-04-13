from mcdreforged.api.all import *

from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.util.translation import tr


class DependencyError(Exception):
    pass


class DependencyNotFound(DependencyError):
    pass


class DependencyNotMet(DependencyError):
    pass


def check_dependency(plugin_id: str, requirement: str):
    if plugin_id not in psi.get_plugin_list():
        raise DependencyNotFound(tr('dependency.dependency_not_found', plugin_id))
    metadata = psi.get_plugin_metadata(plugin_id)
    if not VersionRequirement(requirement).accept(metadata.version):
        raise DependencyNotFound(tr('dependency.dependency_not_met', plugin_id, requirement, metadata.version))
