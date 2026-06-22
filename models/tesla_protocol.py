from odoo import models, fields


class TeslaAPIProtocol(models.Model):
    _name = 'oxl.fleet.tesla.protocol'
    _description = 'Tesla API Protocol'
    _order = 'create_date desc'

    endpoint = fields.Selection(
        string='API Endpoint',
        selection=[
            ('auth', 'Authentication'),
            ('vehicles', 'Vehicle List'),
            ('options', 'Vehicle Options'),
            ('vehicle_data', 'Vehicle Data'),
            ('drivers', 'Vehicle Drivers'),
            ('mobile_enabled', 'Vehicle Mobile-State'),
            ('recent_alerts', 'Vehicle Alerts'),
            ('release_notes', 'Vehicle Release Notes'),
            ('service_data', 'Vehicle Service Data'),
        ],
        required=True,
    )
    url = fields.Char(string='URL', required=False)
    failed = fields.Boolean(string='Failed', default=False)
    status_code = fields.Integer(string='Response-Code', default=0)
    error = fields.Char(string='Error Message', required=False)
