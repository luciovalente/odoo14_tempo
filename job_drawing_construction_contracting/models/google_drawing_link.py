# -*- coding:utf-8 -*-

from odoo import http
from odoo.http import request
# from openerp import api, fields, models, _
from odoo import api, fields, models, _


class GoogleDrawingLink(models.Model):
    _name = "google.drawing.link"

    name = fields.Char(
        string="Drawing Name",
        required=True
    )
    url = fields.Char(
        string="Google Drawing Url",
        required=True
    )
    description = fields.Char(
        string="Description",
        required=True
    )
    job_card_id = fields.Many2one(
        'project.task',
        string="Job Card"
    )

    # @api.multi #odoo13
    def open_google_drawing_document(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_url',
                'url': '/open/drawing_document/%s' %(rec.id),
                'target': 'self',
                'res_id': rec.id,
            }

class GoogleDrawingDocument(http.Controller):

    @http.route(['/open/drawing_document/<int:res_id>'], type='http', auth="public", website=True)
    def open_drawing_document(self, res_id, **post):
        if res_id:
            document_id = request.env['google.drawing.link'].sudo().browse(res_id)
            values = {
                'document': document_id,
            }
            return request.render('job_drawing_construction_contracting.google_drawing_document', values)

