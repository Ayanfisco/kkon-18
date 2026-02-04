# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class portal_login_redirect(models.Model):
#     _name = 'portal_login_redirect.portal_login_redirect'
#     _description = 'portal_login_redirect.portal_login_redirect'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
