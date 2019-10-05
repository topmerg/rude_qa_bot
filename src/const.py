from dto import PluralFormsDto, DurationDto


class TelegramChatType:
    SUPER_GROUP = 'supergroup'


class TelegramParseMode:
    MARKDOWN = 'Markdown'
    HTML = 'HTML'


class TelegramMemberStatus:
    CREATOR = 'creator'
    ADMINISTRATOR = 'administrator'
    MEMBER = 'member'
    RESTRICTED = 'restricted'
    LEFT = 'left'
    KICKED = 'kicked'


class LoggingSettings:
    RECORD_FORMAT = '%(asctime)s %(levelname)s %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    DEFAULT_LEVEL = 'INFO'


class EnvVar:
    TELEGRAM_TOKEN = 'TELEGRAM_TOKEN'
    TELEGRAM_CHAT_ID = 'TELEGRAM_CHAT_ID'
    LOGGING_LEVEL = 'LOGGING_LEVEL'


class ChatCommand:
    RO = '!ro'
    TO = '!to'
    RW = '!rw'
    BAN = '!ban'
    PASS = '!pass'


class BaseDuration:
    DEFAULT_DURATION = None
    DEFAULT_UNIT = None
    MIN_DURATION = None
    MAX_DURATION = None

    SECONDS_SETTINGS = dict(rate=1, plural_forms=PluralFormsDto(form_1='секунду', form_2='секунды', form_3='секунд'))
    MINUTES_SETTINGS = dict(rate=60, plural_forms=PluralFormsDto(form_1='минуту', form_2='минуты', form_3='минут'))
    HOURS_SETTINGS = dict(rate=3600, plural_forms=PluralFormsDto(form_1='час', form_2='часа', form_3='часов'))
    DAYS_SETTINGS = dict(rate=86400, plural_forms=PluralFormsDto(form_1='день', form_2='дня', form_3='дней'))
    YEARS_SETTINGS = dict(rate=31536000, plural_forms=PluralFormsDto(form_1='год', form_2='года', form_3='лет'))

    UNITS = dict(
        s=SECONDS_SETTINGS,
        m=MINUTES_SETTINGS,
        h=HOURS_SETTINGS,
        d=DAYS_SETTINGS,
        y=YEARS_SETTINGS,
    )


class PunishmentDuration(BaseDuration):
    DURATION = DurationDto(300, '5 минут')


class RestrictDuration(BaseDuration):
    DEFAULT_DURATION = 5
    DEFAULT_UNIT = 'm'

    UNSAFE_DURATION_SECONDS = 40

    MIN_DURATION = DurationDto(5, '5 секунд')
    MAX_DURATION = DurationDto(864000, '10 дней')


class BanDuration(BaseDuration):
    AUTO_KICK_DURATION_SECONDS = 60

    DEFAULT_DURATION = -1
    DEFAULT_UNIT = 's'

    MIN_DURATION = DurationDto(0, 'навсегда')
    MAX_DURATION = DurationDto(315360000, '10 лет')


class MessageSettings:
    SELF_DESTRUCT_TIMEOUT = 5


class NotificationTemplateList:
    READ_ONLY = [
        '{first_name} помещен в read-only на {duration_text}.',
        '{first_name} утомил всех и лишился права голоса на {duration_text}.',
        '{first_name} идет поработать на {duration_text}.',
        'Мы не услышим {first_name} еще {duration_text}.',
        '{first_name} отправился подумать над своим поведением {duration_text}.',
    ]

    TEXT_ONLY = [
        '{first_name} помещен в text-only на {duration_text}.',
        '{first_name} обойдется без стикеров {duration_text}.',
        '{first_name} учится выражать свои мысли словами {duration_text}.',
        '{first_name} отправился в путешествие за нормальными стикерами, вернется через {duration_text}.'
    ]

    READ_WRITE = [
        '{first_name} избавлен от всех наказаний.',
        '{first_name} вышел по амнистии.',
    ]

    TIMEOUT_KICK = [
        '{first_name} покидает чат, потому что не ответил на вопрос.',
        'Вопрос был довольно простой. {first_name} ведёт себя, как бот.',
        '{first_name} слишком долго тупит. Здесь таких не держат.',
    ]

    BAN_KICK = [
        '{first_name} удаляется из чата {duration_text}.',
    ]

    UNAUTHORIZED_PUNISHMENT = [
        '{first_name} думал, что ему все можно и получил read-only.',
        '{first_name}, команды администраторов - не для простых смертных.',
        '{first_name}, Quod licet Iovi, non licet bovi.'
    ]
