# -*- coding: utf-8 -*-

from odoo.http import request, Response

#
#
# from werkzeug.routing import Map, Rule, RequestRedirect
# from werkzeug.exceptions import NotFound, HTTPException
#
#
# url_map = Map([
#     Rule('/sydrestapi', endpoint='blog/index'),
# ])
#
#
# def application(environ, start_response):
#     urls = url_map.bind_to_environ(environ)
#     try:
#         endpoint, args = urls.match()
#     except HTTPException as e:
#         return e(environ, start_response)
#     start_response('200 OK', [('Content-Type', 'text/plain')])
#     return ['Rule points to %r with arguments %r' % (endpoint, args)]

# application(http.root.environ)
