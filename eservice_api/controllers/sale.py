from odoo import http, fields
from odoo.http import request
from odoo.addons.api_auth.util.helper import validate_token
from ..utils.main import (
    get_eservice_default_company
)


SALE_ORDER = "sale.order"
RES_PARTNER = "res.partner"
PRODUCT_PRODUCT = "product.product"
ORDER_ID = 28


class SaleHome(http.Controller):

    @validate_token
    @http.route(
        "/fb_api/sale/json",
        auth="public",
        type="json",
        csrf=False,
        cors="*",
    )
    def post_sale_order(self, *args, **kwargs):
        """
        Create a new order with the provided details and return the serialized order response.

        This endpoint allows creating a new order by sending order details in JSON format.
        It processes the request and returns the newly created order's details.

        **Request Example**:
        ```json
        {
            "customer_id": "FOB48274",
            "journal": "INV",
            "date": "2024-02-24",
            "source": "ABC123",
            "product": {
                "code": "CBG",
                "name": "1 Core Big Cable",
                "amount": 20000
            }
        }
        ```

        - `customer_id` (str): The unique identifier of the customer.
        - `journal` (str): The journal used for the order (e.g., 'INV' for invoices).
        - `date` (str): The date the order is being created (in YYYY-MM-DD format).
        - `source` (str): An optional reference code for the order's source.
        - `product` (dict): A dictionary containing the product's details:
            - `code` (str): The unique product code.
            - `name` (str): The product name.
            - `amount` (float): The product's price or total amount.

        **Response Example**:
        ```json
        {
            "id": 13356,
            "name": "SO/2024/0001",
            "order_date": "2024-02-24",
            "pricelist": "Public Pricelist",
            "payment_terms": "Immediate Payment",
            "is_deferred": true,
            "customer": {
                "name": "Shola Ojo-Bello",
                "fob_id": "FOB48274"
            },
            "order_lines": [
                {"product": "Internet Subscription", "quantity": 1, "amount": 5000},
                {"product": "Internet Subscription", "quantity": 1, "amount": 5000}
            ]
        }
        ```

        Args:
            data (dict): A dictionary containing the order details to be created, including customer information, product details, and journal information.

        Returns:
            dict: A dictionary containing the serialized details of the newly created order.

        Raises:
            ValidationError: If the provided data is invalid or required fields are missing.
            AccessError: If the user does not have permission to create the order.
        """
        params = request.get_json_data()

        fob_id = params.get("customer_id")
        order_lines = params.get("order_lines", [])

        # Search with the parameters from the payload
        partner_id = (
            request.env[RES_PARTNER]
            .sudo()
            .search(
                [("x_studio_partner_id", "=", fob_id)],
                limit=1,
            )
        )

        def _get_product_id(product_code=""):
            """Get product using product code."""
            product_id = request.env["product.product"]._get_product_from_code(
                product_code
            )
            return product_id and product_id.id
        payment_term_id = request.env.ref("account.account_payment_term_immediate")
        vals = {
            "date_order": fields.Datetime.now(),
            "pricelist_id": partner_id and partner_id.property_product_pricelist.id,
            "payment_term_id": payment_term_id and payment_term_id.id,
            "is_deferred": True,
            "partner_id": partner_id and partner_id.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": _get_product_id(line["code"]),
                        "product_uom_qty": line["quantity"],
                        "discount": line.get("discount", 0),
                    },
                )
                for line in order_lines
            ],
        }

        # Create order
        new_order = request.env[SALE_ORDER].sudo().create(vals)

        # Confirm order
        new_order.action_confirm()

        data = {
            "id": new_order.id,
            "name": new_order.name,
            "order_date": fields.Date.to_string(new_order.date_order),
            "is_deferred": new_order.is_deferred,
            "pricelist": new_order.pricelist_id.name,
            "payment_terms": new_order.payment_term_id.name,
            "customer": {
                "name": new_order.partner_id.name,
                "fob_id": new_order.partner_id.x_studio_partner_id,
            },
            "order_lines": [
                {
                    "product": line.product_id.name,
                    "quantity": line.product_uom_qty,
                    "amount": line.price_subtotal,
                }
                for line in new_order.order_line
            ],
        }
        return data

    @validate_token
    @http.route(
        "/fb_api/saleorders/<int:id>/register-invoice/json",
        auth="public",
        type="json",
        csrf=False,
        cors="*",
    )
    def register_sale_order_deferred_invoice(self, id=None):
        """
        Create a new order with the provided details and return the serialized order response.

        This endpoint allows creating a new order by sending order details in JSON format.
        It processes the request and returns the newly created order's details.

        Args:
            data (dict): A dictionary containing the order details to be created, including customer information, product details, and journal information.

        Returns:
            dict: A dictionary containing the serialized details of the newly created order.

        Raises:
            ValidationError: If the provided data is invalid or required fields are missing.
            AccessError: If the user does not have permission to create the order.
        """
        order_int_id = id
        if not order_int_id:
            order_int_id = ORDER_ID
        sales_order = (
            request.env["sale.order"]
            .sudo()
            .search([("id", "=", order_int_id)], limit=1)
        )
        if sales_order:
            invoice, payment = sales_order._create_deferred_invoice_and_payment()
            return {
                "message": "Invoice & Payment created successfully",
                "invoice": {
                    "id": invoice and invoice.id,
                    "invoice_number": invoice and invoice.name,
                },
                "payment": {
                    "id": payment and payment.id,
                    "payment_number": payment and payment.name,
                },
            }
        return {"message": "Invoice & payment not created"}

    """
    This method will convert the deferred revenue invoice to an actual invoice
    """

    @validate_token
    @http.route(
        "/fb_api/saleorders/<int:id>/recognize-revenue/json",
        auth="public",
        type="json",
        csrf=False,
        cors="*",
    )
    def register_sale_order_actual_invoice(self, id=None):
        """
        Create a new order with the provided details and return the serialized order response.

        This endpoint allows creating a new order by sending order details in JSON format.
        It processes the request and returns the newly created order's details.

        Args:
            data (dict): A dictionary containing the order details to be created, including customer information, product details, and journal information.

        Returns:
            dict: A dictionary containing the serialized details of the newly created order.

        Raises:
            ValidationError: If the provided data is invalid or required fields are missing.
            AccessError: If the user does not have permission to create the order.
        """
        order_int_id = id
        if not order_int_id:
            return {"message": "No valid order provided!"}
        sales_order = (
            request.env["sale.order"]
            .sudo()
            .search([("id", "=", order_int_id)], limit=1)
        )
        if sales_order:
            sales_order._recognise_actual_revenue()
            return {
                "message": "Revenue has been successfully recognised.",
            }
        return {"message": "Process did not complete successfully."}
