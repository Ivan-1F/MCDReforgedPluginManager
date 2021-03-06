from typing import List, Dict, Optional, Union, Callable, Type, TypeVar, Tuple, Iterable

import requests
from mcdreforged.api.all import *

from mcdreforged_plugin_manager import constants
from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.dependency_checker import DependencyChecker, DependencyNotFound, InvalidDependency, \
    DependencyNotMet, PackageDependencyChecker, PluginDependencyChecker
from mcdreforged_plugin_manager.storage.release import ReleaseSummary
from mcdreforged_plugin_manager.util.mcdr_util import is_plugin_loaded
from mcdreforged_plugin_manager.util.misc import parse_python_requirement
from mcdreforged_plugin_manager.util.text_util import parse_markdown, command_run, link, new_line, \
    insert_new_lines, size, bold
from mcdreforged_plugin_manager.util.translation import tr


class MetaInfo(Serializable):
    id: str
    name: str
    version: str
    repository: str
    labels: List[str]
    authors: List[str]
    dependencies: Dict[str, str]
    requirements: List[str]
    description: Dict[str, str]

    def __get_formatted_description(self) -> RTextBase:
        if not self.description:
            return tr('plugin.no_description')
        language = psi.get_mcdr_language()
        text = self.description.get(language)
        if text is None:
            text = list(self.description.values())[0]
        return parse_markdown(text)

    def __get_version_text(self) -> RTextBase:
        return RText('({}@{})'.format(self.id, self.version), RColor.gray)

    def __get_primary_action_button(self):
        return (
            command_run('[↓]',
                        '{} install {}'.format(constants.PREFIX, self.id),
                        tr('plugin.operation.install')).set_color(RColor.green)
            if not is_plugin_loaded(self.id) else
            command_run('[x]',
                        '{} uninstall {}'.format(constants.PREFIX, self.id),
                        tr('plugin.operation.uninstall')).set_color(RColor.red)
        )

    def __get_upgrade_action_button(self):
        success, latest_version, _ = self.check_update()
        return command_run('[↑]',
                           '{} upgrade {}'.format(constants.PREFIX, self.id),
                           tr('plugin.operation.upgrade', latest_version)).set_color(RColor.green) if success else RText('')

    def __get_action_bar(self) -> RTextList:
        return RTextList(
            self.__get_primary_action_button(),
            command_run('[i]',
                        '{} info {}'.format(constants.PREFIX, self.id),
                        tr('plugin.operation.show_info')).set_color(RColor.aqua),
            self.__get_upgrade_action_button()
        )

    @property
    def brief(self) -> RTextList:
        return RTextList(
            self.__get_action_bar(),
            new_line(),
            self.format
        )

    def __get_status_text(self):
        return tr('plugin.status.installed', psi.get_plugin_metadata(self.id).version) if is_plugin_loaded(self.id) else tr('plugin.status.uninstalled')

    @property
    def format(self) -> RTextList:
        return RTextList(
            RTextList(link(RText(self.name), self.repository), ' ', self.__get_version_text()),
            ' ', self.__get_status_text(),
            new_line(),
            tr('plugin.author', ', '.join(self.authors)),
            new_line(),
            tr('plugin.label', ', '.join(self.labels)),
            new_line(),
            self.__get_formatted_description(),
        )

    T = TypeVar('T', bound=DependencyChecker)

    @staticmethod
    def __format_dependencies(
            checker: Type[T],
            dependencies: Dict[str, str],
            prefix: Optional[Callable[[str, str], RTextBase]] = None
    ) -> RTextBase:
        result: List[RTextBase] = []
        for item, requirement in dependencies.items():
            item_text = RText(item)
            requirement_text = RText(requirement)
            try:
                checker(item, requirement).check()
            except (DependencyNotFound, InvalidDependency) as e:
                item_text.set_color(RColor.red).h(e)
                requirement_text.set_color(RColor.red).h(e)
            except DependencyNotMet as e:
                item_text.set_color(RColor.green)
                requirement_text.set_color(RColor.red).h(e)
            else:
                item_text.set_color(RColor.green).h(tr('dependency.satisfied'))
                requirement_text.set_color(RColor.green).h(tr('dependency.satisfied'))
            finally:
                result.append(RTextList(
                    prefix(item, requirement),
                    item_text,
                    ' | ',
                    requirement_text
                ))
        return insert_new_lines(result)

    # def get_release_summary(self) -> ReleaseSummary:
    #     return ReleaseSummary.of(self.id)

    # @property
    # def formatted_releases(self) -> RTextBase:
    #     result: List[RTextBase] = []
    #     try:
    #         summary = self.get_release_summary()
    #     except requests.RequestException as e:
    #         return tr('plugin.release.failed_to_get_release', e)
    #     for release in summary.releases:
    #         for asset in release.get_mcdr_assets():
    #             asset_text = RTextList(
    #                 link(asset.name, release.url), ' | ', size(asset.size), ' | ',
    #                 release.tag_name, ' | ',
    #                 command_run(
    #                     '[↓]',
    #                     '!!mpm install {} {}'.format(self.id, release.tag_name),
    #                     tr('plugin.operation.install')
    #                 ).set_color(RColor.green)
    #             )
    #             result.append(asset_text)
    #     return insert_new_lines(result)

    @property
    def detail(self) -> RTextBase:
        brief = self.brief
        if len(self.dependencies.items()) != 0:
            brief.append(new_line())
            brief.append(bold(tr('plugin.detail.dependency')))
            brief.append(new_line())
            brief.append(self.__get_formatted_dependencies())
        if len(self.requirements) != 0:
            brief.append(new_line())
            brief.append(bold(tr('plugin.detail.requirement')))
            brief.append(new_line())
            brief.append(self.__get_formatted_requirements())
        # brief.append(new_line())
        # brief.append(bold(tr('plugin.detail.release')))
        # brief.append(new_line())
        # brief.append(self.formatted_releases)
        return brief

    def __get_formatted_requirements(self) -> RTextBase:
        requirements = {parse_python_requirement(requirement)[0]: parse_python_requirement(requirement)[1]
                        for requirement in self.requirements}
        return self.__format_dependencies(
            PackageDependencyChecker,
            requirements,
            lambda package, requirement: link('- ', 'https://pypi.org/project/' + package).set_styles([])
        )

    def __get_formatted_dependencies(self) -> RTextBase:
        return self.__format_dependencies(
            PluginDependencyChecker,
            self.dependencies,
            lambda plugin_id, requirement: command_run('- ', '{} info {}'.format(constants.PREFIX, plugin_id),
                                                       tr('plugin.operation.show_info'))
        )

    def check_update(self) -> Tuple[bool, Optional[Version], Optional[Version]]:
        if is_plugin_loaded(self.id):
            local_version = psi.get_plugin_metadata(self.id).version
            latest_version = Version(self.version)
            if latest_version > local_version:
                return True, latest_version, local_version
        return False, None, None


class PluginMetaInfoStorage(Serializable):
    plugin_amount: int = 0
    plugins: Dict[str, MetaInfo] = {}  # plugin id -> plugin meta

    def get_plugins_by_labels(self, labels: Optional[Union[type(None), str, List[str]]] = None) -> Iterable[MetaInfo]:
        if labels is None:
            labels = ['information', 'tool', 'management', 'api']
        if isinstance(labels, str):
            labels = [labels]
        for plugin in self.plugins.values():
            if any([label in labels for label in plugin.labels]):
                yield plugin

    def search(self, query: str) -> Iterable[MetaInfo]:
        for plugin in self.plugins.values():
            if query in plugin.name or query in plugin.id or query in plugin.description:
                yield plugin

    def is_plugin_present(self, plugin_id: str) -> bool:
        return plugin_id in self.plugins.keys()

    def get_plugin_by_id(self, plugin_id: str) -> MetaInfo:
        return self.plugins.get(plugin_id)

    def get_plugin_ids(self) -> List[str]:
        return list(self.plugins.keys())
