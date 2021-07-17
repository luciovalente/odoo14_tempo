# -*- coding: utf-8 -*-
{
    'name': "syd_rest_in_peace",
    'summary': """Handles Rest API auth operations.""",
    'description': "",
    'author': "Rapsodoo",
    'website': "https://www.rapsodoo.com",
    'category': 'Uncategorized',
    'version': '0.2',
    'depends': ['base', 'base_setup'],
    'external_dependencies': {
        'python': ['pyjwt'],
    },
    'data': [
        'security/ir.model.access.csv',

        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': '',
}
