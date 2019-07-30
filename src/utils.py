from telebot.types import User

from const import RestrictDuration
from dto import DurationDto, PluralFormsDto
from error import ParseBanDurationError


class BotUtils:
    _chat_id: int

    def __init__(self, chat_id: str):
        self._chat_id = int(chat_id)

    @property
    def chat_id(self) -> int:
        return self._chat_id

    @staticmethod
    def prepare_query(text: str) -> str:
        """
        Get text without command

        example: prepare_query("/getUser rudeboy from rude qa") -> returns "rudeboy from rude qa"
        """
        return ' '.join(text.split()[1:])

    def get_duration(self, text: str) -> DurationDto:
        if text == '':
            return self.get_duration(f'{RestrictDuration.DEFAULT_DURATION}{RestrictDuration.DEFAULT_UNIT}')

        try:
            amount = int(text)
            return self.get_duration(f'{amount}{RestrictDuration.DEFAULT_UNIT}')
        except ValueError:
            pass

        try:
            amount = int(text[:-1])
            unit = RestrictDuration.UNITS[text[-1]]

            duration_seconds = int(amount * unit['rate'])

            if duration_seconds < RestrictDuration.MIN_DURATION.seconds:
                return RestrictDuration.MIN_DURATION

            if duration_seconds > RestrictDuration.MAX_DURATION.seconds:
                return RestrictDuration.MAX_DURATION

            duration_unit = self.get_plural(amount, unit['plural_forms'])

            return DurationDto(
                seconds=duration_seconds,
                text=f'{amount} {duration_unit}',
            )
        except (ValueError, KeyError, IndexError):
            raise ParseBanDurationError

    @staticmethod
    def get_plural(amount: int, plural_forms: PluralFormsDto) -> str:
        if amount % 10 == 1 and amount % 100 != 11:
            return plural_forms.form_1

        if 2 <= amount % 10 <= 4 and (amount % 100 < 10 or amount % 100 >= 20):
            return plural_forms.form_2

        return plural_forms.form_3

    @staticmethod
    def mention(user: User):
        return f'[{user.first_name}](tg://user?id={user.id})'
