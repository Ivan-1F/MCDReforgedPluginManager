import os
import subprocess
import sys
from abc import ABC
from typing import List, Optional

import requests
from mcdreforged.api.decorator import new_thread
from mcdreforged.command.command_source import CommandSource
from mcdreforged.minecraft.rtext.style import RColor
from mcdreforged.minecraft.rtext.text import RTextBase, RTextList, RText

from mcdreforged_plugin_manager.config import config
from mcdreforged_plugin_manager.constants import psi, meta
from mcdreforged_plugin_manager.dependency_checker import DependencyOperation, PackageDependencyChecker, \
    DependencyError, PluginDependencyChecker
from mcdreforged_plugin_manager.storage.cache import cache
from mcdreforged_plugin_manager.task.task_manager import Task, task_manager
from mcdreforged_plugin_manager.texts import CONFIRM_COMMAND_TEXT
from mcdreforged_plugin_manager.util.mcdr_util import is_plugin_loaded, remove_plugin_file
from mcdreforged_plugin_manager.util.misc_util import parse_python_requirement
from mcdreforged_plugin_manager.util.network_util import download_file
from mcdreforged_plugin_manager.util.text_util import indented, new_line, insert_between
from mcdreforged_plugin_manager.util.translation_util import tr


class InstallerOperation(ABC):
    def __init__(self, name: str, operation: DependencyOperation):
        self.operation = operation
        self.name = name

    def operate(self, installer: 'PluginInstaller') -> bool:
        """
        Do the operation
        :return: whether the operation is successful
        """
        raise NotImplementedError()


class InstallPluginOperation(InstallerOperation):
    def __init__(self, name: str, operation: DependencyOperation):
        super().__init__(name, operation)
        self.operation = operation
        self.name = name
        self.install_path = config.install_path

    def operate(self, installer: 'PluginInstaller') -> bool:
        if self.operation == DependencyOperation.UPGRADE:
            self.install_path = os.path.dirname(psi.get_plugin_file_path(self.name))
        if self.operation in [DependencyOperation.INSTALL, DependencyOperation.UPGRADE]:
            summary = cache.get_plugin_by_id(self.name).release
            release = summary.get_latest_release()
            url = config.release_download_url_template.format(url=release.asset.browser_download_url)
            filename = release.asset.name
            temp_filename = filename + '.temp'
            download_filename = temp_filename if self.operation == DependencyOperation.UPGRADE else filename
            download_path = os.path.join(self.install_path, download_filename)
            installer.reply(indented(tr('install.operation.plugin.downloading', filename)))
            try:
                download_file(url, download_path)
            except requests.RequestException as e:
                installer.reply(indented(
                    tr('install.operation.plugin.exception', e), 2
                ))
                return False
            else:
                if self.operation == DependencyOperation.UPGRADE:
                    installer.reply(indented(
                        tr('install.operation.plugin.removing', psi.get_plugin_file_path(self.name))
                    ))
                    remove_plugin_file(self.name)
                    os.rename(download_path, os.path.join(self.install_path, filename))
        return True


class InstallPackageOperation(InstallerOperation):
    def __init__(self, name: str, operation: DependencyOperation):
        super().__init__(name, operation)
        self.operation = operation
        self.name = name

    def operate(self, installer: 'PluginInstaller') -> bool:
        installer.reply(
            indented(
                tr('install.operation.package.operating_with_pip', tr(self.operation.value), self.name)
            )
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
                tr('install.operation.package.exception', e), 2
            ))
            return False
        else:
            return True


def get_operate_packages(requirements: List[str]) -> List[InstallPackageOperation]:
    """
    Generate a list of operations from raw requirement list
    """
    result: List[InstallPackageOperation] = []
    for line in requirements:
        package, requirement = parse_python_requirement(line)
        if package.lstrip().startswith('mcdreforged'):
            # skip mcdreforged requirement
            # TODO: warn user here
            continue
        dependency_checker = PackageDependencyChecker(package, requirement)
        try:
            dependency_checker.check()
        except DependencyError:
            if dependency_checker.get_operation() != DependencyOperation.IGNORE:
                result.append(InstallPackageOperation(package, dependency_checker.get_operation()))
    return result


