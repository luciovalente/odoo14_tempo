# -*- coding: utf-8 -*-

from odoo import _, api, models
from lxml.builder import E
from odoo.exceptions import UserError


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def _get_default_pin_map_view(self):
        raise UserError(_("You need to set a <pin_map> view on this model to use the Pin Map View"))
