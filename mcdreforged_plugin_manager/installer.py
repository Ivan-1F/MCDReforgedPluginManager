from typing import List, Tuple

from mcdreforged.api.all import *

from mcdreforged_plugin_manager.dependency_checker import PluginDependencyChecker, PackageDependencyChecker, \
    DependencyError, DependencyOperation
from mcdreforged_plugin_manager.util.cache import cache
from mcdreforged_plugin_manager.util.misc import parse_python_requirement
from mcdreforged_plugin_manager.util.text_util import command_run
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


class PluginInstaller:
    def __init__(self, plugin_id: str, source: CommandSource):
        self.meta = cache.get_plugin_by_id(plugin_id)
        self.reply = source.reply
        self.server = source.get_server()

    def is_installed(self):
        return self.meta.is_installed()

    def show_confirm(self):
        if self.is_installed():
            self.reply(tr('installer.already_installed'))
        else:
            self.reply(tr('installer.confirm.title'))
            operate_plugins, operate_packages = self.get_operate_dependencies()
            if len(operate_plugins) > 0:
                self.reply(tr('installer.confirm.plugin_list'))
                self.reply(', '.join([RText(name).set_color(
                    RColor.dark_aqua if op == DependencyOperation.INSTALL else RColor.aqua
                ).to_colored_text() for name, op in operate_plugins]))
            if len(operate_packages) > 0:
                self.reply(tr('installer.confirm.package_list'))
                self.reply(', '.join([RText(name).set_color(
                    RColor.dark_aqua if op == DependencyOperation.INSTALL else RColor.aqua
                ).to_colored_text() for name, op in operate_packages]))

            self.reply(tr('installer.confirm.footer', command_run('!!mpm confirm', '!!mpm confirm')))

    def get_operate_dependencies(self):
        return get_operate_dependencies(self.meta.id)

    def install(self):
        self.show_confirm()
