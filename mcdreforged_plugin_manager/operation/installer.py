import os
import subprocess
import sys
from abc import ABC, abstractmethod
from typing import List, Optional

import requests
from mcdreforged.api.all import *

from mcdreforged_plugin_manager.config import config
from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.dependency_checker import DependencyOperation, PackageDependencyChecker, \
    DependencyError, PluginDependencyChecker
from mcdreforged_plugin_manager.operation.task_manager import Task
from mcdreforged_plugin_manager.texts import CONFIRM_COMMAND_TEXT
from mcdreforged_plugin_manager.storage.cache import cache
from mcdreforged_plugin_manager.util.mcdr_util import is_plugin_loaded, remove_plugin_file
from mcdreforged_plugin_manager.util.misc import parse_python_requirement
from mcdreforged_plugin_manager.util.network_util import download_file
from mcdreforged_plugin_manager.storage.release import ReleaseSummary
from mcdreforged_plugin_manager.util.text_util import new_line, insert_between, indented
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
        self.install_path = config.install_path

    def operate(self, installer: 'PluginInstaller') -> bool:
        if self.operation == DependencyOperation.UPGRADE:
            installer.reply(indented(
                tr('installer.operation.plugin.removing', psi.get_plugin_file_path(self.name))
            ))
            self.install_path = os.path.dirname(psi.get_plugin_file_path(self.name))
            remove_plugin_file(self.name)
        if self.operation in [DependencyOperation.INSTALL, DependencyOperation.UPGRADE]:
            try:
                summary = ReleaseSummary.of(self.name)
            except requests.RequestException as e:
                installer.reply(indented(
                    tr('plugin.release.failed_to_get_release', e)
                ))
                return False
            release = summary.get_latest_release()
            asset = release.get_mcdr_assets()[0]
            url = asset.browser_download_url
            filename = asset.name
            installer.reply(indented(
                tr('installer.operation.plugin.downloading', filename)
            ))
            try:
                download_file(url, os.path.join(self.install_path, filename))
            except requests.RequestException as e:
                installer.reply(indented(
                    tr('installer.operation.plugin.exception', e), 2
                ))
                return False
        return True


class InstallerPackageOperation(InstallerOperation):
    def __init__(self, name: str, operation: DependencyOperation):
        super().__init__(name, operation)
        self.operation = operation
        self.name = name

    def operate(self, installer: 'PluginInstaller') -> bool:
        installer.reply(indented(
            tr('installer.operation.package.operating_with_pip', tr(self.operation.value), self.name))
        )
        params = []
        if self.operation == DependencyOperation.INSTALL:
            params = [sys.executable, '-m', 'pip', 'install', self.name]
        elif self.operation == DependencyOperation.UPGRADE:
            params = [sys.executable, '-m', 'pip', 'install', '-U', self.name]
        try:
            subprocess.check_call(params)
        except subprocess.CalledProcessError as e:
            installer.reply(indented(
                tr('installer.operation.package.exception', e), 2
            ))
            return False
        else:
            return True


def get_operate_packages(requirements: List[str]) -> List[InstallerPackageOperation]:
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


def get_operations(plugin_id: str, self_operation: DependencyOperation) -> List[InstallerOperation]:
    operations: List[InstallerOperation] = []
    plugin = cache.get_plugin_by_id(plugin_id)
    operations.append(InstallerPluginOperation(plugin_id, self_operation))
    operations = [*operations, *get_operate_packages(plugin.requirements)]

    for dep_id, requirement in plugin.dependencies.items():
        plugin_checker = PluginDependencyChecker(dep_id, requirement)
        try:
            # the dependency is satisfied, ignore further dependency checking
            plugin_checker.check()
        except DependencyError:
            # the dependency is not satisfied, add its dependency then
            operations = [*operations, *get_operations(dep_id, plugin_checker.get_operation())]

    return operations


class PluginInstaller(Task):
    def __init__(self, plugin_ids: List[str], source: CommandSource, upgrade=False):
        self.upgrade = upgrade
        self.plugin_ids = plugin_ids
        self.reply = source.reply
        self.operations: List[InstallerOperation] = []
        self.__cancel_flag = False
        super().__init__()

    def __add_operation(self, operation: InstallerOperation):
        self.operations.append(operation)

    def __init_operations(self) -> bool:
        for plugin_id in self.plugin_ids:
            if is_plugin_loaded(plugin_id):
                if not self.upgrade:
                    self.reply(tr('installer.already_installed', plugin_id))
                success, latest_version, local_version = cache.get_plugin_by_id(plugin_id).check_update()
                if success:
                    if not self.upgrade:
                        self.reply(tr(
                            'installer.newer_version_available',
                            plugin_id,
                            latest_version
                        ))
                        self.upgrade = True
                else:
                    if not self.upgrade:
                        self.reply(tr('installer.already_up_to_date', plugin_id))
                        continue
            for operation in get_operations(
                plugin_id, DependencyOperation.UPGRADE if self.upgrade else DependencyOperation.INSTALL
            ):
                if operation.name not in [op.name for op in self.operations]:
                    self.operations.append(operation)
        return len(self.operations) != 0

    def __format_plugins_confirm(self) -> Optional[RTextBase]:
        ops = [op for op in self.operations if isinstance(op, InstallerPluginOperation)]
        if len(ops) == 0:
            return None
        return RTextList(
            tr('installer.confirm.plugin_list'),
            new_line(),
            insert_between([RText(op.name).set_color(
                RColor.dark_aqua if op.operation == DependencyOperation.INSTALL else RColor.aqua
            ) for op in ops], insertion=RText(', '))
        )

    def __format_packages_confirm(self) -> Optional[RTextBase]:
        ops = [op for op in self.operations if isinstance(op, InstallerPackageOperation)]
        if len(ops) == 0:
            return None
        return RTextList(
            tr('installer.confirm.package_list'),
            new_line(),
            insert_between([RText(op.name).set_color(
                RColor.dark_aqua if op.operation == DependencyOperation.INSTALL else RColor.aqua
            ) for op in ops], insertion=RText(', '))
        )

    def __reply_if_present(self, text: Optional[RTextBase]):
        if text is not None:
            self.reply(text)

    def __show_confirm(self):
        self.reply(tr(
            'installer.confirm.title',
            tr('dependency.operation.upgrade') if self.upgrade else tr('dependency.operation.install')
        ))

        self.__reply_if_present(self.__format_plugins_confirm())
        self.__reply_if_present(self.__format_packages_confirm())

        self.reply(tr('installer.confirm.footer', CONFIRM_COMMAND_TEXT))

    def init(self):
        if self.__init_operations():
            self.__show_confirm()

    @new_thread('mpm-installer')
    def run(self):
        results = []
        for operation in self.operations:
            self.reply(tr('installer.operating', tr(operation.operation.value), operation.name))
            results.append(operation.operate(self))
        if all(results):
            self.reply(tr('installer.operation.reload_mcdr'))
            psi.refresh_changed_plugins()
            self.reply(tr('installer.result.success'))
        else:
            self.reply(tr('installer.result.failed'))
