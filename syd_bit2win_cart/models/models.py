# -*- coding: utf-8 -*-
# © 2019 SayDigital s.r.l.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import datetime, calendar
from dateutil.relativedelta import relativedelta
from odoo import api, exceptions, fields, models, _,SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, ValidationError
from werkzeug import urls
import calendar
from odoo import tools
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_join
from odoo.tools.safe_eval import safe_eval
from odoo.osv import expression 
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from collections import defaultdict

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    def open_sale_order_cart(self):
        action = self.env.ref('syd_bit2win_cart.action_care_app').read()[0]
        
        return action