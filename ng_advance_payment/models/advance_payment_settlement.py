from datetime import date
from odoo import models, fields, api


class AdvPaymentSettlement(models.Model):
    """Advance Payment Model."""

    _name = "advance.payment.settlement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Advance Payment Settlement"

    def _set_logged_in_user(self):
        """Set user id to the session user"""
        return self._uid

    def _set_default_currency(self):
        """Set default currency"""
        if not self.env.user.company_id.currency_id:
            return False
        return int(self.env.user.company_id.currency_id)

    name = fields.Char("name", default="/")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Customer")
    amount = fields.Monetary(string="Amount")
    currency_id = fields.Many2one(
        comodel_name="res.currency", string="Currency", default=_set_default_currency
    )
    journal_id = fields.Many2one(comodel_name="account.journal", string="Journal")
    date = fields.Date(string="Date", default=date.today())
    user_id = fields.Many2one(
        comodel_name="res.users", string="User", default=_set_logged_in_user
    )
    state = fields.Selection(
        selection=[("draft", "New"), ("open", "Submitted"), ("approve", "Approved")],
        default="draft",
        string="State",
    )
    move_id = fields.Many2one("account.move", string="Journal Entry")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.user.company_id
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["name"] = self._compute_next_sequence()
        return super().create(vals)

    def _compute_next_sequence(self):
        return self.env["ir.sequence"].next_by_code("ng_advance_payment.settlement")

    def validate(self):
        """Set document to 'open'"""
        self.state = "open"

    def approve(self):
        """Approve settlement"""
        self.state = "approve"

    def action_post(self):
        """Post journal entries for the settlement"""
        if not self.name or self.name == "/":
            self._compute_next_sequence()
        return self._post()

    def _post(self):
        """Post entries for this advance payment settlement"""
        AccountMove = self.env["account.move"].sudo()
        vals = {
            "name": self.name,
            "date": date.today(),
            "journal_id": int(self.journal_id),
            "line_ids": [
                (
                    0,
                    0,
                    {
                        # Debit Advance account
                        "account_id": self.env["res.config.settings"]
                        .sudo()
                        .get_values()
                        .get("default_advance_account_id"),
                        "partner_id": self.partner_id.id,
                        "name": "Customer Payment",
                        "currency_id": self.currency_id.id,
                        "debit": self.amount,  # For the debit leg
                    },
                ),
                (
                    0,
                    0,
                    {
                        "account_id": self.partner_id.property_account_receivable_id.id,  # Credit receivable
                        "partner_id": self.partner_id.id,
                        "name": "Customer Payment",
                        "currency_id": self.currency_id.id,
                        "credit": self.amount,  # For the credit leg
                    },
                ),
            ],
        }
        move_id = AccountMove.create(vals)
        move_id.action_post()
        self.move_id = move_id.id
        return True

    def action_view_move(self):
        """Open journal entry"""
        action = self.env.ref("account.action_move_journal_line")
        result = action.read()[0]
        if self.move_id:
            res = self.env.ref("account.view_move_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = self.move_id.id
        else:
            result["domain"] = "[('id', 'in', " + "[]" + ")]"
        return result
