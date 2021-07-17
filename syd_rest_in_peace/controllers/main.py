# -*- coding: utf-8 -*-

import re
import json
from base64 import b64decode
from datetime import datetime

from odoo import http, models
from odoo.http import request, Response
from odoo.exceptions import AccessDenied
from odoo.addons.web.controllers.main import Binary

from odoo.addons.syd_rest_in_peace.core import _build_token, make_response, enable_cors_preflight,\
    verify_user_auth_token, enable_cors_preflight_no_acao, company_from_request

from werkzeug.utils import redirect

import logging
_logger = logging.getLogger(__name__)


class RIPController(http.Controller):

    @enable_cors_preflight
    @http.route('/sydrestapi/v1/auth', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, save_session=False)
    def get_auth(self, **args):

        authorization = request.httprequest.headers.get('Authorization', '').split(' ')
        if authorization[0].lower() == 'basic':
            cred = str(b64decode(len(authorization) > 1 and authorization[1] or ''), 'utf8').split(':', 1)

            user = len(cred) > 0 and cred[0]
            password = len(cred) > 1 and cred[1]

            try:
                uid = request.session.authenticate(request.env.cr.dbname, user, password)
                _logger.info('Authenticated User ID <%s>.', uid)
            except AccessDenied:
                return make_response(401, 1, "Wrong username and/or password")

            icp = request.env['ir.config_parameter'].sudo()

            secret = icp.get_param('syd_rip.secret')
            algorithm = icp.get_param('syd_rip.algorithm')
            access_token_exp = icp.get_param('syd_rip.access_token_exp')
            refresh_token_exp = icp.get_param('syd_rip.refresh_token_exp')

            # INFO: builds tokens blending expirations.
            resp = {
                'user_id': uid,
                'access_token': _build_token(secret, algorithm, uid, access_token_exp).decode('UTF-8'),
                'refresh_token': _build_token(secret, algorithm, uid, refresh_token_exp).decode('UTF-8'),
                'expires_in': access_token_exp
            }
            return make_response(200, 0, resp)

        return make_response(401, 11, "Invalid authorization request")

    @enable_cors_preflight
    @verify_user_auth_token
    @http.route('/sydrestapi/v1/auth/refresh', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, save_session=False)
    def get_refresh(self, **kwargs):

        company = request.env.company

        user = kwargs['__user']

        return make_response(200, 0, {
            'user_id': user.id,
            'access_token': _build_token(company.syd_rip_secret, company.syd_rip_algorithm, user.id, company.sys_rip_access_token_exp).decode('UTF-8'),
            'refresh_token': _build_token(company.syd_rip_secret, company.syd_rip_algorithm, user.id, company.syd_rip_refresh_token_exp).decode('UTF-8'),
            'expires_in': company.sys_rip_access_token_exp,
        })

    @staticmethod
    def convert_value_to_string(val, is_dict=False):
        if is_dict:
            # INFO: forces empty json because otherwise error on false bool being converted to json.
            return json.loads(val or '{}')
        elif type(val) == bytes:
            return val.decode('utf8')
        elif type(val) == datetime:
            return val.isoformat()

        return val

    def _explode(self, field_name, field_type, recs, explode=None, include=None):

        if include is None:
            include = []
        if explode is None:
            explode = []
        res = []
        for rec in recs:
            res_rec = {}

            # INFO: managing fields type
            #       - .FIELD: hidden field to be parsed only if in 'include'
            #       - {FIELD}: Value of the FIELD will be parsed as JSON
            #       - ('FIELD', 'ALIAS'): Value of FIELD will be returned as ALIAS
            #       - ('.FIELD', 'ALIAS')
            #       - ('{FIELD}', 'ALIAS')
            for f in getattr(rec, '_RIP_GET_FIELDS', []):
                f_is_tuple = False
                f_is_dict = False
                f_dest = f

                # INFO: checks if 'f' is a tuple, in this case there is a pretty field name to output into json.
                if isinstance(f, tuple):
                    f_dest = len(f) > 1 and f[1] or f[0]
                    f = f[0]
                    f_is_tuple = True

                # INFO: if it's an hidden field then remove initial dot and check if it is 'include'.
                if f[0] == '.':
                    f = f_dest in include and f[1:] or ''
                    if not f_is_tuple:
                        f_dest = f
                elif f[0] == '{':
                    f = f.strip('{}')
                    if not f_is_tuple:
                        f_dest = f
                    f_is_dict = True

                # INFO: in case 'f' had been reset because not 'include'.
                if f:
                    names = f.split('.')
                    if len(names) > 1:
                        # INFO: builds full_name of the model.
                        full_name = (field_name and (field_name + '.') or '') + names[0]

                        # INFO: if full_name is in explode then dig in.
                        if full_name in explode:
                            # INFO: removes full_name from 'explode' list to avoid unwanted explosion while digging in.
                            # explode.remove(full_name)
                            res_rec[names[0]] = self._explode(full_name, False, rec[names[0]], explode, include)
                        else:
                            bm = rec.mapped(f)
                            res_rec[f_dest] = self.convert_value_to_string(len(bm) == 1 and bm[0] or bm or '', f_is_dict)
                    else:
                        # INFO: if field name references a model then auto explode it.
                        if isinstance(rec[f], models.Model):
                            res_rec[f_dest] = self._explode(f, rec._fields.get(f_dest).get_description(rec.env).get('type'), rec[f], explode, include)
                        else:
                            res_rec[f_dest] = self.convert_value_to_string(rec[f], f_is_dict)
            res += [res_rec]
        # INFO: returns a list if input recs is an array or first element if recs was not.
        return (len(res) == 1 and ((field_type and field_type not in ['one2many', 'many2many']) or not field_type) and res[0]) or res

    # INFO: only entry point to preflight requests form clients (e.g.: Ionic app).
    @enable_cors_preflight
    @http.route(
        [
            '/sydrestapi/v1/<string:model>',
            '/sydrestapi/v1/<string:model>/<int:id>',
            '/sydrestapi/v1/<string:model>/<string:func>',
            '/sydrestapi/v1/<string:model>/<string:func>/<int:id>',
        ],
        type='http', auth='public', methods=['OPTIONS'], csrf=False, save_session=False)
    def options_(self):
        _logger.info('Request %s.Headers=%s', request.httprequest.method, request.httprequest.headers)
        return

    @enable_cors_preflight
    @verify_user_auth_token
    @company_from_request
    @http.route([
        '/sydrestapi/v1/<string:model>',
        '/sydrestapi/v1/<string:model>/<int:id>',
        '/sydrestapi/v1/<string:model>/<string:func>',
        '/sydrestapi/v1/<string:model>/<string:func>/<int:id>',
    ], type='http', auth='public', methods=['GET'], csrf=False, save_session=False)
    def get_(self, model, func='', id=False, pages='', items_per_page='20', explode='', include='', filter='', **kwargs):
        _logger.info('Request %s.Headers=%s', request.httprequest.method, request.httprequest.headers)
        mod = request.env.get(model)
        if isinstance(mod, models.BaseModel):
            try:
                user = kwargs['__user']
                company = kwargs['__company']
                _logger.info('Company ID <%s>.', company.id)
                _logger.info('User ID from token <%s>.', user.id)

                # INFO: raises rights to do any kind of operations during this REST call.
                mod = mod.with_user(user).with_company(company).sudo()

                recs = False
                content = False
                # INFO: checks if a function of the model has been queried.
                func = func and getattr(mod, func)
                if func:
                    # INFO: a functional endpoint needs to return id (and "one" recs if it implies a record fetch) or
                    #       a false id and more recs (if it implies more records fetching).
                    rec = False
                    if id:
                        rec = mod.browse(id)
                        rec = rec.exists() and rec
                    # INFO: execute function endpoint.
                    #       Returning:
                    #       rec = if returns a record
                    #       recs = if returns bunch of records
                    #       content = if returns a content (like image)
                    fvals = {}
                    # INFO: creates list of field values from form content passed to the function endpoint.
                    for k, v in request.httprequest.form.items():
                        # INFO: evals them because they can be '"string"' or 'num' or 'float' etc.
                        kwargs.pop(k)
                        fvals[k] = eval(v)
                    vals = {}
                    for k, v in kwargs.items():
                        # INFO: evals them because they can be '"string"' or 'num' or 'float' etc.
                        if not k.startswith('__'):
                            # INFO: catches exceptions that can stop the flow here (for example if you pass auth_token
                            #       as an url parameter because you cannot eval that).
                            try:
                                vals[k] = eval(v)
                            except:
                                pass
                    rec, recs, content = func(user, rec, vals, fvals)
                    #  INFO: id below is needed to return a compact json if not False.
                    id = rec and rec.id
                    # INFO: filling up recs because it is the variable getting output.
                    recs = recs or rec
                    mod = recs or None

                # INFO: parses 'filter=field[op]value' taking care of quoted values (only double quotations are allowed)
                #       + handles lists too (between parenthesis e.g.: "(1,2)").
                ff = re.findall("(?:\".*?\"|\(.*?\)|[^(\[.*?\])\s])+", filter)
                if len(ff) % 3:
                    return make_response(400, 101, "Filter syntax error")
                i = 0
                ff_list = []
                # INFO: loops thru filters.
                while i < len(ff):
                    ff_field = ff[i]
                    ff_op = ff[i+1]
                    ff_value = ff[i+2]

                    # INFO: checks if it is a list of values (e.g.: "(1,2)").
                    if len(ff_value) > 0 and ff_value[0] == '(':
                        ff_value = re.findall("(?:\".*?\"|[^(.*?,)\s])+", ff_value)
                        # INFO: converts if element of list are integers.
                        ff_value = [int(x) if x.isdigit() else x for x in ff_value]
                    elif ff_value.isdigit():
                        # INFO: in case of numeric value then convert it (e.g.: id).
                        ff_value = int(ff_value)
                    elif ff_value.lower() in ('true', 'false'):
                        ff_value = ff_value.lower() == 'true'
                    else:
                        ff_value = ff_value.strip('"')

                    if ff_op in ('ilike', 'like'):
                        ff_value = '%' + ff_value + '%'
                    elif ff_op not in ('=', '!=', 'in', 'not in'):
                        return make_response(400, 102, "Unknown filter operator: <%s>" % ff_op)

                    if ff_field[0] in ('|', '&'):
                        ff_list += [ff_field[0]]
                        ff_field = ff_field[1:]
                    ff_list += [(ff_field, ff_op, ff_value)]
                    i += 3

                try:
                    # TODO: remove redundancy when recs has been already set by an endpoint func and filter is empty.
                    if recs and len(recs) > 0:
                        if ff_list:
                            recs = mod.filtered_domain(ff_list)
                    else:
                        recs = mod is not None and mod.search(id and [('id', '=', id)] or ff_list)
                except Exception as E:
                    return make_response(400, 103, "Search exception: %s" % str(E))

                if recs:
                    res = []
                    if pages:
                        if '-' in pages:
                            pages = pages.split('-')
                            page_from = int(pages[0])
                            page_to = int((len(pages) > 1) and pages[1] or 0) or False
                        else:
                            page_from = int(pages)
                            page_to = page_from
                        items_per_page = int(items_per_page)
                        i = items_per_page * (page_from - 1)
                        n_page = page_from
                        old_n_page = n_page
                        n_items = 0
                        res_items = []
                        while i < len(recs) and (page_to and (n_page < page_to+1) or not page_to):
                            n_items += 1
                            # res += [{
                            #     'page': n_page,
                            #     'items': self._explode(False, False, recs[i], explode.split(','), include.split(','))
                            # }]
                            res_items += [self._explode(False, False, recs[i], explode.split(','), include.split(','))]
                            i += 1
                            n_page = int(i / items_per_page) + 1
                            if old_n_page != n_page or (i == len(recs) or page_to and (n_page == page_to+1)):
                                res += [{
                                    'page': old_n_page,
                                    'items': res_items
                                }]
                                old_n_page = n_page
                                res_items = []

                        # INFO: if paging then a proper response is packed.
                        return make_response(200, 0, {
                            'n_items': n_items,
                            'n_pages': len(res),  # int((i - 1) / items_per_page) + 1,
                            'pages': res
                        })
                    else:
                        for rec in recs:
                            res += [self._explode(False, False, rec, explode.split(','), include.split(','))]

                        # INFO: if id is not false then it is just one rec and return a compact response.
                        if id:
                            return make_response(200, 0, res[0])
                        else:
                            return make_response(200, 0, {
                                'n_items': len(res),
                                'items': res
                            })

                if content:
                    return make_response(200, 0, content)

                return make_response(200, 0, {} if id else {'n_items': 0, 'items': []})
                # return make_response(404, 1, "Record/s not found")

            except Exception as E:
                return make_response(400, 104, "Exception while %s: %s" % (request.httprequest.method, str(E)))

        return make_response(404, 11, "Unknown model <%s>" % model)

    @verify_user_auth_token
    @company_from_request
    @http.route([
        '/sydrestapi/v1/<string:model>',
        '/sydrestapi/v1/<string:model>/<int:id>',
        '/sydrestapi/v1/<string:model>/<string:func>',
        '/sydrestapi/v1/<string:model>/<string:func>/<int:id>'
    ], type='http', auth='public', methods=['POST', 'PUT', 'DELETE'], csrf=False, save_session=False)
    def post_(self, model, func='', id=False, explode='', include='', **kwargs):
        _logger.info('Request %s.Headers=%s', request.httprequest.method, request.httprequest.headers)
        _logger.info('Operation <%s>.', request.httprequest.method)

        _put = request.httprequest.method.upper() == 'PUT'
        _delete = request.httprequest.method.upper() == 'DELETE'
        _post = not _put and not _delete

        mod = request.env.get(model)
        if isinstance(mod, models.BaseModel):
            try:
                user = kwargs['__user']
                company = kwargs['__company']
                _logger.info('Comapny ID <%s>.', company.id)
                _logger.info('User ID from token <%s>.', user.id)

                # INFO: raises rights to do any kind of operations during this REST call.
                mod = mod.with_user(user).with_company(company).sudo()

                # INFO: checks if a function of the model has been queried.
                func = func and getattr(mod, func)
                if func:
                    rec = False
                    if id:
                        rec = mod.browse(id)
                        rec = rec.exists() and rec
                    fvals = {}
                    # INFO: creates list of field values from form content passed to the function endpoint.
                    for k, v in request.httprequest.form.items():
                        # INFO: evals them because they can be '"string"' or 'num' or 'float' etc.
                        try:
                            kwargs.pop(k)
                            fvals[k] = eval(v)
                        except:
                            return make_response(400, 8, "Error parsing param <%s>" % k)
                        vals = {}
                    for k, v in kwargs.items():
                        # INFO: evals them because they can be '"string"' or 'num' or 'float' etc.
                        if not k.startswith('__'):
                            # INFO: catches exceptions that can stop the flow here (for example if you pass auth_token
                            #       as an url parameter because you cannot eval that).
                            try:
                                vals[k] = eval(v)
                            except:
                                pass
                    rec = func(user, rec, vals, fvals)
                    # INFO: checks returned value: if of type Response, something wrong just happened, return it.
                    if isinstance(rec, Response):
                        return rec
                else:
                    # INFO: rec is for PUT or DELETE operations.
                    rec = False
                    if _put or _delete:
                        if not id:
                            return make_response(400, 4, "You need to specify an ID")
                        rec = mod.browse(id).exists()
                        if not rec:
                            return make_response(404, 7, "Record not found")
                        if _delete:
                            rec.unlink()
                            return make_response(200, 0, {'id': id})

                    fs = getattr(mod, '_RIP_POST_FIELDS', [])
                    if fs:
                        _logger.info('Checking _RIP_POST_FIELDS -> %s.', fs)
                        res_dict = {}
                        for f in fs:
                            _logger.info('_RIP_POST_FIELDS[%s]', f)
                            f_is_dict = False
                            if callable(f):
                                res_dict.update(f(mod, user, kwargs))
                            else:
                                if type(f) == tuple:
                                    f_dest = f[0]
                                    f = len(f) > 1 and f[1] or f[0]
                                else:
                                    f_dest = f

                                required = False
                                if f[0] == '*':
                                    required = True
                                    f = f[1:]
                                    f_dest = f_dest[0] == '*' and f_dest[1:] or f_dest

                                if f[0] == '{':
                                    f = f.strip('{}')
                                    f_dest = f
                                    f_is_dict = True

                                f_val = kwargs.get(f)

                                if f_val is None and required:
                                    return make_response(403, 1, "Missing required field <%s>" % f)
                                if f_val is not None:
                                    if mod._fields[f_dest].type in ['many2one', 'integer']:
                                        res_dict[f_dest] = int(f_val)
                                    else:
                                        if f_is_dict:
                                            try:
                                                json.loads(f_val)
                                            except json.decoder.JSONDecodeError:
                                                return make_response(400, 201, "JSON field <%s> wrong format" % f)
                                        res_dict[f_dest] = f_val

                        if res_dict:
                            _logger.info('res_dict has been filled -> %s.', res_dict)
                            if _put:
                                rec.update(res_dict)
                            else:
                                # INFO: if POST and id is set then it is a TransientModel function endpoint.
                                if id:
                                    if isinstance(mod, models.TransientModel):
                                        res_dict['id'] = id
                                    else:
                                        # INFO: if it is not a function endpoint then returns error.
                                        return make_response(400, 3, "You can set an id in POST only when calling a function endpoint")
                                rec = mod.create(res_dict)
                        else:
                            return make_response(400, 2, "No data to %s" % request.httprequest.method)
                    else:
                        return make_response(400, 1, "No _RIP_POST_FIELDS set for model <%s>")

                if rec:
                    rec.flush()
                    # INFO: response with default _RIP_GET_FIELDS of the record just created/updated.
                    return make_response(200, 0, self._explode(False, False, rec, explode.split(','), include.split(',')))

                return make_response(200, 0, {})

            except Exception as E:
                return make_response(400, 104, "Exception while %s: %s" % (request.httprequest.method, str(E)))

        return make_response(404, 11, "Unknown model <%s>" % model)

    # INFO: redirects to arg 'url'.
    # TODO: re-enable this option asap (doing that because IONIC for iOS do not pass auth_token header during redirect).
    @enable_cors_preflight
    @verify_user_auth_token
    @http.route('/sydrestapi/v1/redirect', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, save_session=False)
    def redirect_(self, url, **args):
        _logger.info('Request %s.redirect.Headers=%s', request.httprequest.method, request.httprequest.headers)
        result = redirect(url)
        return result


