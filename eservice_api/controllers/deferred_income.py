from odoo import http, fields
from odoo.http import request
from .invoice import INVOICE_CREATE_FIELDS, INVOICE_READ_FIELDS
from odoo.tests import Form
from ..utils.main import get_eservice_default_company


class DeferredIncomeHome(http.Controller):

    @http.route(
        "/fb_api/deferred_income/json",
        auth="public",
        type="json",
        csrf=False,
        cors="*",
    )
    def create_deferred_income_json(self):
        """Create deferred income"""

        # Second create the invoice
        # First create the payment
        # third, create the deferred income
        DeferredIncome = request.env["account.asset"].sudo()
        deferred_income_model_id = (
            request.env["res.config.settings"]
            .with_user(request.env.ref("base.user_admin"))
            .get_values()["eservice_deferred_model_id"]
        )
        data = request.get_json_data()
        values = {
            "name": data.get("name"),
            "original_value": data.get("amount"),
            "book_value": 0,
            "acquisition_date": fields.Date.from_string(
                data.get("date")
            ),
            "prorata_date": fields.Date.from_string(data.get("date")),
            "model_id": int(deferred_income_model_id),
            "asset_type": "sale",
            "method_number": data.get("number_of_installments"),
            "prorata_computation_type": "constant_periods",
        }
        deferred_income = DeferredIncome.create(values)
        deferred_income._onchange_model_id()
        deferred_income.compute_depreciation_board()
        deferred_income.validate()
        [res] = deferred_income.read(
            ["name", "model_id", "method_number"]
        )
        return res

    def add_invoice_json(self, json_data={}):
        """Create a new invoice on the system"""
        AccountInvoice = request.env["account.move"].sudo()
        if not json_data:
            json_data = request.get_json_data()
        cleaned_data = self._get_cleaned_invoice_create_values(
            json_data=json_data
        )
        invoice = AccountInvoice.create(cleaned_data)
        invoice.action_post()
        partner = invoice.partner_id
        [partner_dict] = partner.read(
            ["name", "email", "phone", "x_studio_partner_id"]
        )
        [invoice_dict] = invoice.read(INVOICE_READ_FIELDS)
        invoice_dict["customer"] = partner_dict
        action_data = invoice.action_register_payment()
        wizard = Form(
            request.env["account.payment.register"]
            .sudo()
            .with_context(action_data["context"])
        ).save()
        wizard.action_create_payments()
        return invoice_dict

    def _get_cleaned_invoice_create_values(self, json_data={}):
        """Clean up values coming from the other system"""
        cleaned_data = {}
        ResPartner = request.env["res.partner"].sudo()
        for field in json_data:
            if field in INVOICE_CREATE_FIELDS:
                cleaned_data[field] = json_data[field]
        eservice_company_id = get_eservice_default_company(
            request._cr
        )
        cleaned_data["invoice_date"] = fields.Date.from_string(
            json_data["date"]
        )
        cleaned_data.setdefault(
            "company_id", int(eservice_company_id)
        )
        cleaned_data["invoice_date_due"] = fields.Date.from_string(
            json_data["date"]
        )
        partner = ResPartner._find_or_create_partner(
            json_data["customer"]
        )
        journal = (
            request.env["account.journal"]
            .sudo()
            .search(
                [
                    ("type", "=", "sale"),
                    ("eservice_code", "=", json_data["journal"]),
                    ("company_id", "=", int(eservice_company_id)),
                ],
                limit=1,
            )
        )
        payment_term = (
            request.env["account.payment.term"]
            .sudo()
            .search([], limit=1)
        )
        cleaned_data["partner_id"] = partner.id
        cleaned_data["journal_id"] = journal.id
        cleaned_data["invoice_payment_term_id"] = payment_term.id
        cleaned_data["move_type"] = "out_invoice"
        cleaned_data["invoice_line_ids"] = [
            (
                0,
                0,
                {
                    "product_id": request.env[
                        "product.product"
                    ]._get_product_from_code(
                        line.get("product").get("code")
                    )
                    and request.env["product.product"]
                    ._get_product_from_code(
                        line.get("product").get("code")
                    )
                    .id,
                    "quantity": line["quantity"] or 1,
                    "price_unit": request.env[
                        "product.product"
                    ]._get_product_from_code(
                        line.get("product").get("code")
                    )
                    and request.env["product.product"]
                    ._get_product_from_code(
                        line.get("product").get("code")
                    )
                    .list_price,
                },
            )
            for line in json_data["invoice_lines"]
        ]
        if json_data.get("deferred_revenue_details"):
            pass
        return cleaned_data

    def get_invoice_line_values(self, json_data):
        vals = {}
        if json_data.get("deferred_revenue_details"):
            deferred_income_account_id = 0
            vals.setdefault("account_id", deferred_income_account_id)
        invoice_line_ids = []
        for line in json_data["invoice_lines"]:
            vals["product_id"] = (
                request.env["product.product"]._get_product_from_code(
                    line.get("product").get("code")
                )
                and request.env["product.product"]
                ._get_product_from_code(
                    line.get("product").get("code")
                )
                .id
            )
            vals["quantity"] = line["quantity"] or 1
            vals["price_unit"] = (
                request.env["product.product"]._get_product_from_code(
                    line.get("product").get("code")
                )
                and request.env["product.product"]
                ._get_product_from_code(
                    line.get("product").get("code")
                )
                .list_price
            )
            invoice_line_ids.append((0, 0, vals))
