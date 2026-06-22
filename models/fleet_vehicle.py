from json import dumps as json_dumps

from odoo import models, fields, api

from .tesla_api import TeslaAPI, APIErrorStatus, APIErrorOffline
from .tesla_option_codes import TESLA_OPTION_CODES


API_OFFLINE_COUNT_MAX = 2
MAX_ALERTS_SHOW = 20
MILE_TO_KM = 1.609344


class ApiExtendedFleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    _tesla_api = TeslaAPI(None)

    is_tesla = fields.Boolean(string='Is Tesla', compute='_compute_is_tesla')
    tesla_api_error = fields.Char(string='Error')
    tesla_api_error_at = fields.Datetime(string='Error Time')
    tesla_api_updated_at = fields.Datetime(string='Update Time')
    tesla_api_offline_count = fields.Integer(string='Car Offline Count')

    # basic info
    tesla_display_name = fields.Char(string='Display Name')
    tesla_option_codes = fields.Char(string='Option Codes')
    tesla_options = fields.Html(string='Options', compute='_compute_tesla_options')

    # vehicle-data
    tesla_show_vehicle_data = fields.Boolean(string='Show Tesla Vehicle-Data', compute='_compute_tesla_show_vehicle_data')
    tesla_supercharger_payment_needed = fields.Boolean(string='Supercharging Payment Needed')
    tesla_supercharging_enabled = fields.Boolean(string='Supercharging Enabled')

    tesla_car_type = fields.Char(string='Car Type')
    tesla_car_special_type = fields.Char(string='Car Special-Type')
    tesla_charge_port_type = fields.Char(string='Charge Port Type')
    tesla_exterior_color = fields.Char(string='Exterior Color')
    tesla_driver_assist = fields.Char(string='Driver Assist')

    tesla_car_version = fields.Char(string='Car Version')
    tesla_api_version = fields.Char(string='API Version')
    tesla_locked = fields.Boolean(string='Is Locked')
    tesla_user_present = fields.Boolean(string='User is Present')

    tesla_show_vehicle_data_raw = fields.Boolean(
        string='Show Tesla Raw Vehicle-Data',
        compute='_compute_tesla_show_vehicle_data_raw',
    )
    tesla_raw_base = fields.Char(string='Base Data')
    tesla_raw_charge_state = fields.Char(string='Charge State')
    tesla_raw_climate_state = fields.Char(string='Climate State')
    tesla_raw_drive_state = fields.Char(string='Drive State')
    tesla_raw_gui_settings = fields.Char(string='GUI Settings')
    tesla_raw_vehicle_config = fields.Char(string='Vehicle Config')
    tesla_raw_vehicle_state = fields.Char(string='Vehicle State')

    # drivers
    tesla_show_drivers = fields.Boolean(string='Show Tesla Drivers', compute='_compute_tesla_show_drivers')
    tesla_drivers = fields.Char(string='Drivers')
    tesla_drivers_list = fields.Html(string='List of Drivers', compute='_compute_tesla_drivers_list')

    # alerts
    tesla_alert_ids = fields.One2many('oxl.fleet.tesla.alerts', 'vehicle_id', 'Tesla Alerts')
    tesla_alert_list = fields.Html(string='List of Alerts', compute='_compute_tesla_alert_list')

    # service status
    tesla_service_status = fields.Char(string='Service Status')
    tesla_service_etc = fields.Char(string='Service ETC')
    tesla_service_nr = fields.Char(string='Service Visit Number')
    tesla_service_status_id = fields.Integer(string='Service Status-ID')

    @api.model
    def _is_tesla(self) -> bool:
        is_tesla = False
        if self.model_id.name:
            is_tesla = self.model_id.name.lower().find('tesla') != -1

        if not is_tesla and self.model_id.brand_id.name:
            is_tesla = self.model_id.brand_id.name.lower().find('tesla') != -1

        return is_tesla

    @api.depends('model_id.name')
    def _compute_is_tesla(self):
        # pylint: disable=W0212
        for rec in self:
            rec.is_tesla = rec._is_tesla()

    @api.depends('tesla_raw_base')
    def _compute_tesla_show_vehicle_data(self):
        for rec in self:
            rec.tesla_show_vehicle_data = self._get_setting('pull_vehicle_data')

    @api.depends('tesla_raw_base')
    def _compute_tesla_show_vehicle_data_raw(self):
        for rec in self:
            rec.tesla_show_vehicle_data_raw = self._get_setting('pull_vehicle_data') and \
                                              self._get_setting('show_raw_tab')

    @api.depends('tesla_raw_base')
    def _compute_tesla_show_drivers(self):
        for rec in self:
            rec.tesla_show_drivers = self._get_setting('pull_drivers')

    @api.depends('tesla_option_codes')
    def _compute_tesla_options(self):
        for rec in self:
            options = []
            if not isinstance(rec.tesla_option_codes, str):
                rec.tesla_options = ''
                continue

            for code in rec.tesla_option_codes.split(','):
                try:
                    options.append(f'<li>{code} - {TESLA_OPTION_CODES[code]}</li>')

                except KeyError:
                    options.append(f'<li>{code}</li>')

            rec.tesla_options = f"<ul>{''.join(options)}</ul>"

    @api.depends('tesla_drivers')
    def _compute_tesla_drivers_list(self):
        for rec in self:
            drivers = []
            if not isinstance(rec.tesla_drivers, str):
                rec.tesla_drivers_list = ''
                continue

            for person in rec.tesla_drivers.split(','):
                try:
                    drivers.append(f'<li>{person}</li>')

                except KeyError:
                    pass

            rec.tesla_drivers_list = f"<ul>{''.join(drivers)}</ul>"

    @api.depends('tesla_alert_list')
    def _compute_tesla_alert_list(self):
        for rec in self:
            alerts = []

            for alert in self.tesla_alert_ids:
                if len(alerts) > MAX_ALERTS_SHOW:
                    break

                alerts.append(
                    f"""<li>
                    <b>Name</b>: {alert.name}<br>
                    <b>Time</b>: {alert.time}<br>
                    <b>Description</b>: {alert.user_text}<br>
                    <b>Categories</b>: {alert.audience}
                    </li>"""
                )

            if len(alerts) == 0:
                self.tesla_alert_list = ''
                return

            rec.tesla_alert_list = f"<ul>{''.join(alerts)}</ul>"

    @api.model
    def _tesla_api_init(self) -> bool:
        try:
            self._tesla_api.odoo_env = self.env
            self._tesla_api.init()
            self._tesla_api.update_expired_data()
            return True

        except PermissionError:
            self._register_api_error('Invalid credentials')

        except (ConnectionError, TimeoutError, OSError):
            self._register_api_error('Network connection error')

        return False

    @api.model
    def _register_api_error(self, msg: str):
        self.tesla_api_error = msg
        self.tesla_api_error_at = fields.Datetime.now()

    @api.model
    def _tesla_api_call(self, endpoint: str) -> (dict, None):
        data = None
        try:
            if not self._tesla_api_init():
                return data

            data = self._tesla_api.call(endpoint)

        except APIErrorStatus as e:
            self._register_api_error(f'Got bad response from API ({e})')

        except APIErrorOffline:
            self._register_api_error('Car is unreachable/offline (408)')
            self.tesla_api_offline_count += 1

        except (ConnectionError, TimeoutError, OSError):
            self._register_api_error('Network connection error')

        return data

    @api.model
    def _tesla_api_pull_vehicle_data(self, v: dict):
        if not self._get_setting('pull_vehicle_data'):
            return

        if v['state'].lower() == 'offline':
            self.tesla_api_error = 'Vehicle is offline'
            return

        data = self._tesla_api_call(f'vehicles/{self.vin_sn}/vehicle_data')
        if data is None:
            return

        self.tesla_api_offline_count = 0

        def _raw_base(raw_full: dict) -> dict:
            d = raw_full.copy()
            d.pop('charge_state')
            d.pop('climate_state')
            d.pop('drive_state')
            d.pop('gui_settings')
            d.pop('vehicle_config')
            d.pop('vehicle_state')
            return d

        def _handle_bool(item) -> bool:
            if isinstance(item, bool):
                return item

            return item.lower() == 'true'

        try:
            odometer = data['vehicle_state']['odometer']
            if self._get_setting('odometer_km'):
                odometer *= MILE_TO_KM

            self.update({
                'tesla_supercharger_payment_needed': _handle_bool(
                    data['supercharger_payment_needed']) if 'supercharger_payment_needed' in data else False,
                'tesla_supercharging_enabled': _handle_bool(
                    data['supercharging_enabled']) if 'supercharging_enabled' in data else False,

                'tesla_car_type': data['vehicle_config']['car_type'],
                'tesla_car_special_type': data['vehicle_config']['car_special_type'],
                'tesla_charge_port_type': data['vehicle_config']['charge_port_type'],
                'tesla_exterior_color': data['vehicle_config']['exterior_color'],
                'tesla_driver_assist': data['vehicle_config']['driver_assist'],

                'odometer': odometer,
                'tesla_car_version': data['vehicle_state']['car_version'],
                'tesla_locked': _handle_bool(data['vehicle_state']['locked']),
                'tesla_user_present': _handle_bool(data['vehicle_state']['is_user_present']),

                'tesla_raw_base': json_dumps(_raw_base(data)),
                'tesla_raw_charge_state': json_dumps(data['charge_state']),
                'tesla_raw_climate_state': json_dumps(data['climate_state']),
                'tesla_raw_drive_state': json_dumps(data['drive_state']),
                'tesla_raw_gui_settings': json_dumps(data['gui_settings']),
                'tesla_raw_vehicle_config': json_dumps(data['vehicle_config']),
                'tesla_raw_vehicle_state': json_dumps(data['vehicle_state']),
            })

        except KeyError as e:
            self._register_api_error(f"Missing vehicle-data: '{e}'")

    @api.model
    def _tesla_api_pull_drivers(self):
        if not self._get_setting('pull_drivers'):
            return

        data = self._tesla_api_call(f'vehicles/{self.vin_sn}/drivers')
        if data is None:
            return

        try:
            self.tesla_drivers = ','.join([
                f"{d['driver_first_name']} {d['driver_last_name']}" for d in data
            ])

        except KeyError as e:
            self._register_api_error(f"Missing driver-info: '{e}'")

    @api.model
    def _tesla_api_pull_alerts(self):
        if not self._get_setting('pull_alerts'):
            return

        data = self._tesla_api_call(f'vehicles/{self.vin_sn}/recent_alerts')
        if data is None:
            return

        try:
            for alert in data['recent_alerts']:
                exists = len(self.env['oxl.fleet.tesla.alerts'].search([
                    ('name','=', alert['name']),
                    ('time', '=', alert['time']),
                ])) > 0
                if not exists:
                    self.env['oxl.fleet.tesla.alerts'].create({
                        'name': alert['name'],
                        'time': alert['time'],
                        'user_text': alert['user_text'],
                        'audience': ','.join(alert['audience']),
                        'vehicle_id': self.id,
                    })

        except KeyError as e:
            self._register_api_error(f"Missing alert-info: '{e}'")

    @api.model
    def _tesla_api_pull_service_status(self):
        if not self._get_setting('pull_service'):
            return

        data = self._tesla_api_call(f'vehicles/{self.vin_sn}/service_data')
        if data is None:
            return

        try:
            self.update({
                'tesla_service_status': data['service_status'],
                'tesla_service_etc': data['service_etc'],
                'tesla_service_nr': data['service_visit_number'],
                'tesla_service_status_id': data['status_id'],
            })

        except KeyError:
            self.tesla_service_status = ''

    def tesla_api_update_single(self):
        if not self._is_tesla():
            return

        if not self._tesla_api_init():
            self._register_api_error('Connection error')
            return

        v = None
        try:
            v = self._tesla_api.get_vehicle_by_vin(self.vin_sn)

        except APIErrorStatus as e:
            self._register_api_error(f'Got bad response from API ({e})')

        except (ConnectionError, TimeoutError, OSError):
            self._register_api_error('Network connection error')

        if v is None:
            self._register_api_error('Vehicle VIN not matched/found')
            return

        # sometimes they are missing (?)
        if v['option_codes'] is not None:
            self.tesla_option_codes = v['option_codes']

        else:
            if self._get_setting('pull_options'):
                options = self._tesla_api_call(f'dx/vehicles/options?vin={self.vin_sn}')
                option_codes = []
                if options is not None and 'codes' in options:
                    for option in options['codes']:
                        option_codes.append(option['code'].replace('$', ''))

                self.tesla_option_codes = ','.join(option_codes)

        self.update({
            'tesla_api_error': '',
            'tesla_display_name': v['display_name'],
            'tesla_api_version': v['api_version'],
        })

        self._tesla_api_pull_vehicle_data(v)
        self._tesla_api_pull_drivers()
        self._tesla_api_pull_service_status()
        self._tesla_api_pull_alerts()

        self.tesla_api_updated_at = fields.Datetime.now()

    @api.model
    def update_needed(self) -> bool:
        if self.tesla_api_updated_at in [None, False]:
            return True

        poll = self._tesla_api.poll_interval
        if poll is None:
            return False

        data_is_old = self.tesla_api_updated_at < (fields.Datetime.now() - poll)

        has_error = False
        retry_needed = False
        if self.tesla_api_error_at not in [None, False] and self.tesla_api_updated_at < self.tesla_api_error_at:
            has_error = True
            if self.tesla_api_offline_count > API_OFFLINE_COUNT_MAX and \
                    self.tesla_api_error_at > (fields.Datetime.now() - int(self._get_setting('offline_retry_interval'))):
                retry_needed = False

            elif self.tesla_api_error_at < (fields.Datetime.now() - self._tesla_api.retry_interval):
                retry_needed = True

        return data_is_old and (not has_error or retry_needed)

    @api.model
    def is_update_time_allowed(self) -> bool:
        # pylint: disable=R0911
        cnf = self._get_setting('poll_limit')
        now = fields.Datetime.now()
        working_hours = 9 < now.hour < 17

        if cnf == '9-5':
            return working_hours

        if cnf == '8-8':
            return 8 < now.hour < 20

        if cnf == 'mo-sa-9-5':
            return now.isoweekday() < 7 and working_hours

        if cnf == 'mo-fr-9-5':
            return now.isoweekday() < 6 and working_hours

        if cnf == 'mo-9-5':
            return now.isoweekday() == 1 and working_hours

        if cnf == 'tu-9-5':
            return now.isoweekday() == 2 and working_hours

        if cnf == 'we-9-5':
            return now.isoweekday() == 3 and working_hours

        if cnf == 'th-9-5':
            return now.isoweekday() == 4 and working_hours

        if cnf == 'fr-9-5':
            return now.isoweekday() == 5 and working_hours

        return True  # no limit

    @api.model
    def _get_setting(self, setting: str) -> any:
        return self.env['ir.config_parameter'].sudo().get_param(f'oxl_fleet_tesla.{setting}')

    @api.model
    def tesla_api_update_all(self, force: bool = False):
        self._tesla_api_init()

        for rec in self.env['fleet.vehicle'].search([]):
            if force or (rec.update_needed() and rec.is_update_time_allowed()):
                rec.tesla_api_update_single()

    @api.model
    def tesla_api_reauthenticate(self):
        self._tesla_api_init()
        try:
            self._tesla_api.reauthenticate()

        except PermissionError:
            self._register_api_error('Invalid credentials')

        except (ConnectionError, TimeoutError, OSError):
            self._register_api_error('Network connection error')
