# -*- coding: utf-8 -*-
from odoo import _, api, models, fields
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.syd_rest_in_peace.core import make_response

import io
import base64

import json

import logging
_logger = logging.getLogger(__name__)


#
# INFO: samples of TransientModel function.
#
# class CheckInOut(models.TransientModel):
#     _name = 'company.asset.reservation.set_checkinout'
#
#     _RIP_POST_FIELDS = (
#         'code',
#         'date_checkin',
#         'date_checkout'
#     )
#
#     id = fields.Many2one('company.asset.reservation')
#     code = fields.Char()
#     date_checkin = fields.Datetime()
#     date_checkout = fields.Datetime()
#
#     def create(self, vals):
#         id = vals.get('id', False)
#         code = vals.get('code', False)
#         date_checkin = vals.get('date_checkin', False)
#         date_checkout = vals.get('date_checkout', False)
#
#         # TODO: check reservation code related to the user.
#         r_id = self.env['company.asset.reservation'].browse(id).exists() or \
#                (code and self.env['company.asset.reservation'].search([('code', '=', code)], limit=1))
#         if r_id:
#             if date_checkin:
#                 r_id.date_checkin = date_checkin
#             if date_checkout:
#                 r_id.date_checkout = date_checkout
#             return r_id
#         else:
#             raise ValidationError(_("Reservation not found"))


