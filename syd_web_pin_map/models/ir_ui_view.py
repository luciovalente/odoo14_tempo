# -*- coding: utf-8 -*-

from odoo import fields, models


class View(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('pin_map', "Pin Map")], ondelete={'pin_map': 'cascade'})
