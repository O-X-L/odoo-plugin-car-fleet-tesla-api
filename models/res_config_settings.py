from odoo import models, fields, api

from .tesla_api import DEFAULT_OFFLINE_RETRY_INTERVAL, DEFAULT_VEHICLE_CACHE_TIME


class ApiExtendedFleetSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # todo: limit access to settings via security.xml
    tesla_client_id = fields.Char(string='Tesla API Client-ID', config_parameter='oxl_fleet_tesla.client_id')
    tesla_client_secret = fields.Char(string='Tesla API Secret', config_parameter='oxl_fleet_tesla.client_secret')
    # todo: en- & decrypt secret

    tesla_poll_interval = fields.Selection(
        string='Tesla API Poll-Interval',
        selection=[
            ('month', 'Monthly'),
            ('week', 'Weekly'),
            ('day', 'Daily'),
            ('hour', 'Hourly'),
            ('30m', '30min'),
            ('15m', '15min'),
            ('10m', '10min'),
            ('5m', '5min'),
            ('none', 'Disable'),
        ],
        default='day',
        config_parameter='oxl_fleet_tesla.poll_interval',
    )
    tesla_poll_limit = fields.Selection(
        string='Tesla API Poll-Limit',
        selection=[
            ('mo-fr-9-5', 'Weekdays between 0900 and 1700'),
            ('mo-sa-9-5', 'Monday to Saturday between 0900 and 1700'),
            ('9-5', 'Every day between 0900 and 1700'),
            ('8-8', 'Every day between 0800 and 2000'),
            ('mo-9-5', 'Monday between 0900 and 1700'),
            ('tu-9-5', 'Tuesday between 0900 and 1700'),
            ('we-9-5', 'Wednesday between 0900 and 1700'),
            ('th-9-5', 'Thursday between 0900 and 1700'),
            ('fr-9-5', 'Friday between 0900 and 1700'),
            ('none', 'No Limit'),
        ],
        default='mo-fr-9-5',
        config_parameter='oxl_fleet_tesla.poll_limit',
    )
    tesla_region = fields.Selection(
        string='Choose your region',
        selection=[
            ('europe', 'Europe'),
            ('america', 'America'),
            ('africa', 'Africa'),
            ('middle_east', 'Middle East'),
            ('asia', 'Asia (excluding China)'),
            ('china', 'China'),
        ],
        default='europe',
        config_parameter='oxl_fleet_tesla.region'
    )
    tesla_offline_retry_interval = fields.Integer(
        string='Offline Retry-Interval (seconds)',
        config_parameter='oxl_fleet_tesla.offline_retry_interval',
    )
    tesla_vehicle_cache_time = fields.Integer(
        string='Vehicle-Cache Time (seconds)',
        config_parameter='oxl_fleet_tesla.vehicle_cache_time',
    )
    tesla_show_raw_tab = fields.Boolean(
        string='Show Raw-Data Tab',
        config_parameter='oxl_fleet_tesla.show_raw_tab',
        default=False,
    )
    tesla_odometer_km = fields.Boolean(
        string='Odometer in KM',
        config_parameter='oxl_fleet_tesla.odometer_km',
        default=False,
    )

    tesla_pull_options = fields.Boolean(  # /api/1/dx/vehicles/options?vin=VIN
        string='Pull Vehicle-Options',
        config_parameter='oxl_fleet_tesla.pull_options',
        default=True,
    )
    tesla_pull_vehicle_data = fields.Boolean(  # /api/1/vehicles/VIN/vehicle_data
        string='Pull Vehicle-Data',
        config_parameter='oxl_fleet_tesla.pull_vehicle_data',
        default=True,
    )
    tesla_pull_drivers = fields.Boolean(  # /api/1/vehicles/VIN/drivers
        string='Pull Drivers',
        config_parameter='oxl_fleet_tesla.pull_drivers',
        default=False,
    )
    tesla_pull_alerts = fields.Boolean(  # /api/1/vehicles/VIN/recent_alerts
        string='Pull Alerts',
        config_parameter='oxl_fleet_tesla.pull_alerts',
        default=False,
    )
    # tesla_pull_release_notes = fields.Boolean(  # /api/1/vehicles/VIN/release_notes
    #     string='Pull Release-Notes',
    #     config_parameter='oxl_fleet_tesla.pull_release_notes',
    #     default=False,
    # )
    tesla_pull_service = fields.Boolean(  # /api/1/vehicles/VIN/service_data
        string='Pull Service-Data',
        config_parameter='oxl_fleet_tesla.pull_service',
        default=False,
    )

    @api.model
    def tesla_api_reauthenticate(self, _ = None):
        self.env['fleet.vehicle'].tesla_api_reauthenticate()

    @api.model
    def tesla_api_update_all(self, _ = None):
        self.env['fleet.vehicle'].tesla_api_update_all()

    def set_values(self):
        super().set_values()
        m = self.env['ir.config_parameter'].sudo()
        m.set_param('oxl_fleet_tesla.offline_retry_interval', DEFAULT_OFFLINE_RETRY_INTERVAL)
        m.set_param('oxl_fleet_tesla.vehicle_cache_time', DEFAULT_VEHICLE_CACHE_TIME)
