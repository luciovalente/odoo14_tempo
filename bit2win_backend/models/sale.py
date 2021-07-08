# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    bit2win_configurator_url = fields.Char(
        related='partner_id.bit2win_configurator_url',
    )

    use_bit2win_configurator = fields.Boolean(
        compute='compute_use_bit2win_configurator',
    )

    def compute_use_bit2win_configurator(self):
        for sale in self:
            sale.use_bit2win_configurator = \
                True if sale.bit2win_configurator_url else False

    def open_bit2win_configurator(self):
        self.ensure_one()
        url = self.bit2win_configurator_url.format(sale_id=self.id)
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
            }
