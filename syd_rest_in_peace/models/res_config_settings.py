# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    secret = fields.Char(config_parameter='syd_rip.secret')
    algorithm = fields.Selection([('HS256', 'HS256')], default="HS256", config_parameter='syd_rip.algorithm')
    access_token_exp = fields.Integer("Access Token Expiration", config_parameter='syd_rip.access_token_exp')
    refresh_token_exp = fields.Integer("Refresh Token Expiration", config_parameter='syd_rip.refresh_token_exp')
