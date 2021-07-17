# -*- coding: utf-8 -*-

from odoo import _, api, models, fields
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class RIPSurvey(models.Model):
    _name = 'rip.survey'
    _order = 'sequence, name'

    _RIP_GET_FIELDS = (
        'id',
        'name', 'description',
        'page_ids'
    )

    sequence = fields.Integer()
    name = fields.Char(required=True)
    description = fields.Char(default='')
    page_ids = fields.One2many('rip.survey.page', 'survey_id')
    model_id = fields.Many2one('ir.model', 'Target Model', required=True, ondelete='cascade')
    code_to_eval = fields.Text()

    available_field_names = fields.Char(compute='_compute_available_field_names', store=False)

    @api.depends('page_ids.question_ids')
    def _compute_available_field_names(self):
        for rec in self:
            rec.available_field_names = ', '.join(rec.page_ids.question_ids.mapped('field_name') or [])

    # INFO: get function endpoint.
    def evaluate(self, user, rec, params, form_vals):
        self = rec.sudo()
        form_vals.update({'rec': self})
        # INFO: form_vals as local variables.
        domain = rec.code_to_eval and safe_eval(rec.code_to_eval, {}, form_vals) or [(),]

        # INFO: looks for domain, use 'limit' from endpoint params (if exists).
        return False, self.model_id and self.env[self.model_id.model].sudo().search([domain],
            limit=params.get('limit', 1)) or False, False


class RIPSurveyPage(models.Model):
    _name = 'rip.survey.page'
    _order = 'sequence, name'

    _RIP_GET_FIELDS = (
        'id',
        'name', 'description',
        'question_ids'
    )

    survey_id = fields.Many2one('rip.survey', ondelete='cascade')

    sequence = fields.Integer()
    name = fields.Char(required=True)
    description = fields.Char(default='')
    help = fields.Char(default='')
    question_ids = fields.One2many('rip.survey.question', 'page_id')


class RIPSurveyQuestion(models.Model):
    _name = 'rip.survey.question'
    _order = 'sequence, name'

    _RIP_GET_FIELDS = (
        'id',
        'name', 'description', 'help',
        'type',
        'field_name',
        'choice_ids'
    )

    page_id = fields.Many2one('rip.survey.page', ondelete='cascade')
    survey_id = fields.Many2one(related='page_id.survey_id', store=False)

    sequence = fields.Integer()
    name = fields.Char(required=True)
    description = fields.Char(default='')
    help = fields.Char(default='')
    type = fields.Selection([
        ('date', 'Date'),
        ('date_range', 'Date Range'),
        ('number', 'Number'),
        ('float', 'Float'),
        ('selection', 'Selection'),
        ('checkbox', 'Checkbox'),
        ('radio', 'Radio'),
        ('slider', 'Slider'),
        ('text', 'Text'),
    ], required=True, default='selection')
    field_name = fields.Char(required=True, default='')
    # INFO: possible choices for 'selection', 'checkbox', 'radio'.
    choice_ids = fields.One2many('rip.survey.question.choice', 'question_id')

    # INFO: be sure question field name is unique per survey.
    @api.onchange('field_name')
    def _onchange_field_name(self):
        for page in self.survey_id.page_ids:
            for q in page.question_ids:
                if self != q and self.field_name == q.field_name:
                    raise ValidationError(_("Field Name must be unique per Survey."))


class RIPSurveyQuestionChoice(models.Model):
    _name = 'rip.survey.question.choice'
    _order = 'sequence, name'

    _RIP_GET_FIELDS = (
        'id',
        'name', 'description', 'help',
        'field_value',
    )

    question_id = fields.Many2one('rip.survey.question')

    sequence = fields.Integer()
    name = fields.Char(required=True)
    description = fields.Char(default='')
    help = fields.Char(default='')
    field_value = fields.Char(required=True)
