import logging
import calendar
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FobDeferredRevenue(models.Model):
    """Deferred Revenue"""

    _name = "fob.deferred.revenue"
    _description = "Custom Deferred Revenue"

    name = fields.Char("Name")
    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        readonly=True,
        readonly="state != 'draft'",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        domain="[('customer_rank', '>', 0)]",
    )
    start_date = fields.Date("Start Date")
    duration = fields.Integer(
        "Number of Installments",
        readonly=True,
        readonly="state != 'draft'",
    )
    duration_unit = fields.Selection(
        selection=[
            ("months", "Months"),
            ("years", "Years"),
        ],
        string="Unit",
        default="months",
        readonly=True,
        readonly="state != 'draft'",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        readonly=True,
        readonly="state != 'draft'",
    )
    deferred_revenue_account_id = fields.Many2one(
        "account.account",
        string="Deferred Income Account",
        domain="[('account_type', '=', 'liability_current')]",
        readonly=True,
        readonly="state != 'draft'",
    )
    revenue_account_id = fields.Many2one(
        "account.account",
        string="Income Account",
        domain="[('account_type', 'in', ('income', 'income_other'))]",
        readonly=True,
        readonly="state != 'draft'",
    )
    amount_initial = fields.Float(
        "Initial Amount",
        readonly=True,
        readonly="state != 'draft'",
    )
    is_model = fields.Boolean(
        "Is Model?",
        readonly=True,
        readonly="state != 'draft'",
        copy=False,
    )
    model_id = fields.Many2one(
        "fob.deferred.revenue",
        string="Model",
        readonly=True,
        readonly="state != 'draft'",
    )
    state = fields.Selection(
        [
            ("draft", "New"),
            ("open", "Running"),
            ("close", "Closed"),
            ("cancel", "Cancelled"),
        ],
        string="State",
        default="draft",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.user.company_id.id,
    )
    line_ids = fields.One2many(
        "fob.deferred.revenue.line",
        "revenue_id",
        string="Revenue Lines",
    )

    invoice_line_ids = fields.One2many(
        "fob.invoice.line", "revenue_id", string="Product Lines"
    )

    revenue_line_count = fields.Float(
        "Revenue Line Count", compute="_compute_revenue_line_count"
    )

    def _compute_revenue_line_count(self):
        for rec in self:
            rec.revenue_line_count = len(rec.line_ids)

    def set_to_running(self):
        """Move state to 'running'"""
        # self._post_
        if not self.line_ids:
            raise UserError("Please compute revenue board first!!!")
        self.state = "open"

    def set_to_close(self):
        """Move state to 'running'"""
        self.state = "close"

    def set_to_cancel(self):
        """Move state to 'cancel'"""
        self.state = "close"

    def set_to_draft(self):
        """Move state to 'draft'"""
        self.state = "draft"

    @api.onchange("model_id")
    def _onchange_model_id(self):
        if model_id := self.model_id:
            self.deferred_revenue_account_id = (
                model_id.deferred_revenue_account_id
                and model_id.deferred_revenue_account_id.id
            )
            self.revenue_account_id = (
                model_id.revenue_account_id
                and model_id.revenue_account_id.id
            )
            self.journal_id = (
                model_id.journal_id and model_id.journal_id.id
            )
            self.duration = model_id.duration
            self.duration_unit = model_id.duration_unit

    def compute_revenue_board(self):
        """Compute the number of installments based on months"""
        self.line_ids = False
        revenue_date = self.start_date
        installment = self.amount_initial / self.duration
        for i in range(self.duration):
            if self.duration_unit == "months":
                revenue_date += relativedelta(months=1)
            elif self.duration_unit == "years":
                revenue_date += relativedelta(years=1)
            else:
                pass
            _logger.info(f"---- count = {i} -------------")
            _logger.info(
                f"---- Revenue date is {revenue_date} -------------"
            )
            self.line_ids += (
                self.env["fob.deferred.revenue.line"]
                .sudo()
                .create(
                    {
                        "name": "/",
                        "date_revenue": date(
                            revenue_date.year,
                            revenue_date.month,
                            calendar.monthrange(
                                revenue_date.year, revenue_date.month
                            )[-1],
                        ),
                        "ref": self.name + " " + "Installment",
                        "amount": installment,
                        "revenue_id": self.id,
                    }
                )
            )

    def _cron_post_revenue(self):
        running_deferred_revenues = self.search(
            [("state", "=", "open")]
        )
        _logger.info(
            f"=================== Running deferred revenues {running_deferred_revenues} ======================"
        )
        return True


