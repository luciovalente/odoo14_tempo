# -*- coding: utf-8 -*-

from odoo import models, fields, api

import json


class ResUsers(models.Model):
    _inherit = 'res.users'

    _RIP_GET_FIELDS = (
        'id', 'name', 'login', 'email',
        '{image_urls}',
        ('partner_id.id', 'partner_id'),
        ('partner_id.contact_address_complete', 'address'),
        '{mobile_data}',
        'active',
    )

    _RIP_POST_FIELDS = (
        'id', 'name', 'login', 'email',
        ('image_1920', 'image'),
        ('partner_id.contact_address_complete', 'address'),
        '{mobile_data}'
    )

    # INFO: data from mobile to be saved (JSON format).
    mobile_data = fields.Text()

    image_urls = fields.Char('Image URLs', compute='_compute_image_urls', store=False)

    @api.depends('image_128', 'image_256', 'image_512', 'image_1024', 'image_1920')
    def _compute_image_urls(self):
        for rec in self:
            _id = rec.id
            rec.image_urls = json.dumps({
                "image_128": "/sydrestapi/v1/redirect?url=/web/image/res.users/%d/image_128" % _id,
                "image_256": "/sydrestapi/v1/redirect?url=/web/image/res.users/%d/image_256" % _id,
                "image_512": "/sydrestapi/v1/redirect?url=/web/image/res.users/%d/image_512" % _id,
                "image_1024": "/sydrestapi/v1/redirect?url=/web/image/res.users/%d/image_1024" % _id,
                "image_1920": "/sydrestapi/v1/redirect?url=/web/image/res.users/%d/image_1920" % _id
            })

    def from_auth_token(self, user, rec, vals, form_vals):
        return user, user, False


class ResPartner(models.Model):
    _inherit = 'res.partner'

    _RIP_GET_FIELDS = (
        'id', 'name', 'email',
    )