class CompanyAssetBuilding(models.Model):
    _name = 'company.asset.building'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = "Company Asset Building Model"
    _order = 'company_id, name'

    _RIP_GET_FIELDS = (
        'id',
        'code', 'name', 'description',
        '.image_128', '.image_256', '.image_512', '.image_1024',
        '{image_urls}',
        ('responsible_id.id', 'responsible_id'),
        ('responsible_id.name', 'responsible_name'),
        ('partner_id.id', 'partner_id'),
        ('partner_id.name', 'partner_name'),
        'floor_ids.id',
        ('asset_item_ids.id', 'asset_item_ids'),
    )

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
        default=lambda self: self.env.company.id)

    name = fields.Char(required=True)
    code = fields.Char()
    description = fields.Text()
    responsible_id = fields.Many2one('res.users', string='Responsible', ondelete='set null')
    partner_id = fields.Many2one('res.partner', string='Related Contact', ondelete='set null')

    floor_ids = fields.One2many('company.asset.floor', 'building_id')
    area_ids = fields.One2many('company.asset.area', compute='_compute_area_ids', readonly=True, store=False)
    area_ids_count = fields.Integer(compute='_compute_area_ids_count')
    asset_item_ids = fields.One2many('company.asset.item', compute='_compute_asset_item_ids', readonly=True, store=False)
    asset_item_ids_count = fields.Integer(compute='_compute_asset_item_ids_count')

    image_urls = fields.Char('Images URLs', compute='_compute_image_urls', store=False)

    survey_id = fields.Many2one('rip.survey', ondelete='set null')

    floor_plans_json = fields.Char(compute="_compute_floor_plans_json", store=False)

    def action_view_assets(self):
        self.ensure_one()
        action = {
            'res_model': 'company.asset.item',
            'type': 'ir.actions.act_window',
        }
        if len(self.asset_item_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.asset_item_ids[0].id,
            })
        else:
            action.update({
                'name': _("Asset of Buildings %s", self.name),
                'domain': [('id', 'in', self.asset_item_ids.ids)],
                'view_mode': 'tree,form',
            })
        return action


    @api.depends('image_128', 'image_256', 'image_512', 'image_1024', 'image_1920')
    def _compute_image_urls(self):
        for rec in self:
            _id = rec.id
            rec.image_urls = json.dumps({
                "image_128": "/sydrestapi/v1/redirect?url=/web/image/company.asset.building/%d/image_128" % _id,
                "image_256": "/sydrestapi/v1/redirect?url=/web/image/company.asset.building/%d/image_256" % _id,
                "image_512": "/sydrestapi/v1/redirect?url=/web/image/company.asset.building/%d/image_512" % _id,
                "image_1024": "/sydrestapi/v1/redirect?url=/web/image/company.asset.building/%d/image_1024" % _id,
                "image_1920": "/sydrestapi/v1/redirect?url=/web/image/company.asset.building/%d/image_1920" % _id
            })

    @api.depends('area_ids')
    def _compute_area_ids_count(self):
        for rec in self:
            rec.area_ids_count = len(rec.area_ids)

    @api.depends('asset_item_ids')
    def _compute_asset_item_ids_count(self):
        for rec in self:
            rec.asset_item_ids_count = len(rec.asset_item_ids)

    def _compute_area_ids(self):
        for rec in self:
            area_ids = self.env['company.asset.area'].search([
                ('building_id', '=', rec.id),
            ])
            rec.area_ids = area_ids
            rec.area_ids_count = len(area_ids)

    def _compute_asset_item_ids(self):
        for rec in self:
            asset_item_ids = self.env['company.asset.item'].search([
                ('building_id', '=', rec.id),
            ])
            rec.asset_item_ids = asset_item_ids
            rec.asset_item_ids_count = len(asset_item_ids)

    def action_show_floor_plans(self):
        return {
            'name': _('Building Floor Plans'),
            'type': 'ir.actions.act_window',
            'view_mode': 'pin_map',
            'views': [(False, "pin_map")],
            'res_model': 'company.asset.floor',
            'context': dict(self.env.context),
            # 'res_id': self.id,
            'domain': [('building_id', '=', self.id)],
            # 'json': self.floor_plans_json
        }

    def _compute_floor_plans_json(self):
        for rec in self:
            try:
                rec.floor_plans_json = str.encode(json.dumps({
                    "mapwidth": "1000",
                    "mapheight": "1000",
                    "levels": [
                        {
                            "id": level.id,
                            "title": level.name,
                            "map": level.internal_floor_plan_url,
                            "minimap": "",
                            "locations": [
                                location.to_json() for location in level.asset_item_ids
                            ]
                        } for level in rec.floor_ids
                    ]
                }))
            except (IOError, OSError):
                rec.floor_plans_json = False

    def get_survey(self, user, rec, vals, fvals):
        return rec.survey_id, False, False

    def get_free(self, user, rec, vals, fvals):
        company_asset_reservation = self.env['company.asset.reservation']
        asset_type_id = vals.get('asset_type_id')
        equipment_type_id = vals.get('equipment_type_id')
        date_from = vals.get('date_from')
        date_to = vals.get('date_to')
        search_domain = [
            ('building_id', '=', rec.id),
            ('reservation_type', '=', 'yes')
        ]
        if asset_type_id:
            search_domain += [('type_id', 'in', type(asset_type_id) is list and asset_type_id or [asset_type_id])]
        if equipment_type_id:
            search_domain += [('equipment_ids.type_id', 'in', type(equipment_type_id) is list and equipment_type_id or [equipment_type_id])]
        recs = self.env['company.asset.item']
        for asset_id in recs.search(search_domain):
            if not company_asset_reservation.search([
                ('date_from', '<=', date_to),
                ('date_to', '>=', date_from),
                ('asset_item_id', '=', asset_id.id),
            ]):
                recs += asset_id

        return False, recs, False


