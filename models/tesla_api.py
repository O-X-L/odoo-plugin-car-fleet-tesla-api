from time import time
from pathlib import Path
from tempfile import gettempdir
from sys import platform
from os import open as open_file
from json import JSONDecodeError
from json import loads as json_loads
from json import dumps as json_dumps
from datetime import timedelta

import requests

LINUX = platform.lower() == 'linux'
TMP_DIR = Path(gettempdir())
FILE_TOKEN_CACHE = TMP_DIR / 'odoo_tesla_token.json'
FILE_VEHICLE_CACHE = TMP_DIR / 'odoo_tesla_vehicles.json'
DEFAULT_OFFLINE_RETRY_INTERVAL = 10 * 60
DEFAULT_VEHICLE_CACHE_TIME = 5 * 60
SETTING_DEFAULTS = {
    'vehicle_cache_time': DEFAULT_VEHICLE_CACHE_TIME,
    'offline_retry_interval': DEFAULT_OFFLINE_RETRY_INTERVAL,
}

LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
URL_AUTH = 'https://auth.tesla.com/oauth2/v3/token'
REGION_ALIASES = {
    'africa': 'europe',
    'middle_east': 'europe',
    'asia': 'america',
}
SERVERS = {
    'europe': 'https://fleet-api.prd.eu.vn.cloud.tesla.com',
    'america': 'https://fleet-api.prd.na.vn.cloud.tesla.com',
    'china': 'https://fleet-api.prd.cn.vn.cloud.tesla.cn',
}

TIME_MAP = {
    'month': timedelta(days=30),
    'week': timedelta(weeks=1),
    'day': timedelta(days=1),
    'hour': timedelta(hours=1),
    '30m': timedelta(minutes=30),
    '15m': timedelta(minutes=15),
    '10m': timedelta(minutes=10),
    '5m': timedelta(minutes=5),
    'none': None,
}
RETRY_MAP = {
    'month': timedelta(hours=4),
    'week': timedelta(hours=3),
    'day': timedelta(hours=1),
    'hour': timedelta(minutes=10),
    '30m': timedelta(minutes=10),
    '15m': timedelta(minutes=1),
    '10m': timedelta(minutes=1),
    '5m': timedelta(minutes=1),
    'none': None,
}


class APIErrorOffline(ConnectionError):
    pass


class APIErrorStatus(ConnectionError):
    pass


def _get_regional_server(odoo_env) -> str:
    region = odoo_env['ir.config_parameter'].sudo().get_param('oxl_fleet_tesla.region')
    if region in REGION_ALIASES:
        region = REGION_ALIASES[region]

    return SERVERS[region]


def build_url(odoo_env, endpoint: str) -> str:
    return f'{_get_regional_server(odoo_env)}/api/1/{endpoint}'


