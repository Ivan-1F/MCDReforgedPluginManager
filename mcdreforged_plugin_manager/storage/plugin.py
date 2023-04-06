from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Iterable, TypeVar, Type, Callable

from mcdreforged.minecraft.rtext.style import RColor
from mcdreforged.minecraft.rtext.text import RText, RTextList, RTextBase
from mcdreforged.plugin.meta.version import Version
from mcdreforged.utils.serializer import Serializable

from mcdreforged_plugin_manager import constants
from mcdreforged_plugin_manager.constants import psi, PLUGIN_LABELS
from mcdreforged_plugin_manager.dependency_checker import DependencyChecker, DependencyNotFound, InvalidDependency, \
    DependencyNotMet, PackageDependencyChecker, PluginDependencyChecker
from mcdreforged_plugin_manager.storage.release import ReleaseSummary
from mcdreforged_plugin_manager.util.mcdr_util import is_plugin_loaded
from mcdreforged_plugin_manager.util.misc_util import parse_python_requirement
from mcdreforged_plugin_manager.util.text_util import command_run, link, new_line, parse_markdown, insert_new_lines, \
    bold
from mcdreforged_plugin_manager.util.translation_util import tr


@dataclass
class CheckUpdateResult:
    is_latest: bool
    latest_version: Version
    local_version: Optional[Version]  # None if plugin is not installed


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
        """
        If the plugin has no description, return translated no description text,
        otherwise return the markdown formatted plugin description in mcdr language
        """
        if not self.description:
            return tr('plugin.no_description')
        language = psi.get_mcdr_language()
        text = self.description.get(language)
        if text is None:
            text = list(self.description.values())[0]
        return parse_markdown(text)

    def __get_version_text(self) -> RTextBase:
        """
        Return the version text in the format of (id@version) in gray color
        """
        return RText('({}@{})'.format(self.id, self.version), RColor.gray)

    def __get_primary_action_button(self):
        """
        Return the primary action button (install or uninstall)
        """
        if is_plugin_loaded(self.id):
            return command_run('[x]',
                               '{} uninstall {}'.format(constants.PREFIX, self.id),
                               tr('plugin.operation.uninstall')).set_color(RColor.red)
        else:
            return command_run('[↓]',
                               '{} install {}'.format(constants.PREFIX, self.id),
                               tr('plugin.operation.install')).set_color(RColor.green)

    def __get_upgrade_action_button(self):
        """
        If the plugin can be upgraded, return the upgrade action button, otherwise return an empty RText
        """
        result = self.check_update()
        if result.is_latest:
            return RText('')
        else:
            return command_run('[↑]',
                               '{} upgrade {}'.format(constants.PREFIX, self.id),
                               tr('plugin.operation.upgrade', result.latest_version)).set_color(RColor.green)

    def __get_info_action_button(self):
        return command_run('[i]',
                           '{} info {}'.format(constants.PREFIX, self.id),
                           tr('plugin.operation.show_info')).set_color(RColor.aqua)

    def __get_action_bar(self) -> RTextList:
        """
        Return the action bar including the primary action button, the info action button,
        and the upgrade action button (if exist)
        """
        return RTextList(
            self.__get_primary_action_button(),
            self.__get_info_action_button(),
            self.__get_upgrade_action_button()
        )

    @property
    def brief(self) -> RTextList:
        """
        Get brief plugin info (used in !!mpm list)
        """
        return RTextList(
            self.__get_action_bar(),
            new_line(),
            self.format()
        )

    @property
    def detail(self) -> RTextBase:
        """
        Get detailed plugin info (used in !!mpm info)
        """
        text = self.brief
        if len(self.dependencies.items()) != 0:
            text.append(new_line())
            text.append(bold(tr('plugin.detail.dependency')))
            text.append(new_line())
            text.append(self.__get_formatted_dependencies())
        if len(self.requirements) != 0:
            text.append(new_line())
            text.append(bold(tr('plugin.detail.requirement')))
            text.append(new_line())
            text.append(self.__get_formatted_requirements())
        return text

    def __get_status_text(self):
        """
        Return the status text indicates whether the plugin is installed
        """
        if is_plugin_loaded(self.id):
            return tr('plugin.status.installed', psi.get_plugin_metadata(self.id).version)
        else:
            return tr('plugin.status.uninstalled')

    def format(self) -> RTextList:
        """
        Format plugin meta info
        """
        return RTextList(
            RTextList(
                link(RText(self.name), self.repository),
                ' ',
                self.__get_version_text(),
                ' ',
                self.__get_status_text(),
            ),
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
        """
        Format dependencies (or requirements) into colored user-friendly text
        :param checker: the dependency checker
        :param dependencies: the key is the dependency name and the value is the version requirement
        :param prefix: the prefix in front of each line of dependency
        """
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

    def check_update(self) -> CheckUpdateResult:
        latest_version = Version(self.version)
        if is_plugin_loaded(self.id):
            local_version = psi.get_plugin_metadata(self.id).version
            if latest_version > local_version:
                return CheckUpdateResult(False, latest_version, local_version)
        return CheckUpdateResult(True, latest_version, None)


class Plugin(Serializable):
    meta: MetaInfo
    release: ReleaseSummary

    @classmethod
    def create(cls, plugin_json: dict, meta_json: dict, release_json: dict):
        """
        Create a plugin from a folder contains `plugin.json`, `meta.json` and `release.json`
        of PluginCatalogue `meta` branch

        :param plugin_json: plugin.json
        :param meta_json: meta.json
        :param release_json: release.json
        :return:
        """
        meta = MetaInfo.deserialize(meta_json)
        meta.labels = plugin_json['labels']

        release = ReleaseSummary.deserialize(release_json)

        return cls(meta=meta, release=release)


class PluginStorage(Serializable):
    plugin_amount: int = 0
    plugins: Dict[str, Plugin] = {}  # plugin id -> plugin

    def get_plugins_by_labels(self, labels: Optional[Union[None, str, List[str]]] = None) -> Iterable[Plugin]:
        if labels is None:
            labels = PLUGIN_LABELS
        if isinstance(labels, str):
            labels = [labels]
        for plugin in self.plugins.values():
            if any([label in labels for label in plugin.meta.labels]):
                yield plugin

    def search(self, query: str) -> Iterable[MetaInfo]:
        for plugin in self.plugins.values():
            if query in plugin.meta.name or query in plugin.meta.id or query in plugin.meta.description:
                yield plugin

    def is_plugin_present(self, plugin_id: str) -> bool:
        return plugin_id in self.plugins.keys()

    def get_plugin_by_id(self, plugin_id: str) -> Optional[Plugin]:
        return self.plugins.get(plugin_id)

    def get_plugin_ids(self) -> List[str]:
        return list(self.plugins.keys())
