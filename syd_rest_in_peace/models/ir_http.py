# -*- coding: utf-8 -*-

from odoo import models
# from odoo.addons.syd_rest_in_peace.core import sudo_self_from_auth_token

import logging
_logger = logging.getLogger(__name__)


class RIPIrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    # TODO: reenable su @sudo_self_from_auth_token so to let sudoing when auth_token.
    # @sudo_self_from_auth_token
    def _get_record_and_check(self, xmlid=None, model=None, id=None, field='datas', access_token=None, **kwargs):
        # INFO: when @sudo_self_from_auth_token is back then remove line below.
        self = self.sudo()
        return super(RIPIrHttp, self)._get_record_and_check(xmlid, model, id, field, access_token)
