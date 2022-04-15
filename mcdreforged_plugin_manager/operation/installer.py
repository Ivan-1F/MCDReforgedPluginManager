from abc import ABC, abstractmethod
from typing import List, Any
from urllib.request import urlretrieve

from mcdreforged.api.all import *

from mcdreforged_plugin_manager.dependency_checker import DependencyOperation, PackageDependencyChecker, \
    DependencyError, PluginDependencyChecker
from mcdreforged_plugin_manager.operation.task_manager import Task
from mcdreforged_plugin_manager.util.cache import cache
from mcdreforged_plugin_manager.util.misc import parse_python_requirement
from mcdreforged_plugin_manager.util.storage import ReleaseSummary
from mcdreforged_plugin_manager.util.text_util import new_line, insert_between, command_run
from mcdreforged_plugin_manager.util.translation import tr


class InstallerOperation(ABC):
    def __init__(self, name: str, operation: DependencyOperation):
        self.operation = operation
        self.name = name

    @abstractmethod
    def operate(self, installer: 'PluginInstaller') -> bool:
        pass


class InstallerPluginOperation(InstallerOperation):
    def __init__(self, name: str, operation: DependencyOperation):
        super().__init__(name, operation)
        self.operation = operation
        self.name = name

    def operate(self, installer: 'PluginInstaller') -> bool:
        if self.operation == DependencyOperation.INSTALL:
            release = ReleaseSummary.of(self.name).get_latest_release()
            asset = release.get_mcdr_assets()[0]
            url = asset.browser_download_url
            filename = asset.name
            # installer.reply(tr('installer.operation.plugin.downloading', filename))
            installer.reply(RTextList(
                '   ',
                tr('installer.operation.plugin.downloading', filename)
            ))
            urlretrieve(url, './plugins/' + release.get_mcdr_assets()[0].name)
        elif self.operation == DependencyOperation.UPGRADE:
            pass
        return True


class InstallerPackageOperation(InstallerOperation):
    def __init__(self, name: str, operation: DependencyOperation):
        super().__init__(name, operation)
        self.operation = operation
        self.name = name

    def operate(self, installer: 'PluginInstaller') -> bool:
        installer.reply(RTextList(
            '   ',
            tr('installer.operation.package.operating_with_pip', tr(self.operation.value), self.name)
        ))
        if self.operation == DependencyOperation.INSTALL:
            pass
        elif self.operation == DependencyOperation.UPGRADE:
            pass
        return True


def get_operate_packages(requirements: List[str]):
    """
    Get a list of operations from raw requirement list
    """
    result: List[InstallerPackageOperation] = []
    for line in requirements:
        package, requirement = parse_python_requirement(line)
        dependency_checker = PackageDependencyChecker(package, requirement)
        try:
            dependency_checker.check()
        except DependencyError:
            if dependency_checker.get_operation() != DependencyOperation.IGNORE:
                result.append(InstallerPackageOperation(package, dependency_checker.get_operation()))
    return result


def get_operations(plugin_id: str):
    operations: List[InstallerOperation] = []
    plugin = cache.get_plugin_by_id(plugin_id)
    operations.append(InstallerPluginOperation(plugin_id, DependencyOperation.INSTALL))
    print('append', plugin_id)
    operations = [*operations, *get_operate_packages(plugin.requirements)]

    for dep_id, requirement in plugin.dependencies.items():
        plugin_checker = PluginDependencyChecker(dep_id, requirement)
        try:
            # the dependency is satisfied, ignore further dependency checking
            plugin_checker.check()
        except DependencyError:
            # the dependency is not satisfied, add its dependency then
            operations = [*operations, *get_operations(dep_id)]

    return operations


class PluginInstaller(Task):
    def __init__(self, plugin_id: str, source: CommandSource):
        self.plugin_id = plugin_id
        self.reply = source.reply
        self.operations: List[InstallerOperation] = []
        super().__init__()

    def __add_operation(self, operation: InstallerOperation):
        self.operations.append(operation)

    def __init_operations(self):
        self.operations = get_operations(self.plugin_id)

    def __format_plugins_confirm(self):
        ops = [op for op in self.operations if isinstance(op, InstallerPluginOperation)]
        if len(ops) == 0:
            return RTextList()
        return RTextList(
            tr('installer.confirm.plugin_list'),
            new_line(),
            insert_between([RText(op.name).set_color(
                RColor.dark_aqua if op.operation == DependencyOperation.INSTALL else RColor.aqua
            ) for op in ops], insertion=RText(', '))
        )

    def __format_packages_confirm(self):
        ops = [op for op in self.operations if isinstance(op, InstallerPackageOperation)]
        if len(ops) == 0:
            return RTextList()
        return RTextList(
            tr('installer.confirm.package_list'),
            new_line(),
            insert_between([RText(op.name).set_color(
                RColor.dark_aqua if op.operation == DependencyOperation.INSTALL else RColor.aqua
            ) for op in ops], insertion=RText(', '))
        )

    def __show_confirm(self):
        self.reply(tr('installer.confirm.title'))

        self.reply(self.__format_plugins_confirm())
        self.reply(self.__format_packages_confirm())

        self.reply(tr('installer.confirm.footer',
                      command_run('!!mpm confirm', '!!mpm confirm', tr('installer.confirm.command_hover'))))

    def init(self):
        self.__init_operations()
        self.__show_confirm()

    def _run(self):
        results = []
        for operation in self.operations:
            self.reply(tr('installer.operating', tr(operation.operation.value), operation.name))
            results.append(operation.operate(self))
        if all(results):
            self.reply(tr('installer.result.success'))
        else:
            self.reply(tr('installer.result.failed'))
