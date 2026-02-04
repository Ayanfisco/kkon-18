# -*- coding: utf-8 -*-
# from odoo import http


# class PortalLoginRedirect(http.Controller):
#     @http.route('/portal_login_redirect/portal_login_redirect', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/portal_login_redirect/portal_login_redirect/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('portal_login_redirect.listing', {
#             'root': '/portal_login_redirect/portal_login_redirect',
#             'objects': http.request.env['portal_login_redirect.portal_login_redirect'].search([]),
#         })

#     @http.route('/portal_login_redirect/portal_login_redirect/objects/<model("portal_login_redirect.portal_login_redirect"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('portal_login_redirect.object', {
#             'object': obj
#         })
