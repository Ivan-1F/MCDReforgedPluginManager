from typing import List, Dict, Optional, Union, Callable

from mcdreforged.api.all import *

from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.util.denpendency_util import check_dependency, DependencyNotFound, DependencyNotMet, \
    check_requirement, InvalidDependency
from mcdreforged_plugin_manager.util.misc import parse_python_requirement
from mcdreforged_plugin_manager.util.text_util import italic, parse_markdown, command_run, link, new_line, \
    insert_new_lines
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

    @property
    def detail(self):
        brief = self.brief
        if len(self.dependencies.items()) != 0:
            brief.append(new_line())
            brief.append(new_line())
            brief.append(tr('plugin.detail.dependency'))
            brief.append(new_line())
            brief.append(self.formatted_dependencies)
        if len(self.requirements) != 0:
            brief.append(new_line())
            brief.append(new_line())
            brief.append(tr('plugin.detail.requirement'))
            brief.append(new_line())
            brief.append(self.formatted_requirements)

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