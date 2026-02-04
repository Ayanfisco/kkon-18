from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MaterialRequisitionLine(models.Model):
    _name = 'material.requisition.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Material Requisition Line (MRL)'
    _rec_name = 'product_template_id'
    
    requisition_id = fields.Many2one('material.requisition')
    product_template_id = fields.Many2one('product.template', 'Product')
    product_id = fields.Many2one('product.product', related='product_template_id.product_variant_id')
    product_categ_id = fields.Many2one(related='product_template_id.categ_id', string='Product Category', store=True)
    description = fields.Char(tracking=True)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', tracking=True)
    product_uom_category_id = fields.Many2one(related='product_template_id.uom_id.category_id', string="Product UoM Category")
    requested_qty = fields.Float(string='Requested Quantity', help="Initially Reqiested Quantity", tracking=True)
    scheduled_qty = fields.Float(compute='_compute_scheduled_qty', store=True,
                                 help="Quantity reserved to be transfered to the project location (Not done yet).", tracking=True)
    received_qty = fields.Float(compute='_compute_received_qty', store=True,
                                help="Quantity actually transfered to the Project Location.", tracking=True)
    remaining_qty = fields.Float(compute='_compute_remaining_qty', store=True,
                                 help="Remaining Quantity to be Fulfilled = Requested Qty - Scheduled Qty - Received Qty", tracking=True)
    stock_qty = fields.Float('Stock Availability', compute='_compute_stock_qty', search='_search_qty_in_stock',
                                help="Quantity currently Available in the stock locations of the MR (excluding reserved quantites).")
    purchase_order_ids = fields.Many2many('purchase.order', string="Purchase Orders", help="Purchase Order issued (from the MR) for purchasing this product")
    purchase_agreement_ids = fields.Many2many('purchase.requisition', string="Purchase Requisitions", help="Puchase Agreements created for this product.")
    picking_ids = fields.Many2many('stock.picking', string="Transfers", help="Transfers for this product.")
    purchase_request_ids = fields.Many2many('az.purchase.request', string="Purchase Requests", help="Purchase Requests Created for this Material.")
    location_ids = fields.Many2many(related='requisition_id.location_ids')
    location_id = fields.Many2one('stock.location') # this is added only to be used in MR line search view, to have the ability to search by location
    company_id = fields.Many2one(related='requisition_id.company_id', store=True)
    fulfilled = fields.Boolean(compute='_compute_fulfilled', store=True)
    fully_received = fields.Boolean(compute='_compute_fulfilled', store=True)
    transfer_count = fields.Integer(compute='_compute_transfer_count')
    purchase_order_count = fields.Integer(compute='_compute_purchase_order_count')
    purchase_agreement_count = fields.Integer(compute='_compute_purchase_agreement_count')
    bills_count = fields.Integer(compute='_compute_bills_count')
    purchase_request_count = fields.Integer(compute='_compute_purchase_request_count')

    @api.model_create_multi
    def create(self, vals_list):
        results = super().create(vals_list)
        for rec in results:
            if rec.product_template_id and not rec.product_uom_id:
                rec.product_uom_id = rec.product_template_id.uom_id
        return results

    @api.depends('picking_ids',
                 'picking_ids.state',
                 'picking_ids.move_ids')
    def _compute_scheduled_qty(self):
        for record in self:
            reserved_qty = 0
            stock_move_ids = self.env['stock.move'].search([('picking_id.material_requisition_id', '=', record.requisition_id.id),
                                                            ('product_tmpl_id', '=', record.product_template_id.id),
                                                            ('state', 'not in', ('done', 'cancel'))])
            for move in stock_move_ids:
                reserved_qty += move.product_uom._compute_quantity(move.reserved_availability or move.product_uom_qty, record.product_uom_id)
            
            record.scheduled_qty = reserved_qty

    @api.depends('picking_ids',
                 'picking_ids.state',
                 'picking_ids.move_ids')
    def _compute_received_qty(self):
        for record in self:
            done_qty = 0
            stock_move_ids = self.env['stock.move'].search([('picking_id.material_requisition_id', '=', record.requisition_id.id),
                                                            ('product_tmpl_id', '=', record.product_template_id.id),
                                                            ('state', '=', 'done')])
            for move in stock_move_ids:
                done_qty += move.product_uom._compute_quantity(move.quantity_done, record.product_uom_id)
            
            record.received_qty = done_qty

    def _compute_stock_qty(self):
        for record in self:
            available_qty = 0
            location_ids = []
            if self._context.get('mrl_location') and isinstance(self._context['mrl_location'], list):
                for location in self._context['mrl_location']:
                    if isinstance(location, int):
                        location_ids.append(location)
            
            location_ids = location_ids or record.location_ids.ids
            stock_quants = self.env['stock.quant'].search([('product_tmpl_id', '=', record.product_template_id.id),
                                                           ('company_id', '=', record.company_id.id),
                                                           ('location_id', 'in', location_ids)])
            for quant in stock_quants:
                available_qty += quant.product_uom_id._compute_quantity(quant.available_quantity, record.product_uom_id)
            
            record.stock_qty = available_qty

    @api.depends('requested_qty', 'scheduled_qty', 'received_qty')
    def _compute_remaining_qty(self):
        for record in self:
            remaining_qty = record.requested_qty - record.received_qty - record.scheduled_qty
            record.remaining_qty = (remaining_qty > 0 and remaining_qty) or 0

    @api.depends('requested_qty', 'received_qty', 'remaining_qty')
    def _compute_fulfilled(self):
        for record in self:
            record.fulfilled = False
            record.fully_received = False
            if record.received_qty < record.requested_qty and record.remaining_qty == 0:
                record.fulfilled = True
            if record.received_qty >= record.requested_qty:
                record.fully_received = True
                record.fulfilled = False

    def _compute_transfer_count(self):
        for record in self:
            record.transfer_count = len(record.picking_ids)

    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = len(record.purchase_order_ids)

    def _compute_purchase_agreement_count(self):
        for record in self:
            record.purchase_agreement_count = len(record.purchase_agreement_ids)

    def _compute_bills_count(self):
        for record in self:
            vendor_bills = self.env['account.move'].search(record._get_vendor_bills_domain())
            record.bills_count = len(vendor_bills)

    def _compute_purchase_request_count(self):
        for record in self:
            record.purchase_request_count = len(record.purchase_request_ids)

    @api.onchange("product_template_id")
    def _onchange_product_id(self):
        if self.product_template_id and not self.product_uom_id:
            self.product_uom_id = self.product_template_id.uom_id

    def _search_qty_in_stock(self, operator, value):
        domain = []
        active_id = self._context.get('active_id') if self._context.get('active_model', '') == 'material.requisition' else None
        if active_id:
            domain = [('requisition_id', '=', active_id)]
        material_lines = self.env['material.requisition.line'].search(domain)
        line_ids = []
        for line in material_lines:
            if self._context.get('available_in_stock'):
                if line.stock_qty > 0:
                    line_ids.append(line.id)
            if self._context.get('not_available_in_stock'):
                if not line.stock_qty:
                    line_ids.append(line.id)
        return [('id', 'in', line_ids)]


    def validate_material_lines(self):
        if len(self.mapped('company_id')) > 1:
            raise UserError(_('Material Lines must belong to the same Company in order to be transfered/purchased.'))
        if len(self.mapped('requisition_id')) > 1:
            raise UserError(_('Material Lines must belong to the same Material Requisition in order to be transfered/purchased.'))
        if any([mr.state != 'in_progress' for mr in self.mapped('requisition_id')]):
            raise UserError(_("Material Requistions must be 'In Progress' State in Order to Transfer or Purchase its Items."))


    def create_transfer(self):
        self.validate_material_lines()
        wizard_id = self.env['create.transfer.for.material.lines'].create({'line_ids': self.ids,
                                                                           'company_id': self.mapped('company_id').id,
                                                                           'destination_location_id': self.mapped('requisition_id').destination_location_id.id,
                                                                           })
        wizard_id.generate_move_lines()
        return {
            'name': _('Create Transfer'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'create.transfer.for.material.lines',
            'res_id': wizard_id.id,
            'target': 'new',
        }

    def create_purchase_order(self):
        self.validate_material_lines()
        
        return {
            'name': _('Create Purchase Order'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.purchase.order.for.material.lines',
            'target': 'new',
            'context': {
                'default_company_id': self.mapped('company_id').id,
                'default_line_ids': self.ids,
                'default_order_type': 'purchase_order'
                }
        }

    def create_purchase_agreement(self):
        self.validate_material_lines()
        
        return {
            'name': _('Create Tender'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.purchase.order.for.material.lines',
            'target': 'new',
            'context': {
                'default_company_id': self.mapped('company_id').id,
                'default_line_ids': self.ids,
                'default_order_type': 'purchase_agreement'
                }
        }

    def create_purchase_request(self):
        pr_line_obj = self.env['az.purchase.request.line']
        if not self:
            raise UserError(_("No Material Lines selected."))
        if all([not line.remaining_qty for line in self]):
            raise UserError(_("No Remaining Quantities for all of the selected MR Lines."))
        
        pr_id = self.env['az.purchase.request'].create({'material_requisition_id': self[0].requisition_id.id})
        for line in self:
            pr_line_obj.create({'request_id': pr_id.id,
                                'product_id': line.product_id.id,
                                'uom_id': line.product_uom_id.id,
                                'quantity': line.remaining_qty,
                                'mr_line_id': line.id
                                })
            line.purchase_request_ids = [(4, pr_id.id)]
        
        return {
            'name': _('Purchase Request'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'az.purchase.request',
            'res_id': pr_id.id,
            'target': 'current'
        }

    def action_view_transfers(self):
        return {
            'name': _('Transfers'),
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list, form',
            'views': [[False, 'list'], [False, 'form']],
            'res_model': 'stock.picking',
            'target': 'current',
            'domain': [('id', 'in', self.picking_ids.ids)],
            'context': {'create': False}
        }

    def action_view_purchase_orders(self):
        return {
            'name': _('Purchase Requests'),
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list, form',
            'views': [[False, 'list'], [False, 'form']],
            'res_model': 'purchase.order',
            'target': 'current',
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
            'context': {'create': False}
        }

    def action_view_purchase_agreements(self):
        return {
            'name': _('Purchase Requisitions'),
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list, form',
            'views': [[False, 'list'], [False, 'form']],
            'res_model': 'purchase.requisition',
            'target': 'current',
            'domain': [('id', 'in', self.purchase_agreement_ids.ids)],
            'context': {'create': False}
        }

    def action_view_vendor_bills(self):
        return {
            'name': _('Vendor Bills'),
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list, form',
            'views': [[False, 'list'], [False, 'form']],
            'res_model': 'account.move',
            'target': 'current',
            'domain': self._get_vendor_bills_domain(),
            'context': {'create': False}
        }

    def action_view_purchase_requests(self):
        return {
            'name': _('Purchase Requests'),
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list, form',
            'views': [[False, 'list'], [False, 'form']],
            'res_model': 'az.purchase.request',
            'target': 'current',
            'domain': [('id', 'in', self.purchase_request_ids.ids)],
            'context': {'create': False}
        }

    def _get_vendor_bills_domain(self):
        purchase_orders = self.purchase_order_ids
        purchase_agreement_orders = self.purchase_agreement_ids.purchase_ids
        
        domain = [('invoice_origin', 'in', (purchase_orders + purchase_agreement_orders).mapped('name'))]
        return domain