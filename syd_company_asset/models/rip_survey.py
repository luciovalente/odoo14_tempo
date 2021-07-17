# -*- coding: utf-8 -*-

from odoo import _, api, models, fields
from random import random

class RIPSurvey(models.Model):
    _inherit = 'rip.survey'

    # INFO: inherits from rip.survey when evaluating.
    def evaluate(self, user, rec, params, form_vals):
        rec, recs, content = super(RIPSurvey, self).evaluate(user, rec, params, form_vals)
        for rec in recs:
            rec.last_affinity_percent = random() * 100
        return False, recs, False
