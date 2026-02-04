from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MaterialRequisitionExtends(models.Model):
    _inherit = 'material.requisition'

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1),
                                  tracking=True)
    employee_manager_id = fields.Many2one('hr.employee', string='Employee Manager', compute='_compute_employee_manager', store=True, tracking=True)

    state = fields.Selection([
        ('new', 'New'),
        ('sent', 'Sent'),
        ('employee_manager_approval', 'Employee Manager Approval'),
        ('inventory_manager_approval', 'Inventory Manager Approval'),
        ('in_progress', 'In Progress'),
        ('approved', 'Approved'),
        ('done', 'Done')
    ], default='new', string="Status", tracking=True)

    @api.depends('employee_id')
    def _compute_employee_manager(self):
        for rec in self:
            rec.employee_manager_id = rec.employee_id.parent_id if rec.employee_id else False

    def action_send(self):
        for rec in self:
            if not rec.employee_manager_id or not rec.employee_manager_id.user_id or not rec.employee_manager_id.user_id.partner_id:
                raise UserError(_('No employee manager or manager user/partner set.'))
            rec.state = 'employee_manager_approval'
            # Send notification (currently disabled)
            rec.notify('sent', [rec.employee_manager_id.user_id.id])

    @api.depends('line_ids', 'line_ids.picking_ids', 'line_ids.remaining_qty')
    def _compute_lines_count(self):
        for record in self:
            # Count lines that match the domain: no pickings OR has remaining quantity
            record.lines_count = len(record.line_ids.filtered(
                lambda line: not line.picking_ids or line.remaining_qty != 0
            ))

    def action_employee_manager_approve(self):
        # Only the designated employee manager can approve at this stage
        for rec in self:
            if not rec.employee_manager_id:
                raise UserError(_('No employee manager set.'))
            # Enforce that the approver is the exact employee manager assigned to the request
            if rec.employee_manager_id.user_id != self.env.user:
                raise UserError(_('Only the assigned Employee Manager can approve this request.'))
            rec.state = 'inventory_manager_approval'
            # Send notification (currently disabled)
            rec.notify('employee_manager_approved', [])

    def action_inventory_manager_approve(self):
        group = self.env.ref('azk_material_requisition_extends.azk_material_requisition_inventory_manager_group', raise_if_not_found=False)
        if not group or self.env.user not in group.users:
            raise UserError(_('You do not have permission to approve as Inventory Manager.'))
        for rec in self:
            if not rec.location_ids:
                raise UserError(_('Source location must be set before approval.'))
            rec.state = 'in_progress'

    def get_inventory_manager_partner_id(self):
        # Find all users in the inventory manager group and return their partner ids as comma-separated string
        group = self.env.ref('azk_material_requisition_extends.azk_material_requisition_inventory_manager_group', raise_if_not_found=False)
        if group:
            partner_ids = group.users.mapped('partner_id.id')
            return ','.join(str(pid) for pid in partner_ids if pid)
        return ''

    def action_reset_to_new(self):
        for rec in self:
            rec.state = 'new'

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_move_to_sent(self):
        for rec in self:
            rec.state = 'sent'

    def notify(self, notification_type, recipients=None):
        """
        Send mail notifications for different events in the material requisition process.
        Currently disabled - just pass.
        """
        # TODO: Enable email notifications here when needed
        pass

    def action_view_material_lines(self):
        return {
            'name': _('Materials'),
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list, form',
            'views': [[False, 'list'],
                    [self.env.ref('azk_material_requisition.material_requisition_line_form_view').id, 'form']],
            'res_model': 'material.requisition.line',
            'target': 'current',
            'domain': [
                ('requisition_id', '=', self.id),
                '|',  # OR operator
                    ('picking_ids', '=', False),  # No pickings
                    ('remaining_qty', '!=', 0)    # OR has remaining quantity
            ],
        }