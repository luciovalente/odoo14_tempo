# -*- coding: utf-8 -*-
{
    'name': "RIP Survey",
    'summary': "Survey Management thru Rest In Peace Module",
    'description': "",
    'category': 'Productivity',
    'version': '0.1',
    'depends': [
        'syd_rest_in_peace'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'views/rip_survey_views.xml',
        'views/menu_views.xml',
    ],
    'application': True,
    'auto_install': False,
    'license': '',
}
