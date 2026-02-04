from odoo import models, fields, _
from odoo.exceptions import UserError

class CreateTransfer(models.TransientModel):
    _name = 'create.transfer.for.material.lines'
    _description = 'Make Transfer for MR Lines'

    picking_type_id = fields.Many2one('stock.picking.type', string="Operation Type")
    company_id = fields.Many2one('res.company')
    destination_location_id = fields.Many2one('stock.location')
    line_ids = fields.Many2many('material.requisition.line', 'create_transfer_for_material_lines_rel')
    move_line_ids = fields.One2many('create.stock.move.for.material.line', 'wizard_id', 'create_moves_for_material_lines')

    def generate_move_lines(self):
        """ Create demo records for the stock moves that will be created for the transfer
            i.e. show every product with its quantity to be transfered and its source location 
            according to its availability
        """
        move_obj = self.env['create.stock.move.for.material.line']
        for line in self.line_ids:
            needed_qty = line.remaining_qty
            if not needed_qty:
                # skip if no more quantity needed for the selected Material
                continue
            # otherwise, check where we can find the remaining qty needed, what location?
            if not line.stock_qty:
                # skip if there is no quantity found in stock for the selected material
                continue 
            # location_ids are where we need to search in (Internal locations selected in the MR)
            location_ids = line.requisition_id.location_ids
            stock_quants = self.env['stock.quant'].search([('product_tmpl_id', '=', line.product_template_id.id),
                                                           ('company_id', '=', line.company_id.id),
                                                           ('location_id', 'in', location_ids.ids)])
            src_location_id = None
            src_locations_dict = {}
            remaining_qty = needed_qty
            for quant in stock_quants:
                if remaining_qty > 0:
                    available_qty = quant.product_uom_id._compute_quantity(quant.available_quantity, line.product_uom_id)
                    if not available_qty:
                        continue
                    
                    if available_qty >= needed_qty:
                        # if the needed_qty all found in one location then take this location
                        src_location_id = quant.location_id
                        break
                    
                    qty_to_transfer = min(remaining_qty, available_qty)
                    if qty_to_transfer > 0:
                        if not src_locations_dict.get(quant.location_id.id):
                            src_locations_dict[quant.location_id.id] = qty_to_transfer
                        else:
                            src_locations_dict[quant.location_id.id] += qty_to_transfer
                    
                    remaining_qty = remaining_qty - qty_to_transfer
                    if remaining_qty < 0: remaining_qty = 0
            
            if src_location_id:
                move_obj.create({'wizard_id': self.id,
                                 'product_tmpl_id': line.product_template_id.id,
                                 'quantity': needed_qty,
                                 'product_uom_id': line.product_uom_id.id,
                                 'description': line.description,
                                 'source_location_id': src_location_id.id,
                                 'material_requisition_line_id': line.id})
                continue
            
            for location_id, qty in src_locations_dict.items():
                move_obj.create({'wizard_id': self.id,
                                 'product_tmpl_id': line.product_template_id.id,
                                 'quantity': qty,
                                 'product_uom_id': line.product_uom_id.id,
                                 'description': line.description,
                                 'source_location_id': location_id,
                                 'material_requisition_line_id': line.id})

    def make_transfer(self):
        """ Create a single Internal Transfer for moving the materials selected from its available
            stock location to the destination of the project related to the MR
        """
        stock_picking_obj = self.env['stock.picking']
        stock_move_obj = self.env['stock.move']
        
        if not self.move_line_ids:
            raise UserError(_('No Materials to Transfer.'))
        if not self.picking_type_id:
            raise UserError(_('Please Select an Operation Type.'))
        if not self.destination_location_id:
            raise UserError(_('Please Select a Destination location for the Material Requisition.'))
        
        stock_picking_id = stock_picking_obj.create({'picking_type_id': self.picking_type_id.id,
                                                     'location_id': self.move_line_ids[0].source_location_id.id,
                                                     'location_dest_id': self.destination_location_id.id,
                                                     'company_id': self.company_id.id,
                                                     'material_requisition_id': self.line_ids[0].requisition_id.id
                                                    })
#         self.line_ids[0].requisition_id.write({'picking_ids': [(4, stock_picking_id.id)]})
        message = _("An Internal Transfer <b>%s</b> has been created to move the following material lines related to the MR %s: ") % (stock_picking_id.name, self.line_ids[0].requisition_id.name)
        for line in self.move_line_ids:
            stock_move_obj.create({'product_tmpl_id': line.product_tmpl_id.id,
                                   'product_id': line.product_tmpl_id.product_variant_id.id,
                                   'product_uom': line.product_uom_id.id,
                                   'product_uom_qty': line.quantity,
                                   'name': line.description or line.product_tmpl_id.display_name,
                                   'location_id': line.source_location_id.id,
                                   'location_dest_id': self.destination_location_id.id,
                                   'date': fields.Date.today(),
                                   'picking_id': stock_picking_id.id
                                   })
            line.material_requisition_line_id.picking_ids = [(4, stock_picking_id.id)]
            mr_message = message + "\n %s of Quantity %s %s From %s to %s" % \
                                (line.product_tmpl_id.display_name, line.quantity, line.product_uom_id.name, line.source_location_id.display_name, self.destination_location_id.display_name)
            line.material_requisition_line_id.message_post(body=mr_message, message_type='comment', subtype_xmlid='mail.mt_comment')
            
        
        stock_picking_id.action_confirm()
        return {
            'name': _('Transfer'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': stock_picking_id.id,
            'target': 'current',
        }


class CreateTransferLine(models.TransientModel):
    _name = 'create.stock.move.for.material.line'
    _description = 'Make Stock Move for MR Line'
    
    wizard_id = fields.Many2one('create.transfer.for.material.lines')
    product_tmpl_id = fields.Many2one('product.template', readonly=True, string="Product")
    quantity = fields.Float('Quantity to be Transfered', readonly=True)
    product_uom_id = fields.Many2one('uom.uom', string='UoM', readonly=True)
    description = fields.Char()
    source_location_id = fields.Many2one('stock.location', readonly=True)
    material_requisition_line_id = fields.Many2one('material.requisition.line')