# -*- coding: utf-8 -*-

from odoo import fields, models, api


PRIORITY = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'High'),
    ('3', 'Very High')
]
class ResPartner(models.Model):
    _inherit = 'res.partner' 
    
    state = fields.Selection([
                              ('prospect','Prospect'),
                              ('active','Active'),
                              ('suspended','Suspended'),
                              ('blocked','Blocked'),
                              ('inactive','Inactive')
                              ])
    is_customer = fields.Boolean(default=True)
    is_vendor = fields.Boolean(default=False)
    is_partner = fields.Boolean(default=False)
    is_competitor = fields.Boolean(default=False)
    contact_ids = fields.One2many('res.partner.role','crm_account_id',string="Contacts")
    crm_account_ids = fields.One2many('res.partner.role','contact_partner_id',string="Accounts")
    ticket_ids = fields.One2many('helpdesk.ticket','partner_id')
    fraud_check = fields.Selection(PRIORITY, string='Fraud Check', default='0')
    credit_check = fields.Float()
    internal_check =  fields.Float()
    crm_quote_ids = fields.Many2many('sale.order',compute="_orders")
    crm_order_ids = fields.Many2many('sale.order',compute="_orders")
    subscription_ids = fields.One2many('sale.subscription','partner_id','Subscription')
    
    flag_data_management = fields.Boolean('Accept Data Management')
    flag_campaign = fields.Boolean('Accept Marketing Campaign')
    flag_profilation = fields.Boolean('Accept Profilation')
    flag_external = fields.Boolean('Accept External Access')
    
    
    contact_method = fields.Selection([('mail','Mail'),
                                       ('phone','Phone'),
                                       ('pec','Pec'),
                                       ('telegram','Telegram'),
                                       ('mail','Mail')])
    
    
    employee_count = fields.Integer('Number of Employee')
    revenue = fields.Float('Revenue')
    document_ids = fields.One2many('documents.document','partner_id','Subscription')
    campaign_ids = fields.Many2many('marketing.campaign',string='Campaigs',compute="_campaigns")
    
    
    def _campaigns(self):
        for a in self:
            mp = self.env['marketing.participant'].search([('model_name','=','res.partner'),('res_id','=',a.id)])
            cp = []
            for m in mp:
                cp.append(m.campaign_id.id)
            a.campaign_ids = cp
    
    
    
    def _orders(self):
        for a in self:
            quote_ids = self.env['sale.order'].search([('partner_id','=',a.id),('state','in',('draft','sent'))]).ids
            order_ids = self.env['sale.order'].search([('partner_id','=',a.id),('state','=','order')]).ids
            a.crm_quote_ids = quote_ids
            a.crm_order_ids = order_ids

class PartnerRole(models.Model):
    _name = 'res.partner.role'
    _description = 'Partner Role'
    _inherits = {'res.partner': 'contact_partner_id'}
    
    crm_account_id = fields.Many2one('res.partner',string="Account")
    contact_partner_id = fields.Many2one('res.partner',string="Contact",auto_join=True, index=True, ondelete="cascade", required=True)
    role = fields.Char('Role')
    
class HelpdeskTicketMacroType(models.Model):
    _name = 'helpdesk.ticket.macro_type'
    _description = 'Helpdesk Ticket Macro Type'
    _order = 'sequence'

    name = fields.Char('Type', required=True, translate=True)
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Type name already exists !"),
    ]
    
class HelpdeskTicketSubType(models.Model):
    _name = 'helpdesk.ticket.sub_type'
    _description = 'Helpdesk Ticket Sub Type'
    _order = 'sequence'

    name = fields.Char('Type', required=True, translate=True)
    sequence = fields.Integer(default=10)
    macro_type_id = fields.Many2one('helpdesk.ticket.macro_type',string="Macro Type")
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Type name already exists !"),
    ]
    
class HelpdeskTicketType(models.Model):
    _inherit = 'helpdesk.ticket.type'
    
    macro_type_id = fields.Many2one('helpdesk.ticket.macro_type',string="Macro Type")
    sub_type_id = fields.Many2one('helpdesk.ticket.sub_type',string="Sub Type",domain="[('macro_type_id','=',macro_type_id)]")

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'
    
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string="Ticket Type",domain="[('sub_type_id','=',sub_type_id)]")
    sub_type_id = fields.Many2one('helpdesk.ticket.sub_type',string="Sub Type",domain="[('macro_type_id','=',macro_type_id)]")
    macro_type_id = fields.Many2one('helpdesk.ticket.macro_type',string="Macro Type")
