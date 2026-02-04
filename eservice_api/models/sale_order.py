from odoo import models, fields, api


RES_CONFIG_SETTINGS = "res.config.settings"
IR_PROPERTY = "ir.property"


class MakeDeferred(models.AbstractModel):
    """Class to make Regular invoices as deferred and vice-versa."""

    _name = "invoice.make.deferred"
    _description = "Deferred Invoice Revenue Processor"

    def _get_deferred_income_account_id(self):
        """Get deferred income account."""
        rcs = self.env[RES_CONFIG_SETTINGS].sudo().get_values()
        deferred_revenue_account_id = rcs.get("deferred_revenue_account_id", False)
        return deferred_revenue_account_id

    def _get_advance_account_id(self):
        """Get advance account."""
        rcs = self.env[RES_CONFIG_SETTINGS].sudo().get_values()
        advance_account_id = rcs.get("advance_account_id", False)
        return advance_account_id

    def _get_receivable_account_id(self):
        """Get receivable account."""
        receivable_account_id = self.env[IR_PROPERTY]._get(
            "property_account_receivable_id", "res.partner"
        )
        return receivable_account_id

    def _get_income_account_id(self, product_id=False):
        """Get income account."""
        if not product_id:
            return self.env["ir.property"]._get(
                "property_account_income_categ_id", "product.category"
            )

        income_account_id = product_id.property_account_income_id
        if not income_account_id:
            income_account_id = self.env[IR_PROPERTY]._get(
                "property_account_income_id",
                "product.template",
                product_id.product_tmpl_id.id,
            )
        return income_account_id

    @api.model
    def _make_invoice_deferred(self, invoice):
        """Make the invoice a deferred invoice"""
        if not invoice.is_deferred:
            return
        # Change the revenue account to deferred revenue account
        for line_id in invoice.invoice_line_ids:
            line_id.account_id = self._get_deferred_income_account_id()
        QUERY = """UPDATE account_move_line aml SET account_id = %s WHERE move_id = %s and debit > 0"""
        self.env.cr.execute(QUERY, (self._get_advance_account_id(), invoice.id))
        self.env.cr.commit()
        return True

    @api.model
    def _convert_to_actual_revenue(self, invoice):
        """Make the invoice a deferred invoice"""
        if not invoice.is_deferred:
            return

        # Converting to actual revenue
        for line_id in invoice.invoice_line_ids:
            line_id.account_id = self._get_income_account_id(line_id.product_id).id
        QUERY = """UPDATE account_move_line aml SET account_id = %s WHERE move_id = %s and debit > 0"""
        self.env.cr.execute(
            QUERY,
            (
                self._get_receivable_account_id()
                and self._get_receivable_account_id().id,
                invoice.id,
            ),
        )
        self.env.cr.commit()
        invoice.is_deferred = False
        return True


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_deferred = fields.Boolean("Is Deferred?")

    def _create_deferred_invoice_and_payment(self):
        """Generate deferred revenue invoice and payment"""
        ctx = self.env.context.copy()
        ctx.update(is_deferred=self.is_deferred, sale_order_ids=self.ids)
        invoice_creation_wizard = (
            self.env["sale.advance.payment.inv"]
            .sudo()
            .with_context(ctx)
            .create(
                {
                    "sale_order_ids": self.ids,
                }
            )
        )
        deferred_invoice = invoice_creation_wizard.with_context(ctx)._create_invoices(
            self
        )
        if self.is_deferred:
            deferred_invoice.update({"is_deferred": self.is_deferred})
        self.env["invoice.make.deferred"]._make_invoice_deferred(deferred_invoice)
        deferred_invoice.action_post()

        JOURNAL_ID = (
            self.env["account.journal"]
            .sudo()
            .search([("type", "=", "bank")], limit=1)
            .id
        )

        payment_vals = {
            "payment_type": "inbound",
            "partner_id": deferred_invoice.partner_id.id,
            "amount": deferred_invoice.amount_total,
            "ref": deferred_invoice.name,
            "currency_id": deferred_invoice.currency_id.id,
            "journal_id": JOURNAL_ID,
        }
        payment = self.env["account.payment"].sudo().create(payment_vals)
        payment.action_post()
        return deferred_invoice, payment

    def _recognise_actual_revenue(self):
        for order in self:
            if not order.is_deferred:
                continue
            if not order.invoice_ids:
                continue
            self.env["invoice.make.deferred"]._convert_to_actual_revenue(
                invoice=order.invoice_ids
            )
        return True
