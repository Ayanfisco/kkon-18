from odoo import fields, models, api, _, exceptions
from markupsafe import Markup


class AccountMoveInherit(models.Model):
    """docstring for ClassName"""

    _inherit = "account.move.line"

    customer_id = fields.Many2one(comodel_name="res.partner", string="Customer/Vendor")


class PaymentRequestLine(models.Model):
    _name = "payment.requisition.line"
    _description = "payment.requisition.line"

    name = fields.Char("Description", required=True)
    request_amount = fields.Float("Requested Amount", required=True)
    approved_amount = fields.Float("Approved Amount")
    payment_request_id = fields.Many2one(
        "payment.requisition", string="Payment Request"
    )
    expense_account_id = fields.Many2one("account.account", "Account")
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Analytic Account"
    )
    state = fields.Char(compute="check_state", string="State")
    partner_id = fields.Many2one("res.partner", string="Customer/Vendor")

    @api.depends("payment_request_id")
    def check_state(self):
        self.state = self.payment_request_id.state
        for record in self:
            if record.state in ('hod', 'internal', 'md', 'done'):
                pass
                # raise exceptions.ValidationError("Cannot change state when state is 'md', or 'done'.")
            return None

    @api.onchange("request_amount")
    def _get_request_amount(self):
        if self.request_amount:
            amount = self.request_amount
            self.approved_amount = amount

