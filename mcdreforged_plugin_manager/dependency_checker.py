from abc import ABC
from enum import Enum, unique

from mcdreforged.plugin.meta.version import VersionRequirement, VersionParsingError

from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.util.mcdr_util import is_plugin_loaded
from mcdreforged_plugin_manager.util.misc_util import get_package_version
from mcdreforged_plugin_manager.util.translation_util import tr


class DependencyError(Exception):
    pass


class DependencyNotFound(DependencyError):
    pass


class DependencyNotMet(DependencyError):
    pass


class InvalidDependency(DependencyError):
    pass


@unique
class DependencyOperation(Enum):
    IGNORE = 'dependency.operation.ignore'
    INSTALL = 'dependency.operation.install'
    UPGRADE = 'dependency.operation.upgrade'


class DependencyChecker(ABC):
    """
    A checker to check if the local dependency met the requirement
    """
    def __init__(self, name: str, requirement: str):
        self.name = name
        self.requirement = requirement

    def _check_version(self, version: str):
        try:
            if not VersionRequirement(self.requirement).accept(version):
                raise DependencyNotMet(tr('dependency.dependency_not_met', self.name, self.requirement, version))
        except VersionParsingError as e:
            raise InvalidDependency(tr('dependency.invalid_dependency', self.name, e))

    def check(self):
        raise NotImplementedError()

    def get_operation(self) -> DependencyOperation:
        try:
            self.check()
        except DependencyNotFound:
            return DependencyOperation.INSTALL
        except DependencyNotMet:
            return DependencyOperation.UPGRADE
        except InvalidDependency:
            return DependencyOperation.IGNORE
        else:
            return DependencyOperation.IGNORE


class PackageDependencyChecker(DependencyChecker):
    def __init__(self, name: str, requirement: str):
        super().__init__(name, requirement)

    def check(self):
        if get_package_version(self.name) is None:
            raise DependencyNotFound(tr('dependency.dependency_not_found', self.name))
        version = get_package_version(self.name)
        self._check_version(version)


class PluginDependencyChecker(DependencyChecker):
    def __init__(self, name: str, requirement: str):
        super().__init__(name, requirement)

    def check(self):
        if not is_plugin_loaded(self.name) and self.name != 'mcdreforged':
            raise DependencyNotFound(tr('dependency.dependency_not_found', self.name))
        metadata = psi.get_plugin_metadata(self.name)
        self._check_version(metadata.version)