class CompanyAssetFloor(models.Model):
    _name = 'company.asset.floor'
    _description = "Company Asset Floor Model"
    _order = 'sequence, code, name'

    _RIP_GET_FIELDS = (
        'id',
        'code', 'name', 'description',
        ('responsible_id.id', 'responsible_id'),
        ('responsible_id.name', 'responsible_name'),
        ('asset_item_ids.id', 'asset_item_ids'),
        'floor_plan_url', 'floor_plan_absolute_url',
    )

    building_id = fields.Many2one('company.asset.building', ondelete='cascade')

    sequence = fields.Integer()
    name = fields.Char(required=True)
    code = fields.Char()
    description = fields.Text()
    responsible_id = fields.Many2one('res.users', string='Responsible', ondelete='set null')
    area_ids = fields.One2many('company.asset.area', 'floor_id')
    area_ids_count = fields.Integer(compute='_compute_area_ids_count')
    asset_item_ids = fields.One2many('company.asset.item', 'floor_id')
    asset_item_ids_count = fields.Integer(compute='_compute_asset_item_ids_count')
    floor_plan = fields.Binary()
    floor_plan_url = fields.Char('Floor Plan URL', compute='_floor_plan_url', store=False)
    internal_floor_plan_url = fields.Char('Floor Plan URL (internal)', compute='_internal_floor_plan_url', store=False)
    floor_plan_absolute_url = fields.Char('Floor Plan Absolute URLs', compute='_floor_plan_absolute_url', store=False)

    floor_plan_json = fields.Char(compute="_compute_floor_plan_json", store=False)

    def action_view_assets(self):
        self.ensure_one()
        action = {
            'res_model': 'company.asset.item',
            'type': 'ir.actions.act_window',
        }
        if len(self.asset_item_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.asset_item_ids[0].id,
            })
        else:
            action.update({
                'name': _("Asset of Buildings %s", self.name),
                'domain': [('id', 'in', self.asset_item_ids.ids)],
                'view_mode': 'tree,form',
            })
        return action

    def _compute_floor_plan_json(self):
        for rec in self:
            try:
                rec.floor_plan_json = str.encode(json.dumps({
                    "mapwidth": "1000",
                    "mapheight": "1000",
                    "levels": [
                        {
                            "id": rec.id,
                            "title": rec.name,
                            "map": rec.internal_floor_plan_url,
                            "minimap": "",
                            "locations": [
                                location.to_json() for location in rec.asset_item_ids
                            ]
                        },
                    ]
                }))
            except (IOError, OSError):
                rec.floor_plan_json = False

    @api.depends('floor_plan')
    def _floor_plan_url(self):
        for rec in self:
            # TODO: inform Seedable to use new url with final fake filename to help client side identify incoming file.
            rec.floor_plan_url = "/sydrestapi/v1/redirect?url=/web/content/company.asset.floor/%d/floor_plan" % rec.id
            # rec.floor_plan_url = "/sydrestapi/v1/redirect?url=/web/content/company.asset.floor/%d/floor_plan/floor_plan.svg" % rec.id

    @api.depends('floor_plan')
    def _internal_floor_plan_url(self):
        for rec in self:
            rec.internal_floor_plan_url = "/web/content/company.asset.floor/%d/floor_plan/floor_plan_%d.svg" % (rec.id, rec.id)

    @api.depends('floor_plan')
    def _floor_plan_absolute_url(self):
        for rec in self:
            rec.floor_plan_absolute_url = "%sweb/content/company.asset.floor/%d/floor_plan/floor_plan.svg" % (request.httprequest.host_url, rec.id)

    @api.depends('area_ids')
    def _compute_area_ids_count(self):
        for rec in self:
            rec.area_ids_count = len(rec.area_ids)

    @api.depends('asset_item_ids')
    def _compute_asset_item_ids_count(self):
        for rec in self:
            rec.asset_item_ids_count = len(rec.asset_item_ids)

    def action_show_floor_plan_map(self):
        return {
            'name': _('Floor Plan'),
            'type': 'ir.actions.act_window',
            'view_mode': 'pin_map',
            'views': [(False, "pin_map")],
            'res_model': 'company.asset.floor',
            'context': dict(self.env.context),
            'domain': [('id', '=', self.id)],
            # 'json': self.floor_plan_json
        }


