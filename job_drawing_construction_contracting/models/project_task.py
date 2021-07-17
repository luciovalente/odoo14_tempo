# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    google_drawing_link_ids = fields.One2many(
        'google.drawing.link',
        'job_card_id',
        string="Google Drawing Link"
    )

    # @api.multi #odoo13
    def create_a_google_drawing(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_url',
                'url': 'https://docs.google.com/drawings/',
                'target': 'new',
            }
