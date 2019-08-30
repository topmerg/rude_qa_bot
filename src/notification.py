from copy import copy
from random import shuffle
from typing import Dict, List

from const import NotificationTemplateList


class Notification:
    _notification: Dict[str, List[str]]

    def __init__(self):
        self._notification = dict()

    def _init_list(self, list_name: str, source_list: list):
        self._notification[list_name] = copy(source_list)
        shuffle(self._notification[list_name])

    def _get_notification(self, list_name: str, source_list: list) -> str:
        self._notification.setdefault(list_name, list())
        if len(self._notification[list_name]) == 0:
            self._init_list(list_name, source_list)
        return self._notification[list_name].pop()

    def read_only(self, first_name: str, duration_text: str) -> str:
        template = self._get_notification('read_only', NotificationTemplateList.READ_ONLY)

        return template.format(
            first_name=first_name,
            duration_text=duration_text,
        )

    def text_only(self, first_name: str, duration_text: str) -> str:
        template = self._get_notification('text_only', NotificationTemplateList.TEXT_ONLY)

        return template.format(
            first_name=first_name,
            duration_text=duration_text,
        )

    def read_write(self, first_name: str) -> str:
        template = self._get_notification('read_write', NotificationTemplateList.READ_WRITE)

        return template.format(first_name=first_name)

    def timeout_kick(self, first_name: str) -> str:
        template = self._get_notification('timeout_kick', NotificationTemplateList.TIMEOUT_KICK)

        return template.format(
            first_name=first_name,
        )

    def ban_kick(self, first_name: str, duration_text: str) -> str:
        template = self._get_notification('ban_kick', NotificationTemplateList.BAN_KICK)

        return template.format(
            first_name=first_name,
            duration_text=duration_text,
        )

    def unauthorized_punishment(self, first_name: str) -> str:
        template = self._get_notification('unauthorized_punishment', NotificationTemplateList.UNAUTHORIZED_PUNISHMENT)

        return template.format(
            first_name=first_name,
        )