class CompanyAssetArea(models.Model):
    _name = 'company.asset.area'
    _description = "Company Asset Area Model"
    _order = 'name'

    name = fields.Char()
    code = fields.Char()
    description = fields.Char()
    responsible_id = fields.Many2one('res.users', string='Responsible', ondelete='set null')
    vertex_ids = fields.One2many('company.asset.vertex', 'area_id')
    # asset_ids = fields.One2many('company.asset.item', 'floor_id')
    area_type = fields.Selection([
        ('room', 'Room'),
        ('area', 'Area'),
    ], default='room')
    floor_id = fields.Many2one('company.asset.floor', ondelete='cascade')
    building_id = fields.Many2one('company.asset.building', related='floor_id.building_id', ondelete='cascade')


class CompanyAssetVertex(models.Model):
    _name = 'company.asset.vertex'
    _description = "Company Asset Vertex Model"

    area_id = fields.Many2one('company.asset.area', ondelete='cascade')
    x = fields.Float(digits=(16, 5))
    y = fields.Float(digits=(16, 5))


class CompanyAssetEquipmentType(models.Model):
    _name = 'company.asset.equipment.type'
    _description = "Company Asset Equipment Type Model"
    _order = 'name'

    _RIP_GET_FIELDS = (
        'id',
        'name', 'description',
        ('product_id.id', 'product_id'),
        ('checkin_rule_id.id', 'checkin_rule_id'),
        ('asset_type_ids.id', 'asset_type_ids'),
    )

    name = fields.Char(required=True)
    code = fields.Char()
    description = fields.Char()
    product_id = fields.Many2one('product.product', ondelete='set null')
    checkin_rule_id = fields.Many2one('company.asset.checkin.rule', ondelete='set null')
    asset_type_ids = fields.Many2many('company.asset.type')


class CompanyAssetEquipment(models.Model):
    _name = 'company.asset.equipment'
    _description = "Company Asset Equipment Model"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = 'name'

    _RIP_GET_FIELDS = (
        'id',
        'name', 'description',
        ('type_id.id', 'type_id'),
        ('asset_item_id.id', 'asset_item_id'),
        ('maintenance_equipment_id.id', 'maintenance_equipment_id'),
    )

    name = fields.Char(required=True)
    code = fields.Char()
    description = fields.Char()
    type_id = fields.Many2one('company.asset.equipment.type', ondelete='set null')
    asset_item_id = fields.Many2one('company.asset.item', ondelete='set null')
    maintenance_equipment_id = fields.Many2one('maintenance.equipment', ondelete='set null')


