from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseRequest(models.Model):
    _name = "az.purchase.request"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Purchase Request (PR)"
    
    name = fields.Char(readonly=True, default='/', copy=False)
    material_requisition_id = fields.Many2one('material.requisition', readonly=True)
    project_id = fields.Many2one(related='material_requisition_id.project_id')
    destination_location_id = fields.Many2one(related='material_requisition_id.destination_location_id')
    mr_state = fields.Selection(related='material_requisition_id.state', string="MR Status")
    line_ids = fields.One2many('az.purchase.request.line', 'request_id', readonly=True)
    company_id = fields.Many2one(related='material_requisition_id.company_id', store=True)
    state = fields.Selection([('to_approve', 'To Approve'),
                              ('approved', 'Approved'),
                              ('in_progress', 'In Progress'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')], default='to_approve', string="Status", tracking=True)
    purchase_order_ids = fields.One2many("purchase.order", "purchase_request_id")
    purchase_agreement_ids = fields.One2many("purchase.requisition", "purchase_request_id")
    purchase_order_count = fields.Integer(compute='_compute_purchase_order_count')
    purchase_agreement_count = fields.Integer(compute='_compute_purchase_agreement_count')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals or vals['name'] == _('/'):
                vals['name'] = self.env['ir.sequence'].next_by_code('az.purchase.request.code') or _('New')
        return super().create(vals_list)

    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = len(record.purchase_order_ids)

    def _compute_purchase_agreement_count(self):
        for record in self:
            record.purchase_agreement_count = len(record.purchase_agreement_ids)

    def validate_material_lines(self):
        if len(self.mapped('company_id')) > 1:
            raise UserError(_('Material Lines must belong to the same Company in order to be transfered/purchased.'))
        if len(self.mapped('material_requisition_id')) > 1:
            raise UserError(_('Material Lines must belong to the same Material Requisition in order to be transfered/purchased.'))
        if any([mr.state != 'in_progress' for mr in self.mapped('material_requisition_id')]):
            raise UserError(_("Material Requistion must be 'In Progress' State in Order to Purchase its Items."))
        if any([pr.state != 'in_progress' for pr in self]):
            raise UserError(_("Purchase Request must be 'In Progress' State in Order to Purchase its Items."))


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
                'default_line_ids': self.line_ids.mapped("mr_line_id").ids,
                'default_order_type': 'purchase_order',
                'default_purchase_request_id': self.id
                }
        }

    def create_purchase_agreement(self):
        self.validate_material_lines()
        
        return {
            'name': _('Create Purchase Agreement'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.purchase.order.for.material.lines',
            'target': 'new',
            'context': {
                'default_company_id': self.mapped('company_id').id,
                'default_line_ids': self.line_ids.mapped("mr_line_id").ids,
                'default_order_type': 'purchase_agreement',
                'default_purchase_request_id': self.id
                }
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
            'domain': [('id', 'in', self.purchase_order_ids.ids)]
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
            'domain': [('id', 'in', self.purchase_agreement_ids.ids)]
        }

class PurchaseRequestLine(models.Model):
    _name = "az.purchase.request.line"
    _description = "Purchase Request (PR)"
    
    request_id = fields.Many2one('az.purchase.request', string="Purchase Request")
    product_id = fields.Many2one('product.product')
    quantity = fields.Float()
    uom_id = fields.Many2one('uom.uom', 'UoM')
    mr_line_id = fields.Many2one('material.requisition.line', 'MR Line')
    description = fields.Char(related='mr_line_id.description')
    company_id = fields.Many2one(related='request_id.company_id', store=True)
