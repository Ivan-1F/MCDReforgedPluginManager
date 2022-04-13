from typing import List, Dict, Optional, Union

from mcdreforged.api.all import *

from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.util.denpendency_util import check_dependency, DependencyNotFound, DependencyNotMet
from mcdreforged_plugin_manager.util.text_util import italic, parse_markdown, command_run, link, new_line
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
            command_run('[ⓘ]', '!!mpm info {}'.format(self.id), tr('plugin.operation.show_info')).set_color(RColor.aqua)
        )

    @property
    def brief(self):
        return RTextList(
            self.action_bar,
            '\n',
            RTextList('- ', link(RText(self.name), self.repository), ' ', self.version_text),
            new_line(),
            RTextList(
                tr('plugin.author', ', '.join(self.authors)).set_color(RColor.aqua),
                ' | ',
                tr('plugin.label', ', '.join(self.labels)).set_color(RColor.aqua),
            ),
            new_line(),
            self.formatted_description,
            new_line(),
        )

    @property
    def formatted_dependencies(self):
        result = RTextList()
        for plugin_id, requirement in self.dependencies.items():
            plugin_id_text = RText(plugin_id)
            requirement_text = RText(requirement)
            try:
                check_dependency(plugin_id, requirement)
            except DependencyNotFound as e:
                plugin_id_text.set_color(RColor.red).h(e)
                requirement_text.set_color(RColor.red).h(e)
            except DependencyNotMet as e:
                plugin_id_text.set_color(RColor.green)
                requirement_text.set_color(RColor.red).h(e)
            else:
                plugin_id_text.set_color(RColor.green)
                requirement_text.set_color(RColor.green)
            finally:
                result.append(RTextList(
                    plugin_id_text,
                    ' | ',
                    requirement_text
                ))
                result.append(new_line())
        return result


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