class CompanyAssetReservation(models.Model):
    _name = 'company.asset.reservation'
    _description = "Company Asset Reservation Model"
    _order = 'date_from'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    _RIP_GET_FIELDS = (
        'id',
        'code', 'name', 'description',
        ('asset_item_id.id', 'asset_item_id'),
        ('reserved_by_id.id', 'reserved_by_id'),
        ('reserved_by_id.name', 'reserved_by_name'),
        'date_from',
        'date_to',
        'date_checkin',
        'date_checkout',
    )

    # INFO: if reserved_by_id is missing, forces current user partner_id.
    def _rip_reserved_by_id(self, user, args):
        _logger.info("user (_rip_post_check_user)=%s", user.id)
        if 'reserved_by_id' not in args:
            return {'reserved_by_id': user.partner_id.id}
        return {}

    _RIP_POST_FIELDS = (
        'code', 'name', 'description',
        '*asset_item_id',
        'reserved_by_id',
        '*date_from',
        '*date_to',
        _rip_reserved_by_id,
        'date_checkin',
        'date_checkout',
    )

    code = fields.Char(related='asset_item_id.code', store=True)
    name = fields.Char(compute="_compute_name", store=False)
    description = fields.Char()
    asset_item_id = fields.Many2one('company.asset.item', ondelete='cascade')
    user_id = fields.Many2one('res.users', ondelete='set null')
    reserved_by_id = fields.Many2one('res.partner', string='Reserved By', ondelete='set null')
    date_from = fields.Datetime(tracking=True)
    date_to = fields.Datetime(tracking=True)
    x = fields.Float(related='asset_item_id.x')
    y = fields.Float(related='asset_item_id.y')
    date_checkin = fields.Datetime(tracking=True)
    date_checkout = fields.Datetime(tracking=True)
    reservation_time = fields.Integer(compute='')
    total_time = fields.Integer(compute='')

    @api.depends('date_from', 'asset_item_id', 'reserved_by_id')
    def _compute_name(self):
        for a in self:
            if a.date_from and a.asset_item_id and a.reserved_by_id:
                a.name = '%s-%s-%s' % (a.date_from.strftime("%d-%m-%y"), a.asset_item_id.name, a.reserved_by_id.name)
            else:
                a.name = False

    # INFO: post function endpoint.
    def set_checkinout(self, user, rec, vals, fvals):
        code = vals.get('code', False)
        date_checkin = fvals.get('date_checkin', False)
        date_checkout = fvals.get('date_checkout', False)

        # TODO: check reservation code related to the user.
        if rec:
            if code and not self.env['company.asset.reservation'].search([('code', '=', code)], limit=1):
                raise ValidationError(_("Code does not match"))
            if date_checkin:
                rec.date_checkin = date_checkin
            if date_checkout:
                rec.date_checkout = date_checkout
            return rec
        raise ValidationError(_("Reservation not found"))

    def get_reserved(self, user, rec, vals, fvals):
        user_id = vals.get('user', user.id)
        return False, self.sudo().search(['&', ('user_id', '=', user_id), ('date_checkout', '=', False)]), False

    def get_checkedout(self, user, rec, vals, fvals):
        user_id = vals.get('user', user.id)
        return False, self.sudo().search(['&', ('user_id', '=', user_id), ('date_checkout', '!=', False)]), False

    def set_reservation(self, user, rec, vals, fvals):
        # TODO: implement a user param to pass someone different than reserved_by_id.
        company_asset_item = self.env['company.asset.item']
        asset_id = fvals.get('asset_item_id')
        code = fvals.get('code', False)
        asset_id = asset_id and company_asset_item.browse(asset_id) or code and company_asset_item.search([('code', '=', code)])
        if asset_id and asset_id.exists():
            date_from = fvals.get('date_from')
            date_to = fvals.get('date_to')
            # INFO: searches for overlapped dates, if so then you cannot reserve because time has been already booked.
            if not self.search([('date_from', '<=', date_to), ('date_to', '>=', date_from)], limit=1).exists():
                rec = self.create({
                    'name': fvals.get('name', ''),
                    'description': fvals.get('description'  ''),
                    'user_id': user.id,
                    'reserved_by_id': fvals.get('reserved_by_id', user.partner_id.id),
                    'date_from': date_from,
                    'date_to': date_to,
                    'asset_item_id': asset_id.id
                })
                return rec
            return make_response(400, 1001, _("Time already booked"))
        return make_response(404, 0, _("Asset not found"))


class CompanyAssetReservationRule(models.Model):
    _name = 'company.asset.reservation.rule'
    _description = "Company Asset Reservation Rule Model"
    _order = 'name'

    name = fields.Char(required=True)
    model = fields.Char(default="res.partner")
    domain = fields.Char()
    group_ids = fields.Many2many('res.partner.category')



class CompanyAssetCheckinRule(models.Model):
    _name = 'company.asset.checkin.rule'
    _description = "Company Asset Checkin Rule Model"
    _order = 'name'

    name = fields.Char(required=True)
    minutes_before_checkin = fields.Integer('Minutes minimum before checkin')
    minutes_to_unreserve = fields.Integer('Minutes after reservation to unreserve')
    qrcode_only = fields.Boolean('Checkin only with qrcode')
    automated_checkin = fields.Boolean('Checkin automated in real time reservation')


