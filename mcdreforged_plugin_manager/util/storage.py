from typing import List, Dict, Optional, Union, Callable

import requests
from mcdreforged.api.all import *

from mcdreforged_plugin_manager.config import config
from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.util.denpendency_util import check_dependency, DependencyNotFound, DependencyNotMet, \
    check_requirement, InvalidDependency
from mcdreforged_plugin_manager.util.misc import parse_python_requirement
from mcdreforged_plugin_manager.util.text_util import italic, parse_markdown, command_run, link, new_line, \
    insert_new_lines, time, size, bold
from mcdreforged_plugin_manager.util.translation import tr


class AssetInfo(Serializable):
    name: str
    size: int
    download_count: int
    created_at: str
    browser_download_url: str


class ReleaseInfo(Serializable):
    url: str
    name: str
    tag_name: str
    created_at: str
    assets: List[AssetInfo]
    description: str
    prerelease: bool

    def get_mcdr_assets(self) -> List[AssetInfo]:
        return [asset for asset in self.assets if asset.name.endswith('.mcdr') or asset.name.endswith('.pyz')]


class ReleaseSummary(Serializable):
    schema_version: int = None
    id: str
    latest_version: str
    etag: str = ''
    releases: List[ReleaseInfo]

    @classmethod
    def of(cls, plugin_id: str):
        try:
            data = requests.get('{}/{}/release.json'.format(config.get_source, plugin_id), timeout=config.timeout).json()
            return cls.deserialize(data)
        except requests.RequestException as e:
            psi.logger.warning(tr('cache.release.exception', plugin_id, e))
            return None


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
    release_summary: Optional[ReleaseSummary]

    @property
    def formatted_description(self) -> RTextBase:
        if not self.description:
            return italic(tr('plugin.no_description'))
        language = psi.get_mcdr_language()
        text = self.description.get(language)
        if text is None:
            text = list(self.description.values())[0]
        return parse_markdown(text)

    @property
    def version_text(self):
        return RText('({}@{})'.format(self.id, self.version), RColor.gray)

    @property
    def action_bar(self):
        return RTextList(
            command_run('[↓]', '!!mpm install {}'.format(self.id), tr('plugin.operation.install')).set_color(
                RColor.green),
            command_run('[i]', '!!mpm info {}'.format(self.id), tr('plugin.operation.show_info')).set_color(RColor.aqua)
        )

    @property
    def brief(self):
        return RTextList(
            self.action_bar,
            new_line(),
            self.format
        )

    @property
    def format(self):
        return RTextList(
            RTextList('- ', link(RText(self.name), self.repository), ' ', self.version_text),
            new_line(),
            tr('plugin.author', ', '.join(self.authors)),
            new_line(),
            tr('plugin.label', ', '.join(self.labels)),
            new_line(),
            self.formatted_description,
        )

    @staticmethod
    def format_dependencies(check: Callable[[str, str], None], dependencies: Dict[str, str]):
        result: List[RTextBase] = []
        for item, requirement in dependencies.items():
            item_text = RText(item)
            requirement_text = RText(requirement)
            try:
                check(item, requirement)
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
                    item_text,
                    ' | ',
                    requirement_text
                ))
        return insert_new_lines(result)

    def get_release_summary(self):
        return ReleaseSummary.of(self.id) if self.release_summary is None else self.release_summary

    @property
    def formatted_releases(self):
        result: List[RTextBase] = []
        for release in self.get_release_summary().releases:
            for asset in release.get_mcdr_assets():
                asset_text = RTextList(
                    link(asset.name, release.url), ' | ', size(asset.size), ' | ',
                    command_run(
                        '[↓]',
                        '!!mpm install {} {}'.format(self.id, release.tag_name),
                        tr('plugin.operation.install')
                    ).set_color(RColor.green)
                )
                result.append(asset_text)
        return insert_new_lines(result)

    @property
    def detail(self):
        brief = self.format
        if len(self.dependencies.items()) != 0:
            brief.append(new_line())
            brief.append(bold(tr('plugin.detail.dependency')))
            brief.append(new_line())
            brief.append(self.formatted_dependencies)
        if len(self.requirements) != 0:
            brief.append(new_line())
            brief.append(bold(tr('plugin.detail.requirement')))
            brief.append(new_line())
            brief.append(self.formatted_requirements)
        brief.append(new_line())
        brief.append(bold(tr('plugin.detail.release')))
        brief.append(new_line())
        brief.append(self.formatted_releases)
        return brief

    @property
    def formatted_requirements(self):
        requirements = {parse_python_requirement(requirement)[0]: parse_python_requirement(requirement)[1]
                        for requirement in self.requirements}
        return self.format_dependencies(check_requirement, requirements)

    @property
    def formatted_dependencies(self):
        return self.format_dependencies(check_dependency, self.dependencies)


class PluginMetaInfoStorage(Serializable):
    plugin_amount: int = 0
    plugins: Dict[str, MetaInfo] = {}  # plugin id -> plugin meta

    def get_plugins_by_labels(self, labels: Optional[Union[type(None), str, List[str]]] = None):
        if labels is None:
            labels = ['information', 'tool', 'management', 'api']
        if isinstance(labels, str):
            labels = [labels]
        for plugin in self.plugins.values():
            if any([label in labels for label in plugin.labels]):
                yield plugin

    def search(self, query: str):
        for plugin in self.plugins.values():
            if query in plugin.name or query in plugin.id:
                yield plugin

    def is_plugin_present(self, plugin_id: str):
        return plugin_id in self.plugins.keys()

    def get_plugin_by_id(self, plugin_id: str):
        return self.plugins.get(plugin_id)

    def get_plugin_ids(self):
        return self.plugins.keys()
