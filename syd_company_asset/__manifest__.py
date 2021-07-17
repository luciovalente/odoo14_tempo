# -*- coding: utf-8 -*-
{
    'name': "Company Asset Data Models",
    'summary': "Defines models and business logic for company asset records",
    'description': "",
    'category': 'Productivity',
    'version': '14.1.0.3',
    'depends': [
        'web',
        'base_setup',
        'product',
        'maintenance',
        'syd_rest_in_peace',
        'syd_web_pin_map',
        'syd_rip_survey'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'views/assets.xml',
        'views/company_asset_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'auto_install': False,
    'license': '',
}
