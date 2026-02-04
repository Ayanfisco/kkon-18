from odoo import models, fields

class PurchaseRequisitions(models.Model):
    _inherit = "purchase.requisition"

    material_requisition_id = fields.Many2one('material.requisition')
    purchase_request_id = fields.Many2one('az.purchase.request')