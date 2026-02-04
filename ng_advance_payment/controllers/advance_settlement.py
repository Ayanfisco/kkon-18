# -*- coding: utf-8 -*-
import logging
from dateutil.relativedelta import relativedelta
from odoo import http, fields
from odoo.tests import Form
from odoo.http import request
from odoo.addons.api_auth.util.helper import validate_token
from ..utils.main import get_eservice_default_company

_logger = logging.getLogger(__name__)


INVOICE_READ_FIELDS = [
    "name",
    "invoice_date",
    "date",
    "invoice_payment_term_id",
    "journal_id",
    "invoice_date_due",
    "invoice_line_ids",
    "source",
]

INVOICE_CREATE_FIELDS = INVOICE_READ_FIELDS + [
    "move_type",
]

PAYMENT_READ_FIELDS = [
    "partner_id",
    "payment_type",
    "date",
    "ref",
    "amount",
]

PAYMENT_CREATE_FIELDS = PAYMENT_READ_FIELDS + [
    "journal_id",
]


# This value is for situations in which the product's selling price is 0
NUMBER_OF_INVOICES = 1


class AdvancePaymentSettlement(http.Controller):

    @validate_token
    @http.route(
        "/fb_api/get-advance-payment-settlement/json",
        auth="public",
        type="json",
        csrf=False,
        cors="*",
    )
    def get_advance_payment_settlement_json(self):
        """Get a list of partners on the system.

        Args:
            None

        Returns:
            list: List of serialized invoice records.
        """
        domain = [("move_type", "=", "out_invoice")]
        invoice_number = request.get_json_data().get("invoice_number")
        if invoice_number:
            domain += [("name", "=", invoice_number)]
        records = request.env["account.move"].sudo().search(domain, limit=1)
        return records.read(INVOICE_READ_FIELDS)

    @http.route(
        "/fb_api/create-advance-payments/json",
        auth="public",
        type="json",
        csrf=False,
        cors="*",
    )
    def create_advance_payment_settlement_json(self):
        """Create a new payment on the system"""
        invalid_fields = []
        AccountPayment = request.env["account.payment"].sudo()
        cleaned_data = self._get_cleaned_payment_create_values(request.get_json_data())
        for field in PAYMENT_CREATE_FIELDS:
            if not cleaned_data.get(field):
                invalid_fields.append(field)
        if invalid_fields:
            return {
                "code": -32602,
                "error": "Invalid params",
                "invalid_fields": {v: cleaned_data[v] for v in invalid_fields},
            }
        default_company_int_id: str = get_eservice_default_company(request._cr)
        company = request.env["res.company"].sudo().browse([default_company_int_id])
        payment = AccountPayment.with_company(company).create(cleaned_data)
        return payment.read(PAYMENT_READ_FIELDS)

    def _get_cleaned_invoice_create_values(self, json_data={}):
        """Return cleaned json_data.

        The values passed into the function are not necessarily the values required to the create the invoice record and thus
        the values have to be cleaned up removing those fields that are not needed to create a new invoice record.

        Args:
            json_data (dict): Dictonary of data coming from client system.
                partner_id (int): id of the customer for which invoice is to be generated
                journal (str): id of the journal to be used for the transaction
                invoice_payment_term_id (int): id of the payment terms on the invoice
                customer_id (str): FOBID of customer
                invoice_date (str): String representation of the invoice date
                date (str): String representation of the invoice date
                invoice_date_due (str): String representation of the invoice date
                invoice_line_ids (list): List containing invoice lines:
                    product (dict): Dictionary of product values:
                        name (str): Name of product
                        code (str): Eservice code for product
                        quantity (int): Quantity of product
                        unit_price (float): Unit price of product
                        source (str): Source sales order document coming from eService

        Returns:
            dict: Dictionary of cleaned data.
                invoice_date (str): Invoice date expressed as spring formatted date.
                company_id (int): Database id of the company the invoice is meant for.
                invoice_date_due (str): String-formatted invoice due date.
                partner_id (int): Database id of the customer.
                journal_id (str): Database id of the journal used for this invoice.
                invoice_payment_term_id (str): Database id of the payment term.
                move_type (str): Move type. Default is 'out_invoice'.
                invoice_line_ids (list): List of invoice lines:
                    product_id (int): Database id of the product.
                    quantity (int): Quantity of product to add to the invoice.
                    price_unit: Unit price of product.
        """
        cleaned_data = {}
        ResPartner = request.env["res.partner"].sudo()
        for field in json_data:
            if field in INVOICE_CREATE_FIELDS:
                cleaned_data[field] = json_data[field]
        eservice_company_id = get_eservice_default_company(request._cr)
        cleaned_data["invoice_date"] = fields.Date.from_string(json_data["date"])
        cleaned_data.setdefault("company_id", int(eservice_company_id))
        cleaned_data["invoice_date_due"] = fields.Date.from_string(json_data["date"])
        # partner = ResPartner.search(
        #     [('x_studio_partner_id', '=', json_data['customer_id'])], limit=1)
        # added for the sake of preventing any error
        partner = ResPartner.search([("id", "=", 10)], limit=1)
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
        payment_term = request.env["account.payment.term"].sudo().search([], limit=1)
        cleaned_data["partner_id"] = partner.id
        cleaned_data["journal_id"] = journal.id
        cleaned_data["invoice_payment_term_id"] = payment_term.id
        cleaned_data["move_type"] = "out_invoice"
        product_id = request.env["product.product"]._get_product_from_code(
            json_data.get("product").get("code")
        )
        cleaned_data["invoice_line_ids"] = [
            (
                0,
                0,
                {
                    "product_id": product_id and product_id.id,
                    "quantity": 1,
                    "account_id": int(
                        json_data.get(
                            "income_account_id",
                            int(product_id.property_account_income_id),
                        )
                    ),
                    "price_unit": product_id and product_id.list_price,
                    "discount": json_data.get("product").get("discount", 0),
                },
            )
        ]
        return cleaned_data
