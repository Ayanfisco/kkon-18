from odoo import models, _

class AccoutMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()
        for move in self.filtered(lambda m: m.move_type == 'in_invoice'):
            purchase_id = self.env['purchase.order'].search([('name', '=', move.invoice_origin)], limit=1)
            if purchase_id and purchase_id.material_requisition_id or (purchase_id.requisition_id and purchase_id.requisition_id.material_requisition_id):
                material_requisition_id = purchase_id.material_requisition_id or purchase_id.requisition_id.material_requisition_id
                mr_lines = material_requisition_id.line_ids.filtered(lambda l: (purchase_id.id in l.purchase_order_ids.ids or purchase_id.requisition_id.id in l.purchase_agreement_ids.ids) and l.product_id in move.invoice_line_ids.mapped('product_id'))
                for line in mr_lines:
                    message = _("A Vendor Bill %s for the Purchase Order '%s' linked to the Material Requisition '%s' has been Validated.") \
                        % (move.name, purchase_id.name, line.requisition_id.name)
                    line.message_post(body=message, message_type='comment', subtype_xmlid='mail.mt_comment')
        
        return res