class CompanyAssetType(models.Model):
    _name = 'company.asset.type'
    _inherit = ['image.mixin']
    _description = "Company Asset Type Model"
    _order = 'name'

    _RIP_GET_FIELDS = (
        'id',
        'name', 'description',
        '{icon_urls}',
        '{image_urls}',
        'reservation_type',
        ('reservation_rule_id.id', 'reservation_rule_id'),
        ('checkin_rule_id.id', 'checkin_rule_id'),
    )

    icon = fields.Image("Icon", max_width=32, max_height=32)
    name = fields.Char(required=True)
    code = fields.Char()
    description = fields.Char()
    reservation_type = fields.Selection([
        ('mono', 'Mono place'),
        ('multi', 'Multi places'),
    ], default='mono')
    reservation_rule_id = fields.Many2one('company.asset.reservation.rule',  ondelete='set null')
    checkin_rule_id = fields.Many2one('company.asset.checkin.rule', ondelete='set null')

    icon_urls = fields.Char('Icon URLs', compute='_compute_icon_urls', store=False)
    image_urls = fields.Char('Image URLs', compute='_compute_image_urls', store=False)

    valuation_ids = fields.One2many('company.asset.valuation', 'asset_type_id')

    @api.depends('icon')
    def _compute_icon_urls(self):
        for rec in self:
            _id= rec.id
            rec.icon_urls = json.dumps({
                "icon": "/sydrestapi/v1/redirect?url=/web/image/company.asset.type/%d/icon" % _id,
            })

    @api.depends('image_128', 'image_256', 'image_512', 'image_1024', 'image_1920')
    def _compute_image_urls(self):
        for rec in self:
            _id = rec.id
            rec.image_urls = json.dumps({
                "image_128": "/sydrestapi/v1/redirect?url=/web/image/company.asset.type/%d/image_128" % _id,
                "image_256": "/sydrestapi/v1/redirect?url=/web/image/company.asset.type/%d/image_256" % _id,
                "image_512": "/sydrestapi/v1/redirect?url=/web/image/company.asset.type/%d/image_512" % _id,
                "image_1024": "/sydrestapi/v1/redirect?url=/web/image/company.asset.type/%d/image_1024" % _id,
                "image_1920": "/sydrestapi/v1/redirect?url=/web/image/company.asset.type/%d/image_1920" % _id
            })