class FobDeferredRevenueLine(models.Model):
    """Deferred Revenue Line"""

    _name = "fob.deferred.revenue.line"
    _description = "Deferred Revenue Line"

    date_revenue = fields.Date(
        "Revenue Date",
        readonly=True,
        readonly="state != 'draft'",
    )
    name = fields.Char("Journal Entry", default="/")
    ref = fields.Char(
        "Reference",
        readonly=True,
        readonly="state != 'draft'",
    )
    amount = fields.Float(
        "Installment",
        readonly=True,
        readonly="state != 'draft'",
    )
    state = fields.Selection(
        related="revenue_id.state", string="State"
    )
    revenue_id = fields.Many2one(
        "fob.deferred.revenue", string="Revenue"
    )
    posted = fields.Boolean("Posted?")
    move_id = fields.Many2one("account.move", string="Journal Entry")

    def function_name(parameter1, parameter2):
        """One-line summary.

        Extended description of the function, including details
        about parameters, return value, and exceptions.

        Args:
            parameter1 (type): Description of parameter1.
            parameter2 (type): Description of parameter2.

        Returns:
            type: Description of the return value.

        Raises:
            ExceptionType: Description of when an exception is raised.
        """
        # Function code goes here
        pass

    def create_move(self):
        """Create account move corresponding to depreciation line.

        Create account move using the amount on the record. The journal configured on the related revenue_id is used as the journal
        for the accounting entry.

        Args:
            None

        Returns:
            bool: True if the record was successfully created, False otherwise.
        """
        for record in self:
            return record._create_move()

    def _create_move(self):
        """Create account move corresponding to depreciation line.

        Create account move using the amount on the record. The journal configured on the related revenue_id is used as the journal
        for the accounting entry.

        Account          | Debit       |  Credit
        -----------------------------------------------
        Deferred Revenue | 5,000.00    |     0.00
        Revenue          |     0.00    | 5,000.00
        -----------------------------------------------
                        | 5,000.00    | 5,000.00
        Args:
            None

        Returns:
            bool: True if the record was successfully created, False otherwise.
        """
        AccountInvoice = self.env["account.move"].sudo()
        for record in self:
            # product_id = record.revenue_id.invoice_line_ids[0].product_id
            journal_id = record.revenue_id.journal_id
            # it proved difficult to use invoice for this operation because of an accountable invoice line constraint that was repeatedly thrown
            move_vals = {
                # "move_type": "out_invoice",
                "company_id": record.revenue_id.company_id.id,
                "invoice_date": record.date_revenue,
                "partner_id": record.revenue_id.partner_id.id,
                "invoice_date_due": record.date_revenue,
                "journal_id": journal_id and journal_id.id,
                "line_ids": [
                    # credit leg (income)
                    (
                        0,
                        0,
                        {
                            "account_id": 125,
                            "partner_id": record.revenue_id.partner_id.id,
                            "name": "Income registration",
                            "credit": record.amount,
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
                            "account_id": record.revenue_id.deferred_revenue_account_id.id,
                            "partner_id": record.revenue_id.partner_id.id,
                            "name": "Debit to deferred income account",
                            "debit": record.amount,
                        },
                    )
                ],
            }
        move = AccountInvoice.create(move_vals)
        return record.write({"name": move.name, "move_id": move.id})


class InvoiceLines(models.Model):
    """Object for product lines stating qty and unit price"""

    _name = "fob.invoice.line"
    _description = "Invoice Line"

    product_id = fields.Many2one("product.product", string="Product")
    name = fields.Char(string="Description")
    uom_qty = fields.Float("Quantity")
    price_unit = fields.Float("Unit Price")
    uom_id = fields.Many2one("uom.uom", string="UoM")
    revenue_id = fields.Many2one(
        "fob.deferred.revenue", string="Revenue"
    )
    subtotal = fields.Float(string="Subtotal")

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if product_id := self.product_id:
            self.name = product_id.name
            self.price_unit = product_id.list_price
            self.uom_id = product_id.uom_id.id