class RIPBinary(Binary):

    # INFO: here we need to inject ACAO when OPTIONS (probably odoo.sh do not interfere here).
    @enable_cors_preflight
    @http.route()
    def content_common(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                       filename=None, filename_field='name', unique=None, mimetype=None,
                       download=None, data=None, token=None, access_token=None, **kw):

        result = super(RIPBinary, self).content_common(xmlid, model, id, field,
                      filename, filename_field, unique, mimetype,
                      download, data, token, access_token, **kw)

        # _logger.info('Request %s.content_common.Headers=%s', request.httprequest.method, request.httprequest.headers)
        # INFO: Avoiding session creation when back with response.
        request.endpoint.routing['save_session'] = False
        return result

    # INFO: here we need to not inject ACAO when OPTIONS (odoo.sh does interfere here).
    @enable_cors_preflight_no_acao
    @http.route()
    def content_image(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                      filename_field='name', unique=None, filename=None, mimetype=None,
                      download=None, width=0, height=0, crop=False, access_token=None,
                      **kwargs):

        result = super(RIPBinary, self).content_image(xmlid, model, id, field,
                      filename_field, unique, filename, mimetype,
                      download, width, height, crop, access_token,
                      **kwargs)

        # _logger.info('Request %s.content_image.Headers=%s', request.httprequest.method, request.httprequest.headers)
        # INFO: Avoiding session creation when back with response.
        request.endpoint.routing['save_session'] = False
        return result
