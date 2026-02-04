import logging
from datetime import date
from odoo import models, fields, api
from ..utils.main import get_eservice_deferred_revenue_account_id

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    source = fields.Char("Source Sales Order")
    is_deferred = fields.Boolean("Deferred?")
    recognition_date = fields.Date("Recognition Date")
    revenue = fields.Char("Revenue document")

    @api.model
    def _cron_reverse_deferred_invoices(self):
        """Create reversal for deferred revenue invoice"""
        # Search for deferred invoice within the month
        # use the invoice date on the invoice
        unreversed_deferred_invoices = self.search(
            [
                ("invoice_date", "=", date.today()),
                ("is_deferred", "=", True),
                ("move_type", "=", "out_invoice"),
                ("revenue", "=", False),
            ]
        )
        return unreversed_deferred_invoices.create_revenue_posting()

    def create_revenue_posting(self):
        """Create posting to reverse deferred revenue"""
        deferred_revenue_account_id = (
            get_eservice_deferred_revenue_account_id(self._cr)
        )
        for move in self:
            if move.move_type != "out_invoice" or move.revenue:
                continue
            invoice_line = move.invoice_line_ids[0]
            account_id = (
                invoice_line.product_id.property_account_income_id
            )
            journal = (
                self.env["account.journal"]
                .sudo()
                .search(
                    [("deferred_revenue_reversal", "=", True)],
                    limit=1,
                )
            )
            vals = {
                "company_id": move.company_id.id,
                "invoice_date": move.date_revenue,
                "partner_id": move.partner_id.id,
                "invoice_date_due": move.date_revenue,
                "journal_id": journal and journal.id,
                "line_ids": [
                    # credit leg (income)
                    (
                        0,
                        0,
                        {
                            "account_id": account_id.id,
                            "partner_id": move.partner_id.id,
                            "name": f"Recognition of revenue for {move.name}",
                            "credit": move.amount,
                        },
                    )
                ]
                + [
                    # debit leg
                    (
                        0,
                        0,
                        {
                            # deferred revenue account
                            "account_id": int(
                                deferred_revenue_account_id
                            ),
                            "partner_id": move.partner_id.id,
                            "name": f"Recognition of revenue for {move.name}",
                            "debit": move.amount,
                        },
                    )
                ],
            }
            rev = AccountMove.create(vals)
            rev.action_post()
            move.update({"revenue": rev.name})
        return True
