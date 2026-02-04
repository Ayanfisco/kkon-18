from odoo import models, fields, api, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    material_requisition_id = fields.Many2one('material.requisition')
    purchase_request_id = fields.Many2one('az.purchase.request')

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res.filtered(lambda p: p.requisition_id and p.requisition_id.material_requisition_id):
            mr_lines = record.requisition_id.material_requisition_id.line_ids.filtered(lambda l: record.requisition_id in l.purchase_agreement_ids and l.product_id in record.order_line.mapped('product_id'))
            for line in record.order_line:
                related_mr_lines = mr_lines.filtered(lambda l: l.product_id == line.product_id)
                for mr_line in related_mr_lines:
                    message = _("A Purchase Order '%s' has been created from the Purchase Requisition %s for the Material '%s' with Quantity (%s %s) and linked to the Material Requisition '%s'") \
                        % (record.name, record.requisition_id.name, line.product_id.display_name, line.product_qty, line.product_uom.display_name, record.requisition_id.material_requisition_id.name)
                    mr_line.message_post(body=message, message_type='comment', subtype_xmlid='mail.mt_comment')
        return res