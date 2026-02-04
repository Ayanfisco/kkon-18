from odoo import models, fields, api, _
from odoo.exceptions import UserError

STATES = [
    ("draft", "Draft"),
    ("submit", "Employee Manager"),
    ("approved", "Inventory Manager"),
    ("cpo", "CPO"),
    ("done", "Done"),
]

class FiberStoreRequest(models.Model):
    _inherit = 'ng.store.request'
    
    state = fields.Selection(selection=STATES, default="draft", tracking=True)
    
    def _current_login_user(self):
        """Return current logined in user."""
        return self.env.uid
        
    def _current_login_employee(self):
        """Get the employee record related to the current login user."""
        hr_employee = self.env["hr.employee"].search([("user_id", "=", self._current_login_user())], limit=1)
        return hr_employee.id
    
    # Override the requester field to trigger employee update
    requester = fields.Many2one(
        comodel_name="res.users",
        string="User",
        tracking=True,
        default=_current_login_user
    )
    
    # Override end_user to be computed from requester
    end_user = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        compute='_compute_employee_from_user',
        store=True,
        readonly=True,
        default=_current_login_employee,
    )
    
    # Change hod field to manager
    manager_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Manager",
        related="end_user.parent_id",
        store=True,
        readonly=True
    )

    # Add compute method for readonly status
    @api.depends('state')
    def _compute_readonly_status(self):
        for record in self:
            record.product_readonly = record.state in ['submit','approved', 'cpo', 'done']

    product_readonly = fields.Boolean(
        compute='_compute_readonly_status',
        store=False
    )
    
    @api.depends('requester')
    def _compute_employee_from_user(self):
        """Automatically set employee based on selected user."""
        for record in self:
            if record.requester:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', record.requester.id)],
                    limit=1
                )
                record.end_user = employee.id
            else:
                record.end_user = self._current_login_employee()

    def submit(self):
        """Override submit method to send to manager instead of HOD."""
        if not self.approve_request_ids:
            raise UserError(_("You cannot submit an empty item list for requisition."))
        
        # Schedule activity for manager
        if self.manager_id and self.manager_id.user_id:
            self.activity_schedule(
                'ng_store_requisition.mail_activity_data_sr',
                user_id=self.manager_id.user_id.id,
                note=_('New Store Requisition requires your approval')
            )
        
        self.write({"state": "submit"})
        
    def manager_approve(self):
        """Replace department_manager_approve with manager_approve."""
        context = self.env.context
        if not context.get("approved", False):
            return {
                "type": "ir.actions.act_window",
                "res_model": "ir.request.wizard",
                "views": [[False, "form"]],
                "context": {"request_id": self.id},
                "target": "new",
            }
        
        # Notify inventory managers
        users = self.env.ref('ng_store_requisition.ng_store_requisition_finance').users
        for user in users:
            self.activity_schedule(
                'ng_store_requisition.mail_activity_data_sr',
                user_id=user.id,
                note=_('Store Requisition is Approved By Manager')
            )
            
        self.write({"state": "approved"})

    def store_officer_approve(self):
        """Inherit store_officer_approve to add action_do_transfer before state change."""
        context = self.env.context
        approved = context.get("approved")
        recipient = self.recipient("department_manager", self.department)
        # global show_error
        
        if not approved:
            # send mail to the author.
            return {
                "type": "ir.actions.act_window",
                "res_model": "ir.request.wizard",
                "views": [[False, "form"]],
                "context": {"request_id": self.id, 'rejecter_name': 'Inventory Manager'},
                "target": "new",
            }
        else:
            not_available = self.approve_request_ids.filtered(lambda r: r.state not in ["available"])
            if not_available:
                raise UserError(
                    _(
                        "Your Request Can not processed. It can be processed once goods is available."
                    ))
                return
            else:
                users = self.env.ref('ng_store_requisition.ng_store_requisition_procurement').users
                for user in users:
                    self.activity_schedule('ng_store_requisition.mail_activity_data_sr',
                                           user_id=user.id,
                                           note=_('Store Requisition is Approved By Inventory Manager!'))
                # Call action_do_transfer before changing state
                self.action_do_transfer()
                self.write({"state": "cpo"})

    def action_do_transfer(self):
        if self:
            if not self.src_location_id or not self.dst_location_id:
                raise UserError(_("Source and destination locations must be set."))

            src_location_id = self.src_location_id.id
            dst_location_id = self.dst_location_id.id
            
            # Search for picking type with broader criteria first
            domain = [
                ("code", "=", "internal"),
            ]
            
            stock_picking = self.env["stock.picking"]
            picking_type = self.env["stock.picking.type"].search(domain, limit=1)
            
            if not picking_type:
                raise UserError(_("No active internal operation type found. Please configure an internal operation type."))
                
            payload = {
                "location_id": src_location_id,
                "location_dest_id": dst_location_id,
                "picking_type_id": picking_type.id,
                "move_type": "direct",
                "user_id": self.env.user.id,
                "scheduled_date": fields.Datetime.now(),
                "immediate_transfer": False,
                "company_id": self.company_id.id,
            }
            
            try:
                stock_picking_id = stock_picking.create(payload)
                move_id = self.stock_move(self.approve_request_ids, stock_picking_id)
                self.process(stock_picking_id)
            except Exception as e:
                raise UserError(_("Failed to create transfer: %s") % str(e))

    def process(self, picking_id):
        pickings_to_do = self.env["stock.picking"]
        pickings_not_to_do = self.env["stock.picking"]

        for picking in picking_id:
            # If still in draft => confirm and assign
            if picking.state == "draft":
                picking.action_confirm()
                if picking.state != "assigned":
                    picking.action_assign()
                    if picking.state != "assigned":
                        raise UserError(
                            _(
                                "Could not reserve all requested products. Please use the 'Mark as Todo' button to handle the reservation manually."
                            )
                        )
        pickings_to_validate = picking_id.ids
        if pickings_to_validate:
            pickings_to_validate = self.env["stock.picking"].browse(pickings_to_validate)
            pickings_to_validate = pickings_to_validate - pickings_not_to_do
            pickings_to_validate.action_confirm()
            return pickings_to_validate.with_context(skip_immediate=True).button_validate()
        return True


class IRRequestApprove(models.Model):
    _inherit = "ng.store.request.approve"

    @api.depends('request_id.state')
    def _compute_parent_state(self):
        for record in self:
            record.parent_state = record.request_id.state

    parent_state = fields.Char(
        compute='_compute_parent_state',
        store=False
    )