class TeslaAPI:
    def __init__(self, odoo_env):
        self.odoo_env = odoo_env
        self.api_token = None
        self.api_token_expiration = int(time())
        self.vehicles = {}
        self.vehicles_expiration = int(time())
        self.init()

    def init(self):
        if self.odoo_env is not None:
            if self.api_token is None:
                self._load_or_generate_api_token()

            if len(self.vehicles) == 0:
                self.update_vehicles()

    def get_setting(self, setting: str) -> any:
        v = self.odoo_env['ir.config_parameter'].sudo().get_param(
            f'oxl_fleet_tesla.{setting}'
        )

        if not v and setting in SETTING_DEFAULTS:
            return SETTING_DEFAULTS[setting]

        if v is False:
            raise ValueError(f"Setting '{setting}' is not configured!")

        return v

    @property
    def poll_interval(self) -> (timedelta, None):
        return TIME_MAP[self.get_setting('poll_interval')]

    @property
    def retry_interval(self) -> (timedelta, None):
        return RETRY_MAP[self.get_setting('poll_interval')]

    def _log_api_call(self, endpoint: str, url: str, status_code: int = 0, error: str = None, failed: bool = False):
        if error is not None:
            failed = True

        if endpoint.find('/') != -1:
            _, endpoint = endpoint.rsplit('/', 1)

        if endpoint.find('?') != -1:
            endpoint, _ = endpoint.split('?', 1)

        self.odoo_env['oxl.fleet.tesla.protocol'].create({
            'endpoint': endpoint,
            'url': url,
            'status_code': status_code,
            'error': error,
            'failed': failed,
        })

    @staticmethod
    def _open_file_0600(path: (str, Path), flags):
        return open_file(path, flags, 0o600)

    @classmethod
    def _write_file(cls, file: (str, Path), content: str):
        if LINUX:
            with open(file, 'w', encoding='utf-8', opener=cls._open_file_0600) as _file:
                _file.write(content)

        else:
            with open(file, 'w', encoding='utf-8') as _file:
                _file.write(content)

    def _generate_tesla_api_token(self) -> dict:
        try:
            res = requests.post(
                url=URL_AUTH,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.get_setting('client_id'),
                    'client_secret': self.get_setting('client_secret'),
                    'scope': 'vehicle_device_data',
                    'audience': _get_regional_server(self.odoo_env),
                },
                timeout=5,
            )

        except (ConnectionError, TimeoutError, OSError):
            self._log_api_call('auth', url=URL_AUTH, error='Network error')
            raise

        if res.status_code != 200:
            self._log_api_call('auth', url=URL_AUTH, status_code=res.status_code, error='Invalid credentials')
            raise PermissionError(
                'Failed to generate Tesla API-Token! '
                'Make sure the provided credentials are correct!'
            )

        self._log_api_call('auth', url=URL_AUTH, status_code=res.status_code)
        return res.json()

    def _load_or_generate_api_token(self, reauth: bool = False):
        generate = True
        if not reauth:
            try:
                if FILE_TOKEN_CACHE.is_file():
                    with open(FILE_TOKEN_CACHE, 'r', encoding='utf-8') as f:
                        cnf = json_loads(f.read())
                        if cnf['time'] + cnf['expires_in'] > int(time()):
                            generate = False

            except (OSError, JSONDecodeError, KeyError):
                pass

        if generate:
            cnf = self._generate_tesla_api_token()
            cnf['time'] = int(time())
            self._write_file(file=FILE_TOKEN_CACHE, content=json_dumps(cnf))

        self.api_token = cnf['access_token']
        self.api_token_expiration = cnf['time'] + (cnf['expires_in'] - 60)

    def call(self, endpoint: str) -> (dict, None):
        url = build_url(odoo_env=self.odoo_env, endpoint=endpoint)
        try:
            res = requests.get(
                url=url,
                headers={'Authorization': f'Bearer {self.api_token}'},
                timeout=5,
            )

        except (ConnectionError, TimeoutError, OSError):
            self._log_api_call(endpoint, url=url, error='Network error')
            raise

        if res.status_code == 408:
            # tesla is unable to reach the car
            self._log_api_call(endpoint, url=url, status_code=res.status_code, error='Vehicle offline')
            raise APIErrorOffline()

        if res.status_code != 200:
            self._log_api_call(endpoint, url=url, status_code=res.status_code, failed=True)
            raise APIErrorStatus(str(res.status_code))

        self._log_api_call(endpoint, url=url, status_code=res.status_code)
        data = res.json()

        if data is None:
            return None

        if 'pagination' not in data and 'response' in data:
            return data['response']

        return data

    def call_multi(self, endpoint: str) -> (dict, None):
        next_page = True
        page = 1
        data = []

        while next_page:
            _data = self.call(f'{endpoint}?page={page}')
            if _data is None:
                break

            if 'response' not in _data or 'pagination' not in _data:
                return _data

            data.extend(_data['response'])
            next_page = _data['pagination']['next']
            page += 1

        if len(data) == 0:
            return None

        return data

    def _load_vehicles(self) -> (dict, None):
        try:
            if FILE_VEHICLE_CACHE.is_file():
                with open(FILE_VEHICLE_CACHE, 'r', encoding='utf-8') as f:
                    cnf = json_loads(f.read())
                    if cnf['time'] + int(self.get_setting('vehicle_cache_time')) > int(time()):
                        return cnf

        except (OSError, JSONDecodeError, KeyError):
            pass

        return None

    def update_vehicles(self, force: bool = False):
        pull = True
        if not force:
            cnf = self._load_vehicles()
            if cnf is not None:
                pull = False

        if pull:
            cnf = {
              'vehicles': self.call_multi('vehicles'),
              'time': int(time())
            }
            self._write_file(file=FILE_VEHICLE_CACHE, content=json_dumps(cnf))

        self.vehicles = cnf['vehicles']
        self.vehicles_expiration = cnf['time'] + int(self.get_setting('vehicle_cache_time'))

    def update_expired_data(self):
        if self.api_token_expiration < time():
            self._load_or_generate_api_token()

        if self.vehicles_expiration < time():
            self.update_vehicles()

    def get_vehicle_by_vin(self, vin: str) -> (dict, None):
        if len(self.vehicles) == 0:
            self.update_vehicles()

        for v in self.vehicles:
            if v['vin'] == vin:
                return v

        return None

    def reauthenticate(self):
        self._load_or_generate_api_token(reauth=True)
