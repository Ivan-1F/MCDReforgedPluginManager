from mcdreforged.api.all import *
from mcdreforged.plugin.meta.version import VersionParsingError

from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.util.misc import get_package_version
from mcdreforged_plugin_manager.util.translation import tr


class DependencyError(Exception):
    pass


class DependencyNotFound(DependencyError):
    pass


class DependencyNotMet(DependencyError):
    pass


class InvalidDependency(DependencyError):
    pass


def check_version(requirement: str, version: str):
    try:
        if not VersionRequirement(requirement).accept(version):
            raise DependencyNotFound(tr('dependency.dependency_not_met', package, requirement, version))
    except VersionParsingError as e:
        raise InvalidDependency(tr('dependency.invalid_dependency', package, e))


def check_dependency(plugin_id: str, requirement: str):
    if plugin_id not in psi.get_plugin_list():
        raise DependencyNotFound(tr('dependency.dependency_not_found', plugin_id))
    metadata = psi.get_plugin_metadata(plugin_id)
    check_version(requirement, metadata.version)


def check_requirement(package: str, requirement: str):
    if get_package_version(package) is None:
        raise DependencyNotFound(tr('dependency.dependency_not_found', package))
    version = get_package_version(package)
    check_version(requirement, version)
