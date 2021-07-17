# -*- coding: utf-8 -*-

from odoo.http import request, Response

import re
import json
import functools
import jwt
from datetime import datetime, timedelta

import logging
_logger = logging.getLogger(__name__)


def make_response(status, code, message, headers=None, acao=True):
    if type(message) == dict:
        message = json.dumps(message)
    elif type(message) == str:
        # INFO: only if a message string then clean it (e.g.: in case of message from exception.)
        message = '"%s"' % re.sub('\s+', ' ', message.replace('"', "'"))
    if 200 <= status < 300:
        result = Response(message, status=status, headers=headers)
        if acao:
            result.headers.set('Access-Control-Allow-Origin', request.httprequest.headers.get('origin', '*'))
        _logger.info('OK Response %s.Headers=%s', request.httprequest.method, result.headers)
        _logger.info("OK Response (%d, %d) <%s>" % (status, code, message))
    else:
        result = Response('{"code": %d, "message": %s}' % (code, message), status=status, headers=headers)
        _logger.error('ERROR %s.Headers=%s', request.httprequest.method, result.headers)
        _logger.error("ERROR Response (%d, %d) <%s>" % (status, code, message))

    if acao:
        result.headers.set('Access-Control-Allow-Origin', request.httprequest.headers.get('origin', '*'))

    return result


# INFO: builds the token from a payload dictionary.
def _build_token(secret, algorithm, uid, exp):
    payload = {
        'uid': uid,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=int(exp))
    }
    return jwt.encode(payload, secret, algorithm)


# INFO: adds options response and ACAO required for cors call (do not use cors='' parameter in route because conflicts).
def enable_cors_preflight(func):

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            headers = {
                'Access-Control-Max-Age': 60 * 60 * 24,
                'Access-Control-Allow-Headers': 'Accept,Authorization,Cache-Control,Content-Type,DNT,If-Modified-Since,Range,Origin,Content-Type,Postman-Token,User-Agent,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
                'Allow': 'OPTIONS',
                'Referrer-Policy': 'origin',
                'Content-Type': 'text/plain; charset=utf-8',
                'Content-Length': 0
            }
            return make_response(204, 0, "OK", headers=headers)

        result = func(self, *args, **kwargs)

        if request.httprequest.headers.get('Authorization'):
            result.headers['Access-Control-Allow-Origin'] = request.httprequest.headers.get('origin', '*')

        return result

    return wrapper


# INFO: This does not set ACAO and ACAC policy because Odoo.sh, probably during redirect, dirty headers of responses
#       (injecting ac-Allow-Origin and ac-Allow-Credentials).
def enable_cors_preflight_no_acao(func):

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            headers = {
                'Access-Control-Max-Age': 60 * 60 * 24,
                'Access-Control-Allow-Headers': 'Accept,Authorization,Cache-Control,Content-Type,DNT,If-Modified-Since,Range,Origin,Content-Type,Postman-Token,User-Agent,X-Requested-With',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
                'Allow': 'OPTIONS',
                'Referrer-Policy': 'origin',
                'Content-Type': 'text/plain; charset=utf-8',
                'Content-Length': 0
            }
            return make_response(204, 0, "OK", headers=headers, acao=False)

        return func(self, *args, **kwargs)

    return wrapper


# INFO: extracts company from user request or company_id if passed as a request argument.
def company_from_request(func):

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        user = kwargs.get('__user')
        kwargs['__company'] = user and user.company_id or request.env.company

        # INFO: checks if request is related to a different company.
        company_id = kwargs.get('company_id')
        if company_id:
            # INFO: sets company from request args or, if missing, from user.company_id.
            try:
                company = request.env.company.browse(int(company_id))
            except ValueError:
                company = False

            if company and company.exists():
                # INFO: stores selected company.
                kwargs['__company'] = company
            else:
                return make_response(401, 61, "Invalid Company request <%s>" % company_id)

        return func(self, *args, **kwargs)

    return wrapper


# INFO: checks token validity and return id of the user into the wrapped func.
def verify_user_auth_token(func):

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):

        try:
            token = False
            if request.httprequest.method == 'GET':
                token = kwargs.get('auth_token', False)
            if not token:
                authorization = request.httprequest.headers.get('Authorization', '').split(' ')
                token = authorization[0].lower() == 'bearer' and len(authorization) > 1 and authorization[1]

            if token:
                company = request.env.company

                icp = request.env['ir.config_parameter'].sudo()

                secret = icp.get_param('syd_rip.secret')
                algorithm = icp.get_param('syd_rip.algorithm')

                payload = jwt.decode(token, secret, algorithms=[algorithm])

                user = request.env['res.users'].browse(payload.get('uid', False)).sudo().exists()
                if user:
                    # INFO: stores selected user.
                    kwargs['__user'] = user
                else:
                    return make_response(401, 21, "Invalid User request")

                return func(self, *args, **kwargs)

            else:
                return make_response(401, 31, "Access token not found")

        except jwt.exceptions.ExpiredSignatureError:
            return make_response(401, 41, "Access token has expired")

        except jwt.exceptions.InvalidTokenError:
            return make_response(401, 51, "Invalid access Token")

    return wrapper


# DEPRECATED
# INFO: checks token validity and return id of the user into the wrapped func.
# def sudo_self_from_auth_token(func):
#
#     @functools.wraps(func)
#     def wrapper(self, *args, **kwargs):
#
#         try:
#             # INFO: forces sudoing self when valid auth_token in hedaers.
#             authorization = request.httprequest.headers.get('Authorization', '').split(' ')
#             token = authorization[0].lower() == 'bearer' and len(authorization) > 1 and authorization[1]
#
#             company = request.env.company
#
#             if token:
#                 payload = jwt.decode(token, company.syd_rip_secret, algorithms=[company.syd_rip_algorithm])
#                 kwargs['__user_id'] = payload.get('uid', False)
#                 if getattr(self, 'sudo', False):
#                     self = self.sudo()
#         finally:
#             return func(self, *args, **kwargs)
#
#     return wrapper