class CompanyAssetItem(models.Model):
    _name = 'company.asset.item'
    _description = "Company Asset Item Model"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = 'code, name'

    _RIP_GET_FIELDS = (
        'id',
        'code', 'name', 'description',
        ('type_id.id', 'type_id'),
        ('type_id.name', 'type_name'),
        ('floor_id.id', 'floor_id'),
        ('floor_id.floor_plan_url', 'floor_plan_url'),
        ('building_id.id', 'building_id'),
        ('responsible_id.id', 'responsible_id'),
        'max_places',
        'reservation_type',
        ('reserved_by_id.id', 'reserved_by_id'),
        'x', 'y',
        'state',
        ('equipment_ids.id', 'equipment_ids'),
        'last_affinity_percent',
        'notes',
    )

    parent_id = fields.Many2one('company.asset.item')
    code = fields.Char()
    qrcode = fields.Binary(compute='_compute_qrcode', attachment=False, store=True, readonly=True)
    name = fields.Char(required=True)
    description = fields.Char()
    type_id = fields.Many2one('company.asset.type',required=True)
    floor_id = fields.Many2one('company.asset.floor', ondelete='cascade')
    building_id = fields.Many2one(related='floor_id.building_id')
    # area_id = fields.Many2one('company.asset.area', ondelete='set null')
    responsible_id = fields.Many2one('res.users', string='Responsible', ondelete='set null')
    max_places = fields.Integer(default=1)
    reservation_type = fields.Selection([
        ('no', 'Not reservable'),
        ('yes', 'Reservable'),
        ('auto', 'Auto'),
    ], default='yes')
    reserved_by_id = fields.Many2one('res.partner', string='Reserved By', ondelete='set null')
    x = fields.Float(digits=(3, 5))
    y = fields.Float(digits=(3, 5))

    state = fields.Selection([
        ('reserved', 'Reserved'),
        ('free', 'Free'),
    ], default='free')
    product_id = fields.Many2one('product.product', ondelete='set null')
    maintenance_equipment_id = fields.Many2one('maintenance.equipment', ondelete='set null')
    reservation_rule_id = fields.Many2one('company.asset.reservation.rule',  ondelete='set null')
    checkin_rule_id = fields.Many2one('company.asset.checkin.rule', ondelete='set null')

    active_checkin_rule_id = fields.Many2one('company.asset.checkin.rule', compute="_active_checkin_rule_id")
    active_reservation_rule_id = fields.Many2one('company.asset.reservation.rule', compute="_active_reservation_rule_id")

    equipment_ids = fields.One2many('company.asset.equipment', 'asset_item_id')
    notes = fields.Char()

    valuation_ids = fields.One2many('company.asset.valuation', 'asset_item_id')

    last_affinity_percent = fields.Float(digits=(3, 2), default=0.0)

    def _active_reservation_rule_id(self):
        for a in self:
            if a.reservation_rule_id :
                a.active_reservation_rule_id = a.reservation_rule_id.id
            elif a.type_id.reservation_rule_id :
                a.active_reservation_rule_id = a.type_id.reservation_rule_id.id

    def _active_checkin_rule_id(self):
        for a in self:
            if a.checkin_rule_id :
                a.active_checkin_rule_id = a.checkin_rule_id.id
            elif a.type_id.checkin_rule_id :
                a.active_checkin_rule_id = a.type_id.checkin_rule_id.id


    @api.depends('code')
    def _compute_qrcode(self):
        for rec in self:
            if rec.code:
                data = io.BytesIO()
                import qrcode
                qrcode.make('code=%s' % rec.code, box_size=4).save(data, optimise=True, format='PNG')
                rec.qrcode = base64.b64encode(data.getvalue()).decode()
            else:
                rec.qrcode = False

    # INFO: get function endpoint.
    def get_floor_plan_pin_included(self, user, rec, vals, fvals):
        w = vals.get('width', 1000)
        h = vals.get('height', 1000)
        a_style = vals.get('a_style', "background-color:#fb7575;border-radius:6px;width:12px;height:12px;margin:-6px 0 0 -6px;")
        s = False
        if rec.floor_id:
            s = f'''<?xml version="1.0" encoding="utf-8" ?>
<style>.pin-map{{position:absolute;left:{rec.x*100}%;top:{rec.y*100}%;{a_style}}}</style>
<div style="position:absolute;width:{w}px;height:{h}px;">
<a class="pin-map"></a>
<svg baseProfile="full" height="{w}" version="1.1" width="{h}" xmlns="http://www.w3.org/2000/svg" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:xlink="http://www.w3.org/1999/xlink">
<image width="{w}" height="{h}" xlink:href="{rec.floor_id.floor_plan_absolute_url}"/>
</svg>
</div>'''
        # INFO: returning byte encoded to return a pure HTML content.
        return False, False, s and s.encode()

    def to_json(self):
        return {
            'id': self.id,
            'title': self.name,
            'about': '',
            'description': self.description,
            'category': '',
            'x': str(self.x),
            'y': str(self.y),
        }


class CompanyAssetValuation(models.Model):
    _name = 'company.asset.valuation'
    _order = 'sequence'

    asset_item_id = fields.Many2one('company.asset.item', ondelete='set null')
    asset_type_id = fields.Many2one('company.asset.type', ondelete='set null')

    sequence = fields.Integer()
    type_id = fields.Many2one('company.asset.valuation.type')
    score = fields.Float(digits=(4, 2))


class CompanyAssetValuationType(models.Model):
    _name = 'company.asset.valuation.type'
    _order = 'sequence'

    sequence = fields.Integer()
    code = fields.Char()
    name = fields.Char()
