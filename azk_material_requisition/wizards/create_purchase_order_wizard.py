from odoo import models, fields, _
from odoo.exceptions import UserError

class CreatePurchaseOrder(models.TransientModel):
    _name = 'create.purchase.order.for.material.lines'
    _description = 'Make Purchase Order for MR Lines'

    company_id = fields.Many2one('res.company')
    picking_type_id = fields.Many2one('stock.picking.type', required=True, string="Operation Type")
    line_ids = fields.Many2many('material.requisition.line', 'create_purchase_for_material_lines_rel')
    partner_ids = fields.Many2many('res.partner', string="Vendor(s)")
    order_type = fields.Selection([('purchase_order', 'Purchase Order'),
                                   ('purchase_agreement', 'Purchase Agreement')], required=True)
    purchase_agreement_type_id = fields.Many2one('purchase.requisition.type')
    purchase_request_id = fields.Many2one('az.purchase.request')

    def make_purchase_order(self):
        purchase_order_obj = self.env['purchase.order']
        purchase_order_line_obj = self.env['purchase.order.line']
        
        if not self.partner_ids:
            raise UserError(_("Please Select a Vendor."))
        if not self.line_ids:
            raise UserError(_("No Materials selected."))
        if not self.order_type == 'purchase_order':
            raise UserError(_("Order Type must be 'Purchase Order'."))
        
        purchase_ids = []
        for partner in self.partner_ids:
            order_id = purchase_order_obj.create({'company_id': self.company_id.id,
                                                  'partner_id': partner.id,
                                                  'picking_type_id': self.picking_type_id.id,
                                                  'material_requisition_id': self.line_ids[0].requisition_id.id})
            purchase_ids.append(order_id.id)
            for line in self.line_ids.filtered(lambda l: l.remaining_qty > 0):
                purchase_order_line_obj.create({'order_id': order_id.id,
                                                'product_id': line.product_template_id.product_variant_id.id,
                                                'name': line.description or line.product_template_id.display_name,
                                                'product_qty': line.remaining_qty,
                                                'product_uom': line.product_uom_id.id,
                                                })
                line.purchase_order_ids = [(4, order_id.id)]
                if self.purchase_request_id:
                    self.purchase_request_id.purchase_order_ids = [(4, order_id.id)]
                # log message on the chatter of the material lines to note that a transfer has been created
                message = _("A Purchase Order '%s' has been created for the Material '%s' with Quantity (%s %s) and linked to the Material Requisition '%s'") \
                        % (order_id.name, line.product_template_id.display_name, line.remaining_qty, line.product_uom_id.display_name, line.requisition_id.name)
                line.message_post(body=message, message_type='comment', subtype_xmlid='mail.mt_comment')
                
        return {
            'name': _('Purchase Order(s)'),
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list, form',
            'views': [[False, 'list'], [False, 'form']],
            'res_model': 'purchase.order',
            'target': 'current',
            'domain': [('id', 'in', purchase_ids)]
        }

    def make_purchase_agreement(self):
        if not self.line_ids:
            raise UserError(_("No Materials selected."))
        if not self.order_type == 'purchase_agreement':
            raise UserError(_("Order Type must be 'Purchase Agreement'."))
        if not self.purchase_agreement_type_id:
            raise UserError(_("Please Select Purchase Agreement Type."))
        
        purchase_agreement_obj = self.env['purchase.requisition']
        purchase_agreement_line_obj = self.env['purchase.requisition.line']
        requisition_id = purchase_agreement_obj.sudo().create({'company_id': self.company_id.id,
                                                                'type_id': self.purchase_agreement_type_id.id,
                                                                'picking_type_id': self.picking_type_id.id,
                                                                'material_requisition_id': self.line_ids[0].requisition_id.id})
        for line in self.line_ids.filtered(lambda l: l.remaining_qty > 0):
            purchase_agreement_line_obj.create({'requisition_id': requisition_id.id,
                                                'product_id': line.product_template_id.product_variant_id.id,
                                                'product_description_variants': line.description or line.product_template_id.display_name,
                                                'product_qty': line.remaining_qty,
                                                'product_uom_id': line.product_uom_id.id,
                                                })
            line.purchase_agreement_ids = [(4, requisition_id.id)]
            if self.purchase_request_id:
                self.purchase_request_id.purchase_agreement_ids = [(4, requisition_id.id)]
            # log message on the chatter of the material lines to note that a transfer has been created
            message = _("A Purchase Requisition has been created for the Material '%s' with Quantity (%s %s) and linked to the Material Requisition '%s'") \
                    % (line.product_template_id.display_name, line.remaining_qty, line.product_uom_id.display_name, line.requisition_id.name)
            line.message_post(body=message, message_type='comment', subtype_xmlid='mail.mt_comment')
        
        return {
            'name': _('Purchase Agreement'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.requisition',
            'res_id': requisition_id.id,
            'target': 'current',
        }