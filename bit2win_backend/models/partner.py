# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    bit2win_configurator_type = fields.Selection([
        ('telco', 'Telco'),
        ('utilities', 'Utilities'),
        ])

    bit2win_configurator_url = fields.Char(
        compute='compute_bit2win_configurator_url',
    )

    def compute_bit2win_configurator_url(self):
        for partner in self:
            url = ''
            if partner.bit2win_configurator_type == 'telco':
                url = \
                    'https://bit2win-cart-simulator.herokuapp.com/' \
                    '?source=ext&catalogName=TelcoWholesale&quoteId={sale_id}'
            elif partner.bit2win_configurator_type == 'utilities':
                url = \
                    'https://bit2win-cart-simulator.herokuapp.com/' \
                    '?source=ext&catalogName=POC%20Eni%3A%20Power%20500%20-' \
                    '%20Gas%20400&quoteId={sale_id}'
            partner.bit2win_configurator_url = url
