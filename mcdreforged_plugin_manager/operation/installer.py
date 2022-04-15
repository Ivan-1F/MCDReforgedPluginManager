import subprocess
import sys
from typing import List, Tuple
from urllib.request import urlretrieve

from mcdreforged.api.all import *

from mcdreforged_plugin_manager.dependency_checker import PluginDependencyChecker, PackageDependencyChecker, \
    DependencyError, DependencyOperation
from mcdreforged_plugin_manager.operation.task_manager import Task
from mcdreforged_plugin_manager.util.cache import cache
from mcdreforged_plugin_manager.util.misc import parse_python_requirement
from mcdreforged_plugin_manager.util.storage import ReleaseSummary
from mcdreforged_plugin_manager.util.text_util import command_run, insert_between
from mcdreforged_plugin_manager.util.translation import tr

Operation = Tuple[str, DependencyOperation]


def get_operate_dependencies(plugin_id: str):
    def get_operate_packages(requirements: List[str]):
        """
        Get operate packages from raw requirement list
        """
        result: List[Operation] = []
        for item in requirements:
            parsed = parse_python_requirement(item)
            package_checker = PackageDependencyChecker(*parsed)
            try:
                package_checker.check()
            except DependencyError:
                if package_checker.get_operation() != DependencyOperation.IGNORE:
                    result.append((parsed[0], package_checker.get_operation()))
        return result

    meta = cache.get_plugin_by_id(plugin_id)
    plugins: List[Operation] = [(plugin_id, DependencyOperation.INSTALL)]
    packages: List[Operation] = get_operate_packages(meta.requirements)
    for dep_id, requirement in meta.dependencies.items():
        plugin_checker = PluginDependencyChecker(dep_id, requirement)
        try:
            # the dependency is satisfied, ignore further dependency checking
            plugin_checker.check()
        except DependencyError:
            # the dependency is not satisfied, add its dependency then
            dep_plugins, dep_packages = get_operate_dependencies(dep_id)
            plugins = [*plugins, *dep_plugins]
            packages = [*packages, *dep_packages]
    return plugins, packages


class PluginInstaller(Task):
    def __init__(self, plugin_id: str, source: CommandSource):
        self.meta = cache.get_plugin_by_id(plugin_id)
        self.reply = source.reply
        self.server = source.get_server()
        self.operate_plugins: List[Operation] = []
        self.operate_packages: List[Operation] = []
        super().__init__()

    def is_installed(self):
        return self.meta.is_installed()

    def show_confirm(self):
        if self.is_installed():
            self.reply(tr('installer.already_installed'))
        else:
            self.reply(tr('installer.confirm.title'))
            operate_plugins, operate_packages = self.get_operate_dependencies()
            self.operate_plugins, self.operate_packages = operate_plugins, operate_packages
            if len(operate_plugins) > 0:
                self.reply(tr('installer.confirm.plugin_list'))
                self.reply(insert_between([RText(name).set_color(
                    RColor.dark_aqua if op == DependencyOperation.INSTALL else RColor.aqua
                ) for name, op in operate_plugins], insertion=RText(', ')))
            if len(operate_packages) > 0:
                self.reply(tr('installer.confirm.package_list'))
                self.reply(insert_between([RText(name).set_color(
                    RColor.dark_aqua if op == DependencyOperation.INSTALL else RColor.aqua
                ) for name, op in operate_packages], insertion=RText(', ')))

            self.reply(tr('installer.confirm.footer', command_run('!!mpm confirm', '!!mpm confirm', tr('installer.confirm.command_hover'))))

    def get_operate_dependencies(self):
        return get_operate_dependencies(self.meta.id)

    def get_installed_plugin_file(self, plugin_id: str):
        return self.server.get_plugin_file_path(plugin_id)

    def _run(self):
        for plugin, op in self.operate_plugins:
            if op == DependencyOperation.INSTALL:
                release = ReleaseSummary.of(plugin).get_latest_release()
                self.reply(tr('installer.install.downloading', release.get_mcdr_assets()[0].name))
                url = release.get_mcdr_assets()[0].browser_download_url
                urlretrieve(url, './plugins/' + release.get_mcdr_assets()[0].name)
            elif op == DependencyOperation.UPGRADE:
                pass
        self.open_pip_process([package for package, op in self.operate_packages])

    def open_pip_process(self, packages: List[str]):
        params = [sys.executable, '-m', 'pip', 'install', '-U', *packages]
        self.reply(tr('installer.install.pip.install', ', '.join(packages)))
        try:
            subprocess.check_call(params)
        except subprocess.CalledProcessError as e:
            self.reply(tr('installer.install.pip.error', e))

    def init(self):
        self.show_confirm()
