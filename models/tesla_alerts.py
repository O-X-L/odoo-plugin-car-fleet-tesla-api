from odoo import models, fields


class TeslaVehicleAlerts(models.Model):
    _name = 'oxl.fleet.tesla.alerts'
    _description = 'Tesla Vehicle Alerts'

    name = fields.Char(string='Name', required=True)
    time = fields.Char(string='Time', required=True)
    user_text = fields.Char(string='Information')
    audience = fields.Char(string='Audience')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle ID', ondelete='cascade', required=True)
