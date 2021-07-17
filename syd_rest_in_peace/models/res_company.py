# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    syd_rip_secret = fields.Char('Secret')
    syd_rip_algorithm = fields.Selection(selection=[('HS256', 'HS256')], string="Algorithm", default="HS256")
    syd_rip_access_token_exp = fields.Integer("Access Token Expiration")
    syd_rip_refresh_token_exp = fields.Integer("Refresh Token Expiration")
