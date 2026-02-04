from odoo import models, fields, api, _
import os
import csv
import base64
import logging
from odoo.tools.config import config
from odoo.exceptions import ValidationError

log = logging.getLogger(__name__)

class MaterialRequisition(models.Model):
    _name = "material.requisition"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Material Requisotion (MR)"
    
    name = fields.Char(readonly=True, default='/', copy=False)
    project_id = fields.Many2one('project.project', tracking=True)
    task_id = fields.Many2one('project.task', string='Project Task', tracking=True)
    analytic_account_id = fields.Many2one(related='project_id.account_id', store=True)
    destination_location_id = fields.Many2one('stock.location', tracking=True)
    location_ids = fields.Many2many('stock.location', string='Source Locations', tracking=True,
                                    help="Source Locations used as a source for the requested materials according to their availabilty.")
    can_edit_locations = fields.Boolean(compute='_compute_can_edit_locations')
    state = fields.Selection([('new', 'New'),
                              ('sent', 'Sent'),
                              ('approved', 'Approved'),
                              ('in_progress', 'In Progress'),
                              ('done', 'Done')], default='new', string="Status", tracking=True)
    line_ids = fields.One2many('material.requisition.line', 'requisition_id', string="Material Requisition Lines")
    lines_count = fields.Integer(compute='_compute_lines_count')
    transfer_count = fields.Integer(compute='_compute_transfer_count')
    purchase_order_count = fields.Integer(compute='_compute_purchase_order_count')
    purchase_agreement_count = fields.Integer(compute='_compute_purchase_agreement_count')
    bills_count = fields.Integer(compute='_compute_bills_count')
    purchase_request_count = fields.Integer(compute='_compute_purchase_request_count')
    company_id = fields.Many2one('res.company', required=True, default= lambda self: self.env.company)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals or vals['name'] == _('/'):
                vals['name'] = self.env['ir.sequence'].next_by_code('material.requisition.code') or _('New')
        return super().create(vals_list)

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def _compute_lines_count(self):
        for record in self:
            record.lines_count = len(record.line_ids)

    def _compute_transfer_count(self):
        for record in self:
            record.transfer_count = len(self.env['stock.picking'].search([('material_requisition_id', '=', record.id)]))

    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = len(self.env['purchase.order'].search([('material_requisition_id', '=', record.id)]))

    def _compute_purchase_agreement_count(self):
        for record in self:
            record.purchase_agreement_count = len(self.env['purchase.requisition'].search([('material_requisition_id', '=', record.id)]))

    def _compute_bills_count(self):
        for record in self:
            vendor_bills = self.env['account.move'].search(record._get_vendor_bills_domain())
            record.bills_count = len(vendor_bills)

    def _compute_purchase_request_count(self):
        for record in self:
            record.purchase_request_count = len(self.env['az.purchase.request'].search([('material_requisition_id', '=', record.id)]))

    def _compute_can_edit_locations(self):
        for record in self:
            record.can_edit_locations = True
            if not self.env.user.has_group('azk_material_requisition.group_material_requisition_officer'):
                record.can_edit_locations = False

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id and self.project_id.project_location_id:
            self.destination_location_id = self.project_id.project_location_id

    def action_view_material_lines(self):
        return {
            'name': _('Materials'),
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list, form',
            'views': [[False, 'list'], [self.env.ref('azk_material_requisition.material_requisition_line_form_view').id, 'form']],
            'res_model': 'material.requisition.line',
            'target': 'current',
            'domain': [('requisition_id', '=', self.id)],
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
            'domain': [('material_requisition_id', '=', self.id)],
            'context': {'default_material_requisition_id': self.id, 'create': False}
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
            'domain': [('material_requisition_id', '=', self.id)],
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
            'domain': [('material_requisition_id', '=', self.id)],
            'context': {'create': False}
        }

    def action_view_vendor_bills(self):
        return {
            'name': _('Vendor Bills'),
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'tree, form',
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
            'view_type': 'tree',
            'view_mode': 'tree, form',
            'views': [[False, 'list'], [False, 'form']],
            'res_model': 'az.purchase.request',
            'target': 'current',
            'domain': [('material_requisition_id', '=', self.id)],
            'context': {'create': False}
        }

    def _get_vendor_bills_domain(self):
        purchase_orders = self.line_ids.purchase_order_ids
        purchase_agreement_orders = self.line_ids.purchase_agreement_ids.purchase_ids
        
        domain = [('invoice_origin', 'in', (purchase_orders + purchase_agreement_orders).mapped('name'))]
        return domain


    def action_open_import_wizard(self):
        new_wizard = self.env['az.import.materila.csv'].create({
            'mr_id': self.ids,
        })
        return {
            'name': _('Import Materia Items'),
            'view_mode': 'form',
            'res_model': 'az.import.materila.csv',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': new_wizard.id,
        }
