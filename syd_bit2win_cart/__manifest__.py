# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Bit2Win Cart",
    "version": "14.0.1.0.0",
    "category": "Bit2Win",
    "author": "Rapsodoo Italia",
    
    "website": "https://www.rapsodoo.com",
    "depends": ["web",'web_enterprise','sale'],
    "data": [
             "security/security.xml",
         "security/ir.model.access.csv",
        "views/views.xml",
        "views/templates.xml",
    ],
    'qweb': [
        "static/src/xml/qweb_templates.xml",
    ],
    "installable": True,
}
