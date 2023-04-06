from mcdreforged.api.all import *

from abc import ABC
from typing import Optional

from mcdreforged_plugin_manager.util.translation_util import tr


class Task(ABC):
    def init(self):
        """
        Called when initializing the task
        """
        pass

    def run(self):
        """
        Run the task, called after executing !!mpm confirm
        """
        raise NotImplementedError()


class TaskManager:
    def __init__(self):
        self.pending_task: Optional[Task] = None

    def manage_task(self, task: Task):
        self.pending_task = task
        self.pending_task.init()

    def on_confirm(self, source: CommandSource):
        if self.pending_task is None:
            source.reply(tr('task_manager.nothing_to_confirm'))
        else:
            self.pending_task.run()
            self.clear_task()

    def clear_task(self):
        self.pending_task = None


task_manager = TaskManager()
