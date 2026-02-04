# -*- coding: utf-8 -*-
# from odoo import http


# class PortalPaymentRedirect(http.Controller):
#     @http.route('/portal_payment_redirect/portal_payment_redirect', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/portal_payment_redirect/portal_payment_redirect/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('portal_payment_redirect.listing', {
#             'root': '/portal_payment_redirect/portal_payment_redirect',
#             'objects': http.request.env['portal_payment_redirect.portal_payment_redirect'].search([]),
#         })

#     @http.route('/portal_payment_redirect/portal_payment_redirect/objects/<model("portal_payment_redirect.portal_payment_redirect"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('portal_payment_redirect.object', {
#             'object': obj
#         })
