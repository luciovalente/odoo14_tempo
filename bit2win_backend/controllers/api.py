# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import json
from odoo.http import Controller, request, route, Response
import logging


_logger = logging.getLogger(__name__)


class ApiController(Controller):

    @route('/bit2win/ping', auth='public', type='http',
           methods=['GET', 'OPTIONS'], cors='*')
    def ping(self):
        _logger.error(request.httprequest.headers)
        if request._is_cors_preflight(request.endpoint):
            headers = {
                'Access-Control-Max-Age': 60 * 60 * 24,
                'access-control-allow-headers': 'Origin, X-Requested-With, Content-Type, Accept, Authorization, access-control-allow-headers'
            }
            return Response(status=200, headers=headers)
        result = {'result': 'pong'}
        return json.dumps(result)

    @route('/bit2win/add_line/<int:order_id>', auth='public', type='http',
           methods=['GET'], cors='*')
    def add_line(self, order_id, **params):
        product_code = params['product_code']
        quantity = params['quantity']
        price = params['price']
        line_model = request.env['sale.order.line'].sudo()
        product_model = request.env['product.product'].sudo()
        product = product_model.search(
            [('default_code', '=', product_code)], limit=1)
        line_data = {
            'product_id': product.id,
            'name': product.name_get()[0][1],
            'order_id': order_id,
            'product_uom_qty': quantity,
            'price_unit': price,
            }
        line = line_model.create(line_data)
        result = {'result': {'id': line.id}}
        return json.dumps(result)