def get_operations(plugin_id: str, dependency_operation: DependencyOperation) -> List[InstallerOperation]:
    """
    Generate installer operations from plugin_id and dependency_operation
    """
    operations: List[InstallerOperation] = []
    plugin = cache.get_plugin_by_id(plugin_id)
    operations.append(InstallPluginOperation(plugin_id, dependency_operation))
    operations = [*operations, *get_operate_packages(plugin.meta.requirements)]

    for dep_id, requirement in plugin.meta.dependencies.items():
        if dep_id.lstrip().startswith('mcdreforged'):
            # skip mcdreforged dependency
            # TODO: warn user here
            continue
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
        """
        :param plugin_ids: the ids of plugins need to be installed
        :param source: the CommandSource
        :param upgrade: whether the plugin should be upgraded
        """
        self.plugin_ids = plugin_ids
        self.reply = source.reply
        self.upgrade = upgrade
        self.operations: List[InstallerOperation] = []

    def init(self):
        # don't operate on self (mcdreforged_plugin_manager)
        if meta.id in self.plugin_ids:
            if len(self.plugin_ids) == 1:  # ['mcdreforged_plugin_manager']
                self.reply(tr('install.cannot_install_self'))
                task_manager.clear_task()
                return
            else:
                self.plugin_ids.remove(meta.id)

        if self.__init_operations():
            self.__show_confirm()
        else:
            task_manager.clear_task()

    def __reply_if_present(self, text: Optional[RTextBase]):
        if text is not None:
            self.reply(text)

    def __init_operations(self):
        """
        Generate all operations from self.plugin_ids
        """
        for plugin_id in self.plugin_ids:
            if is_plugin_loaded(plugin_id):
                if not self.upgrade:
                    self.reply(tr('install.already_installed', plugin_id))
                result = cache.get_plugin_by_id(plugin_id).meta.check_update()
                if not result.is_latest:
                    self.reply(tr(
                        'install.newer_version_available',
                        plugin_id,
                        result.latest_version
                    ))
                    self.upgrade = True
                else:
                    self.reply(tr('install.already_up_to_date', plugin_id))
                    continue
            for operation in get_operations(
                    plugin_id, DependencyOperation.UPGRADE if self.upgrade else DependencyOperation.INSTALL
            ):
                if operation.name not in [op.name for op in self.operations]:
                    self.operations.append(operation)
        return len(self.operations) != 0

    def __format_plugins_confirm(self) -> Optional[RTextBase]:
        ops = [op for op in self.operations if isinstance(op, InstallPluginOperation)]
        if len(ops) == 0:
            return None
        return RTextList(
            tr('install.confirm.plugin_list'),
            new_line(),
            insert_between([
                RText(op.name).set_color(
                    RColor.dark_aqua if op.operation == DependencyOperation.INSTALL else RColor.aqua
                ) for op in ops],
                insertion=RText(', ')
            )
        )

    def __format_packages_confirm(self) -> Optional[RTextBase]:
        ops = [op for op in self.operations if isinstance(op, InstallPackageOperation)]
        if len(ops) == 0:
            return None
        return RTextList(
            tr('install.confirm.package_list'),
            new_line(),
            insert_between([
                RText(op.name).set_color(
                    RColor.dark_aqua if op.operation == DependencyOperation.INSTALL else RColor.aqua
                ) for op in ops],
                insertion=RText(', ')
            )
        )

    def __show_confirm(self):
        self.reply(tr(
            'install.confirm.title',
            tr('dependency.operation.upgrade') if self.upgrade else tr('dependency.operation.install')
        ))

        self.__reply_if_present(self.__format_plugins_confirm())
        self.__reply_if_present(self.__format_packages_confirm())

        self.reply(tr('install.confirm.footer', CONFIRM_COMMAND_TEXT))

    @new_thread('MPMInstall')
    def run(self):
        results = []
        for operation in self.operations:
            self.reply(tr('install.operating', tr(operation.operation.value), operation.name))
            results.append(operation.operate(self))
        if all(results):
            self.reply(tr('install.operation.reload_mcdr'))
            psi.refresh_changed_plugins()
            self.reply(tr('install.result.success'))
        else:
            self.reply(tr('install.result.failed'))