class PaymentRequest(models.Model):
    _inherit = ["mail.thread"]
    _name = "payment.requisition"
    _description = "Payment Requisition"

    @api.depends(
        "request_line",
        "request_line.request_amount",
        "request_line.approved_amount",
        "state",
    )
    def _compute_requested_amount(self):
        for record in self:
            requested_amount = 0
            approved_amount = 0
            for line in record.request_line:
                requested_amount += line.request_amount
                approved_amount += line.approved_amount
                #
                record.amount_company_currency = approved_amount
                record.approved_amount = approved_amount
                record.requested_amount = requested_amount

            # record.amount_company_currency = requested_amount
            company_currency = record.company_id.currency_id
            current_currency = record.currency_id
            conversion_rate = company_currency._get_conversion_rate(company_currency, current_currency, record.company_id, record.date)

            if company_currency != current_currency:
                # amount = company_currency.compute(requested_amount, current_currency)
                approved_amount = record.approved_amount/conversion_rate
                # requested_amount = requested_amount/conversion_rate
                record.amount_company_currency = requested_amount/conversion_rate
                record.approved_amount = requested_amount
                record.requested_amount = requested_amount

    company_currency = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    company_currency_sign = fields.Char(string='Company Currency Sign', compute='_compute_company_currency_sign', readonly=True)

    @api.depends('company_currency')
    def _compute_company_currency_sign(self):
        for record in self:
            record.company_currency_sign = record.company_currency.symbol or record.company_currency.name


    name = fields.Char("Name", default="/", copy=False)
    requester_id = fields.Many2one(
        "res.users", "Requester", required=True, default=lambda self: self.env.user
    )
    employee_id = fields.Many2one("hr.employee", "Employee", required=True)
    department_id = fields.Many2one("hr.department", "Department")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    description = fields.Text(string="Description")
    bank_id = fields.Many2one("res.bank", "Bank")
    bank_account = fields.Char("Bank Account", copy=False)
    request_line = fields.One2many(
        "payment.requisition.line", "payment_request_id", string="Lines", copy=False
    )
    requested_amount = fields.Float(
        compute="_compute_requested_amount", string="Requested Amount", store=True
    )
    approved_amount = fields.Float(
        compute="_compute_requested_amount", string="Approved Amount", store=True
    )
    amount_company_currency = fields.Float(
        compute="_compute_requested_amount",
        string="Amount In Company Currency",
        store=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.user.company_id.currency_id.id,
    )

    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env["res.company"]._company_default_get(
            "payment.requisition"
        ),
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("hod", "Await HOD"),
            ("internal", "Await Internal Control"),
            ("md", "Await Head of Finance/MD"),
            ("done", "Approved"),
            ("paid", "Paid"),
            ("refused", "Refused"),
            ("cancelled", "Cancelled"),
        ],
        tracking=True,
        default="draft",
        string="State",
    )


    move_id = fields.Many2one("account.move", string="Journal Entry")
    journal_id = fields.Many2one("account.journal", string="Journal")
    update_cash = fields.Boolean(
        string="Update Cash Register?",
        readonly=False,
        states={"draft": [("readonly", True)]},
        help="Tick if you want to update cash register by creating cash transaction line.",
    )
    cash_id = fields.Many2one(
        "account.bank.statement",
        string="Cash Register",
        domain=[("journal_id.type", "in", ["cash"]), ("state", "=", "open")],
        required=False,
        readonly=False,
        states={"draft": [("readonly", False)]},
    )


    @api.model
    def create(self, vals):
        if not vals.get("name"):
            vals["name"] = self.env["ir.sequence"].next_by_code("payment.requisition")


        return super(PaymentRequest, self).create(vals)

    @api.onchange("requester_id")
    def onchange_requester(self):
        employee = self.env["hr.employee"].search(
            [("user_id", "=", self._uid)], limit=1
        )
        self.employee_id = employee.id
        self.department_id = (
            employee.department_id and employee.department_id.id or False
        )

    def action_confirm(self):
        if not self.request_line:
            raise exceptions.UserError(
                _("Can not confirm request without request lines.")
            )
        
        # Determine the next approval step based on requester's role
        requester_user = self.requester_id
        next_state = self._determine_next_approval_state(requester_user)
        
        body = Markup(
            "💰 <b>Payment Requisition %s</b><br/>"
            "Request has been confirmed by <b>%s</b>.<br/>"
            "Please check and approve."
        ) % (self.name, self.env.user.partner_id.name)
        subject = _("Payment Requisition %s" % (self.name,))
        
        # Notify appropriate group based on next state
        if next_state == 'hod':
            # Notify the employee's manager
            manager = self.employee_id.parent_id
            if manager and manager.user_id:
                self.notify(body, subject, users=[manager.user_id.id])
        elif next_state == 'internal':
            self.notify(body, subject, group="ng_payment_request.group_internal")
        elif next_state == 'md':
            # Final approver group is Head of Finance; we still use state 'md' for final step label
            self.notify(body, subject, group="ng_payment_request.group_finance_head")
        
        return self.write({"state": next_state})

    def _determine_next_approval_state(self, requester_user):
        """Determine the next approval state based on organizational hierarchy.

        Always start with Line Manager (HOD) approval when a manager exists.
        If the requester has no manager configured, raise an error to enforce
        proper hierarchy configuration.
        """
        # If the employee has a manager with a linked user, start with HOD
        employee_manager_user = self.employee_id.parent_id.user_id
        if employee_manager_user:
            return 'hod'

        # No manager configured
        raise exceptions.UserError(_(
            "No Line Manager configured for the employee. Please set a manager on the employee record before confirming the request."
        ))

    def action_hod_approve(self):
        # Check if current user is the employee's manager
        manager_user = self.employee_id.parent_id.user_id
        if not manager_user or self.env.user.id != manager_user.id:
            raise exceptions.UserError(_("Only the employee's manager can approve this request."))
        
        # Prevent requester from approving their own request
        if self.env.user.id == self.requester_id.id:
            raise exceptions.UserError(_("You cannot approve your own request."))
        
        # Prevent employee from approving their own request
        if self.env.user.id == self.employee_id.user_id.id:
            raise exceptions.UserError(_("The employee cannot approve their own request."))
        
        body = Markup(
            "✅ <b>Payment Requisition %s</b><br/>"
            "Request has been approved by Manager <b>%s</b>.<br/>"
            "Please check and approve."
        ) % (self.name, self.env.user.partner_id.name)
        subject = _("Payment Requisition %s" % (self.name,))
        
        # Always go to internal control - no skipping based on requester's role
        # Internal control will handle their own approval logic
        self.notify(body, subject, group="ng_payment_request.group_internal")
        return self.write({"state": "internal"})

    def action_internal_approve(self):
        # Check separation of duties - approver cannot be the requester
        if self.env.user.id == self.requester_id.id:
            raise exceptions.UserError(_("You cannot approve your own request."))

        # Check separation of duties - approver cannot be the employee's manager if manager is in internal control
        manager_user = self.employee_id.parent_id.user_id
        if manager_user and self.env.user.id == manager_user.id:
            raise exceptions.UserError(_("The employee's manager cannot approve in Internal Control step. Another Internal Control member must approve."))

        # Ensure the approver is in the Internal Control group
        internal_group = self.env.ref('ng_payment_request.group_internal')
        if self.env.user not in internal_group.users:
            raise exceptions.UserError(_("Only Internal Control group members can approve at this step."))

        body = Markup(
            "🔍 <b>Payment Requisition %s</b><br/>"
            "Request has been approved by Internal Control <b>%s</b>.<br/>"
            "Please check and approve."
        ) % (self.name, self.env.user.partner_id.name)
        subject = _("Payment Requisition %s" % (self.name,))

        # Notify appropriate group based on amount
        if self.approved_amount >= 10000000:  # 10M threshold
            # High-value request - notify MD group
            self.notify(body, subject, group="ng_payment_request.group_managing_director")
        else:
            # Regular request - notify Head of Finance group
            self.notify(body, subject, group="ng_payment_request.group_finance_head")
        
        return self.write({"state": "md"})

    def action_md_approve(self):
        # Check separation of duties - approver cannot be the requester
        if self.env.user.id == self.requester_id.id:
            raise exceptions.UserError(_("You cannot approve your own request."))

        finance_head_group = self.env.ref('ng_payment_request.group_finance_head')
        md_group = self.env.ref('ng_payment_request.group_managing_director')
        
        # Check if amount requires MD approval
        if self.approved_amount >= 10000000:  # 10M threshold
            # High-value request - only MD can approve
            if self.env.user not in md_group.users:
                raise exceptions.UserError(_("Only Managing Director group members can approve high-value requests (>= 10M)."))
            
            approver_role = "Managing Director"
        else:
            # Regular request - only Head of Finance can approve
            if self.env.user not in finance_head_group.users:
                raise exceptions.UserError(_("Only Head of Finance group members can approve regular requests (< 10M)."))
            
            # Ensure another Head of Finance member approves (not the requester if requester is also in HoF)
            requester_user = self.requester_id
            if requester_user in finance_head_group.users and requester_user.id == self.env.user.id:
                raise exceptions.UserError(_("Another Head of Finance member must approve this request."))
            
            approver_role = "Head of Finance"

        body = Markup(
            "🎉 <b>Payment Requisition %s</b><br/>"
            "Request has been approved by %s <b>%s</b>.<br/>"
            "Request is now approved."
        ) % (self.name, approver_role, self.env.user.partner_id.name)
        subject = _("Payment Requisition %s" % (self.name,))

        self.notify(body, subject, group="account.group_account_invoice")
        return self.write({"state": "done"})


    def notify(self, body, subject, users=None, group=None):
        partner_ids = []
        if group:
            users = self.env.ref(group).users
            for user in users:
                partner_ids.append(user.partner_id.id)
        elif users:
            users = self.env["res.users"].browse(users)
            for user in users:
                partner_ids.append(user.partner_id.id)
        if partner_ids:
            self.message_post(body=body, subject=subject, partner_ids=partner_ids)
        return True

    def action_pay(self):
        move_obj = self.env["account.move"]
        move_line_obj = self.env["account.move.line"]
        currency_obj = self.env["res.currency"]
        statement_line_obj = self.env["account.bank.statement.line"]

        ctx = dict(self._context or {})
        for record in self:

            company_currency = record.company_id.currency_id
            current_currency = record.currency_id

            ctx.update({"date": record.date})
            conversion_rate = company_currency._get_conversion_rate(company_currency, current_currency, record.company_id, record.date)
            amount = record.approved_amount/conversion_rate
            if record.journal_id.type == "purchase":
                sign = 1
            else:
                sign = -1
            asset_name = record.description # record.name
            reference = record.name

            move_vals = {
                "date": record.date,
                "ref": reference,
                "journal_id": record.journal_id.id,
                "move_type": 'entry',
            }

            move_id = move_obj.with_context(check_move_validity=False).create(move_vals)
            journal_id = record.journal_id.id
            partner_id = record.employee_id.address_home_id
            if not partner_id:
                print("Please Specify Employee Address")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Warning',
                        'message': "Please specify Employee Home Address in the Employee Form!",
                        'sticky': False,
                    }
                }
            for line in record.request_line:
                conversion_rate = company_currency._get_conversion_rate(company_currency, current_currency, record.company_id, record.date)
                amount_line = line.approved_amount/conversion_rate
                test_amount = line.approved_amount/conversion_rate
                move_line_obj.with_context(check_move_validity=False).create(
                    {
                        "name": asset_name,
                        "ref": reference,
                        "move_id": move_id.id,
                        "account_id": line.expense_account_id.id or record.journal_id.default_account_id.id,
                        "balance": test_amount,
                        "journal_id": journal_id,
                        "partner_id": partner_id.id,
                        "customer_id": line.partner_id.id,
                        "currency_id": current_currency.id,
                        "amount_currency": amount_line,
                        "analytic_distribution": {str(line.analytic_account_id.id):100.00} if line.analytic_account_id else False,
                        "date": record.date,
                    }
                )
            approved_amount_base_cur = 0
            for line in record.request_line:
                test_amount = line.approved_amount/conversion_rate
                approved_amount_base_cur += test_amount
            move_line_obj.with_context(check_move_validity=False).create(
                {
                    "name": asset_name,
                    "ref": reference,
                    "move_id": move_id.id,
                    "account_id": record.journal_id.default_account_id.id,
                    "balance": (-1*approved_amount_base_cur),
                    "journal_id": journal_id,
                    "partner_id": partner_id.id,
                    "customer_id": line.partner_id.id,
                    "currency_id": current_currency.id,
                    "amount_currency": (-1 * record.approved_amount),
                    "date": record.date,
                }
            )
            record.move_id = move_id.id
            if record.update_cash:
                type = "general"
                amount = -1 * record.approved_amount
                account = record.journal_id.default_debit_account_id.id
                if not record.journal_id.type == "cash":
                    raise exceptions.Warning(
                        _("Journal should match with selected cash register journal.")
                    )
                stline_vals = {
                    "name": record.name or "?",
                    "amount": amount,
                    "type": type,
                    "account_id": account,
                    "statement_id": record.cash_id.id,
                    "ref": record.name,
                    "partner_id": partner_id.id,
                    "date": record.date,
                    "PaymentRequest_id": record.id,
                }
                statement_line_obj.create(stline_vals)
        self.state = "paid"
        return True

    def action_cancel(self):
        self.state = "cancelled"
        return True

    def action_reset(self):
        self.state = "draft"
        return True

    def action_refuse(self):
        self.state = "refused"
        return True


class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"

    PaymentRequest_id = fields.Many2one("payment.requisition", string="Payment Request")
