# -*- coding: utf-8 -*-

# pylint: disable=W0104
{
    'name': 'OXL Fleet Tesla-API',
    'author': 'OXL IT Services',
    'support': 'odoo@oxl.at',
    'version': '1.2',
    'category': 'Human Resources',
    'summary': 'Integrate Tesla Fleet-API',
    'description': """Integrates Tesla Fleet-API into the Odoo fleet-management. 
    You can fetch vehicle information on a schedule or on-demand. WARNING: The Tesla Fleet-API IS NOT FREE!""",
    'website': 'https://github.com/O-X-L/odoo-plugin-car-fleet-tesla-api',
    'depends': [
        'base',
        'fleet',
    ],
    'data': [
        'security/fleet_tesla_security.xml',
        'security/ir.model.access.csv',
        'views/fleet_vehicle_view.xml',
        'views/fleet_tesla_protocol_view.xml',
        'views/res_config_settings_view.xml',
    ],
    'demo': [],
    'css': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 500,
    'currency': 'EUR',
    'license': 'OPL-1',
}
