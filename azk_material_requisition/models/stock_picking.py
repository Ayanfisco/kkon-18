from odoo import models, fields, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    material_requisition_id = fields.Many2one('material.requisition')

    def _action_done(self):
        """ Log in the chatter of Material Requisition lines upon validating an internal transfer linked to an MR or on a Receipt Transfer for a PO linked to MR """
        result = super()._action_done()
        for picking in self:
            if picking.material_requisition_id:
                mr_lines = picking.material_requisition_id.line_ids.filtered(lambda l: picking.id in l.picking_ids.ids and l.product_id in picking.move_line_ids.mapped('product_id'))
                for line in mr_lines:
                    message = _("The Transfer '%s' linked to the Material Requisition '%s' has been validated.") \
                        % (picking.name, line.requisition_id.name)
                    line.message_post(body=message, message_type='comment', subtype_xmlid='mail.mt_comment')
            
            if picking.purchase_id and (picking.purchase_id.material_requisition_id or (picking.purchase_id.requisition_id and picking.purchase_id.requisition_id.material_requisition_id)):
                material_requisition_id = picking.purchase_id.material_requisition_id or picking.purchase_id.requisition_id.material_requisition_id
                mr_lines = material_requisition_id.line_ids.filtered(lambda l: (picking.purchase_id in l.purchase_order_ids or picking.purchase_id.requisition_id in l.purchase_agreement_ids) and l.product_id in picking.move_line_ids.mapped('product_id'))
                for line in mr_lines:
                    message = _("The Receipt Transfer %s of the Purchase Order '%s' linked to the Material Requisition '%s' has been received.") \
                        % (picking.name, picking.purchase_id.name, line.requisition_id.name)
                    line.message_post(body=message, message_type='comment', subtype_xmlid='mail.mt_comment')
        
        return result