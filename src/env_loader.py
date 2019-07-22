import logging
import os
from os.path import join, dirname, abspath

from dotenv import load_dotenv


class EnvLoader:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    @staticmethod
    def from_file():
        dotenv_path = abspath(join(dirname(__file__), '..', '.env'))
        load_dotenv(dotenv_path)

    def get(self, env_name: str, default: str = '', sensitive: bool = False) -> str:
        return self._get_env(env_name, default, sensitive)

    def get_required(self, env_name: str, default: str = '', sensitive: bool = False) -> str:
        val = self._get_env(env_name, default, sensitive)

        if val == '':
            self._logger.critical('Required envvar is missing: %s', {
                'name': env_name
            })
            exit(1)

        if val == default:
            self._logger.warning('Default value used for required envvar: %s', {
                'name': env_name,
                'value': self._mask_value(val, sensitive)
            })

        return val

    def _get_env(self, env_name: str, default: str = '', sensitive: bool = False) -> str:
        res = os.getenv(env_name, default).strip()

        self._logger.debug('Envvar: %s', {
            'name': env_name,
            'value': self._mask_value(res, sensitive)
        })

        return res

    @staticmethod
    def _mask_value(value: str, sensitive: bool = False) -> str:
        return value if not sensitive else value[:3] + '*' * (len(value) - 6) + value[-3:]
