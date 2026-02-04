# -*- coding: utf-8 -*-
# from odoo import http


# class ContractKkonSvcmgmt(http.Controller):
#     @http.route('/contract_kkon_svcmgmt/contract_kkon_svcmgmt', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/contract_kkon_svcmgmt/contract_kkon_svcmgmt/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('contract_kkon_svcmgmt.listing', {
#             'root': '/contract_kkon_svcmgmt/contract_kkon_svcmgmt',
#             'objects': http.request.env['contract_kkon_svcmgmt.contract_kkon_svcmgmt'].search([]),
#         })

#     @http.route('/contract_kkon_svcmgmt/contract_kkon_svcmgmt/objects/<model("contract_kkon_svcmgmt.contract_kkon_svcmgmt"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('contract_kkon_svcmgmt.object', {
#             'object': obj
#         })
