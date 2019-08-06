from dto import PluralFormsDto, DurationDto


class TelegramChatType:
    SUPER_GROUP = 'supergroup'


class TelegramParseMode:
    MARKDOWN = 'Markdown'
    HTML = 'HTML'


class LoggingSettings:
    RECORD_FORMAT = '%(asctime)s %(levelname)s %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    DEFAULT_LEVEL = 'INFO'


class EnvVar:
    TELEGRAM_TOKEN = 'TELEGRAM_TOKEN'
    TELEGRAM_CHAT_ID = 'TELEGRAM_CHAT_ID'
    LOGGING_LEVEL = 'LOGGING_LEVEL'


class RestrictCommand:
    RO = '!ro'
    TO = '!to'


class RestrictDuration:
    DEFAULT_DURATION = 5
    DEFAULT_UNIT = 'm'

    UNSAFE_DURATION_SECONDS = 40

    MIN_DURATION = DurationDto(5, '5 секунд')
    MAX_DURATION = DurationDto(864000, '10 дней')

    SECONDS_SETTINGS = dict(rate=1, plural_forms=PluralFormsDto(form_1='секунду', form_2='секунды', form_3='секунд'))
    MINUTES_SETTINGS = dict(rate=60, plural_forms=PluralFormsDto(form_1='минуту', form_2='минуты', form_3='минут'))
    HOURS_SETTINGS = dict(rate=3600, plural_forms=PluralFormsDto(form_1='час', form_2='часа', form_3='часов'))
    DAYS_SETTINGS = dict(rate=86400, plural_forms=PluralFormsDto(form_1='день', form_2='дня', form_3='дней'))

    UNITS = dict(
        s=SECONDS_SETTINGS,
        m=MINUTES_SETTINGS,
        h=HOURS_SETTINGS,
        d=DAYS_SETTINGS,
    )


class BanDuration:
    DURATION_SECONDS = 60


class MessageSettings:
    SELF_DESTRUCT_TIMEOUT = 5


class NotificationTemplateList:
    READ_ONLY = [
        '{first_name} помещен в read-only на {duration_text}.',
        '{first_name} завалил ебало на {duration_text}.',
        '{first_name} выпил высокий стакан ебалозавалина, которого хватит на {duration_text}.',
        '{first_name} не будет пиздеть ещё {duration_text}.',
        '{first_name} сможет дальше пиздеть только через {duration_text}.',
    ]

    TEXT_ONLY = [
        '{first_name} помещен в text-only на {duration_text}.',
        '{first_name} не будет постить уебанские картиночки {duration_text}.',
    ]

    TIMEOUT_KICK = [
        '{first_name} пиздует из чата, потому что не ответил на вопрос.',
        'Вопрос был довольно простой. {first_name} ведёт себя, как бот.',
        '{first_name} слишком долго тупит. Здесь таких не держат.',
    ]
